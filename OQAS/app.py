from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from services.auth_service import AuthService
from services.module_service import ModuleService
from services.session_service import SessionController
from config import SECRET_KEY
from functools import wraps

app = Flask(__name__)
app.secret_key = SECRET_KEY   # Needed for session

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Lecturer required decorator
def lecturer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.')
            return redirect(url_for('login'))
        if not AuthService.is_lecturer(session['user']):
            flash('Access denied. Lecturer privileges required.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

@app.route("/logout")
def logout():
    session.pop('user', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    return "<h1>Admin Dashboard</h1>"

@app.route("/lecturer/dashboard")
@lecturer_required
def lecturer_dashboard():
    """Lecturer dashboard showing their modules"""
    user = session['user']
    modules = ModuleService.get_modules_by_lecturer(user['user_id'])
    
    # Get active sessions for each module
    for module in modules:
        module['active_session'] = ModuleService.get_active_session(module['module_id'])
    
    return render_template("dashboard.html", user=user, modules=modules)

@app.route("/session/start/<int:module_id>", methods=["POST"])
@lecturer_required
def start_session(module_id):
    """Start a new session for a module"""
    try:
        # Get the next week number for this module
        # For simplicity, we'll use the current week number
        from datetime import datetime
        week_number = datetime.now().isocalendar()[1]
        
        success = ModuleService.start_session(module_id, week_number)
        
        if success:
            flash(f'Session started successfully for week {week_number}')
        else:
            flash('Session already exists for today or failed to start')
            
    except Exception as e:
        flash(f'Error starting session: {str(e)}')
    
    return redirect(url_for('lecturer_dashboard'))

@app.route("/session/close/<int:module_id>", methods=["POST"])
@lecturer_required
def close_session(module_id):
    """Close the active session for a module"""
    try:
        success = ModuleService.close_session(module_id)
        
        if success:
            flash('Session closed successfully')
        else:
            flash('No active session found to close')
            
    except Exception as e:
        flash(f'Error closing session: {str(e)}')
    
    return redirect(url_for('lecturer_dashboard'))

@app.route("/session/qr/start/<int:module_id>")
def start_session_qr(module_id):
    user = session.get("user")
    if not user or user.get("role") != "lecturer":
        return redirect(url_for("login"))

    result, error = SessionController.start_session(module_id, user["user_id"])
    if error:
        return f"<h3>{error}</h3><a href='/dashboard'>Back</a>"

    return render_template("session_qr.html", qr=result["qr"], module_id=module_id, session_id=result["session_id"])

@app.route("/session/qr/close/<int:session_id>")
def close_session_qr(session_id):
    SessionController.close_session(session_id)
    return redirect(url_for("lecturer_dashboard"))

if __name__ == "__main__":
    app.run(port=8000, debug=True)
