"""Teacher analytics and lecture plan view."""

import streamlit as st

from ui.api_client import get, post
from ui.i18n import t


def render():
    st.title(t("analytics_title"))
    summary = get("/analytics/dashboard")
    if not summary:
        return
    source_label = (
        t("live_submissions")
        if summary.get("data_source") == "student-real-submissions"
        else t("demo_data_unconfigured")
    )
    st.caption(t("data_source", source=source_label))

    col1, col2, col3 = st.columns(3)
    col1.metric(t("average_score"), f"{summary['average_score']:.1f}")
    col2.metric(t("completion_rate"), f"{summary['completion_rate']:.1f}%")
    col3.metric(t("weak_concepts"), len(summary["weak_concepts"]))

    st.subheader(t("assignment_analytics"))
    published = get("/assignments") or []
    if published:
        labels = {f"{item['title']} ({item['target_concept']})": item for item in published}
        selected = st.selectbox(t("select_assignment"), list(labels))
        assignment_result = get(f"/assignments/{labels[selected]['id']}/analytics")
        if assignment_result:
            a1, a2, a3, a4 = st.columns(4)
            a1.metric(t("assigned"), assignment_result["total_assigned"])
            a2.metric(t("submissions"), assignment_result["total_submitted"])
            a3.metric(t("average_score"), f"{assignment_result['average_score']:.1f}")
            a4.metric(t("wrong_rate_metric"), f"{assignment_result['wrong_rate']:.1f}%")
            if assignment_result["missing_concepts"]:
                st.markdown(f"**{t('missing_concepts')}**")
                for concept in assignment_result["missing_concepts"]:
                    st.markdown(f"- {concept}")
            if assignment_result["error_patterns"]:
                st.markdown(f"**{t('error_patterns')}**")
                for pattern in assignment_result["error_patterns"]:
                    st.markdown(f"- {pattern}")
    else:
        st.info(t("no_published_assignments"))

    evidence = get("/analytics/evidence") or []

    st.subheader(t("incorrect_trends"))
    for concept in summary["weak_concepts"]:
        with st.container(border=True):
            st.markdown(f"**{concept['concept']}** — {t('wrong_rate_line', rate=concept['wrong_rate'])}")
            st.markdown(f"{t('misconception')}: {concept['misconception']}")
            st.markdown(f"{t('teaching_focus')}: {concept['recommended_focus']}")

    st.subheader(t("evidence_view"))
    if not evidence:
        st.info(t("no_evidence"))
    for item in evidence:
        with st.expander(f"{item['concept']} — {item['confidence']}"):
            st.caption(item["evidence_status"])
            st.markdown(f"**{t('affected_students')}**")
            for student in item["affected_students"]:
                st.markdown(f"- {student}")
            st.markdown(f"**{t('related_seeds')}**")
            if item["related_question_seeds"]:
                for seed in item["related_question_seeds"]:
                    st.markdown(f"- {seed}")
            else:
                st.markdown(f"- {t('no_related_seed')}")
            st.markdown(f"**{t('typical_evidence')}**")
            for error in item["typical_errors"]:
                st.markdown(f"- {error}")
            st.markdown(f"**{t('recommended_action')}:** {item['recommended_action']}")

    st.subheader(t("next_lecture"))
    if st.button(t("generate_plan"), width="stretch"):
        plan = post("/analytics/lecture-plan", {"course_id": summary["course_id"]})
        if plan:
            st.session_state.lecture_plan = plan

    plan = st.session_state.get("lecture_plan")
    if plan:
        st.markdown(f"**{t('opening_activity')}**")
        st.info(plan["opening_activity"])
        st.markdown(f"**{t('weakest_concepts')}**")
        for concept in plan["weakest_concepts"]:
            st.markdown(f"- {concept}")
        st.markdown(f"**{t('common_misconceptions')}**")
        for item in plan["common_misconceptions"]:
            st.markdown(f"- {item}")
        st.markdown(f"**{t('recommended_focus')}**")
        for item in plan["recommended_focus"]:
            st.markdown(f"- {item}")
        st.markdown(f"**{t('review_sequence')}**")
        for item in plan["review_sequence"]:
            st.markdown(f"- {item}")
        st.markdown(f"**{t('in_class_check')}**")
        st.success(plan["in_class_check"])
        st.markdown(f"**{t('follow_up')}**")
        for item in plan["follow_up_actions"]:
            st.markdown(f"- {item}")
        if plan["recommended_seed_titles"]:
            st.markdown(f"**{t('recommended_seeds')}**")
            for title in plan["recommended_seed_titles"]:
                st.markdown(f"- {title}")
        st.caption(plan["suggested_activity"])
