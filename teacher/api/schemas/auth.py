"""Authentication schemas."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    teacher_code: str
    password: str


class TeacherResponse(BaseModel):
    id: int
    teacher_code: str
    name: str


class LoginResponse(BaseModel):
    token: str
    teacher: TeacherResponse


class MessageResponse(BaseModel):
    message: str

