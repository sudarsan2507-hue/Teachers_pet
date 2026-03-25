from services.session_service import create_session, submit_student_response, get_submissions

print("1. Creating session for 'robust_ai_test'...")
code = create_session("DEMO", "robust_ai", "Explain the Big O complexity of QuickSort.")

# Expert ChatGPT-like answer with standard AI intro
ai_expert_answer = (
    "As an AI language model, I can explain that QuickSort is an efficient, comparison-based sorting algorithm "
    "that uses a divide-and-conquer strategy. On average, its time complexity is O(n log n) because the "
    "partitioning process divides the array into roughly equal halves. However, in the worst-case scenario—"
    "such as when the pivot is consistently the smallest or largest element—the complexity degrades to O(n^2)."
)

print("\n2. Submitting expert AI answer...")
success, msg, score, status, reason, missing = submit_student_response(code, "Expert_AI_Bot", ai_expert_answer, "robust_ai")

print(f"\nFinal Status: {status}")
print(f"Final Reason: {reason}")
print(f"Final Score: {score}%")

# Retrieve from DB to see if rate is 100
subs = get_submissions(code)
if subs:
    latest = subs[-1]
    rate = latest.get("plagiarism_rate")
    print(f"\nStored Plagiarism Rate: {rate}%")
    
    if rate == 100 and status == "Engaged":
        print("\n✅ Verification SUCCESS: 100% Plagiarism was flagged AND status was promoted to Engaged.")
    else:
        print("\n❌ Verification FAILED: Expectations not met.")
else:
    print("\n❌ No submissions found.")
