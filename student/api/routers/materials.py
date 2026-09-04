"""Read-only, enrollment-scoped materials available to students."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.materials import StudentMaterialResponse
from db.database import get_db
from db.models import Course, CourseMaterial, Enrollment, Lecture, Student


router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("", response_model=list[StudentMaterialResponse])
def list_student_materials(
    external_course_id: str | None = Query(default=None),
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    query = (
        db.query(CourseMaterial)
        .join(Course, CourseMaterial.course_id == Course.id)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .outerjoin(Lecture, CourseMaterial.lecture_id == Lecture.id)
        .filter(
            Enrollment.student_id == student.id,
            Enrollment.status == "active",
            CourseMaterial.student_visible.is_(True),
        )
    )
    if external_course_id:
        query = query.filter(Course.external_key == external_course_id)

    materials = query.order_by(
        Course.title,
        Lecture.lecture_number,
        CourseMaterial.title,
    ).all()
    return [
        StudentMaterialResponse(
            id=material.id,
            external_material_id=material.external_key,
            external_course_id=material.course.external_key,
            course_title=material.course.title,
            lecture_id=material.lecture_id,
            lecture_number=material.lecture.lecture_number if material.lecture else None,
            lecture_title=material.lecture.title if material.lecture else None,
            title=material.title,
            material_type=material.material_type,
            content=material.content,
            updated_at=material.updated_at,
        )
        for material in materials
    ]

