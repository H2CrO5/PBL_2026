"""Streamlit application entry point for the teacher module."""

from importlib import reload
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

BRAND_ICON = Path(__file__).resolve().parents[2] / "assets" / "branding" / "classpilot-favicon.png"

from ui import i18n
from ui.components import sidebar
from ui.views import analytics, assignment, dashboard, login, materials, students

# Streamlit keeps imported modules in memory between reruns. Reload view modules
# so language and UI edits are reflected immediately during local development.
reload(i18n)
for _view_module in (sidebar, analytics, assignment, dashboard, login, materials, students):
    reload(_view_module)

st.set_page_config(
    page_title="ClassPilot Teacher",
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

if "token" not in st.session_state:
    st.session_state.token = None
if "teacher_lang" not in st.session_state:
    st.session_state.teacher_lang = "en"

# Keep the login screen uncluttered. Sidebar controls return after login.
if not st.session_state.token:
    st.markdown("""
    <style>
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stExpandSidebarButton"],
    [data-testid="collapsedControl"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

_lang_left, _lang_right = st.columns([5, 1])
with _lang_right:
    _languages = {"en": "English", "ja": "日本語"}
    _current_lang = st.session_state.teacher_lang
    _selected_lang = st.selectbox(
        "Language",
        options=list(_languages),
        format_func=_languages.get,
        index=list(_languages).index(_current_lang),
        label_visibility="collapsed",
        key="teacher_language_selector",
    )
    if _selected_lang != _current_lang:
        st.session_state.teacher_lang = _selected_lang
        st.rerun()

page = sidebar.render_sidebar()

if page == "login":
    login.render()
elif page == "dashboard":
    dashboard.render()
elif page == "materials":
    materials.render()
elif page == "assignment":
    assignment.render()
elif page == "analytics":
    analytics.render()
elif page == "students":
    students.render()
