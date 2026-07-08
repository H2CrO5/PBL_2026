"""Have a persona answer an assignment.

Both modes go through `provider.complete_json` and return an answer string, so
the downstream grading judge is provider-agnostic.
"""

from __future__ import annotations

ANSWER_SYSTEM = (
    "You are simulating a university programming student answering an assignment. "
    "Stay in character for the given ability level, including realistic mistakes "
    'for lower-ability personas. Return ONLY JSON: {"answer_text": "..."}.'
)

ANSWER_PROMPT = """\
## Student persona
- Level: {label} (ability {ability:.2f} on a 0-1 scale)
- Behavior: {description}

## Assignment
- Type: {question_type}
- Question: {question_text}

Answer the way this student would. Return ONLY JSON: {{"answer_text": "..."}}.
"""


def simulate_answer(provider, case, persona) -> str:
    prompt = ANSWER_PROMPT.format(
        label=persona.label,
        ability=persona.ability,
        description=persona.description,
        question_type=case["question_type"],
        question_text=case["question_text"],
    )
    seed = f"case={case['id']} persona={persona.id} ability={persona.ability:.2f}"
    result = provider.complete_json(
        prompt, system=ANSWER_SYSTEM, temperature=0.7, kind="answer", seed=seed
    )
    return str(result.get("answer_text", "")).strip()
