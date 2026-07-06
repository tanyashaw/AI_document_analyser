from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from pathlib import Path
import shutil
from typing import Optional

from app.services.pdf_parser import extract_text_from_pdf
from app.services.chunker import chunk_document

from app.graph.workflow import app_graph

from app.vectordb.store import store_chunks
from app.memory.chat_memory import session_store
from app.api.deps import get_current_user

router = APIRouter(
    prefix="/rfp",
    tags=["RFP"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class TextRFPRequest(BaseModel):
    text: str
    session_id: Optional[str] = None


def _build_final_response(workflow_result: dict) -> dict:
    """Build the final_extracted_data dict from workflow results."""
    doc_type = workflow_result.get("document_type", {})
    summary = workflow_result.get("summary", {})

    return {
        "document_type": doc_type.get("document_type", "Other"),
        "document_type_label": doc_type.get("document_type_label", "Document"),
        "document_type_confidence": doc_type.get("confidence", "Low"),

        "executive_summary": summary.get("executive_summary", ""),
        "objectives": summary.get("objectives", []),
        "key_highlights": summary.get("key_highlights", []),

        # Structured objects with page refs
        "project_scope": workflow_result["scope"].get("project_scope", []),
        "deadlines": workflow_result["deadlines"].get("deadlines", []),
        "staffing_requirements": workflow_result["staffing"].get("staffing_requirements", []),
        "compliance_requirements": workflow_result["compliance"].get("compliance_requirements", []),
        "deliverables": workflow_result.get("deliverables", {}).get("deliverables", []),
        "technical_requirements": workflow_result.get("technical", {}).get("technical_requirements", []),
        "commercial_requirements": workflow_result.get("commercial", {}).get("commercial_requirements", []),
        "risks": workflow_result.get("risks", {}).get("risks", []),
    }


def process_and_store_document(
    text: str,
    document_id: str,
    user_id: str,
    filename: str,
) -> tuple[dict, dict]:
    """
    Embed document chunks and run the extraction workflow.

    Steps:
      1. Chunk the text into small pieces for RAG retrieval.
      2. Embed and store those chunks in ChromaDB, keyed to document_id + user_id.
      3. Run the LangGraph workflow to extract structured fields.
      4. Persist the extraction result on the document row.

    Returns (meta_dict, workflow_result).
    """
    # Fine-grained chunks for chat/RAG (separate from the larger workflow batches)
    chunks = chunk_document(text)
    store_chunks(
        chunks,
        document_id=document_id,
        user_id=user_id,
        filename=filename,
    )

    initial_state = {
        "text": text,
        "document_type": {},
        "scope": {},
        "deadlines": {},
        "staffing": {},
        "compliance": {},
        "deliverables": {},
        "technical": {},
        "commercial": {},
        "risks": {},
        "summary": {},
    }

    workflow_result = app_graph.invoke(initial_state)
    final_response = _build_final_response(workflow_result)

    # Persist analysis on the document record (not the session)
    session_store.set_document_analysis(document_id, final_response)

    meta = {
        "total_characters": len(text),
        "total_chunks": len(chunks),
        "message": "Document processed successfully",
        "document_id": document_id,
        "final_extracted_data": final_response,
    }

    return meta, workflow_result


@router.post("/upload")
async def upload_rfp(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    """
    Upload and analyze a PDF or DOCX document.

    If a document with the same filename has already been uploaded by this user,
    we reuse its document_id and analysis, avoiding re-embedding and re-extracting,
    and simply start a new chat session for it.
    """
    # Check for existing document by this user with the same filename
    existing_doc = session_store.get_document_by_filename(user_id=user_id, filename=file.filename)

    if existing_doc is not None:
        document_id = existing_doc["document_id"]
        # Check if chunks actually exist in ChromaDB and are correctly scoped to the user
        from app.vectordb.chroma_client import get_collection
        try:
            col = get_collection()
            existing_chunks = col.get(
                where={"document_id": document_id},
                limit=1,
                include=["metadatas"],
            )
            has_chunks = False
            if existing_chunks and existing_chunks.get("ids") and existing_chunks.get("metadatas"):
                meta = existing_chunks["metadatas"][0]
                if meta.get("user_id") == user_id:
                    has_chunks = True
        except Exception:
            has_chunks = False

        if has_chunks:
            # Re-use existing document and start a new chat session
            doc_type_label = existing_doc["doc_type"] or "Document"
            session_id = str(uuid4())
            title = f"{doc_type_label}: {file.filename}"
            session_store.create_session(
                session_id=session_id,
                document_id=document_id,
                user_id=user_id,
                title=title,
            )
            return {
                "filename": file.filename,
                "document_id": document_id,
                "session_id": session_id,
                "total_characters": 0,
                "total_chunks": 0,
                "message": "Reused existing document embeddings and analysis",
                "final_extracted_data": existing_doc["analysis"],
            }
        else:
            # Document exists in Postgres but embeddings are missing in ChromaDB.
            # Regenerate embeddings and run workflow under the same document_id.
            file_path = UPLOAD_DIR / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            text = extract_text_from_pdf(str(file_path))

            meta, workflow_result = process_and_store_document(
                text=text,
                document_id=document_id,
                user_id=user_id,
                filename=file.filename,
            )

            doc_type_label = meta["final_extracted_data"].get("document_type_label", "Document")
            session_store.set_document_type(document_id, doc_type_label)

            session_id = str(uuid4())
            title = f"{doc_type_label}: {file.filename}"
            session_store.create_session(
                session_id=session_id,
                document_id=document_id,
                user_id=user_id,
                title=title,
            )

            return {
                "filename": file.filename,
                "document_id": document_id,
                "session_id": session_id,
                **meta,
            }

    # 1. Save file to disk
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Extract text
    text = extract_text_from_pdf(str(file_path))

    # 3. Create the document record first (so we have a document_id)
    document_id = session_store.create_document(
        user_id=user_id,
        filename=file.filename,
    )

    # 4. Embed + run workflow
    meta, workflow_result = process_and_store_document(
        text=text,
        document_id=document_id,
        user_id=user_id,
        filename=file.filename,
    )

    # 5. Update doc_type now that we know it
    doc_type_label = meta["final_extracted_data"].get("document_type_label", "Document")
    session_store.set_document_type(document_id, doc_type_label)

    # 6. Create the initial chat session for this document
    session_id = str(uuid4())
    title = f"{doc_type_label}: {file.filename}"
    session_store.create_session(
        session_id=session_id,
        document_id=document_id,
        user_id=user_id,
        title=title,
    )

    return {
        "filename": file.filename,
        "document_id": document_id,
        "session_id": session_id,
        **meta,
    }


@router.post("/analyze-text")
async def process_text_rfp(
    request: TextRFPRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Analyze pasted/manually entered text.

    Same flow as /upload but without a physical file.  A document record is
    created with filename="Pasted Text" so the document management model
    works identically.
    """
    filename = "Pasted Text"

    # 1. Create the document record
    document_id = session_store.create_document(
        user_id=user_id,
        filename=filename,
    )

    # 2. Embed + run workflow
    meta, workflow_result = process_and_store_document(
        text=request.text,
        document_id=document_id,
        user_id=user_id,
        filename=filename,
    )

    # 3. Update doc_type
    doc_type_label = meta["final_extracted_data"].get("document_type_label", "Document")
    session_store.set_document_type(document_id, doc_type_label)

    # 4. Create the initial chat session
    session_id = str(uuid4())
    title = f"{doc_type_label}: Pasted Text"
    session_store.create_session(
        session_id=session_id,
        document_id=document_id,
        user_id=user_id,
        title=title,
    )

    return {
        "source": "manual_text",
        "document_id": document_id,
        "session_id": session_id,
        **meta,
    }


@router.get("/download/{filename}")
async def download_file(filename: str, user_id: str = Depends(get_current_user)):
    """Serve the originally uploaded file as a download attachment."""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )