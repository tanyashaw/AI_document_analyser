from uuid import uuid4
import json

from fastapi import APIRouter, Header, HTTPException

from app.vectordb.retriever import retrieve_relevant_chunks
from app.core.llm import client, GROQ_MODEL
from app.memory.chat_memory import session_store

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


def _check_owner(session_id: str, user_id: str) -> None:
    """Raise 403 if this session belongs to a different user.
    Sessions with no recorded owner (created before this check existed)
    are left accessible rather than locked out."""
    owner = session_store.get_owner(session_id)
    if owner is not None and owner != user_id:
        raise HTTPException(status_code=403, detail="This session belongs to another user.")


@router.get("/sessions")
async def get_sessions(x_user_id: str = Header(...)):
    return {"sessions": session_store.all_sessions(user_id=x_user_id)}


@router.post("/new-session")
async def create_new_session(x_user_id: str = Header(...)):
    session_id = str(uuid4())
    session_store.create_session(session_id, title="New Chat", user_id=x_user_id)
    return {"session_id": session_id}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str, x_user_id: str = Header(...)):
    _check_owner(session_id, x_user_id)
    session_store.delete_session(session_id)
    return {"deleted": session_id}


@router.patch("/session/{session_id}/rename")
async def rename_session(session_id: str, title: str, x_user_id: str = Header(...)):
    _check_owner(session_id, x_user_id)
    session_store.set_title(session_id, title)
    return {"session_id": session_id, "title": title}


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, x_user_id: str = Header(...)):
    _check_owner(session_id, x_user_id)
    return {
        "session_id": session_id,
        "messages": session_store.get_messages(session_id),
        "title": session_store.get_title(session_id),
        "doc_name": session_store.get_doc_name(session_id),
        "analysis": session_store.get_analysis(session_id),
    }


@router.post("/ask")
async def ask_question(question: str, session_id: str, x_user_id: str = Header(...)):

    if session_id not in session_store:
        session_store.create_session(session_id, user_id=x_user_id)
    else:
        _check_owner(session_id, x_user_id)

    # ── Document identity ──────────────────────────────────────────────────
    doc_name = session_store.get_doc_name(session_id) or "the uploaded document"
    doc_type = session_store.get_doc_name(session_id)  # may be None
    stored_analysis = session_store.get_analysis(session_id)

    # ── Retrieve relevant chunks scoped to this session ────────────────────
    # top_k=6 gives broader coverage than 3 for detailed questions
    relevant_chunks = retrieve_relevant_chunks(question, session_id=session_id, top_k=6)

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
        for msg in previous_messages[-6:]  # last 3 turns only to save tokens
    )

    # ── Structured analysis summary (already extracted) ───────────────────
    analysis_summary = ""
    if stored_analysis:
        # Provide a compact version of the structured analysis for the LLM
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