"""Student-facing course material schemas."""

from datetime import datetime

from pydantic import BaseModel


class StudentMaterialResponse(BaseModel):
    id: int
    external_material_id: str
    external_course_id: str
    course_title: str
    lecture_id: int | None = None
    lecture_number: int | None = None
    lecture_title: str | None = None
    title: str
    material_type: str
    content: str
    updated_at: datetime

