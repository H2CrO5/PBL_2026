"""Read-only viewer for lecture materials published by the teacher."""

from collections import OrderedDict

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

    groups = _api_get("/materials")
    if groups is None:
        return
    if not groups:
        st.info(t("no_materials"))
        return

    by_course = OrderedDict()
    for group in groups:
        course_key = group["external_course_id"]
        by_course.setdefault(
            course_key,
            {
                "title": group["course_title"],
                "term": group["term"],
                "lectures": [],
            },
        )["lectures"].append(group)

    for course in by_course.values():
        st.subheader(course["title"])
        if course["term"] and course["term"] != "unspecified":
            st.caption(course["term"])

        for group in course["lectures"]:
            if group["lecture_number"] is None:
                lecture_heading = t("general_materials")
            else:
                prefix = t("lecture_prefix", n=group["lecture_number"])
                lecture_heading = f"{prefix} — {group['lecture_title']}"
            st.markdown(f"### {lecture_heading}")

            for material in group["materials"]:
                type_key = f"material_type_{material['material_type']}"
                type_label = t(type_key)
                if type_label == type_key:
                    type_label = material["material_type"].upper()
                with st.expander(f"{material['title']} · {type_label}"):
                    st.markdown(material["content"])
                    st.download_button(
                        t("download_material_text"),
                        data=material["content"],
                        file_name=f"material-{material['id']}.txt",
                        mime="text/plain",
                        key=f"material_download_{material['id']}",
                    )
