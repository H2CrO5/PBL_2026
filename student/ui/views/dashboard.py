"""Student progress dashboard backed by real submission APIs."""

import httpx
import pandas as pd
import streamlit as st

from config import API_BASE_URL
from ui.components.charts import accuracy_gauge, score_trend_chart, topic_bar_chart
from ui.i18n import t


def _api_get(path: str):
    try:
        response = httpx.get(
            f"{API_BASE_URL}{path}",
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=10.0,
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            st.warning(t("session_expired"))
            st.session_state.clear()
            st.rerun()
        st.error(response.json().get("detail", t("api_error")))
    except httpx.ConnectError:
        st.error(t("api_connect_error"))
    except httpx.ReadTimeout:
        st.error(t("timeout_error"))
    return None


def render():
    student = st.session_state.get("student", {})
    st.title(t("welcome_student", name=student.get("name", "")))
    st.caption(t("dashboard_caption"))

    summary = _api_get("/dashboard/summary")
    trends = _api_get("/dashboard/trends?days=30")
    memory = _api_get("/students/me/memory")
    if summary is None or trends is None or memory is None:
        return

    score_col, accuracy_col, answered_col, today_col = st.columns(4)
    score_col.metric(t("overall_score"), f"{summary['overall_score']:.1f}/100")
    accuracy_col.metric(t("accuracy"), f"{summary['accuracy']:.1f}%")
    answered_col.metric(t("answered"), summary["total_answered"])
    today_col.metric(
        t("today_progress"),
        f"{summary['today_correct']}/{summary['today_answered']}",
    )

    left, right = st.columns([2, 1])
    with left:
        if trends["daily_scores"]:
            st.plotly_chart(score_trend_chart(trends["daily_scores"]), width="stretch")
        else:
            st.info(t("no_trend_data"))
    with right:
        st.plotly_chart(accuracy_gauge(summary["accuracy"]), width="stretch")

    if trends["topic_trends"]:
        st.plotly_chart(topic_bar_chart(trends["topic_trends"]), width="stretch")

    if memory["concept_mastery"]:
        st.subheader(t("concept_mastery"))
        st.dataframe(
            pd.DataFrame([
                {
                    t("topic"): item["concept"],
                    t("mastery_score"): item["mastery_score"],
                    t("attempts"): item["attempts"],
                }
                for item in memory["concept_mastery"]
            ]),
            width="stretch",
            hide_index=True,
        )

    weak_col, strong_col = st.columns(2)
    with weak_col:
        st.subheader(t("weak_topics_title"))
        if summary["weak_topics"]:
            for topic in summary["weak_topics"]:
                st.markdown(f"- {topic}")
        else:
            st.info(t("no_weak_topics"))
    with strong_col:
        st.subheader(t("strong_topics_title"))
        if summary["strong_topics"]:
            for topic in summary["strong_topics"]:
                st.markdown(f"- {topic}")
        else:
            st.info(t("no_strong_topics"))
