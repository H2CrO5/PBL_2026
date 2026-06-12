"""Assignment request/response schemas."""

from datetime import datetime

from pydantic import BaseModel


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


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    answer_text: str
    is_correct: bool
    score: float
    feedback: str
    correct_answer: str
    explanation: str
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
    submitted_at: datetime


class HistoryLectureGroup(BaseModel):
    """A lecture with its submitted assignments."""
    lecture: LectureInfo
    submissions: list[HistoryAssignment]
