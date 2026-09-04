"""Student view for teacher-published course materials."""

from collections import defaultdict

import httpx
import streamlit as st

from config import API_BASE_URL
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
    st.title(t("materials_title"))
    st.caption(t("materials_caption"))

    courses = _api_get("/students/me/courses")
    if courses is None:
        return
    if not courses:
        st.info(t("no_active_courses"))
        return

    course_labels = {
        f"{course['title']} ({course['term']})": course["external_course_id"]
        for course in courses
    }
    selected_course = st.selectbox(t("course_label"), list(course_labels))
    external_course_id = course_labels[selected_course]
    rows = _api_get(f"/materials?external_course_id={external_course_id}")
    if rows is None:
        return
    if not rows:
        st.info(t("no_published_materials"))
        return

    grouped = defaultdict(list)
    for material in rows:
        key = (
            material.get("lecture_number") or 0,
            material.get("lecture_title") or t("other_materials"),
        )
        grouped[key].append(material)

    for (lecture_number, lecture_title), materials in sorted(grouped.items()):
        heading = (
            f"{t('lecture_prefix', n=lecture_number)}: {lecture_title}"
            if lecture_number else lecture_title
        )
        st.subheader(heading)
        for material in materials:
            with st.expander(f"{material['title']} · {t(material['material_type'])}"):
                st.markdown(material["content"])

