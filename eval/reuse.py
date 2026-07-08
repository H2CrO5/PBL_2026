"""Reuse of the student module's LLM assets, without duplicating them.

The student backend keeps its Bedrock client and prompt templates under
`student/llm/`. We add `student/` to `sys.path` so the evaluation harness can
import the *same* prompts (offline-safe: they are plain strings) and, in live
mode, the *same* Bedrock client.
"""

from __future__ import annotations

import sys
from pathlib import Path

STUDENT_DIR = Path(__file__).resolve().parents[1] / "student"


def _ensure_student_on_path() -> None:
    path = str(STUDENT_DIR)
    if path not in sys.path:
        sys.path.insert(0, path)


_ensure_student_on_path()

try:
    # Pure string templates — safe to import offline (no AWS / no httpx).
    from llm.prompts import GRADING_PROMPT, GRADING_SYSTEM
except Exception as exc:  # pragma: no cover - defensive
    raise ImportError(
        f"Could not import grading prompts from {STUDENT_DIR / 'llm' / 'prompts.py'}: {exc}"
    ) from exc


def load_bedrock_client():
    """Import and return the student Bedrock client (live mode only)."""
    _ensure_student_on_path()
    from llm import bedrock_client  # imported lazily: needs httpx / AWS config

    return bedrock_client
