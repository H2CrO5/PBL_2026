"""FastAPI dependency injection for auth and DB sessions."""

from datetime import datetime

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from db.database import get_db
from db.models import Session, Teacher


def get_current_teacher(
    authorization: str = Header(..., description="Bearer token"),
    db: DBSession = Depends(get_db),
) -> Teacher:
    """Validate bearer token and return the current teacher."""
    if not authorization.startswith("Bearer "):
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    teacher = db.query(Teacher).filter(Teacher.id == session.teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Teacher not found")

    return teacher

