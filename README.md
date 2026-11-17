# Blogging Platform — Ink & Ideas

A simple multi-user blogging website built with Python, Flask, SQLite, HTML and CSS.

## Features
- Register an account and log in / log out using either email address or display name.
- Passwords are stored as secure password hashes.
- View published articles on the home page.
- Create, read, edit and delete your own articles.
- Users can edit or delete only their own articles.
- SQLite database is created automatically on first run.
- Responsive layout for desktop and mobile.

## Requirements
- Python 3.10 or newer
- Internet connection is only needed if the browser is to load the optional Google Fonts; the app itself runs locally.

## Run on Windows

Open this folder in VS Code, then choose Terminal → New Terminal.

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
```

At login, enter the email address OR display name you used during registration, along with the same password.

Open this address in your browser:

`http://127.0.0.1:5000`

The `blogging.db` file is created automatically when the app starts.

## Folder structure

```text
Flask_Blogging_Platform/
├── app.py
├── requirements.txt
├── README.md
├── blogging.db          # created automatically at runtime
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── post_form.html
│   ├── view_post.html
│   └── message.html
└── static/
    └── style.css
```

## Before using or presenting
This is a learning/demo application, not a production-ready service. It uses a development secret key and Flask's development server. Set a private `SECRET_KEY` environment variable and use a production WSGI server before any real deployment. Add CSRF protection and further validation before exposing it publicly.

Understand and test the code, make your own meaningful changes, and follow your internship's policies on AI assistance, collaboration, similarity checks and authorship. Do not claim work you did not personally complete.
