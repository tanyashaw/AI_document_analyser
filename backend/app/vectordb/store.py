import uuid

from app.vectordb.embedder import embed_texts
from app.vectordb.chroma_client import get_collection


def store_chunks(
    chunks: list[str],
    document_id: str,
    user_id: str,
    filename: str,
) -> None:
    """
    Store document chunks in ChromaDB, scoped to a document (not a session).

    Metadata stored per chunk:
      - document_id  — the primary filter for retrieval
      - user_id      — second-factor isolation so a user cannot retrieve
                       another user's chunks even if they know the document_id
      - filename     — human-readable label, useful for debugging

    Chunk IDs include a random tag so the same document can be re-uploaded
    (with a new document_id) without colliding with previous chunks.
    """
    if not document_id:
        raise ValueError("store_chunks requires a document_id")
    if not user_id:
        raise ValueError("store_chunks requires a user_id")
    if not chunks:
        return

    upload_tag = uuid.uuid4().hex[:8]

    embeddings = embed_texts(chunks)

    ids = [f"{document_id}_{upload_tag}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "user_id": user_id, "filename": filename}
        for _ in chunks
    ]

    get_collection().add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )