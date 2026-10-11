"""P1.1-A3 functional & security acceptance on the original D0 FastAPI application."""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_tpa_integrated import app, prepare_draft  # noqa: F401 - pytest imported fixture
from test_d0 import login

PROJECT="PRJ-SYN-CASE001"
BATCH="BATCH-SYN-CASE001"

def post_project(p, headers, key="project-key-001", project_id=PROJECT, name="Synthetic evidence program"):
    return p.post('/v1/tpa/projects',headers=headers,json={"project_id":project_id,
        "name":name,"description":"Synthetic operational metadata", "idempotency_key":key})


def post_batch(p, headers, project=PROJECT, key="batch-key-001", batch_id=BATCH):
    return p.post(f'/v1/tpa/projects/{project}/batches',headers=headers,
        json={"batch_id":batch_id,"label":"Pilot testing batch","purpose":"synthetic grouping","idempotency_key":key})


def setup(p,h):
    assert post_project(p,h).status_code==200
    assert post_batch(p,h).status_code==200
    sources=p.get('/v1/tpa/sources').json()['sources']
    main=next(s for s in sources if s['source_type']=='RANDOMIZED_TRIAL')
    other=next(s for s in sources if s['source_type']=='GUIDELINE')
    return main,other


def draft(main, task_id="TPA-SYN-P11-001", strategy="AGENT_PROPOSE_EXPERT_VERIFY", others=()):
    all_sources=[main,*others]
    return {"task_id":task_id,"task_kind":"EVIDENCE_ECOSYSTEM_CASE",
      "primary_source":{"source_id":main['source_id'],"revision_id":main['revision_id']},
      "allowed_source_versions":[{k:s[k] for k in ('source_id','revision_id','canonical_document_sha256')} for s in all_sources],
      "profile_id":main['profile_id'],"knowledge_cutoff":"2026-10-10T00:00:00Z",
      "workflow_strategy":strategy,"project_id":PROJECT,"batch_id":BATCH,"idempotency_key":"task-key-001"}


def test_p11_project_batch_create_and_idempotent(app):
    p,h=login(app,'producer')
    first=post_project(p,h)
    assert first.status_code==200,first.text
    assert post_project(p,h).json()==first.json()
    assert post_project(p,h,name="Altered title").status_code==409
    assert post_project(p,h,key="other-project-key",name="Altered title").status_code==409
    b=post_batch(p,h)
    assert b.status_code==200,b.text
    assert post_batch(p,h).json()==b.json()
    assert post_batch(p,h,key="other-batch-key").status_code==409
    assert p.get('/v1/tpa/projects').json()['total']==1
    assert p.get(f'/v1/tpa/projects/{PROJECT}/batches').json()['batches'][0]['task_count']==0
    assert p.get(f'/v1/tpa/projects/{PROJECT}/batches/{BATCH}').json()['project_id']==PROJECT


def test_p11_atomic_task_placement_and_legacy(app):
    p,h=login(app,'producer')
    main,guide=setup(p,h)
    payload=draft(main,others=[guide])
    path='/v1/tpa/tasks/in-batch'
    created=p.post(path,headers=h,json=payload)
    assert created.status_code==200,created.text
    assert created.json()['placement']=={'project_id':PROJECT,'batch_id':BATCH,'task_id':payload['task_id'],'task_revision_id':'r1'}
    assert p.post(path,headers=h,json=payload).json()==created.json()
    changed={**payload,'task_id':'TPA-SYN-P11-TAMPER'}
    assert p.post(path,headers=h,json=changed).status_code==409
    assert p.get('/v1/tpa/tasks/TPA-SYN-P11-TAMPER/management').status_code==404
    detail=p.get(f'/v1/tpa/tasks/{payload["task_id"]}/management').json()
    assert detail['state']=='DRAFT' and detail['placement']['batch_id']==BATCH
    assert detail['gold_qualification']=='NOT_ELIGIBLE'
    assert 'candidate_payload' not in str(detail) and 'units' not in str(detail)
    allowed=p.get(f'/v1/tpa/tasks?project_id={PROJECT}&batch_id={BATCH}&limit=100&offset=0')
    assert allowed.status_code==200 and allowed.json()['total']==1
    assert p.get('/v1/tpa/tasks').status_code==200  # old unfiltered route still compatible
    prepare_draft(app, 'TPA-SYN-P11-LEGACY')
    legacy=p.get('/v1/tpa/tasks?state=LEGACY').json()
    assert legacy['total']==1 and legacy['tasks'][0]['legacy'] is True
    assert p.get('/v1/tpa/overview').json()['counts']['legacy']==1
    assert p.get(f'/v1/tpa/overview?project_id={PROJECT}&batch_id={BATCH}').json()['counts']['total']==1


def test_p11_invalid_source_or_scope_has_zero_side_effect(app):
    p,h=login(app,'producer')
    main,_=setup(p,h)
    bad=draft(main,task_id='TPA-SYN-P11-BADSCOPE')
    bad['batch_id']='BATCH-SYN-NOEXIST'
    assert p.post('/v1/tpa/tasks/in-batch',headers=h,json=bad).status_code==404
    assert p.get('/v1/tpa/tasks/TPA-SYN-P11-BADSCOPE/management').status_code==404
    bad=draft(main,task_id='TPA-SYN-P11-BADHASH')
    bad['allowed_source_versions'][0]['canonical_document_sha256']='0'*64
    assert p.post('/v1/tpa/tasks/in-batch',headers=h,json=bad).status_code==409
    assert p.get('/v1/tpa/tasks/TPA-SYN-P11-BADHASH/management').status_code==404
    bad=draft(main,task_id='TPA-SYN-P11-BADTIME')
    bad['knowledge_cutoff']='2000-01-01T00:00:00Z'
    assert p.post('/v1/tpa/tasks/in-batch',headers=h,json=bad).status_code==409
    assert p.get('/v1/tpa/tasks/TPA-SYN-P11-BADTIME/management').status_code==404
    assert p.get(f'/v1/tpa/projects/{PROJECT}/batches/{BATCH}').json()['task_count']==0


def test_p11_strict_roles_original_blindness_and_csrf(app):
    p,h=login(app,'producer');setup(p,h)
    assert p.post('/v1/tpa/projects',json={}).status_code==403  # missing Origin + CSRF
    assert p.post('/v1/tpa/projects',headers={"Origin":"http://testserver"},json={}).status_code==403
    m,mh=login(app,'manager')
    assert m.get('/v1/tpa/projects').status_code==200
    assert m.get('/v1/tpa/overview').status_code==200
    assert m.post('/v1/tpa/projects',headers=mh,json={}).status_code==403
    assert m.post('/v1/tpa/tasks/in-batch',headers=mh,json={}).status_code==403
    assert m.get('/v1/ea/tasks').status_code==403
    assert m.get('/v1/tpa/audit').status_code==403
    for who in ('ea1','ea2','r0','r1','r2','auditor'):
        c,_=login(app,who)
        assert c.get('/v1/tpa/projects').status_code==403
        assert c.get('/v1/tpa/overview').status_code==403
        assert c.get(f'/v1/tpa/projects/{PROJECT}/batches').status_code==403
    assert p.get('/v1/tpa/overview?batch_id=BATCH-SYN-ANY').status_code==422
    assert p.get('/v1/tpa/projects?limit=10000').status_code==422


def test_p11_server_state_counts_and_no_gold(app):
    p,h=login(app,'producer');main,_=setup(p,h)
    body=draft(main,strategy='HUMAN_INDEPENDENT')
    assert p.post('/v1/tpa/tasks/in-batch',headers=h,json=body).status_code==200
    tid=body['task_id']
    def scoped():return p.get('/v1/tpa/overview?project_id='+PROJECT+'&batch_id='+BATCH).json()['counts']
    assert scoped()['preparing']==1
    for action,state in (('validate','VALIDATED'),('freeze','DEFINITION_FROZEN'),('prepare','READY_FOR_ASSIGNMENT')):
        r=p.post(f'/v1/tpa/tasks/{tid}/{action}',headers=h)
        assert r.status_code==200,r.text
        assert r.json()['state']==state
    assert scoped()['ready']==1 and scoped()['preparing']==0
    m,mh=login(app,'manager')
    assert p.post(f'/v1/tpa/tasks/{tid}/assign',headers=h,json={}).status_code==403
    r=m.post(f'/v1/tpa/tasks/{tid}/assign',headers=mh,json={
        'expert_actor':'SYN-EA-EXPERT-B','idempotency_key':'p11-assign-key-001'})
    assert r.status_code==200,r.text
    assert scoped()['assigned']==1
    r=m.post(f'/v1/tpa/tasks/{tid}/publish',headers=mh,json={
        'idempotency_key':'p11-publish-key-001'})
    assert r.status_code==200,r.text
    assert scoped()['published']==1
    d=m.get(f'/v1/tpa/tasks/{tid}/management').json()
    assert d['state']=='PUBLISHED' and d['gold_qualification']=='NOT_ELIGIBLE'
    assert 'candidate' not in str(d).lower()
    r=m.post(f'/v1/tpa/tasks/{tid}/revoke',headers=mh)
    assert r.status_code==200
    assert scoped()['revoked']==1
    ea,_=login(app,'ea2')
    assert ea.get(f'/v1/ea/tasks/{tid}/workpack').status_code==403
    auditor,_=login(app,'auditor')
    assert auditor.get('/v1/tpa/audit').json()['valid'] is True


def test_p11_no_markup_in_operational_metadata(app):
    p,h=login(app,'producer')
    x=post_project(p,h,key='markup-try-key',project_id='PRJ-SYN-NOHTML',name='<img src=x onerror=alert(1)>')
    assert x.status_code==422
    assert p.get('/v1/tpa/projects').json()['total']==0
    x=post_project(p,h,key='email-try-key',project_id='PRJ-SYN-NOEMAIL',name='PII user@example.com')
    assert x.status_code==422