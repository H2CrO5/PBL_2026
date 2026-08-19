"""Teacher-authored question seed schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class QuestionSeedCreateRequest(BaseModel):
    course_id: int
    lecture_id: int
    title: str = Field(min_length=1)
    target_concept: str = Field(min_length=1)
    seed_type: Literal["base", "required", "rubric_seed"] = "base"
    difficulty: Literal["supportive", "balanced", "challenging"] = "balanced"
    question_text: str = Field(min_length=1)
    expected_answer: str = Field(min_length=1)
    rubric: list[str] = Field(min_length=1)
    points: float = Field(default=100, gt=0)
    max_attempts: int = Field(default=1, ge=1, le=10)
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
    points: float
    max_attempts: int
    notes: str | None
    created_at: datetime


class QuestionSeedCandidateResponse(BaseModel):
    title: str
    target_concept: str
    seed_type: Literal["base", "required", "rubric_seed"]
    difficulty: Literal["supportive", "balanced", "challenging"]
    question_text: str
    expected_answer: str
    rubric: list[str]
    notes: str
    rationale: str
    assessment_scope: str
    variation_policy: str
    teacher_priority: str


class GenerationMaterialResponse(BaseModel):
    id: int
    title: str
    material_type: str
    ingestion_status: str


class ReadinessCheckResponse(BaseModel):
    name: str
    status: Literal["ready", "warning", "blocked"]
    detail: str


class GenerationContextResponse(BaseModel):
    course_id: int
    lecture_id: int
    lecture_title: str
    learning_objectives: list[str]
    materials: list[GenerationMaterialResponse]
    material_titles: list[str]
    weak_concepts: list[str]
    question_seeds: list[QuestionSeedResponse]
    question_seed_candidates: list[QuestionSeedCandidateResponse]
    readiness_checks: list[ReadinessCheckResponse]
    ready_for_generation: bool
    backend_instruction: str


class AssignmentPublishRequest(BaseModel):
    due_at: datetime | None = None
    target_student_codes: list[str] = Field(default_factory=list)


class AssignmentPublishResponse(BaseModel):
    publication_id: int
    external_assignment_id: str
    status: str
    created_for_students: int
    already_present: int
    missing_student_codes: list[str]


class QuestionGenerateRequest(BaseModel):
    course_id: int
    lecture_id: int
    target_concept: str | None = None
    difficulty: Literal["supportive", "balanced", "challenging"] = "balanced"
    points: float = Field(default=100, gt=0)
    max_attempts: int = Field(default=1, ge=1, le=10)
