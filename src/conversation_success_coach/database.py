"""Small thread-safe SQLite wrapper and schema."""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS privacy_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    allow_raw_content_storage INTEGER NOT NULL DEFAULT 0,
    default_analysis_retention_days INTEGER NOT NULL DEFAULT 7,
    audit_retention_days INTEGER NOT NULL DEFAULT 30,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('sales', 'support', 'recruiting', 'community')),
    owner TEXT NOT NULL,
    participant_label TEXT NOT NULL,
    goal TEXT NOT NULL DEFAULT '',
    stage TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT
);

CREATE TABLE IF NOT EXISTS turns (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    speaker TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('operator', 'participant', 'observer')),
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (conversation_id, position)
);

CREATE TABLE IF NOT EXISTS analyses (
    id TEXT PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(id) ON DELETE CASCADE,
    mode TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    result_json TEXT NOT NULL,
    raw_content_stored INTEGER NOT NULL DEFAULT 0,
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    expires_at TEXT
);

CREATE TABLE IF NOT EXISTS suggestions (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    conversation_id TEXT REFERENCES conversations(id) ON DELETE CASCADE,
    mode TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    action TEXT NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    suggestion_id TEXT REFERENCES suggestions(id) ON DELETE SET NULL,
    conversation_id TEXT REFERENCES conversations(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('accepted', 'rejected', 'outcome')),
    outcome TEXT,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS playbooks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('sales', 'support', 'recruiting', 'community')),
    description TEXT NOT NULL,
    principles_json TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    is_demo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    summary TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_turns_conversation
    ON turns (conversation_id, position);
CREATE INDEX IF NOT EXISTS idx_analyses_conversation
    ON analyses (conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_expiry
    ON analyses (expires_at);
CREATE INDEX IF NOT EXISTS idx_suggestions_conversation
    ON suggestions (conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_created
    ON feedback (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_created
    ON audit (created_at DESC);
"""


class Database:
    """One-connection SQLite store guarded for TestClient/server threads."""

    def __init__(self, path: str) -> None:
        self.path = path
        if path != ":memory:":
            db_path = Path(path).expanduser().resolve()
            db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            resolved = str(db_path)
        else:
            resolved = path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(
            resolved,
            check_same_thread=False,
            isolation_level=None,
        )
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA busy_timeout = 5000")
            if path != ":memory:":
                self._conn.execute("PRAGMA journal_mode = WAL")
                self._conn.execute("PRAGMA synchronous = NORMAL")
            self._conn.executescript(SCHEMA)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield self._conn
                self._conn.execute("COMMIT")
            except Exception:
                self._conn.execute("ROLLBACK")
                raise

    def execute(
        self,
        sql: str,
        params: Sequence[Any] = (),
    ) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.execute(sql, params)

    def executemany(
        self,
        sql: str,
        values: Sequence[Sequence[Any]],
    ) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.executemany(sql, values)

    def query_all(
        self,
        sql: str,
        params: Sequence[Any] = (),
    ) -> list[sqlite3.Row]:
        with self._lock:
            return list(self._conn.execute(sql, params).fetchall())

    def query_one(
        self,
        sql: str,
        params: Sequence[Any] = (),
    ) -> sqlite3.Row | None:
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    def close(self) -> None:
        with self._lock:
            self._conn.close()
