"""Teacher login view."""

import httpx
import streamlit as st
from pathlib import Path

from config import API_BASE_URL
from ui.i18n import t

BRAND_DIR = Path(__file__).resolve().parents[3] / "assets" / "branding"
LOGO_PATH = BRAND_DIR / "classpilot-logo-light.png"


def render():
    left, center, right = st.columns([1, 2, 1])
    with center:
        st.image(str(LOGO_PATH), width="stretch")
        st.markdown(
            f"<h1 style='text-align: center;'>{t('teacher_login')}</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(t("login_intro"))

        with st.form("teacher_login"):
            teacher_code = st.text_input(t("teacher_id"), value="t2024001")
            password = st.text_input(t("password"), type="password", value="demo123")
            submitted = st.form_submit_button(t("login"), width="stretch")

    if submitted:
        try:
            resp = httpx.post(
                f"{API_BASE_URL}/auth/login",
                json={"teacher_code": teacher_code, "password": password},
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.token = data["token"]
                st.session_state.teacher = data["teacher"]
                st.rerun()
            else:
                st.error(resp.json().get("detail", t("login_failed")))
        except httpx.ConnectError:
            st.error(t("connection_error"))

    with center:
        st.divider()
        st.caption(t("demo_account"))
