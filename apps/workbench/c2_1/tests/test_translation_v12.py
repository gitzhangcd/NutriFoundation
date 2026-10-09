"""P1.2: bilingual manifest scientific-honesty, auth and audit kill tests."""
import copy
import sqlite3
import pytest

from conftest import h, bind
from test_secure_reader import scope, setup_r2
from bilingual import projection
from translation_contract import SCHEMA, validate, numerical_warnings, utf16_slice

KEYS = ("schema_version", "source_document_id", "source_revision",
        "source_markdown_sha256", "source_pdf_sha256", "translation_version",
        "target_language", "policy", "items")

def raw_pack(doc):
    p = projection(doc)
    return {k: copy.deepcopy(p[k]) for k in KEYS}

def test_versioned_manifest_and_coverage_truthfulness(env):
    c, keys, _ = env
    doc, headers = setup_r2(env)
    pack=raw_pack(doc)
    assert pack['schema_version']==SCHEMA
    result=validate(doc,pack)
    assert result['coverage']=='PARTIAL_UNVERIFIED'
    assert result['coverage_counts']['fully_translated_units']==0
    assert result['coverage_counts']['untranslated_units']==doc['unit_count']
    assert result['scientific_capture'] is False
    assert result['items']
    assert all(x['review_receipt_ref'] is None for x in result['items'])
    assert c.get(scope()+'/translations',headers=headers).json()['delivery_audit']=='RECORDED_NOT_PROOF_OF_HUMAN_VIEWING'

@pytest.mark.parametrize('key', ['source_revision','source_markdown_sha256','source_pdf_sha256','source_document_id'])
def test_bad_revision_or_source_digest_fails_closed(env,key):
    doc, _ = setup_r2(env)
    pack=raw_pack(doc)
    pack[key]='bad'
    with pytest.raises(ValueError,match='TRANSLATION_SOURCE_VERSION_MISMATCH'):
        validate(doc,pack)

def test_false_full_unit_and_self_claimed_review_denied(env):
    doc,_=setup_r2(env)
    pack=raw_pack(doc)
    assert pack['items']
    pack['items'][0]['alignment_level']='FULL_UNIT'
    with pytest.raises(ValueError,match='TRANSLATION_FALSE_FULL_UNIT'):
        validate(doc,pack)
    pack=raw_pack(doc)
    pack['items'][0]['review_receipt_ref']='SELF_ASSERTED_PASS'
    with pytest.raises(ValueError,match='TRANSLATION_REVIEW_CLAIM_NOT_VERIFIED'):
        validate(doc,pack)

def test_source_span_and_duplicate_tampering_blocked(env):
    doc,_=setup_r2(env)
    pack=raw_pack(doc)
    pack['items'][0]['source_start_utf16']+=1
    with pytest.raises(ValueError,match='TRANSLATION_ORIGINAL_SPAN_MISMATCH'):
        validate(doc,pack)
    pack=raw_pack(doc)
    pack['items'].append(copy.deepcopy(pack['items'][0]))
    with pytest.raises(ValueError,match='TRANSLATION_DUPLICATE_SPAN'):
        validate(doc,pack)

def test_utf16_non_bmp_and_numeric_warning_are_not_qualified():
    assert utf16_slice('a🙂b',1,3)=='🙂'
    with pytest.raises(ValueError,match='INVALID_UTF16_BOUNDARY'):
        utf16_slice('a🙂b',1,2)
    assert numerical_warnings('RR 0.75, p 0.03','RR 0.75，p 0.05')
    assert numerical_warnings('RR 0.75','RR 0.75')==[]

def test_delivery_is_audited_once_append_only_and_not_r1(env):
    c,keys,app=env
    doc,headers=setup_r2(env)
    url=scope()+'/translations'
    r=c.get(url,headers=headers)
    assert r.status_code==200
    assert c.get(url,headers=headers).status_code==200
    with app.state.controller.conn() as db:
        row=db.execute('SELECT * FROM translation_projections_served WHERE task=?',('SYN-R2',)).fetchall()
        assert len(row)==1
        with pytest.raises(sqlite3.IntegrityError,match='IMMUTABLE_TRANSLATION_EXPOSURE'):
            db.execute('DELETE FROM translation_projections_served WHERE task=?',('SYN-R2',))
    audited=c.get('/v1/tasks/SYN-R2/audit',headers=h(keys,'SYN-AUDITOR')).json()['events']
    assert len([x for x in audited if x['event']=='TRANSLATION_PROJECTION_DELIVERED'])==1
    bind(env,'SYN-R1','SYN-EXPERT-B')
    assert c.get(scope('SYN-R1')+'/translations',headers=h(keys,'SYN-EXPERT-B')).status_code==404
