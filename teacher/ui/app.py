"""Streamlit application entry point for the teacher module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

BRAND_ICON = Path(__file__).resolve().parents[2] / "assets" / "branding" / "classpilot-logo-light.png"

from ui.components.sidebar import render_sidebar
from ui.views import analytics, assignment, dashboard, login, materials, students

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

page = render_sidebar()

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
