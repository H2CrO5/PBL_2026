"""Course-scoped aliases matching the shared API plan."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_teacher
from api.routers import analytics as analytics_routes
from api.routers.materials import _material_response, create_material
from api.routers.questions import _seed_response
from api.schemas.analytics import DashboardSummary
from api.schemas.materials import CourseMaterialCreateRequest, MaterialCreateRequest, MaterialResponse
from api.schemas.questions import QuestionSeedResponse
from db.database import get_db
from db.models import Course, Material, QuestionSeed, Teacher


router = APIRouter(prefix="/courses", tags=["courses"])


def _owned_course(course_id: int, teacher: Teacher, db: DBSession) -> Course:
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.teacher_id == teacher.id,
    ).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}/analytics/class", response_model=DashboardSummary)
def class_analytics(
    course_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    _owned_course(course_id, teacher, db)
    return analytics_routes.dashboard(teacher, db, course_id)


@router.get("/{course_id}/assignments", response_model=list[QuestionSeedResponse])
def course_assignments(
    course_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    _owned_course(course_id, teacher, db)
    seeds = db.query(QuestionSeed).filter(QuestionSeed.course_id == course_id).all()
    return [_seed_response(seed) for seed in seeds]


@router.get("/{course_id}/materials", response_model=list[MaterialResponse])
def course_materials(
    course_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    _owned_course(course_id, teacher, db)
    materials = db.query(Material).filter(Material.course_id == course_id).all()
    return [_material_response(material) for material in materials]


@router.post("/{course_id}/materials", response_model=MaterialResponse)
def add_course_material(
    course_id: int,
    req: CourseMaterialCreateRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    _owned_course(course_id, teacher, db)
    return create_material(
        MaterialCreateRequest(course_id=course_id, **req.model_dump()),
        teacher,
        db,
    )
