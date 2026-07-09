"""LLM provider abstraction for the evaluation harness.

Two backends:
  - MockProvider   : deterministic, offline, no AWS. Default for scaffolding/CI.
  - BedrockProvider: reuses student/llm/bedrock_client.py (needs AWS creds).

Both expose the same `complete_json(...)` call. Callers pass a `kind` hint
("answer" | "grading") and a `seed` string; the mock uses them to produce a
reproducible, appropriately-shaped payload, while Bedrock ignores them.
"""

from __future__ import annotations

import hashlib
import re

_ABILITY_RE = re.compile(r"ability=([0-9]*\.?[0-9]+)")


def _unit(text: str) -> float:
    """Map an arbitrary string to a stable float in [0, 1)."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _ability_from_seed(seed: str) -> float:
    match = _ABILITY_RE.search(seed)
    return float(match.group(1)) if match else 0.5


class MockProvider:
    """Deterministic offline provider (default backend).

    `jitter` (0..1) injects per-call grader variance so an *inconsistent*
    grader can be simulated to demonstrate a failing gate without a live model.
    At jitter=0 the grader is perfectly consistent.
    """

    name = "mock"

    def __init__(self, jitter: float = 0.0):
        self.jitter = max(0.0, min(1.0, jitter))
        self._call = 0

    def complete_json(self, prompt, system="", temperature=0.7, *, kind="generic", seed=""):
        self._call += 1

        if kind == "answer":
            ability = _ability_from_seed(seed)
            # Echo the ability into the answer so the grader can react to it.
            return {"answer_text": f"ability={ability:.2f} {seed} :: mock student answer"}

        if kind == "grading":
            base = _unit(seed or prompt)          # deterministic per (case, answer)
            ability = _ability_from_seed(seed)    # stronger persona -> higher score
            score = 100.0 * (0.35 * base + 0.65 * ability)
            if self.jitter:
                offset = (_unit(f"{seed}:{self._call}") - 0.5) * 2.0 * self.jitter * 100.0
                score += offset
            score = round(max(0.0, min(100.0, score)), 1)
            return {
                "is_correct": score >= 60.0,
                "score": score,
                "feedback": "Mock offline feedback.",
            }

        if kind == "generation":
            # Deterministic placeholder question. Mock is for scaffolding/CI only;
            # the real question comes from Bedrock in --live mode.
            return {
                "question_text": f"[mock generated question :: {seed}]",
                "choices": None,
                "correct_answer": "mock correct answer",
                "explanation": "mock explanation",
            }

        if kind == "gen_judge":
            score = self._quality_score(seed or prompt)
            return {
                "question_validity": score,
                "concept_match": score,
                "difficulty_match": score,
                "rationale": "Mock offline judge.",
            }

        if kind == "ta_answer":
            return {"answer_text": f"[mock TA answer grounded in the provided sources :: {seed}]"}

        if kind == "ta_judge":
            grounding = self._quality_score(f"{seed}:grounding")
            # Hallucination is the "bad" direction: small by default, grows with jitter.
            hallucination = round(min(1.0, (1.0 - grounding) * 0.5), 3)
            return {
                "grounding": grounding,
                "hallucination": hallucination,
                "rationale": "Mock offline judge.",
            }

        return {}

    def _quality_score(self, seed: str) -> float:
        """Deterministic judge score in [0,1], high by default; jitter degrades it."""
        base = _unit(seed)
        score = 0.90 + 0.09 * base          # 0.90 .. 0.99 -> passes gates
        if self.jitter:
            score -= self.jitter * (0.4 + 0.5 * _unit(f"{seed}:{self._call}"))
        return round(max(0.0, min(1.0, score)), 3)


class BedrockProvider:
    """Live provider backed by the student module's Bedrock client."""

    name = "bedrock"

    def __init__(self, client):
        self._client = client

    def complete_json(self, prompt, system="", temperature=0.7, *, kind="generic", seed=""):
        # The TA bot answers in free text (multi-line), like production; wrap it
        # so callers get a uniform dict. Everything else returns real JSON.
        if kind == "ta_answer":
            text = self._client.invoke(prompt=prompt, system=system, temperature=temperature)
            return {"answer_text": text}
        return self._client.invoke_json(prompt=prompt, system=system, temperature=temperature)


def load_bedrock_provider() -> "BedrockProvider":
    """Construct the live provider. Raises if AWS/deps are unavailable."""
    from .reuse import load_bedrock_client

    return BedrockProvider(load_bedrock_client())
