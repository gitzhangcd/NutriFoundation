from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from gates import assess,EXTERNAL_RECEIPTS
from app import make_app

@pytest.fixture
def patch_assess(monkeypatch):
    import app
    record={'real_person_ux_pilot':'NO_GO_PENDING_IDENTITY_ETHICS_DEPLOYMENT_EVIDENCE',
            'formal_NDS_R1_experiment':'NO_GO_EMPIRICAL_CAPTURE_PENDING','source_count':6,
            'external_requirements':[{'gate':x,'status':'PENDING_INDEPENDENT_EVIDENCE','requirement':y} for x,y in EXTERNAL_RECEIPTS.items()],
            'case_projection_binding':{'decision':'BLOCK_REQUIRES_SCIENTIFIC_OWNER_RECONCILIATION'},
            'bounded_projection_contract':'PASS'}
    monkeypatch.setattr(app,'assess',lambda repo_root:record)
    return record

def test_app_does_not_accept_empty_admin_token(patch_assess):
    with pytest.raises(RuntimeError):make_app(Path('.'),'')

def test_no_anonymous_readiness(patch_assess):
    c=TestClient(make_app(Path('.'),'SYN-LOCAL-LONG-TOKEN-ONLY'))
    assert c.get('/v1/readiness').status_code==401
    assert c.get('/v1/readiness',headers={'X-Workbench-Admin-Token':'wrong'}).status_code==401

def test_scoped_admin_only_no_authorization_endpoints(patch_assess):
    c=TestClient(make_app(Path('.'),'SYN-LOCAL-LONG-TOKEN-ONLY'))
    j=c.get('/v1/readiness',headers={'X-Workbench-Admin-Token':'SYN-LOCAL-LONG-TOKEN-ONLY'})
    assert j.status_code==200 and j.json()['source_count']==6
    assert j.headers['Cache-Control'].startswith('no-store')
    for path in ['/reader','/api/original.pdf','/v1/tasks','/v1/experts/qualify','/v1/gold','/v1/official/submit']:
        assert c.get(path).status_code==404

def test_static_security_headers(patch_assess):
    c=TestClient(make_app(Path('.'),'SYN-LOCAL-LONG-TOKEN-ONLY'))
    resp=c.get('/')
    assert resp.status_code==200
    assert "'unsafe-eval'" not in resp.headers['Content-Security-Policy']
    assert 'no-store' in resp.headers['Cache-Control']

def test_untrusted_overrides_cannot_unlock(monkeypatch):
    import gates
    class A:pass
    monkeypatch.setattr(gates,'ScientificAdapter',lambda path:A())
    monkeypatch.setattr(gates,'compare_r0_r2',lambda a:{'case_ref':'D2-NHANES-L-0001:r3','source_packet_id':'HBSP-R1P0-001','sources':[0]*6,'projection_sha256':'z'})
    monkeypatch.setattr(gates,'view_binding_check',lambda path:{'same_case_ref':False,'decision':'BLOCK_REQUIRES_SCIENTIFIC_OWNER_RECONCILIATION'})
    x=assess(Path('.'),{k:True for k in EXTERNAL_RECEIPTS})
    assert x['real_person_ux_pilot'].startswith('NO_GO')
    assert x['formal_NDS_R1_experiment'].startswith('NO_GO')
    assert all(z['status']!='PASS' for z in x['external_requirements'])
