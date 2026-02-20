import streamlit as st
from hybrid_engine import evaluate_response

st.title("Hybrid Cognitive Attendance System")

response = st.text_area("Enter student response:")

if st.button("Evaluate"):
    if response.strip() == "":
        st.warning("Please enter a response.")
    else:
        score, status = evaluate_response(response)
        st.success(f"Cognitive Score: {score}")
        st.write(f"Engagement Status: {status}")