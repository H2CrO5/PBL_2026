"""Teacher analytics and lecture plan view."""

import streamlit as st

from ui.api_client import get, post


def render():
    st.title("Analytics and Lecture Improvement")
    summary = get("/analytics/dashboard")
    if not summary:
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Average Score", f"{summary['average_score']:.1f}")
    col2.metric("Completion Rate", f"{summary['completion_rate']:.1f}%")
    col3.metric("Weak Concepts", len(summary["weak_concepts"]))

    st.subheader("Incorrect Answer Trends")
    for concept in summary["weak_concepts"]:
        with st.container(border=True):
            st.markdown(f"**{concept['concept']}** — wrong rate: **{concept['wrong_rate']:.0f}%**")
            st.markdown(f"Misconception: {concept['misconception']}")
            st.markdown(f"Teaching focus: {concept['recommended_focus']}")

    st.subheader("Next Lecture Recommendation")
    if st.button("Generate lecture plan", width="stretch"):
        plan = post("/analytics/lecture-plan", {"course_id": summary["course_id"]})
        if plan:
            st.session_state.lecture_plan = plan

    plan = st.session_state.get("lecture_plan")
    if plan:
        st.markdown("**Weakest concepts**")
        for concept in plan["weakest_concepts"]:
            st.markdown(f"- {concept}")
        st.markdown("**Common misconceptions**")
        for item in plan["common_misconceptions"]:
            st.markdown(f"- {item}")
        st.markdown("**Recommended focus**")
        for item in plan["recommended_focus"]:
            st.markdown(f"- {item}")
        st.info(plan["suggested_activity"])
