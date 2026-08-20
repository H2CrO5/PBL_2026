"""Dashboard endpoints for student progress visualization."""

from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.dashboard import (
    DailyScore,
    DashboardSummary,
    TopicTrend,
    TrendsResponse,
)
from db.database import get_db
from db.models import Assignment, Student, Submission
from services.progress import latest_attempts

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return overall stats, accuracy, topic scores, and today's progress."""
    import json

    # Today's submissions
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_subs = (
        db.query(Submission)
        .filter(Submission.student_id == student.id, Submission.submitted_at >= today_start)
        .all()
    )

    # Topic scores
    all_subs = latest_attempts((
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Submission.student_id == student.id)
        .all()
    ))

    topic_scores_raw: dict[str, list[float]] = defaultdict(list)
    for sub in all_subs:
        topic_scores_raw[sub.assignment.topic].append(sub.score)

    topic_scores = {
        topic: round(sum(scores) / len(scores), 1)
        for topic, scores in topic_scores_raw.items()
    }

    accuracy = (
        round(student.total_correct / student.total_answered * 100, 1)
        if student.total_answered > 0
        else 0.0
    )

    return DashboardSummary(
        overall_score=student.overall_score,
        total_answered=student.total_answered,
        total_correct=student.total_correct,
        accuracy=accuracy,
        weak_topics=json.loads(student.weak_topics),
        strong_topics=json.loads(student.strong_topics),
        today_answered=len(today_subs),
        today_correct=sum(1 for s in today_subs if s.is_correct),
        topic_scores=topic_scores,
    )


@router.get("/trends", response_model=TrendsResponse)
def get_trends(
    days: int = Query(default=14, ge=1, le=90),
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return daily score trends and topic-level aggregation."""
    since = datetime.utcnow() - timedelta(days=days)

    submissions = latest_attempts((
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .filter(Submission.student_id == student.id, Submission.submitted_at >= since)
        .order_by(Submission.submitted_at)
        .all()
    ))

    # Daily aggregation
    daily: dict[str, list[float]] = defaultdict(list)
    topic_agg: dict[str, list[float]] = defaultdict(list)

    for sub in submissions:
        day_key = sub.submitted_at.strftime("%Y-%m-%d")
        daily[day_key].append(sub.score)
        topic_agg[sub.assignment.topic].append(sub.score)

    daily_scores = [
        DailyScore(
            date=date,
            score=round(sum(scores) / len(scores), 1),
            count=len(scores),
        )
        for date, scores in sorted(daily.items())
    ]

    topic_trends = [
        TopicTrend(
            topic=topic,
            average_score=round(sum(scores) / len(scores), 1),
            count=len(scores),
        )
        for topic, scores in sorted(topic_agg.items())
    ]

    return TrendsResponse(daily_scores=daily_scores, topic_trends=topic_trends)
