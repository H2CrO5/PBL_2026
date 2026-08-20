"""Individual student analysis view."""

import pandas as pd
import streamlit as st

from ui.api_client import get, post
from ui.i18n import t


def render():
    st.title(t("student_analysis"))
    insights = get("/students/insights") or []
    if not insights:
        st.info(t("no_student_insights"))
        return
    data_source = insights[0].get("data_source")
    source_label = (
        t("submissions_with_seed") if data_source == "student-submissions-including-seed"
        else t("live_submissions") if data_source == "student-real-submissions"
        else t("demo_data")
    )
    st.caption(t("data_source", source=source_label))

    rows = [
        {
            t("student"): f"{item['name']} ({item['student_code']})",
            t("average_score"): item["average_score"],
            t("completion"): item["completion_rate"],
            t("weak_topics"): ", ".join(item["weak_topics"]),
            t("recommended_action"): item["recommended_action"],
        }
        for item in insights
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    student_column = t("student")
    selected = st.selectbox(t("inspect_student"), [row[student_column] for row in rows])
    item = insights[[row[student_column] for row in rows].index(selected)]
    col1, col2 = st.columns(2)
    col1.metric(t("average_score"), f"{item['average_score']:.1f}")
    col2.metric(t("completion"), f"{item['completion_rate']:.1f}%")
    st.markdown(f"**{t('strong_topics')}**")
    for topic in item["strong_topics"]:
        st.markdown(f"- {topic}")
    st.markdown(f"**{t('weak_topics')}**")
    for topic in item["weak_topics"]:
        st.markdown(f"- {topic}")
    st.info(item["recommended_action"])

    st.subheader(t("recent_questions"))
    if item.get("chat_summary"):
        for question in item["chat_summary"]:
            st.markdown(f"- {question}")
    else:
        st.info(t("no_questions"))

    recent = item.get("recent_submissions", [])
    st.subheader(t("recent_submissions"))
    if not recent:
        st.info(t("no_submissions"))
    for submission in recent:
        icon = "✅" if submission["is_correct"] else "❌"
        with st.expander(
            f"{icon} {submission['topic']} — {submission['score']:.0f}/100"
        ):
            st.markdown(f"**{t('question')}:** {submission['question_text']}")
            st.markdown(f"**{t('student_answer')}:** {submission['answer_text']}")
            st.markdown(f"**{t('feedback')}:** {submission['feedback']}")
            if submission.get("missing_concepts"):
                st.markdown(
                    f"**{t('missing_concepts')}:** " + ", ".join(submission["missing_concepts"])
                )
            if submission.get("teacher_error_pattern"):
                st.markdown(
                    f"**{t('error_pattern')}:** {submission['teacher_error_pattern']}"
                )
            st.caption(
                t("attempt_grading", attempt=submission.get("attempt_number", 1), source=submission.get("grading_source", "auto"))
            )
            if submission.get("source") == "seed":
                st.caption(t("sample_answer"))
            st.caption(t("submitted", date=submission["submitted_at"]))
            if submission.get("source") == "seed":
                continue
            with st.form(f"override_{submission['submission_id']}"):
                corrected_score = st.number_input(
                    t("corrected_score"),
                    min_value=0.0,
                    max_value=100.0,
                    value=float(submission["score"]),
                    key=f"score_{submission['submission_id']}",
                )
                corrected_feedback = st.text_area(
                    t("corrected_feedback"),
                    value=submission["feedback"],
                    key=f"feedback_{submission['submission_id']}",
                )
                override = st.form_submit_button(t("save_correction"))
            if override:
                result = post(
                    f"/students/submissions/{submission['submission_id']}/override",
                    {"score": corrected_score, "feedback": corrected_feedback},
                )
                if result:
                    st.success(t("correction_saved"))
                    st.rerun()
