import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wb_a import AnchorRequest, Store, build_source_package, canonicalize, make_app, read_package, sha, substring_u16, u16len

SRC = Path(__file__).resolve().parents[1] / 'fixtures' / '5_2_diet.AnnotationSourcePackage.v0.1.zip'

@pytest.fixture
def raw():
    return SRC.read_bytes()

@pytest.fixture
def client(tmp_path):
    return TestClient(make_app(tmp_path))


def repack(raw, changes):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        docs = {k: z.read(k) for k in z.namelist() if not k.endswith('/')}
    docs.update(changes)
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for k, v in docs.items(): z.writestr(k, v)
    return b.getvalue()


def test_true_real_pdf_import_and_metadata(client, raw):
    reply = client.post('/api/import', files={'file': ('source.zip', raw, 'application/zip')})
    assert reply.status_code == 200, reply.text
    doc = client.get('/api/document').json()
    assert doc['source_pages'] == 16
    assert doc['unit_count'] > 100
    assert '5:2 diet' in doc['title']
    assert doc['source_status'] == 'STRUCTURED_NOT_SCIENTIFICALLY_VERIFIED'
    assert any(u['type'] == 'TABLE' for u in doc['units'])
    assert any(u['type'] == 'FIGURE' for u in doc['units'])
    assert any(u['pdf_page_hint'] == 7 for u in doc['units'])
    assert client.get('/api/original.pdf').content.startswith(b'%PDF-')
    assert client.get('/assets/fig1_consorte_diagram.jpg').status_code == 200


def test_exact_anchor_replay_persists_across_restart(tmp_path, raw):
    cli = TestClient(make_app(tmp_path))
    assert cli.post('/api/import', files={'file': ('a.zip', raw, 'application/zip')}).status_code == 200
    doc = cli.get('/api/document').json()
    unit = next(u for u in doc['units'] if 'Three hundred adults with obesity' in u['raw'])
    quote = 'Three hundred adults with obesity were randomised'
    start = u16len(unit['raw'].split(quote)[0]); end = start+u16len(quote)
    req = {'unit_id':unit['unit_id'], 'quote':quote,'start_utf16':start,'end_utf16':end,
           'expected_revision':doc['revision'],'expected_source_markdown_sha256':doc['source_markdown_sha256']}
    created = cli.post('/api/anchors', json=req)
    assert created.status_code == 201, created.text
    a = created.json()
    assert a['quote_sha256'] == sha(quote)
    assert a['source_pdf_sha256'] == doc['source_pdf_sha256']
    assert substring_u16(unit['raw'], a['start_utf16'], a['end_utf16']) == a['quote']
    assert a['pdf_page_hint'] == 1
    assert a['pdf_location_kind'] == 'PAGE_HINT_ONLY_NOT_EXACT_BBOX'
    reloaded = TestClient(make_app(tmp_path))
    assert reloaded.get('/api/anchors').json()[0]['anchor_id'] == a['anchor_id']
    assert reloaded.post('/api/anchors',json=req).status_code == 201
    assert len(reloaded.get('/api/anchors').json()) == 1


def test_negative_anchor_cases(client,raw):
    client.post('/api/import', files={'file': ('a.zip', raw, 'application/zip')})
    doc = client.get('/api/document').json()
    unit = next(u for u in doc['units'] if 'Three hundred adults with obesity' in u['raw'])
    quote = 'Three hundred adults with obesity'
    req = {'unit_id':unit['unit_id'], 'quote':quote,'start_utf16':0,'end_utf16':u16len(quote),
           'expected_revision':doc['revision'],'expected_source_markdown_sha256':doc['source_markdown_sha256']}
    for patch, error in [({'expected_revision':'old-r0'},'STALE'),({'expected_source_markdown_sha256':'00'*32},'STALE'),
                         ({'unit_id':'non-existent'},'UNKNOWN'),({'quote':'fabricated'},'QUOTE'),({'end_utf16':999999},'QUOTE')]:
        r=client.post('/api/anchors', json=req|patch)
        assert r.status_code == 409 and error in r.text


def test_corrupt_source_hash_rejected(client,raw):
    damaged = repack(raw, {'document.md':b'# forged scientific results'})
    r = client.post('/api/import',files={'file':('a.zip',damaged,'application/zip')})
    assert r.status_code == 422 and 'MARKDOWN_MANIFEST_MISMATCH' in r.text
    assert client.get('/api/document').json()['status'] == 'NO_IMPORTED_DOCUMENT'


def test_no_pdf_rejected(client, raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files={n:z.read(n) for n in z.namelist() if n!='source/original.pdf'}
    o=io.BytesIO()
    with zipfile.ZipFile(o,'w') as z:
        for n,v in files.items():z.writestr(n,v)
    r=client.post('/api/import', files={'file':('no_pdf.zip',o.getvalue(),'application/zip')})
    assert r.status_code==422 and 'MISSING_PDF' in r.text


def test_zip_slip_rejected(client,raw):
    r=client.post('/api/import', files={'file':('attack.zip',repack(raw,{'../escape.txt':b'hijack'}),'application/zip')})
    assert r.status_code==422 and 'ZIP_INVALID' in r.text


def test_utf16_surrogate_strict():
    raw='A😀B'
    assert u16len(raw)==4
    assert substring_u16(raw,1,3)=='😀'
    with pytest.raises(ValueError, match='SPLIT_UNICODE'):
        substring_u16(raw,1,2)


def test_scientific_boundary_and_static_reader(client,raw):
    assert client.get('/api/health').json()['scientific_status']=='NOT_SCIENTIFICALLY_VERIFIED'
    page=client.get('/')
    assert page.status_code==200 and '结构化阅读' in page.text
    assert '/api/candidates' not in page.text
    assert client.get('/api/candidates').status_code==404


def test_reimport_same_source_idempotent(client,raw):
    for _ in range(2):
        assert client.post('/api/import',files={'file':('source.zip',raw,'application/zip')}).status_code==200
    assert client.get('/api/document').json()['unit_count']>100