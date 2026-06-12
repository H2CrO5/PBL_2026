"""Material schemas."""

from datetime import datetime

from pydantic import BaseModel


class MaterialResponse(BaseModel):
    id: int
    course_id: int
    lecture_id: int
    lecture_title: str
    title: str
    material_type: str
    ingestion_status: str
    content_preview: str
    created_at: datetime


class MaterialCreateRequest(BaseModel):
    course_id: int
    lecture_id: int
    title: str
    material_type: str
    content: str


class LectureResponse(BaseModel):
    id: int
    lecture_number: int
    title: str
    learning_objectives: list[str]

