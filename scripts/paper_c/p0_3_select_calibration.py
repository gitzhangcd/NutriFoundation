#!/usr/bin/env python3
import json, hashlib
from pathlib import Path
from ortools.sat.python import cp_model

ROOT=Path(__file__).resolve().parents[2]
UNIVERSE=ROOT/"runs/E0.4.3/P0.2.4/Gold100_Augmented_Sampling_Universe_v1.0.json"
GOLD100=ROOT/"runs/E0.4.3/P0.2.4/Gold100_Source_Set_FROZEN_v1.0.json"
OUT=ROOT/"runs/E0.4.3/P0.3"
OUT.mkdir(parents=True,exist_ok=True)

STAGE="E0.4.3-P0.3"
SOURCE_SET_SHA="fdb1189647fe4022411d3ebfd6591da2398135aed398c88ca6f85236678420ad"
SELECTION_KEY=f"{STAGE}|CALIBRATION24|{SOURCE_SET_SHA}"

def csha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()

u=json.loads(UNIVERSE.read_text())
g=json.loads(GOLD100.read_text())

gold_ids={a["candidate_id"] for a in g["assignments"]}
gold_clusters={a.get("study_identity_cluster_id") or a["candidate_id"] for a in g["assignments"]}

candidates=[]
leakage_excluded=[]
for r in u["records"]:
    cid=r["candidate_id"]
    cluster=r.get("study_identity",{}).get("study_identity_cluster_id") or cid
    if cid in gold_ids:
        continue
    if cluster in gold_clusters:
        leakage_excluded.append({"candidate_id":cid,"reason":"shared_StudyIdentityCluster_with_Gold100","cluster":cluster})
        continue
    candidates.append(r)

rounds=["A","B"]
family_quota={
    "primary_interventional":4,
    "primary_observational":2,
    "evidence_synthesis":2,
    "guideline_or_consensus":2,
    "companion_or_secondary":2
}
domain_quota={
    "nutrition_metabolic_cardiometabolic":9,
    "external_biomedical_or_public_health":3
}
challenge_min={
    "numeric_complexity":8,
    "causal_language_risk":2,
    "StudyIdentity_dependency":2,
    "correction_retraction_living_version":2,
    "conflict":2,
    "recommendation_exception":2,
    "temporal_cutoff_sensitive":2
}

model=cp_model.CpModel()
x={}
for rd in rounds:
    for r in candidates:
        x[(rd,r["candidate_id"])]=model.NewBoolVar(f"x__{rd}__{r['candidate_id']}")

# 12 per round.
for rd in rounds:
    model.Add(sum(x[(rd,r["candidate_id"])] for r in candidates)==12)

# Candidate can appear in at most one calibration round.
for r in candidates:
    model.Add(sum(x[(rd,r["candidate_id"])] for rd in rounds)<=1)

# Exact family and domain quotas per round.
for rd in rounds:
    for fam,n in family_quota.items():
        model.Add(sum(x[(rd,r["candidate_id"])] for r in candidates if r.get("source_family")==fam)==n)
    for dom,n in domain_quota.items():
        model.Add(sum(x[(rd,r["candidate_id"])] for r in candidates if r.get("domain")==dom)==n)

# Each round includes exactly one naturally incomplete-source case.
for rd in rounds:
    model.Add(sum(x[(rd,r["candidate_id"])] for r in candidates if r.get("challenge_tags",{}).get("incomplete_source_text"))==1)

# All non-incomplete calibration sources must have frozen full text.
for rd in rounds:
    for r in candidates:
        if not r.get("challenge_tags",{}).get("incomplete_source_text") and r.get("source_text",{}).get("status")!="official_full_text_frozen":
            model.Add(x[(rd,r["candidate_id"])]==0)

# Challenge coverage per round.
for rd in rounds:
    for tag,n in challenge_min.items():
        model.Add(sum(x[(rd,r["candidate_id"])] for r in candidates if r.get("challenge_tags",{}).get(tag))>=n)

# No duplicate StudyIdentityCluster across the full 24.
clusters={}
for r in candidates:
    cluster=r.get("study_identity",{}).get("study_identity_cluster_id") or r["candidate_id"]
    clusters.setdefault(cluster,[]).append(r)
for cluster,rs in clusters.items():
    if len(rs)>1:
        model.Add(sum(x[(rd,r["candidate_id"])] for rd in rounds for r in rs)<=1)

# Deterministic seeded ordering; first feasible solution is the selection.
ranked=[]
for rd in rounds:
    for r in candidates:
        cid=r["candidate_id"]
        rank=int.from_bytes(hashlib.sha256(f"{SELECTION_KEY}|{rd}|{cid}".encode()).digest()[:8],"big")
        ranked.append((rank,rd,cid,x[(rd,cid)]))
ranked.sort(key=lambda z:(z[0],z[1],z[2]))
model.AddDecisionStrategy([z[3] for z in ranked],cp_model.CHOOSE_FIRST,cp_model.SELECT_MAX_VALUE)

solver=cp_model.CpSolver()
solver.parameters.num_search_workers=1
solver.parameters.search_branching=cp_model.FIXED_SEARCH
solver.parameters.stop_after_first_solution=True
solver.parameters.max_time_in_seconds=120
status=solver.Solve(model)
if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
    raise SystemExit(f"CALIBRATION_SELECTION_INFEASIBLE:{solver.StatusName(status)}")

by_id={r["candidate_id"]:r for r in candidates}
selected=[]
for rd in rounds:
    rows=[]
    for r in candidates:
        if solver.Value(x[(rd,r["candidate_id"])]):
            rows.append(r)
    rows.sort(key=lambda r:int.from_bytes(hashlib.sha256(f"{SELECTION_KEY}|{rd}|{r['candidate_id']}".encode()).digest()[:8],"big"))
    for i,r in enumerate(rows,1):
        selected.append({
            "calibration_slot_id":f"CAL-{rd}-{i:02d}",
            "round":rd,
            "mode":"guided_training" if rd=="A" else "blinded_reliability_validation",
            "candidate_id":r["candidate_id"],
            "pmid":r.get("pmid"),"pmcid":r.get("pmcid"),"doi":r.get("doi"),
            "title":r.get("title"),"source_family":r.get("source_family"),"domain":r.get("domain"),
            "study_identity_cluster_id":r.get("study_identity",{}).get("study_identity_cluster_id"),
            "source_text_status":r.get("source_text",{}).get("status"),
            "worker_visible_text_sha256":r.get("source_text",{}).get("worker_visible_text_sha256"),
            "challenge_tags":r.get("challenge_tags",{})
        })

selected_ids=[x["candidate_id"] for x in selected]
selected_clusters=[x["study_identity_cluster_id"] or x["candidate_id"] for x in selected]

def round_count(rd,fn):
    return sum(1 for x in selected if x["round"]==rd and fn(x))

audit={"stage":STAGE,"status":"PASS_CALIBRATION24_SOURCE_SET_FROZEN",
       "selection_key":SELECTION_KEY,
       "input":{"sampling_universe_count":len(u["records"]),"gold100_count":len(gold_ids),
                "leakage_safe_candidate_count":len(candidates),"same_study_leakage_excluded_count":len(leakage_excluded)},
       "solver":{"engine":"OR-Tools CP-SAT","version":"9.14.6206","num_search_workers":1,
                 "search_branching":"FIXED_SEARCH","stop_after_first_solution":True,"status":solver.StatusName(status)},
       "rounds":{},"checks":{}}
for rd in rounds:
    audit["rounds"][rd]={
      "count":round_count(rd,lambda x:True),
      "family":{f:round_count(rd,lambda x,f=f:x["source_family"]==f) for f in family_quota},
      "domain":{d:round_count(rd,lambda x,d=d:x["domain"]==d) for d in domain_quota},
      "challenge":{t:round_count(rd,lambda x,t=t:x["challenge_tags"].get(t)) for t in list(challenge_min)+["incomplete_source_text"]},
      "full_text_frozen":round_count(rd,lambda x:x["source_text_status"]=="official_full_text_frozen"),
      "incomplete_source":round_count(rd,lambda x:x["challenge_tags"].get("incomplete_source_text"))
    }

audit["checks"]={
  "selected_24":len(selected)==24,
  "unique_candidates":len(selected_ids)==len(set(selected_ids)),
  "unique_study_identity_clusters":len(selected_clusters)==len(set(selected_clusters)),
  "no_Gold100_source_overlap":not any(x in gold_ids for x in selected_ids),
  "no_Gold100_StudyIdentity_overlap":not any((x["study_identity_cluster_id"] or x["candidate_id"]) in gold_clusters for x in selected),
  "round_A_count_12":audit["rounds"]["A"]["count"]==12,
  "round_B_count_12":audit["rounds"]["B"]["count"]==12,
  "round_family_quotas":all(audit["rounds"][rd]["family"]==family_quota for rd in rounds),
  "round_domain_quotas":all(audit["rounds"][rd]["domain"]==domain_quota for rd in rounds),
  "one_incomplete_per_round":all(audit["rounds"][rd]["incomplete_source"]==1 for rd in rounds),
  "challenge_minima":all(audit["rounds"][rd]["challenge"][t]>=n for rd in rounds for t,n in challenge_min.items()),
  "non_incomplete_have_full_text":all(x["source_text_status"]=="official_full_text_frozen" or x["challenge_tags"].get("incomplete_source_text") for x in selected)
}
if not all(audit["checks"].values()):
    raise SystemExit("CALIBRATION_POST_SELECTION_AUDIT_FAILED:"+json.dumps(audit["checks"],sort_keys=True))

source_set={
  "corpus":"Paper_C_Calibration24",
  "version":"v1.0",
  "stage":STAGE,
  "status":"FROZEN_NON_GOLD100_CALIBRATION_SOURCE_SET",
  "gold100_source_set_sha256":SOURCE_SET_SHA,
  "selection_key":SELECTION_KEY,
  "design":{
    "round_A":{"n":12,"mode":"guided_training_after_independent_first_pass"},
    "round_B":{"n":12,"mode":"blinded_reliability_gate"},
    "family_quota_per_round":family_quota,
    "domain_quota_per_round":domain_quota,
    "challenge_minima_per_round":challenge_min,
    "incomplete_source_per_round":1,
    "gold100_SourceArtifact_overlap":0,
    "gold100_StudyIdentityCluster_overlap":0
  },
  "assignments":selected
}
source_set_sha=csha(source_set)
source_set["calibration24_source_set_sha256"]=source_set_sha
audit["calibration24_source_set_sha256"]=source_set_sha

(OUT/"Calibration24_Source_Set_FROZEN_v1.0.json").write_text(json.dumps(source_set,indent=2,ensure_ascii=False)+"\n")
(OUT/"Calibration24_Source_Set_SHA256_v1.0.txt").write_text(source_set_sha+"\n")
(OUT/"Calibration24_Selection_Audit_v1.0.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n")
(OUT/"Calibration12A_Training_Manifest_v1.0.json").write_text(json.dumps({"round":"A","mode":"guided_training_after_independent_first_pass","records":[x for x in selected if x["round"]=="A"]},indent=2,ensure_ascii=False)+"\n")
(OUT/"Calibration12B_Reliability_Manifest_v1.0.json").write_text(json.dumps({"round":"B","mode":"blinded_reliability_gate","records":[x for x in selected if x["round"]=="B"]},indent=2,ensure_ascii=False)+"\n")
print(json.dumps(audit,indent=2))
