"""
Persistence for user accounts — Postgres if DATABASE_URL is set, otherwise a
local SQLite file for zero-setup local development.

Why this exists: with SQLite alone, "the database" is just a file sitting
next to the code. Whichever machine runs the app owns that file, so an
account created on one machine simply doesn't exist on another machine's
copy of the repo (this is exactly what caused "my login works on my
personal machine but not my work machine"). Pointing DATABASE_URL at a
real hosted Postgres instance (Supabase, Neon, and Render all have usable
free tiers) fixes that at the root: every machine talks to the same
database over the network, so accounts — and anything else you store here
later — are shared instead of living on one laptop's disk.

Both backends expose the SAME interface to the rest of the app:
get_db(), conn.execute(sql, params).fetchone()/.fetchall(), row["column"]
access, and an IntegrityError you can catch on duplicate inserts — so
nothing in auth.py (or any future caller) needs backend-specific code.
Just set DATABASE_URL and nothing else has to change.
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
        Makes a psycopg2 connection support conn.execute(sql, params) the
        same way sqlite3.Connection does (sqlite3 lets you call .execute()
        directly on the connection; psycopg2 requires a cursor). Also
        translates '?' placeholders — used everywhere else in this
        codebase, sqlite-style — into psycopg2's '%s' style, so callers
        don't need to know which database they're talking to.
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


def init_db() -> None:
    if USING_POSTGRES:
        create_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """
        # Postgres UNIQUE is case-sensitive by default (no COLLATE NOCASE
        # equivalent needed here) — not a problem in practice because
        # every caller already lowercases the email before insert/lookup
        # (see auth.py), so case-insensitivity is enforced at the
        # application layer either way.
    else:
        create_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """
    with get_db() as conn:
        conn.execute(create_sql)


# Run once at import time so the table exists before the first request.
init_db()