"""Teacher analytics endpoints.

Narration (typical errors, recommended actions, lecture-plan prose) is produced
by the LLM when config.USE_LLM is on (env var TEACHER_USE_LLM). All numeric
facts stay deterministic and authoritative; the LLM only writes prose around
them. Any LLM failure falls back to the rule-based narration below, so the
endpoints always return a valid response.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

import config
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
from services import analytics_llm
from services import student_data

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _analytics_records(db: DBSession, course: Course):
    try:
        feed = student_data.fetch_feed(course.external_key)
    except student_data.StudentDataUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    if feed is not None:
        students, concepts, generated_at = student_data.teacher_records(feed)
        return students, concepts, feed.get("data_source", "student-real-submissions"), generated_at, feed.get("score_trend", [])
    if not config.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Student integration is required. Set TEACHER_DEMO_MODE=1 only for an intentional demo.",
        )
    students = db.query(StudentProfile).filter(StudentProfile.course_id == course.id).all()
    concepts = (
        db.query(ConceptMetric)
        .filter(ConceptMetric.course_id == course.id)
        .order_by(ConceptMetric.wrong_rate.desc())
        .all()
    )
    return students, concepts, "teacher-demo-data", None, []


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


def _affected_students(concept: ConceptMetric, students: list[StudentProfile]) -> list[StudentProfile]:
    affected = [s for s in students if _student_matches_concept(s, concept.concept)]
    if not affected and students:
        affected = sorted(students, key=lambda s: s.average_score)[:2]
    return affected


def _concept_facts(
    concepts: list[ConceptMetric], students: list[StudentProfile]
) -> list[dict]:
    """Deterministic facts fed to the LLM for evidence narration."""
    return [
        {
            "concept": concept.concept,
            "wrong_rate": concept.wrong_rate,
            "misconception": concept.misconception,
            "affected_count": len(_affected_students(concept, students)),
        }
        for concept in concepts
    ]


def _evidence_for(
    concepts: list[ConceptMetric],
    students: list[StudentProfile],
    question_seeds: list[QuestionSeed],
    narration: dict | None = None,
) -> list[EvidenceItem]:
    narration = narration or {}
    evidence_items = []
    for concept in concepts:
        affected = _affected_students(concept, students)

        related_seeds = [
            seed.title
            for seed in question_seeds
            if seed.target_concept.lower() == concept.concept.lower()
            or concept.concept.lower() in seed.target_concept.lower()
            or seed.target_concept.lower() in concept.concept.lower()
        ]

        narrated = narration.get(concept.concept)
        if narrated:
            typical_errors = narrated["typical_errors"]
            recommended_action = narrated["recommended_action"]
        else:
            typical_errors = [
                concept.misconception,
                f"Observed in {len(affected)} student profile(s) in the local teacher demo data.",
            ]
            recommended_action = concept.recommended_focus

        confidence = _confidence_for(concept, len(affected))
        evidence_items.append(EvidenceItem(
            concept=concept.concept,
            confidence=confidence,
            evidence_status="persistent issue" if concept.wrong_rate >= 50 else "monitor",
            affected_students=[f"{s.name} ({s.student_code})" for s in affected],
            related_question_seeds=related_seeds,
            typical_errors=typical_errors,
            recommended_action=recommended_action,
        ))
    return evidence_items


def _teacher_action_facts(
    students: list[StudentProfile],
    concepts: list[ConceptMetric],
    question_seeds: list[QuestionSeed],
    completion_rate: float,
) -> list[dict]:
    """Deterministic action facts.

    Each carries authoritative priority/title, a rule-based reason/next_step
    (used as the fallback), and a `context` string handed to the LLM so it can
    rewrite reason/next_step while staying grounded in the numbers.
    """
    facts = []
    if concepts:
        top = concepts[0]
        facts.append({
            "priority": "high" if top.wrong_rate >= 55 else "medium",
            "title": f"Review {top.concept}",
            "reason": f"{top.wrong_rate:.0f}% wrong-rate signal in current analytics.",
            "next_step": top.recommended_focus,
            "context": (
                f"Concept '{top.concept}' has the highest wrong_rate at {top.wrong_rate:.0f}%. "
                f"Cataloged misconception: {top.misconception}"
            ),
        })

    low_students = [
        s for s in students
        if getattr(s, "total_submissions", 1) > 0 and s.average_score < 60
    ]
    if low_students:
        names = ", ".join(s.name for s in low_students[:3])
        facts.append({
            "priority": "high",
            "title": "Check low-performing students",
            "reason": f"{len(low_students)} student(s) are below 60 average score: {names}.",
            "next_step": "Open Individual Student Analysis and plan follow-up practice.",
            "context": f"{len(low_students)} student(s) are below 60 average score: {names}.",
        })

    required_count = sum(1 for seed in question_seeds if seed.seed_type == "required")
    if required_count < 2:
        facts.append({
            "priority": "medium",
            "title": "Add required question seeds",
            "reason": "Shared backend generation needs teacher constraints before assignment creation.",
            "next_step": "Add at least one required seed for each active lecture.",
            "context": f"Only {required_count} required question seed(s) exist; at least 2 are expected.",
        })

    if completion_rate < 85:
        facts.append({
            "priority": "medium",
            "title": "Monitor completion",
            "reason": f"Average completion is {completion_rate:.1f}%.",
            "next_step": "Use completion data after integration to identify missing submissions.",
            "context": f"Average completion rate is {completion_rate:.1f}% (below the 85% target).",
        })

    return facts[:4]


def _teacher_actions_from_facts(action_facts: list[dict]) -> list[TeacherAction]:
    """Build TeacherAction objects, replacing prose with LLM narration if enabled."""
    narrated = None
    if config.USE_LLM and action_facts:
        llm_facts = [
            {"priority": f["priority"], "title": f["title"], "context": f["context"]}
            for f in action_facts
        ]
        try:
            narrated = analytics_llm.narrate_teacher_actions(llm_facts)
        except Exception as exc:  # pragma: no cover - fallback path
            print(f"[analytics] teacher-actions LLM fallback: {type(exc).__name__}: {exc}")
            narrated = None

    if narrated:
        return [TeacherAction(**a) for a in narrated]
    return [
        TeacherAction(
            priority=f["priority"], title=f["title"], reason=f["reason"], next_step=f["next_step"]
        )
        for f in action_facts
    ]


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
    course_id: int | None = None,
):
    course_query = db.query(Course).filter(Course.teacher_id == teacher.id)
    if course_id is not None:
        course_query = course_query.filter(Course.id == course_id)
    course = course_query.first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    students, concepts, data_source, data_updated_at, score_trend = _analytics_records(db, course)
    question_seeds = db.query(QuestionSeed).filter(QuestionSeed.course_id == course.id).all()

    scored_students = [
        student for student in students
        if getattr(student, "total_submissions", 1) > 0
    ]
    avg_score = (
        round(sum(s.average_score for s in scored_students) / len(scored_students), 1)
        if scored_students else 0
    )
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
        teacher_actions=_teacher_actions_from_facts(
            _teacher_action_facts(students, concepts, question_seeds, completion)
        ),
        data_source=data_source,
        data_updated_at=data_updated_at,
        score_trend=score_trend,
    )


@router.get("/evidence", response_model=list[EvidenceItem])
def evidence(
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    students, concepts, _, _, _ = _analytics_records(db, course)
    question_seeds = db.query(QuestionSeed).filter(QuestionSeed.course_id == course.id).all()

    narration = None
    if config.USE_LLM and concepts:
        try:
            narration = analytics_llm.narrate_evidence(_concept_facts(concepts, students))
        except Exception as exc:  # pragma: no cover - fallback path
            print(f"[analytics] evidence LLM fallback: {type(exc).__name__}: {exc}")
            narration = None

    return _evidence_for(concepts, students, question_seeds, narration)


@router.post("/lecture-plan", response_model=LecturePlanResponse)
def lecture_plan(
    req: LecturePlanRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == req.course_id, Course.teacher_id == teacher.id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    _, all_concepts, _, _, _ = _analytics_records(db, course)
    concepts = all_concepts[:3]
    if not concepts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analytics data found")

    seeds_query = db.query(QuestionSeed).filter(QuestionSeed.course_id == course.id)
    if req.question_seed_id:
        seeds_query = seeds_query.filter(QuestionSeed.id == req.question_seed_id)
    seeds = seeds_query.order_by(QuestionSeed.created_at.desc()).limit(3).all()
    seed_titles = [seed.title for seed in seeds]
    primary_concept = concepts[0]
    primary_seed = seed_titles[0] if seed_titles else "a teacher-reviewed question seed"

    # Deterministic prose fallback (also used when the LLM is disabled/fails).
    prose = {
        "suggested_activity": (
            "Start the next lecture with a 10-minute misconception review, then ask students "
            "to grade two sample answers using the teacher-authored rubric seeds."
        ),
        "opening_activity": (
            f"Open with a 5-minute diagnostic question on {primary_concept.concept}, "
            "then ask students to explain the boundary or operation they used."
        ),
        "review_sequence": [f"Revisit misconception: {c.misconception}" for c in concepts],
        "in_class_check": f"Use '{primary_seed}' as a short in-class checkpoint before moving on.",
        "follow_up_actions": [
            "Ask low-confidence students to submit one corrected explanation.",
            "Use the evidence view to select students for individual follow-up.",
            "Keep required seeds locked when shared backend generates assignment variants.",
        ],
    }

    if config.USE_LLM:
        concept_facts = [
            {"concept": c.concept, "wrong_rate": c.wrong_rate, "misconception": c.misconception}
            for c in concepts
        ]
        try:
            prose = analytics_llm.narrate_lecture_plan(concept_facts, seed_titles)
        except Exception as exc:  # pragma: no cover - fallback path
            print(f"[analytics] lecture-plan LLM fallback: {type(exc).__name__}: {exc}")

    response = LecturePlanResponse(
        weakest_concepts=[c.concept for c in concepts],
        common_misconceptions=[c.misconception for c in concepts],
        recommended_focus=[c.recommended_focus for c in concepts],
        suggested_activity=prose["suggested_activity"],
        opening_activity=prose["opening_activity"],
        review_sequence=prose["review_sequence"],
        in_class_check=prose["in_class_check"],
        follow_up_actions=prose["follow_up_actions"],
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
