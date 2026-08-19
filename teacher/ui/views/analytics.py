"""Teacher analytics and lecture plan view."""

import streamlit as st

from ui.api_client import get, post


def render():
    st.title("Analytics and Lecture Improvement")
    summary = get("/analytics/dashboard")
    if not summary:
        return
    source_label = (
        "Live Student submissions"
        if summary.get("data_source") == "student-real-submissions"
        else "Demo analytics data (Student integration is not configured)"
    )
    st.caption(f"Data source: {source_label}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Average Score", f"{summary['average_score']:.1f}")
    col2.metric("Completion Rate", f"{summary['completion_rate']:.1f}%")
    col3.metric("Weak Concepts", len(summary["weak_concepts"]))

    evidence = get("/analytics/evidence") or []

    st.subheader("Incorrect Answer Trends")
    for concept in summary["weak_concepts"]:
        with st.container(border=True):
            st.markdown(f"**{concept['concept']}** — wrong rate: **{concept['wrong_rate']:.0f}%**")
            st.markdown(f"Misconception: {concept['misconception']}")
            st.markdown(f"Teaching focus: {concept['recommended_focus']}")

    st.subheader("Evidence View")
    if not evidence:
        st.info("No evidence data available.")
    for item in evidence:
        with st.expander(f"{item['concept']} — {item['confidence']}"):
            st.caption(item["evidence_status"])
            st.markdown("**Affected students**")
            for student in item["affected_students"]:
                st.markdown(f"- {student}")
            st.markdown("**Related question seeds**")
            if item["related_question_seeds"]:
                for seed in item["related_question_seeds"]:
                    st.markdown(f"- {seed}")
            else:
                st.markdown("- No related seed yet")
            st.markdown("**Typical evidence**")
            for error in item["typical_errors"]:
                st.markdown(f"- {error}")
            st.markdown(f"**Recommended action:** {item['recommended_action']}")

    st.subheader("Next Lecture Recommendation")
    if st.button("Generate lecture plan", width="stretch"):
        plan = post("/analytics/lecture-plan", {"course_id": summary["course_id"]})
        if plan:
            st.session_state.lecture_plan = plan

    plan = st.session_state.get("lecture_plan")
    if plan:
        st.markdown("**Opening activity**")
        st.info(plan["opening_activity"])
        st.markdown("**Weakest concepts**")
        for concept in plan["weakest_concepts"]:
            st.markdown(f"- {concept}")
        st.markdown("**Common misconceptions**")
        for item in plan["common_misconceptions"]:
            st.markdown(f"- {item}")
        st.markdown("**Recommended focus**")
        for item in plan["recommended_focus"]:
            st.markdown(f"- {item}")
        st.markdown("**Review sequence**")
        for item in plan["review_sequence"]:
            st.markdown(f"- {item}")
        st.markdown("**In-class check**")
        st.success(plan["in_class_check"])
        st.markdown("**Follow-up actions**")
        for item in plan["follow_up_actions"]:
            st.markdown(f"- {item}")
        if plan["recommended_seed_titles"]:
            st.markdown("**Recommended seeds**")
            for title in plan["recommended_seed_titles"]:
                st.markdown(f"- {title}")
        st.caption(plan["suggested_activity"])
