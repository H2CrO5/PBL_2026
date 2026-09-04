"""Student profile aliases matching the shared backend contract."""

from collections import defaultdict
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.assignments import AssignmentResponse, HistoryItem, HistoryResponse
from api.schemas.students import ConceptMastery, StudentCourseResponse, StudentMemoryResponse
from db.database import get_db
from db.models import Assignment, Course, Enrollment, Student, Submission
from services.progress import STUDENT_PROGRESS_SOURCES, latest_attempts


router = APIRouter(prefix="/students", tags=["students"])


def _require_self(student_id: int, student: Student) -> None:
    if student_id != student.id:
        raise HTTPException(status_code=403, detail="Students may access only their own data")


def _course(db: DBSession, student: Student, external_course_id: str | None) -> Course | None:
    if not external_course_id:
        return None
    course = (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(
            Course.external_key == external_course_id,
            Enrollment.student_id == student.id,
            Enrollment.status == "active",
        )
        .first()
    )
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _memory(
    db: DBSession,
    student: Student,
    external_course_id: str | None,
) -> StudentMemoryResponse:
    course = _course(db, student, external_course_id)
    query = db.query(Submission).join(Assignment, Submission.assignment_id == Assignment.id).filter(
        Submission.student_id == student.id
    )
    if course:
        query = query.filter(Assignment.course_id == course.id)
    submissions = latest_attempts(
        query.all(),
        allowed_sources=STUDENT_PROGRESS_SOURCES,
    )

    by_concept: dict[str, list[Submission]] = defaultdict(list)
    for submission in submissions:
        by_concept[submission.assignment.topic].append(submission)
    mastery = [
        ConceptMastery(
            concept=concept,
            mastery_score=round(sum(item.score for item in items) / len(items), 1),
            attempts=len(items),
            # Evidence IDs are a stable API value even when multiple rows have
            # the same database-generated timestamp.
            evidence=sorted(item.id for item in items),
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


@router.get("/me/courses", response_model=list[StudentCourseResponse])
def my_courses(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    courses = (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.student_id == student.id, Enrollment.status == "active")
        .order_by(Course.title.asc())
        .all()
    )
    return [
        StudentCourseResponse(
            id=course.id,
            external_course_id=course.external_key,
            title=course.title,
            term=course.term,
        )
        for course in courses
    ]


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
    external_course_id: str | None = Query(default=None),
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    _require_self(student_id, student)
    course = _course(db, student, external_course_id)
    query = (
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Submission.student_id == student.id)
    )
    if course:
        query = query.filter(Assignment.course_id == course.id)
    submissions = latest_attempts(
        query.order_by(Submission.submitted_at.desc()).limit(limit).all(),
        allowed_sources=STUDENT_PROGRESS_SOURCES,
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
                max_score=item.max_score,
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
            db.query(Submission).filter(Submission.student_id == student.id).all(),
            allowed_sources=STUDENT_PROGRESS_SOURCES,
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
            external_assignment_id=item.external_key,
            topic=item.topic,
            difficulty=item.difficulty,
            question_text=item.question_text,
            choices=json.loads(item.choices) if item.choices else None,
            question_type=item.question_type,
            lecture_id=item.lecture_id,
            course_id=item.course_id,
            title=item.title,
            points=item.points,
            max_attempts=item.max_attempts,
            attempts_used=0,
            due_at=item.due_at,
            created_at=item.created_at,
        )
        for item in assignments
    ]
