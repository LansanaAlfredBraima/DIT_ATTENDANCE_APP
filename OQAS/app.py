from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from flask import Response
from services.auth_service import AuthService
from services.module_service import ModuleService
from services.session_service import SessionController
from services.qr_services import QRService
from services.attendance_service import AttendanceService
from services.report_service import ReportService
import sqlite3
from datetime import datetime
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

@app.route("/lecturer/sessions/<int:session_id>/attendance", methods=["GET"])
@lecturer_required
def lecturer_view_attendance(session_id: int):
    """Render attendance list for a given session (open or closed)."""
    try:
        # Fetch basic session + module info
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.session_id, s.session_date, s.status, m.module_code, m.module_name
            FROM sessions s
            JOIN modules m ON s.module_id = m.module_id
            WHERE s.session_id = ?
            """,
            (session_id,),
        )
        row = cursor.fetchone()
    finally:
        try:
            conn.close()  # type: ignore[name-defined]
        except Exception:
            pass

    if not row:
        flash("Session not found")
        return redirect(url_for("lecturer_dashboard"))

    session_info = {
        "session_id": row[0],
        "session_date": row[1],
        "status": row[2],
        "module_code": row[3],
        "module_name": row[4],
    }

    records = AttendanceService.list_attendance_for_session(session_id)
    return render_template("attendance_session.html", session_info=session_info, records=records)

@app.route("/lecturer/modules/<int:module_id>/weeks", methods=["GET"])
@lecturer_required
def lecturer_module_weeks(module_id: int):
    """Show Weeks 1–14 for a module with any sessions per week and links to attendance."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT module_code, module_name, planned_weeks FROM modules WHERE module_id = ?", (module_id,))
        mod = cursor.fetchone()
        if not mod:
            flash("Module not found")
            return redirect(url_for("lecturer_dashboard"))

        module_info = {
            "module_id": module_id,
            "module_code": mod[0],
            "module_name": mod[1],
            "planned_weeks": mod[2] or 14,
        }

        cursor.execute(
            """
            SELECT session_id, week_number, session_date, status
            FROM sessions
            WHERE module_id = ?
            ORDER BY week_number ASC, session_date ASC
            """,
            (module_id,),
        )
        rows = cursor.fetchall()
    finally:
        try:
            conn.close()  # type: ignore[name-defined]
        except Exception:
            pass

    weeks = {w: [] for w in range(1, 15)}
    for r in rows:
        weeks.setdefault(r[1], []).append({
            "session_id": r[0],
            "session_date": r[2],
            "status": r[3],
        })

    return render_template("module_weeks.html", module_info=module_info, weeks=weeks)

@app.route("/module/summary", methods=["GET"])
@lecturer_required
def module_summary():
    """Render per-student totals for a module with optional filters.

    Query params:
      - module_id (required)
      - start_date (YYYY-MM-DD)
      - end_date (YYYY-MM-DD)
      - student_id (optional)
    """
    try:
        module_id = request.args.get("module_id", type=int)
        if not module_id:
            flash("module_id is required")
            return redirect(url_for("lecturer_dashboard"))

        start_date = request.args.get("start_date") or None
        end_date = request.args.get("end_date") or None
        student_id = request.args.get("student_id", type=int) or None

        report = ReportService.get_module_summary(
            module_id=module_id,
            start_date=start_date,
            end_date=end_date,
            student_id=student_id,
        )

        if report.get("error"):
            flash(report.get("error"))
            return redirect(url_for("lecturer_dashboard"))

        return render_template("summary.html", report=report)
    except Exception as e:
        flash(f"Error generating summary: {str(e)}")
        return redirect(url_for("lecturer_dashboard"))

@app.route("/module/summary/export/csv", methods=["GET"])
@lecturer_required
def module_summary_export_csv():
    try:
        module_id = request.args.get("module_id", type=int)
        if not module_id:
            flash("module_id is required")
            return redirect(url_for("lecturer_dashboard"))

        start_date = request.args.get("start_date") or None
        end_date = request.args.get("end_date") or None
        student_id = request.args.get("student_id", type=int) or None

        filename, data = ReportService.export_csv(
            module_id=module_id,
            start_date=start_date,
            end_date=end_date,
            student_id=student_id,
        )
        resp = Response(data, mimetype="text/csv; charset=utf-8")
        resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return resp
    except Exception as e:
        flash(f"CSV export failed: {str(e)}")
        if request.args.get("module_id"):
            return redirect(url_for("module_summary", **request.args))
        return redirect(url_for("lecturer_dashboard"))

@app.route("/module/summary/export/pdf", methods=["GET"])
@lecturer_required
def module_summary_export_pdf():
    try:
        module_id = request.args.get("module_id", type=int)
        if not module_id:
            flash("module_id is required")
            return redirect(url_for("lecturer_dashboard"))

        start_date = request.args.get("start_date") or None
        end_date = request.args.get("end_date") or None
        student_id = request.args.get("student_id", type=int) or None

        filename, data = ReportService.export_pdf(
            module_id=module_id,
            start_date=start_date,
            end_date=end_date,
            student_id=student_id,
        )
        resp = Response(data, mimetype="application/pdf")
        resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return resp
    except ImportError as e:
        flash(str(e))
        return redirect(url_for("module_summary", **request.args))
    except Exception as e:
        flash(f"PDF export failed: {str(e)}")
        if request.args.get("module_id"):
            return redirect(url_for("module_summary", **request.args))
        return redirect(url_for("lecturer_dashboard"))

@app.route("/api/attendance/session/<int:session_id>", methods=["GET"])
@lecturer_required
def api_list_attendance_for_session(session_id: int):
    try:
        records = AttendanceService.list_attendance_for_session(session_id)
        return jsonify({"ok": True, "records": records})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/attendance/submit", methods=["POST"])
def api_submit_attendance():
    """API endpoint for submitting attendance records"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        session_id = data.get("session_id")
        student_id = data.get("student_id")
        student_name = data.get("student_name")
        
        if not all([session_id, student_id, student_name]):
            return jsonify({"success": False, "error": "Missing required fields: session_id, student_id, student_name"}), 400
        
        # Validate session_id is integer
        try:
            session_id = int(session_id)
        except ValueError:
            return jsonify({"success": False, "error": "session_id must be an integer"}), 400
        
        # Validate student_id is integer
        try:
            student_id = int(student_id)
        except ValueError:
            return jsonify({"success": False, "error": "student_id must be an integer"}), 400
        
        # Submit attendance
        success, error_message = AttendanceService.submit_attendance(
            session_id=session_id,
            student_id=student_id,
            student_name=student_name
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": "Attendance recorded successfully",
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": error_message
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


# Day 11: Attendance calculation APIs
@app.route("/api/attendance/student/<int:student_id>/module/<int:module_id>", methods=["GET"])
@lecturer_required
def api_student_attendance_percentage(student_id: int, module_id: int):
    try:
        result = AttendanceService.calculate_student_attendance_percentage(student_id, module_id)
        if result.get("error"):
            return jsonify({"ok": False, "error": result["error"]}), 404
        return jsonify({"ok": True, "data": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/attendance/module/<int:module_id>/summary", methods=["GET"])
@lecturer_required
def api_module_attendance_summary(module_id: int):
    try:
        summary = AttendanceService.calculate_module_attendance_summary(module_id)
        if summary.get("error"):
            return jsonify({"ok": False, "error": summary["error"]}), 404
        return jsonify({"ok": True, "data": summary})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

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

        ok, err = AttendanceService.submit_attendance(session_id=int(data["session_id"]), student_id=student_id, student_name=student_name)
        if not ok:
            return render_template("checkin.html", data=data, form_error=err, form_values={"student_id": full_student_id, "student_name": student_name}), 400

        # Success
        return render_template("checkin.html", data=data, success=True, form_values={"student_id": student_id, "student_name": student_name})

    # GET
    return render_template("checkin.html", data=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
