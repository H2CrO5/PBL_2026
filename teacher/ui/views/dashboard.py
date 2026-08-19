"""Teacher dashboard view."""

import plotly.express as px
import streamlit as st

from ui.api_client import get


def render():
    st.title("Class Dashboard")
    summary = get("/analytics/dashboard")
    if not summary:
        st.info("No dashboard data available.")
        return

    st.caption(summary["course_title"])
    source_label = (
        "Live Student submissions"
        if summary.get("data_source") == "student-real-submissions"
        else "Demo analytics data (Student integration is not configured)"
    )
    st.caption(f"Data source: {source_label}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Students", summary["total_students"])
    col2.metric("Average Score", f"{summary['average_score']:.1f}")
    col3.metric("Completion", f"{summary['completion_rate']:.1f}%")
    col4.metric("Question Seeds", f"{summary['question_seed_count']} total / {summary['required_question_count']} required")

    actions = summary.get("teacher_actions", [])
    if actions:
        st.subheader("Teacher Action List")
        for action in actions:
            with st.container(border=True):
                st.caption(action["priority"].upper())
                st.markdown(f"**{action['title']}**")
                st.markdown(action["reason"])
                st.markdown(f"Next step: {action['next_step']}")

    weak = summary["weak_concepts"]
    if weak:
        st.subheader("Weak Concepts")
        fig = px.bar(
            weak,
            x="concept",
            y="wrong_rate",
            text="wrong_rate",
            labels={"wrong_rate": "Wrong Rate (%)", "concept": "Concept"},
            color="wrong_rate",
            color_continuous_scale="Reds",
        )
        fig.update_layout(height=360, coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")

        st.subheader("Recommended Lecture Focus")
        for item in weak[:3]:
            st.markdown(f"- **{item['concept']}**: {item['recommended_focus']}")
