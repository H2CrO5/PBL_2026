"""Teacher-authored question seed schemas."""

from datetime import datetime

from pydantic import BaseModel


class QuestionSeedCreateRequest(BaseModel):
    course_id: int
    lecture_id: int
    title: str
    target_concept: str
    seed_type: str = "base"
    difficulty: str = "medium"
    question_text: str
    expected_answer: str
    rubric: list[str]
    notes: str | None = None


class QuestionSeedResponse(BaseModel):
    id: int
    course_id: int
    lecture_id: int | None
    lecture_title: str | None
    title: str
    target_concept: str
    seed_type: str
    difficulty: str
    question_text: str
    expected_answer: str
    rubric: list[str]
    notes: str | None
    created_at: datetime


class GenerationContextResponse(BaseModel):
    course_id: int
    lecture_id: int
    lecture_title: str
    material_titles: list[str]
    weak_concepts: list[str]
    question_seeds: list[QuestionSeedResponse]
    backend_instruction: str

