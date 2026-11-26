"""C2 development-only admission on independently rederived risk decisions.
Never use caller-submitted flags as authority. This module gates projected candidates;
it cannot authorize scientific mappings or access to private review opinions.
"""
from collections import defaultdict
from risk import decide
from core import require,canon,ref
PURPOSES={"CURATION_INSPECT","DEVELOPMENT_CONCEPT_REVIEW"}
DENIED={"EQUIVALENCE","NUTRIENT_TRANSFER","PHYSICAL_IDENTITY","TRAIN","LOCKED_EVALUATION","GOLD","NUTRIENT_CALCULATION","CLINICAL_DECISION","MAPPING_RELEASE","SCIENTIFIC_RELEASE"}
def expected_disposition(payload,source,target,policy,scope_status,upstream_red):
    a=source["payload"]
    if target["kind"]=="ScopeAssessment":
        t=target["payload"];label=t["native_label"];grain="ONTOLOGY_TYPED_EXTENSION_CATEGORY"
    else:
        t=target["payload"];label=t["native_label"];grain=t["native_kind"]
    return decide({"label":a["native_label"],"grain":a["native_kind"]},{"label":label,"grain":grain},policy,scope_status,upstream_red)
def verify_decision(payload,source,target,policy,scope_status,upstream_red):
    d=expected_disposition(payload,source,target,policy,scope_status,upstream_red)
    require(all(canon(payload[k])==canon(v) for k,v in d.items()),"RISK_RECOMPUTE_MISMATCH")
    return d
def shortlist(rows,per_scope):
    groups=defaultdict(list)
    for o in rows:
        if o["payload"]["concept_review_eligible"]:groups[o["payload"]["target_scope"]].append(o)
    out=[]
    for _,rr in sorted(groups.items()):
        out.extend(sorted(rr,key=lambda o:(o["payload"]["rank_in_frozen_pool"] or 99999,o["object_id"]))[:per_scope])
    return [ref(o) for o in out]
def verify_query(payload,rows,per_scope):
    rs=shortlist(rows,per_scope);n=sum(o["payload"]["concept_review_eligible"] for o in rows)
    require(payload["pool_count"]==len(rows) and payload["eligible_count"]==n and payload["shortlist_refs"]==rs,"QUERY_RECOMPUTE_MISMATCH")
    expected="DEVELOPMENT_REVIEW_AVAILABLE" if rs else "ABSTAIN_NO_ELIGIBLE_CANDIDATE_IN_RETRIEVED_POOL"
    require(payload["query_status"]==expected,"QUERY_RECOMPUTE_ABSTENTION")
    return rs
class DevelopmentGate:
    def __init__(self,verified_records,verified_queries):
        self.records=verified_records;self.queries=verified_queries
        self.selected={r for q in verified_queries.values() for r in q["payload"]["shortlist_refs"]}
    def request(self,purpose,candidate_ref):
        if purpose not in PURPOSES:return {"decision":"HOLD","reason":"PURPOSE_NOT_AUTHORIZED"}
        if candidate_ref not in self.records:return {"decision":"HOLD","reason":"UNVERIFIED_RECORD"}
        o=self.records[candidate_ref]
        if purpose=="CURATION_INSPECT":return {"decision":"ALLOW","reason":"CURATION_ONLY"}
        p=o["payload"]
        if candidate_ref in self.selected and p["concept_review_eligible"]:return {"decision":"ALLOW","reason":"DEVELOPMENT_REVIEW_ONLY"}
        return {"decision":"HOLD","reason":p["disposition"] if not p["concept_review_eligible"] else "NOT_IN_DEVELOPMENT_SHORTLIST"}
