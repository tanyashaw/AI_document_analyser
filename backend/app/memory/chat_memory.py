import json
import os
from pathlib import Path

# Path to the persistence file (lives next to this module)
_SESSIONS_FILE = Path(__file__).parent / "sessions.json"


def _load() -> dict:
    """Load sessions from disk. Returns empty dict if file doesn't exist."""
    if _SESSIONS_FILE.exists():
        try:
            with open(_SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save(data: dict):
    """Persist sessions to disk atomically."""
    tmp = _SESSIONS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, _SESSIONS_FILE)


class _SessionStore:
    """
    Thread-safe-ish in-process store backed by a JSON file.
    Provides dict-like access to session messages plus helper methods
    for titles and document metadata.
    """

    def __init__(self):
        self._data: dict = _load()

    # ── Internal helpers ──────────────────────────────────────

    def _get_session(self, session_id: str) -> dict:
        return self._data.get(session_id, {})

    # ── Session lifecycle ─────────────────────────────────────

    def create_session(self, session_id: str, title: str = "New Chat") -> None:
        if session_id not in self._data:
            self._data[session_id] = {
                "title": title,
                "messages": [],
                "doc_name": None,
                "doc_type": None,
            }
            _save(self._data)

    def delete_session(self, session_id: str) -> None:
        if session_id in self._data:
            del self._data[session_id]
            _save(self._data)

    def all_sessions(self) -> list[dict]:
        return [
            {
                "session_id": sid,
                "title": s.get("title", "Untitled Chat"),
                "doc_name": s.get("doc_name"),
                "doc_type": s.get("doc_type"),
            }
            for sid, s in self._data.items()
        ]

    def __contains__(self, session_id: str) -> bool:
        return session_id in self._data

    # ── Messages ──────────────────────────────────────────────

    def get_messages(self, session_id: str) -> list:
        return self._data.get(session_id, {}).get("messages", [])

    def append_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self._data:
            self.create_session(session_id)
        self._data[session_id]["messages"].append(
            {"role": role, "content": content}
        )
        _save(self._data)

    # ── Titles ────────────────────────────────────────────────

    def get_title(self, session_id: str) -> str:
        return self._data.get(session_id, {}).get("title", "Untitled Chat")

    def set_title(self, session_id: str, title: str) -> None:
        if session_id in self._data:
            self._data[session_id]["title"] = title
            _save(self._data)

    # ── Document metadata ─────────────────────────────────────

    def set_doc_info(self, session_id: str, doc_name: str, doc_type: str) -> None:
        if session_id in self._data:
            self._data[session_id]["doc_name"] = doc_name
            self._data[session_id]["doc_type"] = doc_type
            _save(self._data)

    def get_doc_name(self, session_id: str) -> str | None:
        return self._data.get(session_id, {}).get("doc_name")


# Singleton — imported everywhere
session_store = _SessionStore()

# ── Backward-compat shims (used by chat.py) ──────────────────
# These proxy dicts map to the underlying SessionStore so existing
# code that reads chat_sessions[sid] or chat_titles[sid] still works.

class _MessagesProxy:
    def __getitem__(self, sid):
        return session_store.get_messages(sid)

    def __setitem__(self, sid, val):
        # Used when code does: chat_sessions[sid] = []
        session_store.create_session(sid)

    def get(self, sid, default=None):
        if sid in session_store:
            return session_store.get_messages(sid)
        return default

    def __contains__(self, sid):
        return sid in session_store

    def __iter__(self):
        return iter(s["session_id"] for s in session_store.all_sessions())


class _TitlesProxy:
    def __getitem__(self, sid):
        return session_store.get_title(sid)

    def __setitem__(self, sid, val):
        session_store.set_title(sid, val)

    def get(self, sid, default=None):
        if sid in session_store:
            return session_store.get_title(sid)
        return default


# These names are imported by chat.py for backward compat
chat_sessions = _MessagesProxy()
chat_titles = _TitlesProxy()