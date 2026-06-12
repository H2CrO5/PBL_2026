"""Sidebar component for the teacher UI."""

import httpx
import streamlit as st

from config import API_BASE_URL


def render_sidebar() -> str:
    """Render navigation and return selected page."""
    with st.sidebar:
        st.title("🎓 Teacher Support")

        if st.session_state.get("token"):
            teacher = st.session_state.get("teacher", {})
            st.markdown(f"**{teacher.get('name', '')}**")
            st.caption(teacher.get("teacher_code", ""))
            st.divider()

            pages = {
                "Dashboard": "dashboard",
                "Materials": "materials",
                "Question Bank": "assignment",
                "Analytics": "analytics",
                "Students": "students",
            }
            label = st.radio("Navigation", list(pages.keys()), label_visibility="collapsed")

            st.divider()
            if st.button("Logout", width="stretch"):
                try:
                    httpx.post(
                        f"{API_BASE_URL}/auth/logout",
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                        timeout=5.0,
                    )
                except Exception:
                    pass
                st.session_state.clear()
                st.rerun()

            return pages[label]

        return "login"
