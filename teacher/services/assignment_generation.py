"""Bedrock-backed draft generation grounded in teacher course materials."""

import json
import re
from typing import Any

from llm import bedrock_client

SYSTEM = """You create formative university programming questions.
Use only the supplied course material and target concept. Return strict JSON.
Do not invent claims that are absent from the supplied material."""

PROMPT = """Create one short-answer draft for teacher review.

Target concept: {target_concept}
Assignment goal: {assignment_goal}
Difficulty: {difficulty}
Learning objectives: {objectives}

Student mastery context:
{student_context}

Course material:
{material_context}

Return exactly one valid JSON object with these field types:
{{
  "title": "string",
  "question_text": "string",
  "expected_answer": "one plain-text string, not an object or array",
  "rubric": ["string", "string", "string"],
  "source_titles": ["string"]
}}

Do not use Markdown fences. Keep multi-step answers inside one JSON string and
avoid double quotation marks inside string values.
"""

JSON_RETRY = """

Your previous response could not be parsed against the required JSON schema.
Try once more. Return only syntactically valid JSON. In particular,
expected_answer must be one string and every rubric item must be one string.
"""

_RUBRIC_PREFIX = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")


def _plain_text(value: Any, field_name: str) -> str:
    """Convert predictable Bedrock text structures into readable plain text."""
    if isinstance(value, str):
        text = value.strip()
    elif isinstance(value, list):
        text = "\n".join(_plain_text(item, field_name) for item in value)
    elif isinstance(value, dict):
        text = "\n".join(
            f"{key}: {_plain_text(item, field_name)}"
            for key, item in value.items()
        )
    else:
        raise ValueError(f"Bedrock assignment {field_name} must contain text")
    if not text.strip():
        raise ValueError(f"Bedrock assignment {field_name} must not be empty")
    return text.strip()


def _rubric_items(value: Any) -> list[str]:
    """Normalize a rubric returned as a list, multiline string, or object."""
    if isinstance(value, str):
        candidates = value.splitlines()
    elif isinstance(value, list):
        candidates = [_plain_text(item, "rubric") for item in value]
    elif isinstance(value, dict):
        candidates = [
            f"{key}: {_plain_text(item, 'rubric')}"
            for key, item in value.items()
        ]
    else:
        raise ValueError("Bedrock assignment rubric must contain text items")
    items = [
        _RUBRIC_PREFIX.sub("", item).strip()
        for item in candidates
        if item.strip()
    ]
    if not items:
        raise ValueError("Bedrock assignment rubric must not be empty")
    return items


def _source_titles(value: Any) -> list[str]:
    """Normalize an optional source title or list of source titles."""
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError("Bedrock assignment source_titles must contain strings")
    return [item.strip() for item in value if item.strip()]


def _normalize_draft(result: Any) -> dict:
    """Validate required fields and repair common, unambiguous schema drift."""
    if not isinstance(result, dict):
        raise ValueError("Bedrock assignment draft must be an object")
    draft = dict(result)
    for key in ("title", "question_text"):
        if not isinstance(draft.get(key), str) or not draft[key].strip():
            raise ValueError(f"Bedrock assignment {key} must be a string")
        draft[key] = draft[key].strip()
    draft["expected_answer"] = _plain_text(
        draft.get("expected_answer"),
        "expected_answer",
    )
    draft["rubric"] = _rubric_items(draft.get("rubric"))
    draft["source_titles"] = _source_titles(draft.get("source_titles"))
    return draft


def generate_draft(
    target_concept: str,
    difficulty: str,
    objectives: list[str],
    materials: list[dict],
    assignment_goal: str = "Check conceptual understanding using course evidence",
    student_context: list[dict] | None = None,
) -> dict:
    if not materials:
        raise ValueError("At least one ready course material is required")
    context = "\n\n".join(
        f"[Source: {item['title']}]\n{item['content'][:6000]}"
        for item in materials[:4]
    )
    prompt = PROMPT.format(
        target_concept=target_concept,
        assignment_goal=assignment_goal,
        difficulty=difficulty,
        objectives=json.dumps(objectives, ensure_ascii=False),
        student_context=json.dumps(student_context or [], ensure_ascii=False),
        material_context=context,
    )
    last_error: ValueError | None = None
    for attempt in range(2):
        try:
            result = bedrock_client.invoke_json(
                prompt + (JSON_RETRY if attempt else ""),
                system=SYSTEM,
                max_tokens=2048,
                temperature=0.2 if attempt == 0 else 0.0,
            )
            return _normalize_draft(result)
        except ValueError as exc:
            last_error = exc
    raise ValueError("Bedrock returned invalid assignment JSON after one retry") from last_error
