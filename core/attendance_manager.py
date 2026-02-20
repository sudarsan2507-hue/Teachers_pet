from hybrid_engine import evaluate_response
from datetime import datetime


class AttendanceSession:
    def __init__(self, topic, teacher_name, section):
        self.topic = topic
        self.teacher_name = teacher_name
        self.section = section
        self.session_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.student_list = []
        self.records = []

    # -----------------------------------------
    # Load Student List
    # -----------------------------------------
    def load_students(self, students):
        self.student_list = students

    # -----------------------------------------
    # Conduct Attendance
    # -----------------------------------------
    def conduct_attendance(self, responses_dict, threshold=75):

        for student in self.student_list:

            name = student["name"]
            roll_no = student["roll_no"]

            response = responses_dict.get(name, "")

            score, status, reasons = evaluate_response(response, threshold)

            if status in ["Engaged", "Partially Engaged"]:
                attendance = "Present"
            else:
                attendance = "Absent"

            record = {
                "roll_no": roll_no,
                "name": name,
                "response": response,
                "score": score,
                "engagement_status": status,
                "attendance": attendance,
                "explanation": ", ".join(reasons) if reasons else "Valid response"
            }

            self.records.append(record)

    # -----------------------------------------
    # Generate Summary
    # -----------------------------------------
    def generate_summary(self):

        total = len(self.records)
        present = sum(1 for r in self.records if r["attendance"] == "Present")
        absent = total - present

        engagement_rate = round((present / total) * 100, 2) if total > 0 else 0

        return {
            "Teacher": self.teacher_name,
            "Section": self.section,
            "Topic": self.topic,
            "Session Time": self.session_time,
            "Total Students": total,
            "Present": present,
            "Absent": absent,
            "Engagement Rate (%)": engagement_rate
        }