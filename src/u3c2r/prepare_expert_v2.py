#!/usr/bin/env python3
"""Prepare revised neutral expert packets and v0.2 response contract.
No assignment, no expert answers, no authorization. Separate directories are
not cross-user ACL isolation; actual reviewer dispatch stays HOLD.
"""
import argparse,copy,os,json,pathlib as P,hashlib
from collections import Counter
from jsonschema import Draft202012Validator
def require(x,c):
 if not x:raise ValueError(c)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def digest(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf8"))
def put(p,x):
 with p.open("x",encoding="utf8") as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write("\n")
 os.chmod(p,0o600)
def build_schema(old):
 s=copy.deepcopy(old);s["$id"]="urn:nutrifoundation:udf:u3c2r:expert-response:0.2";s["title"]="C2-R1 expert response v0.2"
 s["description"]="Draft response, never automatically qualified. Controller-bound runtime checks exact task and authority, references and freeze/unblind receipts."
 a,b=s["oneOf"];ap=a["properties"];bp=b["properties"]
 for x in ap["source_reconstruction"]["properties"].values():
  x["allOf"]=[{"if":{"properties":{"state":{"const":"UNRESOLVED"}}},"then":{"properties":{"value":{"const":None},"evidence_refs":{"maxItems":0}}}},{"if":{"properties":{"state":{"enum":["SOURCE_EXPLICIT","EXPERT_INFERENCE"]}}},"then":{"properties":{"value":{"type":"string","minLength":1},"evidence_refs":{"minItems":1}}}}]
 ci=ap["independent_candidates"]["items"];ci["properties"]["target_system"]={"enum":["FoodOn","FDC_SR_Legacy","FNDDS"]}
 ci["properties"]["evidence_refs"]["minItems"]=1
 ci["allOf"]=[{"if":{"properties":{"relation":{"const":"CONDITIONAL"}}},"then":{"properties":{"conditions":{"minItems":1}}}},{"if":{"properties":{"task_applicability":{"const":"CONDITIONAL_CONCEPT_ONLY"}}},"then":{"properties":{"conditions":{"minItems":1}}}}]
 a["allOf"] += [{"if":{"properties":{"initial_disposition":{"const":"CANDIDATE_CONCEPT_ONLY"}}},"then":{"properties":{"independent_candidates":{"minItems":1}}}},{"if":{"properties":{"initial_disposition":{"const":"NO_SUPPORTED_TARGET_IN_REVIEWED_MATERIAL"}}},"then":{"properties":{"independent_candidates":{"maxItems":0}}}}]
 ei=bp["edge_judgments"]["items"];ei["properties"]["evidence_refs"]["minItems"]=1
 ei["allOf"]=[{"if":{"properties":{"verdict":{"const":"CONDITIONAL_RELATION"}}},"then":{"properties":{"conditions":{"minItems":1}}}},{"if":{"properties":{"relation":{"const":"CONDITIONAL"}}},"then":{"properties":{"conditions":{"minItems":1}}}}]
 bp["edge_judgments"]["minItems"]=1
 b["allOf"] += [{"if":{"properties":{"changed_initial_judgment":{"const":False}}},"then":{"properties":{"change_reason":{"const":None}}}}]
 Draft202012Validator.check_schema(s);return s
def main(root,profile,profile_hash,out):
 root=root.resolve();out=out.resolve();require(not out.exists() and out.is_relative_to(root/"runs/B2/U3-B/C2/R1"),"NEW_EXPERT_DIR")
 require(sha(profile)==profile_hash,"PROFILE_HASH");p=load(profile);policy=load(root/p["policy"])
 for x in p["pins"]:
  if "Expert" in x or x.endswith("C2AdmissionReceipt.json"):require(sha(root/x)==p["pins"][x],"OLD_EXPERT_HASH")
 base=root/"runs/B2/U3-B/C2/real_001/private";first=load(base/"ExpertSourceFirstQueue.json");post=load(base/"ExpertComparisonHidden.json");acc=load(root/"runs/B2/U3-B/C2/expert_packet_001/private/ExpertSourceAccessManifest.json")
 require(len(first)==len(post)==len(acc["source_cases"])==36,"OLD_CASE_COUNT")
 oldpost={x["review_id"]:x for x in post};access={x["review_id"]:x for x in acc["source_cases"]}
 require(set(oldpost)==set(access)=={x["review_id"] for x in first},"OLD_CASE_PAIR")
 schema_path=root/"schemas/udf/u3c2r/ExpertAdjudicationResponse_v0.2.schema.json"
 old_schema=root/"schemas/udf/u3c2/ExpertAdjudicationResponse_v0.1.schema.json";s=build_schema(load(old_schema))
 require(not schema_path.exists() or load(schema_path)==s,"EXPERT_SCHEMA_DRIFT")
 if not schema_path.exists():put(schema_path,s)
 for x in policy["expert_target_files"]:require(sha(root/x["path"])==x["sha256"],"TARGET_SOURCE_HASH")
 fields=("source_ref","source_legacy_ref","source_scope","source_native_label","source_native_kind","source_locator","source_artifact_sha256")
 tasks=[];hidden=[];source_files={};role_tuple=tuple(policy["expert_roles"])
 for i,x in enumerate(sorted(first,key=lambda a:digest(["C2R_NEUTRAL_ORDER_V1",a["source_legacy_ref"]])),1):
  a=access[x["review_id"]]["source_access"];q=root/a["path"];require(q.resolve().is_relative_to(root) and sha(q)==a["sha256"]==x["source_artifact_sha256"] and a["native_locator"]==x["source_locator"],"TASK_SOURCE_HASH")
  source_files[a["path"]]=a["sha256"]
  # No old critic-derived roles, status, severity, priorities or opinions.
  z={k:copy.deepcopy(x[k]) for k in fields}
  z.update({"review_id":"R1-EXP-"+str(i).zfill(3),"required_roles":list(role_tuple),"questions":["Reconstruct the source meaning and explicitly state unknown dimensions.","Independently inspect permitted standards; retain unresolved or conditional relationships.","Separate concept relationships from physical identity and nutrient transfer."],"source_access":a,"initial_review_status":"NOT_ADJUDICATED","scientific_reference_qualified":False,"mapping_release_authorized":False})
  z["task_ref"]="u3c2r:ExpertTask:"+digest([z["source_legacy_ref"],"R1"])[:40]+"@"+digest(z)
  tasks.append(z)
  b=oldpost[x["review_id"]];cards=[]
  for j,c in enumerate(b["priority_evidence"],1):
   cards.append({"comparison_evidence_key":"R1-E-"+str(i).zfill(3)+"-"+str(j).zfill(2),**c})
  hidden.append({"review_id":z["review_id"],"task_ref":z["task_ref"],"old_review_id":x["review_id"],"source_legacy_ref":z["source_legacy_ref"],"priority_evidence":cards,"additional_evidence_count":b["additional_evidence_count"],"full_evidence_locator":b["full_evidence_locator"],"exposure_condition":"AFTER_ACTUAL_INITIAL_FREEZE_AND_CONTROLLER_AUTHORIZED_UNBLIND","adjudication":"PENDING"})
 require(len({x["task_ref"] for x in tasks})==36 and len({tuple(x["required_roles"]) for x in tasks})==1,"NEUTRAL_TASKS")
 out.mkdir(parents=True,mode=0o700);phasea=out/"reviewer_source_only";phasea.mkdir(mode=0o700);phaseb=out/"controller_restricted";phaseb.mkdir(mode=0o700)
 put(phasea/"ExpertSourceFirstQueue.json",tasks)
 put(phasea/"TargetReferenceManifest.json",{"reference_inputs":policy["expert_target_files"],"purpose":"DEVELOPMENT_ONLY","no_release":True})
 put(phaseb/"ExpertComparisonHidden.json",hidden)
 # Keep authorization absent. Actual source-first access requires different
 # account or deployed ACL / isolated export; same-account paths alone do not suffice.
 result={"status":"PASS_NEUTRAL_PACKET_PREPARATION / EXPERT_DISPATCH_HOLD_ACCESS_CONTROL_AND_QUALIFICATION",
 "tasks":len(tasks),"uniform_role_sets":1,"source_files_verified":len(source_files),"reference_files_verified":len(policy["expert_target_files"]),
 "priority_cards":sum(len(x["priority_evidence"]) for x in hidden),"additional_evidence_count":sum(x["additional_evidence_count"] for x in hidden),
 "source_selection":"C1 risk-enriched developer sample; membership itself not blind/confirmatory","phase_a_queue_sha256":sha(phasea/"ExpertSourceFirstQueue.json"),"phase_a_reference_manifest_sha256":sha(phasea/"TargetReferenceManifest.json"),
 "phase_b_packet_sha256":sha(phaseb/"ExpertComparisonHidden.json"),"response_schema_sha256":sha(schema_path),"actual_reviewer_assignment_count":0,"expert_responses":0,"acl_isolation_verified":False,"expert_dispatch_authorized":False,"scientific_release":False}
 put(out/"ExpertPacketR1Report.json",result);print(json.dumps(result,ensure_ascii=False))
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--profile-sha",required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.profile.resolve(),x.profile_sha,x.out)
