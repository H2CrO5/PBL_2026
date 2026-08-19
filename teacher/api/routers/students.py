"""Student insight endpoints for teachers."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_teacher
from api.schemas.students import GradeOverrideRequest, GradeOverrideResponse, StudentInsightResponse
from db.database import get_db
from db.models import Course, StudentProfile, Teacher
from services import student_data
import config

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/insights", response_model=list[StudentInsightResponse])
def get_student_insights(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.teacher_id == teacher.id).first()
    if not course:
        return []

    try:
        feed = student_data.fetch_feed(course.external_key)
    except student_data.StudentDataUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    if feed is not None:
        students, _, _ = student_data.teacher_records(feed)
        students.sort(key=lambda student: student.average_score)
        data_source = "student-real-submissions"
    else:
        if not config.DEMO_MODE:
            raise HTTPException(
                status_code=503,
                detail="Student integration is required. Set TEACHER_DEMO_MODE=1 only for an intentional demo.",
            )
        students = (
            db.query(StudentProfile)
            .filter(StudentProfile.course_id == course.id)
            .order_by(StudentProfile.average_score.asc())
            .all()
        )
        data_source = "teacher-demo-data"
    return [
        StudentInsightResponse(
            id=s.id,
            student_code=s.student_code,
            name=s.name,
            average_score=s.average_score,
            completion_rate=s.completion_rate,
            strong_topics=json.loads(s.strong_topics),
            weak_topics=json.loads(s.weak_topics),
            recommended_action=s.recommended_action,
            recent_submissions=getattr(s, "recent_submissions", []),
            chat_summary=getattr(s, "chat_summary", []),
            data_source=data_source,
        )
        for s in students
    ]


@router.post("/submissions/{submission_id}/override", response_model=GradeOverrideResponse)
def override_submission_grade(
    submission_id: int,
    req: GradeOverrideRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.teacher_id == teacher.id).first()
    if course is None or not student_data.integration_enabled():
        raise HTTPException(status_code=503, detail="Student integration is not configured")
    # Confirm the submission is present in this teacher's course feed before
    # forwarding a write operation.
    try:
        feed = student_data.fetch_feed(course.external_key)
        allowed_ids = {
            item["submission_id"]
            for student in feed.get("students", [])
            for item in student.get("recent_submissions", [])
        }
        if submission_id not in allowed_ids:
            raise HTTPException(status_code=404, detail="Submission not found in this course")
        result = student_data.override_grade(
            submission_id, course.external_key, req.score, req.feedback
        )
    except student_data.StudentDataUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return GradeOverrideResponse(**result)
