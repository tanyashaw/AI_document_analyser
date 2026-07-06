"""
Persistence layer — Postgres (Supabase). Requires DATABASE_URL to be set.

Tables managed here:
  users          — authentication
  documents      — one row per uploaded / pasted document
  chat_sessions  — one row per conversation thread
  messages       — ordered turn-by-turn conversation history

Exposes the Postgres interface: get_db(), conn.execute(sql, params), row["column"], IntegrityError.
"""

import os
from contextlib import contextmanager
import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "A PostgreSQL database connection string is required to run this application."
    )

IntegrityError = psycopg2.IntegrityError


class _PGConnWrapper:
    """
    Makes a psycopg2 connection support conn.execute(sql, params) the same
    way sqlite3.Connection does. Also translates '?' placeholders (used
    everywhere else in this codebase) into psycopg2's '%s' style.
    """

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql: str, params=()):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql.replace("?", "%s"), params)
        return cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def _connect():
    raw_conn = psycopg2.connect(DATABASE_URL)
    return _PGConnWrapper(raw_conn)


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ── Table definitions ──────────────────────────────────────────────────────

_USERS_SQL = """
    CREATE TABLE IF NOT EXISTS users (
        id           TEXT PRIMARY KEY,
        email        TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
"""

_DOCUMENTS_SQL = """
    CREATE TABLE IF NOT EXISTS documents (
        id          TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        filename    TEXT NOT NULL,
        doc_type    TEXT,
        analysis    JSONB,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
"""

_SESSIONS_SQL = """
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id          TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        title       TEXT NOT NULL DEFAULT 'New Chat',
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
"""

_MESSAGES_SQL = """
    CREATE TABLE IF NOT EXISTS messages (
        id         BIGSERIAL PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
        role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
        content    TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
"""


def init_db() -> None:
    """Create all tables idempotently. Safe to call multiple times."""
    statements = [_USERS_SQL, _DOCUMENTS_SQL, _SESSIONS_SQL, _MESSAGES_SQL]
    with get_db() as conn:
        for sql in statements:
            conn.execute(sql)


# Run once at import time so all tables exist before the first request.
init_db()