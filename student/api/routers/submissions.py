"""Shared-contract submission read and grade endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.assignments import SubmissionResponse
from db.database import get_db
from db.models import Student, Submission


router = APIRouter(prefix="/submissions", tags=["submissions"])


def _response(submission: Submission) -> SubmissionResponse:
    assignment = submission.assignment
    return SubmissionResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        answer_text=submission.answer_text,
        is_correct=submission.is_correct,
        score=submission.score,
        max_score=submission.max_score,
        feedback=submission.feedback,
        student_feedback=submission.feedback,
        correct_answer=assignment.correct_answer,
        explanation=assignment.explanation,
        attempt_number=submission.attempt_number,
        attempts_remaining=max(0, assignment.max_attempts - submission.attempt_number),
        grading_source=submission.grading_source,
        missing_concepts=json.loads(submission.missing_concepts or "[]"),
        submitted_at=submission.submitted_at,
    )


def _owned_submission(
    submission_id: int,
    student: Student,
    db: DBSession,
) -> Submission:
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.student_id == student.id,
    ).first()
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission(
    submission_id: int,
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    return _response(_owned_submission(submission_id, student, db))


@router.post("/{submission_id}/grade", response_model=SubmissionResponse)
def grade_submission(
    submission_id: int,
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return the persisted grade; submission creation currently grades synchronously."""
    submission = _owned_submission(submission_id, student, db)
    if submission.status != "graded":
        raise HTTPException(
            status_code=409,
            detail=f"Submission cannot be returned as graded while status is {submission.status}",
        )
    return _response(submission)
