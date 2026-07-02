"""
Embeddings via a hosted API instead of a local sentence-transformers model.

WHY THIS CHANGE:
`sentence-transformers` pulls in PyTorch as a transitive dependency. Loading
`SentenceTransformer("all-MiniLM-L6-v2")` as a module-level global meant
~400-500MB of RAM (torch + the model weights) was allocated the instant this
module was imported — which happens during app startup (main.py -> rfp.py ->
store.py -> this file), before Uvicorn even finishes booting. That's what
was blowing through Render's 512MB limit.

This module replaces that with plain HTTP calls to Jina AI's embeddings API
(https://jina.ai/embeddings) using `jina-embeddings-v3`. Jina was chosen
because it needs no SDK (just an HTTP POST), has a free tier, and returns
1024-dim vectors that work as a drop-in replacement for MiniLM's 384-dim
vectors in ChromaDB (ChromaDB doesn't care about the dimensionality as long
as it's consistent within a collection).

If you'd rather use OpenAI, Voyage, Cohere, or Gemini instead, only the
`_call_embedding_api` function below needs to change — everything else
(store.py, retriever.py) calls the provider-agnostic `embed_texts` /
`embed_query` functions and doesn't need to know which API is behind them.

No heavy import happens here at module load time — `httpx` is lightweight
(~a few MB) and the actual network call only happens when a document is
uploaded or a chat question is asked, i.e. lazily, on first real use.
"""

import os
import httpx

JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_API_URL = "https://api.jina.ai/v1/embeddings"
JINA_MODEL = os.getenv("JINA_EMBEDDING_MODEL", "jina-embeddings-v3")

# A single reusable HTTP client (connection pooling) — created lazily on
# first use, not at import time, so importing this module costs ~nothing.
_http_client: httpx.Client | None = None


def _get_http_client() -> httpx.Client:
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=30.0)
    return _http_client


def _call_embedding_api(texts: list[str], task: str) -> list[list[float]]:
    """
    Calls Jina AI's embeddings endpoint.

    `task` is one of "retrieval.passage" (for documents being stored) or
    "retrieval.query" (for the user's search query) — Jina v3 uses this to
    optimise the embedding for each side of the retrieval, which improves
    RAG quality over using the same embedding call for both.
    """
    if not JINA_API_KEY:
        raise RuntimeError(
            "JINA_API_KEY is not set. Get a free key at https://jina.ai/embeddings "
            "and set it as an environment variable."
        )

    response = _get_http_client().post(
        JINA_API_URL,
        headers={
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": JINA_MODEL,
            "task": task,
            "input": texts,
        },
    )
    response.raise_for_status()
    data = response.json()

    # Preserve input order — API returns an "index" per item.
    ordered = sorted(data["data"], key=lambda item: item["index"])
    return [item["embedding"] for item in ordered]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of document chunks for storage."""
    if not texts:
        return []
    return _call_embedding_api(texts, task="retrieval.passage")


def embed_query(text: str) -> list[float]:
    """Embed a single search query."""
    return _call_embedding_api([text], task="retrieval.query")[0]