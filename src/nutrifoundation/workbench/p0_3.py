from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import secrets
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

BUILD_ID = "P03-WORKBENCH-REF-v0.1.0"
TOKENIZER_ID = "ws-token-v1"
TOKEN_RE = re.compile(r"\\S+")


class WorkbenchError(RuntimeError):
    pass


class AccessDenied(WorkbenchError):
    pass


class SourceHashMismatch(WorkbenchError):
    pass


class LockedRecordError(WorkbenchError):
    pass


class InvalidState(WorkbenchError):
    pass


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _node_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return " ".join(" ".join(node.itertext()).split())


def _http_get(url: str, retries: int = 4) -> bytes:
    last: Exception | None = None
    for i in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "NutriFoundation-P0.3-Workbench/0.1"}
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()
        except Exception as exc:  # pragma: no cover - network behavior
            last = exc
            time.sleep(min(8, 1.5 * (i + 1)))
    assert last is not None
    raise last


def fetch_worker_visible_text(record: dict[str, Any]) -> str:
    """Reconstruct exactly the P0.2.3/P0.2.4 worker-visible source text."""
    pmcid = record.get("pmcid")
    pmid = record.get("pmid")
    if pmcid:
        article: ET.Element | None = None
        try:
            raw = _http_get(
                f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML",
                retries=3,
            )
            root = ET.fromstring(raw)
            article = root if root.tag == "article" else root.find(".//article")
        except Exception:
            numeric = str(pmcid).replace("PMC", "")
            query = urllib.parse.urlencode(
                {
                    "db": "pmc",
                    "id": numeric,
                    "retmode": "xml",
                    "tool": "NutriFoundation",
                    "email": "noreply@example.invalid",
                }
            )
            root = ET.fromstring(
                _http_get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + query
                )
            )
            article = root if root.tag == "article" else root.find(".//article")
        if article is None:
            raise WorkbenchError(f"PMC full text unavailable for {pmcid}")
        parts: list[str] = []
        title = article.find(".//article-title")
        if title is not None:
            parts.append(_node_text(title))
        for abstract in article.findall(".//abstract"):
            parts.append(_node_text(abstract))
        body = article.find(".//body")
        if body is not None:
            parts.append(_node_text(body))
        return "\n\n".join(x for x in parts if x).strip()

    if not pmid:
        raise WorkbenchError("Source has neither PMCID nor PMID")
    query = urllib.parse.urlencode(
        {
            "db": "pubmed",
            "id": str(pmid),
            "retmode": "xml",
            "tool": "NutriFoundation",
            "email": "noreply@example.invalid",
        }
    )
    root = ET.fromstring(
        _http_get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + query)
    )
    article = root.find(".//PubmedArticle")
    if article is None:
        raise WorkbenchError(f"PubMed record unavailable for {pmid}")
    return " ".join(
        _node_text(x) for x in article.findall(".//Abstract/AbstractText")
    ).strip()


def tokenize(text: str) -> list[dict[str, Any]]:
    return [
        {"i": i, "text": m.group(0), "start": m.start(), "end": m.end()}
        for i, m in enumerate(TOKEN_RE.finditer(text))
    ]


def bind_span(
    text: str, source_sha256: str, start_token: int, end_token: int, supported: list[str]
) -> dict[str, Any]:
    """Bind a half-open token interval [start_token, end_token)."""
    toks = tokenize(text)
    if start_token < 0 or end_token <= start_token or end_token > len(toks):
        raise ValueError("Invalid token interval")
    start_char = toks[start_token]["start"]
    end_char = toks[end_token - 1]["end"]
    return {
        "source_text_sha256": source_sha256,
        "tokenizer_id": TOKENIZER_ID,
        "start_token": start_token,
        "end_token": end_token,
        "exact_text": text[start_char:end_char],
        "supported_object_ids": supported,
    }


class P03Workbench:
    def __init__(
        self,
        db_path: str | Path,
        calibration_records: list[dict[str, Any]],
        gold100_ids: set[str],
        source_loader: Callable[[dict[str, Any]], str] = fetch_worker_visible_text,
    ):
        self.db_path = str(db_path)
        self.records = {x["candidate_id"]: x for x in calibration_records}
        self.gold100_ids = set(gold100_ids)
        self.source_loader = source_loader
        self._sessions: dict[str, dict[str, str]] = {}
        self._session_lock = threading.Lock()
        self._init_db()

    @classmethod
    def from_repo(
        cls,
        repo_root: str | Path,
        db_path: str | Path,
        source_loader: Callable[[dict[str, Any]], str] = fetch_worker_visible_text,
    ) -> "P03Workbench":
        root = Path(repo_root)
        a = json.loads(
            (root / "runs/E0.4.3/P0.3/Calibration12A_Training_Manifest_v1.0.json").read_text()
        )["records"]
        b = json.loads(
            (root / "runs/E0.4.3/P0.3/Calibration12B_Reliability_Manifest_v1.0.json").read_text()
        )["records"]
        gold = json.loads(
            (root / "runs/E0.4.3/P0.2.4/Gold100_Source_Set_FROZEN_v1.0.json").read_text()
        )
        return cls(db_path, a + b, {x["candidate_id"] for x in gold["assignments"]}, source_loader)

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self) -> None:
        with self.connect() as con:
            con.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS source_cache(
                  candidate_id TEXT PRIMARY KEY,
                  text_content TEXT NOT NULL,
                  source_sha256 TEXT NOT NULL,
                  token_count INTEGER NOT NULL,
                  verified_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS annotation_record(
                  round TEXT NOT NULL,
                  candidate_id TEXT NOT NULL,
                  role TEXT NOT NULL,
                  pseudonym TEXT NOT NULL,
                  status TEXT NOT NULL,
                  payload_json TEXT NOT NULL,
                  record_sha256 TEXT,
                  locked_at TEXT,
                  updated_at TEXT NOT NULL,
                  PRIMARY KEY(round,candidate_id,role)
                );
                CREATE TABLE IF NOT EXISTS metric_freeze(
                  round TEXT PRIMARY KEY,
                  report_sha256 TEXT NOT NULL,
                  frozen_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_event(
                  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  created_at TEXT NOT NULL,
                  role TEXT,
                  pseudonym TEXT,
                  candidate_id TEXT,
                  event_type TEXT NOT NULL,
                  detail_json TEXT NOT NULL,
                  prev_hash TEXT,
                  event_hash TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS immutable_locked_update
                BEFORE UPDATE ON annotation_record
                WHEN OLD.status='FIRST_PASS_LOCKED'
                BEGIN
                  SELECT RAISE(ABORT,'locked annotation record is immutable');
                END;
                CREATE TRIGGER IF NOT EXISTS immutable_locked_delete
                BEFORE DELETE ON annotation_record
                WHEN OLD.status='FIRST_PASS_LOCKED'
                BEGIN
                  SELECT RAISE(ABORT,'locked annotation record is immutable');
                END;
                """
            )

    def login(self, role: str, pseudonym: str) -> str:
        if role not in {"A", "B"}:
            raise AccessDenied("Role must be A or B")
        pseudonym = pseudonym.strip()
        if not pseudonym:
            raise AccessDenied("Pseudonymous expert ID required")
        token = secrets.token_hex(24)
        with self._session_lock:
            self._sessions[token] = {"role": role, "pseudonym": pseudonym}
        self.audit("workspace_login", role=role, pseudonym=pseudonym)
        return token

    def session(self, token: str) -> dict[str, str]:
        with self._session_lock:
            s = self._sessions.get(token)
        if not s:
            raise AccessDenied("Invalid session")
        return dict(s)

    def audit(
        self,
        event_type: str,
        *,
        role: str | None = None,
        pseudonym: str | None = None,
        candidate_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> str:
        detail_json = canonical_json(detail or {})
        with self.connect() as con:
            row = con.execute(
                "SELECT event_hash FROM audit_event ORDER BY event_id DESC LIMIT 1"
            ).fetchone()
            prev = row["event_hash"] if row else ""
            created = utcnow()
            base = canonical_json(
                {
                    "created_at": created,
                    "role": role,
                    "pseudonym": pseudonym,
                    "candidate_id": candidate_id,
                    "event_type": event_type,
                    "detail": json.loads(detail_json),
                    "prev_hash": prev,
                }
            )
            event_hash = sha256_text(base)
            con.execute(
                """INSERT INTO audit_event
                (created_at,role,pseudonym,candidate_id,event_type,detail_json,prev_hash,event_hash)
                VALUES(?,?,?,?,?,?,?,?)""",
                (created, role, pseudonym, candidate_id, event_type, detail_json, prev, event_hash),
            )
        return event_hash

    def list_sources(self, round_id: str) -> list[dict[str, Any]]:
        if round_id not in {"A", "B"}:
            raise ValueError("round must be A or B")
        rows = [x for x in self.records.values() if x["round"] == round_id]
        return [
            {
                "calibration_slot_id": x["calibration_slot_id"],
                "candidate_id": x["candidate_id"],
                "pmid": x.get("pmid"),
                "title": x.get("title"),
                "source_family": x.get("source_family"),
                "domain": x.get("domain"),
                "source_text_status": x.get("source_text_status"),
            }
            for x in sorted(rows, key=lambda z: z["calibration_slot_id"])
        ]

    def _record_for_source(self, candidate_id: str) -> dict[str, Any]:
        if candidate_id in self.gold100_ids:
            self.audit("unauthorized_access_attempt", candidate_id=candidate_id, detail={"target": "Gold100"})
            raise AccessDenied("Gold100 access is prohibited in P0.3")
        record = self.records.get(candidate_id)
        if not record:
            raise AccessDenied("Source is not in Calibration24")
        return record

    def source(self, candidate_id: str, role: str | None = None, pseudonym: str | None = None) -> dict[str, Any]:
        rec = self._record_for_source(candidate_id)
        expected = rec.get("worker_visible_text_sha256")
        with self.connect() as con:
            cached = con.execute(
                "SELECT text_content,source_sha256,token_count FROM source_cache WHERE candidate_id=?",
                (candidate_id,),
            ).fetchone()
        if cached:
            if cached["source_sha256"] != expected:
                raise SourceHashMismatch("Cached source hash no longer matches manifest")
            text = cached["text_content"]
        else:
            text = self.source_loader(rec)
            actual = sha256_text(text)
            if actual != expected:
                self.audit(
                    "source_hash_mismatch",
                    role=role,
                    pseudonym=pseudonym,
                    candidate_id=candidate_id,
                    detail={"expected": expected, "actual": actual},
                )
                raise SourceHashMismatch(f"Source hash mismatch for {candidate_id}")
            toks = tokenize(text)
            with self.connect() as con:
                con.execute(
                    """INSERT OR REPLACE INTO source_cache
                    (candidate_id,text_content,source_sha256,token_count,verified_at)
                    VALUES(?,?,?,?,?)""",
                    (candidate_id, text, actual, len(toks), utcnow()),
                )
        toks = tokenize(text)
        self.audit("source_open", role=role, pseudonym=pseudonym, candidate_id=candidate_id)
        self.audit(
            "source_hash_verified",
            role=role,
            pseudonym=pseudonym,
            candidate_id=candidate_id,
            detail={"sha256": expected, "tokenizer_id": TOKENIZER_ID, "token_count": len(toks)},
        )
        return {
            "metadata": {
                k: rec.get(k)
                for k in (
                    "calibration_slot_id",
                    "round",
                    "candidate_id",
                    "pmid",
                    "pmcid",
                    "doi",
                    "title",
                    "source_family",
                    "domain",
                    "source_text_status",
                    "worker_visible_text_sha256",
                )
            },
            "tokenizer_id": TOKENIZER_ID,
            "tokens": toks,
        }

    def bind_span(
        self,
        candidate_id: str,
        start_token: int,
        end_token: int,
        supported_object_ids: list[str],
        *,
        role: str | None = None,
        pseudonym: str | None = None,
    ) -> dict[str, Any]:
        src = self.source(candidate_id, role=role, pseudonym=pseudonym)
        with self.connect() as con:
            row = con.execute(
                "SELECT text_content,source_sha256 FROM source_cache WHERE candidate_id=?",
                (candidate_id,),
            ).fetchone()
        assert row is not None
        span = bind_span(
            row["text_content"], row["source_sha256"], start_token, end_token, supported_object_ids
        )
        self.audit("span_bind", role=role, pseudonym=pseudonym, candidate_id=candidate_id, detail=span)
        return span

    def _round_for(self, candidate_id: str) -> str:
        return self._record_for_source(candidate_id)["round"]

    def save_draft(
        self, candidate_id: str, role: str, pseudonym: str, payload: dict[str, Any]
    ) -> None:
        round_id = self._round_for(candidate_id)
        if role not in {"A", "B"}:
            raise AccessDenied("Invalid annotator role")
        with self.connect() as con:
            row = con.execute(
                "SELECT status FROM annotation_record WHERE round=? AND candidate_id=? AND role=?",
                (round_id, candidate_id, role),
            ).fetchone()
            if row and row["status"] == "FIRST_PASS_LOCKED":
                raise LockedRecordError("First pass is locked")
            con.execute(
                """INSERT INTO annotation_record
                (round,candidate_id,role,pseudonym,status,payload_json,updated_at)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(round,candidate_id,role) DO UPDATE SET
                  pseudonym=excluded.pseudonym,
                  payload_json=excluded.payload_json,
                  updated_at=excluded.updated_at""",
                (round_id, candidate_id, role, pseudonym, "DRAFT", canonical_json(payload), utcnow()),
            )
        self.audit("draft_save", role=role, pseudonym=pseudonym, candidate_id=candidate_id)

    @staticmethod
    def _validate_lock_payload(payload: dict[str, Any]) -> None:
        required_science = {
            "study_identity",
            "evidence_units",
            "applicability_boundary",
            "source_spans",
            "critical_error_opportunities",
            "annotation_quality",
        }
        science = payload.get("scientific_payload")
        if not isinstance(science, dict) or not required_science.issubset(science):
            raise InvalidState("scientific_payload is incomplete")
        att = payload.get("independence_attestation")
        required_att = [
            "no_Gold100_source_access",
            "no_AB_outputs_seen",
            "no_evaluator_scores_seen",
            "no_other_annotator_first_pass_seen_before_lock",
            "no_discussion_before_lock",
            "conflict_of_interest_declared",
        ]
        if not isinstance(att, dict) or not all(att.get(x) is True for x in required_att):
            raise InvalidState("All independence/COI attestations must be true before lock")
        timing = payload.get("timing")
        if not isinstance(timing, dict) or int(timing.get("active_annotation_seconds", -1)) < 0:
            raise InvalidState("active_annotation_seconds required")

    def lock(self, candidate_id: str, role: str, pseudonym: str) -> dict[str, Any]:
        round_id = self._round_for(candidate_id)
        with self.connect() as con:
            row = con.execute(
                "SELECT payload_json,status FROM annotation_record WHERE round=? AND candidate_id=? AND role=?",
                (round_id, candidate_id, role),
            ).fetchone()
        if not row:
            raise InvalidState("No draft exists")
        if row["status"] == "FIRST_PASS_LOCKED":
            raise LockedRecordError("Already locked")
        payload = json.loads(row["payload_json"])
        self._validate_lock_payload(payload)
        rec = self._record_for_source(candidate_id)
        canonical_record = {
            "calibration_identity": {
                "calibration_slot_id": rec["calibration_slot_id"],
                "calibration_round": round_id,
                "mode": rec["mode"],
                "annotator_role": f"Calibration_Annotator_{role}",
                "annotator_pseudonymous_id": pseudonym,
            },
            "source_binding": {
                "candidate_id": candidate_id,
                "pmid": rec.get("pmid"),
                "pmcid": rec.get("pmcid"),
                "doi": rec.get("doi"),
                "exact_source_text_sha256": rec["worker_visible_text_sha256"],
                "source_text_status": rec["source_text_status"],
                "evidence_cutoff": "2026-10-03T23:26:00+08:00",
            },
            **payload,
        }
        digest = sha256_text(canonical_json(canonical_record))
        locked_at = utcnow()
        canonical_record["first_pass_lock"] = {
            "canonical_record_sha256": digest,
            "locked_at": locked_at,
            "immutable_after_lock": True,
        }
        with self.connect() as con:
            con.execute(
                """UPDATE annotation_record SET
                status='FIRST_PASS_LOCKED',payload_json=?,record_sha256=?,locked_at=?,updated_at=?
                WHERE round=? AND candidate_id=? AND role=?""",
                (
                    canonical_json(canonical_record),
                    digest,
                    locked_at,
                    locked_at,
                    round_id,
                    candidate_id,
                    role,
                ),
            )
        self.audit(
            "first_pass_lock",
            role=role,
            pseudonym=pseudonym,
            candidate_id=candidate_id,
            detail={"record_sha256": digest},
        )
        if self.pair_locked(candidate_id):
            self.audit("pair_lock", candidate_id=candidate_id, detail={"round": round_id})
        return canonical_record

    def own_record(self, candidate_id: str, role: str) -> dict[str, Any] | None:
        round_id = self._round_for(candidate_id)
        with self.connect() as con:
            row = con.execute(
                "SELECT status,payload_json,record_sha256,locked_at FROM annotation_record WHERE round=? AND candidate_id=? AND role=?",
                (round_id, candidate_id, role),
            ).fetchone()
        if not row:
            return None
        return {
            "status": row["status"],
            "payload": json.loads(row["payload_json"]),
            "record_sha256": row["record_sha256"],
            "locked_at": row["locked_at"],
        }

    def pair_locked(self, candidate_id: str) -> bool:
        round_id = self._round_for(candidate_id)
        with self.connect() as con:
            rows = con.execute(
                "SELECT role,status FROM annotation_record WHERE round=? AND candidate_id=?",
                (round_id, candidate_id),
            ).fetchall()
        locked = {r["role"] for r in rows if r["status"] == "FIRST_PASS_LOCKED"}
        return locked == {"A", "B"}

    def peer_record(self, candidate_id: str, requester_role: str) -> dict[str, Any]:
        if not self.pair_locked(candidate_id):
            self.audit(
                "unauthorized_access_attempt",
                role=requester_role,
                candidate_id=candidate_id,
                detail={"target": "peer_first_pass_before_pair_lock"},
            )
            raise AccessDenied("Peer record hidden until both first passes are locked")
        peer = "B" if requester_role == "A" else "A"
        out = self.own_record(candidate_id, peer)
        assert out is not None
        self.audit("diff_release", role=requester_role, candidate_id=candidate_id)
        return out

    def freeze_round_b_metric(self, report_sha256: str) -> None:
        if not re.fullmatch(r"[0-9a-f]{64}", report_sha256):
            raise InvalidState("report_sha256 must be 64 lowercase hex characters")
        b_ids = [x["candidate_id"] for x in self.records.values() if x["round"] == "B"]
        if not all(self.pair_locked(cid) for cid in b_ids):
            raise InvalidState("All Round B A/B first passes must be locked before metric freeze")
        with self.connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO metric_freeze(round,report_sha256,frozen_at) VALUES('B',?,?)",
                (report_sha256, utcnow()),
            )
        self.audit("metric_freeze", detail={"round": "B", "report_sha256": report_sha256})

    def metric_frozen(self, round_id: str) -> bool:
        with self.connect() as con:
            row = con.execute("SELECT 1 FROM metric_freeze WHERE round=?", (round_id,)).fetchone()
        return bool(row)

    def discussion_allowed(self, candidate_id: str) -> bool:
        round_id = self._round_for(candidate_id)
        if not self.pair_locked(candidate_id):
            return False
        return round_id == "A" or (round_id == "B" and self.metric_frozen("B"))

    def export_record(self, candidate_id: str, role: str) -> dict[str, Any]:
        own = self.own_record(candidate_id, role)
        if own is None:
            raise InvalidState("No record")
        with self.connect() as con:
            events = [
                {
                    "event_id": r["event_id"],
                    "created_at": r["created_at"],
                    "role": r["role"],
                    "pseudonym": r["pseudonym"],
                    "candidate_id": r["candidate_id"],
                    "event_type": r["event_type"],
                    "detail": json.loads(r["detail_json"]),
                    "prev_hash": r["prev_hash"],
                    "event_hash": r["event_hash"],
                }
                for r in con.execute(
                    "SELECT * FROM audit_event WHERE candidate_id=? OR candidate_id IS NULL ORDER BY event_id",
                    (candidate_id,),
                ).fetchall()
            ]
        self.audit("export", role=role, candidate_id=candidate_id)
        return {
            "build_id": BUILD_ID,
            "tokenizer_id": TOKENIZER_ID,
            "record": own,
            "audit_events": events,
        }

    def verify_audit_chain(self) -> bool:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM audit_event ORDER BY event_id").fetchall()
        prev = ""
        for row in rows:
            base = canonical_json(
                {
                    "created_at": row["created_at"],
                    "role": row["role"],
                    "pseudonym": row["pseudonym"],
                    "candidate_id": row["candidate_id"],
                    "event_type": row["event_type"],
                    "detail": json.loads(row["detail_json"]),
                    "prev_hash": prev,
                }
            )
            if row["prev_hash"] != prev or row["event_hash"] != sha256_text(base):
                return False
            prev = row["event_hash"]
        return True


def _json_response(handler: BaseHTTPRequestHandler, status: int, obj: Any) -> None:
    data = json.dumps(obj, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class WorkbenchHTTPHandler(BaseHTTPRequestHandler):
    server_version = BUILD_ID

    @property
    def app(self) -> P03Workbench:
        return self.server.app  # type: ignore[attr-defined]

    @property
    def repo_root(self) -> Path:
        return self.server.repo_root  # type: ignore[attr-defined]

    def _body(self) -> dict[str, Any]:
        n = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(n) or b"{}")

    def _session(self) -> dict[str, str]:
        return self.app.session(self.headers.get("X-Workbench-Token", ""))

    def do_GET(self) -> None:
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            q = urllib.parse.parse_qs(parsed.query)
            if path == "/":
                data = (self.repo_root / "paper_c/P0.3/workbench/index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            s = self._session()
            if path == "/api/sources":
                _json_response(self, 200, self.app.list_sources(q.get("round", ["A"])[0]))
                return
            if path.startswith("/api/source/"):
                cid = path.rsplit("/", 1)[-1]
                _json_response(self, 200, self.app.source(cid, **s))
                return
            if path.startswith("/api/record/"):
                cid = path.rsplit("/", 1)[-1]
                _json_response(self, 200, self.app.own_record(cid, s["role"]))
                return
            if path.startswith("/api/peer/"):
                cid = path.rsplit("/", 1)[-1]
                _json_response(self, 200, self.app.peer_record(cid, s["role"]))
                return
            if path.startswith("/api/discussion/"):
                cid = path.rsplit("/", 1)[-1]
                _json_response(self, 200, {"allowed": self.app.discussion_allowed(cid)})
                return
            if path.startswith("/api/export/"):
                cid = path.rsplit("/", 1)[-1]
                _json_response(self, 200, self.app.export_record(cid, s["role"]))
                return
            _json_response(self, 404, {"error": "not_found"})
        except AccessDenied as exc:
            _json_response(self, 403, {"error": str(exc)})
        except SourceHashMismatch as exc:
            _json_response(self, 409, {"error": str(exc)})
        except Exception as exc:
            _json_response(self, 400, {"error": f"{type(exc).__name__}: {exc}"})

    def do_POST(self) -> None:
        try:
            path = urllib.parse.urlparse(self.path).path
            body = self._body()
            if path == "/api/login":
                token = self.app.login(body.get("role", ""), body.get("pseudonym", ""))
                _json_response(self, 200, {"token": token, "build_id": BUILD_ID})
                return
            s = self._session()
            if path.startswith("/api/record/") and path.endswith("/lock"):
                cid = path.split("/")[-2]
                _json_response(self, 200, self.app.lock(cid, s["role"], s["pseudonym"]))
                return
            if path.startswith("/api/record/"):
                cid = path.rsplit("/", 1)[-1]
                self.app.save_draft(cid, s["role"], s["pseudonym"], body)
                _json_response(self, 200, {"status": "saved"})
                return
            if path.startswith("/api/span/"):
                cid = path.rsplit("/", 1)[-1]
                span = self.app.bind_span(
                    cid,
                    int(body["start_token"]),
                    int(body["end_token"]),
                    list(body.get("supported_object_ids", [])),
                    **s,
                )
                _json_response(self, 200, span)
                return
            if path == "/api/metric-freeze":
                self.app.freeze_round_b_metric(body["report_sha256"])
                _json_response(self, 200, {"status": "METRIC_FROZEN"})
                return
            _json_response(self, 404, {"error": "not_found"})
        except AccessDenied as exc:
            _json_response(self, 403, {"error": str(exc)})
        except (InvalidState, LockedRecordError, SourceHashMismatch, ValueError) as exc:
            _json_response(self, 409, {"error": str(exc)})
        except Exception as exc:
            _json_response(self, 400, {"error": f"{type(exc).__name__}: {exc}"})

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def serve(repo_root: str | Path, db_path: str | Path, host: str, port: int) -> None:
    app = P03Workbench.from_repo(repo_root, db_path)
    server = ThreadingHTTPServer((host, port), WorkbenchHTTPHandler)
    server.app = app  # type: ignore[attr-defined]
    server.repo_root = Path(repo_root)  # type: ignore[attr-defined]
    print(f"{BUILD_ID} listening on http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    ap = argparse.ArgumentParser(description="Paper C P0.3 local expert annotation workbench")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--db", default="runs/E0.4.3/P0.3/workbench.sqlite3")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    serve(args.repo_root, args.db, args.host, args.port)


if __name__ == "__main__":
    main()
