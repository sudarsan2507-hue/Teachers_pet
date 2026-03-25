from core.question_generator import QuestionGenerator
from core.attendance_manager import AttendanceSession

generator = QuestionGenerator()

topic = "Recursion"
question = generator.generate_question(topic)

print("\nGenerated Cognitive Question:")
print(question)
# ---------------------------------------------------------
# STEP 1: Create Classroom Session
# ---------------------------------------------------------

session = AttendanceSession(
    topic="Recursion",
    teacher_name="Dr. Sharma",
    section="CSE-A"
)

# ---------------------------------------------------------
# STEP 2: Create Dummy Student List
# ---------------------------------------------------------

students = [
    {"roll_no": 1, "name": "Aarav"},
    {"roll_no": 2, "name": "Meera"},
    {"roll_no": 3, "name": "Rohan"},
    {"roll_no": 4, "name": "Ananya"},
    {"roll_no": 5, "name": "Vikram"},
    {"roll_no": 6, "name": "Priya"},
    {"roll_no": 7, "name": "Karan"},
    {"roll_no": 8, "name": "Sneha"}
]

session.load_students(students)

# ---------------------------------------------------------
# STEP 3: Simulated Student Responses
# ---------------------------------------------------------

responses = {
    "Aarav": "Recursion stops when base case is reached",
    "Meera": "I don't know",
    "Rohan": "It repeats until condition",
    "Ananya": "Function calls itself until stopping condition",
    "Vikram": "Not sure",
    "Priya": "Base case prevents infinite loop",
    "Karan": "Repeats",
    "Sneha": "Confused about recursion"
}

session.conduct_attendance(responses)

# ---------------------------------------------------------
# STEP 4: Display Full Report
# ---------------------------------------------------------

summary = session.generate_summary()
print("\n--- Attendance Summary ---")
for k, v in summary.items():
    print(f"{k}: {v}")

print("\n--- Student Records ---")
for r in session.records:
    print(f"{r['name']} ({r['roll_no']}): {r['attendance']} - Score: {r['score']:.2f} - {r['engagement_status']}")
    print(f"  Reason: {r['explanation']}")