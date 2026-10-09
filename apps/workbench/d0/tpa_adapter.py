"""WB-TPA-P1 manager/producer routes; original D0 session/Origin/CSRF guard owns access."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, ValidationError

from tpa_runtime import TPAError, TaskProduction
from ea_runtime import EAError


class StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ImportCheck(StrictBody):
    import_kind: str
    source_id: str
    revision_id: str
    canonical_document_sha256: str


class Draft(StrictBody):
    task_id: str
    task_kind: str
    primary_source: dict
    allowed_source_versions: list[dict]
    profile_id: str
    knowledge_cutoff: str
    workflow_strategy: str


class BatchDraft(StrictBody):
    batch_id: str
    idempotency_key: str
    items: list[Draft]


class Assignment(StrictBody):
    expert_actor: str
    idempotency_key: str


class Publish(StrictBody):
    idempotency_key: str


def install_tpa_routes(app: FastAPI, controller: TaskProduction):
    def validate_body(cls, value):
        try:
            return cls.model_validate(value).model_dump()
        except (ValidationError,TypeError,ValueError) as exc:
            raise HTTPException(422,detail={"code":"INVALID_TPA_REQUEST"}) from exc

    def person(request, allowed):
        p = getattr(request.state, "principal", None)
        if p is None:
            raise HTTPException(401, detail={"code":"UNAUTHENTICATED"})
        if p["role"] not in allowed:
            raise HTTPException(403, detail={"code":"ROLE_FORBIDDEN"})
        # Manager/producer accounts may not be synthetic EA experts.
        if p["actor"].startswith("SYN-EA-"):
            raise HTTPException(403, detail={"code":"CROSS_PROGRAM_EXPOSURE"})
        return p

    def call(fn, **kwargs):
        try:
            return fn(**kwargs)
        except (TPAError, EAError) as ex:
            deny_codes=("ROLE_FORBIDDEN","NDS_SOURCE_OF_TRUTH_ONLY",
                        "TASK_NOT_DELIVERED_OR_ASSIGNED","CROSS_ARM_PRIOR_EXPOSURE",
                        "SYNTHETIC_ONLY_REAL_SOURCE_DENY","DENY_INDEPENDENT_AGENT_EXPOSURE",
                        "PRODUCER_OWNER_MISMATCH")
            status=403 if ex.code in deny_codes else 404 if ex.code in ("TASK_NOT_FOUND","SOURCE_NOT_REGISTERED") else 409
            raise HTTPException(status,detail={"code":ex.code}) from ex

    @app.get("/v1/tpa/status")
    def status(request: Request):
        p=person(request,("manager","producer"))
        return {"mode":"SYNTHETIC_TASK_MANAGEMENT_ONLY","role":p["role"],
                "real_source_import":False,"true_agent":False,
                "real_experts":False,"gold_promotion":False,
                "original_d0_preserved":True}

    @app.get("/v1/tpa/sources")
    def sources(request:Request):
        p=person(request,("manager","producer"))
        return call(controller.sources,role=p["role"])

    @app.post("/v1/tpa/source-imports/validate")
    def check_import(request:Request,body:dict):
        p=person(request,("producer",))
        return call(controller.validate_import,role=p["role"],body=validate_body(ImportCheck,body))

    @app.get("/v1/tpa/tasks")
    def list_tasks(request:Request):
        p=person(request,("manager","producer"))
        return call(controller.listing,role=p["role"],actor=p["actor"])

    @app.post("/v1/tpa/tasks/drafts")
    def drafts(request:Request,body:dict):
        p=person(request,("producer",))
        return call(controller.draft,role=p["role"],actor=p["actor"],body=validate_body(Draft,body))

    @app.post("/v1/tpa/batches/drafts")
    def batch_drafts(request:Request,body:dict):
        p=person(request,("producer",))
        return call(controller.batch_drafts,role=p["role"],actor=p["actor"],
                    body=validate_body(BatchDraft,body))

    @app.get("/v1/tpa/batches")
    def batches(request:Request):
        p=person(request,("manager","producer"))
        return call(controller.batches,role=p["role"])

    @app.post("/v1/tpa/tasks/{task_id}/validate")
    def validate(task_id:str,request:Request):
        p=person(request,("producer",))
        return call(controller.transition,role=p["role"],actor=p["actor"],
                    task_id=task_id,action="validate")

    @app.post("/v1/tpa/tasks/{task_id}/freeze")
    def freeze(task_id:str,request:Request):
        p=person(request,("producer",))
        return call(controller.transition,role=p["role"],actor=p["actor"],
                    task_id=task_id,action="freeze")

    @app.post("/v1/tpa/tasks/{task_id}/prepare")
    def prepare(task_id:str,request:Request):
        p=person(request,("producer",))
        return call(controller.prepare,role=p["role"],actor=p["actor"],task_id=task_id)

    @app.post("/v1/tpa/tasks/{task_id}/assign")
    def assign(task_id:str,request:Request,body:dict):
        p=person(request,("manager",))
        return call(controller.assign,role=p["role"],actor=p["actor"],
                    task_id=task_id,body=validate_body(Assignment,body))

    @app.post("/v1/tpa/tasks/{task_id}/publish")
    def publish(task_id:str,request:Request,body:dict):
        p=person(request,("manager",))
        return call(controller.publish,role=p["role"],actor=p["actor"],
                    task_id=task_id,body=validate_body(Publish,body))

    @app.post("/v1/tpa/tasks/{task_id}/revoke")
    def revoke(task_id:str,request:Request):
        p=person(request,("manager",))
        return call(controller.revoke,role=p["role"],actor=p["actor"],task_id=task_id)

    @app.get("/v1/tpa/audit")
    def audit(request:Request):
        p=person(request,("auditor",))
        return call(controller.audit,role=p["role"])
