"""Authentication endpoints."""

import json
import uuid
from datetime import datetime, timedelta

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.auth import LoginRequest, LoginResponse, MessageResponse, StudentResponse
from config import SESSION_EXPIRE_HOURS
from db.database import get_db
from db.models import Session, Student

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: DBSession = Depends(get_db)):
    """Authenticate a student and return a session token."""
    student = db.query(Student).filter(Student.student_code == req.student_code).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not bcrypt.checkpw(req.password.encode(), student.password_hash.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Create session
    token = str(uuid.uuid4())
    session = Session(
        student_id=student.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS),
    )
    db.add(session)
    db.commit()

    return LoginResponse(
        token=token,
        student=StudentResponse(
            id=student.id,
            student_code=student.student_code,
            name=student.name,
            overall_score=student.overall_score,
            total_answered=student.total_answered,
            total_correct=student.total_correct,
            weak_topics=json.loads(student.weak_topics),
            strong_topics=json.loads(student.strong_topics),
        ),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    authorization: str = Header(...),
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Delete only the caller's session so other devices remain signed in."""
    token = authorization.removeprefix("Bearer ")
    db.query(Session).filter(
        Session.student_id == student.id,
        Session.token == token,
    ).delete()
    db.commit()
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=StudentResponse)
def get_me(student: Student = Depends(get_current_student)):
    """Return the current authenticated student's info."""
    return StudentResponse(
        id=student.id,
        student_code=student.student_code,
        name=student.name,
        overall_score=student.overall_score,
        total_answered=student.total_answered,
        total_correct=student.total_correct,
        weak_topics=json.loads(student.weak_topics),
        strong_topics=json.loads(student.strong_topics),
    )
