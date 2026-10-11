"""B3 expert operations reuse original D0 cookie, CSRF, Host, Origin guards."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, ValidationError
from tpa_runtime import TPAError
from ea_runtime import EAError
from tpa_expert_handoff import ExpertHandoffLedger


class HandoffRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    contract:str
    idempotency_key:str
    expected_assignment_event_hash:str
    expected_grant_event_hash:str


def install_expert_handoff_routes(app:FastAPI, ledger:ExpertHandoffLedger):
    def identity(request,allowed):
        p=getattr(request.state,"principal",None)
        if p is None:raise HTTPException(401,detail={"code":"UNAUTHENTICATED"})
        if p["role"] not in allowed or p["actor"].startswith("SYN-EA-"):
            raise HTTPException(403,detail={"code":"ROLE_FORBIDDEN"})
        return p

    def guard(fn,**kwargs):
        try:return fn(**kwargs)
        except (TPAError,EAError) as exc:
            forbidden={"ROLE_FORBIDDEN","DENY_INDEPENDENT_AGENT_EXPOSURE",
                       "CROSS_ARM_PRIOR_EXPOSURE","SYNTHETIC_ONLY_REAL_SOURCE_DENY"}
            invalid={"INVALID_PAGINATION","INVALID_EXPERT_TASK_ID",
                     "INVALID_IDEMPOTENCY_KEY","INVALID_HANDOFF_CONTRACT"}
            missing={"TASK_NOT_FOUND","SOURCE_NOT_REGISTERED"}
            code=403 if exc.code in forbidden else 422 if exc.code in invalid else 404 if exc.code in missing else 409
            raise HTTPException(code,detail={"code":exc.code}) from exc

    @app.get("/v1/tpa/expert-roster")
    def roster(request:Request):
        p=identity(request,("manager","producer"))
        return guard(ledger.roster,role=p["role"])

    @app.get("/v1/tpa/expert-handoffs")
    def listing(request:Request,limit:int=25,offset:int=0):
        p=identity(request,("manager","producer"))
        return guard(ledger.listing,role=p["role"],limit=limit,offset=offset)

    @app.get("/v1/tpa/expert-handoffs/{task_id}/preview")
    def preview(task_id:str,request:Request):
        p=identity(request,("manager","producer"))
        return guard(ledger.preview,role=p["role"],task_id=task_id)

    @app.get("/v1/tpa/expert-handoffs/{task_id}")
    def detail(task_id:str,request:Request):
        p=identity(request,("manager","producer"))
        return guard(ledger.detail,role=p["role"],task_id=task_id)

    @app.post("/v1/tpa/expert-handoffs/{task_id}/attest")
    def attest(task_id:str,request:Request,payload:dict):
        p=identity(request,("manager",))
        try:body=HandoffRequest.model_validate(payload).model_dump()
        except (ValidationError,TypeError,ValueError) as exc:
            raise HTTPException(422,detail={"code":"INVALID_EXPERT_HANDOFF_REQUEST"}) from exc
        return guard(ledger.attest,role=p["role"],actor=p["actor"],task_id=task_id,body=body)
