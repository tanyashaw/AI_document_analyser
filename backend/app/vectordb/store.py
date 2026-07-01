import uuid

from app.vectordb.embedder import embedding_model
from app.vectordb.chroma_client import collection


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

    upload_tag = uuid.uuid4().hex[:8]

    for index, chunk in enumerate(chunks):
        embedding = embedding_model.encode(chunk).tolist()

        collection.add(
            ids=[f"{session_id}_{upload_tag}_{index}"],
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[{"session_id": session_id}],
        )