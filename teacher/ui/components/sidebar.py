"""Sidebar component for the teacher UI."""

import httpx
import streamlit as st
from pathlib import Path

from config import API_BASE_URL
from ui.i18n import t

LOGO_PATH = Path(__file__).resolve().parents[3] / "assets" / "branding" / "classpilot-logo-light.png"


def render_sidebar() -> str:
    """Render navigation and return selected page."""
    with st.sidebar:
        st.image(str(LOGO_PATH), width="stretch")
        st.caption(t("teacher_workspace"))

        if st.session_state.get("token"):
            teacher = st.session_state.get("teacher", {})
            st.markdown(f"**{teacher.get('name', '')}**")
            st.caption(teacher.get("teacher_code", ""))
            st.divider()

            pages = {
                t("dashboard"): "dashboard",
                t("materials"): "materials",
                t("question_bank"): "assignment",
                t("analytics"): "analytics",
                t("students"): "students",
            }
            label = st.radio("Navigation", list(pages.keys()), label_visibility="collapsed")

            st.divider()
            if st.button(t("logout"), width="stretch"):
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
