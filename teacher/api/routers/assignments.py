"""Shared-contract assignment aliases and assignment-level analytics."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_teacher
from api.schemas.assignments import AssignmentAnalyticsResponse
from api.schemas.questions import (
    AssignmentPublishRequest,
    AssignmentPublishResponse,
    AssignmentBatchPublishRequest,
    AssignmentBatchPublishResponse,
    QuestionGenerateRequest,
    QuestionGenerateBatchResponse,
    QuestionSeedResponse,
)
from db.database import get_db
from db.models import PublishedAssignment, QuestionSeed, Teacher
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


@router.post("/generate-batch", response_model=QuestionGenerateBatchResponse)
def generate_assignment_batch(
    req: QuestionGenerateRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    single = req.model_copy(update={"number_questions": 1})
    return QuestionGenerateBatchResponse(questions=[
        question_routes.generate_question_draft(single, teacher, db)
        for _ in range(req.number_questions)
    ])


@router.post("/publish-batch", response_model=AssignmentBatchPublishResponse)
def publish_assignment_batch(
    req: AssignmentBatchPublishRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    if len(req.seed_ids) != len(set(req.seed_ids)):
        raise HTTPException(status_code=422, detail="Duplicate question seed IDs are not allowed")
    publish_request = AssignmentPublishRequest(
        due_at=req.due_at,
        target_student_codes=req.target_student_codes,
    )
    results = [
        question_routes.publish_question_seed(seed_id, publish_request, teacher, db)
        for seed_id in req.seed_ids
    ]
    return AssignmentBatchPublishResponse(
        assignments=results,
        created_for_students=sum(item.created_for_students for item in results),
        already_present=sum(item.already_present for item in results),
        missing_student_codes=sorted({
            code for item in results for code in item.missing_student_codes
        }),
    )


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


@router.get("/{assignment_id}")
def get_assignment(
    assignment_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    publication = db.query(PublishedAssignment).filter(
        PublishedAssignment.id == assignment_id,
        PublishedAssignment.course.has(teacher_id=teacher.id),
    ).first()
    seed = publication.question_seed if publication else db.query(QuestionSeed).filter(
        QuestionSeed.id == assignment_id,
        QuestionSeed.course.has(teacher_id=teacher.id),
    ).first()
    if seed is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {
        "id": publication.id if publication else seed.id,
        "question_seed_id": seed.id,
        "external_assignment_id": publication.external_key if publication else None,
        "status": publication.status if publication else "draft",
        "course_id": seed.course_id,
        "lecture_id": seed.lecture_id,
        "title": seed.title,
        "target_concept": seed.target_concept,
        "difficulty": seed.difficulty,
        "question_text": seed.question_text,
        "correct_answer": seed.expected_answer,
        "rubric": json.loads(seed.rubric),
        "points": seed.points,
        "max_attempts": seed.max_attempts,
    }


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
