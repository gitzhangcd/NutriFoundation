"""Original D0 cookie/CSRF/Origin-gated synthetic fixture attestation routes."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, ValidationError

from ea_runtime import EAError
from tpa_runtime import TPAError
from tpa_agent_operations import AgentPreparationLedger


class StrictBody(BaseModel):
    model_config=ConfigDict(extra="forbid")


class Attestation(StrictBody):
    contract:str
    idempotency_key:str
    expected_preparation_event_hash:str
    expected_candidate_set_digest:str


def install_agent_preparation_routes(app:FastAPI, ledger:AgentPreparationLedger):
    def person(request, allowed):
        p=getattr(request.state,"principal",None)
        if p is None:raise HTTPException(401,detail={"code":"UNAUTHENTICATED"})
        if p["role"] not in allowed or p["actor"].startswith("SYN-EA-"):
            raise HTTPException(403,detail={"code":"ROLE_FORBIDDEN"})
        return p

    def call(fn,**kwargs):
        try:return fn(**kwargs)
        except (TPAError,EAError) as exc:
            code=exc.code
            forbidden={"ROLE_FORBIDDEN","DENY_INDEPENDENT_AGENT_EXPOSURE",
                       "SYNTHETIC_ONLY_REAL_SOURCE_DENY","PRODUCER_OWNER_MISMATCH"}
            missing={"TASK_NOT_FOUND","SOURCE_NOT_REGISTERED"}
            invalid={"INVALID_IDEMPOTENCY_KEY","INVALID_AGENT_TASK_ID",
                     "INVALID_PROVENANCE_DIGEST","INVALID_PREPARATION_CONTRACT",
                     "INVALID_PAGINATION"}
            status=403 if code in forbidden else 404 if code in missing else 422 if code in invalid else 409
            raise HTTPException(status,detail={"code":code}) from exc

    @app.get("/v1/tpa/agent-preparations")
    def listing(request:Request,limit:int=25,offset:int=0):
        p=person(request,("producer","manager"))
        return call(ledger.listing,role=p["role"],limit=limit,offset=offset)

    @app.get("/v1/tpa/agent-preparations/{task_id}")
    def detail(task_id:str,request:Request):
        p=person(request,("producer","manager"))
        return call(ledger.detail,role=p["role"],actor=p["actor"],task_id=task_id)

    @app.get("/v1/tpa/agent-preparations/{task_id}/inspect")
    def inspect(task_id:str,request:Request):
        p=person(request,("producer",))
        return call(ledger.inspect,role=p["role"],actor=p["actor"],task_id=task_id)

    @app.post("/v1/tpa/agent-preparations/{task_id}/attest")
    def attest(task_id:str,request:Request,payload:dict):
        p=person(request,("producer",))
        try:body=Attestation.model_validate(payload).model_dump()
        except (ValidationError,TypeError,ValueError) as exc:
            raise HTTPException(422,detail={"code":"INVALID_AGENT_ATTESTATION_BODY"}) from exc
        return call(ledger.attest,role=p["role"],actor=p["actor"],task_id=task_id,body=body)
