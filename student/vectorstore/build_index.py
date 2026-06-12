"""Build a FAISS index from markdown documents using Amazon Titan Embed Text v2."""

import json
import sys
from pathlib import Path

import faiss
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCUMENTS_DIR,
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL_ID,
    FAISS_INDEX_DIR,
)
from llm.bedrock_client import invoke_model


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks by character count."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


def _get_embedding(text: str) -> list[float]:
    """Get embedding vector from Amazon Titan Embed Text v2."""
    result = invoke_model(EMBEDDING_MODEL_ID, {"inputText": text})
    return result["embedding"]


def build_index():
    """Read documents, chunk, embed, and save FAISS index + metadata."""
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks: list[str] = []
    all_metadata: list[dict] = []

    # Read and chunk all markdown files
    for md_file in sorted(DOCUMENTS_DIR.glob("*.md")):
        print(f"Processing: {md_file.name}")
        text = md_file.read_text(encoding="utf-8")
        chunks = _chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "source": md_file.name,
                "chunk_index": i,
            })

    if not all_chunks:
        print("No documents found.")
        return

    print(f"Total chunks: {len(all_chunks)}")

    # Generate embeddings
    embeddings = []
    for i, chunk in enumerate(all_chunks):
        emb = _get_embedding(chunk)
        embeddings.append(emb)
        if (i + 1) % 10 == 0:
            print(f"  Embedded {i + 1}/{len(all_chunks)}")

    embeddings_np = np.array(embeddings, dtype=np.float32)

    # Build FAISS index
    index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)  # Inner product (cosine on normalized)
    faiss.normalize_L2(embeddings_np)
    index.add(embeddings_np)

    # Save
    faiss.write_index(index, str(FAISS_INDEX_DIR / "index.faiss"))

    with open(FAISS_INDEX_DIR / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(
            [{"text": c, **m} for c, m in zip(all_chunks, all_metadata)],
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"FAISS index saved to {FAISS_INDEX_DIR}")
    print(f"Index size: {index.ntotal} vectors of dimension {EMBEDDING_DIMENSION}")


if __name__ == "__main__":
    build_index()
