"""Read-only service-to-service analytics schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CourseSyncRequest(BaseModel):
    external_course_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    term: str = "unspecified"
    enrolled_student_codes: list[str] = Field(default_factory=list)


class CourseSyncResponse(BaseModel):
    course_id: int
    external_course_id: str
    enrolled_students: int


class AssignmentPublishRequest(BaseModel):
    external_assignment_id: str = Field(min_length=1)
    external_course_id: str = Field(min_length=1)
    course_title: str = Field(min_length=1)
    term: str = "unspecified"
    lecture_external_id: str
    lecture_number: int = Field(ge=0)
    lecture_title: str
    title: str
    target_concept: str
    difficulty: Literal["easy", "medium", "hard", "supportive", "balanced", "challenging"]
    question_text: str
    choices: list[str] | None = None
    correct_answer: str
    explanation: str
    question_type: Literal["multiple_choice", "short_answer", "code"] = "short_answer"
    rubric: list[str] = Field(min_length=1)
    points: float = Field(default=100, gt=0)
    max_attempts: int = Field(default=1, ge=1, le=10)
    due_at: datetime | None = None
    target_student_codes: list[str] = Field(default_factory=list)


class AssignmentPublishResponse(BaseModel):
    external_assignment_id: str
    created: int
    already_present: int
    missing_student_codes: list[str]


class MaterialSyncRequest(BaseModel):
    external_material_id: str = Field(min_length=1)
    external_course_id: str = Field(min_length=1)
    course_title: str
    term: str = "unspecified"
    lecture_external_id: str
    lecture_number: int = Field(ge=0)
    lecture_title: str
    title: str
    material_type: str
    content: str = Field(min_length=1)


class MaterialSyncResponse(BaseModel):
    material_id: int
    external_material_id: str
    ingestion_status: str
    chunk_count: int


class GradeOverrideRequest(BaseModel):
    external_course_id: str = Field(min_length=1)
    score: float = Field(ge=0, le=100)
    feedback: str = Field(min_length=1)


class GradeOverrideResponse(BaseModel):
    submission_id: int
    score: float
    feedback: str
    grading_source: str


class TeacherSubmissionItem(BaseModel):
    submission_id: int
    assignment_id: int
    external_assignment_id: str | None = None
    topic: str
    question_text: str
    answer_text: str
    is_correct: bool
    score: float
    feedback: str
    attempt_number: int
    grading_source: str
    source: Literal["real", "seed", "synthetic"] = "real"
    missing_concepts: list[str]
    teacher_error_pattern: str | None = None
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
    chat_summary: list[str] = Field(default_factory=list)


class TeacherTopicMetric(BaseModel):
    topic: str
    attempts: int
    incorrect: int
    wrong_rate: float
    common_error_patterns: list[str] = Field(default_factory=list)


class TeacherScoreTrend(BaseModel):
    date: str
    average_score: float
    submissions: int


class TeacherAnalyticsFeed(BaseModel):
    data_source: str
    generated_at: datetime
    external_course_id: str | None = None
    students: list[TeacherStudentAnalytics]
    topic_metrics: list[TeacherTopicMetric]
    score_trend: list[TeacherScoreTrend] = Field(default_factory=list)


class AssignmentAnalyticsFeed(BaseModel):
    data_source: str = "student-real-submissions"
    external_assignment_id: str
    total_assigned: int
    total_submitted: int
    completion_rate: float
    average_score: float
    wrong_rate: float
    missing_concepts: list[str] = Field(default_factory=list)
    error_patterns: list[str] = Field(default_factory=list)
