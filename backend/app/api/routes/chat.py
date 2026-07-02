from uuid import uuid4

from fastapi import APIRouter

from app.vectordb.retriever import retrieve_relevant_chunks
from app.core.llm import client, GROQ_MODEL
from app.memory.chat_memory import session_store

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.get("/sessions")
async def get_sessions():
    return {"sessions": session_store.all_sessions()}


@router.post("/new-session")
async def create_new_session():
    session_id = str(uuid4())
    session_store.create_session(session_id, title="New Chat")
    return {"session_id": session_id}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    session_store.delete_session(session_id)
    return {"deleted": session_id}


@router.patch("/session/{session_id}/rename")
async def rename_session(session_id: str, title: str):
    session_store.set_title(session_id, title)
    return {"session_id": session_id, "title": title}


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    return {
        "session_id": session_id,
        "messages": session_store.get_messages(session_id),
        "title": session_store.get_title(session_id),
        "doc_name": session_store.get_doc_name(session_id),
        "analysis": session_store.get_analysis(session_id),
    }


@router.post("/ask")
async def ask_question(question: str, session_id: str):

    if session_id not in session_store:
        session_store.create_session(session_id)

    # Build conversation history string for context
    previous_messages = session_store.get_messages(session_id)
    previous_conversation = "\n".join(
        f"{msg['role']}: {msg['content']}"
        for msg in previous_messages
    )

    # Retrieve relevant chunks from the vector store, scoped to this session
    relevant_chunks = retrieve_relevant_chunks(question, session_id=session_id)
    context = "\n".join(relevant_chunks)

    # Detect analytical questions
    analytical_keywords = [
        "risk", "risks",
        "challenge", "challenges",
        "dependency", "dependencies",
        "assumption", "assumptions",
        "concern", "concerns",
        "recommendation", "recommendations",
        "issue", "issues",
        "problem", "problems",
    ]

    is_analytical_query = any(
        keyword in question.lower()
        for keyword in analytical_keywords
    )

    prompt = f"""
You are an intelligent AI Document Intelligence assistant.

PREVIOUS CONVERSATION:
{previous_conversation}

DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

IMPORTANT GUIDELINES:

1. If the answer is explicitly present in the document, answer directly and
   cite the page number when available (e.g., "(Page 3)").

2. If the user asks about risks, assumptions, dependencies, challenges,
   concerns, recommendations, issues, or any analysis beyond the document
   text, clearly identify those observations as inferred insights.

3. Never present inferred insights as confirmed facts.

4. Distinguish between:
   - Explicit document information (with page references where possible)
   - Inferred analysis

Answer clearly, accurately, and reference page numbers wherever relevant.
"""

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