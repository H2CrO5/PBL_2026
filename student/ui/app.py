"""Streamlit application entry point."""

from importlib import reload
import sys
from pathlib import Path

# Ensure the student/ directory is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

BRAND_ICON = Path(__file__).resolve().parents[2] / "assets" / "branding" / "classpilot-favicon.png"

st.set_page_config(
    page_title="ClassPilot Student",
    page_icon=str(BRAND_ICON),
    layout="wide",
)

st.markdown("""
<style>
:root { --classpilot-purple: #2d0b78; --classpilot-teal: #14b8b8; }
.stButton > button, .stFormSubmitButton > button { border-color: var(--classpilot-purple); }
.stButton > button[kind="primary"], .stFormSubmitButton > button {
  background: linear-gradient(90deg, #2d0b78, #4b1ba8); color: white;
}
a { color: var(--classpilot-teal) !important; }
</style>
""", unsafe_allow_html=True)

from ui import i18n
from ui.components import sidebar
from ui.views import assignment, dashboard, login, ta_chat

# Streamlit keeps imported modules in memory between reruns. Reload view modules
# so UI-only edits are reflected immediately during local development.
reload(i18n)
for _view_module in (sidebar, assignment, dashboard, login, ta_chat):
    reload(_view_module)

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "lang" not in st.session_state:
    st.session_state.lang = "ja"

# Remove the entire sidebar on the login screen. It returns after login.
if not st.session_state.token:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stExpandSidebarButton"],
    [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

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
page = sidebar.render_sidebar()

if page == "login":
    login.render()
elif page == "dashboard":
    dashboard.render()
elif page == "assignments":
    assignment.render()
elif page == "ta_bot":
    ta_chat.render()
