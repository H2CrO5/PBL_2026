"""Teacher question bank view."""

import streamlit as st

from ui.api_client import get, post


def _rubric_items(raw_text: str) -> list[str]:
    return [line.strip("- ").strip() for line in raw_text.splitlines() if line.strip()]


def _show_seed(seed: dict):
    seed_label = seed["seed_type"].replace("_", " ").title()
    st.markdown(f"**{seed['title']}**")
    st.caption(f"{seed_label} | {seed['difficulty']} | {seed['target_concept']} | {seed.get('lecture_title') or 'No lecture'}")
    st.markdown(seed["question_text"])
    with st.expander("Expected answer and rubric"):
        st.markdown(f"**Expected answer:** {seed['expected_answer']}")
        st.markdown("**Rubric:**")
        for item in seed["rubric"]:
            st.markdown(f"- {item}")
        if seed.get("notes"):
            st.markdown(f"**Notes:** {seed['notes']}")


def render():
    st.title("Question Bank")

    summary = get("/analytics/dashboard")
    lectures = get("/materials/lectures") or []
    if not summary or not lectures:
        st.info("No course materials available.")
        return

    lecture_labels = {f"Lecture {item['lecture_number']}: {item['title']}": item for item in lectures}
    selected_label = st.selectbox("Lecture", list(lecture_labels.keys()))
    selected_lecture = lecture_labels[selected_label]

    context = get(f"/questions/generation-context/{selected_lecture['id']}")
    if context:
        col1, col2, col3 = st.columns(3)
        col1.metric("Materials", len(context["material_titles"]))
        col2.metric("Weak Concepts", len(context["weak_concepts"]))
        col3.metric("Lecture Seeds", len(context["question_seeds"]))

    with st.form("create_question_seed"):
        st.subheader("Add Question Seed")
        title = st.text_input("Title", value=f"{selected_lecture['title']} checkpoint")
        target_concept = st.text_input("Target concept", value=context["weak_concepts"][0] if context and context["weak_concepts"] else "")
        col1, col2 = st.columns(2)
        seed_type = col1.selectbox("Seed type", ["base", "required", "rubric_seed"])
        difficulty = col2.selectbox("Difficulty", ["supportive", "balanced", "challenging"], index=1)
        question_text = st.text_area("Question", height=120)
        expected_answer = st.text_area("Expected answer", height=100)
        rubric_text = st.text_area(
            "Rubric",
            value="Correctly identifies inputs and outputs\nHandles the edge case\nExplains the reasoning clearly",
            height=100,
        )
        notes = st.text_area("Internal notes", height=80)
        submitted = st.form_submit_button("Save question seed", width="stretch")

    if submitted:
        rubric = _rubric_items(rubric_text)
        if not question_text.strip() or not expected_answer.strip() or not rubric:
            st.error("Question, expected answer, and rubric are required.")
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
                "notes": notes or None,
            })
            if result:
                st.success("Question seed saved.")
                st.rerun()

    st.divider()
    st.subheader("Generation Context")
    if context:
        left, right = st.columns(2)
        with left:
            st.markdown("**Materials**")
            for title in context["material_titles"]:
                st.markdown(f"- {title}")
        with right:
            st.markdown("**Current weak concepts**")
            for concept in context["weak_concepts"]:
                st.markdown(f"- {concept}")

    st.divider()
    st.subheader("Question Seeds")
    seeds = get("/questions") or []
    lecture_seeds = [seed for seed in seeds if seed["lecture_id"] == selected_lecture["id"]]
    if not lecture_seeds:
        st.info("No question seeds for this lecture yet.")
    for seed in lecture_seeds:
        with st.container(border=True):
            _show_seed(seed)
