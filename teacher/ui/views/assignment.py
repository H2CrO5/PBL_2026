"""Teacher question bank view."""

import streamlit as st

from ui.api_client import get, post
from ui.i18n import t


def _rubric_items(raw_text: str) -> list[str]:
    return [line.strip("- ").strip() for line in raw_text.splitlines() if line.strip()]


def _show_seed(seed: dict):
    seed_label = seed["seed_type"].replace("_", " ").title()
    st.markdown(f"**{seed['title']}**")
    st.caption(f"{seed_label} | {seed['difficulty']} | {seed['target_concept']} | {seed.get('lecture_title') or t('no_lecture')}")
    st.markdown(seed["question_text"])
    with st.expander(t("answer_rubric")):
        st.markdown(f"**{t('expected_answer')}:** {seed['expected_answer']}")
        st.markdown(f"**{t('rubric')}:**")
        for item in seed["rubric"]:
            st.markdown(f"- {item}")
        if seed.get("notes"):
            st.markdown(f"**{t('notes')}:** {seed['notes']}")


def _control_notes(scope: str, variation_policy: str, priority: str, notes: str) -> str:
    controls = [
        f"Assessment scope: {scope}",
        f"Variation policy: {variation_policy}",
        f"Teacher priority: {priority}",
    ]
    if notes.strip():
        controls.append(notes.strip())
    return "\n".join(controls)


def render():
    st.title(t("question_bank"))

    summary = get("/analytics/dashboard")
    lectures = get("/materials/lectures") or []
    if not summary or not lectures:
        st.info(t("no_course_materials"))
        return

    lecture_labels = {f"Lecture {item['lecture_number']}: {item['title']}": item for item in lectures}
    selected_label = st.selectbox(t("lecture"), list(lecture_labels.keys()))
    selected_lecture = lecture_labels[selected_label]

    context = get(f"/questions/generation-context/{selected_lecture['id']}")
    if context:
        col1, col2, col3 = st.columns(3)
        col1.metric(t("materials_count"), len(context["materials"]))
        col2.metric(t("weak_concepts"), len(context["weak_concepts"]))
        col3.metric(t("lecture_seeds"), len(context["question_seeds"]))

        readiness_label = t("ready_handoff") if context["ready_for_generation"] else t("needs_review")
        st.subheader(t("generation_readiness"))
        st.caption(readiness_label)
        for check in context["readiness_checks"]:
            with st.container(border=True):
                st.markdown(f"**{check['name']}**")
                st.caption(check["status"].upper())
                st.markdown(check["detail"])
        if st.button(
            t("generate_bedrock"),
            disabled=not bool(context["materials"]),
            width="stretch",
        ):
            generated = post(
                "/questions/generate",
                {
                    "course_id": summary["course_id"],
                    "lecture_id": selected_lecture["id"],
                    "target_concept": (
                        context["weak_concepts"][0]
                        if context["weak_concepts"] else selected_lecture["title"]
                    ),
                    "difficulty": "balanced",
                    "points": 100,
                    "max_attempts": 1,
                },
                timeout=120.0,
            )
            if generated:
                st.success(t("draft_saved"))
                st.rerun()

    with st.form("create_question_seed"):
        st.subheader(t("add_seed"))
        title = st.text_input(t("title"), value=f"{selected_lecture['title']} checkpoint")
        target_concept = st.text_input(t("target_concept"), value=context["weak_concepts"][0] if context and context["weak_concepts"] else "")
        col1, col2 = st.columns(2)
        seed_type = col1.selectbox(t("seed_type"), ["base", "required", "rubric_seed"])
        difficulty = col2.selectbox(t("difficulty"), ["supportive", "balanced", "challenging"], index=1)
        question_text = st.text_area(t("question"), height=120)
        expected_answer = st.text_area(t("expected_answer"), height=100)
        rubric_text = st.text_area(
            t("rubric"),
            value="Correctly identifies inputs and outputs\nHandles the edge case\nExplains the reasoning clearly",
            height=100,
        )
        points_col, attempts_col = st.columns(2)
        points = points_col.number_input(t("points"), min_value=1, max_value=1000, value=100)
        max_attempts = attempts_col.number_input(
            t("max_attempts"), min_value=1, max_value=10, value=1
        )
        control_col1, control_col2, control_col3 = st.columns(3)
        assessment_scope = control_col1.selectbox(t("assessment_scope"), ["practice_only", "formative_checkpoint", "exam_relevant"], index=1)
        variation_policy = control_col2.selectbox(t("variation_policy"), ["allow_variants", "teacher_review_required", "do_not_generate_variants"], index=1)
        teacher_priority = control_col3.selectbox(t("teacher_priority"), ["normal", "high", "critical"])
        notes = st.text_area(t("internal_notes"), height=80)
        submitted = st.form_submit_button(t("save_seed"), width="stretch")

    if submitted:
        rubric = _rubric_items(rubric_text)
        if not question_text.strip() or not expected_answer.strip() or not rubric:
            st.error(t("required_fields"))
        else:
            result = post("/questions", {
                "course_id": summary["course_id"],
                "lecture_id": selected_lecture["id"],
                "title": title,
                "target_concept": target_concept,
                "seed_type": seed_type,
                "difficulty": difficulty,
                "question_text": question_text,
                "expected_answer": expected_answer,
                "rubric": rubric,
                "points": points,
                "max_attempts": max_attempts,
                "notes": _control_notes(assessment_scope, variation_policy, teacher_priority, notes),
            })
            if result:
                st.success(t("seed_saved"))
                st.rerun()

    st.divider()
    st.subheader(t("generation_context"))
    if context:
        left, right = st.columns(2)
        with left:
            st.markdown(f"**{t('materials')}**")
            for material in context["materials"]:
                st.markdown(
                    f"- #{material['id']} {material['title']} "
                    f"({material['material_type']}, {material['ingestion_status']})"
                )
        with right:
            st.markdown(f"**{t('current_weak')}**")
            for concept in context["weak_concepts"]:
                st.markdown(f"- {concept}")

    if context and context["question_seed_candidates"]:
        st.divider()
        st.subheader(t("candidate_seeds"))
        for index, candidate in enumerate(context["question_seed_candidates"]):
            with st.container(border=True):
                st.markdown(f"**{candidate['title']}**")
                st.caption(
                    f"{candidate['seed_type']} | {candidate['difficulty']} | "
                    f"{candidate['assessment_scope']} | {candidate['variation_policy']}"
                )
                st.markdown(candidate["question_text"])
                with st.expander(t("candidate_details")):
                    st.markdown(f"**{t('expected_answer')}:** {candidate['expected_answer']}")
                    st.markdown(f"**{t('rubric')}:**")
                    for item in candidate["rubric"]:
                        st.markdown(f"- {item}")
                    st.markdown(f"**{t('rationale')}:** {candidate['rationale']}")
                if st.button(t("save_candidate"), key=f"save_candidate_{selected_lecture['id']}_{index}", width="stretch"):
                    saved = post("/questions", {
                        "course_id": summary["course_id"],
                        "lecture_id": selected_lecture["id"],
                        "title": candidate["title"],
                        "target_concept": candidate["target_concept"],
                        "seed_type": candidate["seed_type"],
                        "difficulty": candidate["difficulty"],
                        "question_text": candidate["question_text"],
                        "expected_answer": candidate["expected_answer"],
                        "rubric": candidate["rubric"],
                        "points": 100,
                        "max_attempts": 1,
                        "notes": candidate["notes"],
                    })
                    if saved:
                        st.success(t("candidate_saved"))
                        st.rerun()

    st.divider()
    st.subheader(t("question_seeds"))
    seeds = get("/questions") or []
    lecture_seeds = [seed for seed in seeds if seed["lecture_id"] == selected_lecture["id"]]
    if not lecture_seeds:
        st.info(t("no_seeds"))
    for seed in lecture_seeds:
        with st.container(border=True):
            _show_seed(seed)
            st.caption(
                t("seed_summary", points=seed.get("points", 100), attempts=seed.get("max_attempts", 1))
            )
            if st.button(
                t("publish_student"),
                key=f"publish_seed_{seed['id']}",
                width="stretch",
            ):
                result = post(f"/questions/{seed['id']}/publish", {})
                if result:
                    st.success(
                        t("published", created=result["created_for_students"], existing=result["already_present"])
                    )
