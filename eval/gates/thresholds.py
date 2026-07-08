"""Threshold gates.

A run fails if any gated metric fails its threshold. Starting values are
intentionally conservative; calibrate against a first baseline run, then
ratchet up (see docs/evaluation-system-design.md section 3.3).
"""

from __future__ import annotations

GATES = {
    "grading": {
        "grading_consistency": (">=", 0.90),
        "correctness_agreement": (">=", 0.90),
    },
}

_OPS = {
    ">=": lambda v, t: v >= t,
    "<=": lambda v, t: v <= t,
    ">": lambda v, t: v > t,
    "<": lambda v, t: v < t,
}


def evaluate_gate(target, metrics):
    """Return (all_passed, [{metric, op, threshold, value, passed}, ...])."""
    thresholds = GATES.get(target, {})
    results = []
    all_passed = True
    for metric, (op, threshold) in thresholds.items():
        value = metrics.get(metric)
        passed = value is not None and _OPS[op](value, threshold)
        all_passed = all_passed and passed
        results.append(
            {"metric": metric, "op": op, "threshold": threshold, "value": value, "passed": passed}
        )
    return all_passed, results
