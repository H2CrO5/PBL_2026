"""Teacher material management view."""

import streamlit as st

from config import MAX_MATERIAL_UPLOAD_BYTES
from ui.api_client import get, post, post_file
from ui.i18n import t, tv


def render():
    st.title(t("material_management"))
    st.markdown(t("material_intro"))

    summary = get("/analytics/dashboard")
    lectures = get("/materials/lectures") or []
    materials = get("/materials") or []

    with st.expander(t("add_material"), expanded=False):
        if not lectures:
            st.info(t("no_lectures"))
        else:
            lecture_labels = {
                t("lecture_label", number=lec["lecture_number"], title=lec["title"]): lec["id"]
                for lec in lectures
            }
            with st.form("add_material"):
                selected = st.selectbox(t("lecture"), list(lecture_labels.keys()))
                title = st.text_input(t("title"), value=t("default_material_title"))
                material_type = st.selectbox(
                    t("type"), ["note", "slide", "book"], format_func=tv
                )
                student_visible = st.checkbox(
                    t("student_visible"),
                    value=False,
                    help=t("student_visible_help"),
                )
                content = st.text_area(
                    t("content"),
                    value=t("default_material_content"),
                    height=160,
                )
                submitted = st.form_submit_button(t("add_material"), width="stretch")
            if submitted:
                if not summary:
                    st.error(t("course_unknown"))
                    return
                result = post("/materials", {
                    "course_id": summary["course_id"],
                    "lecture_id": lecture_labels[selected],
                    "title": title,
                    "material_type": material_type,
                    "audience": "student" if student_visible else "teacher",
                    "content": content,
                })
                if result:
                    st.success(t("material_added"))
                    st.rerun()

            st.markdown(f"**{t('upload_course_file')}**")
            upload_limit_mb = max(1, MAX_MATERIAL_UPLOAD_BYTES // (1024 * 1024))
            st.caption(t("upload_instructions", size=upload_limit_mb))
            upload = st.file_uploader(
                t("file_types"),
                type=["pdf", "pptx", "md", "txt"],
                max_upload_size=upload_limit_mb,
            )
            upload_title = st.text_input(t("upload_title"))
            upload_student_visible = st.checkbox(
                t("student_visible"),
                value=True,
                help=t("student_visible_help"),
                key="upload_student_visible",
            )
            if st.button(t("upload_index"), disabled=upload is None, width="stretch"):
                if not summary:
                    st.error(t("course_unknown"))
                else:
                    result = post_file(
                        "/materials/upload",
                        upload.name,
                        upload.getvalue(),
                        {
                            "course_id": str(summary["course_id"]),
                            "lecture_id": str(lecture_labels[selected]),
                            "title": upload_title,
                            "audience": (
                                "student" if upload_student_visible else "teacher"
                            ),
                        },
                    )
                    if result:
                        st.success(t("uploaded", status=tv(result["ingestion_status"])))
                        st.rerun()

    st.subheader(t("current_materials"))
    if not materials:
        st.info(t("no_materials"))
        return

    if st.button(t("sync_all_rag"), width="stretch"):
        result = post("/materials/sync-all", {}, timeout=300.0)
        if result:
            st.success(
                t("sync_result", synced=result["synced"], chunks=result["chunks"], failed=result["failed"])
            )
            st.rerun()

    for material in materials:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            col1.markdown(f"**{material['title']}**")
            col1.caption(material["lecture_title"])
            col2.code(tv(material["material_type"]))
            col3.info(tv(material["audience"]))
            col4.success(tv(material["ingestion_status"]))
            st.caption(material["content_preview"])
            target_audience = (
                "teacher" if material["audience"] == "student" else "student"
            )
            if st.button(
                (
                    t("make_teacher_only")
                    if target_audience == "teacher"
                    else t("make_student_visible")
                ),
                key=f"audience_material_{material['id']}",
                width="stretch",
            ):
                result = post(
                    f"/materials/{material['id']}/audience",
                    {"audience": target_audience},
                    timeout=120.0,
                )
                if result:
                    st.success(t("visibility_updated"))
                    st.rerun()
            if st.button(
                (
                    t("sync_rag")
                    if material["audience"] == "student"
                    else t("apply_teacher_only")
                ),
                key=f"sync_material_{material['id']}",
                width="stretch",
            ):
                result = post(f"/materials/{material['id']}/sync", {}, timeout=120.0)
                if result:
                    st.success(
                        t("indexed", chunks=result["chunk_count"], status=tv(result["ingestion_status"]))
                    )
                    st.rerun()
