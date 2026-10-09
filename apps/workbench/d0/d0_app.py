"""Unified private engineering Workbench. Formal capture has no enabled mode."""
from __future__ import annotations
import argparse
import importlib.util
import json
import secrets
import sys
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,ConfigDict,Field
from auth import Auth,ACTORS
from bootstrap import bootstrap
from ea_runtime import EvidenceEngine
from ea_seed import populate as seed_evidence_synthetic
from ea_adapter import install_evidence_routes

BASE=Path(__file__).resolve().parent
C21=BASE.parent/'c2_1';C22=BASE.parent/'c2_2'
sys.path.insert(0,str(C21))
sys.path.append(str(C22))
spec=importlib.util.spec_from_file_location('c21_runtime',C21/'app.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
from gates import assess

class Login(BaseModel):
    model_config=ConfigDict(extra='forbid')
    username:str=Field(min_length=1,max_length=80)
    password:str=Field(min_length=1,max_length=256)

def make_app(root:Path,repo_root:Path,*,accounts:dict,auth_path:Path,origin:str,allow_synthetic:bool=False):
    if allow_synthetic is not True:raise RuntimeError('SYNTHETIC_ONLY_EXPLICIT_OPT_IN_REQUIRED')
    parsed=urlsplit(origin)
    if parsed.scheme not in ('http','https') or not parsed.netloc or parsed.path or parsed.query or parsed.fragment:
        raise RuntimeError('EXACT_ORIGIN_REQUIRED')
    if parsed.scheme=='http' and parsed.hostname not in ('127.0.0.1','localhost','testserver'):
        raise RuntimeError('PLAINTEXT_PUBLIC_ORIGIN_FORBIDDEN')
    inner=legacy.make_app(root,repo_root,actors=ACTORS)
    # Old UI is replaced; old controller and secure reader endpoints are retained.
    inner.router.routes=[r for r in inner.router.routes if getattr(r,'path',None) not in ('/','/static','/health')]
    bootstrap(inner.state.controller)
    auth=Auth(auth_path,accounts)
    tokens={actor:token for token,(actor,_) in inner.state.tokens.items()}
    readiness=assess(repo_root)
    app=FastAPI(title='NutriFoundation private synthetic Workbench',docs_url=None,redoc_url=None,openapi_url=None)
    app.state.inner=inner;app.state.auth=auth
    # Additive evidence annotation. Reuses this app's authenticated D0 session,
    # existing visual Workbench and read-only NDS science controller.
    # Only self-authored, explicitly synthetic fixtures; never auto-load real files.
    ea=EvidenceEngine(Path(root)/'ea_synthetic.sqlite', BASE/'ea_contract.v0.1.json')
    with ea.connect() as ea_db:
        has_demo=ea_db.execute('SELECT 1 FROM tasks LIMIT 1').fetchone() is not None
    if not has_demo:
        seed_evidence_synthetic(ea)
    app.state.evidence_engine=ea
    install_evidence_routes(app,ea)
    secure=parsed.scheme=='https'
    def failure(code,status):return JSONResponse({'detail':{'code':code}},status_code=status)
    @app.middleware('http')
    async def session_gate(request,call_next):
        # Drop externally supplied synthetic bearer tokens: cookie is the only entry.
        request.scope['headers']=[(k,v) for k,v in request.scope['headers'] if k.lower()!=b'x-workbench-token']
        path=request.url.path
        public=path in ('/','/health','/v1/login') or path.startswith('/static/')
        session=auth.session(request.cookies.get('nutri_session'))
        response=None
        if request.headers.get('host')!=parsed.netloc:
            response=failure('HOST_NOT_ALLOWED',400)
        elif request.method not in ('GET','HEAD','OPTIONS'):
            if request.headers.get('origin')!=origin:
                response=failure('ORIGIN_REQUIRED',403)
            elif path!='/v1/login' and (not session or not secrets.compare_digest(request.headers.get('x-csrf-token',''),session['csrf'])):
                response=failure('CSRF_REQUIRED',403)
        if response is None and not public and session is None:
            response=failure('UNAUTHENTICATED',401)
        if response is None:
            if session:
                request.state.principal=session
                request.scope['headers'].append((b'x-workbench-token',tokens[session['actor']].encode()))
            response=await call_next(request)
        response.headers.update({'Cache-Control':'private, no-store, max-age=0','Vary':'Cookie',
            'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','X-Frame-Options':'DENY',
            'X-Robots-Tag':'noindex, nofollow',
            'Content-Security-Policy':"default-src 'self'; script-src 'self'; worker-src 'self' blob:; img-src 'self' blob: data:; style-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        if secure:response.headers['Strict-Transport-Security']='max-age=31536000'
        return response
    @app.get('/health')
    def health():return {'stage':'WB-P0.2-D0','mode':'SYNTHETIC_ENGINEERING_ONLY','scientific_capture':'DISABLED',
        'live_pilot':'NO_GO','public_https':'CONFIGURED' if secure else 'NOT_ACTIVATED_SSH_TUNNEL_ONLY','os_security_acceptance':'NOT_PASSED'}
    @app.post('/v1/login')
    def login(body:Login,request:Request):
        value,error=auth.login(body.username,body.password,request.client.host)
        if error:return failure(error,429 if error=='RATE_LIMITED' else 401)
        auth.logout(request.cookies.get('nutri_session'))
        session_payload={k:v for k,v in value.items() if k!='id'}
        session_payload['program']='EVIDENCE_ANNOTATION' if auth.accounts[value['username']]['actor'].startswith('SYN-EA-') else 'NDS_DECISION'
        response=JSONResponse(session_payload)
        response.set_cookie('nutri_session',value['id'],httponly=True,secure=secure,samesite='strict',max_age=auth.ttl,path='/')
        return response
    @app.get('/v1/session')
    def session(request:Request):
        p=request.state.principal
        return {'username':p['username'],'role':p['role'],'csrf_token':p['csrf'],'synthetic':True,'program':'EVIDENCE_ANNOTATION' if p['actor'].startswith('SYN-EA-') else 'NDS_DECISION'}
    @app.post('/v1/logout')
    def logout(request:Request):
        auth.logout(request.cookies.get('nutri_session'))
        response=JSONResponse({'logged_out':True});response.delete_cookie('nutri_session',path='/',secure=secure,httponly=True,samesite='strict')
        return response
    @app.get('/v1/profile')
    def profile():return json.loads((BASE.parent/'c1/specs/decision_profile.json').read_text())
    @app.get('/v1/tasks/{task}/records')
    def records(task:str,request:Request):
        p=request.state.principal;controller=inner.state.controller
        with controller.conn() as db:
            controller._binding(db,task,p['actor'],p['role'])
            rows=db.execute('SELECT * FROM snapshots WHERE task=? ORDER BY created_at',(task,)).fetchall()
            result=[]
            for row in rows:
                controller._valid_snapshot(row)
                result.append({'kind':row['kind'],'payload':json.loads(row['payload']),
                    'content_sha':row['content_sha'],'created_at':row['created_at'],
                    'read_only':True,'synthetic':True})
            return {'records':result,'scientific_capture':False}
    @app.get('/v1/readiness')
    def get_readiness(request:Request):
        if request.state.principal['role']!='manager':raise HTTPException(403,detail='MANAGER_ONLY')
        return readiness
    @app.post('/v1/demo/prepare/{task}')
    def prepare(task:str,request:Request):
        p=request.state.principal
        if p['role']!='producer':raise HTTPException(403,detail='PRODUCER_ONLY')
        return inner.state.controller.generate(task,p['actor'],p['role'],[{
            'candidate_ref':'SYN-DEMO-CANDIDATE-1','text':'Synthetic engineering candidate; assess the quoted study design. Not a clinical recommendation.',
            'source_spans':[{'source_ref':'SYN-5-2-PAPER','quote':'Three hundred adults with obesity were randomised'}]}],
            'D0-SYNTHETIC-CANDIDATES-v1')
    app.mount('/static',StaticFiles(directory=BASE/'web'),name='ui')
    @app.get('/')
    def index():return FileResponse(BASE/'web/index.html')
    app.mount('/',inner)
    return app

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo-root',type=Path,required=True);parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--accounts',type=Path,required=True);parser.add_argument('--auth-db',type=Path,required=True)
    parser.add_argument('--origin',required=True);parser.add_argument('--port',type=int,default=8793)
    parser.add_argument('--allow-synthetic-execution',action='store_true')
    args=parser.parse_args()
    if args.accounts.stat().st_mode & 0o037:raise SystemExit('ACCOUNTS_FILE_MUST_BE_PRIVATE_0600_OR_0640')
    app=make_app(args.root,args.repo_root,accounts=json.loads(args.accounts.read_text()),auth_path=args.auth_db,
                 origin=args.origin,allow_synthetic=args.allow_synthetic_execution)
    import uvicorn
    # One worker, loopback only, no forwarded-header trust and no credential-bearing access log.
    uvicorn.run(app,host='127.0.0.1',port=args.port,workers=1,proxy_headers=False,access_log=False)
if __name__=='__main__':main()
