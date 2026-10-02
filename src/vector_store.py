"""Persistent local Chroma storage for text, embeddings, and PDF citations."""

import hashlib
import math
from collections import defaultdict
from pathlib import Path

import chromadb

from src.embeddings import embed_query
from src.errors import VectorStoreError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "chroma_db"
DATABASE_PATH.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(DATABASE_PATH))
collection = client.get_or_create_collection(name="academic_notes")


def _make_chunk_ids(chunks):
    ids = []
    occurrence_counts = defaultdict(int)

    for chunk in chunks:
        source = str(chunk["source"]).strip()
        page = int(chunk["page"])
        text = str(chunk["text"]).strip()
        key = (source, page)
        occurrence = occurrence_counts[key]
        occurrence_counts[key] += 1
        identity = f"{source}:{page}:{occurrence}:{text}"
        ids.append(hashlib.sha256(identity.encode("utf-8")).hexdigest())
    return ids


def save_chunks(chunks, vectors):
    """Store chunks and replace older chunks for each included PDF source."""
    if len(chunks) != len(vectors):
        raise ValueError("There must be one embedding for each chunk.")
    if not chunks:
        raise ValueError("There are no text chunks to store.")

    for chunk, vector in zip(chunks, vectors):
        if not isinstance(chunk, dict) or not {"text", "source", "page"}.issubset(chunk):
            raise ValueError("Each chunk must include text, source, and page fields.")
        if not str(chunk["text"]).strip() or not str(chunk["source"]).strip():
            raise ValueError("Chunks must include non-empty text and a source filename.")
        if not vector or any(
            not isinstance(value, (int, float)) or not math.isfinite(value)
            for value in vector
        ):
            raise ValueError("Every chunk must have a valid numeric embedding.")

    ids = _make_chunk_ids(chunks)
    metadatas = [
        {"source": str(chunk["source"]).strip(), "page": int(chunk["page"])}
        for chunk in chunks
    ]
    new_ids_by_source = defaultdict(set)
    for chunk_id, metadata in zip(ids, metadatas):
        new_ids_by_source[metadata["source"]].add(chunk_id)

    try:
        collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=[str(chunk["text"]).strip() for chunk in chunks],
            metadatas=metadatas,
        )

        # Remove obsolete chunks left behind when a PDF is reprocessed.
        for source, current_ids in new_ids_by_source.items():
            existing = collection.get(where={"source": source}, include=["metadatas"])
            stale_ids = [item_id for item_id in existing["ids"] if item_id not in current_ids]
            if stale_ids:
                collection.delete(ids=stale_ids)
        return collection.count()
    except Exception as error:
        raise VectorStoreError("Could not save the document chunks to the local vector database.") from error


def list_documents():
    """Return indexed PDF names and the number of stored chunks per PDF."""
    try:
        records = collection.get(include=["metadatas"])
        counts = defaultdict(int)
        for metadata in records.get("metadatas") or []:
            if metadata and metadata.get("source"):
                counts[metadata["source"]] += 1
        return [{"source": name, "chunks": count} for name, count in sorted(counts.items())]
    except Exception as error:
        raise VectorStoreError("Could not read the indexed-document list.") from error


def delete_document(source: str) -> int:
    """Remove all chunks for one PDF source and return the number removed."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Choose a document name to remove.")
    try:
        existing = collection.get(where={"source": source.strip()}, include=["metadatas"])
        ids = existing.get("ids") or []
        if ids:
            collection.delete(ids=ids)
        return len(ids)
    except Exception as error:
        raise VectorStoreError(f"Could not remove {source} from the vector database.") from error


def search_chunks(question, limit=3):
    """Find stored chunks closest in meaning to a question."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Enter a question before searching.")
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("Search limit must be a positive integer.")
    try:
        total = collection.count()
    except Exception as error:
        raise VectorStoreError("Could not read the local vector database.") from error
    if total == 0:
        raise VectorStoreError("No documents are indexed yet. Process a PDF first.")

    question_vector = embed_query(question)
    try:
        results = collection.query(
            query_embeddings=[question_vector],
            n_results=min(limit, total),
            include=["documents", "metadatas", "distances"],
        )
    except Exception as error:
        raise VectorStoreError("Could not search the local vector database.") from error

    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]
    matches = []
    for index, text in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else None
        if not text or not metadata:
            continue
        matches.append({
            "text": text,
            "source": metadata.get("source", "Unknown document"),
            "page": metadata.get("page", "?"),
            "distance": distances[index] if index < len(distances) else None,
        })
    return matches
