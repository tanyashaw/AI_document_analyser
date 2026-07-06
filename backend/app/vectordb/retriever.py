from app.vectordb.embedder import embed_query
from app.vectordb.chroma_client import get_collection


def retrieve_relevant_chunks(
    query: str,
    document_id: str,
    user_id: str,
    top_k: int = 6,
) -> list[str]:
    """
    Retrieve the top_k most relevant chunks for a query, restricted to the
    chunks that belong to the given document_id AND user_id.

    Filtering on both fields provides two-layer isolation:
      1. document_id — scopes results to the correct document
      2. user_id     — ensures a user cannot retrieve another user's
                       embeddings even if they somehow know the document_id

    The double filter uses ChromaDB's $and operator so both conditions must
    be satisfied simultaneously.
    """
    if not document_id:
        raise ValueError("retrieve_relevant_chunks requires a document_id")
    if not user_id:
        raise ValueError("retrieve_relevant_chunks requires a user_id")

    query_embedding = embed_query(query)

    results = get_collection().query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={
            "$and": [
                {"document_id": {"$eq": document_id}},
                {"user_id": {"$eq": user_id}},
            ]
        },
    )

    documents = results.get("documents")
    if not documents or not documents[0]:
        return []

    return documents[0]