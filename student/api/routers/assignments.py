"""Assignment submission and history endpoints.

Assignments are pre-created (by teacher or seed data) and assigned to students.
Students browse pending assignments, answer them, and receive LLM-graded feedback.
"""

import json
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.assignments import (
    AssignmentResponse,
    HistoryAssignment,
    HistoryItem,
    HistoryLectureGroup,
    HistoryResponse,
    LectureAssignments,
    LectureInfo,
    SubmissionResponse,
    SubmitRequest,
)
from db.database import get_db
from db.models import Assignment, Lecture, Student, Submission
from llm import bedrock_client, prompts
from llm.memory import build_student_memory

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("/pending", response_model=list[AssignmentResponse])
def get_pending(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return assignments that the student has not yet submitted."""
    submitted_ids = (
        db.query(Submission.assignment_id)
        .filter(Submission.student_id == student.id)
        .scalar_subquery()
    )

    pending = (
        db.query(Assignment)
        .filter(
            Assignment.student_id == student.id,
            ~Assignment.id.in_(submitted_ids),
        )
        .order_by(Assignment.created_at.desc())
        .all()
    )

    return [
        AssignmentResponse(
            id=a.id,
            topic=a.topic,
            difficulty=a.difficulty,
            question_text=a.question_text,
            choices=json.loads(a.choices) if a.choices else None,
            question_type=a.question_type,
            lecture_id=a.lecture_id,
            created_at=a.created_at,
        )
        for a in pending
    ]


@router.get("/pending/by-lecture", response_model=list[LectureAssignments])
def get_pending_by_lecture(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return pending assignments grouped by lecture."""
    submitted_ids = (
        db.query(Submission.assignment_id)
        .filter(Submission.student_id == student.id)
        .scalar_subquery()
    )

    pending = (
        db.query(Assignment)
        .filter(
            Assignment.student_id == student.id,
            ~Assignment.id.in_(submitted_ids),
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
            AssignmentResponse(
                id=a.id,
                topic=a.topic,
                difficulty=a.difficulty,
                question_text=a.question_text,
                choices=json.loads(a.choices) if a.choices else None,
                question_type=a.question_type,
                lecture_id=a.lecture_id,
                created_at=a.created_at,
            )
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
            AssignmentResponse(
                id=a.id,
                topic=a.topic,
                difficulty=a.difficulty,
                question_text=a.question_text,
                choices=json.loads(a.choices) if a.choices else None,
                question_type=a.question_type,
                lecture_id=None,
                created_at=a.created_at,
            )
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
        .filter(Submission.student_id == student.id)
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
                feedback=sub.feedback,
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

    # Check for duplicate submission
    existing = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment.id, Submission.student_id == student.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already submitted an answer for this assignment",
        )

    # Grade with LLM
    grade_prompt = prompts.GRADING_PROMPT.format(
        question_text=assignment.question_text,
        question_type=assignment.question_type,
        correct_answer=assignment.correct_answer,
        student_answer=req.answer_text,
    )
    grade_result = bedrock_client.invoke_json(
        prompt=grade_prompt,
        system=prompts.GRADING_SYSTEM,
        temperature=0.3,
    )

    is_correct = grade_result.get("is_correct", False)
    score = float(grade_result.get("score", 0))
    feedback = grade_result.get("feedback", "")

    # Save submission
    submission = Submission(
        assignment_id=assignment.id,
        student_id=student.id,
        answer_text=req.answer_text,
        is_correct=is_correct,
        score=score,
        feedback=feedback,
    )
    db.add(submission)

    # Update student stats
    student.total_answered += 1
    if is_correct:
        student.total_correct += 1
    # Recalculate overall score as running average
    all_scores = [s.score for s in db.query(Submission).filter(Submission.student_id == student.id).all()]
    all_scores.append(score)
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
        feedback=submission.feedback,
        correct_answer=assignment.correct_answer,
        explanation=assignment.explanation,
        submitted_at=submission.submitted_at,
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
        .filter(Submission.student_id == student.id)
        .count()
    )

    submissions = (
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Submission.student_id == student.id)
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
            feedback=sub.feedback,
            submitted_at=sub.submitted_at,
        )
        for sub in submissions
    ]

    return HistoryResponse(items=items, total=total)
