"""P1 expert-feedback closure: per-item provenance and synthetic bilingual scope."""
import hashlib
import json
import sqlite3
import pytest
from conftest import bind,h,saved
from test_secure_reader import scope,setup_r2,anchor_request

def test_full_self_authored_bilingual_demo_is_permission_gated(env):
    c,k,_=env
    doc,r2=setup_r2(env)
    url='/v1/tasks/SYN-R2/reading-demo'
    r=c.get(url,headers=r2)
    assert r.status_code==200,r.text
    data=r.json()
    assert data['coverage']['bilingual_units']==data['coverage']['units']
    assert data['coverage']['units']>=12
    assert sum(x['type']=='TABLE' for x in data['units'])==2
    assert all(x['english'] and x['chinese'] for x in data['units'])
    assert data['source_anchor_eligible'] is False
    assert data['pdf_available'] is False
    assert data['scientific_capture'] is False
    assert c.get(url).status_code in (401,404)
    assert c.get(url,headers=h(k,'SYN-ADMIN')).status_code in (401,404)
    bind(env,'SYN-R1','SYN-EXPERT-B')
    assert c.get('/v1/tasks/SYN-R1/reading-demo',headers=h(k,'SYN-EXPERT-B')).status_code==404

def test_item_level_evidence_binding_is_draft_version_bound_and_immutable(env):
    c,k,app=env
    doc,headers=setup_r2(env)
    result=c.post(scope()+'/anchors',headers=headers,json=anchor_request(doc))
    assert result.status_code==201,result.text
    anchor_id=result.json()['anchor_id']
    # No item-level binding to unsaved revision zero.
    empty=c.post(scope()+'/bind-anchor-item',headers=headers,json={
       'anchor_id':anchor_id,'field':'decision_focus','item_index':0,
       'item_sha256':'0'*64,'expected_draft_revision':1,
       'expected_document_revision':doc['revision'],'expected_pdf_sha256':doc['source_pdf_sha256']})
    assert empty.status_code==409
    saved(env,'SYN-R2','SYN-EXPERT-C')
    draft=c.get('/v1/tasks/SYN-R2/draft',headers=headers).json()
    text=draft['payload']['decision_focus']
    req={'anchor_id':anchor_id,'field':'decision_focus','item_index':0,
       'item_sha256':hashlib.sha256(text.encode()).hexdigest(),
       'expected_draft_revision':draft['revision'],
       'expected_document_revision':doc['revision'],'expected_pdf_sha256':doc['source_pdf_sha256']}
    url=scope()+'/bind-anchor-item'
    assert c.post(url,headers=headers,json=req).status_code==200
    items=c.get(scope()+'/item-bindings',headers=headers).json()['items']
    assert len(items)==1 and items[0]['current_statement_matches'] is True
    assert c.post(url,headers=headers,json={**req,'item_sha256':'0'*64}).status_code==409
    assert c.post(url,headers=h(k,'SYN-AUDITOR'),json=req).status_code==404
    with app.state.controller.conn() as db:
        with pytest.raises(sqlite3.IntegrityError,match='IMMUTABLE_ITEM_BINDING'):
            db.execute('DELETE FROM source_item_bindings WHERE task=?',('SYN-R2',))
    payload=json.loads(json.dumps(draft['payload']))
    payload['decision_focus']='Revised synthetic judgment that invalidates the earlier item link.'
    put=c.put('/v1/tasks/SYN-R2/draft',headers=headers,json={
        'payload':payload,'expected_revision':draft['revision'],
        'packet_digest':draft['packet_digest']})
    assert put.status_code==200,put.text
    updated=c.get(scope()+'/item-bindings',headers=headers).json()['items']
    assert updated[0]['current_statement_matches'] is False
