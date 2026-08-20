"""Assignment request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class LectureInfo(BaseModel):
    id: int
    lecture_number: int
    title: str
    description: str | None = None
    lecture_date: datetime | None = None
    deadline: datetime | None = None

    model_config = {"from_attributes": True}


class AssignmentResponse(BaseModel):
    id: int
    topic: str
    difficulty: str
    question_text: str
    choices: list[str] | None = None
    question_type: str
    lecture_id: int | None = None
    course_id: int | None = None
    title: str | None = None
    max_attempts: int = 1
    attempts_used: int = 0
    due_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignmentWithLecture(BaseModel):
    """Assignment with its lecture info for grouped display."""
    id: int
    topic: str
    difficulty: str
    question_text: str
    choices: list[str] | None = None
    question_type: str
    lecture: LectureInfo | None = None
    created_at: datetime


class LectureAssignments(BaseModel):
    """A lecture with its list of assignments."""
    lecture: LectureInfo
    assignments: list[AssignmentResponse]


class SubmitRequest(BaseModel):
    assignment_id: int
    answer_text: str


class SharedSubmissionRequest(BaseModel):
    """Compatibility shape for POST /assignments/{id}/submissions."""

    answer_text: str | None = None
    answers: list[dict[str, str]] = Field(default_factory=list)


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    answer_text: str
    is_correct: bool
    score: float
    feedback: str
    correct_answer: str
    explanation: str
    attempt_number: int = 1
    attempts_remaining: int = 0
    grading_source: str = "auto"
    missing_concepts: list[str] = Field(default_factory=list)
    submitted_at: datetime


class HistoryItem(BaseModel):
    assignment_id: int
    topic: str
    difficulty: str
    question_text: str
    question_type: str
    answer_text: str
    is_correct: bool
    score: float
    feedback: str
    submitted_at: datetime


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int


class HistoryAssignment(BaseModel):
    """A submitted assignment with its result."""
    id: int
    topic: str
    difficulty: str
    question_text: str
    question_type: str
    answer_text: str
    is_correct: bool
    score: float
    feedback: str
    attempt_number: int = 1
    grading_source: str = "auto"
    missing_concepts: list[str] = Field(default_factory=list)
    submitted_at: datetime


class HistoryLectureGroup(BaseModel):
    """A lecture with its submitted assignments."""
    lecture: LectureInfo
    submissions: list[HistoryAssignment]
