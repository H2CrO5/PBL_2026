"""Material management endpoints."""

from io import BytesIO
import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_teacher
from api.schemas.materials import (
    LectureCreateRequest,
    LectureResponse,
    MaterialCreateRequest,
    MaterialResponse,
    MaterialSyncAllResponse,
    MaterialSyncResponse,
)
from db.database import get_db
from db.models import Course, Lecture, Material, Teacher
from services import student_data
from services import material_storage
from config import MAX_MATERIAL_UPLOAD_BYTES

router = APIRouter(prefix="/materials", tags=["materials"])


def _lecture_response(lecture: Lecture) -> LectureResponse:
    return LectureResponse(
        id=lecture.id,
        lecture_number=lecture.lecture_number,
        title=lecture.title,
        learning_objectives=json.loads(lecture.learning_objectives),
    )


def _material_response(material: Material) -> MaterialResponse:
    lecture = material.lecture
    return MaterialResponse(
        id=material.id,
        external_key=material.external_key,
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
    return [_lecture_response(lecture) for lecture in lectures]


@router.post("/lectures", response_model=LectureResponse)
def create_lecture(
    req: LectureCreateRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(
        Course.id == req.course_id,
        Course.teacher_id == teacher.id,
    ).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    duplicate = db.query(Lecture).filter(
        Lecture.course_id == course.id,
        Lecture.lecture_number == req.lecture_number,
    ).first()
    if duplicate is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Lecture {req.lecture_number} already exists",
        )

    objectives = [item.strip() for item in req.learning_objectives if item.strip()]
    title = req.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Lecture title is required")
    if not objectives:
        raise HTTPException(status_code=422, detail="At least one learning objective is required")

    lecture = Lecture(
        course_id=course.id,
        lecture_number=req.lecture_number,
        title=title,
        learning_objectives=json.dumps(objectives, ensure_ascii=False),
    )
    db.add(lecture)
    db.commit()
    db.refresh(lecture)
    return _lecture_response(lecture)


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
        ingestion_status="local_only",
    )
    db.add(material)
    db.flush()
    material.external_key = f"{course.external_key}:material-{material.id}"
    if student_data.integration_enabled():
        try:
            result = student_data.sync_material(_sync_payload(material))
            material.ingestion_status = result["ingestion_status"]
        except student_data.StudentDataUnavailable:
            material.ingestion_status = "sync_failed"
    db.commit()
    db.refresh(material)
    return _material_response(material)


def _extract_upload(filename: str, content: bytes) -> tuple[str, str]:
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8"), "note"
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        pages = [
            f"[Page {index}]\n{page.extract_text() or ''}"
            for index, page in enumerate(reader.pages, start=1)
        ]
        return "\n\n".join(pages), "book"
    if suffix == ".pptx":
        from pptx import Presentation

        presentation = Presentation(BytesIO(content))
        slides = []
        for index, slide in enumerate(presentation.slides, start=1):
            text_items = [
                shape.text for shape in slide.shapes
                if hasattr(shape, "text") and shape.text.strip()
            ]
            slides.append(f"[Slide {index}]\n" + "\n".join(text_items))
        return "\n\n".join(slides), "slide"
    raise HTTPException(status_code=415, detail="Supported files: PDF, PPTX, MD, TXT")


@router.post("/upload", response_model=MaterialResponse)
async def upload_material(
    course_id: int = Form(...),
    lecture_id: int = Form(...),
    title: str = Form(""),
    file: UploadFile = File(...),
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.teacher_id == teacher.id,
    ).first()
    lecture = db.query(Lecture).filter(
        Lecture.id == lecture_id,
        Lecture.course_id == course_id,
    ).first()
    if course is None or lecture is None:
        raise HTTPException(status_code=404, detail="Course or lecture not found")
    raw = await file.read(MAX_MATERIAL_UPLOAD_BYTES + 1)
    if len(raw) > MAX_MATERIAL_UPLOAD_BYTES:
        limit_mb = MAX_MATERIAL_UPLOAD_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"Material file is too large (maximum {limit_mb} MB)",
        )
    try:
        extracted, material_type = _extract_upload(file.filename or "material.txt", raw)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Material file could not be parsed") from exc
    if not extracted.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from this file")
    material = Material(
        course_id=course.id,
        lecture_id=lecture.id,
        title=title.strip() or Path(file.filename or "Material").stem,
        material_type=material_type,
        source_path=material_storage.store_original(
            file.filename or "material",
            raw,
            course.external_key or f"course-{course.id}",
        ),
        content=extracted,
        ingestion_status="local_only",
    )
    db.add(material)
    db.flush()
    material.external_key = f"{course.external_key}:material-{material.id}"
    if student_data.integration_enabled():
        try:
            result = student_data.sync_material(_sync_payload(material))
            material.ingestion_status = result["ingestion_status"]
        except student_data.StudentDataUnavailable:
            material.ingestion_status = "sync_failed"
    db.commit()
    db.refresh(material)
    return _material_response(material)


def _sync_payload(material: Material) -> dict:
    return {
        "external_material_id": material.external_key,
        "external_course_id": material.lecture.course.external_key,
        "course_title": material.lecture.course.title,
        "term": material.lecture.course.term,
        "lecture_external_id": (
            f"{material.lecture.course.external_key}:lecture-{material.lecture.id}"
        ),
        "lecture_number": material.lecture.lecture_number,
        "lecture_title": material.lecture.title,
        "title": material.title,
        "material_type": material.material_type,
        "content": material.content,
    }


@router.post("/sync-all", response_model=MaterialSyncAllResponse)
def sync_all_materials(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    if not student_data.integration_enabled():
        raise HTTPException(status_code=503, detail="Student integration is not configured")
    materials = (
        db.query(Material)
        .join(Course, Material.course_id == Course.id)
        .filter(Course.teacher_id == teacher.id)
        .all()
    )
    synced = failed = chunks = 0
    for material in materials:
        try:
            result = student_data.sync_material(_sync_payload(material))
            material.ingestion_status = result["ingestion_status"]
            chunks += result["chunk_count"]
            synced += 1
        except student_data.StudentDataUnavailable:
            material.ingestion_status = "sync_failed"
            failed += 1
    db.commit()
    return MaterialSyncAllResponse(synced=synced, failed=failed, chunks=chunks)


@router.post("/{material_id}/sync", response_model=MaterialSyncResponse)
def sync_material(
    material_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    material = (
        db.query(Material)
        .join(Course, Material.course_id == Course.id)
        .filter(Material.id == material_id, Course.teacher_id == teacher.id)
        .first()
    )
    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")
    if not student_data.integration_enabled():
        raise HTTPException(status_code=503, detail="Student integration is not configured")
    try:
        result = student_data.sync_material(_sync_payload(material))
    except student_data.StudentDataUnavailable as exc:
        material.ingestion_status = "sync_failed"
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    material.ingestion_status = result["ingestion_status"]
    db.commit()
    return MaterialSyncResponse(
        id=material.id,
        ingestion_status=material.ingestion_status,
        chunk_count=result["chunk_count"],
    )
