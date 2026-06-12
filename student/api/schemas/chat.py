"""Chat request/response schemas."""

from datetime import datetime

from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    message: str


class SourceInfo(BaseModel):
    source: str
    score: float


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: list[SourceInfo] | None = None
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
