"""FastAPI dependency injection for auth and DB sessions."""

from datetime import datetime

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from db.database import get_db
from db.models import Session, Student


def get_current_student(
    authorization: str | None = Header(None, description="Bearer token"),
    db: DBSession = Depends(get_db),
) -> Student:
    """Extract and validate the session token, returning the authenticated student."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '",
        )

    token = authorization[len("Bearer "):]

    session = (
        db.query(Session)
        .filter(Session.token == token, Session.expires_at > datetime.utcnow())
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    student = db.query(Student).filter(Student.id == session.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student not found",
        )

    return student
