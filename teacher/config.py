"""Centralized configuration for the teacher education system."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "teacher.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

API_HOST = "0.0.0.0"
API_PORT = int(os.getenv("TEACHER_API_PORT", "8100"))
STREAMLIT_PORT = int(os.getenv("TEACHER_STREAMLIT_PORT", "8601"))
API_BASE_URL = os.getenv("TEACHER_API_BASE_URL", f"http://localhost:{API_PORT}")

MATERIALS_DIR = BASE_DIR / "materials"

