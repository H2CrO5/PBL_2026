"""Assignment submission and history endpoints.

Assignments are pre-created (by teacher or seed data) and assigned to students.
Students browse pending assignments, answer them, and receive LLM-graded feedback.
"""

import json
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.assignments import (
    AssignmentResponse,
    BatchSubmissionRequest,
    BatchSubmissionResponse,
    HistoryAssignment,
    HistoryItem,
    HistoryLectureGroup,
    HistoryResponse,
    LectureAssignments,
    LectureInfo,
    SubmissionResponse,
    SharedSubmissionRequest,
    SubmitRequest,
)
from db.database import get_db
from db.models import Assignment, Lecture, Student, Submission
from llm import bedrock_client, prompts
from llm.memory import build_student_memory
from services.course_rag import retrieve_course

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _assignment_response(db: DBSession, assignment: Assignment, student_id: int) -> AssignmentResponse:
    attempts_used = db.query(Submission).filter(
        Submission.assignment_id == assignment.id,
        Submission.student_id == student_id,
    ).count()
    return AssignmentResponse(
        id=assignment.id,
        external_assignment_id=assignment.external_key,
        topic=assignment.topic,
        difficulty=assignment.difficulty,
        question_text=assignment.question_text,
        choices=json.loads(assignment.choices) if assignment.choices else None,
        question_type=assignment.question_type,
        lecture_id=assignment.lecture_id,
        course_id=assignment.course_id,
        title=assignment.title,
        points=assignment.points,
        max_attempts=assignment.max_attempts,
        attempts_used=attempts_used,
        due_at=assignment.due_at,
        created_at=assignment.created_at,
    )


@router.get("/pending", response_model=list[AssignmentResponse])
def get_pending(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return assignments that the student has not yet submitted."""
    exhausted_ids = (
        db.query(Submission.assignment_id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(
            Submission.student_id == student.id,
            Submission.status.in_(["grading", "graded"]),
        )
        .group_by(Submission.assignment_id, Assignment.max_attempts)
        .having(func.count(Submission.id) >= Assignment.max_attempts)
        .scalar_subquery()
    )

    pending = (
        db.query(Assignment)
        .filter(
            Assignment.student_id == student.id,
            ~Assignment.id.in_(exhausted_ids),
        )
        .order_by(Assignment.created_at.desc())
        .all()
    )

    return [
        _assignment_response(db, a, student.id)
        for a in pending
    ]


@router.get("/pending/by-lecture", response_model=list[LectureAssignments])
def get_pending_by_lecture(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return pending assignments grouped by lecture."""
    exhausted_ids = (
        db.query(Submission.assignment_id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(
            Submission.student_id == student.id,
            Submission.status.in_(["grading", "graded"]),
        )
        .group_by(Submission.assignment_id, Assignment.max_attempts)
        .having(func.count(Submission.id) >= Assignment.max_attempts)
        .scalar_subquery()
    )

    pending = (
        db.query(Assignment)
        .filter(
            Assignment.student_id == student.id,
            ~Assignment.id.in_(exhausted_ids),
        )
        .order_by(Assignment.created_at.desc())
        .all()
    )

    # Group by lecture
    lecture_map: dict[int | None, list[Assignment]] = defaultdict(list)
    for a in pending:
        lecture_map[a.lecture_id].append(a)

    # Fetch lectures
    lecture_ids = [lid for lid in lecture_map.keys() if lid is not None]
    lectures = {
        lec.id: lec
        for lec in db.query(Lecture).filter(Lecture.id.in_(lecture_ids)).all()
    } if lecture_ids else {}

    result = []
    # Sort by lecture_number
    for lid in sorted(lecture_map.keys(), key=lambda x: (x is None, lectures.get(x, Lecture(lecture_number=0)).lecture_number if x else 0)):
        if lid is None:
            continue
        lec = lectures[lid]
        assignments = [
            _assignment_response(db, a, student.id)
            for a in lecture_map[lid]
        ]
        result.append(LectureAssignments(
            lecture=LectureInfo(
                id=lec.id,
                lecture_number=lec.lecture_number,
                title=lec.title,
                description=lec.description,
                lecture_date=lec.lecture_date,
                deadline=lec.deadline,
            ),
            assignments=assignments,
        ))

    # Append unassigned assignments under a virtual "その他" lecture
    if None in lecture_map:
        ungrouped = [
            _assignment_response(db, a, student.id)
            for a in lecture_map[None]
        ]
        result.append(LectureAssignments(
            lecture=LectureInfo(id=0, lecture_number=0, title="その他"),
            assignments=ungrouped,
        ))

    return result


@router.get("/history/by-lecture", response_model=list[HistoryLectureGroup])
def get_history_by_lecture(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return submitted assignments grouped by lecture with scores and feedback."""
    submissions = (
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Submission.student_id == student.id, Submission.status == "graded")
        .order_by(Submission.submitted_at.desc())
        .all()
    )

    # Group by lecture_id
    lecture_map: dict[int | None, list[Submission]] = defaultdict(list)
    for sub in submissions:
        lecture_map[sub.assignment.lecture_id].append(sub)

    # Fetch lectures
    lecture_ids = [lid for lid in lecture_map.keys() if lid is not None]
    lectures = {
        lec.id: lec
        for lec in db.query(Lecture).filter(Lecture.id.in_(lecture_ids)).all()
    } if lecture_ids else {}

    result = []
    for lid in sorted(
        lecture_map.keys(),
        key=lambda x: (x is None, lectures.get(x, Lecture(lecture_number=0)).lecture_number if x else 0),
    ):
        if lid is None:
            continue
        lec = lectures[lid]
        items = [
            HistoryAssignment(
                id=sub.assignment.id,
                topic=sub.assignment.topic,
                difficulty=sub.assignment.difficulty,
                question_text=sub.assignment.question_text,
                question_type=sub.assignment.question_type,
                answer_text=sub.answer_text,
                is_correct=sub.is_correct,
                score=sub.score,
                max_score=sub.max_score,
                feedback=sub.feedback,
                attempt_number=sub.attempt_number,
                grading_source=sub.grading_source,
                missing_concepts=json.loads(sub.missing_concepts or "[]"),
                submitted_at=sub.submitted_at,
            )
            for sub in lecture_map[lid]
        ]
        result.append(HistoryLectureGroup(
            lecture=LectureInfo(
                id=lec.id,
                lecture_number=lec.lecture_number,
                title=lec.title,
                description=lec.description,
                lecture_date=lec.lecture_date,
                deadline=lec.deadline,
            ),
            submissions=items,
        ))

    return result


@router.post("/submit", response_model=SubmissionResponse)
def submit_answer(
    req: SubmitRequest,
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Grade a student's answer using LLM and update stats."""
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == req.assignment_id, Assignment.student_id == student.id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # Allow a bounded number of attempts. Analytics use only the latest graded
    # attempt, so retries do not inflate averages or completion rates.
    consumed_attempts = (
        db.query(Submission)
        .filter(
            Submission.assignment_id == assignment.id,
            Submission.student_id == student.id,
            Submission.status.in_(["grading", "graded"]),
        )
        .count()
    )
    if consumed_attempts >= assignment.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum attempts reached ({assignment.max_attempts})",
        )

    attempt_number = db.query(Submission).filter(
        Submission.assignment_id == assignment.id,
        Submission.student_id == student.id,
    ).count() + 1
    submission = Submission(
        assignment_id=assignment.id,
        student_id=student.id,
        answer_text=req.answer_text,
        is_correct=False,
        score=0,
        feedback="Grading in progress",
        source="real",
        attempt_number=attempt_number,
        status="grading",
        max_score=100.0,
        grading_source="auto",
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Grade with LLM. Persist an explicit failure state so the answer is never
    # lost and a failed provider call does not consume a permitted graded retry.
    grading_chunks = (
        retrieve_course(
            db,
            assignment.course_id,
            f"{assignment.question_text}\n{req.answer_text}",
            top_k=3,
        )
        if assignment.course_id else []
    )
    course_context = "\n\n".join(
        f"[{item['source']} / {item.get('source_locator', 'chunk')}]\n{item['text']}"
        for item in grading_chunks
    ) or "No relevant synchronized course material was found."
    grade_prompt = prompts.GRADING_PROMPT.format(
        question_text=assignment.question_text,
        question_type=assignment.question_type,
        correct_answer=assignment.correct_answer,
        rubric=assignment.rubric,
        student_answer=req.answer_text,
        course_context=course_context,
    )
    try:
        grade_result = bedrock_client.invoke_json(
            prompt=grade_prompt,
            system=prompts.GRADING_SYSTEM,
            temperature=0.3,
        )
    except Exception as exc:
        submission.status = "grading_failed"
        submission.feedback = "Automatic grading is temporarily unavailable. Please retry."
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Automatic grading is temporarily unavailable; the answer was saved",
        ) from exc

    score = round(max(0.0, min(100.0, float(grade_result.get("score", 0)))), 1)
    is_correct = score >= 60.0
    feedback = str(grade_result.get("feedback") or "Review the model answer and rubric.")
    raw_missing = grade_result.get("missing_concepts", [])
    missing_concepts = (
        [str(item) for item in raw_missing if str(item).strip()]
        if isinstance(raw_missing, list) else []
    )
    raw_pattern = grade_result.get("teacher_error_pattern")
    teacher_error_pattern = str(raw_pattern) if raw_pattern else None

    submission.is_correct = is_correct
    submission.score = score
    submission.feedback = feedback
    submission.status = "graded"
    submission.auto_score = score
    submission.auto_feedback = feedback
    submission.missing_concepts = json.dumps(missing_concepts, ensure_ascii=False)
    submission.teacher_error_pattern = teacher_error_pattern
    # SessionLocal uses autoflush=False. Flush here so the current answer is
    # included in the memory recalculation below.
    db.flush()

    # Recalculate progress from the latest graded real attempt per assignment.
    from services.progress import latest_attempts
    latest = latest_attempts(
        db.query(Submission).filter(Submission.student_id == student.id).all()
    )
    all_scores = [item.score for item in latest]
    student.total_answered = len(latest)
    student.total_correct = sum(1 for item in latest if item.is_correct)
    student.overall_score = round(sum(all_scores) / len(all_scores), 1)

    # Update weak/strong topics
    memory = build_student_memory(db, student)
    student.weak_topics = json.dumps(memory["weak_topics"], ensure_ascii=False)
    student.strong_topics = json.dumps(memory["strong_topics"], ensure_ascii=False)

    db.commit()
    db.refresh(submission)

    return SubmissionResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        answer_text=submission.answer_text,
        is_correct=submission.is_correct,
        score=submission.score,
        max_score=submission.max_score,
        feedback=submission.feedback,
        student_feedback=submission.feedback,
        correct_answer=assignment.correct_answer,
        explanation=assignment.explanation,
        attempt_number=submission.attempt_number,
        attempts_remaining=max(0, assignment.max_attempts - submission.attempt_number),
        grading_source=submission.grading_source,
        missing_concepts=missing_concepts,
        submitted_at=submission.submitted_at,
    )


@router.post("/batch/submissions", response_model=BatchSubmissionResponse)
def create_batch_submissions(
    req: BatchSubmissionRequest,
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Submit and grade every question in one student action.

    The ownership and duplicate checks run before grading starts. Provider
    failures keep already-saved answers with an explicit failure status, so no
    student input is silently lost.
    """
    ids = [answer.assignment_id for answer in req.answers]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=422, detail="Duplicate assignment IDs are not allowed")
    owned = db.query(Assignment).filter(
        Assignment.id.in_(ids), Assignment.student_id == student.id
    ).count()
    if owned != len(ids):
        raise HTTPException(status_code=404, detail="One or more assignments were not found")

    results = [
        submit_answer(
            SubmitRequest(assignment_id=answer.assignment_id, answer_text=answer.answer_text),
            student,
            db,
        )
        for answer in req.answers
    ]
    return BatchSubmissionResponse(
        submissions=results,
        total_score=round(sum(result.score for result in results), 1),
        max_score=round(sum(result.max_score for result in results), 1),
    )


@router.post("/{assignment_id}/submissions", response_model=SubmissionResponse)
def create_shared_submission(
    assignment_id: int,
    req: SharedSubmissionRequest,
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Shared-contract alias; current assignments contain one question each."""
    answer_text = req.answer_text
    if not answer_text and req.answers:
        answer_text = req.answers[0].get("answer_text") or req.answers[0].get("answer")
    if not answer_text or not answer_text.strip():
        raise HTTPException(status_code=422, detail="An answer is required")
    return submit_answer(
        SubmitRequest(assignment_id=assignment_id, answer_text=answer_text),
        student,
        db,
    )


@router.get("/history", response_model=HistoryResponse)
def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return past submissions with assignment details."""
    total = (
        db.query(Submission)
        .filter(Submission.student_id == student.id, Submission.status == "graded")
        .count()
    )

    submissions = (
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Submission.student_id == student.id, Submission.status == "graded")
        .order_by(Submission.submitted_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [
        HistoryItem(
            assignment_id=sub.assignment.id,
            topic=sub.assignment.topic,
            difficulty=sub.assignment.difficulty,
            question_text=sub.assignment.question_text,
            question_type=sub.assignment.question_type,
            answer_text=sub.answer_text,
            is_correct=sub.is_correct,
            score=sub.score,
            max_score=sub.max_score,
            feedback=sub.feedback,
            submitted_at=sub.submitted_at,
        )
        for sub in submissions
    ]

    return HistoryResponse(items=items, total=total)
