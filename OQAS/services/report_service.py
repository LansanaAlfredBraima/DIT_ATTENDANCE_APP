import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from config import DB_PATH
import io
import csv
from services.attendance_service import AttendanceService


class ReportService:
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[str]:
        """Validate and normalize date as YYYY-MM-DD or return None."""
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.date().isoformat()
        except Exception:
            return None

    @staticmethod
    def get_module_summary(
        module_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        student_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Build per-student attendance totals for a module with optional filters.

        Returns dict with:
          - module: {module_id, module_code, module_name}
          - filters: {start_date, end_date, student_id}
          - total_sessions: int (within date window)
          - students: List[{student_id, student_name, attended_sessions, percentage}]
        """
        try:
            norm_start = ReportService._parse_date(start_date)
            norm_end = ReportService._parse_date(end_date)

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Module info
            cursor.execute(
                "SELECT module_code, module_name FROM modules WHERE module_id = ?",
                (module_id,),
            )
            mod = cursor.fetchone()
            if not mod:
                return {
                    "error": "Module not found",
                    "module": None,
                    "filters": {"start_date": norm_start, "end_date": norm_end, "student_id": student_id},
                    "total_sessions": 0,
                    "students": [],
                }

            module_info = {
                "module_id": module_id,
                "module_code": mod[0],
                "module_name": mod[1],
            }

            # Build sessions filter
            where_clauses: List[str] = ["module_id = ?"]
            params: List[Any] = [module_id]
            if norm_start:
                where_clauses.append("session_date >= ?")
                params.append(norm_start)
            if norm_end:
                where_clauses.append("session_date <= ?")
                params.append(norm_end)

            where_sql = " AND ".join(where_clauses)

            # Total sessions in window
            cursor.execute(
                f"SELECT COUNT(*) FROM sessions WHERE {where_sql}",
                tuple(params),
            )
            total_sessions = int(cursor.fetchone()[0] or 0)

            if total_sessions == 0:
                return {
                    "module": module_info,
                    "filters": {"start_date": norm_start, "end_date": norm_end, "student_id": student_id},
                    "total_sessions": 0,
                    "students": [],
                }

            # Fetch attendance per student within sessions window
            # First, get relevant session_ids
            cursor.execute(
                f"SELECT session_id FROM sessions WHERE {where_sql}",
                tuple(params),
            )
            session_ids = [row[0] for row in cursor.fetchall()]
            if not session_ids:
                return {
                    "module": module_info,
                    "filters": {"start_date": norm_start, "end_date": norm_end, "student_id": student_id},
                    "total_sessions": total_sessions,
                    "students": [],
                }

            # Build attendance query
            att_where = [
                f"a.session_id IN ({','.join(['?'] * len(session_ids))})",
            ]
            att_params: List[Any] = list(session_ids)
            if student_id:
                att_where.append("a.student_id = ?")
                att_params.append(int(student_id))

            att_sql = " AND ".join(att_where)

            cursor.execute(
                f"""
                SELECT a.student_id, u.full_name, COUNT(*) as attended
                FROM attendance a
                JOIN users u ON u.user_id = a.student_id
                WHERE {att_sql}
                GROUP BY a.student_id, u.full_name
                ORDER BY u.full_name
                """,
                tuple(att_params),
            )
            rows = cursor.fetchall()

            students: List[Dict[str, Any]] = []
            for sid, full_name, attended in rows:
                percentage = round((attended / total_sessions) * 100.0, 2) if total_sessions else 0.0
                students.append(
                    {
                        "student_id": sid,
                        "student_name": full_name,
                        "attended_sessions": int(attended),
                        "attendance_percentage": percentage,
                    }
                )

            return {
                "module": module_info,
                "filters": {"start_date": norm_start, "end_date": norm_end, "student_id": student_id},
                "total_sessions": total_sessions,
                "students": students,
            }
        except Exception as e:
            return {
                "error": f"Report error: {str(e)}",
                "module": None,
                "filters": {"start_date": start_date, "end_date": end_date, "student_id": student_id},
                "total_sessions": 0,
                "students": [],
            }
        finally:
            try:
                conn.close()  # type: ignore[name-defined]
            except Exception:
                pass

    @staticmethod
    def export_csv(
        module_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        student_id: Optional[int] = None,
    ) -> Tuple[str, bytes]:
        """
        Export per-module attendance summary as CSV including percentage and grade.

        Returns: (filename, csv_bytes)
        """
        report = ReportService.get_module_summary(
            module_id=module_id,
            start_date=start_date,
            end_date=end_date,
            student_id=student_id,
        )

        if report.get("error") or not report.get("module"):
            raise ValueError(report.get("error") or "Module not found")

        module = report["module"]
        total_sessions = report["total_sessions"]
        students = report.get("students", [])

        # Prepare filename
        parts: List[str] = [
            f"module_{module['module_id']}",
        ]
        if start_date:
            parts.append(f"from_{start_date}")
        if end_date:
            parts.append(f"to_{end_date}")
        if student_id:
            parts.append(f"student_{student_id}")
        filename = "_".join(parts) + ".csv"

        buf = io.StringIO()
        writer = csv.writer(buf)

        # Header info rows
        writer.writerow(["Module Code", module["module_code"]])
        writer.writerow(["Module Name", module["module_name"]])
        writer.writerow(["Total Sessions", total_sessions])
        writer.writerow(["Start Date", start_date or ""])
        writer.writerow(["End Date", end_date or ""])
        writer.writerow([])

        # Table header
        writer.writerow([
            "Student ID",
            "Student Name",
            "Attended Sessions",
            "Total Sessions",
            "Attendance %",
            "Grade (max 5%)",
        ])

        for s in students:
            pct = float(s.get("attendance_percentage", 0.0))
            grade = AttendanceService.apply_grading_rule(pct, max_grade=5.0)
            writer.writerow([
                s.get("student_id", ""),
                s.get("student_name", ""),
                s.get("attended_sessions", 0),
                total_sessions,
                f"{pct:.2f}",
                f"{grade:.2f}",
            ])

        data = buf.getvalue().encode("utf-8-sig")  # include BOM for Excel friendliness
        buf.close()
        return filename, data

    @staticmethod
    def export_pdf(
        module_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        student_id: Optional[int] = None,
    ) -> Tuple[str, bytes]:
        """
        Optional PDF export using ReportLab. Raises ImportError if ReportLab is not installed.
        Returns: (filename, pdf_bytes)
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        except Exception as e:
            raise ImportError("ReportLab is not installed. Install reportlab to enable PDF export.") from e

        report = ReportService.get_module_summary(
            module_id=module_id,
            start_date=start_date,
            end_date=end_date,
            student_id=student_id,
        )

        if report.get("error") or not report.get("module"):
            raise ValueError(report.get("error") or "Module not found")

        module = report["module"]
        total_sessions = report["total_sessions"]
        students = report.get("students", [])

        parts: List[str] = [f"module_{module['module_id']}"]
        if start_date:
            parts.append(f"from_{start_date}")
        if end_date:
            parts.append(f"to_{end_date}")
        if student_id:
            parts.append(f"student_{student_id}")
        filename = "_".join(parts) + ".pdf"

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        story: List[Any] = []

        title = f"Attendance Summary — {module['module_code']} {module['module_name']}"
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))
        meta = f"Total Sessions: {total_sessions}"
        if start_date:
            meta += f" | Start: {start_date}"
        if end_date:
            meta += f" | End: {end_date}"
        story.append(Paragraph(meta, styles['Normal']))
        story.append(Spacer(1, 12))

        data: List[List[Any]] = [[
            "Student ID", "Name", "Attended", "Total", "%", "Grade"
        ]]
        for s in students:
            pct = float(s.get("attendance_percentage", 0.0))
            grade = AttendanceService.apply_grading_rule(pct, max_grade=5.0)
            data.append([
                s.get("student_id", ""),
                s.get("student_name", ""),
                s.get("attended_sessions", 0),
                total_sessions,
                f"{pct:.2f}",
                f"{grade:.2f}",
            ])

        tbl = Table(data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ]))
        story.append(tbl)

        doc.build(story)
        pdf_bytes = buf.getvalue()
        buf.close()
        return filename, pdf_bytes


