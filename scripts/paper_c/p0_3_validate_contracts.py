#!/usr/bin/env python3
import json, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
P03=ROOT/"paper_c/P0.3/P0.3_Calibration_Protocol_v1.0.json"
WB=ROOT/"paper_c/P0.3/Annotation_Workbench_Contract_v1.0.json"
RG=ROOT/"paper_c/P0.3/Reliability_Gate_Contract_v1.0.json"
CS=ROOT/"paper_c/P0.3/Calibration_Annotation_Record_Schema_v1.0.json"
CAL=ROOT/"runs/E0.4.3/P0.3/Calibration24_Source_Set_FROZEN_v1.0.json"
CALSHA=ROOT/"runs/E0.4.3/P0.3/Calibration24_Source_Set_SHA256_v1.0.txt"
GOLD=ROOT/"runs/E0.4.3/P0.2.4/Gold100_Source_Set_FROZEN_v1.0.json"
GOV=ROOT/"paper_c/P0.1/Gold100_Gold_Governance_Contract_v1.0.json"
OUT=ROOT/"runs/E0.4.3/P0.3"
OUT.mkdir(parents=True,exist_ok=True)

def load(p): return json.loads(p.read_text())
def csha(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()

p03,wb,rg,cs,cal,gold,gov=map(load,[P03,WB,RG,CS,CAL,GOLD,GOV])

tmp=dict(cal)
embedded=tmp.pop("calibration24_source_set_sha256",None)
expected=CALSHA.read_text().strip()
actual=csha(tmp)

gold_ids={x["candidate_id"] for x in gold["assignments"]}
gold_clusters={x.get("study_identity_cluster_id") or x["candidate_id"] for x in gold["assignments"]}
cal_ids=[x["candidate_id"] for x in cal["assignments"]]
cal_clusters=[x.get("study_identity_cluster_id") or x["candidate_id"] for x in cal["assignments"]]

transitions={tuple(x[:2]):x[2:] for x in wb["state_machine"]["transitions"]}

checks={
  "calibration_hash_matches": actual==expected==embedded,
  "protocol_parent_calibration_hash_matches": p03["parent"]["calibration24_source_set_sha256"]==expected,
  "calibration_n_24": len(cal["assignments"])==24,
  "round_A_n_12": sum(1 for x in cal["assignments"] if x["round"]=="A")==12,
  "round_B_n_12": sum(1 for x in cal["assignments"] if x["round"]=="B")==12,
  "calibration_unique_sources": len(cal_ids)==len(set(cal_ids)),
  "calibration_unique_clusters": len(cal_clusters)==len(set(cal_clusters)),
  "no_Gold100_source_overlap": not bool(set(cal_ids)&gold_ids),
  "no_Gold100_cluster_overlap": not bool(set(cal_clusters)&gold_clusters),
  "Gold100_hidden_during_P0_3": wb["isolation"]["Gold100_hidden_during_P0_3"] is True,
  "cross_annotator_visibility_blocked": wb["isolation"]["annotator_A_cannot_read_B_before_both_locks"] and wb["isolation"]["annotator_B_cannot_read_A_before_both_locks"],
  "locked_record_immutable": wb["state_machine"]["edit_after_FIRST_PASS_LOCKED"]=="PROHIBITED" and wb["first_pass_lock"]["immutable"] is True,
  "RoundB_metric_before_discussion": ("DIFF_ELIGIBLE","METRIC_FROZEN") in transitions and ("METRIC_FROZEN","DISCUSSION_ELIGIBLE") in transitions,
  "RoundA_discussion_after_lock": ("DIFF_ELIGIBLE","DISCUSSION_ELIGIBLE") in transitions,
  "AB_outputs_prohibited": wb["isolation"]["AB_outputs_prohibited"] is True,
  "record_hash_required": wb["export"]["record_hash_required"] is True,
  "source_hash_required": wb["export"]["source_hash_required"] is True,
  "fresh_holdout_after_RoundB_failure": any("fresh" in x.lower() or "unused" in x.lower() for x in p03["failure_policy"]["if_round_B_fails_any_primary_gate"]),
  "Gold100_annotation_prohibited_before_pass": p03["failure_policy"]["Gold100_annotation_before_pass"]=="PROHIBITED",
  "schema_has_independence_attestation": "independence_attestation" in cs["fields"],
  "schema_has_first_pass_lock": "first_pass_lock" in cs["fields"]
}

# Threshold equivalence to P0.1 authority.
p01=gov["agreement_gates"]["corpus_level_before_Gold100_freeze"]
checks["critical_AC1_threshold_inherited"]=rg["primary_thresholds"]["critical_categorical_Gwet_AC1"]==float(p01["critical_categorical_Gwet_AC1"].replace(">=",""))
checks["ordinal_threshold_inherited"]=rg["primary_thresholds"]["ordinal_weighted_agreement"]==float(p01["ordinal_weighted_agreement"].replace(">=",""))
checks["numeric_threshold_inherited"]=rg["primary_thresholds"]["numeric_agreement"]==float(p01["numeric_exact_or_predeclared_tolerance_agreement"].replace(">=",""))
checks["span_F1_threshold_inherited"]=rg["primary_thresholds"]["source_span_token_F1"]==float(p01["source_span_token_F1"].replace(">=",""))

# Text availability profile.
for rd in ("A","B"):
    rows=[x for x in cal["assignments"] if x["round"]==rd]
    checks[f"{rd}_exactly_one_incomplete"]=sum(1 for x in rows if x["challenge_tags"].get("incomplete_source_text"))==1
    checks[f"{rd}_other_sources_full_text"]=all(x["source_text_status"]=="official_full_text_frozen" or x["challenge_tags"].get("incomplete_source_text") for x in rows)

report={
 "stage":"E0.4.3-P0.3",
 "artifact":"Workbench_Contract_Conformance",
 "version":"v1.0",
 "status":"PASS_MACHINE_CONFORMANCE" if all(checks.values()) else "FAIL_MACHINE_CONFORMANCE",
 "calibration24_source_set_sha256":expected,
 "gold100_source_set_sha256":gold["gold100_source_set_sha256"],
 "checks":checks,
 "human_ui_smoke_test":"NOT_RUN",
 "expert_round_A":"NOT_STARTED",
 "expert_round_B":"NOT_STARTED",
 "reliability_metrics":"NOT_AVAILABLE",
 "important_boundary":"Machine conformance validates protocol/state-machine/hash invariants only. It does not establish expert reliability or human usability."
}
(OUT/"P0.3_Workbench_Contract_Conformance_Report_v1.0.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(report,indent=2))
if not all(checks.values()):
    raise SystemExit(1)
