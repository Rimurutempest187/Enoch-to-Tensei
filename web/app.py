from flask import Flask, render_template, redirect, request, url_for
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, UserMixin
)

from auth import Admin, ADMINS
import db_api

app = Flask(__name__)
app.secret_key = "super-secret-key"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return Admin(user_id)


# ============ LOGIN ============

@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        user = request.form["username"]
        pw = request.form["password"]

        if user in ADMINS and ADMINS[user] == pw:
            login_user(Admin(user))
            return redirect("/dashboard")

    return render_template("login.html")


# ============ DASHBOARD ============

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# ============ USERS ============

@app.route("/users")
@login_required
def users():

    rows = db_api.get_users()
    return render_template("users.html", users=rows)


@app.route("/edit_coins/<uid>", methods=["POST"])
@login_required
def edit_coins(uid):

    new = request.form["coins"]
    db_api.update_coins(uid, new)

    return redirect("/users")


# ============ CHARACTERS ============

@app.route("/chars")
@login_required
def chars():

    rows = db_api.get_chars()
    return render_template("chars.html", chars=rows)


# ============ LOGOUT ============

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
