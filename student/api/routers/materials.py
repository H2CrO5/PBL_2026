"""Authenticated, enrollment-scoped, teacher-published lecture materials."""

from collections import OrderedDict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.materials import (
    StudentLectureMaterialsResponse,
    StudentMaterialResponse,
)
from db.database import get_db
from db.models import Course, CourseMaterial, Enrollment, Lecture, Student


router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("", response_model=list[StudentLectureMaterialsResponse])
def get_student_materials(
    external_course_id: str | None = Query(default=None),
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return published materials only for the student's active courses."""
    course_query = (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(
            Enrollment.student_id == student.id,
            Enrollment.status == "active",
        )
    )
    if external_course_id:
        course_query = course_query.filter(Course.external_key == external_course_id)

    courses = course_query.order_by(Course.title.asc()).all()
    if external_course_id and not courses:
        raise HTTPException(status_code=404, detail="Course not found")
    if not courses:
        return []

    course_ids = [course.id for course in courses]
    rows = (
        db.query(CourseMaterial, Course, Lecture)
        .join(Course, Course.id == CourseMaterial.course_id)
        .outerjoin(
            Lecture,
            and_(
                Lecture.id == CourseMaterial.lecture_id,
                Lecture.course_id == Course.id,
            ),
        )
        .filter(
            CourseMaterial.course_id.in_(course_ids),
            CourseMaterial.student_visible.is_(True),
        )
        .order_by(
            Course.title.asc(),
            Lecture.lecture_number.asc(),
            CourseMaterial.created_at.asc(),
            CourseMaterial.id.asc(),
        )
        .all()
    )

    grouped: OrderedDict[
        tuple[int, int | None], StudentLectureMaterialsResponse
    ] = OrderedDict()
    for material, course, lecture in rows:
        key = (course.id, lecture.id if lecture else None)
        if key not in grouped:
            grouped[key] = StudentLectureMaterialsResponse(
                course_id=course.id,
                external_course_id=course.external_key,
                course_title=course.title,
                term=course.term,
                lecture_id=lecture.id if lecture else None,
                lecture_number=lecture.lecture_number if lecture else None,
                lecture_title=lecture.title if lecture else None,
            )
        grouped[key].materials.append(
            StudentMaterialResponse(
                id=material.id,
                external_material_id=material.external_key,
                title=material.title,
                material_type=material.material_type,
                content=material.content,
                ingestion_status=material.ingestion_status,
                created_at=material.created_at,
                updated_at=material.updated_at,
            )
        )

    return list(grouped.values())
