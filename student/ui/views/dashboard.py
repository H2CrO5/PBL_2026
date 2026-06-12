"""Dashboard page - simple welcome overview."""

import streamlit as st
import httpx

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from config import API_BASE_URL


def _api_get(path: str):
    """Helper to make authenticated GET requests."""
    try:
        resp = httpx.get(
            f"{API_BASE_URL}{path}",
            headers={"Authorization": f"Bearer {st.session_state.token}"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 401:
            st.warning("セッションが切れました。再ログインしてください。")
            st.session_state.clear()
            st.rerun()
        else:
            st.error(f"API error: {resp.status_code}")
    except httpx.ConnectError:
        st.error("APIサーバーに接続できません。")
    return None


def render():
    """Render the dashboard page."""
    student = st.session_state.get("student", {})
    st.title(f"ようこそ、{student.get('name', '')}さん")
    st.markdown("学習支援システムへようこそ。左のメニューから課題やTA Botを利用できます。")
