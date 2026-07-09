"""TA-bot judge (case 3b: no student endpoint required).

Reproduces the TA-bot path at the prompt level: given fixed source passages
(standing in for RAG retrieval so the harness runs offline), generate an answer
with the student's real TA prompt, then judge how well the answer is grounded in
those sources. Metrics:
  - grounding      : fraction of the answer's claims supported by the sources
  - hallucination  : fraction of the answer's claims unsupported/contradicted
"""

from __future__ import annotations

from ..reuse import TA_BOT_PROMPT, TA_BOT_SYSTEM

TA_JUDGE_SYSTEM = (
    "You evaluate whether a teaching-assistant answer is grounded in the provided "
    "source passages. The sources are the only allowed evidence. Return ONLY JSON."
)

TA_JUDGE_PROMPT = """\
## Source passages (the only allowed evidence)
{context}

## Student question
{question}

## TA answer
{answer}

Judge the answer strictly against the sources:
- grounding: fraction (0.0-1.0) of the answer's factual claims that are supported by the sources.
- hallucination: fraction (0.0-1.0) of the answer's factual claims that are unsupported or contradicted by the sources.

Return ONLY JSON:
{{"grounding": 0.0, "hallucination": 0.0, "rationale": "..."}}
"""

def _context_text(case) -> str:
    return "\n\n---\n\n".join(case["context"])


def generate_answer(provider, case) -> str:
    """Generate a TA answer from the fixed source passages.

    Uses the student's real TA prompt as-is; the provider returns the answer as
    free text (kind="ta_answer"), exactly like the production TA endpoint.
    """
    prompt = TA_BOT_PROMPT.format(
        student_name="評価用ユーザー",
        overall_score=70,
        weak_topics=[],
        context=_context_text(case),
        chat_history="",
        message=case["question"],
    )
    seed = f"ta|{case['id']}"
    result = provider.complete_json(
        prompt, system=TA_BOT_SYSTEM, temperature=0.5, kind="ta_answer", seed=seed
    )
    return str(result.get("answer_text", "")).strip()


def judge_answer(provider, case, answer_text: str) -> dict:
    """Score grounding / hallucination of a TA answer against the sources."""
    prompt = TA_JUDGE_PROMPT.format(
        context=_context_text(case),
        question=case["question"],
        answer=answer_text,
    )
    seed = f"ta_judge|{case['id']}"
    return provider.complete_json(
        prompt, system=TA_JUDGE_SYSTEM, temperature=0.0, kind="ta_judge", seed=seed
    )
