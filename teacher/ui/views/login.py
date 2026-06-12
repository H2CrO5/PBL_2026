"""Teacher login view."""

import httpx
import streamlit as st

from config import API_BASE_URL


def render():
    st.title("Teacher Login")
    st.markdown("Use the demo teacher account to enter the Teacher Part.")

    with st.form("teacher_login"):
        teacher_code = st.text_input("Teacher ID", value="t2024001")
        password = st.text_input("Password", type="password", value="demo123")
        submitted = st.form_submit_button("Login", width="stretch")

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
                st.error(resp.json().get("detail", "Login failed"))
        except httpx.ConnectError:
            st.error("Cannot connect to teacher API server.")

    st.divider()
    st.caption("Demo account: t2024001 / demo123")
