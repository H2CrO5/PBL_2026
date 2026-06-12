"""Material management endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_teacher
from api.schemas.materials import LectureResponse, MaterialCreateRequest, MaterialResponse
from db.database import get_db
from db.models import Course, Lecture, Material, Teacher

router = APIRouter(prefix="/materials", tags=["materials"])


def _material_response(material: Material) -> MaterialResponse:
    lecture = material.lecture
    return MaterialResponse(
        id=material.id,
        course_id=material.course_id,
        lecture_id=material.lecture_id,
        lecture_title=lecture.title,
        title=material.title,
        material_type=material.material_type,
        ingestion_status=material.ingestion_status,
        content_preview=material.content[:220],
        created_at=material.created_at,
    )


@router.get("/lectures", response_model=list[LectureResponse])
def get_lectures(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.teacher_id == teacher.id).first()
    if not course:
        return []

    lectures = db.query(Lecture).filter(Lecture.course_id == course.id).order_by(Lecture.lecture_number).all()
    return [
        LectureResponse(
            id=lecture.id,
            lecture_number=lecture.lecture_number,
            title=lecture.title,
            learning_objectives=json.loads(lecture.learning_objectives),
        )
        for lecture in lectures
    ]


@router.get("", response_model=list[MaterialResponse])
def get_materials(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.teacher_id == teacher.id).first()
    if not course:
        return []

    materials = (
        db.query(Material)
        .join(Lecture, Material.lecture_id == Lecture.id)
        .filter(Material.course_id == course.id)
        .order_by(Lecture.lecture_number, Material.id)
        .all()
    )
    return [_material_response(material) for material in materials]


@router.post("", response_model=MaterialResponse)
def create_material(
    req: MaterialCreateRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == req.course_id, Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    lecture = db.query(Lecture).filter(Lecture.id == req.lecture_id, Lecture.course_id == course.id).first()
    if not lecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")

    material = Material(
        course_id=course.id,
        lecture_id=lecture.id,
        title=req.title,
        material_type=req.material_type,
        content=req.content,
        ingestion_status="ready",
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return _material_response(material)

