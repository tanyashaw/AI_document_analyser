from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_document(text: str):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=300
    )

    chunks = splitter.split_text(text)

    return chunks