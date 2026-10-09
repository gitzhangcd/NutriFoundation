"""Private synthetic full-unit translation storage and immutable exposure version."""
import json
from pathlib import Path
import pytest
from conftest import h, bind
from test_secure_reader import scope,setup_r2
from translation_prepare import prepare

def test_private_full_unit_sidecar_and_version_pin(env):
    c,keys,app=env
    doc,headers=setup_r2(env)
    unit=next(u for u in doc['units'] if u['type']=='PARAGRAPH')
    private=app.state.source_store.root.parent/'translation_sidecars'
    private.mkdir()
    path=private/(doc['document_id']+'.json')
    pack=prepare(doc,{unit['unit_id']:'这是一份仅用于测试的中文翻译，未经科学审校。'},'V12-SYNTHETIC-FULL-UNIT')
    path.write_text(json.dumps(pack,ensure_ascii=False))
    url=scope()+'/translations'
    res=c.get(url,headers=headers)
    assert res.status_code==200,res.text
    obj=res.json()
    assert obj['coverage_counts']['fully_translated_units']==1
    assert obj['coverage_counts']['untranslated_units']==doc['unit_count']-1
    assert obj['items'][0]['alignment_level']=='FULL_UNIT'
    assert obj['delivery_audit']=='RECORDED_NOT_PROOF_OF_HUMAN_VIEWING'
    # Same version cannot be silently replaced after any projection delivery.
    pack2=prepare(doc,{unit['unit_id']:'不同内容，不可默默替换。'},'V12-SYNTHETIC-FULL-UNIT')
    path.write_text(json.dumps(pack2,ensure_ascii=False))
    denied=c.get(url,headers=headers)
    assert denied.status_code==409
    assert denied.json()['detail']['code']=='TRANSLATION_VERSION_CHANGED_AFTER_EXPOSURE'

def test_corrupt_private_pack_fail_closed_not_demo_fallback(env):
    c,keys,app=env
    doc,headers=setup_r2(env)
    private=app.state.source_store.root.parent/'translation_sidecars'
    private.mkdir()
    path=private/(doc['document_id']+'.json')
    pack=prepare(doc,{doc['units'][0]['unit_id']:'合成译文'},'V12-BAD-SOURCE')
    pack['source_pdf_sha256']='source-was-mutated'
    path.write_text(json.dumps(pack,ensure_ascii=False))
    r=c.get(scope()+'/translations',headers=headers)
    assert r.status_code==409
    assert r.json()['detail']['code']=='TRANSLATION_SIDECAR_INVALID'
    # R1 must not receive source text from the private sidecar either.
    bind(env,'SYN-R1','SYN-EXPERT-B')
    assert c.get(scope('SYN-R1')+'/translations',headers=h(keys,'SYN-EXPERT-B')).status_code==404

def test_unknown_unit_rejected_offline(env):
    doc,_=setup_r2(env)
    with pytest.raises(ValueError,match='UNKNOWN_TRANSLATED_UNIT'):
        prepare(doc,{'UNAUTHORIZED_UNIT':'非法'},'V12-BAD-UNIT')
