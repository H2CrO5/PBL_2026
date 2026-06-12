"""Student insight schemas for the teacher side."""

from pydantic import BaseModel


class StudentInsightResponse(BaseModel):
    id: int
    student_code: str
    name: str
    average_score: float
    completion_rate: float
    strong_topics: list[str]
    weak_topics: list[str]
    recommended_action: str

