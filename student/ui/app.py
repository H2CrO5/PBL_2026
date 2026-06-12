"""Streamlit application entry point."""

import sys
from pathlib import Path

# Ensure the student/ directory is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(
    page_title="Learning Support System",
    page_icon="📚",
    layout="wide",
)

from ui.components.sidebar import render_sidebar
from ui.views import assignment, login, ta_chat

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "lang" not in st.session_state:
    st.session_state.lang = "ja"

# ── Language selector pinned to top-right ──────────────────────────────
_lang_bar_left, _lang_bar_right = st.columns([5, 1])
with _lang_bar_right:
    lang_options = {"ja": "日本語", "en": "English"}
    current = st.session_state.get("lang", "ja")
    selected = st.selectbox(
        "Lang",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(current),
        label_visibility="collapsed",
    )
    if selected != current:
        st.session_state.lang = selected
        st.rerun()

# ── Page routing ───────────────────────────────────────────────────────
page = render_sidebar()

if page == "login":
    login.render()
elif page == "assignments":
    assignment.render()
elif page == "ta_bot":
    ta_chat.render()
