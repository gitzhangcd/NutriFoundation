"""Synthetic-only Project/Batch routes inside original D0 cookie+Origin+CSRF perimeter."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, ValidationError

from tpa_runtime import TPAError
from tpa_adapter import Draft


class StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectCreate(StrictBody):
    project_id: str
    name: str
    description: str = ""
    idempotency_key: str


class BatchCreate(StrictBody):
    batch_id: str
    label: str
    purpose: str = ""
    idempotency_key: str


class InBatchDraft(Draft):
    project_id: str
    batch_id: str
    idempotency_key: str


def install_project_routes(app: FastAPI, operations):
    def principal(req: Request, write=False):
        p = getattr(req.state, "principal", None)
        if p is None:
            raise HTTPException(401, detail={"code": "UNAUTHENTICATED"})
        if p["role"] not in (("producer",) if write else ("producer", "manager")) or p["actor"].startswith("SYN-EA-"):
            raise HTTPException(403, detail={"code": "ROLE_FORBIDDEN"})
        return p

    def invoke(fn, **kwargs):
        try:
            return fn(**kwargs)
        except TPAError as exc:
            code = exc.code
            status = (403 if code == "ROLE_FORBIDDEN" else
                      404 if code in ("PROJECT_NOT_FOUND", "BATCH_NOT_FOUND_OR_SCOPE_MISMATCH", "TASK_NOT_FOUND") else
                      422 if code.startswith("INVALID_") or code == "PROJECT_SCOPE_REQUIRED_FOR_BATCH" else 409)
            raise HTTPException(status, detail={"code": code}) from exc

    def body(cls, payload):
        try:
            return cls.model_validate(payload).model_dump()
        except (ValidationError, TypeError, ValueError) as exc:
            raise HTTPException(422, detail={"code": "INVALID_TPA_OPS_REQUEST"}) from exc

    @app.get("/v1/tpa/projects")
    def projects(request: Request, limit: int = 50, offset: int = 0):
        p = principal(request)
        return invoke(operations.list_projects, role=p["role"], limit=limit, offset=offset)

    @app.post("/v1/tpa/projects")
    def create_project(request: Request, payload: dict):
        p = principal(request, True)
        return invoke(operations.create_project, role=p["role"], actor=p["actor"], body=body(ProjectCreate, payload))

    @app.get("/v1/tpa/projects/{project_id}")
    def project(request: Request, project_id: str):
        p = principal(request)
        return invoke(operations.project, role=p["role"], project_id=project_id)

    @app.get("/v1/tpa/projects/{project_id}/batches")
    def batches(request: Request, project_id: str):
        p = principal(request)
        return invoke(operations.batches, role=p["role"], project_id=project_id)

    @app.post("/v1/tpa/projects/{project_id}/batches")
    def create_batch(request: Request, project_id: str, payload: dict):
        p = principal(request, True)
        return invoke(operations.create_batch, role=p["role"], actor=p["actor"],
                      project_id=project_id, body=body(BatchCreate, payload))

    @app.get("/v1/tpa/projects/{project_id}/batches/{batch_id}")
    def batch(request: Request, project_id: str, batch_id: str):
        p = principal(request)
        return invoke(operations.batch, role=p["role"], project_id=project_id, batch_id=batch_id)

    @app.post("/v1/tpa/tasks/in-batch")
    def create_in_batch(request: Request, payload: dict):
        p = principal(request, True)
        return invoke(operations.create_task_in_batch, role=p["role"], actor=p["actor"],
                      body=body(InBatchDraft, payload))

    @app.get("/v1/tpa/tasks/{task_id}/management")
    def detail(request: Request, task_id: str):
        p = principal(request)
        return invoke(operations.detail, role=p["role"], task_id=task_id)

    @app.get("/v1/tpa/overview")
    def overview(request: Request, project_id: str | None = None, batch_id: str | None = None):
        p = principal(request)
        return invoke(operations.overview, role=p["role"], project_id=project_id, batch_id=batch_id)