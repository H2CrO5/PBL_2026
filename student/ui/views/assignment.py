"""Assignment page: browse assignments grouped by lecture, answer, and get feedback."""

import streamlit as st
import httpx

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config import API_BASE_URL
from ui.i18n import t


def _api_post(path: str, json_data: dict) -> dict | None:
    try:
        resp = httpx.post(
            f"{API_BASE_URL}{path}",
            json=json_data,
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=30.0,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 401:
            st.warning(t("session_expired"))
            st.session_state.clear()
            st.rerun()
        else:
            detail = resp.json().get("detail", t("api_error"))
            st.error(detail)
    except httpx.ConnectError:
        st.error(t("api_connect_error"))
    except httpx.ReadTimeout:
        st.error(t("timeout_error"))
    return None


def _api_get(path: str) -> dict | list | None:
    try:
        resp = httpx.get(
            f"{API_BASE_URL}{path}",
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 401:
            st.warning(t("session_expired"))
            st.session_state.clear()
            st.rerun()
    except httpx.ConnectError:
        st.error(t("api_connect_error"))
    return None


def _diff_label(key: str) -> str:
    return t(key) if key in ("easy", "medium", "hard") else key


def _qtype_label(key: str) -> str:
    return t(key) if key in ("multiple_choice", "short_answer", "code") else key


def render():
    """Render the assignment page."""
    st.title(t("assignments_title"))

    # If answering a specific assignment, show that
    assignment = st.session_state.get("current_assignment")
    if assignment:
        submission = st.session_state.get("submission_result")
        if submission:
            _render_feedback(assignment, submission)
        else:
            _render_question(assignment)
        return

    # If viewing TA Bot for a completed assignment
    if st.session_state.get("history_chat_assignment"):
        _render_history_chat()
        return

    # Otherwise show pending + history tabs
    tab_pending, tab_history = st.tabs([t("tab_pending"), t("tab_history")])

    with tab_pending:
        _render_pending_by_lecture()

    with tab_history:
        _render_history()


def _render_pending_by_lecture():
    """Show pending assignments grouped by lecture."""
    data = _api_get("/assignments/pending/by-lecture")
    if data is None:
        return

    if not data:
        st.info(t("no_pending"))
        return

    total = sum(len(group["assignments"]) for group in data)
    st.markdown(f"**{t('pending_count', count=total)}**")

    for group in data:
        lecture = group["lecture"]
        assignments = group["assignments"]
        lecture_num = lecture["lecture_number"]
        title = lecture["title"]

        deadline_str = ""
        if lecture.get("deadline"):
            deadline_str = f"　({t('deadline')}: {lecture['deadline'][:10]})"

        lec_prefix = t("lecture_prefix", n=lecture_num)
        with st.expander(f"{lec_prefix}: {title}{deadline_str} — {len(assignments)}{t('items_suffix')}", expanded=True):
            if lecture.get("description"):
                st.caption(lecture["description"])

            for a in assignments:
                diff = _diff_label(a["difficulty"])
                qtype = _qtype_label(a["question_type"])

                with st.container(border=True):
                    col_info, col_btn = st.columns([4, 1])
                    with col_info:
                        st.markdown(f"**{a['topic']}**　`{diff}`　`{qtype}`")
                        if a.get("max_attempts", 1) > 1:
                            st.caption(
                                f"Attempt {a.get('attempts_used', 0) + 1} of {a['max_attempts']}"
                            )
                        st.caption(a["question_text"][:80] + ("..." if len(a["question_text"]) > 80 else ""))
                    with col_btn:
                        if st.button(t("answer_button"), key=f"start_{a['id']}", use_container_width=True):
                            st.session_state.current_assignment = a
                            st.session_state.submission_result = None
                            st.rerun()


def _render_question(assignment: dict):
    """Show the assignment question and answer form."""
    diff = _diff_label(assignment["difficulty"])
    qtype = _qtype_label(assignment["question_type"])

    if st.button(t("back_to_list")):
        st.session_state.current_assignment = None
        st.session_state.submission_result = None
        st.rerun()

    st.subheader(t("question_header"))
    st.markdown(f"**{t('topic_label')}**: {assignment['topic']}　|　**{t('difficulty_label')}**: {diff}　|　**{t('format_label')}**: {qtype}")
    st.markdown(assignment["question_text"])

    choices = assignment.get("choices")

    with st.form("answer_form"):
        if choices and assignment["question_type"] == "multiple_choice":
            answer = st.radio(t("select_answer"), choices)
        elif assignment["question_type"] == "code":
            answer = st.text_area(t("enter_code"), height=150)
        else:
            answer = st.text_area(t("enter_answer"), height=100)

        submitted = st.form_submit_button(t("submit_answer"), use_container_width=True)

    if submitted:
        if not answer:
            st.warning(t("answer_empty_warning"))
            return
        with st.spinner(t("grading_spinner")):
            result = _api_post(
                "/assignments/submit",
                {"assignment_id": assignment["id"], "answer_text": answer},
            )
            if result:
                st.session_state.submission_result = result
                me = _api_get("/auth/me")
                if me:
                    st.session_state.student = me
                st.rerun()


def _render_feedback(assignment: dict, submission: dict):
    """Show grading feedback after submission."""
    if st.button(t("back_to_list")):
        st.session_state.current_assignment = None
        st.session_state.submission_result = None
        st.rerun()

    st.subheader(t("result_header"))

    if submission["is_correct"]:
        st.success(t("correct_msg", score=submission["score"]))
    else:
        st.error(t("incorrect_msg", score=submission["score"]))

    st.markdown(f"**{t('feedback_label')}**")
    st.markdown(submission["feedback"])
    if submission.get("attempts_remaining", 0):
        st.info(f"You can retry {submission['attempts_remaining']} more time(s).")

    with st.expander(t("show_answer")):
        st.markdown(f"**{t('correct_answer_label')}** {submission['correct_answer']}")
        st.markdown(f"**{t('explanation_label')}** {submission['explanation']}")


def _render_history():
    """Show submission history grouped by lecture."""
    data = _api_get("/assignments/history/by-lecture")
    if not data:
        st.info(t("no_history"))
        return

    total = sum(len(group["submissions"]) for group in data)
    st.markdown(f"**{t('history_count', count=total)}**")

    for group in data:
        lecture = group["lecture"]
        submissions = group["submissions"]
        lecture_num = lecture["lecture_number"]
        title = lecture["title"]

        correct_count = sum(1 for s in submissions if s["is_correct"])
        lec_prefix = t("lecture_prefix", n=lecture_num)

        with st.expander(
            f"{lec_prefix}: {title} — {correct_count}/{len(submissions)} {t('correct_suffix')}",
            expanded=False,
        ):
            for item in submissions:
                diff = _diff_label(item["difficulty"])
                icon = "✅" if item["is_correct"] else "❌"

                with st.container(border=True):
                    col_info, col_btn = st.columns([4, 1])
                    with col_info:
                        st.markdown(
                            f"{icon} **{item['topic']}**　`{diff}`　"
                            f"{t('score_label')}: **{item['score']:.0f}**/100"
                        )
                        st.caption(item["question_text"][:80] + ("..." if len(item["question_text"]) > 80 else ""))
                    with col_btn:
                        if st.button(t("ask_ta_bot"), key=f"tachat_{item['id']}", use_container_width=True):
                            st.session_state.history_chat_assignment = item
                            st.session_state.pop("assignment_chat_messages", None)
                            st.rerun()
                    with st.expander(t("show_details"), expanded=False):
                        st.markdown(f"**{t('your_answer')}** {item['answer_text']}")
                        st.markdown(f"**{t('feedback_label')}** {item['feedback']}")
                        st.markdown(f"**{t('submitted_at')}** {item['submitted_at']}")
                        st.caption(
                            f"Attempt {item.get('attempt_number', 1)} | "
                            f"Grading: {item.get('grading_source', 'auto')}"
                        )


def _render_history_chat():
    """Render TA Bot chat for a completed assignment."""
    item = st.session_state.history_chat_assignment

    if st.button(t("back_to_history")):
        st.session_state.pop("history_chat_assignment", None)
        st.session_state.pop("assignment_chat_messages", None)
        st.rerun()

    diff = _diff_label(item["difficulty"])
    icon = "✅" if item["is_correct"] else "❌"

    st.subheader(f"{icon} {item['topic']}　`{diff}`　{t('score_label')}: {item['score']:.0f}/100")
    st.markdown(item["question_text"])

    with st.expander(t("your_answer_feedback"), expanded=False):
        st.markdown(f"**{t('your_answer')}** {item['answer_text']}")
        st.markdown(f"**{t('feedback_label')}** {item['feedback']}")

    st.divider()
    st.markdown(f"**{t('ta_bot_assignment_header')}**")

    if "assignment_chat_messages" not in st.session_state:
        st.session_state.assignment_chat_messages = []

    for msg in st.session_state.assignment_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input(t("ta_bot_assignment_placeholder"), key="history_chat_input")
    if user_input:
        context_prefix = (
            f"[Question about an assignment]\n"
            f"Topic: {item['topic']}\n"
            f"Question: {item['question_text']}\n"
            f"Student answer: {item['answer_text']}\n"
            f"Score: {item['score']:.0f}/100\n"
            f"Feedback: {item['feedback']}\n\n"
            f"Student's question: {user_input}"
        )

        st.session_state.assignment_chat_messages.append(
            {"role": "user", "content": user_input}
        )

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner(t("ta_bot_thinking")):
                result = _api_post("/chat/message", {"message": context_prefix})

            if result:
                st.markdown(result["content"])
                st.session_state.assignment_chat_messages.append(
                    {"role": "assistant", "content": result["content"]}
                )
            else:
                st.error(t("ta_bot_response_error"))
