"""G1-Shared isolated engineering-only, task-scoped source and independent reviewer adapter.

This is NOT an enrollment system or an expert Gold adjudicator. It is intentionally
separate from the existing NDS-R1 decision workflow and its blinded evaluations.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

SOURCE_PATTERN = re.compile(r"^CAND-G100-\d{3}$")
SRC_ROOT = Path("paper_c/P0/g1_shared_p0_1")
PACK_PATH = SRC_ROOT / "P0_1_A_FirstFive_Typed_Source_TaskPack_v0.1.json"
BLIND_PATH = SRC_ROOT / "P0_1_A_1_Blind_Expert_L4_Independent_Review_Packets_v0.1.json"
ROLE_SLOTS = {"SYN-EXPERT-A": "A", "SYN-EXPERT-B": "B"}
ALLOWED_ORIGINAL_HOST = "https://pmc.ncbi.nlm.nih.gov/articles/"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Draft(StrictModel):
    expected_revision: int = Field(ge=0)
    answers: dict[str, str] = Field(default_factory=dict)


class Freeze(StrictModel):
    expected_revision: int = Field(ge=0)


def _fail(code: str, status: int = 403):
    raise HTTPException(status_code=status, detail={"code": code})


def _digest(data: object) -> str:
    body = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _principal(request: Request) -> tuple[str, str]:
    principal = getattr(request.state, "principal", None)
    if not isinstance(principal, dict):
        _fail("G1_AUTH_REQUIRED", 401)
    return str(principal.get("actor", "")), str(principal.get("role", ""))


def _field_spec(item: dict) -> dict:
    # Strict allow-list: never read from the team-side typed pack's answer/Agent fields.
    return {
        "field_id": item["field_id"],
        "prompt_cn": item["prompt_cn"],
        "required": bool(item.get("required")),
        "answer_type": item.get("answer_type", "text"),
        "must_anchor": bool(item.get("must_anchor")),
    }


def install_g1_source_pilot(app, repo_root: Path, runtime_root: Path) -> None:
    """Mount only by explicit --enable-g1-pilot-engineering opt-in from D0."""
    canonical_repo = Path(repo_root).resolve(strict=True)
    pack = json.loads((canonical_repo / PACK_PATH).read_text(encoding="utf-8"))
    blind = json.loads((canonical_repo / BLIND_PATH).read_text(encoding="utf-8"))
    if pack.get("source_count") != 5 or blind.get("created_assignments") != 10:
        raise RuntimeError("G1_SOURCE_CONTRACT_MISMATCH")
    typed = {x["source_candidate_ref"]: x for x in pack["records"]}
    forms: dict[tuple[str, str], dict] = {}
    for x in blind["assignments"]:
        sid, slot = x["candidate_ref"], x["reviewer_slot"]
        if sid not in typed or slot not in ("A", "B") or (sid, slot) in forms:
            raise RuntimeError("G1_INVALID_BLIND_ASSIGNMENT")
        forms[(sid, slot)] = x
    if len(typed) != 5 or len(forms) != 10:
        raise RuntimeError("G1_SOURCE_ASSIGNMENT_COUNT_MISMATCH")

    root = Path(runtime_root).resolve() / "g1_engineering_pilot"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    db_path = root / "reviews.sqlite"

    def connect():
        db = sqlite3.connect(str(db_path), timeout=8, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=8000")
        return db

    with connect() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""CREATE TABLE IF NOT EXISTS independent_review(
            candidate TEXT NOT NULL,
            reviewer TEXT NOT NULL,
            revision INTEGER NOT NULL DEFAULT 0,
            answers TEXT NOT NULL DEFAULT '{}',
            frozen INTEGER NOT NULL DEFAULT 0,
            freeze_digest TEXT,
            PRIMARY KEY (candidate, reviewer)
        )""")
    pilot = APIRouter(prefix="/v1/g1/pilot", tags=["G1 Engineering Only"])

    def expert(request: Request) -> str:
        actor, role = _principal(request)
        if role != "expert" or actor not in ROLE_SLOTS:
            _fail("G1_EXPERT_ONLY")
        return ROLE_SLOTS[actor]

    def eligible(candidate: str, slot: str) -> dict:
        if not SOURCE_PATTERN.fullmatch(candidate) or (candidate, slot) not in forms:
            _fail("G1_NOT_ASSIGNED_OR_SOURCE_UNKNOWN", 404)
        return forms[(candidate, slot)]

    def task_public(candidate: str, slot: str):
        raw = eligible(candidate, slot)
        fields = [_field_spec(x) for x in raw["fields"]]
        link = typed[candidate]["authoritative_links"]["uri"]
        if not isinstance(link, str) or not link.startswith(ALLOWED_ORIGINAL_HOST):
            raise RuntimeError("G1_ORIGINAL_URL_CONTRACT_ERROR")
        return {
            "candidate_id": candidate,
            "role": raw["source"]["source_type"],
            "question": raw["question"],
            "original_source_uri": link,
            "source_pmid": raw["source"]["PMID"],
            "source_pmcid": raw["source"]["PMCID"],
            "fields": fields,
            "agent_candidates_visible": False,
            "source_use": "G1_ENGINEERING_NON_GOLD",
        }

    def state(candidate: str, slot: str):
        with connect() as db:
            row = db.execute(
                "SELECT * FROM independent_review WHERE candidate=? AND reviewer=?",
                (candidate, slot),
            ).fetchone()
        if row is None:
            return {"revision": 0, "answers": {}, "frozen": False, "freeze_digest": None}
        return {
            "revision": row["revision"],
            "answers": json.loads(row["answers"]),
            "frozen": bool(row["frozen"]),
            "freeze_digest": row["freeze_digest"],
        }

    @pilot.get("/health")
    def health(request: Request):
        actor, role = _principal(request)
        if role not in ("expert", "manager", "auditor"):
            _fail("G1_PILOT_UNAUTHORIZED")
        return {
            "status": "ENGINEERING_ONLY",
            "real_expert_enrollment": "DISABLED",
            "gold_freeze": "DISABLED",
            "source_count": 5,
            "session_role": role,
        }

    @pilot.get("/tasks")
    def tasks(request: Request):
        slot = expert(request)
        return {"items": [task_public(sid, slot) for sid in sorted(typed)]}

    @pilot.get("/tasks/{candidate}/source")
    def source(candidate: str, request: Request):
        slot = expert(request)
        t = task_public(candidate, slot)
        # Source text is never fetched from arbitrary URLs or paths.
        # Only the explicitly CC-BY source already approved in public repo
        # is eligible for internal body delivery in this engineering adapter.
        if candidate != "CAND-G100-004":
            return {
                **t,
                "source_body": None,
                "availability": "EXTERNAL_LINK_ONLY",
                "original_pdf_parity": "NOT_VERIFIED",
                "reason": "NO_APPROVED_LOCAL_SOURCE_PROJECTION",
            }
        relative = typed[candidate]["authoritative_links"].get("source_projection")
        if relative != "paper_c/P0/g1_shared_p0_1/source_projections/CAND-G100-004_PMC8864028_PMC_body_CC-BY-4.0.md":
            _fail("G1_PROJECTION_NOT_ALLOWLISTED", 409)
        path = (canonical_repo / relative).resolve(strict=True)
        if not path.is_relative_to(canonical_repo):
            _fail("G1_SOURCE_PATH_ESCAPES_REPO", 409)
        projection = path.read_text(encoding="utf-8")
        raw_bytes = projection.encode("utf-8")
        git_blob = hashlib.sha1(b"blob " + str(len(raw_bytes)).encode("ascii") + b"\0" + raw_bytes).hexdigest()
        if git_blob != "bf58378d849ab4a780aa752a0fa4e78c951d28ac":
            _fail("G1_PINNED_SOURCE_BLOB_MISMATCH", 409)
        delimiter = "## PMC article-body text projection\n\n"
        if projection.count(delimiter) != 1:
            _fail("G1_SOURCE_BODY_FORMAT_MISMATCH", 409)
        body = projection.split(delimiter, 1)[1].rstrip("\n")
        expected = typed[candidate]["provenance"]["retrieved_body_chars"]
        if len(body) != expected:
            _fail("G1_SOURCE_BODY_INTEGRITY_FAILED", 409)
        return {
            **t,
            "source_body": body,
            "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "availability": "LICENSED_PMC_TEXT_BODY_ONLY",
            "original_pdf_parity": "NOT_VERIFIED",
            "translation": None,
            "scientific_gold": False,
        }

    @pilot.get("/tasks/{candidate}/review")
    def read_review(candidate: str, request: Request):
        slot = expert(request)
        eligible(candidate, slot)
        return {"candidate_id": candidate, "reviewer_slot": slot, **state(candidate, slot)}

    @pilot.put("/tasks/{candidate}/review")
    def write_review(candidate: str, data: Draft, request: Request):
        slot = expert(request)
        template = eligible(candidate, slot)
        allowed = {field["field_id"] for field in template["fields"]}
        if len(data.answers) > len(allowed) or not set(data.answers).issubset(allowed):
            _fail("G1_UNDECLARED_EXPERT_FIELD", 422)
        if any(not isinstance(v, str) or len(v) > 5000 for v in data.answers.values()):
            _fail("G1_INVALID_EXPERT_RESPONSE", 422)
        serial = json.dumps(data.answers, ensure_ascii=False, sort_keys=True)
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT revision, frozen FROM independent_review WHERE candidate=? AND reviewer=?",
                (candidate, slot),
            ).fetchone()
            revision = row["revision"] if row else 0
            if row and row["frozen"]:
                db.execute("ROLLBACK")
                _fail("G1_IMMUTABLE_REVIEW", 409)
            if revision != data.expected_revision:
                db.execute("ROLLBACK")
                _fail("G1_STALE_REVISION", 409)
            db.execute(
                """INSERT INTO independent_review(candidate, reviewer, revision, answers)
                   VALUES (?, ?, 1, ?)
                   ON CONFLICT(candidate,reviewer)
                   DO UPDATE SET revision=excluded.revision,
                                 answers=excluded.answers""",
                (candidate, slot, serial),
            ) if not row else db.execute(
                "UPDATE independent_review SET revision=revision+1, answers=? "
                "WHERE candidate=? AND reviewer=?",
                (serial, candidate, slot),
            )
            db.execute("COMMIT")
        return {"candidate_id": candidate, "reviewer_slot": slot, "revision": revision + 1}

    @pilot.post("/tasks/{candidate}/freeze")
    def freeze(candidate: str, data: Freeze, request: Request):
        slot = expert(request)
        eligible(candidate, slot)
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT revision, frozen, answers FROM independent_review "
                "WHERE candidate=? AND reviewer=?",
                (candidate, slot),
            ).fetchone()
            if not row or row["frozen"] or row["revision"] != data.expected_revision:
                db.execute("ROLLBACK")
                _fail("G1_FREEZE_STATE_INVALID", 409)
            answers = json.loads(row["answers"])
            required = {x["field_id"] for x in forms[(candidate, slot)]["fields"] if x.get("required")}
            if not required.issubset({k for k, v in answers.items() if v.strip()}):
                db.execute("ROLLBACK")
                _fail("G1_REQUIRED_FIELDS_INCOMPLETE", 422)
            digest = _digest({
                "candidate_id": candidate, "slot": slot,
                "revision": row["revision"], "answers": answers,
                "state": "ENGINEERING_REVIEW_FROZEN_NOT_GOLD",
            })
            db.execute(
                "UPDATE independent_review SET frozen=1, freeze_digest=? "
                "WHERE candidate=? AND reviewer=?",
                (digest, candidate, slot),
            )
            db.execute("COMMIT")
        return {
            "state": "ENGINEERING_REVIEW_FROZEN_NOT_GOLD",
            "freeze_digest": digest, "scientific_l4_gold": False,
        }

    @pilot.get("/audit/status")
    def status(request: Request):
        _actor, role = _principal(request)
        if role != "manager":
            _fail("G1_MANAGER_ONLY")
        with connect() as db:
            rows = db.execute(
                "SELECT candidate, reviewer, frozen, revision FROM independent_review"
            ).fetchall()
        return {
            "stage": "G1-P0.1-A.2",
            "engineering_review_count": len(rows),
            "engineering_frozen_count": sum(bool(r["frozen"]) for r in rows),
            "scientific_l4_gold_count": 0,
            # Deliberately no source text, private reviewer draft, or agent outputs.
        }

    app.include_router(pilot)
