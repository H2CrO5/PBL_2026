"""TA Bot chat endpoints with RAG."""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.chat import ChatHistoryResponse, ChatMessageResponse, ChatMessageRequest, SourceInfo
from db.database import get_db
from db.models import ChatMessage, Student
from llm import bedrock_client, prompts
from vectorstore.retriever import retrieve

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
def send_message(
    req: ChatMessageRequest,
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Process a student message: retrieve context, generate response, save both."""
    # Save user message
    user_msg = ChatMessage(
        student_id=student.id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    db.flush()

    # RAG retrieval
    context_chunks = retrieve(req.message)
    context_text = "\n\n---\n\n".join(c["text"] for c in context_chunks)

    sources = [
        {"source": c["source"], "score": round(c["score"], 3)}
        for c in context_chunks
    ]

    # Build chat history (last 10 messages)
    recent_msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.student_id == student.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
        .all()
    )
    recent_msgs.reverse()

    chat_history = "\n".join(
        f"{'学生' if m.role == 'user' else 'TA'}: {m.content}"
        for m in recent_msgs
    )

    # Build prompt
    prompt = prompts.TA_BOT_PROMPT.format(
        student_name=student.name,
        overall_score=student.overall_score,
        weak_topics=json.loads(student.weak_topics),
        context=context_text,
        chat_history=chat_history,
        message=req.message,
    )

    # Call LLM
    response_text = bedrock_client.invoke(
        prompt=prompt,
        system=prompts.TA_BOT_SYSTEM,
        temperature=0.5,
    )

    # Save assistant message
    assistant_msg = ChatMessage(
        student_id=student.id,
        role="assistant",
        content=response_text,
        sources=json.dumps(sources, ensure_ascii=False),
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatMessageResponse(
        id=assistant_msg.id,
        role="assistant",
        content=response_text,
        sources=[SourceInfo(**s) for s in sources],
        created_at=assistant_msg.created_at,
    )


@router.get("/history", response_model=ChatHistoryResponse)
def get_history(
    limit: int = Query(default=50, ge=1, le=200),
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Return chat history for the current student."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.student_id == student.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )

    result = []
    for msg in messages:
        sources = None
        if msg.sources:
            try:
                raw = json.loads(msg.sources)
                sources = [SourceInfo(**s) for s in raw]
            except (json.JSONDecodeError, TypeError):
                sources = None

        result.append(
            ChatMessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                sources=sources,
                created_at=msg.created_at,
            )
        )

    return ChatHistoryResponse(messages=result)
