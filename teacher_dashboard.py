import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from core.attendance_manager import AttendanceSession
from core.question_generator import QuestionGenerator

st.set_page_config(page_title="Hybrid Cognitive Attendance", layout="wide")

st.title("Hybrid Cognitive Attendance System")

# ------------------------------
# Teacher Inputs
# ------------------------------
teacher_name = st.text_input("Teacher Name")
section = st.text_input("Section")
topic = st.text_input("Enter Today's Topic")

engagement_threshold = st.slider(
    "Engagement Strictness Threshold",
    min_value=60,
    max_value=90,
    value=75
)

if topic:
    generator = QuestionGenerator()
    question = generator.generate_question(topic)
    st.info(f"Generated Question: {question}")

# ------------------------------
# Start Session
# ------------------------------
if st.button("Start Attendance Session") and teacher_name and section and topic:

    st.session_state.session = AttendanceSession(topic, teacher_name, section)

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

    st.session_state.session.load_students(students)

    responses = {
        "Aarav": "Recursion stops when base case is reached",
        "Meera": "I don't know",
        "Rohan": "It repeats until condition",
        "Ananya": "Function calls itself until stopping condition",
        "Vikram": "",
        "Priya": "Base case prevents infinite loop",
        "Karan": "Repeats",
        "Sneha": ""
    }

    st.session_state.session.conduct_attendance(responses, engagement_threshold)

# ------------------------------
# Display Results
# ------------------------------
if "session" in st.session_state:

    session = st.session_state.session

    if session.records:

        df = pd.DataFrame(session.records)

        st.subheader("Attendance Table")
        st.dataframe(df, use_container_width=True)

        # Engagement Chart
        st.subheader("Engagement Distribution")
        engagement_counts = df["engagement_status"].value_counts()

        fig, ax = plt.subplots()
        engagement_counts.plot(kind="bar", ax=ax)
        ax.set_xlabel("Engagement Level")
        ax.set_ylabel("Number of Students")
        st.pyplot(fig)

        # Attendance Chart
        st.subheader("Attendance Overview")
        attendance_counts = df["attendance"].value_counts()

        fig2, ax2 = plt.subplots()
        ax2.pie(attendance_counts, labels=attendance_counts.index, autopct='%1.1f%%')
        ax2.set_title("Present vs Absent")
        st.pyplot(fig2)

        # Summary Metrics
        summary = session.generate_summary()

        st.subheader("Session Summary")
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Students", summary["Total Students"])
        col2.metric("Present", summary["Present"])
        col3.metric("Absent", summary["Absent"])
        col4.metric("Engagement Rate (%)", summary["Engagement Rate (%)"])

        # Export
        st.subheader("Export Attendance Report")
        csv = df.to_csv(index=False)

        st.download_button(
            label="Download Attendance Report (CSV)",
            data=csv,
            file_name=f"{summary['Topic']}_Attendance_Report.csv",
            mime="text/csv"
        )

# Reset Session
if st.button("Reset Session"):
    st.session_state.clear()