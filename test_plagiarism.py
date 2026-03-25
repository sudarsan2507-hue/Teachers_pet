from services.session_service import check_plagiarism, get_session, submit_student_response

print("Creating session...")
from services.session_service import create_session
code = create_session("DEMO", "recursion", "What is the role of base case in recursion?")
print(f"Session {code} created.")

print("\nSubmitting Answer 1...")
success, msg, score, status, reason, missing = submit_student_response(code, "Alice", "The base case acts as a stopping condition so that the recursion does not run infinitely.", "recursion")
print(f"Alice Reason: {reason}")

print("\nSubmitting Answer 2 (Plagiarised)...")
# Submit the exact same answer as Alice
success, msg, score, status, reason, missing = submit_student_response(code, "Bob", "The base case acts as a stopping condition so that the recursion does not run infinitely.", "recursion")

print(f"Bob Reason: {reason}")
