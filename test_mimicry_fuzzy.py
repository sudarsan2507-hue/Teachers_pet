from services.session_service import create_session, submit_student_response, get_submissions

print("1. Creating session for 'mimicry_fuzzy_test'...")
question_text = "How does the Python Global Interpreter Lock (GIL) affect multi-threading?"
code = create_session("DEMO", "gil_python", question_text)

# Student copies the question but changes ? to .
mimic_answer = "How does the Python Global Interpreter Lock (GIL) affect multi-threading."

print(f"\n2. Submitting fuzzy mimicry answer: '{mimic_answer}'")
success, msg, score, status, reason, missing = submit_student_response(code, "Fuzzy_Copier", mimic_answer, "gil_python")

print(f"\nFinal Status: {status}")
print(f"Final Reason: {reason}")
print(f"Final Score: {score}%")

if score == 0.0 and status == "Disengaged" and "mimicry" in reason.lower():
    print("\n✅ Verification SUCCESS: Fuzzy mimicry was correctly ignored even with punctuation changes.")
else:
    print("\n❌ Verification FAILED: System awarded a score or missed the mimicry.")
