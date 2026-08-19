"""Shared-contract assignment aliases and assignment-level analytics."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_teacher
from api.schemas.assignments import AssignmentAnalyticsResponse
from api.schemas.questions import (
    AssignmentPublishRequest,
    AssignmentPublishResponse,
    QuestionGenerateRequest,
    QuestionSeedResponse,
)
from db.database import get_db
from db.models import PublishedAssignment, Teacher
from services import student_data
from api.routers import questions as question_routes


router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("/generate", response_model=QuestionSeedResponse)
def generate_assignment(
    req: QuestionGenerateRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    return question_routes.generate_question_draft(req, teacher, db)


@router.get("")
def list_published_assignments(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    rows = (
        db.query(PublishedAssignment)
        .filter(PublishedAssignment.course.has(teacher_id=teacher.id))
        .order_by(PublishedAssignment.published_at.desc())
        .all()
    )
    return [
        {
            "id": item.id,
            "external_assignment_id": item.external_key,
            "title": item.question_seed.title,
            "target_concept": item.question_seed.target_concept,
            "status": item.status,
            "published_at": item.published_at,
        }
        for item in rows
    ]


@router.post("/{assignment_id}/publish", response_model=AssignmentPublishResponse)
def publish_assignment(
    assignment_id: int,
    req: AssignmentPublishRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    return question_routes.publish_question_seed(assignment_id, req, teacher, db)


@router.get("/{assignment_id}/analytics", response_model=AssignmentAnalyticsResponse)
def assignment_analytics(
    assignment_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    publication = db.query(PublishedAssignment).filter(
        PublishedAssignment.id == assignment_id,
    ).first()
    if publication is None or publication.course.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Published assignment not found")
    try:
        analytics = student_data.fetch_assignment_analytics(publication.external_key)
    except student_data.StudentDataUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    seed = publication.question_seed
    return AssignmentAnalyticsResponse(
        assignment_id=publication.id,
        title=seed.title,
        target_concept=seed.target_concept,
        **analytics,
    )
