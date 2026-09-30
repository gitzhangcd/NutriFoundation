from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from nutrifoundation.domain.evidence_pipeline import (
    EvidenceExtractionCandidate,
    EvidenceVerificationRecord,
    F0FreezeRecord,
)
from nutrifoundation.domain.models import EvidenceUnit, SourceArtifact
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

CREATE TABLE IF NOT EXISTS source_text_snapshot (
  text_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  text_kind TEXT NOT NULL,
  content TEXT NOT NULL,
  content_sha256 TEXT NOT NULL,
  provider TEXT NOT NULL,
  retrieved_at TEXT NOT NULL,
  FOREIGN KEY(source_id) REFERENCES source_artifact(source_id)
);

CREATE INDEX IF NOT EXISTS idx_source_text_source
ON source_text_snapshot(source_id, text_kind);

CREATE TABLE IF NOT EXISTS evidence_candidate (
  candidate_id TEXT PRIMARY KEY,
  evidence_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  extractor_id TEXT NOT NULL,
  source_text_sha256 TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(source_id) REFERENCES source_artifact(source_id),
  FOREIGN KEY(run_id) REFERENCES run_manifest(run_id)
);

CREATE TABLE IF NOT EXISTS evidence_verification (
  verification_id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL,
  evidence_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  verifier_id TEXT NOT NULL,
  status TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(candidate_id) REFERENCES evidence_candidate(candidate_id),
  FOREIGN KEY(source_id) REFERENCES source_artifact(source_id),
  FOREIGN KEY(run_id) REFERENCES run_manifest(run_id)
);

CREATE TABLE IF NOT EXISTS evidence_unit_f0 (
  evidence_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  run_id TEXT NOT NULL,
  candidate_ref TEXT NOT NULL,
  verification_ref TEXT NOT NULL,
  source_text_sha256 TEXT NOT NULL,
  evidence_payload_json TEXT NOT NULL,
  evidence_payload_sha256 TEXT NOT NULL,
  freeze_payload_json TEXT NOT NULL,
  frozen_at TEXT NOT NULL,
  FOREIGN KEY(source_id) REFERENCES source_artifact(source_id),
  FOREIGN KEY(run_id) REFERENCES run_manifest(run_id)
);

CREATE TABLE IF NOT EXISTS evidence_event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  evidence_id TEXT NOT NULL,
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
            existing = connection.execute(
                "SELECT status,payload_json FROM run_manifest WHERE run_id=?",
                (manifest.run_id,),
            ).fetchone()

            if (
                existing
                and existing["status"] == "completed"
                and existing["payload_json"] != payload
            ):
                raise ValueError(
                    f"Completed RunManifest is immutable: {manifest.run_id}"
                )

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

    def save_source_text(
        self,
        source_id: str,
        text_kind: str,
        content: str,
        provider: str,
    ) -> str:
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        text_id = f"{source_id}:{text_kind}:{digest[:16]}"
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as connection:
            connection.execute(
                """INSERT OR IGNORE INTO source_text_snapshot
                (text_id,source_id,text_kind,content,content_sha256,provider,retrieved_at)
                VALUES(?,?,?,?,?,?,?)""",
                (text_id, source_id, text_kind, content, digest, provider, now),
            )
        return text_id

    def get_source_text(
        self,
        source_id: str,
        *,
        preferred_kinds: tuple[str, ...] = ("pmc_fulltext", "pubmed_abstract"),
    ) -> tuple[str, str, str] | None:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT text_kind,content,content_sha256
                FROM source_text_snapshot
                WHERE source_id=?
                ORDER BY retrieved_at DESC""",
                (source_id,),
            ).fetchall()
        by_kind = {row["text_kind"]: row for row in rows}
        for kind in preferred_kinds:
            if kind in by_kind:
                row = by_kind[kind]
                return row["content"], row["text_kind"], row["content_sha256"]
        if rows:
            row = rows[0]
            return row["content"], row["text_kind"], row["content_sha256"]
        return None

    def save_evidence_candidate(
        self,
        candidate: EvidenceExtractionCandidate,
        run_id: str,
    ) -> None:
        payload = candidate.model_dump_json()
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        with self.connect() as connection:
            existing = connection.execute(
                "SELECT payload_json FROM evidence_candidate WHERE candidate_id=?",
                (candidate.candidate_id,),
            ).fetchone()
            if existing and existing["payload_json"] != payload:
                raise ValueError(
                    f"EvidenceExtractionCandidate is immutable: {candidate.candidate_id}"
                )
            connection.execute(
                """INSERT OR IGNORE INTO evidence_candidate
                (candidate_id,evidence_id,source_id,run_id,extractor_id,source_text_sha256,payload_json,payload_sha256,created_at)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    candidate.candidate_id,
                    candidate.evidence.evidence_id,
                    candidate.evidence.source_id,
                    run_id,
                    candidate.extractor_id,
                    candidate.source_text_sha256,
                    payload,
                    digest,
                    candidate.created_at.isoformat(),
                ),
            )

    def save_evidence_verification(
        self,
        record: EvidenceVerificationRecord,
        run_id: str,
    ) -> None:
        payload = record.model_dump_json()
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        with self.connect() as connection:
            existing = connection.execute(
                "SELECT payload_json FROM evidence_verification WHERE verification_id=?",
                (record.verification_id,),
            ).fetchone()
            if existing and existing["payload_json"] != payload:
                raise ValueError(
                    f"EvidenceVerificationRecord is immutable: {record.verification_id}"
                )
            connection.execute(
                """INSERT OR IGNORE INTO evidence_verification
                (verification_id,candidate_id,evidence_id,source_id,run_id,verifier_id,status,payload_json,payload_sha256,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    record.verification_id,
                    record.candidate_id,
                    record.evidence_id,
                    record.source_id,
                    run_id,
                    record.verifier_id,
                    record.status,
                    payload,
                    digest,
                    record.verified_at.isoformat(),
                ),
            )

    def freeze_f0(
        self,
        evidence: EvidenceUnit,
        freeze: F0FreezeRecord,
        run_id: str,
    ) -> None:
        evidence_payload = evidence.model_dump_json()
        evidence_digest = hashlib.sha256(evidence_payload.encode("utf-8")).hexdigest()
        freeze_payload = freeze.model_dump_json()
        with self.connect() as connection:
            existing = connection.execute(
                """SELECT evidence_payload_json,freeze_payload_json
                FROM evidence_unit_f0 WHERE evidence_id=?""",
                (evidence.evidence_id,),
            ).fetchone()
            if existing and (
                existing["evidence_payload_json"] != evidence_payload
                or existing["freeze_payload_json"] != freeze_payload
            ):
                raise ValueError(
                    f"F0 EvidenceUnit is immutable: {evidence.evidence_id}"
                )
            connection.execute(
                """INSERT OR IGNORE INTO evidence_unit_f0
                (evidence_id,source_id,run_id,candidate_ref,verification_ref,source_text_sha256,evidence_payload_json,evidence_payload_sha256,freeze_payload_json,frozen_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    evidence.evidence_id,
                    evidence.source_id,
                    run_id,
                    freeze.candidate_ref,
                    freeze.verification_ref,
                    freeze.source_text_sha256,
                    evidence_payload,
                    evidence_digest,
                    freeze_payload,
                    freeze.frozen_at.isoformat(),
                ),
            )

    def get_f0_evidence(self, evidence_id: str) -> EvidenceUnit | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT evidence_payload_json FROM evidence_unit_f0 WHERE evidence_id=?",
                (evidence_id,),
            ).fetchone()
        return EvidenceUnit.model_validate_json(row[0]) if row else None

    def list_f0_evidence(self) -> list[EvidenceUnit]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT evidence_payload_json FROM evidence_unit_f0 ORDER BY evidence_id"
            ).fetchall()
        return [EvidenceUnit.model_validate_json(row[0]) for row in rows]

    def log_evidence_event(
        self,
        run_id: str,
        evidence_id: str,
        source_id: str,
        action: str,
        status: str,
        detail: str | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO evidence_event
                (run_id,evidence_id,source_id,action,status,detail,created_at)
                VALUES(?,?,?,?,?,?,?)""",
                (
                    run_id,
                    evidence_id,
                    source_id,
                    action,
                    status,
                    detail,
                    datetime.now(timezone.utc).isoformat(),
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
