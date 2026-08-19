"""Bedrock-backed draft generation grounded in teacher course materials."""

import json

from llm import bedrock_client

SYSTEM = """You create formative university programming questions.
Use only the supplied course material and target concept. Return strict JSON.
Do not invent claims that are absent from the supplied material."""

PROMPT = """Create one short-answer draft for teacher review.

Target concept: {target_concept}
Difficulty: {difficulty}
Learning objectives: {objectives}

Course material:
{material_context}

Return JSON:
{{
  "title": "short title",
  "question_text": "question",
  "expected_answer": "grounded model answer",
  "rubric": ["criterion 1", "criterion 2", "criterion 3"],
  "source_titles": ["title used"]
}}
"""


def generate_draft(
    target_concept: str,
    difficulty: str,
    objectives: list[str],
    materials: list[dict],
) -> dict:
    if not materials:
        raise ValueError("At least one ready course material is required")
    context = "\n\n".join(
        f"[Source: {item['title']}]\n{item['content'][:6000]}"
        for item in materials[:4]
    )
    result = bedrock_client.invoke_json(
        PROMPT.format(
            target_concept=target_concept,
            difficulty=difficulty,
            objectives=json.dumps(objectives, ensure_ascii=False),
            material_context=context,
        ),
        system=SYSTEM,
        temperature=0.2,
    )
    required = ("title", "question_text", "expected_answer", "rubric")
    if not isinstance(result, dict) or any(not result.get(key) for key in required):
        raise ValueError("Bedrock returned an invalid assignment draft")
    if not isinstance(result["rubric"], list):
        raise ValueError("Bedrock assignment rubric must be a list")
    return result
