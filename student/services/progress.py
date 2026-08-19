"""Canonical progress rules shared by Student and Teacher analytics."""

from db.models import Submission


def latest_attempts(submissions: list[Submission]) -> list[Submission]:
    """Use only the newest graded real attempt for each assignment."""
    latest: dict[int, Submission] = {}
    for submission in submissions:
        if submission.source != "real" or submission.status != "graded":
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
