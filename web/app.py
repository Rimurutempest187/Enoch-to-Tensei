# web/app.py

import os
from functools import wraps

from flask import (
    Flask, render_template, redirect,
    request, url_for, flash, abort
)

from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)

from auth import Admin
import db_api
import db_admin

# ================= CONFIG =================

from config import ALLOWED_IPS

APP_SECRET = os.getenv("WEB_SECRET", "CHANGE_ME_NOW")

# ================= INIT ===================

app = Flask(__name__)
app.secret_key = APP_SECRET

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ================= LOGIN LOADER ============


@login_manager.user_loader
def load_user(username):
    return Admin(username)


# ================= IP RESTRICT =============


@app.before_request
def restrict_ip():

    if not ALLOWED_IPS:
        return

    if request.endpoint in ("login", "static"):
        return

    ip = request.remote_addr

    if ip not in ALLOWED_IPS:
        abort(403)


# ================= LOGIN ===================


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect("/dashboard")

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if db_admin.verify_admin(username, password):

            login_user(Admin(username))

            db_admin.log_action(
                username,
                "LOGIN",
                "SUCCESS",
                request.remote_addr
            )

            return redirect("/dashboard")

        else:

            db_admin.log_action(
                username,
                "LOGIN",
                "FAILED",
                request.remote_addr
            )

            flash("Invalid username or password", "danger")

    return render_template("login.html")


# ================= LOGOUT ==================


@app.route("/logout")
@login_required
def logout():

    db_admin.log_action(
        current_user.id,
        "LOGOUT",
        "-",
        request.remote_addr
    )

    logout_user()
    return redirect("/login")


# ================= DASHBOARD ===============


@app.route("/dashboard")
@login_required
def dashboard():

    total_users = db_api.count_users()
    total_chars = db_api.count_chars()

    return render_template(
        "dashboard.html",
        user=current_user.id,
        users=total_users,
        chars=total_chars
    )


# ================= USERS ===================


@app.route("/users")
@login_required
def users():

    rows = db_api.get_users()

    return render_template("users.html", users=rows)


@app.route("/users/edit/<uid>", methods=["POST"])
@login_required
def edit_user(uid):

    coins = request.form.get("coins")
    level = request.form.get("level")

    db_api.update_user(uid, coins, level)

    db_admin.log_action(
        current_user.id,
        "EDIT_USER",
        f"UID={uid}|coins={coins}|level={level}",
        request.remote_addr
    )

    flash("User updated", "success")

    return redirect("/users")


# ================= CHARACTERS ==============


@app.route("/chars")
@login_required
def chars():

    rows = db_api.get_chars()

    return render_template("chars.html", chars=rows)


# ================= AUDIT LOGS ==============


@app.route("/logs")
@login_required
def logs():

    rows = db_admin.get_logs(limit=200)

    return render_template("logs.html", logs=rows)


# ================= ERROR ===================


@app.errorhandler(403)
def forbidden(e):
    return "<h3>403 - Access Denied</h3>", 403


@app.errorhandler(404)
def not_found(e):
    return "<h3>404 - Not Found</h3>", 404


# ================= MAIN ====================


if __name__ == "__main__":

    # For HTTPS (optional dev cert)
    CERT = os.getenv("SSL_CERT")
    KEY = os.getenv("SSL_KEY")

    if CERT and KEY:
        app.run(
            host="0.0.0.0",
            port=5000,
            ssl_context=(CERT, KEY),
            debug=False
        )
    else:
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=True
        )
