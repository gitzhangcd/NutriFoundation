"""Generic read-only queue audit on version-projected candidates.
No hidden Critic results read, no old queue edited. A new generator review scope is
only reported, not released. Caller supplies source-only queue paths from its run.
"""
from core import *
from collections import Counter
def audit_queue(rt,run,queue_paths):
    b=rt.b;run=run.resolve();tree=run/"private/typed_partitions"
    manifest=load(run/"private/partition_manifest.json")
    receipts={str(p):sha(p) for p in queue_paths}
    existing=set();review_ids=set();old_routes=Counter()
    for p in queue_paths:
        for q in load(p):
            require(set(q)=={"review_id","source_ref","source_scope","source_native_label","native_kind","question","status"},"REVIEW_SOURCE_ONLY_FIELDS")
            require(q["status"]=="NOT_REVIEWED" and q["review_id"] not in review_ids and q["source_ref"] not in existing,"REVIEW_DUPLICATE_OR_STATUS")
            a=lookup(b.idx,q["source_ref"],"NativeVocabularyRecord")["payload"]
            require(a["native_namespace"]==q["source_scope"] and a["native_label"]==q["source_native_label"] and a["native_kind"]==q["native_kind"],"REVIEW_SOURCE_IDENTITY")
            existing.add(q["source_ref"]);review_ids.add(q["review_id"])
    red=set();high=set();unknown=set();edges=0;flag_counts=Counter();old_red=set()
    for name,x in sorted(manifest.items()):
        if not name.endswith("/AlignmentRecord.jsonl"):continue
        p=tree/name;require(sha(p)==x["sha256"],"REVIEW_CANDIDATE_HASH")
        for o in lines(p):
            v=o["payload"];g=o["governance"]["candidate_risk"];r=v["source_ref"];edges+=1
            if v["review_route"]=="RED":red.add(r)
            if g["legacy_review_route"]=="RED":old_red.add(r)
            if v["review_route"]=="AMBER" and v["ranking_score"]>=0.9:high.add(r)
            if "STATE_DIMENSION_UNRESOLVED" in g["flags"]:unknown.add(r)
            for k in g["flags"]:flag_counts[k]+=1
    require(all(sha(Path(p))==h for p,h in receipts.items()),"REVIEW_INPUT_MUTATION")
    return {"status":"PASS_READ_ONLY_REVIEW_RISK_AUDIT","candidate_edges_checked":edges,"existing_source_queue":len(existing),
            "previous_rule_red_sources":len(old_red),"new_rule_red_sources":len(red),"new_red_sources_already_queued":len(red&existing),
            "new_red_sources_not_queued":len(red-existing),"high_score_amber_sources":len(high),"high_score_amber_sources_not_queued":len(high-existing),
            "state_unresolved_sources":len(unknown),"edge_flags":dict(flag_counts),"source_only_queue_unchanged":True,
            "review_completed_by_this_audit":0,"new_review_queue_released":False,
            "limit":"Persisted candidate risk re-screen only; pre-ranking discarded candidates and independent semantic accuracy remain unmeasured. Existing Gemini review packets untouched."}
