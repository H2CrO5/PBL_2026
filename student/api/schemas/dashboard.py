"""Dashboard response schemas."""

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
