"""Student insight schemas for the teacher side."""

from datetime import datetime

from pydantic import BaseModel, Field


class RecentSubmissionResponse(BaseModel):
    submission_id: int
    assignment_id: int
    topic: str
    question_text: str
    answer_text: str
    is_correct: bool
    score: float
    feedback: str
    submitted_at: datetime


class StudentInsightResponse(BaseModel):
    id: int
    student_code: str
    name: str
    average_score: float
    completion_rate: float
    strong_topics: list[str]
    weak_topics: list[str]
    recommended_action: str
    recent_submissions: list[RecentSubmissionResponse] = Field(default_factory=list)
    data_source: str = "teacher-demo-data"
