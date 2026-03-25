from services.session_service import create_session, submit_student_response

print("1. Creating session for 'recursion'...")
code = create_session("DEMO", "recursion", "What is the base case in recursion?")

# Simulated ChatGPT answer: technically correct but might use different phrasing than our static cluster keywords
chatgpt_answer = (
    "In the context of computer science and functional programming, the termination criteria, "
    "often referred to as the base case, is a specific condition where the recursive procedure "
    "ceases to call itself further. This prevents stack overflow and provides the initial "
    "return value that bubbles back up through the recursion stack."
)

print("\n2. Submitting high-quality AI-generated answer...")
success, msg, score, status, reason, missing = submit_student_response(code, "AI_User", chatgpt_answer, "recursion")

print(f"\nFinal Status: {status}")
print(f"Final Reason: {reason}")
print(f"Final Score: {score}%")

if "AI verified conceptual depth" in reason and "Likely AI Generated" in reason:
    print("\n✅ Verification SUCCESS: Hybrid logic correctly upgraded status and flagged AI content.")
else:
    print("\n❌ Verification FAILED: Logic did not correctly handle AI content.")
