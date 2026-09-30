from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from nutrifoundation.domain.models import SourceArtifact
from nutrifoundation.domain.run_manifest import RunManifest


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS run_manifest (
  run_id TEXT PRIMARY KEY,
  pipeline_name TEXT NOT NULL,
  pipeline_version TEXT NOT NULL,
  mode TEXT NOT NULL,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_artifact (
  source_id TEXT PRIMARY KEY,
  pmid TEXT UNIQUE,
  pmcid TEXT,
  doi TEXT,
  title TEXT NOT NULL,
  source_type TEXT NOT NULL,
  publication_date TEXT,
  payload_json TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_full_text (
  pmcid TEXT PRIMARY KEY,
  source_id TEXT,
  content_xml TEXT NOT NULL,
  content_sha256 TEXT NOT NULL,
  retrieved_at TEXT NOT NULL,
  provider TEXT NOT NULL,
  FOREIGN KEY(source_id) REFERENCES source_artifact(source_id)
);

CREATE TABLE IF NOT EXISTS ingestion_event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  action TEXT NOT NULL,
  status TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES run_manifest(run_id)
);
"""


class SQLiteStore:
    def __init__(self, path: str | Path):
        self.path = str(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def save_run_manifest(self, manifest: RunManifest) -> None:
        payload = manifest.model_dump_json()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO run_manifest
                (run_id,pipeline_name,pipeline_version,mode,status,started_at,finished_at,payload_json)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(run_id) DO UPDATE SET
                  status=excluded.status,
                  finished_at=excluded.finished_at,
                  payload_json=excluded.payload_json
                """,
                (
                    manifest.run_id,
                    manifest.pipeline_name,
                    manifest.pipeline_version,
                    manifest.mode,
                    manifest.status,
                    manifest.started_at.isoformat(),
                    manifest.finished_at.isoformat() if manifest.finished_at else None,
                    payload,
                ),
            )

    def upsert_source(self, source: SourceArtifact) -> None:
        payload = source.model_dump_json()
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc).isoformat()

        with self.connect() as connection:
            connection.execute(
                """INSERT INTO source_artifact
                (source_id,pmid,pmcid,doi,title,source_type,publication_date,payload_json,payload_sha256,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(source_id) DO UPDATE SET
                  pmid=excluded.pmid,
                  pmcid=excluded.pmcid,
                  doi=excluded.doi,
                  title=excluded.title,
                  source_type=excluded.source_type,
                  publication_date=excluded.publication_date,
                  payload_json=excluded.payload_json,
                  payload_sha256=excluded.payload_sha256,
                  updated_at=excluded.updated_at
                """,
                (
                    source.source_id,
                    source.identifiers.pmid,
                    source.identifiers.pmcid,
                    source.identifiers.doi,
                    source.title,
                    source.source_type.value,
                    source.publication_date.isoformat() if source.publication_date else None,
                    payload,
                    digest,
                    now,
                    now,
                ),
            )

    def get_source(self, source_id: str) -> SourceArtifact | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM source_artifact WHERE source_id=?",
                (source_id,),
            ).fetchone()
        return SourceArtifact.model_validate_json(row[0]) if row else None

    def list_sources(self) -> list[SourceArtifact]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM source_artifact ORDER BY source_id"
            ).fetchall()
        return [SourceArtifact.model_validate_json(row[0]) for row in rows]

    def save_full_text(
        self,
        pmcid: str,
        content_xml: str,
        provider: str = "NCBI PMC",
        source_id: str | None = None,
    ) -> None:
        digest = hashlib.sha256(content_xml.encode("utf-8")).hexdigest()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO source_full_text
                (pmcid,source_id,content_xml,content_sha256,retrieved_at,provider)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(pmcid) DO UPDATE SET
                  source_id=excluded.source_id,
                  content_xml=excluded.content_xml,
                  content_sha256=excluded.content_sha256,
                  retrieved_at=excluded.retrieved_at,
                  provider=excluded.provider
                """,
                (
                    pmcid,
                    source_id,
                    content_xml,
                    digest,
                    datetime.now(timezone.utc).isoformat(),
                    provider,
                ),
            )

    def log_ingestion_event(
        self,
        run_id: str,
        source_id: str,
        action: str,
        status: str,
        detail: str | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO ingestion_event
                (run_id,source_id,action,status,detail,created_at)
                VALUES(?,?,?,?,?,?)""",
                (
                    run_id,
                    source_id,
                    action,
                    status,
                    detail,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
