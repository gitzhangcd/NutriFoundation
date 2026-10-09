"""Isolated WB-EA-P1 synthetic-only API. Not mounted into existing D0/NDS."""
from __future__ import annotations

import argparse
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from core import EAError, EvidenceEngine


HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / "ea_p0" / "specs" / "annotation_contract.v0.1.json"


class SourceRequest(BaseModel):
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


class TaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: str
    task_kind: str
    profile_id: str
    primary_source: dict
    allowed_source_versions: list[dict]
    knowledge_cutoff: str
    workflow_strategy: str
    expert_actor: str


class CandidatesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[dict]


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[dict]
    candidate_set_digest: str | None = None


def make_app(db_path: Path, *, allow_synthetic: bool = False):
    if allow_synthetic is not True:
        raise RuntimeError("EA_P1_SYNTHETIC_ONLY_EXPLICIT_OPT_IN_REQUIRED")
    app = FastAPI(title="WB-EA-P1 isolated synthetic annotation", docs_url=None,
                  redoc_url=None, openapi_url=None)
    engine = EvidenceEngine(db_path, MANIFEST)
    app.state.engine = engine
    # Generated per-process, operator distributed via private local CLI only.
    roles = {
        "producer": ("SYN-PRODUCER-1", "producer"),
        "expert": ("SYN-EXPERT-A", "expert"),
        "expert_b": ("SYN-EXPERT-B", "expert"),
        "auditor": ("SYN-AUDITOR", "auditor"),
    }
    app.state.tokens = {key: secrets.token_urlsafe(32) for key in roles}

    def principal(x_ea_token: str | None = Header(default=None)):
        if not x_ea_token:
            raise HTTPException(status_code=401, detail="UNAUTHENTICATED")
        for key, token in app.state.tokens.items():
            if secrets.compare_digest(x_ea_token, token):
                return roles[key]
        raise HTTPException(status_code=401, detail="UNAUTHENTICATED")

    @app.exception_handler(EAError)
    async def validation_error(request: Request, exc: EAError):
        if exc.code in ("ROLE_FORBIDDEN", "TASK_NOT_ASSIGNED", "DENY_SOURCE_NOT_ALLOWED",
                        "DENY_INDEPENDENT_AGENT_EXPOSURE", "DENY_EXPOSURE"):
            status = 403
        elif exc.code in ("TASK_NOT_FOUND", "SOURCE_VERSION_NOT_FOUND"):
            status = 404
        else:
            status = 409
        return JSONResponse(status_code=status, content={"detail": exc.code},
                            headers={"Cache-Control": "no-store"})

    @app.middleware("http")
    async def isolate(request: Request, call_next):
        # The server must bind loopback; no reverse proxy / public access approved.
        host = request.headers.get("host", "").split(":", 1)[0].lower()
        if host not in ("127.0.0.1", "localhost", "testserver"):
            return JSONResponse({"detail": "LOOPBACK_ONLY"}, status_code=403)
        if request.method not in ("GET", "HEAD", "OPTIONS") and request.url.path != "/":
            origin = request.headers.get("origin")
            if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
                return JSONResponse({"detail": "ORIGIN_MISMATCH"}, status_code=403)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; style-src 'self'; script-src 'self'; "
            "connect-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'"
        )
        return response

    @app.get("/health")
    def health():
        return {"stage": "WB-EA-P1", "mode": "SYNTHETIC_ENGINEERING_ONLY",
                "scientific_capture": False, "real_expert": "NO_GO", "gold": "NOT_QUALIFIED"}

    @app.get("/")
    def index():
        return FileResponse(HERE / "web" / "index.html")

    @app.get("/static/ea_p1.js")
    def script():
        return FileResponse(HERE / "web" / "ea_p1.js", media_type="text/javascript")

    @app.get("/static/ea_p1.css")
    def stylesheet():
        return FileResponse(HERE / "web" / "ea_p1.css", media_type="text/css")

    @app.get("/v1/ea/profiles")
    def profiles(p=Depends(principal)):
        return {"profiles": engine.contract["profiles"],
                "status": "PROPOSED_PROFILE_EXECUTION_SYNTHETIC_ONLY"}

    @app.post("/v1/ea/sources")
    def add_source(payload: SourceRequest, p=Depends(principal)):
        return engine.register_source(actor=p[0], role=p[1], source=payload.model_dump())

    @app.post("/v1/ea/tasks")
    def create_task(payload: TaskRequest, p=Depends(principal)):
        return engine.create_task(actor=p[0], role=p[1], task=payload.model_dump())

    @app.get("/v1/ea/tasks")
    def tasks(p=Depends(principal)):
        with engine.connect() as db:
            from json import loads
            out = []
            for row in db.execute("SELECT task_id,record,state FROM tasks ORDER BY task_id"):
                task = loads(row["record"])
                try:
                    engine._access(task, *p)
                except EAError:
                    continue
                if p[1] == "auditor" or p[1] == "expert" or p[1] == "producer":
                    out.append({"task_id": task["task_id"], "profile_id": task["profile_id"],
                                "state": row["state"], "workflow": task["workflow_strategy"]})
        return {"tasks": out}

    @app.get("/v1/ea/tasks/{task_id}/workpack")
    def workpack(task_id: str, p=Depends(principal)):
        return engine.workpack(actor=p[0], role=p[1], task_id=task_id)

    @app.get("/v1/ea/tasks/{task_id}/sources")
    def sources(task_id: str, p=Depends(principal)):
        return engine.list_sources(actor=p[0], role=p[1], task_id=task_id)

    @app.get("/v1/ea/tasks/{task_id}/sources/{source_id}/{revision_id}")
    def read_source(task_id: str, source_id: str, revision_id: str, p=Depends(principal)):
        return engine.read_source(actor=p[0], role=p[1], task_id=task_id,
                                  source_id=source_id, revision_id=revision_id)

    @app.post("/v1/ea/tasks/{task_id}/candidates/freeze")
    def freeze_candidates(task_id: str, request: CandidatesRequest, p=Depends(principal)):
        return engine.freeze_candidates(actor=p[0], role=p[1], task_id=task_id,
                                        items=request.items)

    @app.get("/v1/ea/tasks/{task_id}/candidates")
    def candidates(task_id: str, p=Depends(principal)):
        return engine.read_candidates(actor=p[0], role=p[1], task_id=task_id)

    @app.post("/v1/ea/tasks/{task_id}/review/freeze")
    def freeze_review(task_id: str, request: ReviewRequest, p=Depends(principal)):
        return engine.freeze_review(actor=p[0], role=p[1], task_id=task_id,
                                    items=request.items,
                                    candidate_set_digest=request.candidate_set_digest)

    @app.get("/v1/ea/tasks/{task_id}/export")
    def export(task_id: str, p=Depends(principal)):
        return engine.export_record(actor=p[0], role=p[1], task_id=task_id)

    @app.get("/v1/ea/audit")
    def audit(p=Depends(principal)):
        return engine.audit(actor=p[0], role=p[1])

    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8795)
    parser.add_argument("--allow-synthetic-execution", action="store_true")
    args = parser.parse_args()
    if not args.allow_synthetic_execution:
        raise SystemExit("Explicit --allow-synthetic-execution required")
    app = make_app(args.db, allow_synthetic=True)
    for role, token in app.state.tokens.items():
        print(f"LOCAL ENGINEERING TOKEN {role}: {token}", flush=True)
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
