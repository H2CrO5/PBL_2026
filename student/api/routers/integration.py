"""Authenticated read-only endpoints consumed by the Teacher backend."""

import json
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session as DBSession

from api.schemas.integration import (
    AssignmentPublishRequest,
    AssignmentPublishResponse,
    AssignmentAnalyticsFeed,
    CourseSyncRequest,
    CourseSyncResponse,
    GradeOverrideRequest,
    GradeOverrideResponse,
    MaterialSyncRequest,
    MaterialSyncResponse,
    RagRetrieveRequest,
    RagRetrieveResponse,
    TeacherAnalyticsFeed,
)
from config import TEACHER_INTEGRATION_TOKEN
from db.database import get_db
from db.models import (
    Assignment,
    AuditLog,
    Course,
    CourseMaterial,
    Enrollment,
    Lecture,
    Student,
    Submission,
)
from services.course_rag import ingest_material, retrieve_course
from services.progress import latest_attempts
from llm.memory import build_student_memory
from services.teacher_analytics import build_teacher_feed

router = APIRouter(prefix="/integrations/teacher", tags=["integration"])


def require_teacher_integration(
    x_integration_token: str = Header(default=""),
) -> None:
    if not TEACHER_INTEGRATION_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Teacher integration is not configured",
        )
    if not secrets.compare_digest(x_integration_token, TEACHER_INTEGRATION_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid integration token",
        )


@router.get(
    "/analytics",
    response_model=TeacherAnalyticsFeed,
    dependencies=[Depends(require_teacher_integration)],
)
def teacher_analytics(
    external_course_id: str | None = Query(default=None),
    db: DBSession = Depends(get_db),
):
    """Return aggregate and recent real-submission data; never credentials."""
    return build_teacher_feed(db, external_course_id)


@router.get(
    "/assignments/{external_assignment_id}/analytics",
    response_model=AssignmentAnalyticsFeed,
    dependencies=[Depends(require_teacher_integration)],
)
def assignment_analytics(
    external_assignment_id: str,
    db: DBSession = Depends(get_db),
):
    assignments = db.query(Assignment).filter(
        Assignment.external_key.like(f"{external_assignment_id}:%")
    ).all()
    assignment_ids = [item.id for item in assignments]
    submissions = latest_attempts(
        db.query(Submission).filter(Submission.assignment_id.in_(assignment_ids or [-1])).all()
    )
    scores = [item.score for item in submissions]
    missing = []
    patterns = []
    for submission in submissions:
        missing.extend(json.loads(submission.missing_concepts or "[]"))
        if submission.teacher_error_pattern:
            patterns.append(submission.teacher_error_pattern)
    total_assigned = len(assignments)
    total_submitted = len(submissions)
    incorrect = sum(1 for item in submissions if not item.is_correct)
    return AssignmentAnalyticsFeed(
        external_assignment_id=external_assignment_id,
        total_assigned=total_assigned,
        total_submitted=total_submitted,
        completion_rate=round(100 * total_submitted / total_assigned, 1) if total_assigned else 0,
        average_score=round(sum(scores) / len(scores), 1) if scores else 0,
        wrong_rate=round(100 * incorrect / total_submitted, 1) if total_submitted else 0,
        missing_concepts=list(dict.fromkeys(missing)),
        error_patterns=list(dict.fromkeys(patterns)),
    )


def _audit(db: DBSession, action: str, resource_type: str, resource_id: str, details: dict):
    db.add(AuditLog(
        actor_type="teacher-service",
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=json.dumps(details, ensure_ascii=False),
    ))


def _upsert_course(db: DBSession, external_id: str, title: str, term: str) -> Course:
    course = db.query(Course).filter(Course.external_key == external_id).first()
    if course is None:
        course = Course(external_key=external_id, title=title, term=term)
        db.add(course)
        db.flush()
    else:
        course.title = title
        course.term = term
    return course


def _upsert_lecture(
    db: DBSession,
    course: Course,
    external_id: str,
    number: int,
    title: str,
) -> Lecture:
    lecture = db.query(Lecture).filter(
        Lecture.course_id == course.id,
        Lecture.external_key == external_id,
    ).first()
    if lecture is None:
        lecture = Lecture(
            course_id=course.id,
            external_key=external_id,
            lecture_number=number,
            title=title,
        )
        db.add(lecture)
        db.flush()
    else:
        lecture.lecture_number = number
        lecture.title = title
    return lecture


@router.post(
    "/courses/sync",
    response_model=CourseSyncResponse,
    dependencies=[Depends(require_teacher_integration)],
)
def sync_course(req: CourseSyncRequest, db: DBSession = Depends(get_db)):
    course = _upsert_course(db, req.external_course_id, req.title, req.term)
    enrolled = 0
    if req.enrolled_student_codes:
        students = db.query(Student).filter(Student.student_code.in_(req.enrolled_student_codes)).all()
        for student in students:
            enrollment = db.query(Enrollment).filter(
                Enrollment.course_id == course.id,
                Enrollment.student_id == student.id,
            ).first()
            if enrollment is None:
                db.add(Enrollment(course_id=course.id, student_id=student.id))
            else:
                enrollment.status = "active"
            enrolled += 1
    _audit(db, "course.sync", "course", req.external_course_id, {"enrolled": enrolled})
    db.commit()
    return CourseSyncResponse(
        course_id=course.id,
        external_course_id=course.external_key,
        enrolled_students=enrolled,
    )


@router.post(
    "/assignments/publish",
    response_model=AssignmentPublishResponse,
    dependencies=[Depends(require_teacher_integration)],
)
def publish_assignment(req: AssignmentPublishRequest, db: DBSession = Depends(get_db)):
    course = _upsert_course(db, req.external_course_id, req.course_title, req.term)
    lecture = _upsert_lecture(
        db, course, req.lecture_external_id, req.lecture_number, req.lecture_title
    )
    query = db.query(Student)
    if req.target_student_codes:
        query = query.filter(Student.student_code.in_(req.target_student_codes))
    students = query.order_by(Student.student_code).all()
    found_codes = {student.student_code for student in students}
    missing = sorted(set(req.target_student_codes) - found_codes)
    created = 0
    present = 0
    difficulty_map = {"supportive": "easy", "balanced": "medium", "challenging": "hard"}
    for student in students:
        enrollment = db.query(Enrollment).filter(
            Enrollment.course_id == course.id,
            Enrollment.student_id == student.id,
        ).first()
        if enrollment is None:
            db.add(Enrollment(course_id=course.id, student_id=student.id))
        assignment_key = f"{req.external_assignment_id}:{student.student_code}"
        existing = db.query(Assignment).filter(Assignment.external_key == assignment_key).first()
        if existing:
            present += 1
            continue
        db.add(Assignment(
            course_id=course.id,
            external_key=assignment_key,
            student_id=student.id,
            lecture_id=lecture.id,
            title=req.title,
            topic=req.target_concept,
            difficulty=difficulty_map.get(req.difficulty, req.difficulty),
            question_text=req.question_text,
            choices=json.dumps(req.choices, ensure_ascii=False) if req.choices else None,
            correct_answer=req.correct_answer,
            explanation=req.explanation,
            question_type=req.question_type,
            rubric=json.dumps(req.rubric, ensure_ascii=False),
            points=req.points,
            max_attempts=req.max_attempts,
            due_at=req.due_at,
            published_at=datetime.now(timezone.utc).replace(tzinfo=None),
        ))
        created += 1
    _audit(db, "assignment.publish", "assignment", req.external_assignment_id, {
        "created": created, "already_present": present, "missing": missing,
    })
    db.commit()
    return AssignmentPublishResponse(
        external_assignment_id=req.external_assignment_id,
        created=created,
        already_present=present,
        missing_student_codes=missing,
    )


@router.post(
    "/materials/sync",
    response_model=MaterialSyncResponse,
    dependencies=[Depends(require_teacher_integration)],
)
def sync_material(req: MaterialSyncRequest, db: DBSession = Depends(get_db)):
    if req.audience == "teacher":
        existing = db.query(CourseMaterial).filter(
            CourseMaterial.external_key == req.external_material_id
        ).first()
        removed_id = existing.id if existing else None
        if existing is not None:
            db.delete(existing)
        _audit(db, "material.unsync", "material", req.external_material_id, {
            "reason": "teacher_only",
            "removed": existing is not None,
        })
        db.commit()
        return MaterialSyncResponse(
            material_id=removed_id,
            external_material_id=req.external_material_id,
            ingestion_status="teacher_only",
            chunk_count=0,
        )

    course = _upsert_course(db, req.external_course_id, req.course_title, req.term)
    lecture = _upsert_lecture(
        db, course, req.lecture_external_id, req.lecture_number, req.lecture_title
    )
    material = db.query(CourseMaterial).filter(
        CourseMaterial.external_key == req.external_material_id
    ).first()
    if material is None:
        material = CourseMaterial(
            external_key=req.external_material_id,
            course_id=course.id,
            lecture_id=lecture.id,
            title=req.title,
            material_type=req.material_type,
            audience="student",
            content=req.content,
        )
        db.add(material)
        db.flush()
    else:
        material.course_id = course.id
        material.lecture_id = lecture.id
        material.title = req.title
        material.material_type = req.material_type
        material.audience = "student"
        material.content = req.content
    ingestion_status = ingest_material(db, material)
    _audit(db, "material.sync", "material", req.external_material_id, {
        "ingestion_status": ingestion_status,
    })
    db.commit()
    db.refresh(material)
    return MaterialSyncResponse(
        material_id=material.id,
        external_material_id=material.external_key,
        ingestion_status=material.ingestion_status,
        chunk_count=len(material.chunks),
    )


@router.post(
    "/rag/retrieve",
    response_model=RagRetrieveResponse,
    dependencies=[Depends(require_teacher_integration)],
)
def retrieve_rag_context(req: RagRetrieveRequest, db: DBSession = Depends(get_db)):
    """Return course-scoped chunks to other trusted backend services."""
    course = db.query(Course).filter(Course.external_key == req.external_course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return RagRetrieveResponse(
        external_course_id=course.external_key,
        chunks=retrieve_course(db, course.id, req.query, top_k=req.top_k),
    )


@router.post(
    "/submissions/{submission_id}/override",
    response_model=GradeOverrideResponse,
    dependencies=[Depends(require_teacher_integration)],
)
def override_grade(
    submission_id: int,
    req: GradeOverrideRequest,
    db: DBSession = Depends(get_db),
):
    submission = (
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(Course, Assignment.course_id == Course.id)
        .filter(
            Submission.id == submission_id,
            Course.external_key == req.external_course_id,
        )
        .first()
    )
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.auto_score is None:
        submission.auto_score = submission.score
        submission.auto_feedback = submission.feedback
    submission.score = req.score
    submission.feedback = req.feedback
    submission.is_correct = req.score >= 60
    submission.status = "graded"
    submission.grading_source = "teacher_override"
    submission.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.flush()
    student = submission.student
    latest = latest_attempts(
        db.query(Submission).filter(Submission.student_id == student.id).all()
    )
    student.overall_score = round(sum(item.score for item in latest) / len(latest), 1)
    student.total_answered = len(latest)
    student.total_correct = sum(1 for item in latest if item.is_correct)
    memory = build_student_memory(db, student)
    student.weak_topics = json.dumps(memory["weak_topics"], ensure_ascii=False)
    student.strong_topics = json.dumps(memory["strong_topics"], ensure_ascii=False)
    _audit(db, "grade.override", "submission", str(submission.id), {"score": req.score})
    db.commit()
    return GradeOverrideResponse(
        submission_id=submission.id,
        score=submission.score,
        feedback=submission.feedback,
        grading_source=submission.grading_source,
    )
