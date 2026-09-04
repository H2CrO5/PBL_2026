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
from .judges.analytics import generate_narration, judge_narration
from .judges.generation import generate_question, judge_question
from .judges.grading import grade_answer
from .judges.ta_bot import generate_answer, judge_answer
from .llm import MockProvider, load_bedrock_provider
from .personas.definitions import PERSONAS
from .personas.simulate import simulate_answer

EVAL_DIR = Path(__file__).resolve().parent
DATASETS_DIR = EVAL_DIR / "datasets"
DEFAULT_CASES = DATASETS_DIR / "seed_cases.json"
GENERATION_CASES = DATASETS_DIR / "generation_cases.json"
TA_CASES = DATASETS_DIR / "ta_cases.json"
ANALYTICS_FACTS = DATASETS_DIR / "analytics_facts.json"
REPORTS_DIR = EVAL_DIR / "reports"

# Per-target default dataset when --cases is not given.
DEFAULT_DATASET = {
    "grading": DEFAULT_CASES,
    "teacher-feed": DEFAULT_CASES,
    "generation": GENERATION_CASES,
    "ta-bot": TA_CASES,
    "analytics": ANALYTICS_FACTS,
}


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


def run_generation(provider, cases):
    """Generate a question per case and judge validity / concept / difficulty."""
    groups = []
    for case in cases:
        generated = generate_question(provider, case)
        j = judge_question(provider, case, generated)
        groups.append(
            {
                "case_id": case["id"],
                "concept": case["concept"],
                "difficulty": case["difficulty"],
                "question_validity": round(float(j.get("question_validity", 0.0)), 3),
                "concept_match": round(float(j.get("concept_match", 0.0)), 3),
                "difficulty_match": round(float(j.get("difficulty_match", 0.0)), 3),
                "question_preview": str(generated.get("question_text", ""))[:80],
            }
        )

    def _mean(key):
        return round(statistics.mean(g[key] for g in groups), 3) if groups else 0.0

    metrics = {
        "question_validity": _mean("question_validity"),
        "concept_match": _mean("concept_match"),
        "difficulty_match": _mean("difficulty_match"),
    }
    return metrics, groups


def run_ta_bot(provider, cases):
    """Generate a TA answer per case and judge grounding / hallucination."""
    groups = []
    for case in cases:
        answer = generate_answer(provider, case)
        j = judge_answer(provider, case, answer)
        groups.append(
            {
                "case_id": case["id"],
                "grounding": round(float(j.get("grounding", 0.0)), 3),
                "hallucination": round(float(j.get("hallucination", 0.0)), 3),
                "answer_preview": answer[:80],
            }
        )

    metrics = {
        "citation_grounding_rate": round(statistics.mean(g["grounding"] for g in groups), 3)
        if groups
        else 0.0,
        "hallucination_rate": round(statistics.mean(g["hallucination"] for g in groups), 3)
        if groups
        else 0.0,
    }
    return metrics, groups


def run_analytics(provider, facts):
    """Independently narrate the numeric facts, then judge faithfulness.

    `facts` is a dict {concept_metrics, students} (teacher_feed.json schema).
    """
    narration = generate_narration(provider, facts)
    result = judge_narration(provider, facts, narration)
    score = round(float(result.get("analytics_faithfulness", 0.0)), 3)

    groups = [
        {
            "concepts": len(facts.get("concept_metrics", [])),
            "students": len(facts.get("students", [])),
            "analytics_faithfulness": score,
            "narration_summary": str(narration.get("summary", ""))[:80],
            "narration_weak_concepts": narration.get("weak_concepts", []),
        }
    ]
    metrics = {"analytics_faithfulness": score}
    return metrics, groups


def _print_gate_summary(target, provider, metrics, groups, gate_passed, gate_results):
    """Generic metrics + gate printer for non-grading targets."""
    print(f"\n=== eval: {target} | provider={provider.name} | cases={len(groups)} ===")
    for g in groups:
        detail = " ".join(f"{k}={v}" for k, v in g.items() if k not in ("question_preview", "answer_preview"))
        print(f"  {detail}")

    print("\nMetrics:")
    for name, value in metrics.items():
        print(f"  {name:<26} {value}")

    print("\nGates:")
    for r in gate_results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  [{mark}] {r['metric']} {r['op']} {r['threshold']} (value={r['value']})")

    print(f"\nRESULT: {'PASS' if gate_passed else 'FAIL'}")


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
    parser.add_argument(
        "--target",
        default="grading",
        choices=["grading", "teacher-feed", "generation", "ta-bot", "analytics", "workflow"],
    )
    parser.add_argument("--live", action="store_true", help="use real Bedrock (needs AWS creds)")
    parser.add_argument("--repeats", type=int, default=3, help="grading repeats per answer")
    parser.add_argument(
        "--jitter",
        type=float,
        default=0.0,
        help="mock only: inject judge/grader variance (0..1) to simulate a failing gate",
    )
    parser.add_argument(
        "--cases",
        default=None,
        help="path to a cases JSON (defaults to the dataset for the chosen target)",
    )
    parser.add_argument("--out", default=str(REPORTS_DIR), help="report output directory")
    parser.add_argument("--teacher-url", default="http://127.0.0.1:8100")
    parser.add_argument("--student-url", default="http://127.0.0.1:8000")
    args = parser.parse_args(argv)

    if args.target == "workflow":
        # Keep the deterministic CI gates standard-library-only. The live
        # workflow's HTTP dependency is loaded only when that target is used.
        from .workflows.full_pipeline import run_full_pipeline

        metrics, groups = run_full_pipeline(args.teacher_url, args.student_url)
        provider = type("ServiceProvider", (), {"name": "live-services"})()
        gate_passed, gate_results = evaluate_gate(args.target, metrics)
        _print_gate_summary(
            args.target, provider, metrics, groups, gate_passed, gate_results
        )
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = out_dir / f"workflow_{stamp}.json"
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump({
                "target": "workflow",
                "provider": provider.name,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "metrics": metrics,
                "gate_passed": gate_passed,
                "gates": gate_results,
                "groups": groups,
            }, handle, ensure_ascii=False, indent=2)
        print(f"Report: {report_path}")
        return 0 if gate_passed else 1

    provider = load_bedrock_provider() if args.live else MockProvider(jitter=args.jitter)
    cases_path = Path(args.cases) if args.cases else DEFAULT_DATASET[args.target]
    cases = _load_cases(cases_path)

    if args.target == "teacher-feed":
        return _run_teacher_feed(provider, cases, Path(args.out))

    if args.target == "grading":
        metrics, groups = run_grading(provider, cases, args.repeats)
    elif args.target == "generation":
        metrics, groups = run_generation(provider, cases)
    elif args.target == "ta-bot":
        metrics, groups = run_ta_bot(provider, cases)
    else:  # analytics (cases is a {concept_metrics, students} dict, not a list)
        metrics, groups = run_analytics(provider, cases)

    gate_passed, gate_results = evaluate_gate(args.target, metrics)
    if args.target == "grading":
        _print_summary(args.target, provider, args.repeats, metrics, groups, gate_passed, gate_results)
    else:
        _print_gate_summary(args.target, provider, metrics, groups, gate_passed, gate_results)

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
