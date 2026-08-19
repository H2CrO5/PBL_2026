"""Assignment-level analytics and shared endpoint schemas."""

from pydantic import BaseModel, Field


class AssignmentAnalyticsResponse(BaseModel):
    assignment_id: int
    external_assignment_id: str
    title: str
    target_concept: str
    data_source: str
    total_assigned: int
    total_submitted: int
    completion_rate: float
    average_score: float
    wrong_rate: float
    missing_concepts: list[str] = Field(default_factory=list)
    error_patterns: list[str] = Field(default_factory=list)
