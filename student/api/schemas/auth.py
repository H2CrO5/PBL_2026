"""Auth request/response schemas."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    student_code: str
    password: str


class StudentResponse(BaseModel):
    id: int
    student_code: str
    name: str
    overall_score: float
    total_answered: int
    total_correct: int
    weak_topics: list[str]
    strong_topics: list[str]

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    token: str
    student: StudentResponse


class MessageResponse(BaseModel):
    message: str
