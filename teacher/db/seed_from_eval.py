"""Import a synthetic analytics feed from the eval harness into the teacher DB.

Replaces hand-seeded numbers with values derived from synthetic submissions
(docs/evaluation-system-design.md step 2). Run order:

    cd teacher
    python -m db.seed              # base course/lectures/materials/seeds
    python -m db.seed_from_eval    # overlay synthetic-derived analytics

Behavior:
- Updates `ConceptMetric.wrong_rate` for concepts already present (keeping the
  teacher's catalog misconception / recommended_focus text). Unknown concepts
  are inserted with placeholder text pending teacher review.
- Upserts synthetic `StudentProfile` rows (student_code `syn-*`) idempotently.
  Existing seeded students (e.g. s2024001) are left untouched.

The feed artifact is produced by: `python -m eval.run --target teacher-feed`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import SessionLocal, create_tables
from db.models import ConceptMetric, Course, StudentProfile

DEFAULT_FEED = Path(__file__).resolve().parents[2] / "eval" / "reports" / "teacher_feed.json"


def _recommended_action(weak_topics: list) -> str:
    if weak_topics:
        return "Focus follow-up practice on: " + ", ".join(weak_topics) + "."
    return "On track; assign a challenge-level item next."


def import_feed(feed_path: Path = DEFAULT_FEED) -> None:
    if not feed_path.exists():
        raise SystemExit(
            f"Feed not found: {feed_path}\n"
            "Generate it first: python -m eval.run --target teacher-feed"
        )

    create_tables()
    db = SessionLocal()
    try:
        course = db.query(Course).first()
        if course is None:
            raise SystemExit("No teacher course found. Run `python -m db.seed` first.")

        feed = json.loads(feed_path.read_text(encoding="utf-8"))

        updated_concepts = inserted_concepts = 0
        for cm in feed.get("concept_metrics", []):
            row = (
                db.query(ConceptMetric)
                .filter(
                    ConceptMetric.course_id == course.id,
                    ConceptMetric.concept == cm["concept"],
                )
                .first()
            )
            if row is not None:
                row.wrong_rate = cm["wrong_rate"]  # keep catalog text
                updated_concepts += 1
            else:
                db.add(
                    ConceptMetric(
                        course_id=course.id,
                        concept=cm["concept"],
                        wrong_rate=cm["wrong_rate"],
                        misconception="(synthetic-derived; pending teacher review)",
                        recommended_focus="(pending teacher review)",
                    )
                )
                inserted_concepts += 1

        upserted_students = 0
        for student in feed.get("students", []):
            row = (
                db.query(StudentProfile)
                .filter(
                    StudentProfile.course_id == course.id,
                    StudentProfile.student_code == student["student_code"],
                )
                .first()
            )
            if row is None:
                row = StudentProfile(
                    course_id=course.id, student_code=student["student_code"]
                )
                db.add(row)
            row.name = student["name"]
            row.average_score = student["average_score"]
            row.completion_rate = student["completion_rate"]
            row.strong_topics = json.dumps(student.get("strong_topics", []), ensure_ascii=False)
            row.weak_topics = json.dumps(student.get("weak_topics", []), ensure_ascii=False)
            row.recommended_action = _recommended_action(student.get("weak_topics", []))
            upserted_students += 1

        db.commit()
        print(
            f"Imported eval feed from {feed_path.name}: "
            f"concepts updated={updated_concepts} inserted={inserted_concepts}, "
            f"synthetic students upserted={upserted_students}"
        )
    finally:
        db.close()


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Import eval synthetic feed into teacher DB")
    parser.add_argument("--feed", default=str(DEFAULT_FEED), help="path to teacher_feed.json")
    args = parser.parse_args(argv)
    import_feed(Path(args.feed))


if __name__ == "__main__":
    main()
