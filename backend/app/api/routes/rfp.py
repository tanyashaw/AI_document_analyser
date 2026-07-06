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


def _ensure_session(session_id: Optional[str], user_id: str) -> str:
    """
    Guarantee we always have a session_id to scope vector store chunks to.
    If the caller didn't provide one, create a fresh chat session and use
    that ID so chunks and future chat retrieval line up automatically.
    Raises 403 if the caller tries to upload into a session owned by
    a different user.
    """
    if session_id and session_id in session_store:
        owner = session_store.get_owner(session_id)
        if owner is not None and owner != user_id:
            raise HTTPException(status_code=403, detail="This session belongs to another user.")
        return session_id

    new_session_id = session_id or str(uuid4())
    session_store.create_session(new_session_id, user_id=user_id)
    return new_session_id


def process_rfp_text(text: str, session_id: str) -> tuple[dict, dict]:
    """
    Process raw document text through the agent workflow.
    Returns (final_extracted_data, workflow_result).

    NOTE: the full document text is handed to the workflow, not a
    truncated slice of it. The workflow (app/graph/workflow.py) batches
    the full text and extracts from every batch, so long documents are
    fully covered, not just their first ~2 pages.
    """
    # Small, fine-grained chunks used ONLY for the chat/RAG feature —
    # separate from the larger batches the extraction workflow builds
    # internally.
    chunks = chunk_document(text)
    store_chunks(chunks, session_id=session_id)

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

    # Persist so the analysis is restored when the user reopens this session
    session_store.set_analysis(session_id, final_response)

    meta = {
        "total_characters": len(text),
        "total_chunks": len(chunks),
        "message": "Document processed successfully",
        "session_id": session_id,
        "final_extracted_data": final_response,
    }

    return meta, workflow_result


@router.post("/upload")
async def upload_rfp(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
    user_id: str = Depends(get_current_user),
):
    session_id = _ensure_session(session_id, user_id)

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text_from_pdf(str(file_path))

    meta, workflow_result = process_rfp_text(text, session_id=session_id)

    doc_type_label = meta["final_extracted_data"].get("document_type_label", "Document")
    title = f"{doc_type_label}: {file.filename}"
    session_store.set_title(session_id, title)
    session_store.set_doc_info(session_id, file.filename, doc_type_label)

    return {"filename": file.filename, **meta}


@router.post("/analyze-text")
async def process_text_rfp(request: TextRFPRequest, user_id: str = Depends(get_current_user)):
    session_id = _ensure_session(request.session_id, user_id)

    meta, workflow_result = process_rfp_text(request.text, session_id=session_id)

    doc_type_label = meta["final_extracted_data"].get("document_type_label", "Document")
    title = f"{doc_type_label}: Pasted Text"
    session_store.set_title(session_id, title)
    session_store.set_doc_info(session_id, "Pasted Text", doc_type_label)

    return {"source": "manual_text", **meta}


@router.get("/download/{filename}")
async def download_file(filename: str, user_id: str = Depends(get_current_user)):
    """Serve the originally uploaded file as a download attachment.
    Requires login (previously unauthenticated)."""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )