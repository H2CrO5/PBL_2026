"""TA Bot chat endpoints with RAG."""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from api.dependencies import get_current_student
from api.schemas.chat import ChatHistoryResponse, ChatMessageResponse, ChatMessageRequest, SourceInfo
from db.database import get_db
from db.models import ChatMessage, Course, Enrollment, Student
from llm import bedrock_client, prompts
from services.course_rag import retrieve_course
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

    # Resolve only a course the authenticated student is actively enrolled in.
    course_query = (
        db.query(Course)
        .join(Enrollment, Enrollment.course_id == Course.id)
        .filter(Enrollment.student_id == student.id, Enrollment.status == "active")
    )
    if req.external_course_id:
        course_query = course_query.filter(Course.external_key == req.external_course_id)
    course = course_query.order_by(Course.created_at.desc()).first()

    context_chunks = retrieve_course(db, course.id, req.message) if course else []
    if not context_chunks:
        # Preserve the original fixed-document demo until Teacher materials are
        # synced. A missing local FAISS index should not break the TA Bot.
        try:
            context_chunks = retrieve(req.message)
        except FileNotFoundError:
            context_chunks = []
    context_text = "\n\n---\n\n".join(
        f"[資料: {c['source']} / {c.get('source_locator', 'chunk')}]\n{c['text']}"
        for c in context_chunks
    ) or "（この質問に利用できる授業教材はありません）"

    sources = [
        {
            "source": c["source"],
            "score": round(c["score"], 3),
            "material_id": c.get("material_id"),
            "chunk_index": c.get("chunk_index"),
            "source_locator": c.get("source_locator"),
            "retrieval_mode": c.get("retrieval_mode", "legacy-faiss"),
        }
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


@router.post("", response_model=ChatMessageResponse, include_in_schema=True)
def shared_chat(
    req: ChatMessageRequest,
    student: Student = Depends(get_current_student),
    db: DBSession = Depends(get_db),
):
    """Shared-contract alias for POST /chat."""
    return send_message(req, student, db)


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
