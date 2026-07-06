"""
Splits a full document into batches so the extraction step can cover the
ENTIRE document instead of just the first couple of pages.

Sized for Groq's free tier, specifically llama-3.1-8b-instant's limits
(from console.groq.com/docs/rate-limits, checked July 2026):
    30 RPM · 6,000 TPM · 14,400 RPD · 500,000 TPD

TPM (tokens per minute, input + output combined, shared across your whole
account) is the tight constraint here — not the daily caps. The math this
batch size is based on:
    - ~4 characters per token for English text
    - DEFAULT_BATCH_CHARS=5000 chars  -> ~1,250 input tokens
    - + prompt instructions           -> ~350 input tokens
    - + max_tokens=1000 output cap    -> up to 1,000 output tokens
    - worst case per call             -> ~2,600 tokens
This leaves headroom to make 2 calls inside the same 60-second window
(2 x 2,600 = 5,200 < 6,000) without tripping the rate limit, even before
counting the retry-with-backoff already built into core/llm.py as a
safety net for bursts.

This is deliberately separate from chunker.py, which makes SMALL chunks
(3,000 chars) for the chat/RAG feature, where retrieval precision matters
more than call count.
"""

# Size of each batch in characters. See the module docstring for the
# token-budget math behind this number.
DEFAULT_BATCH_CHARS = 5_000

# Small overlap between consecutive batches so an item that happens to
# fall right on a batch boundary isn't missed entirely.
DEFAULT_OVERLAP_CHARS = 300

# Hard safety ceiling on total document size we'll run extraction over.
# This is NOT the old "only read the first 2 pages" bug — it's a sane
# upper bound (roughly 100+ pages) to protect against an extreme edge
# case (e.g. a corrupted file extracting as millions of characters)
# blowing up cost/latency/time unexpectedly. A document at this ceiling
# would already take several minutes to fully process on the free tier —
# see the pacing note in graph/workflow.py.
MAX_DOCUMENT_CHARS = 200_000


def create_batches(
    text: str,
    batch_chars: int = DEFAULT_BATCH_CHARS,
    overlap: int = DEFAULT_OVERLAP_CHARS,
) -> list[str]:
    """
    Split `text` into a list of overlapping batches, each up to
    `batch_chars` characters long, covering the full input (up to the
    MAX_DOCUMENT_CHARS safety ceiling).
    """
    text = text.strip()
    if not text:
        return []

    if len(text) > MAX_DOCUMENT_CHARS:
        text = text[:MAX_DOCUMENT_CHARS]

    if len(text) <= batch_chars:
        return [text]

    batches = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + batch_chars, n)
        batches.append(text[start:end])
        if end == n:
            break
        # Step forward by (batch size - overlap) so batches overlap
        # slightly instead of cutting an item in half.
        start = end - overlap

    return batches