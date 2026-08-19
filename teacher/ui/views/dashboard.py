"""Teacher dashboard view."""

import plotly.express as px
import streamlit as st

from ui.api_client import get
from ui.i18n import t


def render():
    st.title(t("class_dashboard"))
    summary = get("/analytics/dashboard")
    if not summary:
        st.info(t("no_dashboard"))
        return

    st.caption(summary["course_title"])
    source_label = (
        t("live_submissions")
        if summary.get("data_source") == "student-real-submissions"
        else t("demo_data_unconfigured")
    )
    st.caption(t("data_source", source=source_label))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("student_count"), summary["total_students"])
    col2.metric(t("average_score"), f"{summary['average_score']:.1f}")
    col3.metric(t("completion"), f"{summary['completion_rate']:.1f}%")
    col4.metric(t("question_seeds"), t("seed_total", total=summary["question_seed_count"], required=summary["required_question_count"]))

    actions = summary.get("teacher_actions", [])
    if actions:
        st.subheader(t("action_list"))
        for action in actions:
            with st.container(border=True):
                st.caption(action["priority"].upper())
                st.markdown(f"**{action['title']}**")
                st.markdown(action["reason"])
                st.markdown(t("next_step", step=action["next_step"]))

    if summary.get("score_trend"):
        st.subheader(t("score_trend"))
        trend = px.line(
            summary["score_trend"],
            x="date",
            y="average_score",
            markers=True,
            labels={
                "date": t("date"),
                "average_score": t("average_score"),
                "submissions": t("submissions"),
            },
            hover_data=["submissions"],
        )
        trend.update_yaxes(range=[0, 100])
        st.plotly_chart(trend, width="stretch")

    weak = summary["weak_concepts"]
    if weak:
        st.subheader(t("weak_concepts"))
        fig = px.bar(
            weak,
            x="concept",
            y="wrong_rate",
            text="wrong_rate",
            labels={"wrong_rate": t("wrong_rate"), "concept": t("concept")},
            color="wrong_rate",
            color_continuous_scale="Reds",
        )
        fig.update_layout(height=360, coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")

        st.subheader(t("lecture_focus"))
        for item in weak[:3]:
            st.markdown(f"- **{item['concept']}**: {item['recommended_focus']}")
