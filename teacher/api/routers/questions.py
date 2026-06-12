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
    QuestionSeedCandidateResponse,
    QuestionSeedCreateRequest,
    QuestionSeedResponse,
    ReadinessCheckResponse,
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


def _candidate_for(concept: str, lecture_title: str, required_missing: bool) -> QuestionSeedCandidateResponse:
    seed_type = "required" if required_missing else "base"
    difficulty = "balanced" if required_missing else "supportive"
    title = f"{concept} checkpoint"
    notes = (
        "Assessment scope: formative_checkpoint\n"
        "Variation policy: teacher_review_required\n"
        "Teacher priority: high\n"
        "Generated as a local candidate from completed lecture materials and analytics."
    )
    return QuestionSeedCandidateResponse(
        title=title,
        target_concept=concept,
        seed_type=seed_type,
        difficulty=difficulty,
        question_text=(
            f"For the lecture '{lecture_title}', answer a short question that demonstrates "
            f"understanding of {concept}. Include one explanation of your reasoning."
        ),
        expected_answer=(
            f"A correct answer should explicitly use the lecture concept {concept}, "
            "state the reasoning path, and handle the most likely misconception."
        ),
        rubric=[
            f"Uses {concept} accurately",
            "Explains reasoning instead of only giving a final answer",
            "Addresses the likely misconception or edge case",
        ],
        notes=notes,
        rationale=(
            "Suggested to reduce teacher workload: this candidate is not sent to students "
            "until the teacher reviews and saves it."
        ),
        assessment_scope="formative_checkpoint",
        variation_policy="teacher_review_required",
        teacher_priority="high" if required_missing else "normal",
    )


def _concept_matches_lecture(concept: str, lecture: Lecture) -> bool:
    objectives = " ".join(json.loads(lecture.learning_objectives)).lower()
    lecture_text = f"{lecture.title} {objectives}".lower()
    concept_text = concept.lower()
    keyword_map = {
        "edge": ("edge", "boundary", "constraint", "empty", "input", "output"),
        "decomposition": ("decomposition", "subproblem", "problem", "step"),
        "data": ("data structure", "lookup", "dictionary", "stack", "queue", "set"),
        "complexity": ("complexity", "growth", "trace", "traversal"),
    }
    for concept_key, keywords in keyword_map.items():
        if concept_key in concept_text:
            return any(keyword in lecture_text for keyword in keywords)
    concept_words = [word for word in concept_text.replace("-", " ").split() if len(word) > 4]
    return any(word in lecture_text for word in concept_words)


def _readiness_checks(
    lecture: Lecture,
    materials: list[Material],
    concepts: list[ConceptMetric],
    seeds: list[QuestionSeed],
) -> list[ReadinessCheckResponse]:
    objectives = json.loads(lecture.learning_objectives)
    ready_materials = [material for material in materials if material.ingestion_status == "ready"]
    required_seeds = [seed for seed in seeds if seed.seed_type == "required"]
    rubric_seeds = [seed for seed in seeds if seed.seed_type == "rubric_seed"]

    return [
        ReadinessCheckResponse(
            name="Completed materials",
            status="ready" if ready_materials else "blocked",
            detail=f"{len(ready_materials)} ready material(s) are available for this lecture.",
        ),
        ReadinessCheckResponse(
            name="Learning objectives",
            status="ready" if objectives else "blocked",
            detail=f"{len(objectives)} objective(s) are attached to this lecture.",
        ),
        ReadinessCheckResponse(
            name="Weak concept signal",
            status="ready" if concepts else "warning",
            detail=(
                f"{len(concepts)} concept signal(s) are available."
                if concepts else "No analytics signal yet; shared backend can only generate generic practice."
            ),
        ),
        ReadinessCheckResponse(
            name="Required question seed",
            status="ready" if required_seeds else "blocked",
            detail=(
                f"{len(required_seeds)} required seed(s) will constrain generation."
                if required_seeds else "Add at least one required seed before backend assignment generation."
            ),
        ),
        ReadinessCheckResponse(
            name="Rubric guidance",
            status="ready" if rubric_seeds else "warning",
            detail=(
                f"{len(rubric_seeds)} rubric seed(s) are available."
                if rubric_seeds else "No rubric seed yet; grading guidance may be weaker."
            ),
        ),
    ]


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
    required_missing = not any(seed.seed_type == "required" for seed in seeds)
    seeded_concepts = {seed.target_concept.lower() for seed in seeds}
    candidate_concepts = [
        concept.concept
        for concept in concepts
        if concept.concept.lower() not in seeded_concepts
        and _concept_matches_lecture(concept.concept, lecture)
    ][:3]
    if required_missing and concepts and _concept_matches_lecture(concepts[0].concept, lecture):
        candidate_concepts = [concepts[0].concept] + [
            concept for concept in candidate_concepts if concept != concepts[0].concept
        ]
    candidates = [
        _candidate_for(concept, lecture.title, required_missing and index == 0)
        for index, concept in enumerate(candidate_concepts)
    ]
    readiness_checks = _readiness_checks(lecture, materials, concepts, seeds)

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
        question_seed_candidates=candidates,
        readiness_checks=readiness_checks,
        ready_for_generation=all(check.status != "blocked" for check in readiness_checks),
        backend_instruction=(
            "Shared backend should generate adaptive assignments from uploaded materials, "
            "student memory, weak concepts, and teacher-authored base/required question seeds."
        ),
    )
