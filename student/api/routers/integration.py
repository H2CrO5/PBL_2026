"""Authenticated read-only endpoints consumed by the Teacher backend."""

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.schemas.integration import TeacherAnalyticsFeed
from config import TEACHER_INTEGRATION_TOKEN
from db.database import get_db
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
def teacher_analytics(db: DBSession = Depends(get_db)):
    """Return aggregate and recent real-submission data; never credentials."""
    return build_teacher_feed(db)
