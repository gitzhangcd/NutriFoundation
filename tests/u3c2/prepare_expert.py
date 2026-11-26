#!/usr/bin/env python3
"""Prepare restricted source-first access manifest, not expert answers.
Explicit paths and byte hashes resolve each task without searching hidden candidates.
"""
import argparse,sys,pathlib as P,json,hashlib,copy,collections as C
from jsonschema import Draft202012Validator,FormatChecker
ROOT=P.Path(__file__).resolve().parents[2]
def require(v,k):
 if not v:raise ValueError(k)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf8"))
def put(p,x):
 with p.open("x",encoding="utf8") as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write("\n")
def main(root,run,out):
 root=root.resolve();run=run.resolve();out=out.resolve()
 require(not out.exists() and out.is_relative_to(root/"runs/B2/U3-B/C2") and not out.is_relative_to(run),"NEW_EXPERT_PACKET")
 rp=run/"C2ExecutionReport.json";report=load(rp);q=run/"private/ExpertSourceFirstQueue.json";tasks=load(q)
 require(report["status"].startswith("PASS_BOUNDED_C2") and len(tasks)==36,"C2_TASKS")
 old=root/"runs/B2/U3-A/real_002/private";m=load(old/"collection_manifest.json");f=old/"typed_collections/SourceSnapshotDraft.jsonl"
 require(sha(f)==m["SourceSnapshotDraft.jsonl"]["sha256"],"SOURCE_SNAPSHOT_MANIFEST")
 snapshots=[json.loads(l)["payload"] for l in f.open()]
 by={(x["scope"],x["sha256"]):x for x in snapshots}
 config=root/"configs/audit/tasks/B2_U3B_C0_Gemini_001.json";cfg=load(config)
 allowed=[x for x in cfg["allowed_inputs"] if x["role"] not in ("source-only base","source-only supplement") and x["path"].startswith("runs/B2/U3-A/inputs/")]
 require(len(allowed)==4,"EXPERT_TARGET_SOURCES")
 checks={};records=[]
 for x in tasks:
  a=by[(x["source_scope"],x["source_artifact_sha256"])]
  p=(root/a["path"]).resolve();require(p.is_relative_to(root) and p.is_file(),"SOURCE_PATH")
  if a["path"] not in checks:
   h=sha(p);require(h==a["sha256"],"SOURCE_BYTES");checks[a["path"]]=h
  records.append({"review_id":x["review_id"],"task_ref":x["task_ref"],"source_legacy_ref":x["source_legacy_ref"],"source_access":{"path":a["path"],"sha256":a["sha256"],"source_version":a["version"],"native_locator":x["source_locator"],"scope":a["scope"],"access_limit":"Task-scoped native record only; do not open unrelated private rows or candidate outputs."},"reviewer_status":"NOT_ASSIGNED"})
 for x in allowed:
  p=(root/x["path"]).resolve();require(p.is_relative_to(root) and sha(p)==x["sha256"],"REFERENCE_SOURCE")
 schema_path=root/"schemas/udf/u3c2/ExpertAdjudicationResponse_v0.1.schema.json";s=load(schema_path)
 Draft202012Validator.check_schema(s);v=Draft202012Validator(s,format_checker=FormatChecker())
 # Synthetic structural tests only; never insert examples into the actual expert queue.
 h="0"*64;fake_ref="synthetic:task@"+h;dim={"value":None,"state":"UNRESOLVED","evidence_refs":[]}
 base={"task_ref":fake_ref,"review_id":"SYNTHETIC_TEST_ONLY","source_legacy_ref":fake_ref,"reviewer_id":"SYNTHETIC_TEST","reviewer_role":"SYNTHETIC_TEST","qualification_evidence_ref":"SYNTHETIC_TEST_NOT_QUALIFIED","utc":"2026-11-27T00:00:00Z","evidence":[],"reviewer_minutes":0,"review_status":"EXPERT_DRAFT_PENDING_FREEZE","mapping_release_authorized":False,"scientific_reference_qualified":False}
 a=dict(base,phase="INITIAL_SOURCE_FIRST",prior_candidate_exposure="UNKNOWN",source_reconstruction={k:copy.deepcopy(dim) for k in ("base_food","entity_grain","food_state","preparation","species_variety","edible_part","composition","regional_scope")},independent_candidates=[],unresolved_reasons=["synthetic missing evidence"],initial_disposition="HOLD_INSUFFICIENT_EVIDENCE")
 b=dict(base,phase="POST_INITIAL_COMPARISON",initial_frozen_sha256=h,comparison_packet_sha256=h,explicit_unblind_authorization_ref="SYNTHETIC_TEST_ONLY",edge_judgments=[],remaining_uncertainties=[],changed_initial_judgment=False,change_reason=None)
 tests=[]
 def t(name,x,expected):
  observed=v.is_valid(x);tests.append({"test":name,"expected_valid":expected,"observed_valid":observed,"pass":observed==expected})
 t("initial structure synthetic",a,True);t("post structure synthetic",b,True)
 t("release promotion denied",dict(a,mapping_release_authorized=True),False)
 t("unresolved without reason denied",dict(a,unresolved_reasons=[]),False)
 t("post missing initial frozen hash", {k:x for k,x in b.items() if k!="initial_frozen_sha256"},False)
 t("changed initial judgement without reason",dict(b,changed_initial_judgment=True),False)
 t("fake qualification denied",dict(b,scientific_reference_qualified=True),False)
 t("unexpected candidate opinion in source-first",dict(a,critic_relation="EXACT"),False)
 require(all(x["pass"] for x in tests),"EXPERT_SCHEMA_TEST_FAILURE")
 out.mkdir(parents=True);private=out/"private";private.mkdir()
 put(private/"ExpertSourceAccessManifest.json",{"status":"PREPARED_NOT_ASSIGNED","case_count":len(records),"task_queue_sha256":sha(q),"target_reference_inputs":allowed,"source_cases":records,"post_initial_comparison":"NOT_AUTHORIZED_BEFORE_INITIAL_FREEZE","source_artifact_count":len(checks),"schema_sha256":sha(schema_path),"scientific_release":False})
 result={"status":"PASS_EXPERT_TASK_SOURCE_ACCESS_PREPARATION / EXPERT_EXECUTION_HOLD","source_first_cases":len(records),"distinct_source_artifacts":len(checks),"public_standard_files":len(allowed),"actual_source_hash_verified_cases":len(records),"response_schema_tests_passed":sum(x["pass"] for x in tests),"response_schema_tests_total":len(tests),"tests":tests,"assigned_reviewers":0,"actual_expert_responses":0,"scientific_reference_count":0,"source_access_manifest_sha256":sha(private/"ExpertSourceAccessManifest.json"),"limitations":["task-level file and locator manifest, not deployed per-row access control","synthetic schema tests do not constitute actual expert judgments or verify professional qualification","source class labels may not resolve preparation, composition or measurement"],"mapping_release_authorized":False}
 put(out/"ExpertPacketPreparationReport.json",result);print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--run",type=P.Path,required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.run,x.out)
