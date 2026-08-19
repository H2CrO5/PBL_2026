"""Individual student analysis view."""

import pandas as pd
import streamlit as st

from ui.api_client import get


def render():
    st.title("Individual Student Analysis")
    insights = get("/students/insights") or []
    if not insights:
        st.info("No student insights available.")
        return
    source_label = (
        "Live Student submissions"
        if insights[0].get("data_source") == "student-real-submissions"
        else "Demo analytics data"
    )
    st.caption(f"Data source: {source_label}")

    rows = [
        {
            "Student": f"{item['name']} ({item['student_code']})",
            "Average Score": item["average_score"],
            "Completion": item["completion_rate"],
            "Weak Topics": ", ".join(item["weak_topics"]),
            "Recommended Action": item["recommended_action"],
        }
        for item in insights
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    selected = st.selectbox("Inspect student", [row["Student"] for row in rows])
    item = insights[[row["Student"] for row in rows].index(selected)]
    col1, col2 = st.columns(2)
    col1.metric("Average Score", f"{item['average_score']:.1f}")
    col2.metric("Completion", f"{item['completion_rate']:.1f}%")
    st.markdown("**Strong topics**")
    for topic in item["strong_topics"]:
        st.markdown(f"- {topic}")
    st.markdown("**Weak topics**")
    for topic in item["weak_topics"]:
        st.markdown(f"- {topic}")
    st.info(item["recommended_action"])

    recent = item.get("recent_submissions", [])
    st.subheader("Recent Submissions")
    if not recent:
        st.info("No real submissions yet.")
    for submission in recent:
        icon = "✅" if submission["is_correct"] else "❌"
        with st.expander(
            f"{icon} {submission['topic']} — {submission['score']:.0f}/100"
        ):
            st.markdown(f"**Question:** {submission['question_text']}")
            st.markdown(f"**Student answer:** {submission['answer_text']}")
            st.markdown(f"**Feedback:** {submission['feedback']}")
            st.caption(f"Submitted: {submission['submitted_at']}")
