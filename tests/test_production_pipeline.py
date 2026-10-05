from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta,date

import pytest

from nutrifoundation.production.acquisition import SnapshotService
from nutrifoundation.production.models import (FieldAssertion,ResultDraft,PrefillDraft,IndependentReadout,
    ReviewDecision,digest,now)
from nutrifoundation.production.parsing import parse_document,replay_anchor
from nutrifoundation.production.prefill import PrefillService
from nutrifoundation.production.review import ReviewService
from nutrifoundation.production.verification import verify_draft
from nutrifoundation.production.store import ProductionStore
from nutrifoundation.production.jobs import JobQueue
from nutrifoundation.production.release import ReleaseService,cutoff_eligibility


@pytest.fixture
def pipeline(tmp_path):
    store=ProductionStore(tmp_path/'d0.db')
    svc=SnapshotService(store,tmp_path/'blobs')
    data=b'Adults: Model 1 OR 1.38 for diabetes; Model 2 OR 1.02. Dose 5 mg.\n'
    snap=svc.ingest(data,source_id='s',source_version='v1',format='TEXT',content_scope='fulltext',license='synthetic',origin='test')
    parsed=parse_document(snap,data)
    store.put('parsed',parsed.parsed_id,parsed)
    store.depend(parsed.parsed_id,(snap.snapshot_id,))
    task=PrefillService(store).prepare(snap,parsed,authority_sha256='a'*64,extractor_id='extractor',model_version='synthetic',prompt_version='v1',coverage_request='one result')
    assertion=lambda value:FieldAssertion(state='PRESENT',source_value=value,anchor_refs=(parsed.anchors[0].anchor_id,))
    result=ResultDraft(result_id='r1',object_type='EvidenceUnit',fields={'population':assertion('Adults'),'outcome':assertion('diabetes'),'effect_value':assertion('OR 1.38'),'model':assertion('Model 1')})
    draft=PrefillDraft(draft_id='d1',task=task,task_sha256=digest(task),results=(result,),coverage_completed='one result',coverage_omissions=())
    return store,svc,snap,parsed,task,draft


@pytest.mark.parametrize('field,value,anchor',[
    ('model','Model 9',None),('outcome','cancer',None),
    ('effect_value','Model 2 OR 1.38',None),('effect_value','5 g',None),
    ('effect_value','OR 1.38','invented-anchor'),
])
def test_previous_false_passes_are_not_accepted(pipeline,field,value,anchor):
    store,svc,snap,parsed,task,draft=pipeline
    fields=dict(draft.results[0].fields)
    fields[field]=FieldAssertion(state='PRESENT',source_value=value,anchor_refs=(anchor or parsed.anchors[0].anchor_id,))
    changed=draft.model_copy(update={'results':(draft.results[0].model_copy(update={'fields':fields}),)})
    report=verify_draft(changed,parsed)
    assert any(c.field==field and c.status=='FAIL' for c in report.checks)


def test_causal_normalization_and_missing_readout_are_unresolved(pipeline):
    *_,parsed,task,draft=pipeline
    fields=dict(draft.results[0].fields)
    fields['effect_value']=fields['effect_value'].model_copy(update={'normalized_value':'causes diabetes; OR 1.38'})
    changed=draft.model_copy(update={'results':(draft.results[0].model_copy(update={'fields':fields}),)})
    report=verify_draft(changed,parsed)
    assert any(c.rule=='causal_scope' and c.status=='UNRESOLVED' for c in report.checks)
    assert report.independent_evidence_status=='NOT_PROVEN'


def test_snapshot_idempotence_events_and_corrupt_blob_rejected(pipeline):
    store,svc,snap,parsed,task,draft=pipeline
    _,data=svc.read(snap.snapshot_id)
    assert svc.ingest(data,source_id='s',source_version='v1',format='TEXT',content_scope='fulltext',license='synthetic',origin='second')==snap
    with store.transaction() as con:
        assert con.execute('SELECT COUNT(*) FROM d0_event').fetchone()[0]==2
    from pathlib import Path
    Path(snap.blob_path).write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='integrity'):
        PrefillService(store).ingest(draft)


def test_multi_result_and_unknowns_stay_staging(pipeline):
    store,svc,snap,parsed,task,draft=pipeline
    second=draft.results[0].model_copy(update={'result_id':'r2','issues':('source OR/P conflict',)})
    multi=draft.model_copy(update={'results':draft.results+(second,)})
    report=PrefillService(store).ingest(multi)
    assert len(store.get('draft','d1')['results'])==2
    assert any(c.rule=='source_issue' for c in report.checks)
    gates=ReleaseService(store).promotion_gates('d1',report.report_id,use='canonical')
    assert not gates['allowed']
    assert 'human_or_h0_release_authority_not_qualified' in gates['blocked_gates']
    with pytest.raises(ValueError,match='Immutable'):
        PrefillService(store).ingest(draft)


def test_independent_readout_bound_and_exposure_cannot_pass(pipeline):
    store,svc,snap,parsed,task,draft=pipeline
    readout=IndependentReadout(readout_id='read1',task_sha256=digest(task),snapshot_id=snap.snapshot_id,
        parsed_sha256=digest(parsed),worker_id='verifier',session_id='separate-execution-attestation',
        input_scope='source_only',candidate_exposed=False,completed_at=now(),locked_at=now(),results=draft.results)
    report=verify_draft(draft,parsed,readout)
    assert report.independent_evidence_status=='ATTESTED_EXECUTION_ONLY'
    exposed=verify_draft(draft,parsed,readout.model_copy(update={'candidate_exposed':True}))
    assert exposed.independent_evidence_status=='NOT_PROVEN'
    assert any(c.rule=='readout_binding' and c.status=='FAIL' for c in exposed.checks)
    wrong=readout.model_copy(update={'worker_id':'extractor'})
    assert verify_draft(draft,parsed,wrong).independent_evidence_status=='NOT_PROVEN'


def test_review_projections_and_immutable_patch(pipeline):
    store,svc,snap,parsed,task,draft=pipeline
    old_report=PrefillService(store).ingest(draft)
    reviews=ReviewService(store)
    a=reviews.create('d1',reviewer_id='synthetic-a',mode='source_only')
    exported=reviews.export(a['review_task_id'])
    assert not {'prefill','anchors','checks','issues','results'}&exported.keys()
    assisted=reviews.create('d1',reviewer_id='synthetic-b',mode='assisted')
    assert reviews.export(assisted['review_task_id'])['prefill']['results']
    patch=draft.results[0].fields['model'].model_copy(update={'source_value':'Model 2'})
    decision=ReviewDecision(decision_id='dec1',review_task_id=assisted['review_task_id'],draft_sha256=digest(draft),
        mode='assisted',reviewer_id='synthetic-b',submitted_at=now(),decision='REVISE',
        patches={'r1/model':patch},reasons={'r1/model':'synthetic workflow check'})
    reviews.submit(decision)
    changed=reviews.revised_draft('dec1','d2')
    assert store.get('draft','d1')['results'][0]['fields']['model']['source_value']=='Model 1'
    assert changed.results[0].fields['model'].source_value=='Model 2'
    assert 'verification_candidate_version_mismatch' in ReleaseService(store).promotion_gates('d2',old_report.report_id,use='canonical')['blocked_gates']
    with pytest.raises(ValueError,match='Immutable'):
        reviews.submit(decision.model_copy(update={'decision':'CONFIRM'}))
    with pytest.raises(ValueError,match='mode mismatch'):
        reviews.submit(decision.model_copy(update={'mode':'source_only'}))


def test_jats_cell_anchors_preserve_headers_footnotes_and_version(pipeline):
    store,svc,*_=pipeline
    xml=b'<article><table-wrap id="t1"><caption>Diabetes OR</caption><table><tr><th>Diet</th><th colspan="2">Model 2</th></tr><tr><td>Western</td><td>1.38</td></tr></table><table-wrap-foot>P=.053</table-wrap-foot></table-wrap></article>'
    snap=svc.ingest(xml,source_id='s',source_version='jats1',format='JATS_XML',content_scope='fulltext',license='synthetic',origin='test')
    parsed=parse_document(snap,xml)
    anchor=next(a for a in parsed.anchors if a.exact_text=='1.38')
    assert anchor.context['headers']==[['Diet','Model 2']]
    assert anchor.context['footnotes']=='P=.053'
    assert anchor.context['column_semantics']=='not_inferred'
    assert replay_anchor(snap,xml,anchor)=='1.38'
    with pytest.raises(ValueError,match='mismatch'):
        replay_anchor(snap,xml,anchor.model_copy(update={'exact_text':'1.36'}))


def test_equal_numeric_cells_keep_table_row_identity(pipeline):
    store,svc,*_=pipeline
    xml=b'<article><table-wrap id="t1"><table><tr><td>Model 1</td><td>1.38</td></tr><tr><td>Model 2</td><td>1.38</td></tr></table></table-wrap><table-wrap id="t2"><table><tr><td>Other outcome</td><td>1.38</td></tr></table></table-wrap></article>'
    snap=svc.ingest(xml,source_id='s',source_version='duplicates',format='JATS_XML',content_scope='fulltext',license='synthetic',origin='test')
    anchors=[a for a in parse_document(snap,xml).anchors if a.exact_text=='1.38']
    assert len(anchors)==3
    assert len({a.anchor_id for a in anchors})==3
    assert {(a.context['table_id'],a.context['row'],a.context['cell']) for a in anchors}=={('t1',0,1),('t1',1,1),('t2',0,1)}


def test_queue_deduplicates_claims_and_rejects_stale_worker(pipeline):
    store,*_=pipeline
    q=JobQueue(store)
    k=q.enqueue({'kind':'prefill','task_id':'t'},instant=100)
    assert q.enqueue({'kind':'prefill','task_id':'t'},instant=100)==k
    with ThreadPoolExecutor(max_workers=4) as pool:
        claimed=list(pool.map(lambda _:q.claim(instant=101,lease_seconds=10),range(4)))
    old=next(j for j in claimed if j)
    assert sum(j is not None for j in claimed)==1
    new=q.claim(instant=112,lease_seconds=10)
    with pytest.raises(ValueError,match='lease'):
        q.complete(old,{'draft':'old'},instant=113)
    q.complete(new,{'draft':'new'},instant=113)
    assert q.summary()=={'succeeded':1}
    assert store.get('job_result',k)=={'draft':'new'}


def test_queue_retries_and_permanent_semantic_blocks(pipeline):
    store,*_=pipeline;q=JobQueue(store)
    q.enqueue({'n':1},instant=0,max_attempts=2)
    j=q.claim(instant=1);q.fail(j,'timeout',retryable=True,instant=2)
    assert q.claim(instant=3) is None
    j=q.claim(instant=5);q.fail(j,'missing_source_unit',retryable=False,instant=6)
    assert q.claim(instant=1000) is None
    assert q.summary()=={'blocked':1}
    assert q.reserve_request('shared',requests_per_second=3,instant=100)==0
    assert q.reserve_request('shared',requests_per_second=3,instant=100)==pytest.approx(1/3)


def test_invalidation_and_temporal_release(pipeline):
    store,svc,snap,parsed,task,draft=pipeline
    before=now()-timedelta(seconds=1)
    PrefillService(store).ingest(draft)
    releases=ReleaseService(store)
    with pytest.raises(ValueError,match='not in system'):
        releases.staging_release(('d1',),release_id='old',cutoff_mode='SYSTEM_FAITHFUL',cutoff=before)
    released=releases.staging_release(('d1',),release_id='new',cutoff_mode='SYSTEM_FAITHFUL',cutoff=now())
    assert released['status']=='STAGING_ONLY'
    with pytest.raises(ValueError,match='deferred'):
        releases.staging_release(('d1',),release_id='content',cutoff_mode='CONTENT_FAITHFUL',cutoff=now())
    with pytest.raises(ValueError,match='cycle'):
        store.depend(snap.snapshot_id,('d1',))
    affected=store.invalidate(snap.snapshot_id,'synthetic correction')
    assert {'d1',task.task_id,parsed.parsed_id,'new'}.issubset(affected)
    assert store.get('release','new')==released  # history remains immutable
    with pytest.raises(ValueError,match='invalidated'):
        PrefillService(store).ingest(draft)
    with pytest.raises(ValueError,match='invalidated'):
        store.depend('new-child',('d1',))


def test_observation_cannot_become_evidence(pipeline):
    store,svc,*_=pipeline
    snap=svc.ingest(b'SEQN=1',source_id='person',source_version='cycle',format='TEXT',content_scope='observation',license='synthetic',origin='test',lane='observation')
    parsed=parse_document(snap,b'SEQN=1')
    with pytest.raises(ValueError,match='separate'):
        PrefillService(store).prepare(snap,parsed,authority_sha256='a'*64,extractor_id='e',model_version='v',prompt_version='p',coverage_request='wrong lane')


def test_cutoff_interval_does_not_invent_date():
    assert cutoff_eligibility(date(2023,1,1),date(2023,12,31),date(2023,6,1))=='UNRESOLVED'
    assert cutoff_eligibility(date(2023,1,1),date(2023,12,31),date(2024,1,1))=='ELIGIBLE'
