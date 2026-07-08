"""Evaluation harness entrypoint.

Usage:
    python -m eval.run --target grading                 # offline mock (default)
    python -m eval.run --target grading --repeats 5
    python -m eval.run --target grading --jitter 0.4    # simulate an inconsistent grader (mock)
    python -m eval.run --target grading --live          # real Bedrock (needs AWS creds)

Exit code is 0 when every gate passes, 1 otherwise (so CI can block a merge).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

from .feeds.teacher_analytics import build_feed
from .gates.thresholds import evaluate_gate
from .judges.grading import grade_answer
from .llm import MockProvider, load_bedrock_provider
from .personas.definitions import PERSONAS
from .personas.simulate import simulate_answer

EVAL_DIR = Path(__file__).resolve().parent
DEFAULT_CASES = EVAL_DIR / "datasets" / "seed_cases.json"
REPORTS_DIR = EVAL_DIR / "reports"


def _load_cases(path: Path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def run_grading(provider, cases, repeats: int):
    """Grade every (case, persona) answer `repeats` times and score consistency."""
    groups = []
    for case in cases:
        for persona in PERSONAS:
            answer = simulate_answer(provider, case, persona)
            scores, corrects = [], []
            for _ in range(repeats):
                result = grade_answer(provider, case, answer)
                scores.append(float(result.get("score", 0.0)))
                corrects.append(bool(result.get("is_correct", False)))

            spread = (max(scores) - min(scores)) if scores else 0.0
            consistency = max(0.0, 1.0 - spread / 100.0)
            agreement = 1.0 if len(set(corrects)) <= 1 else 0.0
            groups.append(
                {
                    "case_id": case["id"],
                    "persona": persona.id,
                    "answer_preview": answer[:80],
                    "scores": scores,
                    "score_mean": round(statistics.mean(scores), 1) if scores else 0.0,
                    "score_spread": round(spread, 1),
                    "consistency": round(consistency, 3),
                    "correctness_agreement": agreement,
                    "is_correct_votes": corrects,
                }
            )

    metrics = {
        "grading_consistency": round(statistics.mean(g["consistency"] for g in groups), 3)
        if groups
        else 0.0,
        "correctness_agreement": round(
            statistics.mean(g["correctness_agreement"] for g in groups), 3
        )
        if groups
        else 0.0,
    }
    return metrics, groups


def _print_summary(target, provider, repeats, metrics, groups, gate_passed, gate_results):
    print(f"\n=== eval: {target} | provider={provider.name} | repeats={repeats} ===")
    print(f"{'case':<12} {'persona':<14} {'mean':>6} {'spread':>7} {'consist':>8} {'agree':>6}")
    for g in groups:
        print(
            f"{g['case_id']:<12} {g['persona']:<14} {g['score_mean']:>6} "
            f"{g['score_spread']:>7} {g['consistency']:>8} {g['correctness_agreement']:>6}"
        )

    print("\nMetrics:")
    for name, value in metrics.items():
        print(f"  {name:<24} {value}")

    print("\nGates:")
    for r in gate_results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  [{mark}] {r['metric']} {r['op']} {r['threshold']} (value={r['value']})")

    print(f"\nRESULT: {'PASS' if gate_passed else 'FAIL'}")


def _run_teacher_feed(provider, cases, out_dir: Path) -> int:
    """Build the teacher-analytics feed artifact and write it to a stable path."""
    feed = build_feed(provider, cases)

    print(f"\n=== teacher-feed | provider={provider.name} ===")
    print("Concept metrics (wrong_rate, synthetic-derived):")
    for cm in feed["concept_metrics"]:
        print(f"  {cm['concept']:<26} wrong_rate={cm['wrong_rate']:>5}  (n={cm['attempts']})")
    print("\nSynthetic students:")
    for s in feed["students"]:
        print(
            f"  {s['student_code']:<16} avg={s['average_score']:>5}  "
            f"weak={s['weak_topics']}  strong={s['strong_topics']}"
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "source": "eval-synthetic",
        "provider": provider.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "concept_metrics": feed["concept_metrics"],
        "students": feed["students"],
    }
    feed_path = out_dir / "teacher_feed.json"
    with open(feed_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(f"\nFeed: {feed_path}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="LLM subsystem evaluation harness")
    parser.add_argument("--target", default="grading", choices=["grading", "teacher-feed"])
    parser.add_argument("--live", action="store_true", help="use real Bedrock (needs AWS creds)")
    parser.add_argument("--repeats", type=int, default=3, help="grading repeats per answer")
    parser.add_argument(
        "--jitter",
        type=float,
        default=0.0,
        help="mock only: inject grader variance (0..1) to simulate inconsistency",
    )
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="path to seed cases JSON")
    parser.add_argument("--out", default=str(REPORTS_DIR), help="report output directory")
    args = parser.parse_args(argv)

    provider = load_bedrock_provider() if args.live else MockProvider(jitter=args.jitter)
    cases = _load_cases(Path(args.cases))

    if args.target == "teacher-feed":
        return _run_teacher_feed(provider, cases, Path(args.out))

    metrics, groups = run_grading(provider, cases, args.repeats)
    gate_passed, gate_results = evaluate_gate(args.target, metrics)
    _print_summary(args.target, provider, args.repeats, metrics, groups, gate_passed, gate_results)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = out_dir / f"{args.target}_{stamp}.json"
    report = {
        "target": args.target,
        "provider": provider.name,
        "repeats": args.repeats,
        "jitter": args.jitter if not args.live else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "gate_passed": gate_passed,
        "gates": gate_results,
        "groups": groups,
    }
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(f"Report: {report_path}")

    return 0 if gate_passed else 1


if __name__ == "__main__":
    sys.exit(main())
