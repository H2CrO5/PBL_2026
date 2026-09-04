"""Bedrock-backed draft generation grounded in teacher course materials."""

import json

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
            if not isinstance(result, dict):
                raise ValueError("Bedrock assignment draft must be an object")
            for key in ("title", "question_text", "expected_answer"):
                if not isinstance(result.get(key), str) or not result[key].strip():
                    raise ValueError(f"Bedrock assignment {key} must be a string")
            rubric = result.get("rubric")
            if (
                not isinstance(rubric, list)
                or not rubric
                or any(not isinstance(item, str) or not item.strip() for item in rubric)
            ):
                raise ValueError("Bedrock assignment rubric must be a list of strings")
            sources = result.get("source_titles", [])
            if not isinstance(sources, list) or any(
                not isinstance(item, str) for item in sources
            ):
                raise ValueError("Bedrock assignment source_titles must be a list of strings")
            result["source_titles"] = sources
            return result
        except ValueError as exc:
            last_error = exc
    raise ValueError("Bedrock returned invalid assignment JSON after one retry") from last_error
