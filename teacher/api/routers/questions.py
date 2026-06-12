"""Teacher question bank endpoints.

Teachers do not generate the final adaptive assignment here. They maintain
base questions, required questions, expected answers, and rubrics. The future
shared backend/student side uses these seeds plus materials and student memory
to generate personalized assignments.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_teacher
from api.schemas.questions import (
    GenerationContextResponse,
    GenerationMaterialResponse,
    QuestionSeedCreateRequest,
    QuestionSeedResponse,
)
from db.database import get_db
from db.models import ConceptMetric, Course, Lecture, Material, QuestionSeed, Teacher

router = APIRouter(prefix="/questions", tags=["questions"])


def _seed_response(seed: QuestionSeed) -> QuestionSeedResponse:
    return QuestionSeedResponse(
        id=seed.id,
        course_id=seed.course_id,
        lecture_id=seed.lecture_id,
        lecture_title=seed.lecture.title if seed.lecture else None,
        title=seed.title,
        target_concept=seed.target_concept,
        seed_type=seed.seed_type,
        difficulty=seed.difficulty,
        question_text=seed.question_text,
        expected_answer=seed.expected_answer,
        rubric=json.loads(seed.rubric),
        notes=seed.notes,
        created_at=seed.created_at,
    )


@router.get("", response_model=list[QuestionSeedResponse])
def get_question_seeds(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.teacher_id == teacher.id).first()
    if not course:
        return []

    seeds = (
        db.query(QuestionSeed)
        .filter(QuestionSeed.course_id == course.id)
        .order_by(QuestionSeed.created_at.desc())
        .all()
    )
    return [_seed_response(seed) for seed in seeds]


@router.post("", response_model=QuestionSeedResponse)
def create_question_seed(
    req: QuestionSeedCreateRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == req.course_id, Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    lecture = db.query(Lecture).filter(Lecture.id == req.lecture_id, Lecture.course_id == course.id).first()
    if not lecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")

    seed = QuestionSeed(
        course_id=course.id,
        lecture_id=lecture.id,
        title=req.title,
        target_concept=req.target_concept,
        seed_type=req.seed_type,
        difficulty=req.difficulty,
        question_text=req.question_text,
        expected_answer=req.expected_answer,
        rubric=json.dumps(req.rubric, ensure_ascii=False),
        notes=req.notes,
    )
    db.add(seed)
    db.commit()
    db.refresh(seed)
    return _seed_response(seed)


@router.get("/generation-context/{lecture_id}", response_model=GenerationContextResponse)
def get_generation_context(
    lecture_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    lecture = db.query(Lecture).filter(Lecture.id == lecture_id, Lecture.course_id == course.id).first()
    if not lecture:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lecture not found")

    materials = db.query(Material).filter(Material.lecture_id == lecture.id).all()
    concepts = (
        db.query(ConceptMetric)
        .filter(ConceptMetric.course_id == course.id)
        .order_by(ConceptMetric.wrong_rate.desc())
        .limit(4)
        .all()
    )
    seeds = (
        db.query(QuestionSeed)
        .filter(QuestionSeed.course_id == course.id, QuestionSeed.lecture_id == lecture.id)
        .order_by(QuestionSeed.created_at.desc())
        .all()
    )

    return GenerationContextResponse(
        course_id=course.id,
        lecture_id=lecture.id,
        lecture_title=lecture.title,
        learning_objectives=json.loads(lecture.learning_objectives),
        materials=[
            GenerationMaterialResponse(
                id=material.id,
                title=material.title,
                material_type=material.material_type,
                ingestion_status=material.ingestion_status,
            )
            for material in materials
        ],
        material_titles=[m.title for m in materials],
        weak_concepts=[c.concept for c in concepts],
        question_seeds=[_seed_response(seed) for seed in seeds],
        backend_instruction=(
            "Shared backend should generate adaptive assignments from uploaded materials, "
            "student memory, weak concepts, and teacher-authored base/required question seeds."
        ),
    )
