import pytest
from nutrifoundation.production.curation import priority_plan,stratified_audit_plan


def test_priority_gap_coverage_and_exploration_are_separate():
    sources=[{'source_id':str(i),'question_ids':['q1' if i<3 else 'q2'],
        'deep_extraction_available':True,'study_family':'same-cohort-unresolved'} for i in range(6)]
    plan=priority_plan(sources,{'q1':3,'q2':1},count=3,exploration_count=1,seed=4)
    assert plan==priority_plan(sources,{'q1':3,'q2':1},count=3,exploration_count=1,seed=4)
    assert [x['source_id'] for x in plan['selected'][:2]]==['0','1']
    assert plan['selected'][2]['route']=='random_exploration'
    assert plan['selected'][2]['conditional_inclusion_probability']==.25
    assert not plan['scientific_eligibility_verified']


def test_missing_raw_and_duplicates_are_not_silently_selected():
    sources=[{'source_id':'abstract-only','deep_extraction_available':False}]
    assert priority_plan(sources,{},count=1)['selected']==[]
    with pytest.raises(ValueError,match='Duplicate'):
        priority_plan(sources+sources,{},count=1)


def test_random_audit_preserves_strata_probabilities_and_unknowns():
    records=[{'record_id':str(i),'provider':'PMC','parser_version':'v1','source_type':'cohort','risk':'low','confidence':1} for i in range(5)]
    records.append({'record_id':'unknown','confidence':0})
    plan=stratified_audit_plan(records,per_stratum=2,seed=1)
    assert len(plan['selected'])==3
    assert sum(r['inclusion_probability']==.4 for r in plan['selected'])==2
    assert any(r['record_id']=='unknown' for r in plan['selected'])
    assert plan['expert_reviews_completed']==0
    assert not plan['error_rate_estimated']
