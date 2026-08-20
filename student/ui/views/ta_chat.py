"""TA Bot chat page with RAG-based responses."""

import streamlit as st
import httpx
from urllib.parse import quote

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
    except httpx.ConnectError:
        st.error(t("api_connect_error"))
    except httpx.ReadTimeout:
        st.error(t("timeout_error"))
    return None


def _api_get(path: str) -> dict | None:
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


def _load_history(external_course_id: str):
    """Load only the selected course's chat history."""
    if st.session_state.get("chat_course_id") != external_course_id:
        path = f"/chat/history?limit=50&external_course_id={quote(external_course_id, safe='')}"
        data = _api_get(path)
        if data and data.get("messages"):
            st.session_state.chat_messages = [
                {"role": m["role"], "content": m["content"], "sources": m.get("sources")}
                for m in data["messages"]
            ]
        else:
            st.session_state.chat_messages = []
        st.session_state.chat_course_id = external_course_id


def render():
    """Render the TA Bot chat page."""
    st.title(t("ta_bot_title"))
    st.caption(t("ta_bot_caption"))

    courses = _api_get("/students/me/courses")
    if not courses:
        st.info(t("no_active_courses"))
        return
    labels = {f"{course['title']} ({course['term']})": course for course in courses}
    selected_label = st.selectbox(t("course_label"), list(labels))
    selected_course = labels[selected_label]
    external_course_id = selected_course["external_course_id"]

    _load_history(external_course_id)

    # Display chat messages
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources") and msg["role"] == "assistant":
                sources = msg["sources"]
                if sources:
                    source_names = set()
                    for s in sources:
                        if isinstance(s, dict):
                            source_names.add(s.get("source", ""))
                        elif isinstance(s, str):
                            source_names.add(s)
                    if source_names:
                        st.caption(f"{t('ta_bot_ref')}: {', '.join(source_names)}")

    # Chat input
    if prompt := st.chat_input(t("ta_bot_placeholder")):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt, "sources": None})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response
        with st.chat_message("assistant"):
            with st.spinner(t("ta_bot_thinking")):
                result = _api_post(
                    "/chat/message",
                    {"message": prompt, "external_course_id": external_course_id},
                )

            if result:
                st.markdown(result["content"])
                sources = result.get("sources", [])
                if sources:
                    source_names = set(s.get("source", "") for s in sources if isinstance(s, dict))
                    if source_names:
                        st.caption(f"{t('ta_bot_ref')}: {', '.join(source_names)}")

                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": result["content"],
                    "sources": sources,
                })
            else:
                st.error(t("ta_bot_response_error"))
