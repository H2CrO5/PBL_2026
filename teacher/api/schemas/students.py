"""Student insight schemas for the teacher side."""

from datetime import datetime

from pydantic import BaseModel, Field


class RecentSubmissionResponse(BaseModel):
    submission_id: int
    assignment_id: int
    external_assignment_id: str | None = None
    topic: str
    question_text: str
    answer_text: str
    is_correct: bool
    score: float
    feedback: str
    attempt_number: int = 1
    grading_source: str = "auto"
    missing_concepts: list[str] = Field(default_factory=list)
    teacher_error_pattern: str | None = None
    submitted_at: datetime


class GradeOverrideRequest(BaseModel):
    score: float = Field(ge=0, le=100)
    feedback: str = Field(min_length=1)


class GradeOverrideResponse(BaseModel):
    submission_id: int
    score: float
    feedback: str
    grading_source: str


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
    chat_summary: list[str] = Field(default_factory=list)
    data_source: str = "teacher-demo-data"
