"""Read-only service-to-service analytics schemas."""

from datetime import datetime

from pydantic import BaseModel


class TeacherSubmissionItem(BaseModel):
    submission_id: int
    assignment_id: int
    topic: str
    question_text: str
    answer_text: str
    is_correct: bool
    score: float
    feedback: str
    submitted_at: datetime


class TeacherStudentAnalytics(BaseModel):
    student_id: int
    student_code: str
    name: str
    average_score: float
    completion_rate: float
    total_assignments: int
    total_submissions: int
    strong_topics: list[str]
    weak_topics: list[str]
    recent_submissions: list[TeacherSubmissionItem]


class TeacherTopicMetric(BaseModel):
    topic: str
    attempts: int
    incorrect: int
    wrong_rate: float


class TeacherAnalyticsFeed(BaseModel):
    data_source: str
    generated_at: datetime
    students: list[TeacherStudentAnalytics]
    topic_metrics: list[TeacherTopicMetric]
