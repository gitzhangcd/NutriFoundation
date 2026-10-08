import copy
import pytest
from source_packet import materialize_baseline,compare_r0_r2,PacketError,digest
from authority import ScientificAdapter
from old_c2_fixtures import fake_authority
from pathlib import Path

def test_r0_r2_identical(adapter):
    r0=materialize_baseline(adapter,workflow='R0')
    r2=materialize_baseline(adapter,workflow='R2_PREAI')
    assert r0==r2 and compare_r0_r2(adapter)==r0
    assert r0['projection_sha256']==r2['projection_sha256']

def test_not_agent_or_r1_source(adapter):
    for arm in ['R1','R2_POSTAI','ADMIN','']:
        with pytest.raises(PacketError,match='ARM_NOT_AUTHORIZED'):materialize_baseline(adapter,workflow=arm)

def test_six_bounded_sources_no_source_expansion(adapter):
    p=compare_r0_r2(adapter)
    assert len(p['sources'])==6
    for r in p['sources']:
        assert r['representation']=='FROZEN_BOUNDED_SOURCE_SUPPORT_NOT_FULLTEXT'
        assert 'fulltext' not in r and not any('agent' in k for k in r)
    assert not p['fulltext_scientifically_verified']

def test_extra_hidden_source_fields_are_not_copied(adapter):
    adapter.source_packet['scientific_sources'][0]['AgentCandidate']='HIDDEN_TEST_ONLY'
    p=materialize_baseline(adapter,workflow='R0')
    assert 'AgentCandidate' not in str(p)

def test_bad_url_rejected(adapter):
    adapter.source_packet['scientific_sources'][0]['canonical_url']='http://malicious.example'
    with pytest.raises(PacketError,match='NON_HTTPS'):materialize_baseline(adapter,workflow='R0')

def test_duplicate_or_missing_source_rejected(adapter):
    adapter.source_packet['scientific_sources'].pop()
    with pytest.raises(PacketError,match='COUNT'):materialize_baseline(adapter,workflow='R2_PREAI')

def test_no_silent_support_rewrite(adapter):
    p=materialize_baseline(adapter,workflow='R0')
    before=p['projection_sha256']
    adapter.source_packet['scientific_sources'][2]['bounded_source_support'][0]+=' new'
    assert materialize_baseline(adapter,workflow='R0')['projection_sha256']!=before

def test_missing_support_rejected(adapter):
    adapter.source_packet['scientific_sources'][3]['bounded_source_support']=[]
    with pytest.raises(PacketError,match='BOUNDED'):materialize_baseline(adapter,workflow='R0')

def test_version_conflict_rejected(adapter):
    adapter.source_packet['version']='v0.1'
    with pytest.raises(PacketError,match='VERSION'):materialize_baseline(adapter,workflow='R0')

def test_stable_digest(adapter):
    p=materialize_baseline(adapter,workflow='R0')
    h=p.pop('projection_sha256')
    assert digest(p)==h
