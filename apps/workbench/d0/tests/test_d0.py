import hashlib
import json
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from d0_app import make_app
REPO=Path(__file__).resolve().parents[4]
PASSWORD='Synthetic-Test-Password-Only-1234'

def accounts():
    import base64
    salt=b'test-fixture-salt'
    digest=hashlib.pbkdf2_hmac('sha256',PASSWORD.encode(),salt,310000)
    encoded='pbkdf2_sha256$310000$'+base64.b64encode(salt).decode()+'$'+base64.b64encode(digest).decode()
    return {name:{'actor':actor,'role':role,'password_hash':encoded} for name,actor,role in [
        ('r0','SYN-EXPERT-A','expert'),('r1','SYN-EXPERT-B','expert'),('r2','SYN-EXPERT-C','expert'),
        ('manager','SYN-ADMIN','manager'),('producer','SYN-PRODUCER-1','producer'),('auditor','SYN-AUDITOR','auditor')]}

@pytest.fixture
def app(tmp_path):
    return make_app(tmp_path/'data',REPO,accounts=accounts(),auth_path=tmp_path/'auth.sqlite',origin='http://testserver',allow_synthetic=True)

def login(app,name='r2'):
    c=TestClient(app)
    r=c.post('/v1/login',json={'username':name,'password':PASSWORD},headers={'Origin':'http://testserver'})
    assert r.status_code==200,r.text
    assert 'HttpOnly' in r.headers['set-cookie'] and 'SameSite=strict' in r.headers['set-cookie']
    assert 'Secure' not in r.headers['set-cookie']
    return c,{'Origin':'http://testserver','X-CSRF-Token':r.json()['csrf_token']}

def test_formal_mode_refused(tmp_path):
    with pytest.raises(RuntimeError,match='SYNTHETIC_ONLY'):
        make_app(tmp_path,REPO,accounts=accounts(),auth_path=tmp_path/'auth.sqlite',origin='http://testserver',allow_synthetic=False)

def test_no_anonymous_bypass_or_external_token(app):
    c=TestClient(app)
    for url in ['/v1/tasks','/v1/readiness','/v1/tasks/SYN-R2/sources/SYN-5-2-PAPER/original.pdf']:
        r=c.get(url,headers={'X-Workbench-Token':next(iter(app.state.inner.state.tokens))})
        assert r.status_code==401
        assert 'no-store' in r.headers['cache-control']
    for url in ['/reader/api/original.pdf','/api/import','/openapi.json']:
        assert c.get(url).status_code in (401,404)
    assert c.get('/health').json()['scientific_capture']=='DISABLED'

def test_login_origin_bad_password_and_rate_limit(app):
    c=TestClient(app)
    assert c.post('/v1/login',json={'username':'r2','password':PASSWORD}).status_code==403
    assert c.post('/v1/login',json={'username':'r2','password':PASSWORD},headers={'Origin':'https://evil.example'}).status_code==403
    for _ in range(5):
        assert c.post('/v1/login',json={'username':'r2','password':'wrong'},headers={'Origin':'http://testserver'}).status_code==401
    assert c.post('/v1/login',json={'username':'r2','password':PASSWORD},headers={'Origin':'http://testserver'}).status_code==429

def test_task_owner_and_arm_isolation(app):
    r0,_=login(app,'r0'); r1,_=login(app,'r1'); r2,_=login(app)
    assert [t['task_id'] for t in r2.get('/v1/tasks').json()['tasks']]==['SYN-R2']
    assert r0.get('/v1/tasks/SYN-R2/read-model').status_code==404
    assert r0.get('/v1/tasks/SYN-R0/candidate-set').status_code==403
    assert r2.get('/v1/tasks/SYN-R2/candidate-set').status_code==403
    assert r1.get('/v1/tasks/SYN-R1/sources/SYN-5-2-PAPER/original.pdf').status_code==404
    assert r2.get('/v1/readiness').status_code==403
    mgr,_=login(app,'manager')
    assert mgr.get('/v1/readiness').json()['formal_NDS_R1_experiment'].startswith('NO_GO')

def save(c,h):
    d=c.get('/v1/tasks/SYN-R2/draft').json()
    d['payload']['decision_focus']='Synthetic engineering exercise only'
    body={k:d[k] for k in ['payload','packet_digest']};body['expected_revision']=d['revision']
    return c.put('/v1/tasks/SYN-R2/draft',json=body,headers=h),body

def test_csrf_save_conflict_restart_and_logout(app,tmp_path):
    c,h=login(app)
    assert save(c,{})[0].status_code==403
    assert save(c,{'Origin':'http://testserver','X-CSRF-Token':'wrong'})[0].status_code==403
    r,body=save(c,h);assert r.status_code==200 and r.json()['revision']==1
    assert c.put('/v1/tasks/SYN-R2/draft',json=body,headers=h).status_code==409
    restarted=make_app(tmp_path/'data',REPO,accounts=accounts(),auth_path=tmp_path/'auth.sqlite',origin='http://testserver',allow_synthetic=True)
    other=TestClient(restarted);other.cookies.update(c.cookies)
    assert other.get('/v1/tasks/SYN-R2/draft').json()['payload']==body['payload']
    assert other.post('/v1/logout',headers=h).status_code==200
    assert c.get('/v1/tasks').status_code==401

def test_freeze_and_candidate_phase_boundaries(app):
    c,h=login(app)
    producer,ph=login(app,'producer')
    assert producer.post('/v1/demo/prepare/SYN-R2',headers=ph).status_code==403
    assert save(c,h)[0].status_code==200
    req={'expected_revision':1,'idempotency_key':'d0-freeze-test-12345','exposure_assertions':{k:False for k in ['agent_output_seen','other_expert_output_seen','final_reference_seen','hidden_diet_values_seen','meta_audit_labels_seen']}}
    frozen=c.post('/v1/tasks/SYN-R2/freeze',json=req,headers=h)
    assert frozen.status_code==200 and frozen.json()['scientific_capture'] is False
    assert c.put('/v1/tasks/SYN-R2/draft',json={'expected_revision':1,'payload':{},'packet_digest':'bad'},headers=h).status_code in (403,409)
    assert producer.post('/v1/demo/prepare/SYN-R2',headers=ph).status_code==200
    assert c.get('/v1/tasks/SYN-R2/read-model').json()['allowed_actions']==['reconcile']
    assert producer.post('/v1/demo/prepare/SYN-R0',headers=ph).status_code==403

def test_expired_sessions_and_password_change_revoke(app,tmp_path):
    c,h=login(app)
    with app.state.auth.conn() as db:db.execute('UPDATE sessions SET expires=0')
    assert c.get('/v1/tasks').status_code==401
    c,h=login(app)
    changed=accounts();changed['r2']['password_hash']=changed['r0']['password_hash'].replace('310000','310001')
    other=make_app(tmp_path/'data',REPO,accounts=changed,auth_path=tmp_path/'auth.sqlite',origin='http://testserver',allow_synthetic=True)
    client=TestClient(other);client.cookies.update(c.cookies)
    assert client.get('/v1/tasks').status_code==401

def test_frozen_records_visible_only_to_owner(app):
    c,h=login(app)
    assert c.get('/v1/tasks/SYN-R2/records').status_code==200
    assert c.get('/v1/tasks/SYN-R2/records').json()['records']==[]
    assert save(c,h)[0].status_code==200
    req={'expected_revision':1,'idempotency_key':'d0-records-freeze-123','exposure_assertions':{k:False for k in ['agent_output_seen','other_expert_output_seen','final_reference_seen','hidden_diet_values_seen','meta_audit_labels_seen']}}
    assert c.post('/v1/tasks/SYN-R2/freeze',json=req,headers=h).status_code==200
    records=c.get('/v1/tasks/SYN-R2/records').json()['records']
    assert records[0]['kind']=='J_preAI' and records[0]['read_only'] is True
    other,_=login(app,'r0');assert other.get('/v1/tasks/SYN-R2/records').status_code==404

def test_parallel_first_exposure_is_atomic_and_audited_once(app):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    producer,ph=login(app,'producer')
    assert producer.post('/v1/demo/prepare/SYN-R1',headers=ph).status_code==200
    c,_=login(app,'r1');barrier=Barrier(8)
    def read():
        barrier.wait(timeout=5)
        return c.get('/v1/tasks/SYN-R1/read-model').status_code
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert list(pool.map(lambda _:read(),range(8)))==[200]*8
    auditor,_=login(app,'auditor')
    events=auditor.get('/v1/tasks/SYN-R1/audit').json()['events']
    assert len([x for x in events if x['event']=='CANDIDATE_EXPOSURE'])==1

def test_reader_import_does_not_write_into_readonly_release(tmp_path):
    import subprocess
    import os
    import shutil
    reader=tmp_path/'reader_core.py';(tmp_path/'web').mkdir()
    shutil.copy2(REPO/'apps/workbench/c2_1/reader_core.py',reader)
    env={**os.environ,'PYTHONPATH':str(REPO/'apps/workbench/c2_1')}
    code='import runpy; runpy.run_path('+repr(str(reader))+',run_name="reader_library_import")'
    result=subprocess.run([sys.executable,'-c',code],env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert not (tmp_path/'data').exists(),'importing reader must not create a legacy unprotected app/data workspace'
