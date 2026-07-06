import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.vectordb.retriever import retrieve_relevant_chunks
from app.core.llm import client, GROQ_MODEL
from app.memory.chat_memory import session_store
from app.api.deps import get_current_user

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


def _check_owner(session_id: str, user_id: str) -> None:
    """Raise 403 if this session belongs to a different user."""
    owner = session_store.get_owner(session_id)
    if owner is not None and owner != user_id:
        raise HTTPException(
            status_code=403,
            detail="This session belongs to another user.",
        )


@router.get("/sessions")
async def get_sessions(user_id: str = Depends(get_current_user)):
    """
    Return all chat sessions for the authenticated user.

    Each item includes document_id, doc_name, and doc_type so the frontend
    can group sessions by document or display document metadata alongside
    each session title.
    """
    return {"sessions": session_store.all_sessions(user_id=user_id)}



@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    _check_owner(session_id, user_id)
    session_store.delete_session(session_id)
    return {"deleted": session_id}


@router.patch("/session/{session_id}/rename")
async def rename_session(
    session_id: str,
    title: str,
    user_id: str = Depends(get_current_user),
):
    _check_owner(session_id, user_id)
    session_store.set_title(session_id, title)
    return {"session_id": session_id, "title": title}


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Return the full history for a session including messages, title, and the
    document metadata (document_id, filename, analysis).

    The frontend uses this when restoring a session from the sidebar so it
    can render both the analysis report and the chat thread.
    """
    _check_owner(session_id, user_id)

    messages = session_store.get_messages(session_id)
    title = session_store.get_title(session_id)
    doc_name = session_store.get_doc_name(session_id)
    analysis = session_store.get_analysis(session_id)
    document_id = session_store.get_document_id_for_session(session_id)

    return {
        "session_id": session_id,
        "document_id": document_id,
        "messages": messages,
        "title": title,
        "doc_name": doc_name,
        "analysis": analysis,
    }


@router.post("/ask")
async def ask_question(
    question: str,
    session_id: str,
    user_id: str = Depends(get_current_user),
):
    """
    Ask a question about the document associated with this session.

    Retrieval is filtered by document_id + user_id so embeddings from other
    documents or other users are never returned.
    """
    if session_id not in session_store:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Upload a document to start a new session.",
        )

    _check_owner(session_id, user_id)

    # ── Resolve document identity ──────────────────────────────────────────
    document_id = session_store.get_document_id_for_session(session_id)
    if not document_id:
        raise HTTPException(
            status_code=404,
            detail="No document associated with this session.",
        )

    doc_name = session_store.get_doc_name(session_id) or "the uploaded document"
    stored_analysis = session_store.get_analysis(session_id)

    # ── Retrieve relevant chunks scoped to this document ───────────────────
    relevant_chunks = retrieve_relevant_chunks(
        question,
        document_id=document_id,
        user_id=user_id,
        top_k=6,
    )

    if not relevant_chunks:
        no_doc_answer = (
            "I don't have any document content loaded for this session. "
            "Please upload a document first, then ask your question."
        )
        session_store.append_message(session_id, "user", question)
        session_store.append_message(session_id, "assistant", no_doc_answer)
        return {"session_id": session_id, "answer": no_doc_answer}

    context = "\n\n---\n\n".join(relevant_chunks)

    # ── Conversation history ───────────────────────────────────────────────
    previous_messages = session_store.get_messages(session_id)
    previous_conversation = "\n".join(
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in previous_messages[-6:]  # last 3 turns to save tokens
    )

    # ── Structured analysis summary ────────────────────────────────────────
    analysis_summary = ""
    if stored_analysis:
        analysis_summary = f"""
STRUCTURED ANALYSIS ALREADY EXTRACTED FROM THIS DOCUMENT:
- Executive Summary: {stored_analysis.get('executive_summary', 'N/A')[:600]}
- Objectives: {json.dumps(stored_analysis.get('objectives', []))}
- Project Scope: {json.dumps([s.get('item', s) if isinstance(s, dict) else s for s in stored_analysis.get('project_scope', [])][:5])}
- Deadlines: {json.dumps([d.get('deadline', d) if isinstance(d, dict) else d for d in stored_analysis.get('deadlines', [])][:5])}
- Key Highlights: {json.dumps(stored_analysis.get('key_highlights', [])[:5])}
"""

    # ── Detect analytical questions ────────────────────────────────────────
    analytical_keywords = [
        "risk", "risks", "challenge", "challenges",
        "dependency", "dependencies", "assumption", "assumptions",
        "concern", "concerns", "recommendation", "recommendations",
        "issue", "issues", "problem", "problems",
    ]
    is_analytical_query = any(
        keyword in question.lower() for keyword in analytical_keywords
    )

    prompt = f"""You are an expert Document Intelligence assistant. You have been given access to a specific document and must ONLY answer questions based on its content.

DOCUMENT NAME: {doc_name}

{analysis_summary}

RELEVANT EXCERPTS FROM THE DOCUMENT (retrieved for this question):
{context}

PREVIOUS CONVERSATION:
{previous_conversation}

USER QUESTION: {question}

STRICT RULES:
1. Answer ONLY based on the content of "{doc_name}" shown above.
2. If the answer is present in the document, answer directly and cite the page number when available (e.g., "Page 3").
3. If the information is NOT in this document, say clearly: "This information is not found in {doc_name}." Do NOT make up an answer.
4. Never answer from general knowledge — only from this document's content.
5. Be specific: reference actual names, numbers, dates, and facts from the document.
6. If the user asks about risks, assumptions, or analysis beyond the text, clearly label those as inferred insights, not confirmed facts.

Answer:"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    answer = response.choices[0].message.content

    # Force disclaimer for analytical questions
    if is_analytical_query:
        disclaimer = (
            "⚠️ Disclaimer: The following observations are inferred from the "
            "document requirements and context. They are not necessarily "
            "explicitly stated in the uploaded document.\n\n"
        )
        if "disclaimer" not in answer.lower():
            answer = disclaimer + answer

    # Persist both turns
    session_store.append_message(session_id, "user", question)
    session_store.append_message(session_id, "assistant", answer)

    # Auto title — use first question if still default
    if session_store.get_title(session_id) in ("New Chat", "Untitled Chat"):
        title = question[:40] + ("..." if len(question) > 40 else "")
        session_store.set_title(session_id, title)

    return {"session_id": session_id, "answer": answer}