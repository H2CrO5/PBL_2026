"""Teacher analytics endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_teacher
from api.schemas.analytics import (
    DashboardSummary,
    EvidenceItem,
    LecturePlanRequest,
    LecturePlanResponse,
    TeacherAction,
    WeakConcept,
)
from db.database import get_db
from db.models import ConceptMetric, Course, QuestionSeed, StudentProfile, Teacher, TeacherReport

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _load_list(raw_value: str) -> list[str]:
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _student_matches_concept(student: StudentProfile, concept: str) -> bool:
    concept_text = concept.lower()
    weak_text = " ".join(_load_list(student.weak_topics)).lower()
    if "edge" in concept_text:
        return any(term in weak_text for term in ("edge", "boundary", "empty"))
    if "decomposition" in concept_text:
        return "decomposition" in weak_text
    if "data-structure" in concept_text or "structure" in concept_text:
        return any(term in weak_text for term in ("dictionary", "stack", "queue", "list", "structure"))
    if "complexity" in concept_text:
        return "complexity" in weak_text
    return student.average_score < 70


def _confidence_for(concept: ConceptMetric, affected_count: int) -> str:
    if concept.wrong_rate >= 55 and affected_count >= 2:
        return "high confidence"
    if concept.wrong_rate >= 35 and affected_count >= 1:
        return "medium confidence"
    return "needs more evidence"


def _evidence_for(
    concepts: list[ConceptMetric],
    students: list[StudentProfile],
    question_seeds: list[QuestionSeed],
) -> list[EvidenceItem]:
    evidence_items = []
    for concept in concepts:
        affected = [s for s in students if _student_matches_concept(s, concept.concept)]
        if not affected and students:
            affected = sorted(students, key=lambda s: s.average_score)[:2]

        related_seeds = [
            seed.title
            for seed in question_seeds
            if seed.target_concept.lower() == concept.concept.lower()
            or concept.concept.lower() in seed.target_concept.lower()
            or seed.target_concept.lower() in concept.concept.lower()
        ]

        confidence = _confidence_for(concept, len(affected))
        evidence_items.append(EvidenceItem(
            concept=concept.concept,
            confidence=confidence,
            evidence_status="persistent issue" if concept.wrong_rate >= 50 else "monitor",
            affected_students=[f"{s.name} ({s.student_code})" for s in affected],
            related_question_seeds=related_seeds,
            typical_errors=[
                concept.misconception,
                f"Observed in {len(affected)} student profile(s) in the local teacher demo data.",
            ],
            recommended_action=concept.recommended_focus,
        ))
    return evidence_items


def _teacher_actions(
    students: list[StudentProfile],
    concepts: list[ConceptMetric],
    question_seeds: list[QuestionSeed],
    completion_rate: float,
) -> list[TeacherAction]:
    actions = []
    if concepts:
        top = concepts[0]
        actions.append(TeacherAction(
            priority="high" if top.wrong_rate >= 55 else "medium",
            title=f"Review {top.concept}",
            reason=f"{top.wrong_rate:.0f}% wrong-rate signal in current analytics.",
            next_step=top.recommended_focus,
        ))

    low_students = [s for s in students if s.average_score < 60]
    if low_students:
        names = ", ".join(s.name for s in low_students[:3])
        actions.append(TeacherAction(
            priority="high",
            title="Check low-performing students",
            reason=f"{len(low_students)} student(s) are below 60 average score: {names}.",
            next_step="Open Individual Student Analysis and plan follow-up practice.",
        ))

    required_count = sum(1 for seed in question_seeds if seed.seed_type == "required")
    if required_count < 2:
        actions.append(TeacherAction(
            priority="medium",
            title="Add required question seeds",
            reason="Shared backend generation needs teacher constraints before assignment creation.",
            next_step="Add at least one required seed for each active lecture.",
        ))

    if completion_rate < 85:
        actions.append(TeacherAction(
            priority="medium",
            title="Monitor completion",
            reason=f"Average completion is {completion_rate:.1f}%.",
            next_step="Use completion data after integration to identify missing submissions.",
        ))

    return actions[:4]


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    students = db.query(StudentProfile).filter(StudentProfile.course_id == course.id).all()
    concepts = (
        db.query(ConceptMetric)
        .filter(ConceptMetric.course_id == course.id)
        .order_by(ConceptMetric.wrong_rate.desc())
        .all()
    )
    question_seeds = db.query(QuestionSeed).filter(QuestionSeed.course_id == course.id).all()

    avg_score = round(sum(s.average_score for s in students) / len(students), 1) if students else 0
    completion = round(sum(s.completion_rate for s in students) / len(students), 1) if students else 0

    return DashboardSummary(
        course_id=course.id,
        course_title=course.title,
        total_students=len(students),
        average_score=avg_score,
        completion_rate=completion,
        weak_concepts=[
            WeakConcept(
                concept=c.concept,
                wrong_rate=c.wrong_rate,
                misconception=c.misconception,
                recommended_focus=c.recommended_focus,
            )
            for c in concepts
        ],
        question_seed_count=len(question_seeds),
        required_question_count=sum(1 for seed in question_seeds if seed.seed_type == "required"),
        teacher_actions=_teacher_actions(students, concepts, question_seeds, completion),
    )


@router.get("/evidence", response_model=list[EvidenceItem])
def evidence(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    concepts = (
        db.query(ConceptMetric)
        .filter(ConceptMetric.course_id == course.id)
        .order_by(ConceptMetric.wrong_rate.desc())
        .all()
    )
    students = db.query(StudentProfile).filter(StudentProfile.course_id == course.id).all()
    question_seeds = db.query(QuestionSeed).filter(QuestionSeed.course_id == course.id).all()
    return _evidence_for(concepts, students, question_seeds)


@router.post("/lecture-plan", response_model=LecturePlanResponse)
def lecture_plan(
    req: LecturePlanRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == req.course_id, Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    concepts = (
        db.query(ConceptMetric)
        .filter(ConceptMetric.course_id == course.id)
        .order_by(ConceptMetric.wrong_rate.desc())
        .limit(3)
        .all()
    )
    if not concepts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analytics data found")

    seeds_query = db.query(QuestionSeed).filter(QuestionSeed.course_id == course.id)
    if req.question_seed_id:
        seeds_query = seeds_query.filter(QuestionSeed.id == req.question_seed_id)
    seeds = seeds_query.order_by(QuestionSeed.created_at.desc()).limit(3).all()
    seed_titles = [seed.title for seed in seeds]
    primary_concept = concepts[0]
    primary_seed = seed_titles[0] if seed_titles else "a teacher-reviewed question seed"

    response = LecturePlanResponse(
        weakest_concepts=[c.concept for c in concepts],
        common_misconceptions=[c.misconception for c in concepts],
        recommended_focus=[c.recommended_focus for c in concepts],
        suggested_activity=(
            "Start the next lecture with a 10-minute misconception review, then ask students "
            "to grade two sample answers using the teacher-authored rubric seeds."
        ),
        opening_activity=(
            f"Open with a 5-minute diagnostic question on {primary_concept.concept}, "
            "then ask students to explain the boundary or operation they used."
        ),
        review_sequence=[
            f"Revisit misconception: {c.misconception}"
            for c in concepts
        ],
        in_class_check=f"Use '{primary_seed}' as a short in-class checkpoint before moving on.",
        follow_up_actions=[
            "Ask low-confidence students to submit one corrected explanation.",
            "Use the evidence view to select students for individual follow-up.",
            "Keep required seeds locked when shared backend generates assignment variants.",
        ],
        recommended_seed_titles=seed_titles,
    )

    db.add(TeacherReport(
        course_id=course.id,
        question_seed_id=req.question_seed_id,
        weakest_concepts=json.dumps(response.weakest_concepts),
        common_misconceptions=json.dumps(response.common_misconceptions),
        recommended_focus=json.dumps(response.recommended_focus),
        suggested_activity=response.suggested_activity,
    ))
    db.commit()

    return response
