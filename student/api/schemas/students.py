"""Shared-contract student profile and memory schemas."""

from pydantic import BaseModel, Field


class StudentCourseResponse(BaseModel):
    id: int
    external_course_id: str
    title: str
    term: str


class ConceptMastery(BaseModel):
    concept: str
    mastery_score: float
    attempts: int
    evidence: list[int] = Field(default_factory=list)


class StudentMemoryResponse(BaseModel):
    student_id: int
    student_code: str
    course_id: int | None = None
    external_course_id: str | None = None
    overall_score: float
    concept_mastery: list[ConceptMastery]
    weak_topics: list[str]
    strong_topics: list[str]
