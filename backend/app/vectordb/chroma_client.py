"""
Lazily-initialized ChromaDB client.

WHY THIS CHANGE:
Previously `client` and `collection` were created at module import time,
meaning every request path that eventually imports this module (via
store.py or retriever.py) paid the cost of spinning up a PersistentClient
and touching disk during app startup, before the server was even ready to
serve traffic. ChromaDB itself isn't the biggest memory offender here (that
was sentence-transformers/torch), but lazy-initializing it is still good
practice: it means `import app.vectordb.chroma_client` costs nothing until
`get_collection()` is actually called on first upload/query, and it keeps
app startup fast and memory-light.
"""

import chromadb
from chromadb.api.models.Collection import Collection

_client: chromadb.ClientAPI | None = None
_collection: Collection | None = None


def get_collection() -> Collection:
    """Return the (lazily created) 'rfp_documents' collection."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path="chroma_db")
        _collection = _client.get_or_create_collection(name="rfp_documents")
    return _collection