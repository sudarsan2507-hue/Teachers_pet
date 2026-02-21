"""
teacher_app.py — Teacher-facing Streamlit application.

Run with:  streamlit run teacher_app.py

Navigation is managed via st.session_state["view"]:
  "login"     → Teacher ID / password form
  "dashboard" → Create session tab + Past sessions tab
  "live"      → Auto-refreshing live attendance dashboard
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh

import config
import database
import services.session_service as svc

# ── Init ──────────────────────────────────────────────────────────────────────

database.init_db()

st.set_page_config(
    page_title="Cognitive Attendance — Teacher",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
.session-code {
    font-size: 3rem;
    font-weight: 900;
    letter-spacing: 0.4rem;
    color: #1f77b4;
    text-align: center;
    padding: 1rem;
    background: #e8f4fd;
    border-radius: 12px;
    border: 2px dashed #1f77b4;
}
.status-engaged   { color: #155724; background: #d4edda; padding: 2px 8px; border-radius: 4px; }
.status-partial   { color: #856404; background: #fff3cd; padding: 2px 8px; border-radius: 4px; }
.status-disengaged{ color: #721c24; background: #f8d7da; padding: 2px 8px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _go(view: str) -> None:
    st.session_state["view"] = view
    st.rerun()


def _sidebar_header() -> None:
    st.sidebar.image("https://img.icons8.com/color/96/teacher.png", width=60)
    st.sidebar.markdown(f"**Logged in as:** `{st.session_state['teacher_id']}`")
    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ── View: Login ───────────────────────────────────────────────────────────────

def show_login() -> None:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("## 🎓 Cognitive Attendance System")
        st.markdown("### Teacher Login")
        st.divider()

        with st.form("login_form", clear_on_submit=False):
            teacher_id = st.text_input("Teacher ID", placeholder="e.g. DEMO")
            password   = st.text_input("Password",   type="password")
            submitted  = st.form_submit_button("Login →", use_container_width=True)

        if submitted:
            creds = config.TEACHER_CREDENTIALS
            if teacher_id in creds and creds[teacher_id] == password:
                st.session_state["teacher_id"] = teacher_id
                _go("dashboard")
            else:
                st.error("❌ Invalid Teacher ID or password.")

        st.caption("**Demo credentials** — ID: `DEMO`  |  Password: `demo123`")


# ── View: Dashboard ───────────────────────────────────────────────────────────

def show_dashboard() -> None:
    _sidebar_header()
    st.title("📋 Teacher Dashboard")

    tab_new, tab_hist = st.tabs(["➕  New Session", "📂  Past Sessions"])

    # ── Tab: Create new session ───────────────────────────────────────────────
    with tab_new:
        st.subheader("Create a Live Attendance Session")

        # Topic drives question suggestion (outside form so it triggers rerun)
        topic = st.text_input(
            "Topic",
            placeholder="e.g.  recursion  |  sorting  |  ai  |  oop",
            key="new_topic",
        )

        # Auto-suggest then allow teacher to edit
        if topic:
            suggestion = config.generate_question(topic)
            st.caption(f"💡 Suggested question: *{suggestion}*")
        else:
            suggestion = ""

        col_q, col_t = st.columns([3, 1])
        with col_q:
            # Use a key so value can be programmatically seeded
            if "question_draft" not in st.session_state:
                st.session_state["question_draft"] = suggestion
            if suggestion and st.session_state.get("_last_topic") != topic:
                st.session_state["question_draft"] = suggestion
                st.session_state["_last_topic"] = topic

            question = st.text_input(
                "Question sent to students (edit to customise)",
                key="question_draft",
            )

        with col_t:
            threshold = st.slider("Engagement threshold", 50, 90, 75, key="new_threshold")

        if st.button("🚀 Create Session", type="primary", use_container_width=False):
            if not topic.strip():
                st.warning("Please enter a topic.")
            elif not question.strip():
                st.warning("Please enter a question.")
            else:
                code = svc.create_session(
                    st.session_state["teacher_id"],
                    topic.strip(),
                    question.strip(),
                    threshold,
                )
                st.session_state["active_code"] = code
                # Clear drafts to avoid stale state
                for k in ("question_draft", "_last_topic", "new_topic"):
                    st.session_state.pop(k, None)
                _go("live")

    # ── Tab: Past sessions ────────────────────────────────────────────────────
    with tab_hist:
        st.subheader("Your Sessions")
        sessions = svc.get_teacher_sessions(st.session_state["teacher_id"])

        if not sessions:
            st.info("No sessions yet — create one in the **New Session** tab.")
        else:
            for s in sessions:
                badge   = "🟢 Active" if s["is_active"] else "⚫ Closed"
                summary = svc.get_session_summary(s["session_code"])
                label   = f"{badge} | `{s['session_code']}` — **{s['topic']}** | {s['created_at']}"

                with st.expander(label):
                    st.markdown(f"**Question:** {s['question']}")
                    st.markdown(f"**Threshold:** {s['threshold']}")

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Submitted",    summary["total"])
                    c2.metric("✅ Present",   summary["present"])
                    c3.metric("❌ Absent",    summary["absent"])
                    c4.metric("Engagement %", f"{summary['engagement_rate']}%")

                    subs = svc.get_submissions(s["session_code"])
                    if subs:
                        df = pd.DataFrame(subs)
                        cols = [c for c in
                                ["student_name","response","score","status","reason","submitted_at"]
                                if c in df.columns]
                        st.dataframe(df[cols].rename(columns={
                            "student_name": "Name", "response": "Response",
                            "score": "Score", "status": "Status",
                            "reason": "Reason", "submitted_at": "Time",
                        }), use_container_width=True, hide_index=True)

                        csv = df[cols].to_csv(index=False)
                        st.download_button(
                            "⬇ Download CSV",
                            data=csv,
                            file_name=f"{s['topic']}_{s['session_code']}_report.csv",
                            mime="text/csv",
                            key=f"dl_{s['session_code']}",
                        )

                    col_act, _ = st.columns([1, 3])
                    with col_act:
                        if s["is_active"]:
                            if st.button("📡 Go Live", key=f"live_{s['session_code']}"):
                                st.session_state["active_code"] = s["session_code"]
                                _go("live")
                            if st.button("🔴 Close", key=f"close_{s['session_code']}"):
                                svc.close_session(s["session_code"])
                                st.success("Session closed.")
                                st.rerun()


# ── View: Live Dashboard ──────────────────────────────────────────────────────

def show_live() -> None:
    session_code = st.session_state.get("active_code")
    session      = svc.get_session(session_code) if session_code else None

    if not session:
        st.error("Session not found.")
        if st.button("← Back"):
            _go("dashboard")
        return

    # Non-blocking auto-refresh (st_autorefresh uses a JS timer, not sleep)
    st_autorefresh(
        interval=config.REFRESH_INTERVAL * 1000,
        limit=None,
        key="live_autorefresh",
    )

    # ── Sidebar ───────────────────────────────────────────────────────────────
    _sidebar_header()
    if st.sidebar.button("← Back to Dashboard", use_container_width=True):
        st.session_state.pop("active_code", None)
        _go("dashboard")
    if session["is_active"]:
        if st.sidebar.button("🔴 Close Session", use_container_width=True, type="primary"):
            svc.close_session(session_code)
            st.session_state.pop("active_code", None)
            _go("dashboard")
    st.sidebar.divider()
    st.sidebar.markdown(f"🔄 Auto-refreshes every **{config.REFRESH_INTERVAL}s**")

    # ── Header ────────────────────────────────────────────────────────────────
    st.title("📡 Live Attendance")

    col_code, col_topic, col_stat = st.columns([2, 3, 2])
    with col_code:
        st.markdown("**Session Code — share with students:**")
        st.markdown(f'<div class="session-code">{session_code}</div>', unsafe_allow_html=True)
    with col_topic:
        st.metric("Topic",     session["topic"].title())
        st.metric("Threshold", session["threshold"])
    with col_stat:
        st.metric("Status", "🟢 Active" if session["is_active"] else "⚫ Closed")
        st.caption(f"Student app: `localhost:8502`")

    st.info(f"**Question:** {session['question']}")
    st.divider()

    # ── Live Metrics ─────────────────────────────────────────────────────────
    summary = svc.get_session_summary(session_code)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📨 Submitted",  summary["total"])
    m2.metric("🟢 Engaged",    summary["engaged"])
    m3.metric("🟡 Partial",    summary["partial"])
    m4.metric("🔴 Disengaged", summary["disengaged"])
    m5.metric("📊 Present %",  f"{summary['engagement_rate']}%")

    st.subheader("Submissions")

    subs = svc.get_submissions(session_code)
    if not subs:
        st.info("⏳ Waiting for student submissions…")
    else:
        df = pd.DataFrame(subs)
        display_cols = ["student_name", "response", "score", "status", "reason", "submitted_at"]
        df_show = df[[c for c in display_cols if c in df.columns]].copy()
        df_show.columns = ["Name", "Response", "Score", "Status", "Reason", "Submitted At"]

        def _row_style(row):
            colours = {
                "Engaged":           "background-color:#d4edda",
                "Partially Engaged": "background-color:#fff3cd",
                "Disengaged":        "background-color:#f8d7da",
            }
            colour = colours.get(row["Status"], "")
            return [colour] * len(row)

        styled = df_show.style.apply(_row_style, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)

        csv = df_show.to_csv(index=False)
        st.download_button(
            "⬇ Download CSV Report",
            data=csv,
            file_name=f"{session['topic']}_{session_code}_report.csv",
            mime="text/csv",
        )


# ── Router ────────────────────────────────────────────────────────────────────

def main() -> None:
    if "view" not in st.session_state:
        st.session_state["view"] = "login"

    view = st.session_state["view"]

    if view == "live" and "active_code" in st.session_state:
        show_live()
    elif view == "dashboard" and "teacher_id" in st.session_state:
        show_dashboard()
    else:
        show_login()


main()
