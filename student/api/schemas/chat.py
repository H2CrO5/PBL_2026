"""Chat request/response schemas."""

from datetime import datetime

from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    message: str
    external_course_id: str | None = None


class SourceInfo(BaseModel):
    source: str
    score: float
    material_id: int | None = None
    chunk_index: int | None = None
    source_locator: str | None = None
    retrieval_mode: str | None = None


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: list[SourceInfo] | None = None
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
