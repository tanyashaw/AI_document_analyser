"""
WHY THIS CHANGE:
`langchain_text_splitters` was imported at module scope, so it loaded at
app startup as part of the rfp.py -> chunker.py import chain. It's imported
here inside the function instead, so it only loads on first actual use
(first document processed), not at server boot. It's a small package, so
this is a minor win compared to the embedder change, but it's consistent
with lazy-loading everything not needed for the app to boot and answer
/health.
"""


def chunk_document(text: str):
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=300
    )

    chunks = splitter.split_text(text)

    return chunks