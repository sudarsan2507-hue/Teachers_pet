from services.session_service import create_session, submit_student_response, close_session, generate_session_inference, get_session

print("1. Creating test session...")
code = create_session("DEMO", "binary search", "Explain how binary search halves the search space.")
print(f"Session {code} created.")

print("\n2. Submitting student responses...")
submit_student_response(code, "Alice", "It compares the middle element and discards half based on whether the value is larger or smaller.", "binary search")
submit_student_response(code, "Bob", "I don't know, maybe it just divides everything.", "binary search")
submit_student_response(code, "Charlie", "It finds the median and branches left or right recursively.", "binary search")

print("\n3. Closing session and generating AI inference...")
close_session(code)
inference = generate_session_inference(code)

print("\n--- AI Inference Generated ---")
print(inference)

# Double check database storage
session = get_session(code)
if session.get("inference_ai"):
    print("\n✅ Verification SUCCESS: Inference stored in database.")
else:
    print("\n❌ Verification FAILED: Inference NOT found in database.")
