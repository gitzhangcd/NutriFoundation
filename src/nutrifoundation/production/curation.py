"""Execution selection and random audit plans; no scientific truth labels."""
from __future__ import annotations

import random
from collections import defaultdict

from .models import digest


def priority_plan(sources: list[dict],question_gaps: dict[str,int],*,count: int,
                  exploration_count: int=1,seed: int=0) -> dict:
    """Deep extraction by declared evidence questions, with reproducible exploration.

    Input relevance and availability are proposals, not eligibility/quality gold.
    Exact duplicate source IDs are forbidden. Study-family IDs are retained but
    do not discard companion reports or assert independent empirical evidence.
    """
    if count<0 or not 0<=exploration_count<=count or any(v<0 for v in question_gaps.values()):
        raise ValueError("Invalid selection quotas")
    ids=[s['source_id'] for s in sources]
    if len(set(ids))!=len(ids):
        raise ValueError("Duplicate source ID")
    eligible=[s for s in sources if s.get('deep_extraction_available') is True]
    gaps=dict(question_gaps);selected=[]
    pool={s['source_id']:s for s in eligible}
    priority_count=min(count-exploration_count,len(pool))
    for _ in range(priority_count):
        score=lambda s:sum(gaps.get(q,0) for q in set(s.get('question_ids',[])))
        item=sorted(pool.values(),key=lambda s:(-score(s),s['source_id']))[0]
        selected.append({'source_id':item['source_id'],'route':'priority','gap_score':score(item),
            'selection_basis':'declared_question_coverage_not_scientific_quality'})
        for q in set(item.get('question_ids',[])):
            if q in gaps:gaps[q]=max(0,gaps[q]-1)
        del pool[item['source_id']]
    remaining=sorted(pool)
    k=min(exploration_count,count-len(selected),len(remaining))
    random_ids=random.Random(seed).sample(remaining,k)
    for source_id in random_ids:
        selected.append({'source_id':source_id,'route':'random_exploration',
            'conditional_inclusion_probability':k/len(remaining),
            'sampling_frame':'after_priority_selection'})
    report={'policy':'question-gap-priority-v0.1','seed':seed,'requested_count':count,
        'input_sha256':digest(sources),'question_gaps':question_gaps,'selected':selected,
        'unselected':[i for i in ids if i not in {s['source_id'] for s in selected}],
        'not_deep_available':[s['source_id'] for s in sources if s not in eligible],
        'scientific_eligibility_verified':False}
    return report


def stratified_audit_plan(records: list[dict],*,per_stratum: int,seed: int=0) -> dict:
    """Random audit selection independent of model-reported confidence.

    Report inclusion probability within each declared stratum. Missing stratum
    attributes form an explicit unknown group, rather than dropping records.
    """
    if per_stratum<1:
        raise ValueError("Positive audit sample count required")
    ids=[r['record_id'] for r in records]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate audit record ID')
    groups=defaultdict(list)
    axes=('provider','parser_version','source_type','risk')
    for record in records:
        key=tuple(str(record.get(axis,'UNKNOWN')) for axis in axes)
        groups[key].append(record['record_id'])
    rng=random.Random(seed);selected=[]
    for key in sorted(groups):
        frame=sorted(groups[key]);n=min(per_stratum,len(frame))
        for record_id in rng.sample(frame,n):
            selected.append({'record_id':record_id,'stratum':dict(zip(axes,key)),
                'stratum_population':len(frame),'stratum_sample_count':n,'inclusion_probability':n/len(frame)})
    return {'policy':'stratified-random-audit-v0.1','seed':seed,'frame_sha256':digest(records),
        'selected':selected,'expert_reviews_completed':0,'error_rate_estimated':False,
        'limitations':['sampling unit is a declared record, not assumed independent study',
                      'error estimation requires real reference labels and dependency-aware inference']}
