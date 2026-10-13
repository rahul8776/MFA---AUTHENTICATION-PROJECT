import os
import sqlite3
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp
import qrcode

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "local-capstone-demo-key"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")
QR_PATH = os.path.join(BASE_DIR, "setup_qr.png")

USERNAME = "rahul"
PASSWORD_HASH = generate_password_hash("DemoPass123!")


def connect_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialise():
    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                totp_secret TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                checkin_time TEXT NOT NULL
            )
        """)

        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (USERNAME,)
        ).fetchone()

        if user is None:
            secret = pyotp.random_base32()
            db.execute(
                "INSERT INTO users VALUES (?, ?, ?)",
                (USERNAME, PASSWORD_HASH, secret)
            )
            user_secret = secret
        else:
            user_secret = user["totp_secret"]

    if not os.path.exists(QR_PATH):
        uri = pyotp.TOTP(user_secret).provisioning_uri(
            name=USERNAME,
            issuer_name="BIA MFA Capstone"
        )
        qrcode.make(uri).save(QR_PATH)


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return function(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    if session.get("authenticated"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        with connect_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()

        if user and check_password_hash(
            user["password_hash"], password
        ):
            session.clear()
            session["pending_user"] = username
            return redirect(url_for("verify"))

        flash("Invalid username or password.")

    return render_template("login.html")


@app.route("/verify", methods=["GET", "POST"])
def verify():
    username = session.get("pending_user")

    if not username:
        return redirect(url_for("login"))

    if request.method == "POST":
        otp = request.form.get("otp", "").strip()

        with connect_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()

        if user and pyotp.TOTP(
            user["totp_secret"]
        ).verify(otp, valid_window=1):
            session.clear()
            session["authenticated"] = True
            session["username"] = username
            return redirect(url_for("dashboard"))

        flash("Invalid or expired verification code.")

    return render_template("verify.html")


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    username = session["username"]

    if request.method == "POST":
        with connect_db() as db:
            db.execute(
                "INSERT INTO attendance (username, checkin_time) "
                "VALUES (?, ?)",
                (username, datetime.now().astimezone().isoformat(
                    timespec="seconds"
                ))
            )
        flash("Attendance recorded successfully.")
        return redirect(url_for("dashboard"))

    with connect_db() as db:
        records = db.execute(
            "SELECT checkin_time FROM attendance "
            "WHERE username = ? ORDER BY id DESC",
            (username,)
        ).fetchall()

    return render_template(
        "dashboard.html",
        username=username,
        records=records
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    initialise()
    app.run(host="127.0.0.1", port=5000, debug=False)
