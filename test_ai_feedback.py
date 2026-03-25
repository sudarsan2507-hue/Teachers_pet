from services.session_service import create_session, submit_student_response, get_submissions

print("1. Creating session for 'ai_feedback_test'...")
question_text = "What is the primary difference between a Shallow Copy and a Deep Copy in Python?"
code = create_session("DEMO", "copy_py", question_text)

# Student answer that is correct but a bit brief (missing mutable object details)
real_answer = (
    "A shallow copy creates a new object but inserts references into it. "
    "A deep copy creates a new object and recursively inserts copies of objects found in the original."
)

print(f"\n2. Submitting student answer: '{real_answer}'")
success, msg, score, status, reason, missing = submit_student_response(code, "Alice_Student", real_answer, "copy_py")

print(f"\nFinal Status: {status}")
print(f"Final Reason: {reason}")
print(f"Personalized Gaps: {missing}")

if "TIP:" in reason and "|" in missing:
    print("\n✅ Verification SUCCESS: AI-driven tip and conceptual gaps were generated.")
else:
    print("\n❌ Verification FAILED: Feedback still looks static.")
