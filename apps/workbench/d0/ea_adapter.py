"""Additive WB-EA-P1 routes inside the ORIGINAL D0 FastAPI cookie/session gate.

Existing /v1/tasks, /v1/profile, NDS arms R0/R1/R2 and C2.1 secure_reader
are unchanged. No separate auth, port, static app or uncontrolled source route.
All content is internally generated synthetic text; no scientific capture / Gold.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from ea_runtime import EAError, EvidenceEngine


class CandidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[dict]


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[dict]
    candidate_set_digest: str | None = None


class NewTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: str
    task_kind: str
    profile_id: str
    primary_source: dict
    allowed_source_versions: list[dict]
    knowledge_cutoff: str
    workflow_strategy: str
    expert_actor: str


class NewSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: str
    revision_id: str
    source_type: str
    title: str
    available_at: str
    fetched_at: str
    rights_status: str
    units: list[dict]
    source_family_refs: list[str] = Field(default_factory=list)


def install_evidence_routes(app: FastAPI, engine: EvidenceEngine):
    def auth(request: Request):
        # D0's existing cookie/CSRF middleware already authenticated this.
        p = getattr(request.state, "principal", None)
        if p is None:
            raise HTTPException(401, detail={"code": "UNAUTHENTICATED"})
        return {"actor": p["actor"], "role": p["role"]}

    def task_reader(request: Request):
        p = auth(request)
        # Preserve original D0 role surface: auditor receives audit, never source.
        if p["role"] not in ("expert", "producer") or (
            p["role"] == "expert" and not p["actor"].startswith("SYN-EA-")
        ):
            raise HTTPException(403, detail={"code": "ROLE_FORBIDDEN"})
        return p

    def perform(func, **kwargs):
        try:
            return func(**kwargs)
        except EAError as exc:
            code = exc.code
            if code in ("ROLE_FORBIDDEN", "TASK_NOT_ASSIGNED", "DENY_SOURCE_NOT_ALLOWED",
                        "DENY_INDEPENDENT_AGENT_EXPOSURE"):
                status = 403
            elif code in ("TASK_NOT_FOUND", "SOURCE_VERSION_NOT_FOUND"):
                status = 404
            else:
                status = 409
            raise HTTPException(status, detail={"code": code}) from exc

    @app.get("/v1/ea/status")
    def ea_status(request: Request):
        auth(request)
        return {"status": "D0_INTEGRATED_SYNTHETIC_ONLY",
                "origin": "54b4c2eba844f39c07575573a3e834e0bc00c261",
                "scientific_capture": False, "gold_qualification": "NOT_ELIGIBLE",
                "reader_pdf": "NOT_IN_EA_P1_STRUCTURED_FIXTURE"}

    @app.get("/v1/ea/profiles")
    def profiles(request: Request):
        auth(request)
        return {"profiles": engine.contract["profiles"],
                "status": "P0_PROPOSED_SYNTHETIC_PROFILES"}

    @app.get("/v1/ea/tasks")
    def list_tasks(request: Request):
        p = auth(request)
        if p["role"] not in ("expert", "producer") or (
            p["role"] == "expert" and not p["actor"].startswith("SYN-EA-")
        ):
            raise HTTPException(403, detail={"code": "ROLE_FORBIDDEN"})
        with engine.connect() as db:
            rows = db.execute("SELECT task_id,record,state FROM tasks ORDER BY task_id")
            import json
            out = []
            for r in rows:
                t = json.loads(r["record"])
                if p["role"] == "expert" and t["expert_actor"] != p["actor"]:
                    continue
                if p["role"] == "producer" and t["producer_actor"] != p["actor"]:
                    continue
                out.append({"task_id": r["task_id"], "state": r["state"],
                            "profile_id": t["profile_id"], "source_type": t["source_type"],
                            "workflow": t["workflow_strategy"]})
            return {"tasks": out, "scientific_capture": False}

    @app.get("/v1/ea/tasks/{task_id}/workpack")
    def workpack(task_id: str, request: Request):
        return perform(engine.workpack, **task_reader(request), task_id=task_id)

    @app.get("/v1/ea/tasks/{task_id}/sources")
    def sources(task_id: str, request: Request):
        return perform(engine.list_sources, **task_reader(request), task_id=task_id)

    @app.get("/v1/ea/tasks/{task_id}/sources/{source_id}/{revision_id}")
    def read_source(task_id: str, source_id: str, revision_id: str, request: Request):
        return perform(engine.read_source, **task_reader(request), task_id=task_id,
                       source_id=source_id, revision_id=revision_id)

    @app.get("/v1/ea/tasks/{task_id}/candidates")
    def candidates(task_id: str, request: Request):
        return perform(engine.read_candidates, **task_reader(request), task_id=task_id)

    @app.post("/v1/ea/tasks/{task_id}/candidates/freeze")
    def freeze_candidates(task_id: str, request: Request, body: CandidateRequest):
        return perform(engine.freeze_candidates, **task_reader(request), task_id=task_id,
                       items=body.items)

    @app.post("/v1/ea/tasks/{task_id}/review/freeze")
    def freeze_review(task_id: str, request: Request, body: ReviewRequest):
        return perform(engine.freeze_review, **task_reader(request), task_id=task_id,
                       items=body.items, candidate_set_digest=body.candidate_set_digest)

    @app.get("/v1/ea/tasks/{task_id}/export")
    def export(task_id: str, request: Request):
        return perform(engine.export_record, **task_reader(request), task_id=task_id)

    @app.post("/v1/ea/sources")
    def add_source(body: NewSource, request: Request):
        return perform(engine.register_source, **task_reader(request), source=body.model_dump())

    @app.post("/v1/ea/tasks")
    def add_task(body: NewTask, request: Request):
        return perform(engine.create_task, **task_reader(request), task=body.model_dump())

    @app.get("/v1/ea/audit")
    def audit(request: Request):
        return perform(engine.audit, **auth(request))
