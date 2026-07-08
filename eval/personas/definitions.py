"""Persona definitions for synthetic students.

`ability` is a 0..1 scalar: higher means a stronger student. It drives both the
simulated answer (live mode) and the mock grading bias (offline mode).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    id: str
    label: str
    ability: float
    description: str


PERSONAS = [
    Persona(
        "strong",
        "Strong student",
        0.90,
        "Answers correctly and explains the reasoning; only rare slips.",
    ),
    Persona(
        "average",
        "Average student",
        0.65,
        "Correct on core ideas but shaky on edge cases and precise definitions.",
    ),
    Persona(
        "struggling",
        "Struggling student",
        0.40,
        "Frequent errors; misses boundary conditions and mixes up definitions.",
    ),
    Persona(
        "misconception",
        "Misconception-prone student",
        0.50,
        "Confidently applies a specific wrong mental model to the target concept.",
    ),
]
