"""Sidebar component with navigation, student info, language selector, and logout."""

import streamlit as st
import httpx

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config import API_BASE_URL
from ui.i18n import t

LOGO_PATH = Path(__file__).resolve().parents[3] / "assets" / "branding" / "classpilot-logo-light.png"


def render_sidebar():
    """Render the sidebar and return the selected page key."""
    with st.sidebar:
        st.image(str(LOGO_PATH), width="stretch")
        st.caption(f"Student · {t('app_title')}")

        if "token" in st.session_state and st.session_state.token:
            student = st.session_state.get("student", {})
            st.markdown(f"**{student.get('name', '')}** ({student.get('student_code', '')})")
            st.divider()

            page_keys = ["dashboard", "assignments", "ta_bot"]
            page_labels = [
                t("page_dashboard"),
                t("page_assignments"),
                t("page_ta_bot"),
            ]

            selected_label = st.radio(
                t("page_label"),
                page_labels,
                label_visibility="collapsed",
            )

            page = page_keys[page_labels.index(selected_label)]

            st.divider()
            if st.button(t("logout"), use_container_width=True):
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

            return page
        else:
            return "login"
