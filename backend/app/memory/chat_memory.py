"""
PGSessionStore — PostgreSQL-backed replacement for the old JSON file store.

The old implementation (_SessionStore backed by sessions.json) stored
everything in a local file, which meant data was lost whenever the app ran
on a different machine or restarted on a stateless host.  This module
replaces it with direct Postgres queries through the shared get_db()
context manager so all data is stored in Supabase and is accessible from
any environment.

Public interface is intentionally similar to the old store so call sites in
rfp.py and chat.py need minimal changes.  The backward-compat proxy classes
(_MessagesProxy, _TitlesProxy) have been removed — callers now use the store
methods directly.
"""

from __future__ import annotations

import json
from uuid import uuid4

from app.db.database import get_db, USING_POSTGRES


class PGSessionStore:
    """All chat/document persistence, backed by PostgreSQL (or SQLite locally)."""

    # ── Documents ─────────────────────────────────────────────────────────

    def create_document(
        self,
        user_id: str,
        filename: str,
        doc_type: str | None = None,
    ) -> str:
        """Insert a document record and return its new document_id."""
        doc_id = str(uuid4())
        with get_db() as conn:
            conn.execute(
                "INSERT INTO documents (id, user_id, filename, doc_type) VALUES (?, ?, ?, ?)",
                (doc_id, user_id, filename, doc_type),
            )
        return doc_id

    def set_document_analysis(self, document_id: str, analysis: dict) -> None:
        """Persist the extracted analysis JSON for a document."""
        blob = json.dumps(analysis, ensure_ascii=False)
        with get_db() as conn:
            if USING_POSTGRES:
                conn.execute(
                    "UPDATE documents SET analysis = ?::jsonb WHERE id = ?",
                    (blob, document_id),
                )
            else:
                conn.execute(
                    "UPDATE documents SET analysis = ? WHERE id = ?",
                    (blob, document_id),
                )

    def set_document_type(self, document_id: str, doc_type: str) -> None:
        """Update the doc_type label for a document."""
        with get_db() as conn:
            conn.execute(
                "UPDATE documents SET doc_type = ? WHERE id = ?",
                (doc_type, document_id),
            )

    def get_document(self, document_id: str, user_id: str) -> dict | None:
        """
        Return document metadata for the given document_id, or None if it
        doesn't exist or belongs to a different user.
        """
        with get_db() as conn:
            row = conn.execute(
                "SELECT id, user_id, filename, doc_type, analysis FROM documents "
                "WHERE id = ? AND user_id = ?",
                (document_id, user_id),
            ).fetchone()

        if row is None:
            return None

        analysis = row["analysis"]
        if isinstance(analysis, str):
            try:
                analysis = json.loads(analysis)
            except Exception:
                analysis = None

        return {
            "document_id": row["id"],
            "user_id": row["user_id"],
            "filename": row["filename"],
            "doc_type": row["doc_type"],
            "analysis": analysis,
        }

    def get_document_by_filename(self, user_id: str, filename: str) -> dict | None:
        """
        Return document metadata for the given user_id and filename, or None if not found.
        """
        with get_db() as conn:
            row = conn.execute(
                "SELECT id, user_id, filename, doc_type, analysis FROM documents "
                "WHERE user_id = ? AND filename = ?",
                (user_id, filename),
            ).fetchone()

        if row is None:
            return None

        analysis = row["analysis"]
        if isinstance(analysis, str):
            try:
                analysis = json.loads(analysis)
            except Exception:
                analysis = None

        return {
            "document_id": row["id"],
            "user_id": row["user_id"],
            "filename": row["filename"],
            "doc_type": row["doc_type"],
            "analysis": analysis,
        }


    # ── Chat sessions ─────────────────────────────────────────────────────

    def create_session(
        self,
        session_id: str,
        document_id: str,
        user_id: str,
        title: str = "New Chat",
    ) -> None:
        """Create a chat session linked to an existing document."""
        with get_db() as conn:
            conn.execute(
                "INSERT INTO chat_sessions (id, user_id, document_id, title) "
                "VALUES (?, ?, ?, ?)",
                (session_id, user_id, document_id, title),
            )

    def delete_session(self, session_id: str) -> None:
        """Delete a chat session (cascade deletes its messages)."""
        with get_db() as conn:
            conn.execute(
                "DELETE FROM chat_sessions WHERE id = ?", (session_id,)
            )

    def all_sessions(self, user_id: str) -> list[dict]:
        """
        Return all chat sessions for a user, newest first, joined with the
        document so callers get filename/doc_type without a second query.
        """
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT cs.id         AS session_id,
                       cs.title,
                       cs.document_id,
                       d.filename    AS doc_name,
                       d.doc_type
                FROM   chat_sessions cs
                JOIN   documents d ON d.id = cs.document_id
                WHERE  cs.user_id = ?
                ORDER  BY cs.created_at DESC
                """,
                (user_id,),
            ).fetchall()

        return [
            {
                "session_id": r["session_id"],
                "title": r["title"],
                "document_id": r["document_id"],
                "doc_name": r["doc_name"],
                "doc_type": r["doc_type"],
            }
            for r in rows
        ]

    def get_owner(self, session_id: str) -> str | None:
        """Return the user_id that owns this session, or None if not found."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT user_id FROM chat_sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return row["user_id"] if row else None

    def get_document_id_for_session(self, session_id: str) -> str | None:
        """Return the document_id linked to this session."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT document_id FROM chat_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return row["document_id"] if row else None

    def __contains__(self, session_id: str) -> bool:
        with get_db() as conn:
            row = conn.execute(
                "SELECT 1 FROM chat_sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return row is not None

    # ── Session metadata ──────────────────────────────────────────────────

    def get_title(self, session_id: str) -> str:
        with get_db() as conn:
            row = conn.execute(
                "SELECT title FROM chat_sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return row["title"] if row else "Untitled Chat"

    def set_title(self, session_id: str, title: str) -> None:
        with get_db() as conn:
            conn.execute(
                "UPDATE chat_sessions SET title = ? WHERE id = ?",
                (title, session_id),
            )

    def get_doc_name(self, session_id: str) -> str | None:
        """Return the filename of the document linked to this session."""
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT d.filename
                FROM   chat_sessions cs
                JOIN   documents d ON d.id = cs.document_id
                WHERE  cs.id = ?
                """,
                (session_id,),
            ).fetchone()
        return row["filename"] if row else None

    def get_analysis(self, session_id: str) -> dict | None:
        """
        Return the extracted analysis JSON for the document linked to this
        session (analysis lives on the document, not the session).
        """
        with get_db() as conn:
            row = conn.execute(
                """
                SELECT d.analysis
                FROM   chat_sessions cs
                JOIN   documents d ON d.id = cs.document_id
                WHERE  cs.id = ?
                """,
                (session_id,),
            ).fetchone()

        if row is None or row["analysis"] is None:
            return None

        analysis = row["analysis"]
        if isinstance(analysis, str):
            try:
                return json.loads(analysis)
            except Exception:
                return None
        return analysis  # already a dict when psycopg2 deserialises JSONB

    # ── Messages ──────────────────────────────────────────────────────────

    def get_messages(self, session_id: str) -> list[dict]:
        """Return all messages for a session, ordered by insertion."""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT role, content FROM messages "
                "WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    def append_message(self, session_id: str, role: str, content: str) -> None:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )


# Singleton — imported everywhere
session_store = PGSessionStore()