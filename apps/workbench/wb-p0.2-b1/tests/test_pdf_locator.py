import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from pdf_locator import LocatorError, locate_pdf_quote
from wb_a import make_app, sha

FIXTURE=Path(__file__).resolve().parents[1]/'fixtures'/'5_2_diet.AnnotationSourcePackage.v0.1.zip'
QUOTE='Three hundred adults with obesity were randomised'

@pytest.fixture
def client(tmp_path):
    instance=TestClient(make_app(tmp_path))
    resp=instance.post('/api/import',files={'file':('paper.zip',FIXTURE.read_bytes(),'application/zip')})
    assert resp.status_code==200,resp.text
    return instance


def create(client, quote=QUOTE):
    doc=client.get('/api/document').json()
    unit=next(u for u in doc['units'] if quote in u['raw'])
    i=unit['raw'].index(quote)
    data={'unit_id':unit['unit_id'],'quote':quote,'start_utf16':len(unit['raw'][:i].encode('utf-16-le'))//2,
          'end_utf16':len(unit['raw'][:i+len(quote)].encode('utf-16-le'))//2,
          'expected_revision':doc['revision'],'expected_source_markdown_sha256':doc['source_markdown_sha256']}
    r=client.post('/api/anchors',json=data)
    assert r.status_code==201,r.text
    return r.json(),doc


def resolve(client,anchor,doc,**change):
    req={'expected_revision':doc['revision'],'expected_source_pdf_sha256':doc['source_pdf_sha256']}
    return client.post('/api/locators/'+anchor['anchor_id']+'/resolve',json=req|change)


def test_unique_real_pdf_bbox_and_hashes(client):
    anchor,doc=create(client)
    response=resolve(client,anchor,doc)
    assert response.status_code==200,response.text
    sidecar=response.json()
    match=sidecar['pdf_locator']
    assert match['match_status']=='VERIFIED_UNIQUE_PDF_TEXT'
    assert match['page']==1 and match['page_hint_agrees']
    assert match['pdf_sha256']==doc['source_pdf_sha256']
    assert match['quote_sha256']==sha(QUOTE)
    assert match['coordinate_system']=='PDF_PAGE_TOP_LEFT_POINTS_WITH_NORMALIZED_RECTANGLES'
    assert len(match['rects'])==1
    expected=(200.012,397.924,412.346,407.424)
    assert all(abs(a-b)<1 for a,b in zip(match['rects'][0]['rect_pdf_top_left'],expected))
    for row in match['rects']:
        box=row['rect_normalized']
        assert 0<=box[0]<box[2]<=1 and 0<=box[1]<box[3]<=1
    assert len(sidecar['locator_sha256'])==64
    assert client.get('/api/locators/'+anchor['anchor_id']).json()==sidecar
    assert resolve(client,anchor,doc).json()==sidecar


def test_multi_line_pdf_coordinates_are_per_line(client):
    anchor,doc=create(client,'The 5:2 diet is a popular intermittent energy restriction method of weight management that awaits further evaluation.')
    match=resolve(client,anchor,doc).json()['pdf_locator']
    assert match['page']==1
    assert len(match['rects'])==2
    assert match['rects'][0]['line'] != match['rects'][1]['line']


def test_no_bbox_for_markdown_only_invented_text(client,tmp_path):
    _,doc=create(client)
    pdf=next(tmp_path.glob('DOC-*/source/original.pdf'))
    with pytest.raises(LocatorError, match='PDF_QUOTE_NOT_FOUND'):
        locate_pdf_quote(pdf,'A fabricated scientific statement with no source support is real',doc['source_pdf_sha256'])


def test_wrong_source_sha_and_revision_fail_closed(client):
    anchor,doc=create(client)
    for update in ({'expected_revision':'old-r0'},{'expected_source_pdf_sha256':'00'*32}):
        reply=resolve(client,anchor,doc,**update)
        assert reply.status_code==409 and 'STALE_REVISION' in reply.text
    assert client.get('/api/locators/'+anchor['anchor_id']).status_code==404


def test_generic_short_quote_rejects_exact_locator(client):
    anchor,doc=create(client, 'Three hundred adults with obesity')
    # 5 tokens technically enough; a <5-token quote must not produce exact coordinates.
    unit=next(u for u in doc['units'] if 'Three hundred adults' in u['raw'])
    q='Three hundred adults'
    i=unit['raw'].index(q)
    r=client.post('/api/anchors',json={'unit_id':unit['unit_id'],'quote':q,
        'start_utf16':i,'end_utf16':i+len(q),'expected_revision':doc['revision'],
        'expected_source_markdown_sha256':doc['source_markdown_sha256']})
    assert r.status_code==201
    failure=resolve(client,r.json(),doc)
    assert failure.status_code==409 and 'QUOTE_TOO_SHORT' in failure.text


def test_pdf_page_png_real_original_and_page_boundaries(client):
    r=client.get('/api/pdf/page/1/png?scale=1.1')
    assert r.status_code==200 and r.headers['content-type']=='image/png'
    assert r.content.startswith(b'\x89PNG\r\n\x1a\n')
    assert client.get('/api/pdf/page/0/png').status_code==404
    assert client.get('/api/pdf/page/17/png').status_code==404
    assert client.get('/api/pdf/page/2/png?scale=40').status_code==422


def test_pdf_source_tamper_does_not_return_bbox(client,tmp_path):
    anchor,doc=create(client)
    p=next(tmp_path.glob('DOC-*/source/original.pdf'))
    p.write_bytes(p.read_bytes()+b'\n% malicious change')
    r=resolve(client,anchor,doc)
    assert r.status_code==409 and 'SOURCE_PDF_SHA_MISMATCH' in r.text
    assert client.get('/api/locators/'+anchor['anchor_id']).status_code==404


def test_sidecar_persists_across_app_reload_and_anchor_is_unchanged(client,tmp_path):
    anchor,doc=create(client)
    first=resolve(client,anchor,doc).json()
    new_client=TestClient(make_app(tmp_path))
    assert new_client.get('/api/locators/'+anchor['anchor_id']).json()==first
    assert new_client.get('/api/anchors').json()[0]==anchor


def test_ambiguous_words_refuse_instead_of_guessing(tmp_path):
    f=tmp_path/'same.pdf'
    d=fitz.open(); p=d.new_page();p.insert_text((40,60),'The same exact phrase occurs at least twice here')
    p.insert_text((40,90),'The same exact phrase occurs at least twice here')
    d.save(f);d.close()
    with pytest.raises(LocatorError, match='AMBIGUOUS_MULTIPLE_PDF_MATCHES'):
        locate_pdf_quote(f,'The same exact phrase occurs at least twice here',hashlib.sha256(f.read_bytes()).hexdigest(),1)


def test_evidence_absent_pdf_page_hint_does_not_authorize_bbox(tmp_path):
    f=tmp_path/'mismatch.pdf'
    d=fitz.open();p=d.new_page();p.insert_text((40,80),'Different paper containing totally different facts without the requested statement.')
    d.save(f);d.close()
    with pytest.raises(LocatorError, match='PDF_QUOTE_NOT_FOUND'):
        locate_pdf_quote(f,QUOTE,sha(f.read_bytes()),1)


def test_url_render_does_not_supply_scientific_result(client):
    s=client.get('/').text
    assert 'PDF_PAGE_BBOX' in s
    assert '/api/candidates' not in s
    assert client.get('/api/candidates').status_code==404


def test_tamper_after_locator_freeze_must_reject_replay(client,tmp_path):
    anchor,doc=create(client)
    frozen=resolve(client,anchor,doc)
    assert frozen.status_code==200
    p=next(tmp_path.glob('DOC-*/source/original.pdf'))
    p.write_bytes(p.read_bytes()+b"\n% changed by an attacker")
    assert client.get('/api/locators/'+anchor['anchor_id']).status_code==409
    assert resolve(client,anchor,doc).status_code==409
    assert client.get('/api/pdf/page/1/png').status_code==409
    assert client.get('/api/original.pdf').status_code==409