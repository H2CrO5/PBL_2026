"""Analytics schemas."""

from pydantic import BaseModel


class WeakConcept(BaseModel):
    concept: str
    wrong_rate: float
    misconception: str
    recommended_focus: str


class DashboardSummary(BaseModel):
    course_id: int
    course_title: str
    total_students: int
    average_score: float
    completion_rate: float
    weak_concepts: list[WeakConcept]
    question_seed_count: int
    required_question_count: int


class LecturePlanRequest(BaseModel):
    course_id: int
    question_seed_id: int | None = None


class LecturePlanResponse(BaseModel):
    weakest_concepts: list[str]
    common_misconceptions: list[str]
    recommended_focus: list[str]
    suggested_activity: str
