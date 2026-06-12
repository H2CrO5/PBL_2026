"""Teacher material management view."""

import streamlit as st

from ui.api_client import get, post


def render():
    st.title("Material Management")
    st.markdown("Review seeded materials or add a local text material for smoke testing.")

    lectures = get("/materials/lectures") or []
    materials = get("/materials") or []

    with st.expander("Add Material", expanded=False):
        if not lectures:
            st.info("No lectures available.")
        else:
            lecture_labels = {
                f"Lecture {lec['lecture_number']}: {lec['title']}": lec["id"]
                for lec in lectures
            }
            with st.form("add_material"):
                selected = st.selectbox("Lecture", list(lecture_labels.keys()))
                title = st.text_input("Title", value="Teacher note: Evidence checklist")
                material_type = st.selectbox("Type", ["note", "slide", "book"])
                content = st.text_area(
                    "Content",
                    value="Students should verify whether each generated answer claim is supported by a retrieved source passage.",
                    height=160,
                )
                submitted = st.form_submit_button("Add material", width="stretch")
            if submitted:
                result = post("/materials", {
                    "course_id": 1,
                    "lecture_id": lecture_labels[selected],
                    "title": title,
                    "material_type": material_type,
                    "content": content,
                })
                if result:
                    st.success("Material added and marked ready.")
                    st.rerun()

    st.subheader("Current Materials")
    if not materials:
        st.info("No materials found.")
        return

    for material in materials:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.markdown(f"**{material['title']}**")
            col1.caption(material["lecture_title"])
            col2.code(material["material_type"])
            col3.success(material["ingestion_status"])
            st.caption(material["content_preview"])
