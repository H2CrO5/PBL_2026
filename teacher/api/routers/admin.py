"""Debug/admin endpoints for local teacher development."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_teacher
from db.database import get_db
from db.models import Course, Material, QuestionSeed, StudentProfile, Teacher

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/db/stats")
def db_stats(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    return {
        "courses": db.query(Course).count(),
        "materials": db.query(Material).count(),
        "students": db.query(StudentProfile).count(),
        "question_seeds": db.query(QuestionSeed).count(),
    }
