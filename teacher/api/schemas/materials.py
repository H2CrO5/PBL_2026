"""Material schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MaterialResponse(BaseModel):
    id: int
    external_key: str
    course_id: int
    lecture_id: int
    lecture_title: str
    title: str
    material_type: str
    ingestion_status: str
    content_preview: str
    created_at: datetime


class MaterialSyncResponse(BaseModel):
    id: int
    ingestion_status: str
    chunk_count: int


class MaterialSyncAllResponse(BaseModel):
    synced: int
    failed: int
    chunks: int


class MaterialCreateRequest(BaseModel):
    course_id: int
    lecture_id: int
    title: str = Field(min_length=1)
    material_type: Literal["slide", "book", "note"]
    content: str = Field(min_length=1)


class CourseMaterialCreateRequest(BaseModel):
    lecture_id: int
    title: str = Field(min_length=1)
    material_type: Literal["slide", "book", "note"]
    content: str = Field(min_length=1)


class LectureResponse(BaseModel):
    id: int
    lecture_number: int
    title: str
    learning_objectives: list[str]
