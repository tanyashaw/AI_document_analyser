#!/usr/bin/env python
"""
One-shot database migration script.

Creates the documents, chat_sessions, and messages tables in the Postgres
database pointed to by DATABASE_URL.  Safe to run multiple times — all
CREATE statements use IF NOT EXISTS.

Usage:
    cd backend
    python migrate.py
"""

import os
import sys
from pathlib import Path

# Make sure the app package is importable when running from the backend/ dir.
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    print(
        "ERROR: DATABASE_URL is not set.\n"
        "Set it in your .env file or as an environment variable and re-run."
    )
    sys.exit(1)

import psycopg2

STATEMENTS = [
    # users — must exist before any FK references it
    """
    CREATE TABLE IF NOT EXISTS users (
        id            TEXT PRIMARY KEY,
        email         TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,

    # documents — uploaded files / pasted text, user-owned
    """
    CREATE TABLE IF NOT EXISTS documents (
        id         TEXT PRIMARY KEY,
        user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        filename   TEXT NOT NULL,
        doc_type   TEXT,
        analysis   JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,

    # chat_sessions — many sessions can reference one document
    """
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id          TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        title       TEXT NOT NULL DEFAULT 'New Chat',
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,

    # messages — ordered conversation turns per session
    """
    CREATE TABLE IF NOT EXISTS messages (
        id         BIGSERIAL PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
        role       TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
        content    TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,

    # Performance indices
    "CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_chat_sessions_doc ON chat_sessions(document_id)",
    "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)",
]


def run_migration():
    print(f"Connecting to database…")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        for stmt in STATEMENTS:
            stmt = stmt.strip()
            if not stmt:
                continue
            label = stmt.split("\n")[0][:60].strip()
            print(f"  Running: {label}…")
            cur.execute(stmt)

        conn.commit()
        print("\nOK: Migration complete. All tables and indices are in place.")
    except Exception as exc:
        conn.rollback()
        print(f"\nFAIL: Migration failed: {exc}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_migration()
