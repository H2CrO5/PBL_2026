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

        return {}


class BedrockProvider:
    """Live provider backed by the student module's Bedrock client."""

    name = "bedrock"

    def __init__(self, client):
        self._client = client

    def complete_json(self, prompt, system="", temperature=0.7, *, kind="generic", seed=""):
        return self._client.invoke_json(prompt=prompt, system=system, temperature=temperature)


def load_bedrock_provider() -> "BedrockProvider":
    """Construct the live provider. Raises if AWS/deps are unavailable."""
    from .reuse import load_bedrock_client

    return BedrockProvider(load_bedrock_client())
