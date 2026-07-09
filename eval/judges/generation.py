"""Assignment-generation judge (case 3b: no student endpoint required).

Generates a question by calling the student's real generation prompt through the
provider, then scores the result with an LLM-as-judge rubric. Metrics:
  - question_validity : well-formed, unambiguous, has a correct answer
  - concept_match     : targets the requested concept
  - difficulty_match  : matches the requested difficulty
"""

from __future__ import annotations

import json

from ..reuse import ASSIGNMENT_GENERATE, ASSIGNMENT_SYSTEM

GEN_JUDGE_SYSTEM = (
    "You are a strict evaluator of auto-generated programming assignments. "
    "Judge only what is present. Return ONLY JSON, no extra text."
)

GEN_JUDGE_PROMPT = """\
Evaluate the generated question against the request.

## Requested
- concept: {concept}
- difficulty: {difficulty}
- question_type: {question_type}

## Generated question (JSON)
{generated}

Score each on a 0.0-1.0 scale:
- question_validity: is it a well-formed, unambiguous question that has a correct answer?
- concept_match: does it actually target the requested concept?
- difficulty_match: does it match the requested difficulty?

Return ONLY JSON:
{{"question_validity": 0.0, "concept_match": 0.0, "difficulty_match": 0.0, "rationale": "..."}}
"""

# Neutral student context: generation quality should not depend on a specific learner.
_STUDENT_CONTEXT = {
    "overall_score": 70,
    "topic_scores": "{}",
    "weak_topics": "[]",
    "strong_topics": "[]",
    "context": "(no reference material provided)",
    "recent_questions": "(none)",
}


def generate_question(provider, case) -> dict:
    """Produce a question dict using the student's real generation prompt."""
    prompt = ASSIGNMENT_GENERATE.format(
        topic=case["concept"],
        difficulty=case["difficulty"],
        question_type=case["question_type"],
        **_STUDENT_CONTEXT,
    )
    seed = f"gen|{case['id']}"
    return provider.complete_json(
        prompt, system=ASSIGNMENT_SYSTEM, temperature=0.7, kind="generation", seed=seed
    )


def judge_question(provider, case, generated: dict) -> dict:
    """Score a generated question with the judge rubric (low temperature)."""
    prompt = GEN_JUDGE_PROMPT.format(
        concept=case["concept"],
        difficulty=case["difficulty"],
        question_type=case["question_type"],
        generated=json.dumps(generated, ensure_ascii=False, indent=2),
    )
    seed = f"gen_judge|{case['id']}"
    return provider.complete_json(
        prompt, system=GEN_JUDGE_SYSTEM, temperature=0.0, kind="gen_judge", seed=seed
    )
