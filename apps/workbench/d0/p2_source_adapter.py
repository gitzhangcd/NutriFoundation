"""P2 isolated Source Studio API: same D0 host/cookie/Origin/CSRF.

P2 Source Curator accounts (SYN-P2-CURATOR-*) may review raw synthetic
units only. Original P1.1 Manager remains metadata-only, and no downstream
EA/TPA/Gold/expert route is installed or written by P2.
"""
from __future__ import annotations
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, ValidationError
from p2_source_registry import SourceStudio

class Body(BaseModel):
    model_config=ConfigDict(extra="forbid")

class Register(Body):
    source_id:str
    revision_id:str
    title:str
    source_type:str
    identifier_kind:str
    identifier:str
    available_at:str
    fetched_at:str
    raw_format:str
    raw_content:str
    rights_assertion:str
    source_family_refs:list[str]=[]

class Rights(Body):
    decision:str
    uses:list[str]
    evidence_ref:str

class Convert(Body):
    external_payload:dict|None=None

class Review(Body):
    unit_id:str
    decision:str
    start_utf16:int
    end_utf16:int
    source_quote:str
    source_quote_sha256:str
    pdf_locator_status:str="UNRESOLVED"
    findings:dict={}

class Translation(Body):
    unit_id:str
    translation_zh:str
    provenance_ref:str
    expected_unit_text_sha256:str

class Freeze(Body):
    expected_document_sha256:str

class Scope(Body):
    project_id:str
    batch_id:str

def install_p2_source_routes(app:FastAPI,studio:SourceStudio):
    def person(req:Request):
        p=getattr(req.state,"principal",None)
        if not p:raise HTTPException(401,detail={"code":"UNAUTHENTICATED"})
        if p["actor"].startswith("SYN-EA-"):
            raise HTTPException(403,detail={"code":"CROSS_ARM_SOURCE_DENIED"})
        return p
    def payload(cls,raw):
        try:return cls.model_validate(raw).model_dump()
        except (ValidationError,TypeError,ValueError) as exc:
            raise HTTPException(422,detail={"code":"INVALID_P2_PAYLOAD"}) from exc

    @app.get("/v1/p2/overview")
    def overview(request:Request):
        p=person(request)
        return studio.overview(p["role"])

    @app.get("/v1/p2/sources")
    def listing(request:Request,limit:int=25,offset:int=0,q:str="",status:str="",
                project_id:str="",batch_id:str=""):
        p=person(request)
        return studio.list(p["role"],limit,offset,q,status,project_id,batch_id)

    @app.post("/v1/p2/sources")
    def register(request:Request,body:dict):
        p=person(request)
        return studio.register(p["role"],p["actor"],payload(Register,body))

    @app.get("/v1/p2/sources/{source_id}/{revision_id}")
    def detail(source_id:str,revision_id:str,request:Request):
        p=person(request)
        return studio.detail(p["role"],source_id,revision_id)

    @app.post("/v1/p2/sources/{source_id}/{revision_id}/rights")
    def rights(source_id:str,revision_id:str,request:Request,body:dict):
        p=person(request)
        return studio.rights(p["role"],p["actor"],source_id,revision_id,payload(Rights,body))

    @app.post("/v1/p2/sources/{source_id}/{revision_id}/convert")
    def convert(source_id:str,revision_id:str,request:Request,body:dict):
        p=person(request)
        return studio.convert(p["role"],p["actor"],source_id,revision_id,payload(Convert,body))

    @app.get("/v1/p2/sources/{source_id}/{revision_id}/document")
    def document(source_id:str,revision_id:str,request:Request):
        p=person(request)
        return studio.document(p["role"],source_id,revision_id)

    @app.get("/v1/p2/sources/{source_id}/{revision_id}/original")
    def original(source_id:str,revision_id:str,request:Request):
        p=person(request)
        return studio.original(p["role"],source_id,revision_id)

    @app.get("/v1/p2/sources/{source_id}/{revision_id}/reviews")
    def reviews(source_id:str,revision_id:str,request:Request):
        p=person(request)
        return studio.reviews(p["role"],source_id,revision_id)

    @app.post("/v1/p2/sources/{source_id}/{revision_id}/qa")
    def qa(source_id:str,revision_id:str,request:Request,body:dict):
        p=person(request)
        return studio.review(p["role"],p["actor"],source_id,revision_id,payload(Review,body))

    @app.get("/v1/p2/sources/{source_id}/{revision_id}/rework")
    def rework(source_id:str,revision_id:str,request:Request):
        p=person(request)
        return studio.rework_handoff(p["role"],source_id,revision_id)

    @app.get("/v1/p2/sources/{source_id}/{revision_id}/translations")
    def translations(source_id:str,revision_id:str,request:Request):
        p=person(request)
        return studio.translations(p["role"],source_id,revision_id)

    @app.post("/v1/p2/sources/{source_id}/{revision_id}/translations")
    def add_translation(source_id:str,revision_id:str,request:Request,body:dict):
        p=person(request)
        return studio.save_translation(p["role"],p["actor"],source_id,revision_id,
                                       payload(Translation,body))

    @app.post("/v1/p2/sources/{source_id}/{revision_id}/freeze")
    def freeze(source_id:str,revision_id:str,request:Request,body:dict):
        p=person(request)
        return studio.freeze(p["role"],p["actor"],source_id,revision_id,payload(Freeze,body))

    @app.post("/v1/p2/sources/{source_id}/{revision_id}/scope")
    def bind(source_id:str,revision_id:str,request:Request,body:dict):
        p=person(request);d=payload(Scope,body)
        return studio.bind_scope(p["role"],p["actor"],source_id,revision_id,d["project_id"],d["batch_id"])

    @app.get("/v1/p2/audit")
    def audit(request:Request):
        p=person(request)
        return studio.audit(p["role"])
