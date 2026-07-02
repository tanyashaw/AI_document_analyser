from app.vectordb.embedder import embed_query
from app.vectordb.chroma_client import get_collection


def retrieve_relevant_chunks(query, session_id: str, top_k=3):
    """
    Retrieve the top_k most relevant chunks for a query, restricted to
    the chunks that belong to the given session_id. Without this filter,
    retrieval could return chunks from a completely different uploaded
    document.
    """
    if not session_id:
        raise ValueError("retrieve_relevant_chunks requires a session_id")

    query_embedding = embed_query(query)

    results = get_collection().query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"session_id": session_id},
    )

    documents = results.get("documents")
    if not documents or not documents[0]:
        return []

    return documents[0]