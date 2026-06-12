"""Streamlit application entry point for the teacher module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from ui.components.sidebar import render_sidebar
from ui.views import analytics, assignment, dashboard, login, materials, students

st.set_page_config(
    page_title="Teacher Support System",
    page_icon="🎓",
    layout="wide",
)

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

