"""Teacher material management view."""

import streamlit as st

from ui.api_client import get, post, post_file
from ui.i18n import t


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
                f"Lecture {lec['lecture_number']}: {lec['title']}": lec["id"]
                for lec in lectures
            }
            with st.form("add_material"):
                selected = st.selectbox(t("lecture"), list(lecture_labels.keys()))
                title = st.text_input(t("title"), value="Teacher note: Evidence checklist")
                material_type = st.selectbox(t("type"), ["note", "slide", "book"])
                content = st.text_area(
                    t("content"),
                    value="Students should verify whether each generated answer claim is supported by a retrieved source passage.",
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
                    "content": content,
                })
                if result:
                    st.success(t("material_added"))
                    st.rerun()

            st.markdown(f"**{t('upload_course_file')}**")
            upload = st.file_uploader(
                t("file_types"),
                type=["pdf", "pptx", "md", "txt"],
            )
            upload_title = st.text_input(t("upload_title"))
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
                        },
                    )
                    if result:
                        st.success(t("uploaded", status=result["ingestion_status"]))
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
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.markdown(f"**{material['title']}**")
            col1.caption(material["lecture_title"])
            col2.code(material["material_type"])
            col3.success(material["ingestion_status"])
            st.caption(material["content_preview"])
            if st.button(
                t("sync_rag"),
                key=f"sync_material_{material['id']}",
                width="stretch",
            ):
                result = post(f"/materials/{material['id']}/sync", {}, timeout=120.0)
                if result:
                    st.success(
                        t("indexed", chunks=result["chunk_count"], status=result["ingestion_status"])
                    )
                    st.rerun()
