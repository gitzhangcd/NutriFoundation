"""Leakage kill tests for C2.1 task-scoped synthetic reader, no NDS human outputs."""
import hashlib
import json
from pathlib import Path

import pytest
from conftest import bind, h, saved, freeze_req, screen

SRC = 'SYN-5-2-PAPER'
QUOTE = 'Three hundred adults with obesity were randomised'


def scope(task='SYN-R2'):
    return f'/v1/tasks/{task}/sources/{SRC}'


def anchor_request(doc):
    unit = next(u for u in doc['units'] if QUOTE in u['raw'])
    start = len(unit['raw'][:unit['raw'].index(QUOTE)].encode('utf-16-le')) // 2
    end = start+len(QUOTE.encode('utf-16-le'))//2
    return {'unit_id':unit['unit_id'],'quote':QUOTE,'start_utf16':start,
            'end_utf16':end,'expected_revision':doc['revision'],
            'expected_source_markdown_sha256':doc['source_markdown_sha256']}


def setup_r2(env):
    bind(env,'SYN-R2','SYN-EXPERT-C')
    client,keys,_=env
    headers=h(keys,'SYN-EXPERT-C')
    d=client.get(scope()+'/document',headers=headers)
    assert d.status_code==200,d.text
    return d.json(),headers


def test_no_public_reader_or_direct_file_backdoor(env):
    c,k,_=env
    for url in ['/reader/api/document','/reader/api/original.pdf','/reader/api/pdf/page/1/png',
                '/api/original.pdf','/api/import','/assets/fig1_consorte_diagram.jpg',
                '/v1/sources','/openapi.json','/v1/tasks/SYN-R2/sources',scope()+'/original.pdf']:
        r=c.get(url)
        assert r.status_code in (401,404,405), (url,r.status_code,r.text[:80])
        assert r.headers.get('cache-control','').find('no-store')>=0,url
        assert 'X-Workbench-Token' in r.headers.get('vary',''),url
    assert c.get('/static/vendor/pdfjs/pdf.min.mjs').status_code in (404,200) # engine code only


def test_task_and_token_gate_document_pdf_search_export(env):
    c,k,_=env
    bind(env,'SYN-R0','SYN-EXPERT-A')
    bind(env,'SYN-R1','SYN-EXPERT-B')
    doc,h2=setup_r2(env)
    assert doc['unit_count'] == 154
    assert 'html' not in doc['units'][0]
    assert doc['source_pages']==16
    expected=doc['source_pdf_sha256']
    paths=[scope()+'/document',scope()+'/search?q=randomised',scope()+'/original.pdf',
           scope()+'/pages/1/png',scope()+'/export',scope()+'/anchors']
    for url in paths:
        for hdr in ({},h(k,'SYN-EXPERT-A'),h(k,'SYN-EXPERT-B'),h(k,'SYN-ADMIN')):
            r=c.get(url,headers=hdr)
            assert r.status_code in (401,404), (url,r.status_code,r.text[:120])
            assert r.headers.get('Cache-Control','').find('no-store')>=0
    got=c.get(scope()+'/original.pdf',headers=h2)
    assert got.status_code==200 and got.content.startswith(b'%PDF-')
    assert hashlib.sha256(got.content).hexdigest()==expected
    assert 'no-store' in got.headers['cache-control']
    assert c.get(scope()+'/pages/1/png',headers=h2).content.startswith(b'\x89PNG')
    r=c.get(scope()+'/search?q=randomised',headers=h2)
    assert r.status_code==200 and r.json()['results']
    assert c.get(scope()+'/export',headers=h2).json()['provenance']=='SYNTHETIC_ONLY_NOT_SCIENTIFIC_OUTPUT'
    assert c.get(scope()+'/document',headers={**h2,'If-None-Match':'*'}).status_code==200
    assert c.get(scope()+'/original.pdf',headers={**h2,'Range':'bytes=0-100'}).status_code==200


def test_missing_source_and_no_traversal_or_globalsearch(env):
    c,k,_=env
    doc,headers=setup_r2(env)
    for url in ['/v1/tasks/SYN-R2/sources/OTHER/document',
                scope()+'/assets/../../../../etc/passwd',
                scope()+'/assets/not-a-sha',
                scope()+'/pages/99/png',
                scope()+'/search?q=x',
                '/v1/tasks/SYN-FAKE/sources/'+SRC+'/document']:
        r=c.get(url,headers=headers)
        assert r.status_code in (404,422), (url,r.status_code,r.text[:200])
    assert c.get(scope()+'/sources',headers=headers).status_code==404


def test_task_anchor_ownership_binding_and_restart(env):
    c,k,app=env
    bind(env,'SYN-R0','SYN-EXPERT-A')
    doc,headers=setup_r2(env)
    r=c.post(scope()+'/anchors',json=anchor_request(doc),headers=headers)
    assert r.status_code==201,r.text
    aid=r.json()['anchor_id']
    locate=scope()+'/anchors/'+aid
    assert c.get(locate,headers=headers).status_code==200
    assert c.get(locate,headers=h(k,'SYN-EXPERT-A')).status_code==404
    assert c.post(locate+'/resolve',headers=h(k,'SYN-EXPERT-A'),json={
        'expected_revision':doc['revision'],'expected_source_pdf_sha256':doc['source_pdf_sha256']}).status_code==404
    r=c.post(locate+'/resolve',headers=headers,json={'expected_revision':doc['revision'],
       'expected_source_pdf_sha256':doc['source_pdf_sha256']})
    assert r.status_code==200,r.text
    assert r.json()['pdf_locator']['page']==1
    assert c.get(locate+'/locator',headers=headers).status_code==200
    assert c.get(locate+'/locator',headers=h(k,'SYN-EXPERT-A')).status_code==404
    bind_url=scope()+'/bind-anchor'
    req={'anchor_id':aid,'field':'decision_focus','expected_document_revision':doc['revision'],
         'expected_pdf_sha256':doc['source_pdf_sha256']}
    assert c.post(bind_url,json=req,headers=headers).status_code==200
    assert len(c.get(scope()+'/bindings',headers=headers).json()['items'])==1
    assert c.post(bind_url,json={**req,'field':'meta_audit'},headers=headers).status_code==422
    assert c.post(bind_url,json={**req,'expected_document_revision':'r0-stale'},headers=headers).status_code==409
    assert c.post(scope()+'/anchors',json={**anchor_request(doc),'start_utf16':anchor_request(doc)['start_utf16']+1},headers=headers).status_code==409
    saved(env,'SYN-R2','SYN-EXPERT-C')
    fr=c.post('/v1/tasks/SYN-R2/freeze',json=freeze_req(),headers=headers)
    assert fr.status_code==200,fr.text
    assert c.post(bind_url,json=req,headers=headers).status_code==403
    assert c.post(scope()+'/anchors',json=anchor_request(doc),headers=headers).status_code==403
    assert len(c.get(scope()+'/bindings',headers=headers).json()['items'])==1
    # Audit binds source set before independent judgment freeze.
    events=c.get('/v1/tasks/SYN-R2/audit',headers=h(k,'SYN-AUDITOR')).json()['events']
    names=[x['event'] for x in events]
    assert names.index('FREEZE_SOURCE_BINDING_SET') < names.index('FREEZE_J_preAI')
    digest=json.loads(next(x['details'] for x in events if x['event']=='FREEZE_SOURCE_BINDING_SET'))
    assert digest['count']==1 and len(digest['binding_sha256'])==64
    assert all('candidate_set' not in str(v) for v in c.get('/v1/tasks/SYN-R0/read-model',headers=h(k,'SYN-EXPERT-A')).json().values())


def test_r1_source_spans_only_after_candidate_and_never_full_pdf(env):
    c,k,_=env
    bind(env,'SYN-R1','SYN-EXPERT-B')
    r1=h(k,'SYN-EXPERT-B');src=scope('SYN-R1')
    for url in (src+'/document',src+'/original.pdf',src+'/search?q=obesity',src+'/export',src+'/pages/1/png'):
        assert c.get(url,headers=r1).status_code==404
    assert c.get(src+'/candidate-spans',headers=r1).status_code==404
    producer=h(k,'SYN-PRODUCER-1')
    good={'candidates':[{'candidate_ref':'SYN-1','text':'Synth candidate',
            'source_spans':[{'source_ref':SRC,'quote':QUOTE}]}],
          'idempotency_key':'R1-TEST-CANDIDATES-001'}
    assert c.post('/v1/tasks/SYN-R1/candidate-set',json=good,headers=producer).status_code==200
    record=c.get(src+'/candidate-spans',headers=r1)
    assert record.status_code==200,record.text
    assert record.json()['candidate_spans'][0]['quote']==QUOTE
    assert 'units' not in record.text and 'original.pdf' not in record.text
    assert c.get(src+'/original.pdf',headers=r1).status_code==404
    audit=c.get('/v1/tasks/SYN-R1/audit',headers=h(k,'SYN-AUDITOR')).json()['events']
    assert any(x['event']=='CANDIDATE_EXPOSURE' for x in audit)
    assert c.get(src+'/candidate-spans',headers=h(k,'SYN-EXPERT-C')).status_code==404


def test_r1_invalid_synthetic_candidate_span_fails_closed(env):
    c,k,_=env
    bind(env,'SYN-R1','SYN-EXPERT-B')
    good={'candidates':[{'candidate_ref':'SYN-1','text':'Synth candidate',
            'source_spans':[{'source_ref':SRC,'quote':'A completely nonexistent quote inside this paper'}]}],
          'idempotency_key':'R1-TEST-CANDIDATES-002'}
    assert c.post('/v1/tasks/SYN-R1/candidate-set',json=good,headers=h(k,'SYN-PRODUCER-1')).status_code==200
    r=c.get(scope('SYN-R1')+'/candidate-spans',headers=h(k,'SYN-EXPERT-B'))
    assert r.status_code==409
    events=c.get('/v1/tasks/SYN-R1/audit',headers=h(k,'SYN-AUDITOR')).json()['events']
    assert not any(x['event']=='CANDIDATE_EXPOSURE' for x in events)


def test_tamper_pdf_blocks_all_source_views(env):
    c,k,app=env
    doc,headers=setup_r2(env)
    target=app.state.source_store.verified_pdf_path()
    original=target.read_bytes()
    try:
        target.write_bytes(original+b'CHANGED')
        for url in (scope()+'/document',scope()+'/search?q=three',scope()+'/original.pdf',scope()+'/export'):
            assert c.get(url,headers=headers).status_code==409,url
    finally:
        target.write_bytes(original)


def test_r0_agent_never_and_r2_no_early_candidate_despite_source(env):
    c,k,_=env
    bind(env,'SYN-R0','SYN-EXPERT-A')
    doc,headers=setup_r2(env)
    r0=h(k,'SYN-EXPERT-A')
    assert c.get(scope('SYN-R0')+'/document',headers=r0).status_code==200
    assert c.get('/v1/tasks/SYN-R0/candidate-set',headers=r0).status_code==403
    assert c.get('/v1/tasks/SYN-R2/candidate-set',headers=headers).status_code==403
    response=c.get(scope()+'/document',headers=headers)
    for forbidden in ('candidate_set','meta_audit','QualifiedDecisionReference','SRS-D1-A3R-001:r4'):
        assert forbidden not in response.text
    assert c.get(scope('SYN-R0')+'/export',headers=r0).json()['task_id']=='SYN-R0'


def test_source_binding_own_task_only(env):
    c,k,_=env
    bind(env,'SYN-R0','SYN-EXPERT-A')
    doc,headers=setup_r2(env)
    a=c.post(scope()+'/anchors',json=anchor_request(doc),headers=headers).json()
    other=h(k,'SYN-EXPERT-A')
    req={'anchor_id':a['anchor_id'],'field':'decision_focus','expected_document_revision':doc['revision'],
         'expected_pdf_sha256':doc['source_pdf_sha256']}
    assert c.post(scope('SYN-R0')+'/bind-anchor',headers=other,json=req).status_code==404
    assert not c.get(scope('SYN-R0')+'/anchors',headers=other).json()['items']


def test_database_immutability_for_source_bindings_and_anchor_record(env):
    import sqlite3
    c,k,app=env
    doc,headers=setup_r2(env)
    a=c.post(scope()+'/anchors',json=anchor_request(doc),headers=headers).json()
    req={'anchor_id':a['anchor_id'],'field':'reference_set.conditional',
         'expected_document_revision':doc['revision'],'expected_pdf_sha256':doc['source_pdf_sha256']}
    assert c.post(scope()+'/bind-anchor',json=req,headers=headers).status_code==200
    with pytest.raises(sqlite3.IntegrityError,match='IMMUTABLE_SOURCE_BINDING'):
        with app.state.controller.conn() as db:
            db.execute('DELETE FROM source_bindings WHERE task=?',('SYN-R2',))
    with pytest.raises(sqlite3.IntegrityError,match='IMMUTABLE_SOURCE_ANCHOR'):
        with sqlite3.connect(app.state.source_store.db) as db:
            db.execute('UPDATE anchors SET payload=? WHERE anchor_id=?',('{}',a['anchor_id']))
    assert c.get(scope()+'/anchors',headers=headers).json()['items'][0]['anchor_id']==a['anchor_id']


def test_markdown_tamper_denies_document_search_and_export(env):
    c,k,app=env
    doc,headers=setup_r2(env)
    file=app.state.source_store.path('document.md')
    saved=file.read_bytes()
    try:
        file.write_bytes(saved+b'\nFICTIONAL INJECTION')
        for url in (scope()+'/document',scope()+'/search?q=body',scope()+'/export',scope()+'/original.pdf'):
            assert c.get(url,headers=headers).status_code==409,url
    finally:file.write_bytes(saved)


def test_locator_metadata_mutation_is_denied_by_db_trigger(env):
    import sqlite3
    c,k,app=env
    doc,headers=setup_r2(env)
    a=c.post(scope()+'/anchors',json=anchor_request(doc),headers=headers).json()
    url=scope()+'/anchors/'+a['anchor_id']
    assert c.post(url+'/resolve',headers=headers,json={'expected_revision':doc['revision'],
         'expected_source_pdf_sha256':doc['source_pdf_sha256']}).status_code==200
    with pytest.raises(sqlite3.IntegrityError,match='IMMUTABLE_PDF_LOCATOR'):
        with sqlite3.connect(app.state.source_store.db) as db:
            db.execute('UPDATE pdf_locators SET locator_payload=? WHERE anchor_id=?',('{}',a['anchor_id']))
    assert c.get(url+'/locator',headers=headers).status_code==200


def test_search_reports_total_pages_and_normalises_query(env):
    c,k,_=env
    bind(env,'SYN-R0','SYN-EXPERT-A')
    doc,headers=setup_r2(env)
    first=c.get(scope()+'/search?q=the',headers=headers).json()
    assert first['total']>16 and len(first['results'])==16 and first['truncated'] and first['offset']==0
    ids=[r['unit_id'] for r in first['results']]
    pages=[]
    for offset in range(0,first['total'],16):
        page=c.get(scope()+f'/search?q=the&offset={offset}',headers=headers).json()
        assert page['total']==first['total'] and page['offset']==offset
        pages+=[r['unit_id'] for r in page['results']]
    assert pages[:16]==ids and len(pages)==len(set(pages))==first['total'] and not page['truncated']
    single=c.get(scope()+'/search?q=weight%20loss',headers=headers).json()
    assert c.get(scope()+'/search?q=weight%20%20%0Aloss',headers=headers).json()['total']==single['total']>0
    assert c.get(scope()+'/search?q=WEIGHT%20LOSS',headers=headers).json()['total']==single['total']
    bold=next(u for u in doc['units'] if '**' in u['raw'])
    words=[w for w in bold['raw'].split('**')[1].split() if w][:2]
    assert c.get(scope()+'/search',params={'q':' '.join(words)},headers=headers).json()['total']>0
    for q in ('ab','  ab  '):
        r=c.get(scope()+'/search',params={'q':q},headers=headers)
        assert r.status_code==422 and r.json()['detail']['code']=='SEARCH_QUERY_TOO_SHORT'
    zh=c.get(scope()+'/search',params={'q':'体重'},headers=headers)
    assert zh.status_code==200 and zh.json()['total']==0
    assert c.get(scope()+'/search',params={'q':'体重'},headers=h(k,'SYN-EXPERT-A')).status_code in (401,404)
    assert c.get(scope()+'/search?q=the&offset=-1',headers=headers).status_code==422
