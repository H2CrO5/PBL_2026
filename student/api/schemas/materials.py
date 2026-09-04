"""Read-only course material schemas for the Student application."""

from datetime import datetime

from pydantic import BaseModel, Field


class StudentMaterialResponse(BaseModel):
    id: int
    title: str
    material_type: str
    content: str
    ingestion_status: str
    created_at: datetime


class StudentLectureMaterialsResponse(BaseModel):
    course_id: int
    external_course_id: str
    course_title: str
    term: str
    lecture_id: int | None = None
    lecture_number: int | None = None
    lecture_title: str | None = None
    materials: list[StudentMaterialResponse] = Field(default_factory=list)
