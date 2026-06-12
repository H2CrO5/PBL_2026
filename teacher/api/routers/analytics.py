"""Teacher analytics endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_teacher
from api.schemas.analytics import DashboardSummary, LecturePlanRequest, LecturePlanResponse, WeakConcept
from db.database import get_db
from db.models import ConceptMetric, Course, QuestionSeed, StudentProfile, Teacher, TeacherReport

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    students = db.query(StudentProfile).filter(StudentProfile.course_id == course.id).all()
    concepts = (
        db.query(ConceptMetric)
        .filter(ConceptMetric.course_id == course.id)
        .order_by(ConceptMetric.wrong_rate.desc())
        .all()
    )
    question_seeds = db.query(QuestionSeed).filter(QuestionSeed.course_id == course.id).all()

    avg_score = round(sum(s.average_score for s in students) / len(students), 1) if students else 0
    completion = round(sum(s.completion_rate for s in students) / len(students), 1) if students else 0

    return DashboardSummary(
        course_id=course.id,
        course_title=course.title,
        total_students=len(students),
        average_score=avg_score,
        completion_rate=completion,
        weak_concepts=[
            WeakConcept(
                concept=c.concept,
                wrong_rate=c.wrong_rate,
                misconception=c.misconception,
                recommended_focus=c.recommended_focus,
            )
            for c in concepts
        ],
        question_seed_count=len(question_seeds),
        required_question_count=sum(1 for seed in question_seeds if seed.seed_type == "required"),
    )


@router.post("/lecture-plan", response_model=LecturePlanResponse)
def lecture_plan(
    req: LecturePlanRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == req.course_id, Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    concepts = (
        db.query(ConceptMetric)
        .filter(ConceptMetric.course_id == course.id)
        .order_by(ConceptMetric.wrong_rate.desc())
        .limit(3)
        .all()
    )
    if not concepts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analytics data found")

    response = LecturePlanResponse(
        weakest_concepts=[c.concept for c in concepts],
        common_misconceptions=[c.misconception for c in concepts],
        recommended_focus=[c.recommended_focus for c in concepts],
        suggested_activity=(
            "Start the next lecture with a 10-minute misconception review, then ask students "
            "to grade two sample answers using the teacher-authored rubric seeds."
        ),
    )

    db.add(TeacherReport(
        course_id=course.id,
        question_seed_id=req.question_seed_id,
        weakest_concepts=json.dumps(response.weakest_concepts),
        common_misconceptions=json.dumps(response.common_misconceptions),
        recommended_focus=json.dumps(response.recommended_focus),
        suggested_activity=response.suggested_activity,
    ))
    db.commit()

    return response
