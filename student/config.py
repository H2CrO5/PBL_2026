"""Centralized configuration for the student education system."""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "student.db"
FAISS_INDEX_DIR = BASE_DIR / "data" / "faiss_index"
DOCUMENTS_DIR = BASE_DIR / "vectorstore" / "documents"

# ── Database ───────────────────────────────────────────
DATABASE_URL = f"sqlite:///{DB_PATH}"

# ── AWS Bedrock ────────────────────────────────────────
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
BEDROCK_BEARER_TOKEN = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")
BEDROCK_ENDPOINT = f"https://bedrock-runtime.{AWS_REGION}.amazonaws.com"

# ── LLM parameters ────────────────────────────────────
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.7

# ── Embedding / RAG ───────────────────────────────────
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_DIMENSION = 1024  # Titan Embed Text v2
RAG_TOP_K = 3

# ── Auth ───────────────────────────────────────────────
SESSION_EXPIRE_HOURS = 24

# ── API ────────────────────────────────────────────────
API_HOST = "0.0.0.0"
API_PORT = 8000

# ── Streamlit ──────────────────────────────────────────
STREAMLIT_PORT = 8501
API_BASE_URL = os.getenv("API_BASE_URL", f"http://localhost:{API_PORT}")

# Service-to-service authentication for the read-only Teacher analytics feed.
# Keep this value in the environment; never commit a real token.
TEACHER_INTEGRATION_TOKEN = os.getenv("TEACHER_INTEGRATION_TOKEN", "")
