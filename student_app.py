"""
student_app.py — Student-facing Streamlit application.

Run with:  streamlit run student_app.py --server.port 8502

Navigation via st.session_state["view"]:
  "entry"        → Enter session code + name
  "answer"       → Read question and submit answer
  "confirmation" → Show score and attendance status
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

import database
import services.session_service as svc

# ── Init ──────────────────────────────────────────────────────────────────────

database.init_db()

st.set_page_config(
    page_title="Cognitive Attendance — Student",
    page_icon="📝",
    layout="centered",
)

st.markdown("""
<style>
.big-code {
    font-size: 2rem;
    font-weight: 700;
    color: #1f77b4;
    letter-spacing: 0.2rem;
}
.score-box {
    text-align: center;
    padding: 1.5rem;
    border-radius: 12px;
    font-size: 1.2rem;
}
.present  { background:#d4edda; color:#155724; border:1px solid #c3e6cb; }
.partial  { background:#fff3cd; color:#856404; border:1px solid #ffeeba; }
.absent   { background:#f8d7da; color:#721c24; border:1px solid #f5c6cb; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _go(view: str) -> None:
    st.session_state["view"] = view
    st.rerun()


# ── View: Enter session code + name ──────────────────────────────────────────

def show_entry() -> None:
    st.markdown("## 📝 Student Attendance Portal")
    st.markdown("Enter the **session code** your teacher shared, then your name.")
    st.divider()

    with st.form("entry_form"):
        raw_code = st.text_input(
            "Session Code",
            placeholder="6-character code  (e.g. AB3X7Y)",
            max_chars=6,
        )
        name = st.text_input("Your Full Name", placeholder="e.g. Alice Sharma")
        go   = st.form_submit_button("Continue →", use_container_width=True)

    if go:
        code = raw_code.strip().upper()
        name = name.strip()

        if not code:
            st.error("Please enter the session code.")
            return
        if len(code) != 6:
            st.error("Session code must be exactly 6 characters.")
            return
        if not name:
            st.error("Please enter your name.")
            return

        session = svc.get_session(code)
        if session is None:
            st.error(f"No session found for code **{code}**. Check with your teacher.")
            return
        if not session["is_active"]:
            st.error(f"Session **{code}** has been closed. Contact your teacher.")
            return

        st.session_state["session"]      = session
        st.session_state["student_name"] = name
        _go("answer")


# ── View: Show question + collect answer ──────────────────────────────────────

def show_answer() -> None:
    session = st.session_state["session"]
    name    = st.session_state["student_name"]

    st.markdown(f"## 👋 Hello, **{name}**!")
    st.markdown(f"**Topic:** {session['topic'].title()}")
    st.divider()

    st.markdown("### 📌 Question")
    st.info(session["question"])

    st.markdown("### ✍️ Your Answer")
    st.caption("Write a clear, concise answer. Your response will be evaluated for attendance.")

    with st.form("answer_form"):
        response = st.text_area(
            "Answer",
            placeholder="Type your answer here…",
            height=160,
            label_visibility="collapsed",
        )
        submit = st.form_submit_button("✅ Submit Answer", use_container_width=True, type="primary")

    if submit:
        if not response.strip():
            st.warning("Please write an answer before submitting.")
            return

        with st.spinner("Evaluating your response…"):
            success, message, score, status, reason = svc.submit_student_response(
                session["session_code"],
                name,
                response.strip(),
                session["threshold"],
            )

        if success:
            st.session_state["result"] = {
                "score":    score,
                "status":   status,
                "reason":   reason,
                "response": response.strip(),
            }
            _go("confirmation")
        else:
            # Duplicate submission caught by DB UNIQUE constraint
            st.error(f"⚠️ {message}")


# ── View: Confirmation screen ─────────────────────────────────────────────────

def show_confirmation() -> None:
    result  = st.session_state["result"]
    name    = st.session_state["student_name"]
    session = st.session_state["session"]
    status  = result["status"]

    st.markdown("## ✅ Submission Received!")
    st.success(f"Thank you, **{name}**. Your response has been recorded.")
    st.divider()

    # Score + attendance badge
    col_score, col_attend = st.columns(2)
    with col_score:
        st.metric("Cognitive Score", f"{result['score']} / 100")

    with col_attend:
        if status == "Engaged":
            st.metric("Attendance", "✅ Present")
            st.markdown('<div class="score-box present">🟢 <b>Engaged</b> — Marked Present</div>',
                        unsafe_allow_html=True)
        elif status == "Partially Engaged":
            st.metric("Attendance", "🟡 Present")
            st.markdown('<div class="score-box partial">🟡 <b>Partially Engaged</b> — Marked Present</div>',
                        unsafe_allow_html=True)
        else:
            st.metric("Attendance", "❌ Absent")
            st.markdown('<div class="score-box absent">🔴 <b>Disengaged</b> — Marked Absent</div>',
                        unsafe_allow_html=True)

    st.divider()
    st.markdown("**Your answer:**")
    st.write(f"> {result['response']}")

    if result["reason"]:
        st.markdown("**Feedback:**")
        st.info(result["reason"])

    st.caption(f"Session `{session['session_code']}` · Topic: {session['topic']}")

    st.divider()
    if st.button("Submit for another session", use_container_width=False):
        st.session_state.clear()
        _go("entry")


# ── Router ────────────────────────────────────────────────────────────────────

def main() -> None:
    if "view" not in st.session_state:
        st.session_state["view"] = "entry"

    view = st.session_state["view"]

    if view == "answer" and "session" in st.session_state:
        show_answer()
    elif view == "confirmation" and "result" in st.session_state:
        show_confirmation()
    else:
        show_entry()


main()
