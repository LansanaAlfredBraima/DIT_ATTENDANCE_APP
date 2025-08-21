class AttendanceRecord:
    def __init__(self, attendance_id: int, module_id: int, student_id: str, student_name: str, timestamp_utc: str):
        self.attendance_id = attendance_id
        self.module_id = module_id
        self.student_id = student_id
        self.student_name = student_name
        self.timestamp_utc = timestamp_utc

    def __str__(self):
        return f"[{self.timestamp_utc}] {self.student_name} ({self.student_id}) attended module {self.module_id}"
