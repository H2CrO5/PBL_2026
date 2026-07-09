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

# ── AWS Bedrock (mirrors the student module's auth: bearer token or boto3) ──
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
BEDROCK_BEARER_TOKEN = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")
BEDROCK_ENDPOINT = f"https://bedrock-runtime.{AWS_REGION}.amazonaws.com"

# ── LLM parameters ──
# Analytics narration uses a low temperature so text stays faithful to the
# numeric inputs (important for the eval analytics-faithfulness gate).
LLM_MAX_TOKENS = 1536
LLM_TEMPERATURE = 0.3

# Feature flag: only call the LLM when explicitly enabled. When unset (or when a
# call fails) the analytics endpoints fall back to the deterministic rule-based
# narration, so the teacher UI always renders something.
USE_LLM = os.getenv("TEACHER_USE_LLM", "").strip().lower() not in ("", "0", "false", "no")

