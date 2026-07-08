"""Grading judge.

Calls the *same* grading path the student backend uses
(`student/api/routers/assignments.py` -> GRADING_PROMPT + invoke_json) so what
we measure matches production behavior. The consistency metric comes from
grading the identical answer multiple times (done by the runner).
"""

from __future__ import annotations

from ..reuse import GRADING_PROMPT, GRADING_SYSTEM

# Matches the temperature used by the student submit endpoint.
GRADING_TEMPERATURE = 0.3


def grade_answer(provider, case, answer_text, temperature: float = GRADING_TEMPERATURE) -> dict:
    prompt = GRADING_PROMPT.format(
        question_text=case["question_text"],
        question_type=case["question_type"],
        correct_answer=case["correct_answer"],
        student_answer=answer_text,
    )
    seed = f"{case['id']}|{answer_text}"
    return provider.complete_json(
        prompt, system=GRADING_SYSTEM, temperature=temperature, kind="grading", seed=seed
    )
