"""FAISS retrieval utility for RAG."""

import json

import faiss
import numpy as np

from config import (
    EMBEDDING_MODEL_ID,
    FAISS_INDEX_DIR,
    RAG_TOP_K,
)
from llm.bedrock_client import invoke_model

_index = None
_chunks = None


def _load():
    """Lazy-load the FAISS index and chunk metadata."""
    global _index, _chunks

    if _index is not None:
        return

    index_path = FAISS_INDEX_DIR / "index.faiss"
    chunks_path = FAISS_INDEX_DIR / "chunks.json"

    if not index_path.exists():
        raise FileNotFoundError(
            f"FAISS index not found at {index_path}. "
            "Run `python -m vectorstore.build_index` first."
        )

    _index = faiss.read_index(str(index_path))

    with open(chunks_path, "r", encoding="utf-8") as f:
        _chunks = json.load(f)


def _embed_query(text: str) -> np.ndarray:
    """Embed a query string."""
    result = invoke_model(EMBEDDING_MODEL_ID, {"inputText": text})
    vec = np.array([result["embedding"]], dtype=np.float32)
    faiss.normalize_L2(vec)
    return vec


def retrieve(query: str, top_k: int = RAG_TOP_K) -> list[dict]:
    """Search the FAISS index and return the top-k most relevant chunks.

    Returns a list of dicts with keys: text, source, chunk_index, score.
    """
    _load()

    query_vec = _embed_query(query)
    scores, indices = _index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        chunk = _chunks[idx].copy()
        chunk["score"] = float(score)
        results.append(chunk)

    return results
