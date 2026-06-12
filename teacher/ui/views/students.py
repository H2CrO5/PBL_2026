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
