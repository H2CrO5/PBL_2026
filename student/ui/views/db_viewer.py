"""DB Viewer page - visualize database tables for admin/debug purposes."""

import streamlit as st
import httpx
import pandas as pd

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
    """Render the DB viewer page."""
    st.title("DB閲覧")
    st.caption("バックエンドで管理しているデータベースの内容を確認できます。")

    # Table counts
    stats = _api_get("/admin/db/stats")
    if stats:
        cols = st.columns(len(stats))
        labels = {
            "students": "Students",
            "lectures": "Lectures",
            "assignments": "Assignments",
            "submissions": "Submissions",
            "chat_messages": "Chat Messages",
        }
        for col, (key, count) in zip(cols, stats.items()):
            col.metric(labels.get(key, key), count)

    st.divider()

    # Table selector
    table = st.selectbox(
        "テーブルを選択",
        ["students", "lectures", "assignments", "submissions", "chat_messages"],
        format_func=lambda x: {
            "students": "Students (学生)",
            "lectures": "Lectures (講義)",
            "assignments": "Assignments (課題)",
            "submissions": "Submissions (提出)",
            "chat_messages": "Chat Messages (チャット)",
        }.get(x, x),
    )

    data = _api_get(f"/admin/db/{table}")
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("データがありません。")
