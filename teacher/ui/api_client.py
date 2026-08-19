"""HTTP helpers for Streamlit -> FastAPI calls."""

from typing import Any

import httpx
import streamlit as st

from config import API_BASE_URL


def auth_headers() -> dict[str, str]:
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def get(path: str, timeout: float = 10.0) -> Any | None:
    try:
        resp = httpx.get(f"{API_BASE_URL}{path}", headers=auth_headers(), timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 401:
            st.warning("Session expired. Please log in again.")
            st.session_state.clear()
            st.rerun()
        st.error(resp.json().get("detail", f"API error: {resp.status_code}"))
    except httpx.ConnectError:
        st.error("Cannot connect to teacher API server.")
    except httpx.ReadTimeout:
        st.error("Request timed out.")
    return None


def post(path: str, json_data: dict | None = None, timeout: float = 20.0) -> Any | None:
    try:
        resp = httpx.post(
            f"{API_BASE_URL}{path}",
            json=json_data or {},
            headers=auth_headers(),
            timeout=timeout,
        )
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 401:
            st.warning("Session expired. Please log in again.")
            st.session_state.clear()
            st.rerun()
        st.error(resp.json().get("detail", f"API error: {resp.status_code}"))
    except httpx.ConnectError:
        st.error("Cannot connect to teacher API server.")
    except httpx.ReadTimeout:
        st.error("Request timed out.")
    return None


def post_file(
    path: str,
    filename: str,
    content: bytes,
    data: dict[str, str],
    timeout: float = 300.0,
) -> Any | None:
    try:
        resp = httpx.post(
            f"{API_BASE_URL}{path}",
            data=data,
            files={"file": (filename, content)},
            headers=auth_headers(),
            timeout=timeout,
        )
        if resp.status_code == 200:
            return resp.json()
        st.error(resp.json().get("detail", f"API error: {resp.status_code}"))
    except httpx.ConnectError:
        st.error("Cannot connect to teacher API server.")
    except httpx.ReadTimeout:
        st.error("Material processing timed out.")
    return None
