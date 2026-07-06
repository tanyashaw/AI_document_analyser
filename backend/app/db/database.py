"""
Persistence layer — Postgres (Supabase) when DATABASE_URL is set, otherwise a
local SQLite file for zero-setup local development.

Tables managed here:
  users          — authentication (was here before)
  documents      — one row per uploaded / pasted document (NEW)
  chat_sessions  — one row per conversation thread (NEW)
  messages       — ordered turn-by-turn conversation history (NEW)

All four backends (Postgres or SQLite) expose the SAME interface:
  get_db(), conn.execute(sql, params), row["column"], IntegrityError.
"""

import os
from pathlib import Path
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USING_POSTGRES = bool(DATABASE_URL)

if USING_POSTGRES:
    import psycopg2
    import psycopg2.extras

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

else:
    import sqlite3

    IntegrityError = sqlite3.IntegrityError

    _DB_FILE = Path(__file__).parent / "app.db"

    def _connect():
        conn = sqlite3.connect(_DB_FILE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ── Table definitions ──────────────────────────────────────────────────────

_PG_USERS = """
    CREATE TABLE IF NOT EXISTS users (
        id           TEXT PRIMARY KEY,
        email        TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
"""

_SQLITE_USERS = """
    CREATE TABLE IF NOT EXISTS users (
        id           TEXT PRIMARY KEY,
        email        TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        created_at   TEXT NOT NULL DEFAULT (datetime('now'))
    )
"""

# documents — one row per uploaded/pasted document, independent of sessions
_PG_DOCUMENTS = """
    CREATE TABLE IF NOT EXISTS documents (
        id          TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        filename    TEXT NOT NULL,
        doc_type    TEXT,
        analysis    JSONB,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
"""

_SQLITE_DOCUMENTS = """
    CREATE TABLE IF NOT EXISTS documents (
        id         TEXT PRIMARY KEY,
        user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        filename   TEXT NOT NULL,
        doc_type   TEXT,
        analysis   TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
"""

# chat_sessions — many sessions can reference the same document
_PG_SESSIONS = """
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id          TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        title       TEXT NOT NULL DEFAULT 'New Chat',
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
"""

_SQLITE_SESSIONS = """
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id          TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        title       TEXT NOT NULL DEFAULT 'New Chat',
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )
"""

# messages — ordered conversation turns, foreign-keyed to a session
_PG_MESSAGES = """
    CREATE TABLE IF NOT EXISTS messages (
        id         BIGSERIAL PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
        role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
        content    TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
"""

_SQLITE_MESSAGES = """
    CREATE TABLE IF NOT EXISTS messages (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
        role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
        content    TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
"""


def init_db() -> None:
    """Create all tables idempotently. Safe to call multiple times."""
    if USING_POSTGRES:
        statements = [_PG_USERS, _PG_DOCUMENTS, _PG_SESSIONS, _PG_MESSAGES]
    else:
        statements = [
            _SQLITE_USERS,
            _SQLITE_DOCUMENTS,
            _SQLITE_SESSIONS,
            _SQLITE_MESSAGES,
        ]

    with get_db() as conn:
        for sql in statements:
            conn.execute(sql)


# Run once at import time so all tables exist before the first request.
init_db()