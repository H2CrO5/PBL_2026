"""Canonical progress rules shared by Student UI and analytics."""

from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session as DBSession

from db.models import Assignment, Student, Submission


# Seed submissions form the deterministic demo student's historical baseline.
# Production databases do not contain seed rows, so this remains equivalent to
# real-only progress outside demo data.
STUDENT_PROGRESS_SOURCES = ("real", "seed")


def latest_attempts(
    submissions: list[Submission],
    allowed_sources: tuple[str, ...] = ("real",),
    allowed_statuses: tuple[str, ...] = ("graded",),
) -> list[Submission]:
    """Use the newest matching attempt per assignment."""
    latest: dict[int, Submission] = {}
    for submission in submissions:
        if (
            submission.source not in allowed_sources
            or submission.status not in allowed_statuses
        ):
            continue
        current = latest.get(submission.assignment_id)
        if current is None or (
            submission.attempt_number,
            submission.submitted_at,
            submission.id,
        ) > (
            current.attempt_number,
            current.submitted_at,
            current.id,
        ):
            latest[submission.assignment_id] = submission
    return sorted(latest.values(), key=lambda item: item.submitted_at, reverse=True)


def calculate_progress(
    db: DBSession,
    student: Student,
) -> dict:
    """Return one internally consistent snapshot of the student's progress."""
    total_assignments = db.query(Assignment).filter(
        Assignment.student_id == student.id
    ).count()
    submissions = latest_attempts(
        db.query(Submission).filter(Submission.student_id == student.id).all(),
        allowed_sources=STUDENT_PROGRESS_SOURCES,
    )
    scores = [item.score for item in submissions]
    topic_scores_raw: dict[str, list[float]] = defaultdict(list)
    for submission in submissions:
        topic_scores_raw[submission.assignment.topic].append(submission.score)
    topic_scores = {
        topic: round(sum(values) / len(values), 1)
        for topic, values in topic_scores_raw.items()
    }
    completed = len(submissions)
    total_correct = sum(1 for item in submissions if item.is_correct)
    return {
        "overall_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
        "total_assignments": total_assignments,
        "completed_assignments": completed,
        "pending_assignments": max(0, total_assignments - completed),
        "completion_rate": round(100.0 * completed / total_assignments, 1)
        if total_assignments else 0.0,
        "total_correct": total_correct,
        "accuracy": round(100.0 * total_correct / completed, 1) if completed else 0.0,
        "topic_scores": topic_scores,
        "weak_topics": sorted(topic for topic, score in topic_scores.items() if score < 60),
        "strong_topics": sorted(topic for topic, score in topic_scores.items() if score >= 80),
        "submissions": submissions,
    }


def apply_progress(student: Student, progress: dict) -> None:
    """Keep the denormalized Student columns aligned with canonical progress."""
    import json

    student.total_answered = progress["completed_assignments"]
    student.total_correct = progress["total_correct"]
    student.overall_score = progress["overall_score"]
    student.weak_topics = json.dumps(progress["weak_topics"], ensure_ascii=False)
    student.strong_topics = json.dumps(progress["strong_topics"], ensure_ascii=False)


def build_progress_timeline(
    db: DBSession,
    student: Student,
    since: datetime | None = None,
) -> list[dict]:
    """Reconstruct cumulative snapshots after each successfully graded attempt."""
    total_assignments = db.query(Assignment).filter(
        Assignment.student_id == student.id
    ).count()
    events = (
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(
            Submission.student_id == student.id,
            Submission.source.in_(STUDENT_PROGRESS_SOURCES),
            Submission.status == "graded",
        )
        .order_by(Submission.submitted_at, Submission.attempt_number, Submission.id)
        .all()
    )
    current: dict[int, Submission] = {}
    points = []
    for event in events:
        current[event.assignment_id] = event
        if since and event.submitted_at < since:
            continue
        latest = list(current.values())
        scores = [item.score for item in latest]
        correct = sum(1 for item in latest if item.is_correct)
        topic_scores = [
            item.score for item in latest
            if item.assignment.topic == event.assignment.topic
        ]
        completed = len(latest)
        points.append({
            "submission_id": event.id,
            "assignment_id": event.assignment_id,
            "submitted_at": event.submitted_at,
            "topic": event.assignment.topic,
            "assignment_score": event.score,
            "overall_score": round(sum(scores) / len(scores), 1),
            "accuracy": round(100.0 * correct / completed, 1),
            "topic_mastery": round(sum(topic_scores) / len(topic_scores), 1),
            "completed_assignments": completed,
            "total_assignments": total_assignments,
            "completion_rate": round(100.0 * completed / total_assignments, 1)
            if total_assignments else 0.0,
        })
    return points
