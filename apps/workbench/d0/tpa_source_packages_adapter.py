"""Source-package routes share original /manage D0 cookie, CSRF, Host and Origin."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, ValidationError
from ea_runtime import EAError
from tpa_runtime import TPAError
from tpa_source_packages import SourcePackages


class StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SyntheticPackageManifest(StrictBody):
    schema_version: str
    import_kind: str
    parser_adapter: str
    source_id: str
    revision_id: str
    source_type: str
    profile_id: str
    canonical_document_sha256: str
    rights_status: str
    parent_package_id: str | None = None


class RegisterPackage(SyntheticPackageManifest):
    package_id: str
    idempotency_key: str


def install_source_package_routes(app: FastAPI, registry: SourcePackages):
    def person(request, roles):
        p=getattr(request.state,"principal",None)
        if p is None:
            raise HTTPException(401,detail={"code":"UNAUTHENTICATED"})
        if p["role"] not in roles or p["actor"].startswith("SYN-EA-"):
            raise HTTPException(403,detail={"code":"ROLE_FORBIDDEN"})
        return p

    def body(cls,data):
        try:
            return cls.model_validate(data).model_dump()
        except (ValidationError,TypeError,ValueError) as exc:
            raise HTTPException(422,detail={"code":"INVALID_SOURCE_PACKAGE_BODY"}) from exc

    def call(fn,**kwargs):
        try:
            return fn(**kwargs)
        except (TPAError,EAError) as exc:
            invalid={
                "UNSUPPORTED_PACKAGE_CONTRACT","INVALID_PACKAGE_ID",
                "INVALID_IDEMPOTENCY_KEY","INVALID_PAGINATION","INVALID_SOURCE_LINEAGE",
                "SOURCE_RIGHTS_NOT_QUALIFIED","INVALID_STRUCTURED_SOURCE"
            }
            forbidden={"ROLE_FORBIDDEN","SYNTHETIC_ONLY_REAL_SOURCE_DENY"}
            missing={"SOURCE_NOT_REGISTERED","SOURCE_PACKAGE_NOT_FOUND","PARENT_PACKAGE_NOT_FOUND"}
            status=422 if exc.code in invalid else 403 if exc.code in forbidden else 404 if exc.code in missing else 409
            raise HTTPException(status,detail={"code":exc.code}) from exc

    @app.get("/v1/tpa/source-packages")
    def list_packages(request:Request, limit:int=25, offset:int=0):
        p=person(request,("producer","manager"))
        return call(registry.listing,role=p["role"],limit=limit,offset=offset)

    @app.post("/v1/tpa/source-packages/validate")
    def validate_package(request:Request, payload:dict):
        p=person(request,("producer",))
        return call(registry.validate,role=p["role"],
                    manifest=body(SyntheticPackageManifest,payload))

    @app.post("/v1/tpa/source-packages")
    def register_package(request:Request,payload:dict):
        p=person(request,("producer",))
        return call(registry.register,role=p["role"],actor=p["actor"],
                    body=body(RegisterPackage,payload))

    @app.get("/v1/tpa/source-packages/{package_id}")
    def package_detail(package_id:str,request:Request):
        p=person(request,("producer","manager"))
        return call(registry.detail,role=p["role"],package_id=package_id)
