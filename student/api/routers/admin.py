"""Admin endpoints for viewing database tables (debug/development use)."""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from db.database import get_db
from db.models import Assignment, ChatMessage, Lecture, Student, Submission

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/db/students")
def get_students(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return all students (with sensitive fields masked)."""
    students = db.query(Student).order_by(Student.id).all()
    return [
        {
            "id": s.id,
            "student_code": s.student_code,
            "name": s.name,
            "overall_score": s.overall_score,
            "total_answered": s.total_answered,
            "total_correct": s.total_correct,
            "weak_topics": json.loads(s.weak_topics) if s.weak_topics else [],
            "strong_topics": json.loads(s.strong_topics) if s.strong_topics else [],
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in students
    ]


@router.get("/db/lectures")
def get_lectures(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return all lectures."""
    lectures = db.query(Lecture).order_by(Lecture.lecture_number).all()
    return [
        {
            "id": lec.id,
            "lecture_number": lec.lecture_number,
            "title": lec.title,
            "description": lec.description,
            "lecture_date": lec.lecture_date.isoformat() if lec.lecture_date else None,
            "deadline": lec.deadline.isoformat() if lec.deadline else None,
        }
        for lec in lectures
    ]


@router.get("/db/assignments")
def get_assignments(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Return all assignments."""
    assignments = db.query(Assignment).order_by(Assignment.id.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "student_id": a.student_id,
            "lecture_id": a.lecture_id,
            "topic": a.topic,
            "difficulty": a.difficulty,
            "question_type": a.question_type,
            "question_text": a.question_text[:100],
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in assignments
    ]


@router.get("/db/submissions")
def get_submissions(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Return all submissions."""
    submissions = db.query(Submission).order_by(Submission.id.desc()).limit(limit).all()
    return [
        {
            "id": s.id,
            "assignment_id": s.assignment_id,
            "student_id": s.student_id,
            "answer_text": s.answer_text[:100],
            "is_correct": s.is_correct,
            "score": s.score,
            "feedback": s.feedback[:100] if s.feedback else None,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        }
        for s in submissions
    ]


@router.get("/db/chat_messages")
def get_chat_messages(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Return all chat messages."""
    messages = db.query(ChatMessage).order_by(ChatMessage.id.desc()).limit(limit).all()
    return [
        {
            "id": m.id,
            "student_id": m.student_id,
            "role": m.role,
            "content": m.content[:100],
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]


@router.get("/db/stats")
def get_db_stats(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return record counts for all tables."""
    return {
        "students": db.query(Student).count(),
        "lectures": db.query(Lecture).count(),
        "assignments": db.query(Assignment).count(),
        "submissions": db.query(Submission).count(),
        "chat_messages": db.query(ChatMessage).count(),
    }
