"""Dashboard response schemas."""

from datetime import datetime

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    overall_score: float
    total_answered: int
    total_correct: int
    accuracy: float
    weak_topics: list[str]
    strong_topics: list[str]
    today_answered: int
    today_correct: int
    topic_scores: dict[str, float]
    total_assignments: int
    completed_assignments: int
    pending_assignments: int
    completion_rate: float


class DailyScore(BaseModel):
    date: str
    score: float
    count: int


class TopicTrend(BaseModel):
    topic: str
    average_score: float
    count: int


class TrendsResponse(BaseModel):
    daily_scores: list[DailyScore]
    topic_trends: list[TopicTrend]


class ProgressTimelinePoint(BaseModel):
    submission_id: int
    assignment_id: int
    submitted_at: datetime
    topic: str
    assignment_score: float
    overall_score: float
    accuracy: float
    topic_mastery: float
    completed_assignments: int
    total_assignments: int
    completion_rate: float


class ProgressTimelineResponse(BaseModel):
    points: list[ProgressTimelinePoint]
