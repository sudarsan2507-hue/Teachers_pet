"""
teacher_app.py — Teacher-facing Streamlit application.
Cognitive Learning Analytics System.

Run with:  streamlit run teacher_app.py

Views:
  "login"     → Teacher ID / password form
  "dashboard" → Create session + past sessions
  "live"      → Live analytics dashboard (auto-refresh)
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
    page_title="CLAS — Teacher Dashboard",
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
.gap-alert {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    margin-bottom: 0.4rem;
    font-size: 0.9rem;
}
.gap-critical {
    background: #f8d7da;
    border-left: 4px solid #dc3545;
}
.metric-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 0.5rem;
    text-align: center;
}
.plagiarism-alert {
    background: #f8d7da;
    border-left: 8px solid #dc3545;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    color: #721c24;
    font-weight: bold;
    animation: glow 2s infinite alternate;
}
@keyframes glow {
    from { box-shadow: 0 0 5px #f8d7da; }
    to { box-shadow: 0 0 20px #dc3545; }
}
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


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _bar_chart_understanding(subs: list[dict], threshold: int) -> None:
    """Bar chart: student name vs Understanding % — colour coded by status."""
    import plotly.graph_objects as go

    colour_map = {
        "Engaged":           "#2ecc71",
        "Partially Engaged": "#f39c12",
        "Disengaged":        "#e74c3c",
    }
    names   = [s["student_name"] for s in subs]
    scores  = [s["score"]        for s in subs]
    colours = [colour_map.get(s["status"], "#95a5a6") for s in subs]

    fig = go.Figure(go.Bar(
        x=names, y=scores,
        marker_color=colours,
        text=[f"{sc:.1f}%" for sc in scores],
        textposition="outside",
    ))
    fig.add_hline(y=threshold, line_dash="dash", line_color="#1f77b4",
                  annotation_text=f"Engaged threshold ({threshold}%)")
    fig.add_hline(y=config.PARTIAL_THRESHOLD, line_dash="dot", line_color="#f39c12",
                  annotation_text=f"Partial threshold ({config.PARTIAL_THRESHOLD}%)")
    fig.update_layout(
        title="Student Understanding Scores",
        xaxis_title="Student",
        yaxis_title="Understanding (%)",
        yaxis_range=[0, 110],
        height=350,
        margin=dict(t=50, b=30),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _pie_chart_engagement(summary: dict) -> None:
    """Pie chart: Engaged / Partially Engaged / Disengaged distribution."""
    import plotly.graph_objects as go

    labels = ["Engaged", "Partially Engaged", "Disengaged"]
    values = [summary["engaged"], summary["partial"], summary["disengaged"]]
    colours = ["#2ecc71", "#f39c12", "#e74c3c"]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        marker_colors=colours,
        hole=0.35,
        textinfo="label+percent+value",
    ))
    fig.update_layout(
        title="Engagement Distribution",
        height=320,
        margin=dict(t=50, b=10),
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)


def _heatmap_concept_coverage(session_code: str, subs: list[dict], topic: str) -> None:
    """
    Heatmap: keyword (rows) vs student (columns).
    Cell = 1 if the student's response contained that keyword, else 0.
    """
    import plotly.graph_objects as go

    clusters = config.get_topic_clusters(topic)
    if not clusters:
        st.info("No concept keyword map found for this topic — heatmap unavailable.")
        return

    all_kws = config.get_all_keywords(topic)
    names   = [s["student_name"] for s in subs]
    texts   = [s["response"].lower() for s in subs]

    # Build matrix: rows = keywords, cols = students
    matrix = []
    for kw in all_kws:
        row = [1 if kw in t else 0 for t in texts]
        matrix.append(row)

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=names,
        y=all_kws,
        colorscale=[[0, "#f8d7da"], [1, "#155724"]],
        showscale=False,
        text=matrix,
        texttemplate="%{text}",
    ))
    fig.update_layout(
        title="Concept Coverage Heatmap (1 = keyword present)",
        xaxis_title="Student",
        yaxis_title="Keyword",
        height=max(300, len(all_kws) * 28 + 80),
        margin=dict(t=50, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)


def _line_chart_progression(teacher_id: str, topic: str) -> None:
    """Line chart: topic mastery progression across sessions."""
    import plotly.graph_objects as go

    rows = svc.get_topic_progression(teacher_id, topic)
    if len(rows) < 2:
        st.caption("Topic progression line chart will appear after 2+ sessions on this topic.")
        return

    sessions_labels = [f"Session {i+1}\n{r['created_at'][:10]}" for i, r in enumerate(rows)]
    means           = [r["mean_score"] if r["mean_score"] else 0 for r in rows]

    fig = go.Figure(go.Scatter(
        x=sessions_labels,
        y=means,
        mode="lines+markers+text",
        text=[f"{m:.1f}%" for m in means],
        textposition="top center",
        line=dict(color="#1f77b4", width=2),
        marker=dict(size=8),
    ))
    fig.update_layout(
        title=f"Class Mastery Progression — {topic.title()}",
        xaxis_title="Session",
        yaxis_title="Class Mean Understanding (%)",
        yaxis_range=[0, 110],
        height=320,
        margin=dict(t=50, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)


def _gap_alerts(session_code: str) -> None:
    """Concept gap indicator panel — flagged keywords sorted by gap index."""
    gaps = svc.get_concept_gaps(session_code)
    flagged = [g for g in gaps if g["flagged"]]

    if not flagged:
        st.success("✅ No significant concept gaps detected.")
        return

    st.markdown("**Concepts requiring reinforcement:**")
    for g in flagged:
        severity = "gap-critical" if g["gap_index"] >= 0.80 else "gap-alert"
        bar_width = int(g["gap_index"] * 100)
        st.markdown(
            f'<div class="{severity}">'
            f'<b>{g["keyword"]}</b> &nbsp;|&nbsp; '
            f'Cluster: <i>{g["cluster"]}</i> &nbsp;|&nbsp; '
            f'Gap Index: <b>{g["gap_index"]:.2f}</b> &nbsp;|&nbsp; '
            f'Coverage: {int(g["coverage_ratio"]*100)}% of class'
            f'</div>',
            unsafe_allow_html=True,
        )


def _plagiarism_alerts(subs: list[dict]) -> None:
    """Dedicated warning panel for AI/Plagiarism flags."""
    # Look for any Source that isn't 'Original'
    flagged = [s for s in subs if "Source:" in (s.get("reason") or "") and "Source: Original" not in (s.get("reason") or "")]
    if not flagged:
        return

    st.markdown('<div class="plagiarism-alert">⚠️ Plagiarism & AI Detection Alerts</div>', unsafe_allow_html=True)
    for s in flagged:
        # Extract the source info from "| Source: ... (Risk: ...%)"
        try:
            source_info = s["reason"].split("Source:")[1].strip()
            st.error(f"**Student:** {s['student_name']} | **Alert:** {source_info}")
        except:
            st.error(f"**Student:** {s['student_name']} | **Alert Flagged**")


# ── View: Login ───────────────────────────────────────────────────────────────

def show_login() -> None:
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown("## 🎓 Cognitive Learning Analytics System")
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

    with tab_new:
        st.subheader("Create a Live Session")

        topic = st.text_input(
            "Topic",
            placeholder="e.g.  recursion  |  sorting  |  ai  |  oop  |  data structures",
            key="new_topic",
        )

        if topic:
            suggestion = config.generate_question(topic)
            st.caption(f"💡 Suggested question: *{suggestion}*")
            # Show available keyword clusters
            clusters = config.get_topic_clusters(topic)
            if clusters:
                st.caption(
                    "📌 Concept clusters: "
                    + " · ".join(f"**{c}**" for c, _ in clusters)
                )
        else:
            suggestion = ""

        col_q, col_t = st.columns([3, 1])
        with col_q:
            if "question_draft" not in st.session_state:
                st.session_state["question_draft"] = suggestion
            if suggestion and st.session_state.get("_last_topic") != topic:
                st.session_state["question_draft"] = suggestion
                st.session_state["_last_topic"] = topic
            question = st.text_input(
                "Question for students (edit to customise)",
                key="question_draft",
            )
        with col_t:
            threshold = st.slider("Engaged threshold (%)", 50, 90, 75, key="new_threshold")

        if st.button("🚀 Create Session", type="primary"):
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
                for k in ("question_draft", "_last_topic", "new_topic"):
                    st.session_state.pop(k, None)
                _go("live")

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
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Submitted",       summary.get("total", 0))
                    c2.metric("Engaged",         summary.get("engaged", 0))
                    c3.metric("Partial",         summary.get("partial", 0))
                    c4.metric("Mean Score",      f"{summary.get('mean_score', 0.0)}%")
                    c5.metric("Std Dev",         f"±{summary.get('std_score', 0.0)}%")

                    if s.get("inference_ai"):
                        with st.expander("✨ AI Pedagogical Insights", expanded=True):
                            st.markdown(s["inference_ai"])

                    subs = svc.get_submissions(s["session_code"])
                    if subs:
                        df   = pd.DataFrame(subs)
                        cols = [c for c in
                                ["student_name", "score", "status", "reason", "submitted_at"]
                                if c in df.columns]
                        st.dataframe(df[cols].rename(columns={
                            "student_name": "Name", "score": "Score (%)",
                            "status": "Status", "reason": "Reasoning",
                            "submitted_at": "Time",
                        }), use_container_width=True, hide_index=True)

                        csv = df[cols].to_csv(index=False)
                        st.download_button(
                            "⬇ Download CSV",
                            data=csv,
                            file_name=f"{s['topic']}_{s['session_code']}_scores.csv",
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
                                with st.spinner("Generating AI class insights..."):
                                    svc.close_session(s["session_code"])
                                    svc.generate_session_inference(s["session_code"])
                                st.success("Session closed and AI report generated.")
                                st.rerun()


# ── View: Live Analytics Dashboard ───────────────────────────────────────────

def show_live() -> None:
    session_code = st.session_state.get("active_code")
    session      = svc.get_session(session_code) if session_code else None

    if not session:
        st.error("Session not found.")
        if st.button("← Back"):
            _go("dashboard")
        return

    st_autorefresh(
        interval=config.REFRESH_INTERVAL * 1000,
        limit=None,
        key="live_autorefresh",
    )

    # ── Sidebar ──────────────────────────────────────────────────────────────
    _sidebar_header()
    if st.sidebar.button("← Back to Dashboard", use_container_width=True):
        st.session_state.pop("active_code", None)
        _go("dashboard")
    if session["is_active"]:
        if st.sidebar.button("🔴 Close Session", use_container_width=True, type="primary"):
            with st.spinner("Generating AI class insights..."):
                svc.close_session(session_code)
                svc.generate_session_inference(session_code)
            st.session_state.pop("active_code", None)
            _go("dashboard")
    st.sidebar.divider()
    st.sidebar.markdown(f"🔄 Auto-refreshes every **{config.REFRESH_INTERVAL}s**")

    # ── Header ────────────────────────────────────────────────────────────────
    st.title("📡 Live Analytics — Concept Mastery Monitor")

    col_code, col_topic, col_stat = st.columns([2, 3, 2])
    with col_code:
        st.markdown("**Session Code — share with students:**")
        st.markdown(f'<div class="session-code">{session_code}</div>', unsafe_allow_html=True)
    with col_topic:
        st.metric("Topic",     session["topic"].title())
        st.metric("Threshold", f"{session['threshold']}%")
    with col_stat:
        st.metric("Status", "🟢 Active" if session["is_active"] else "⚫ Closed")
        st.caption(f"Student app: `localhost:8502`")

    st.info(f"**Question:** {session['question']}")
    
    if session.get("inference_ai"):
        with st.expander("✨ AI Pedagogical Insights (Final Report)", expanded=True):
            st.markdown(session["inference_ai"])
            
    st.divider()

    # ── Class-level metrics ───────────────────────────────────────────────────
    summary = svc.get_session_summary(session_code)
    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    m1.metric("Submitted",      summary["total"])
    m2.metric("Engaged",        summary["engaged"])
    m3.metric("Partial",        summary["partial"])
    m4.metric("Disengaged",     summary["disengaged"])
    m5.metric("Class Mean",     f"{summary['mean_score']:.1f}%")
    
    subs = svc.get_submissions(session_code)
    topic = session["topic"]

    # Calculate mean plagiarism
    plag_mean = 0
    if subs:
        plag_mean = sum(s.get("plagiarism_rate", 0) for s in subs) / len(subs)
    m7.metric("Mean Plagiarism", f"{plag_mean:.1f}%", delta=f"{plag_mean:.1f}%", delta_color="inverse")
    
    m6.metric("Std Dev",        f"±{summary['std_score']}%")

    st.divider()

    if not subs:
        st.info("⏳ Waiting for student submissions…")
        return

    # ── Row 1: Bar chart (left) + Pie chart (right) ───────────────────────────
    col_bar, col_pie = st.columns([3, 2])
    with col_bar:
        _bar_chart_understanding(subs, session["threshold"])
    with col_pie:
        _pie_chart_engagement(summary)

    st.divider()

    # ── Row 2: Concept gap heatmap ────────────────────────────────────────────
    with st.expander("🔬 Concept Coverage Heatmap", expanded=True):
        _heatmap_concept_coverage(session_code, subs, topic)

    # ── Row 3: Topic progression line chart ───────────────────────────────────
    with st.expander("📈 Topic Mastery Progression (across sessions)", expanded=True):
        _line_chart_progression(st.session_state["teacher_id"], topic)

    # ── Row 4: Plagiarism & Warnings ──────────────────────────────────────────
    _plagiarism_alerts(subs)
    st.divider()

    # ── Row 5: Concept gap alerts ─────────────────────────────────────────────
    st.subheader("⚠️ Concept Gap Alerts")
    _gap_alerts(session_code)

    st.divider()

    # ── Raw submissions table ─────────────────────────────────────────────────
    with st.expander("📋 All Submissions", expanded=False):
        df = pd.DataFrame(subs)
        display_cols = ["student_name", "score", "status", "plagiarism_rate", "reason", "submitted_at"]
        df_show = df[[c for c in display_cols if c in df.columns]].copy()
        df_show.columns = ["Name", "Score (%)", "Status", "Plag (%)", "Reasoning", "Submitted At"]

        def _row_style(row):
            reason = row["Reasoning"] or ""
            plag_rate = row.get("Plag (%)", 0)

            # 1. Critical Plagiarism/AI Source (Bold Red)
            if "Source:" in reason and "Source: Original" not in reason:
                return ["background-color:#f8d7da; font-weight:bold; border: 2px solid #dc3545"] * len(row)
                
            # 2. Gradient Warning for Plagiarism Risk
            if plag_rate > 30:
                alpha = min(0.4, (plag_rate / 100))
                return [f"background-color: rgba(220, 53, 69, {alpha});"] * len(row)
                
            # 3. Standard Engagement Shading
            colour_map = {
                "Engaged":           "background-color:#d4edda",
                "Partially Engaged": "background-color:#fff3cd",
                "Disengaged":        "background-color:#f8d7da",
            }
            colour = colour_map.get(row["Status"], "")
            return [colour] * len(row)

        has_plagiarism = any("Plagiarism flag:" in (s.get("reason") or "") for s in subs)
        
        styled = df_show.style.apply(_row_style, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)

        csv = df_show.to_csv(index=False)
        st.download_button(
            "⬇ Download CSV Report",
            data=csv,
            file_name=f"{topic}_{session_code}_report.csv",
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
