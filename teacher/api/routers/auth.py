"""Authentication endpoints for teachers."""

import uuid
from datetime import datetime, timedelta

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_teacher
from api.schemas.auth import LoginRequest, LoginResponse, MessageResponse, TeacherResponse
from db.database import get_db
from db.models import Session, Teacher

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_EXPIRE_HOURS = 24


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: DBSession = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.teacher_code == req.teacher_code).first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not bcrypt.checkpw(req.password.encode(), teacher.password_hash.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = str(uuid.uuid4())
    db.add(Session(
        teacher_id=teacher.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS),
    ))
    db.commit()

    return LoginResponse(
        token=token,
        teacher=TeacherResponse(id=teacher.id, teacher_code=teacher.teacher_code, name=teacher.name),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    authorization: str = Header(...),
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    token = authorization.removeprefix("Bearer ")
    db.query(Session).filter(
        Session.teacher_id == teacher.id,
        Session.token == token,
    ).delete()
    db.commit()
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=TeacherResponse)
def get_me(teacher: Teacher = Depends(get_current_teacher)):
    return TeacherResponse(id=teacher.id, teacher_code=teacher.teacher_code, name=teacher.name)
