"""Read-only test-gated manager dashboard, not a real expert server."""
from __future__ import annotations
import argparse
import os
import secrets
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from gates import assess

BASE=Path(__file__).resolve().parent

def make_app(repo_root:Path, admin_test_token:str):
    if not admin_test_token or len(admin_test_token)<20:
        raise RuntimeError('SYNTHETIC_ADMIN_TOKEN_REQUIRED')
    # Startup must fail if science changed or upstream case view isn't pinned.
    status=assess(repo_root)
    app=FastAPI(title='C2.2 readiness inspection (synthetic)',openapi_url=None,docs_url=None,redoc_url=None)
    @app.middleware('http')
    async def security(request,call_next):
        r=await call_next(request)
        r.headers['Cache-Control']='no-store, private, max-age=0'
        r.headers['X-Content-Type-Options']='nosniff'
        r.headers['Referrer-Policy']='no-referrer'
        r.headers['Content-Security-Policy']="default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        r.headers['X-Frame-Options']='DENY'
        return r
    @app.get('/health')
    def health():return {'mode':'SYNTHETIC_PREP_ONLY','production_capture':'DISABLED','live_pilot':'NO_GO'}
    @app.get('/v1/readiness')
    def readiness(x_workbench_admin_token:str|None=Header(None)):
        if not x_workbench_admin_token or not secrets.compare_digest(x_workbench_admin_token,admin_test_token):
            raise HTTPException(401,'UNAUTHENTICATED')
        return status
    app.mount('/static',StaticFiles(directory=BASE/'web'),name='static')
    @app.get('/')
    def index():return FileResponse(BASE/'web/index.html')
    return app

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,required=True)
    p.add_argument('--allow-synthetic-readiness',action='store_true');p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8792)
    a=p.parse_args()
    if not a.allow_synthetic_readiness:raise SystemExit('Real deployment disabled. Supply --allow-synthetic-readiness for local checks only.')
    token=secrets.token_urlsafe(32)
    print('SYNTHETIC ADMIN TOKEN (local console only): '+token,flush=True)
    import uvicorn
    uvicorn.run(make_app(a.repo_root,token),host=a.host,port=a.port)
if __name__=='__main__':main()
