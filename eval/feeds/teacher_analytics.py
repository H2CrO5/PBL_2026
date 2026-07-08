"""Aggregate synthetic grading results into a teacher-analytics feed.

The teacher module's analytics currently read hand-seeded `ConceptMetric` and
`StudentProfile` rows. This builds a portable artifact from synthetic persona
submissions so the teacher side can be driven by realistic, derived numbers
(docs/evaluation-system-design.md section 6, step 2).

Only quantitative fields are derived here (wrong_rate, average_score, weak/
strong topics). Qualitative text (misconception, recommended_focus) stays with
the teacher's catalog until teacher-side LLM analytics exist (step 4).
"""

from __future__ import annotations

import statistics
from collections import defaultdict

from ..judges.grading import grade_answer
from ..personas.definitions import PERSONAS
from ..personas.simulate import simulate_answer

# A concept mean below WEAK is a weak topic; at/above STRONG is a strong topic.
WEAK_THRESHOLD = 60.0
STRONG_THRESHOLD = 75.0


def build_feed(provider, cases) -> dict:
    """Run persona × case grading once each and aggregate into a feed dict."""
    concept_results = defaultdict(lambda: {"attempts": 0, "wrong": 0})
    student_state = {
        persona.id: {"persona": persona, "scores": [], "by_concept": defaultdict(list)}
        for persona in PERSONAS
    }

    for case in cases:
        concept = case["concept"]
        for persona in PERSONAS:
            answer = simulate_answer(provider, case, persona)
            result = grade_answer(provider, case, answer)
            score = float(result.get("score", 0.0))
            is_correct = bool(result.get("is_correct", False))

            agg = concept_results[concept]
            agg["attempts"] += 1
            if not is_correct:
                agg["wrong"] += 1

            state = student_state[persona.id]
            state["scores"].append(score)
            state["by_concept"][concept].append(score)

    concept_metrics = []
    for concept, agg in concept_results.items():
        wrong_rate = round(100.0 * agg["wrong"] / agg["attempts"], 1) if agg["attempts"] else 0.0
        concept_metrics.append(
            {"concept": concept, "attempts": agg["attempts"], "wrong_rate": wrong_rate}
        )
    concept_metrics.sort(key=lambda c: c["wrong_rate"], reverse=True)

    students = []
    for state in student_state.values():
        persona = state["persona"]
        scores = state["scores"]
        average = round(statistics.mean(scores), 1) if scores else 0.0
        concept_means = {c: statistics.mean(v) for c, v in state["by_concept"].items() if v}
        weak = sorted(c for c, mean in concept_means.items() if mean < WEAK_THRESHOLD)
        strong = sorted(c for c, mean in concept_means.items() if mean >= STRONG_THRESHOLD)
        students.append(
            {
                "student_code": f"syn-{persona.id}",
                "name": f"Synthetic {persona.label}",
                "average_score": average,
                "completion_rate": 100.0,
                "weak_topics": weak,
                "strong_topics": strong,
            }
        )
    students.sort(key=lambda s: s["average_score"], reverse=True)

    return {"concept_metrics": concept_metrics, "students": students}
