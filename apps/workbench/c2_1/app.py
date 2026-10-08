"""Synthetic-only FastAPI controller; not a production credential system.

Run behind explicit synthetic flag. No C1 reader, source-library or raw vault mount.
"""
from __future__ import annotations
import argparse
import secrets
from pathlib import Path
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from authority import ScientificAdapter, CASE_REF
from models import Screening,SaveDraft,Freeze,PutCandidates,SubmitVerification,SubmitReconciliation
from workflow import ARMS,Controller,deny
from secure_reader import install_secure_reader

BASE=Path(__file__).resolve().parent

def make_app(root:Path,repo_root:Path|None=None,*,test_authority=None,actors:dict|None=None)->FastAPI:
    """No production mode in C2. Caller must intentionally use SYNTHETIC TEST actors."""
    if test_authority is None and repo_root is None:raise RuntimeError('PINNED_REPOSITORY_REQUIRED')
    a=ScientificAdapter(repo_root or Path('.'),test_authority=test_authority)
    db=Controller(Path(root)/'c2_synthetic.sqlite',a)
    roles=actors or {'SYN-ADMIN':'manager','SYN-PRODUCER-1':'producer',
                     'SYN-EXPERT-A':'expert','SYN-EXPERT-B':'expert','SYN-EXPERT-C':'expert',
                     'SYN-AUDITOR':'auditor'}
    # tokens are server-only; never expose via GET endpoint or bundled JS fixtures.
    tokens={secrets.token_urlsafe(32):(user,role) for user,role in roles.items()}
    app=FastAPI(title='Workbench C2 SYNTHETIC Contract Controller',docs_url=None,redoc_url=None,openapi_url=None)
    app.state.tokens=tokens
    app.state.controller=db
    app.state.adapter=a
    def principal(x_workbench_token:str|None=Header(None)):
        if not x_workbench_token:deny('UNAUTHENTICATED',401)
        v=tokens.get(x_workbench_token)
        if v is None:deny('UNAUTHENTICATED',401)
        return v
    @app.get('/health')
    def health():return {'stage':'WB-P0.2-C2.1','mode':'SYNTHETIC_ENGINEERING_ONLY',
        'scientific_capture':'DISABLED','authority_binding':'FIXTURE_ONLY' if a.test_authority else 'PINNED_GIT_BLOB_VERIFIED',
        'production_authentication':'NOT_IMPLEMENTED'}
    @app.get('/v1/tasks')
    def tasks(p=Depends(principal)):return db.task_list(*p)
    @app.post('/v1/tasks/{task}/qualification')
    def qualify(task:str,screen:Screening,p=Depends(principal)):
        if p[1]!='manager':deny('MANAGER_ONLY')
        if screen.actor_id not in roles or roles[screen.actor_id]!='expert':deny('UNKNOWN_SYNTHETIC_ACTOR',422)
        return db.qualify(task,screen.actor_id,screen.model_dump())
    @app.get('/v1/tasks/{task}/read-model')
    def read_model(task:str,p=Depends(principal)):return db.read_model(task,*p)
    @app.get('/v1/tasks/{task}/draft')
    def draft(task:str,p=Depends(principal)):return db.draft(task,*p)
    @app.put('/v1/tasks/{task}/draft')
    def save(task:str,request:SaveDraft,p=Depends(principal)):
        return db.save(task,*p,request.expected_revision,request.payload,request.packet_digest)
    @app.post('/v1/tasks/{task}/freeze')
    def freeze(task:str,req:Freeze,p=Depends(principal)):
        return db.freeze(task,*p,req.expected_revision,req.idempotency_key,req.exposure_assertions)
    @app.post('/v1/tasks/{task}/candidate-set')
    def set_candidates(task:str,req:PutCandidates,p=Depends(principal)):
        return db.generate(task,*p,[x.model_dump() for x in req.candidates],req.idempotency_key)
    @app.get('/v1/tasks/{task}/candidate-set')
    def get_candidates(task:str,p=Depends(principal)):
        return db.candidate_endpoint(task,*p)
    @app.post('/v1/tasks/{task}/verify')
    def verify(task:str,req:SubmitVerification,p=Depends(principal)):
        return db.complete(task,*p,[x.model_dump() for x in req.items],req.idempotency_key)
    @app.post('/v1/tasks/{task}/reconcile')
    def reconcile(task:str,req:SubmitReconciliation,p=Depends(principal)):
        return db.complete(task,*p,[x.model_dump() for x in req.items],req.idempotency_key,req.post_ai_judgment)
    @app.get('/v1/tasks/{task}/audit')
    def audit(task:str,p=Depends(principal)):return db.audit(*p,task)
    install_secure_reader(app,db,Path(root),principal,BASE/'fixtures/5_2_diet.AnnotationSourcePackage.v0.1.zip')
    # Deliberately no legacy /reader mount or global source-library file routes.
    # No /reader mount: C1's unguarded PDF endpoints must not cross into C2.1.
    app.mount('/static',StaticFiles(directory=BASE/'web'),name='ui')
    @app.get('/')
    def index():return FileResponse(BASE/'web/index.html')
    return app

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path,required=True)
    p.add_argument('--root',type=Path,default=BASE/'.synthetic-data');p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8790)
    p.add_argument('--allow-synthetic-execution',action='store_true')
    args=p.parse_args()
    if not args.allow_synthetic_execution:raise SystemExit('C2 requires explicit --allow-synthetic-execution; not production authorized')
    app=make_app(args.root,args.repo_root)
    # Not a production auth solution: display generated tokens only in local developer console.
    for tok,(name,role) in app.state.tokens.items():print(f'LOCAL SYNTHETIC {name}/{role}: {tok}',flush=True)
    import uvicorn;uvicorn.run(app,host=args.host,port=args.port)
if __name__=='__main__':main()
