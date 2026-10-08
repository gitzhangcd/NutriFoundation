import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server import BASE, FIELD_INFO, DraftDB, empty_decision, make_app

QUOTE = 'Three hundred adults with obesity were randomised'

@pytest.fixture
def client(tmp_path):
    return TestClient(make_app(tmp_path/'runtime',preload_fixture=True))


def state(client,task='DEMO-R2-PREAI'):
    r=client.get(f'/api/tasks/{task}/draft');assert r.status_code==200
    return r.json()


def request_payload(draft):
    return dict(expected_revision=draft['revision'],document_id=draft['document_id'],
                canonical_revision=draft['canonical_revision'],source_pdf_sha256=draft['source_pdf_sha256'],
                payload=draft['payload'],bindings=draft['bindings'])


def make_anchor(client):
    doc=client.get('/reader/api/document').json()
    unit=next(u for u in doc['units'] if QUOTE in u['raw'])
    start=unit['raw'].index(QUOTE)
    reply=client.post('/reader/api/anchors',json={
       'unit_id':unit['unit_id'],'quote':QUOTE,'start_utf16':start,'end_utf16':start+len(QUOTE),
       'expected_revision':doc['revision'],
       'expected_source_markdown_sha256':doc['source_markdown_sha256']})
    assert reply.status_code==201, reply.text
    return reply.json()


def test_real_source_import_canonical_and_pdf(client):
    r=client.get('/reader/api/document').json()
    assert r['unit_count']==154 and r['source_pages']==16
    assert r['source_status']=='STRUCTURED_NOT_SCIENTIFICALLY_VERIFIED'
    assert client.get('/reader/api/original.pdf').content.startswith(b'%PDF-')


def test_all_19_fields_and_seven_reference_categories(client):
    keys=list(FIELD_INFO)
    assert len(keys)==19
    assert len([x for x in keys if x.startswith('reference_set.')])==7
    assert set(state(client)['payload'])==set(empty_decision())


def test_draft_persists_across_new_client_and_restart(tmp_path):
    root=tmp_path/'persistent'
    c1=TestClient(make_app(root,preload_fixture=True))
    d=state(c1);p=request_payload(d)
    p['payload']['decision_focus']='合成研究任务：评估证据适用性'
    p['payload']['reference_set']['unresolved']=['缺少个体营养史']
    p['payload']['clarification_count']=2
    reply=c1.put('/api/tasks/DEMO-R2-PREAI/draft',json=p)
    assert reply.status_code==200 and reply.json()['revision']==1
    c2=TestClient(make_app(root,preload_fixture=False))
    restored=state(c2)
    assert restored['payload']==p['payload'] and restored['revision']==1
    assert restored['updated_at']


def test_anchor_roundtrip_bind_and_replay(client):
    a=make_anchor(client)
    doc=client.get('/reader/api/document').json()
    assert a['source_pdf_sha256']==doc['source_pdf_sha256']
    location=client.post('/reader/api/locators/'+a['anchor_id']+'/resolve',json={
        'expected_revision':doc['revision'],'expected_source_pdf_sha256':doc['source_pdf_sha256']})
    assert location.status_code==200,location.text
    assert location.json()['pdf_locator']['match_status']=='VERIFIED_UNIQUE_PDF_TEXT'
    assert location.json()['pdf_locator']['page']==1
    d=state(client);p=request_payload(d)
    p['payload']['rationale_notes']=['这是一条合成演示说明，不是论文真值']
    p['bindings']={'rationale_notes':[a['anchor_id']]}
    saved=client.put('/api/tasks/DEMO-R2-PREAI/draft',json=p)
    assert saved.status_code==200,saved.text
    exported=client.get('/api/tasks/DEMO-R2-PREAI/export').json()
    assert exported['bindings']==p['bindings'] and exported['payload']==p['payload']
    assert exported['provenance']=='SYNTHETIC_ONLY_NOT_SCIENTIFIC_OUTPUT'
    assert client.get('/reader/api/anchors').json()[0]['anchor_id']==a['anchor_id']


def test_optimistic_conflict_409_not_overwrite(client):
    d=state(client)
    p1=request_payload(copy.deepcopy(d));p1['payload']['decision_focus']='new-a'
    p2=request_payload(copy.deepcopy(d));p2['payload']['decision_focus']='new-b'
    assert client.put('/api/tasks/DEMO-R2-PREAI/draft',json=p1).status_code==200
    rejected=client.put('/api/tasks/DEMO-R2-PREAI/draft',json=p2)
    assert rejected.status_code==409
    assert 'REVISION_CONFLICT' in rejected.text
    assert state(client)['payload']['decision_focus']=='new-a'
    assert len(client.get('/api/tasks/DEMO-R2-PREAI/events').json()['events'])==1


def test_forged_field_and_invalid_payload_rejected(client):
    d=state(client);p=request_payload(d)
    p['payload']['reference_set']['unknown']='SHADOW_FIELD'
    assert client.put('/api/tasks/DEMO-R2-PREAI/draft',json=p).status_code==422
    p=request_payload(d);p['bindings']={'not_in_profile':['SA-fake']}
    assert client.put('/api/tasks/DEMO-R2-PREAI/draft',json=p).status_code==422
    p=request_payload(d);p['payload']['clarification_count']=1.5
    assert client.put('/api/tasks/DEMO-R2-PREAI/draft',json=p).status_code==422


def test_rogue_anchor_rejected_and_no_revision_increment(client):
    d=state(client);p=request_payload(d);p['bindings']={'rationale_notes':['SA-forged']}
    r=client.put('/api/tasks/DEMO-R2-PREAI/draft',json=p)
    assert r.status_code==422 and 'UNKNOWN_ANCHOR_ID' in r.text
    assert state(client)['revision']==0


def test_stale_document_sha_and_revision_rejected(client):
    d=state(client);p=request_payload(d);p['source_pdf_sha256']='tampered'
    assert client.put('/api/tasks/DEMO-R2-PREAI/draft',json=p).status_code==409
    p=request_payload(d);p['canonical_revision']='r999'
    assert client.put('/api/tasks/DEMO-R2-PREAI/draft',json=p).status_code==409
    assert state(client)['revision']==0


def test_isolated_tasks_and_no_agent_or_freeze_endpoints(client):
    a=state(client,'DEMO-R0-NOAI');b=state(client,'DEMO-R2-PREAI')
    req=request_payload(a);req['payload']['decision_focus']='ONLY R0 TEST'
    assert client.put('/api/tasks/DEMO-R0-NOAI/draft',json=req).status_code==200
    assert state(client,'DEMO-R2-PREAI')['payload']['decision_focus'] is None
    for path in ['/api/candidates','/api/tasks/DEMO-R2-PREAI/freeze','/api/agent/reveal','/api/qualified-reference']:
        assert client.get(path).status_code==404
        assert client.post(path).status_code==404
    assert client.get('/api/health').json()['scientific_capture']=='DISABLED'


def test_unknown_task_no_access(client):
    assert client.get('/api/tasks/UNKNOWN/draft').status_code==404
    assert client.put('/api/tasks/UNKNOWN/draft',json=request_payload(state(client))).status_code==404


def test_profile_parity_exact_with_c0_1(client):
    served=client.get('/api/profile').json()
    expected=json.loads((BASE/'specs/decision_profile.json').read_text())
    assert served==expected
    assert set(FIELD_INFO)=={f['key'] for g in served['field_groups'] for f in g['fields']}