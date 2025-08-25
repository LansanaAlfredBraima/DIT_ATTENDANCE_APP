from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from services.auth_service import AuthService
from services.module_service import ModuleService
from services.session_service import SessionController
from services.qr_services import QRService
from services.attendance_service import AttendanceService
import sqlite3
from config import DB_PATH
from config import SECRET_KEY, PORT
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

# JSON route to start session and return QR for floating modal
@app.route("/api/session/qr/start/<int:module_id>", methods=["POST"])
@lecturer_required
def api_start_session_qr(module_id: int):
    user = session["user"]
    result, error = SessionController.start_session(module_id, user["user_id"])
    if error:
        return jsonify({"ok": False, "error": error}), 400
    return jsonify({
        "ok": True,
        "session_id": result["session_id"],
        "qr": result["qr"]
    })

@app.route("/session/qr/close/<int:session_id>")
def close_session_qr(session_id):
    SessionController.close_session(session_id)
    return redirect(url_for("lecturer_dashboard"))

@app.route("/checkin", methods=["GET", "POST"])
def checkin():
    token = request.args.get("tk")
    if not token:
        return render_template("checkin.html", error="Missing token"), 400

    data = QRService.verify_token(token)
    if not data:
        return render_template("checkin.html", error="Invalid or expired token"), 400

    # Optional: validate core fields are present
    required_fields = ["module_id", "run_id", "session_id", "date"]
    if not all(k in data for k in required_fields):
        return render_template("checkin.html", error="Malformed token"), 400

    # Enrich with module_name and week_number for display
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.module_name, s.week_number, u.full_name AS lecturer_name
            FROM sessions s
            JOIN modules m ON s.module_id = m.module_id
            JOIN users u ON m.lecturer_id = u.user_id
            WHERE s.session_id = ?
            """,
            (int(data["session_id"]),),
        )
        row = cursor.fetchone()
        if row:
            data["module_name"] = row[0]
            data["week_number"] = row[1]
            data["lecturer_name"] = row[2]
    finally:
        try:
            conn.close()
        except Exception:
            pass

    if request.method == "POST":
        # Normalize and validate inputs
        full_student_id = (request.form.get("student_id") or "").strip()
        student_name = (request.form.get("student_name") or "").strip()

        # Basic normalization
        if not (full_student_id.isdigit() and len(full_student_id) == 9 and full_student_id.startswith("90500")):
            return render_template("checkin.html", data=data, form_error="Student ID must start with 90500 and have 4 more digits.", form_values={"student_id": full_student_id, "student_name": student_name}), 400

        student_id = int(full_student_id)
        if len(student_name) < 2:
            return render_template("checkin.html", data=data, form_error="Name is too short.", form_values={"student_id": full_student_id, "student_name": student_name}), 400

        ok, err = AttendanceService.record_attendance(session_id=int(data["session_id"]), student_id=student_id, student_name=student_name)
        if not ok:
            return render_template("checkin.html", data=data, form_error=err, form_values={"student_id": full_student_id, "student_name": student_name}), 400

        # Success
        return render_template("checkin.html", data=data, success=True, form_values={"student_id": student_id, "student_name": student_name})

    # GET
    return render_template("checkin.html", data=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
