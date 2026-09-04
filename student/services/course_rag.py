"""Course-scoped material ingestion and retrieval.

Bedrock Titan embeddings are used when credentials are configured. A lexical
fallback keeps local development usable, and its retrieval mode is returned so
the UI never mistakes fallback search for semantic retrieval.
"""

import json
import math
import re

from sqlalchemy.orm import Session as DBSession

from config import BEDROCK_BEARER_TOKEN, CHUNK_OVERLAP, CHUNK_SIZE, EMBEDDING_MODEL_ID
from db.models import CourseMaterial, MaterialChunk
from llm.bedrock_client import invoke_model


def _chunks(text: str) -> list[str]:
    chunks = []
    start = 0
    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    while start < len(text):
        chunk = text[start:start + CHUNK_SIZE].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks


def _embedding(text: str) -> list[float]:
    result = invoke_model(EMBEDDING_MODEL_ID, {"inputText": text})
    return [float(value) for value in result["embedding"]]


def ingest_material(db: DBSession, material: CourseMaterial) -> str:
    """Replace chunks and return `ready_bedrock` or `ready_lexical`."""
    db.query(MaterialChunk).filter(MaterialChunk.material_id == material.id).delete()
    use_bedrock = bool(BEDROCK_BEARER_TOKEN)
    mode = "ready_bedrock" if use_bedrock else "ready_lexical"
    chunk_texts = _chunks(material.content)
    vectors: list[list[float] | None] = [None] * len(chunk_texts)
    if use_bedrock:
        try:
            vectors = [_embedding(chunk_text) for chunk_text in chunk_texts]
        except Exception:
            # Never mix semantic and lexical scores in one index. A later resync
            # retries the entire material after credentials/provider recovery.
            vectors = [None] * len(chunk_texts)
            mode = "ready_lexical"

    for index, (chunk_text, vector) in enumerate(zip(chunk_texts, vectors)):
        db.add(MaterialChunk(
            material_id=material.id,
            chunk_index=index,
            text=chunk_text,
            embedding=json.dumps(vector) if vector is not None else None,
            source_locator=f"chunk-{index + 1}",
        ))
    material.ingestion_status = mode
    db.flush()
    return mode


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    norm = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    return dot / norm if norm else 0.0


def _terms(text: str) -> set[str]:
    return {term.lower() for term in re.findall(r"[A-Za-z0-9_]+|[\u3040-\u30ff\u3400-\u9fff]{2,}", text)}


def retrieve_course(
    db: DBSession,
    course_id: int,
    query: str,
    top_k: int = 3,
    visible_only: bool = False,
) -> list[dict]:
    chunks_query = (
        db.query(MaterialChunk)
        .join(CourseMaterial, MaterialChunk.material_id == CourseMaterial.id)
        .filter(
            CourseMaterial.course_id == course_id,
            CourseMaterial.audience == "student",
        )
    )
    chunks = chunks_query.all()
    if not chunks:
        return []

    query_vector = None
    if BEDROCK_BEARER_TOKEN and any(chunk.embedding for chunk in chunks):
        try:
            query_vector = _embedding(query)
        except Exception:
            query_vector = None

    query_terms = _terms(query)
    results = []
    for chunk in chunks:
        if query_vector is not None and chunk.embedding:
            score = _cosine(query_vector, json.loads(chunk.embedding))
            mode = "bedrock-embedding"
        else:
            chunk_terms = _terms(chunk.text)
            score = len(query_terms & chunk_terms) / max(1, len(query_terms | chunk_terms))
            mode = "lexical-fallback"
        results.append({
            "text": chunk.text,
            "source": chunk.material.title,
            "material_id": chunk.material_id,
            "chunk_index": chunk.chunk_index,
            "source_locator": chunk.source_locator,
            "score": float(score),
            "retrieval_mode": mode,
        })
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]
