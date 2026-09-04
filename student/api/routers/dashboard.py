"""Dashboard endpoints for student progress visualization."""

from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.dashboard import (
    DailyScore,
    DashboardSummary,
    ProgressTimelineResponse,
    TopicTrend,
    TrendsResponse,
)
from db.database import get_db
from db.models import Assignment, Student, Submission
from services.progress import (
    STUDENT_PROGRESS_SOURCES,
    build_progress_timeline,
    calculate_progress,
    latest_attempts,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return overall stats, accuracy, topic scores, and today's progress."""
    progress = calculate_progress(db, student)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_subs = [
        item for item in progress["submissions"]
        if item.submitted_at >= today_start
    ]

    return DashboardSummary(
        overall_score=progress["overall_score"],
        total_answered=progress["completed_assignments"],
        total_correct=progress["total_correct"],
        accuracy=progress["accuracy"],
        weak_topics=progress["weak_topics"],
        strong_topics=progress["strong_topics"],
        today_answered=len(today_subs),
        today_correct=sum(1 for s in today_subs if s.is_correct),
        topic_scores=progress["topic_scores"],
        total_assignments=progress["total_assignments"],
        completed_assignments=progress["completed_assignments"],
        pending_assignments=progress["pending_assignments"],
        completion_rate=progress["completion_rate"],
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
    ), allowed_sources=STUDENT_PROGRESS_SOURCES)

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


@router.get("/timeline", response_model=ProgressTimelineResponse)
def get_progress_timeline(
    days: int = Query(default=30, ge=1, le=365),
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)
    return ProgressTimelineResponse(
        points=build_progress_timeline(db, student, since=since)
    )
