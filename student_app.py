"""
student_app.py — Student-facing Streamlit application.
Cognitive Learning Analytics System — Enhanced UI.

Run with:  streamlit run student_app.py --server.port 8502
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
    page_title="CLAS — Student Portal",
    page_icon="📝",
    layout="centered",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Score badge */
.score-badge {
    text-align: center;
    padding: 2rem 1rem;
    border-radius: 16px;
    margin-bottom: 1.2rem;
    font-size: 1rem;
    font-weight: 600;
}
.score-badge .big-num {
    font-size: 3.5rem;
    font-weight: 900;
    display: block;
    line-height: 1.1;
}
.score-badge .tag {
    font-size: 1.1rem;
    font-weight: 700;
    display: block;
    margin-top: 0.3rem;
    opacity: 0.92;
}

/* Status colours — explicit dark text so visible in dark AND light mode */
.engaged-card    { background: linear-gradient(135deg,#1a7a4a,#27ae60); color:#ffffff; border:2px solid #2ecc71; }
.partial-card    { background: linear-gradient(135deg,#c17f10,#e67e22); color:#ffffff; border:2px solid #f39c12; }
.disengaged-card { background: linear-gradient(135deg,#922b21,#e74c3c); color:#ffffff; border:2px solid #c0392b; }

/* Metric strip */
.metric-strip {
    display: flex;
    gap: 12px;
    margin: 1rem 0;
}
.metric-box {
    flex: 1;
    background: #1e2a3a;
    border-radius: 12px;
    padding: 1rem 0.5rem;
    text-align: center;
    border: 1px solid #2e4057;
}
.metric-box .m-label {
    font-size: 0.75rem;
    color: #8faacc;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.metric-box .m-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: #ffffff;
    margin-top: 4px;
}
.metric-box .m-value.up   { color: #2ecc71; }
.metric-box .m-value.down { color: #e74c3c; }
.metric-box .m-value.neu  { color: #f39c12; }

/* Weak chips */
.chips-wrap { margin: 0.6rem 0; }
.weak-chip {
    display: inline-block;
    background: #2c1e0f;
    border: 1.5px solid #e67e22;
    color: #f0a756;
    border-radius: 20px;
    padding: 4px 14px;
    margin: 4px 4px;
    font-size: 0.82rem;
    font-weight: 600;
}

/* Tip box */
.tip-box {
    background: #0d2137;
    border-left: 4px solid #3498db;
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.2rem;
    color: #c9e4fa !important;
    font-size: 0.95rem;
    line-height: 1.6;
}
.tip-box b, .tip-box strong { color: #7ec8f7 !important; }

/* Section headers */
.section-title {
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8faacc;
    margin: 1.4rem 0 0.5rem 0;
}

/* Reasoning row */
.reason-row {
    background: #131f2e;
    border-left: 3px solid #3d5a80;
    border-radius: 0 8px 8px 0;
    padding: 0.5rem 1rem;
    margin: 4px 0;
    color: #b0c8e8;
    font-size: 0.88rem;
}

hr.styled { border: none; border-top: 1px solid #1e2e40; margin: 1.2rem 0; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _go(view: str) -> None:
    st.session_state["view"] = view
    st.rerun()


def _gauge_chart(score: float, status: str) -> None:
    """Plotly donut-style gauge showing Understanding %."""
    import plotly.graph_objects as go

    color_map = {
        "Engaged":           "#2ecc71",
        "Partially Engaged": "#f39c12",
        "Disengaged":        "#e74c3c",
    }
    bar_color = color_map.get(status, "#7f8c8d")

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        delta={"reference": 75, "increasing": {"color": "#2ecc71"}, "decreasing": {"color": "#e74c3c"}},
        number={"suffix": "%", "font": {"size": 48, "color": "#ffffff"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#555", "tickwidth": 1,
                     "tickvals": [0, 25, 50, 75, 100],
                     "ticktext": ["0", "25", "50", "75", "100"]},
            "bar":  {"color": bar_color, "thickness": 0.28},
            "bgcolor": "#0e1824",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50],    "color": "#1a0a0a"},
                {"range": [50, 75],   "color": "#1a1000"},
                {"range": [75, 100],  "color": "#0a1a0f"},
            ],
            "threshold": {
                "line": {"color": "#ffffff", "width": 3},
                "thickness": 0.8,
                "value": 75,
            },
        },
        title={"text": "Understanding Score", "font": {"size": 16, "color": "#8faacc"}},
        domain={"x": [0, 1], "y": [0, 1]},
    ))
    fig.update_layout(
        paper_bgcolor="#0e1824",
        font_color="#ffffff",
        height=280,
        margin=dict(t=40, b=10, l=20, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)


def _delta_bar(student_score: float, class_mean: float) -> None:
    """Mini horizontal bar comparing student vs class average."""
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=["Class Avg", "Your Score"],
        x=[class_mean, student_score],
        orientation="h",
        marker_color=["#3d5a80", "#2ecc71" if student_score >= class_mean else "#e74c3c"],
        text=[f"{class_mean:.1f}%", f"{student_score:.1f}%"],
        textfont={"size": 13, "color": "#ffffff"},
        textposition="inside",
    ))
    fig.update_layout(
        paper_bgcolor="#0e1824",
        plot_bgcolor="#0e1824",
        font_color="#ffffff",
        xaxis=dict(range=[0, 105], showgrid=False, zeroline=False,
                   ticksuffix="%", color="#8faacc"),
        yaxis=dict(showgrid=False, color="#c9e4fa"),
        height=140,
        margin=dict(t=10, b=10, l=10, r=20),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _improvement_tip(status: str, missing: list[str], score: float, reason: str) -> str:
    if score == 0 and ("Mimics" in reason or "Source:" in reason):
        return "<strong>CRITICAL:</strong> This submission was flagged for invalidity (potential mimicry or copying). Please provide an original explanation in your own words to receive credit."
    if status == "Engaged":
        return "Excellent understanding demonstrated. Consider exploring advanced applications of this concept and connecting it to related topics."
    if missing:
        sample = " | ".join(f"<b>{m}</b>" for m in missing[:3])
        return f"To strengthen your score, focus on these specific concept areas: {sample}. Try to explain each in your own words before the next session."
    if status == "Partially Engaged":
        return "Good start — your response captured some key ideas. Be more specific and include core terminology to push into the Engaged zone."
    return "This topic needs more attention. Re-read the material, write one clear sentence explaining the core concept, and use technical vocabulary in your next response."


# ── View: Entry ───────────────────────────────────────────────────────────────

def show_entry() -> None:
    st.markdown("## 📝 Student Learning Portal")
    st.markdown("Enter the **session code** your teacher shared, then your name.")
    st.divider()

    with st.form("entry_form"):
        raw_code = st.text_input("Session Code", placeholder="6-character code (e.g. AB3X7Y)", max_chars=6)
        name     = st.text_input("Your Full Name", placeholder="e.g. Alice Sharma")
        go       = st.form_submit_button("Continue →", use_container_width=True)

    if go:
        code = raw_code.strip().upper()
        name = name.strip()
        if not code:
            st.error("Please enter the session code."); return
        if len(code) != 6:
            st.error("Session code must be exactly 6 characters."); return
        if not name:
            st.error("Please enter your name."); return

        session = svc.get_session(code)
        if session is None:
            st.error(f"No session found for code **{code}**."); return
        if not session["is_active"]:
            st.error(f"Session **{code}** has been closed."); return

        st.session_state["session"]      = session
        st.session_state["student_name"] = name
        _go("answer")


# ── View: Answer ──────────────────────────────────────────────────────────────

def show_answer() -> None:
    session = st.session_state["session"]
    name    = st.session_state["student_name"]

    st.markdown(f"## 👋 Hello, **{name}**!")
    st.markdown(f"**Topic:** {session['topic'].title()}")
    st.divider()
    st.markdown("### 📌 Question")
    st.info(session["question"])
    st.markdown("### ✍️ Your Answer")
    st.caption("Use subject-specific terminology. Your response is evaluated for concept mastery — not graded.")

    with st.form("answer_form"):
        response = st.text_area("Answer", placeholder="Type your answer here…", height=160,
                                label_visibility="collapsed")
        submit   = st.form_submit_button("✅ Submit Answer", use_container_width=True, type="primary")

    if submit:
        if not response.strip():
            st.warning("Please write an answer before submitting."); return

        with st.spinner("Evaluating your response…"):
            success, message, score, status, reason, missing_kw_text = svc.submit_student_response(
                session["session_code"], name, response.strip(),
                topic=session["topic"], threshold=session["threshold"],
            )

        if success:
            st.session_state["result"] = {
                "score":            score,
                "status":           status,
                "reason":           reason,
                "response":         response.strip(),
                "missing_keywords": [k for k in missing_kw_text.split(" | ") if k],
            }
            _go("confirmation")
        else:
            st.error(f"⚠️ {message}")


# ── View: Confirmation ────────────────────────────────────────────────────────

def show_confirmation() -> None:
    result  = st.session_state["result"]
    name    = st.session_state["student_name"]
    session = st.session_state["session"]
    status  = result["status"]
    score   = result["score"]
    reason  = result.get("reason", "")
    missing = result["missing_keywords"]

    st.markdown(f"## ✅ Submitted — {name}")
    st.divider()

    # ── Gauge chart ──────────────────────────────────────────────────────────
    _gauge_chart(score, status)

    # ── Status badge ─────────────────────────────────────────────────────────
    css = {"Engaged": "engaged-card", "Partially Engaged": "partial-card",
           "Disengaged": "disengaged-card"}.get(status, "partial-card")
    icon = {"Engaged": "🟢", "Partially Engaged": "🟡", "Disengaged": "🔴"}.get(status, "⚪")
    st.markdown(
        f'<div class="score-badge {css}">'
        f'<span class="big-num">{score}%</span>'
        f'<span class="tag">{icon} {status}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Class comparison bar ──────────────────────────────────────────────────
    summary    = svc.get_session_summary(session["session_code"])
    class_mean = summary.get("mean_score", 0.0)
    delta      = round(score - class_mean, 2)
    delta_str  = f"+{delta}%" if delta >= 0 else f"{delta}%"

    st.markdown('<p class="section-title">📊 Your Score vs Class Average</p>', unsafe_allow_html=True)
    _delta_bar(score, class_mean)

    # Metric strip
    delta_cls = "up" if delta >= 0 else "down"
    std       = summary.get("std_score", 0.0)
    st.markdown(
        f'<div class="metric-strip">'
        f'<div class="metric-box"><div class="m-label">Your Score</div><div class="m-value">{score}%</div></div>'
        f'<div class="metric-box"><div class="m-label">Class Avg</div><div class="m-value">{class_mean}%</div></div>'
        f'<div class="metric-box"><div class="m-label">vs Class</div><div class="m-value {delta_cls}">{delta_str}</div></div>'
        f'<div class="metric-box"><div class="m-label">Std Dev</div><div class="m-value neu">±{std}%</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="styled">', unsafe_allow_html=True)

    # ── Weak concepts ─────────────────────────────────────────────────────────
    st.markdown('<p class="section-title">📌 Concepts to Strengthen</p>', unsafe_allow_html=True)
    
    if score == 0 and ("Mimics" in reason or "Source:" in reason):
        st.error("⚠️ **Submission Invalidated**: Copying or mimicry detected. Original thought is required for credit.")
    elif missing:
        chips = "".join(f'<span class="weak-chip">⚡ {kw}</span>' for kw in missing)
        st.markdown(f'<div class="chips-wrap">{chips}</div>', unsafe_allow_html=True)
        st.caption("These topic keywords were absent from your response — include them next time.")
    else:
        st.success("All expected concept areas were covered in your response.")

    st.markdown('<hr class="styled">', unsafe_allow_html=True)

    # ── Study tip ─────────────────────────────────────────────────────────────
    st.markdown('<p class="section-title">💡 Study Tip</p>', unsafe_allow_html=True)
    tip_html = _improvement_tip(status, missing, score, reason)
    st.markdown(f'<div class="tip-box">💡 {tip_html}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="styled">', unsafe_allow_html=True)

    # ── Scoring reasoning ─────────────────────────────────────────────────────
    if result["reason"]:
        with st.expander("📄 Scoring Signals", expanded=False):
            for r in result["reason"].split(", "):
                if r.strip():
                    st.markdown(f'<div class="reason-row">• {r.strip()}</div>',
                                unsafe_allow_html=True)

    st.caption(f"Session `{session['session_code']}` · Topic: **{session['topic'].title()}**")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Join another session", use_container_width=False):
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
