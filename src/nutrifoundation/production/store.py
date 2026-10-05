from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Any

from .models import digest, now


SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS d0_record (
 kind TEXT NOT NULL, id TEXT NOT NULL, sha256 TEXT NOT NULL,
 payload TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(kind,id));
CREATE TABLE IF NOT EXISTS d0_event (
 id INTEGER PRIMARY KEY, kind TEXT NOT NULL, record_id TEXT NOT NULL,
 payload TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS d0_job (
 job_key TEXT PRIMARY KEY, payload TEXT NOT NULL, payload_sha TEXT NOT NULL,
 status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
 max_attempts INTEGER NOT NULL, available_at REAL NOT NULL,
 lease_until REAL, token TEXT, result_sha TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS d0_rate (provider TEXT PRIMARY KEY, next_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS d0_invalidation (
 dependency_id TEXT PRIMARY KEY, reason TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS d0_dependency (
 child_id TEXT NOT NULL, parent_id TEXT NOT NULL, PRIMARY KEY(child_id,parent_id));
"""


class ProductionStore:
    """Additive tables: never rewrites legacy F0 or benchmark payloads."""

    def __init__(self, db: str | Path):
        self.db = str(db)
        with self.transaction() as con:
            con.executescript(SCHEMA)

    @contextmanager
    def transaction(self, *, immediate: bool = True):
        con = sqlite3.connect(self.db, timeout=30)
        con.row_factory = sqlite3.Row
        try:
            con.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def put(self, kind: str, record_id: str, payload: Any, *, con=None) -> str:
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump(mode="json")
        sha = digest(payload)
        if con is None:
            with self.transaction() as tx:
                return self.put(kind, record_id, payload, con=tx)
        row = con.execute("SELECT sha256 FROM d0_record WHERE kind=? AND id=?", (kind, record_id)).fetchone()
        if row and row[0] != sha:
            raise ValueError(f"Immutable {kind} ID already has different content: {record_id}")
        con.execute("INSERT OR IGNORE INTO d0_record VALUES(?,?,?,?,?)", (kind, record_id, sha, json.dumps(payload, ensure_ascii=False), now().isoformat()))
        return sha

    def get(self, kind: str, record_id: str) -> dict:
        with self.transaction(immediate=False) as con:
            row = con.execute("SELECT payload FROM d0_record WHERE kind=? AND id=?", (kind, record_id)).fetchone()
        if not row:
            raise ValueError(f"Missing {kind}: {record_id}")
        return json.loads(row[0])

    def event(self, kind: str, record_id: str, payload: dict):
        with self.transaction() as con:
            con.execute("INSERT INTO d0_event(kind,record_id,payload,created_at) VALUES(?,?,?,?)", (kind, record_id, json.dumps(payload, ensure_ascii=False), now().isoformat()))

    def depend(self, child: str, parents: tuple[str, ...], *, con=None):
        if con is None:
            with self.transaction() as tx:
                return self.depend(child, parents, con=tx)
        for parent in parents:
            if con.execute("SELECT 1 FROM d0_invalidation WHERE dependency_id=?",(parent,)).fetchone():
                raise ValueError("Cannot derive from an invalidated dependency")
            if child == parent:
                raise ValueError("Dependency cycle")
            cycle = con.execute("WITH RECURSIVE p(id) AS (SELECT ? UNION SELECT parent_id FROM d0_dependency JOIN p ON child_id=p.id) SELECT 1 FROM p WHERE id=?", (parent, child)).fetchone()
            if cycle:
                raise ValueError("Dependency cycle")
            con.execute("INSERT OR IGNORE INTO d0_dependency VALUES(?,?)", (child, parent))

    def invalidate(self, dependency: str, reason: str) -> tuple[str, ...]:
        with self.transaction() as con:
            affected = con.execute("WITH RECURSIVE impacted(id) AS (SELECT ? UNION SELECT child_id FROM d0_dependency JOIN impacted ON parent_id=impacted.id) SELECT id FROM impacted ORDER BY id", (dependency,)).fetchall()
            for row in affected:
                con.execute("INSERT OR IGNORE INTO d0_invalidation VALUES(?,?,?)", (row[0], reason, now().isoformat()))
        return tuple(row[0] for row in affected)

    def active(self, record_id: str) -> bool:
        with self.transaction(immediate=False) as con:
            return not con.execute("SELECT 1 FROM d0_invalidation WHERE dependency_id=?", (record_id,)).fetchone()
