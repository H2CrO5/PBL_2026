"""Analytics schemas."""

from pydantic import BaseModel
from datetime import datetime


class WeakConcept(BaseModel):
    concept: str
    wrong_rate: float
    misconception: str
    recommended_focus: str


class TeacherAction(BaseModel):
    priority: str
    title: str
    reason: str
    next_step: str


class EvidenceItem(BaseModel):
    concept: str
    confidence: str
    evidence_status: str
    affected_students: list[str]
    related_question_seeds: list[str]
    typical_errors: list[str]
    recommended_action: str


class DashboardSummary(BaseModel):
    course_id: int
    course_title: str
    total_students: int
    average_score: float
    completion_rate: float
    weak_concepts: list[WeakConcept]
    question_seed_count: int
    required_question_count: int
    teacher_actions: list[TeacherAction]
    data_source: str = "teacher-demo-data"
    data_updated_at: datetime | None = None


class LecturePlanRequest(BaseModel):
    course_id: int
    question_seed_id: int | None = None


class LecturePlanResponse(BaseModel):
    weakest_concepts: list[str]
    common_misconceptions: list[str]
    recommended_focus: list[str]
    suggested_activity: str
    opening_activity: str
    review_sequence: list[str]
    in_class_check: str
    follow_up_actions: list[str]
    recommended_seed_titles: list[str]
