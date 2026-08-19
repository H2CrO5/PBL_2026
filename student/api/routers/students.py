"""Student profile aliases matching the shared backend contract."""

from collections import defaultdict
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.assignments import AssignmentResponse, HistoryItem, HistoryResponse
from api.schemas.students import ConceptMastery, StudentMemoryResponse
from db.database import get_db
from db.models import Assignment, Course, Student, Submission
from services.progress import latest_attempts


router = APIRouter(prefix="/students", tags=["students"])


def _require_self(student_id: int, student: Student) -> None:
    if student_id != student.id:
        raise HTTPException(status_code=403, detail="Students may access only their own data")


def _course(db: DBSession, external_course_id: str | None) -> Course | None:
    if not external_course_id:
        return None
    course = db.query(Course).filter(Course.external_key == external_course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _memory(
    db: DBSession,
    student: Student,
    external_course_id: str | None,
) -> StudentMemoryResponse:
    course = _course(db, external_course_id)
    query = db.query(Submission).join(Assignment, Submission.assignment_id == Assignment.id).filter(
        Submission.student_id == student.id
    )
    if course:
        query = query.filter(Assignment.course_id == course.id)
    submissions = latest_attempts(query.all())

    by_concept: dict[str, list[Submission]] = defaultdict(list)
    for submission in submissions:
        by_concept[submission.assignment.topic].append(submission)
    mastery = [
        ConceptMastery(
            concept=concept,
            mastery_score=round(sum(item.score for item in items) / len(items), 1),
            attempts=len(items),
            evidence=[item.id for item in items],
        )
        for concept, items in sorted(by_concept.items())
    ]
    scores = [item.mastery_score for item in mastery]
    return StudentMemoryResponse(
        student_id=student.id,
        student_code=student.student_code,
        course_id=course.id if course else None,
        external_course_id=course.external_key if course else None,
        overall_score=round(sum(scores) / len(scores), 1) if scores else 0.0,
        concept_mastery=mastery,
        weak_topics=[item.concept for item in mastery if item.mastery_score < 60],
        strong_topics=[item.concept for item in mastery if item.mastery_score >= 80],
    )


@router.get("/me/memory", response_model=StudentMemoryResponse)
def my_memory(
    external_course_id: str | None = Query(default=None),
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    return _memory(db, student, external_course_id)


@router.get("/{student_id}/memory", response_model=StudentMemoryResponse)
def student_memory(
    student_id: int,
    external_course_id: str | None = Query(default=None),
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    _require_self(student_id, student)
    return _memory(db, student, external_course_id)


@router.get("/{student_id}/history", response_model=HistoryResponse)
def student_history(
    student_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    _require_self(student_id, student)
    submissions = latest_attempts(
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Submission.student_id == student.id)
        .order_by(Submission.submitted_at.desc())
        .limit(limit)
        .all()
    )
    return HistoryResponse(
        items=[
            HistoryItem(
                assignment_id=item.assignment_id,
                topic=item.assignment.topic,
                difficulty=item.assignment.difficulty,
                question_text=item.assignment.question_text,
                question_type=item.assignment.question_type,
                answer_text=item.answer_text,
                is_correct=item.is_correct,
                score=item.score,
                feedback=item.feedback,
                submitted_at=item.submitted_at,
            )
            for item in submissions
        ],
        total=len(submissions),
    )


@router.get("/{student_id}/assignments/current", response_model=list[AssignmentResponse])
def current_assignments(
    student_id: int,
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    _require_self(student_id, student)
    consumed = {
        item.assignment_id
        for item in latest_attempts(
            db.query(Submission).filter(Submission.student_id == student.id).all()
        )
    }
    assignments = (
        db.query(Assignment)
        .filter(Assignment.student_id == student.id, ~Assignment.id.in_(consumed or {-1}))
        .order_by(Assignment.created_at.desc())
        .all()
    )
    return [
        AssignmentResponse(
            id=item.id,
            topic=item.topic,
            difficulty=item.difficulty,
            question_text=item.question_text,
            choices=json.loads(item.choices) if item.choices else None,
            question_type=item.question_type,
            lecture_id=item.lecture_id,
            course_id=item.course_id,
            title=item.title,
            max_attempts=item.max_attempts,
            attempts_used=0,
            due_at=item.due_at,
            created_at=item.created_at,
        )
        for item in assignments
    ]
