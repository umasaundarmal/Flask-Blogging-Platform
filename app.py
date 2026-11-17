import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "blogging.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "local-development-key-change-before-deployment")


def connect_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def initialize_db():
    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        db.commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    with connect_db() as db:
        posts = db.execute("""
            SELECT posts.*, users.username
            FROM posts JOIN users ON users.id = posts.user_id
            ORDER BY posts.created_at DESC, posts.id DESC
        """).fetchall()
    return render_template("index.html", posts=posts)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Please complete every field.", "error")
        elif len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
        else:
            try:
                with connect_db() as db:
                    db.execute(
                        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                        (username, email, generate_password_hash(password))
                    )
                    db.commit()
                flash("Account created. You can now log in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("That username or email is already registered.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Accept either the registered email address or display name.
        # This also handles browsers that autofill the display name into the login field.
        login_identifier = request.form.get("login_identifier", "").strip()
        password = request.form.get("password", "")
        with connect_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE email = ? COLLATE NOCASE OR username = ? COLLATE NOCASE",
                (login_identifier, login_identifier)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Welcome back!", "success")
            return redirect(url_for("home"))
        flash("Email/display name or password is incorrect. Use the email address or display name you registered with, and the same password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/post/new", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not content:
            flash("Please enter both a title and the article text.", "error")
        else:
            with connect_db() as db:
                db.execute(
                    "INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
                    (session["user_id"], title, content)
                )
                db.commit()
            flash("Your article has been published.", "success")
            return redirect(url_for("home"))
    return render_template("post_form.html", page_title="Write a post", post=None)


@app.route("/post/<int:post_id>")
def view_post(post_id):
    with connect_db() as db:
        post = db.execute("""
            SELECT posts.*, users.username
            FROM posts JOIN users ON users.id = posts.user_id
            WHERE posts.id = ?
        """, (post_id,)).fetchone()
    if post is None:
        abort(404)
    return render_template("view_post.html", post=post)


@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    with connect_db() as db:
        post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post is None:
            abort(404)
        if post["user_id"] != session["user_id"]:
            abort(403)

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            if not title or not content:
                flash("Please enter both a title and the article text.", "error")
            else:
                db.execute("""
                    UPDATE posts SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                """, (title, content, post_id, session["user_id"]))
                db.commit()
                flash("Your article has been updated.", "success")
                return redirect(url_for("view_post", post_id=post_id))
    return render_template("post_form.html", page_title="Edit your post", post=post)


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    with connect_db() as db:
        post = db.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,)).fetchone()
        if post is None:
            abort(404)
        if post["user_id"] != session["user_id"]:
            abort(403)
        db.execute("DELETE FROM posts WHERE id = ? AND user_id = ?", (post_id, session["user_id"]))
        db.commit()
    flash("Your article has been deleted.", "success")
    return redirect(url_for("home"))


@app.errorhandler(403)
def forbidden(_error):
    return render_template("message.html", heading="Access denied", message="You can only manage your own articles."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("message.html", heading="Page not found", message="The page or article you requested does not exist."), 404


if __name__ == "__main__":
    initialize_db()
    app.run(debug=True)
