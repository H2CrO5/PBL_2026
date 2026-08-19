"""Login page."""

import streamlit as st
import httpx

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config import API_BASE_URL
from ui.i18n import t

BRAND_DIR = Path(__file__).resolve().parents[3] / "assets" / "branding"
LOGO_PATH = BRAND_DIR / "classpilot-logo-light.png"


def render():
    """Render the login form."""
    left, center, right = st.columns([1, 2, 1])
    with center:
        st.image(str(LOGO_PATH), width="stretch")
        st.markdown(
            f"<h1 style='text-align: center;'>{t('login_title')}</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(t("login_instruction"))

        with st.form("login_form"):
            student_code = st.text_input(t("student_id"), value="s2024001")
            password = st.text_input(t("password"), type="password", value="demo123")
            submitted = st.form_submit_button(t("login_button"), use_container_width=True)

    if submitted:
        if not student_code or not password:
            st.error(t("login_empty_error"))
            return

        try:
            resp = httpx.post(
                f"{API_BASE_URL}/auth/login",
                json={"student_code": student_code, "password": password},
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.token = data["token"]
                st.session_state.student = data["student"]
                st.rerun()
            else:
                detail = resp.json().get("detail", t("login_failed"))
                st.error(detail)
        except httpx.ConnectError:
            st.error(t("login_connect_error"))
        except Exception as e:
            st.error(f"{t('login_error')}: {e}")

    with center:
        st.divider()
        st.caption(t("demo_account"))
