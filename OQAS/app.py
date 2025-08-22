from flask import Flask, render_template, request, redirect, session, url_for, flash
from services.auth_service import AuthService
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY   # Needed for session

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    try:
        user = AuthService.login(username, password)
        session["user"] = user  # store user in session

        if AuthService.is_admin(user):
            return redirect(url_for("admin_dashboard"))
        elif AuthService.is_lecturer(user):
            return redirect(url_for("lecturer_dashboard"))
        else:
            flash("Unknown role. Contact admin.")
            return redirect(url_for("login"))

    except ValueError as e:
        flash(str(e))
        return render_template("login.html", error="Invalid credentials")


@app.route("/admin/dashboard")
def admin_dashboard():
    return "<h1>Admin Dashboard</h1>"

@app.route("/lecturer/dashboard")
def lecturer_dashboard():
    return "<h1>Lecturer Dashboard</h1>"

if __name__ == "__main__":
    app.run(port=8000, debug=True)
