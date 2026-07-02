import uuid

from app.vectordb.embedder import embed_texts
from app.vectordb.chroma_client import get_collection


def store_chunks(chunks, session_id: str):
    """
    Store document chunks in the vector store, scoped to a session.

    Each chunk gets a globally-unique ID (session_id + random suffix + index)
    so re-uploading a document, or uploading multiple documents across
    different sessions, never collides with or overwrites existing chunks.
    The session_id is also stored as metadata so retrieval can be filtered
    to only the chunks belonging to a given session/document.
    """
    if not session_id:
        raise ValueError("store_chunks requires a session_id to scope chunks")

    if not chunks:
        return

    upload_tag = uuid.uuid4().hex[:8]

    # Batch-embed all chunks in a single hosted API call — much faster than
    # one-by-one, and avoids loading any model locally.
    embeddings = embed_texts(chunks)

    ids = [f"{session_id}_{upload_tag}_{i}" for i in range(len(chunks))]
    metadatas = [{"session_id": session_id} for _ in chunks]

    # Single bulk insert instead of N individual adds
    get_collection().add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )