#!/usr/bin/env python3
"""Prepare bounded C2 implementation audit material, excluding the new blind cohort.
Only the already PI-unblinded original 44 cases and public scope diagnostics are exposed.
"""
import argparse, pathlib as P, json, hashlib, collections as C
def require(x,c):
 if not x:raise ValueError(c)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf8"))
def lines(p):
 with p.open(encoding="utf8") as f:
  for l in f:
   if l.strip():yield json.loads(l)
def put(p,x):
 with p.open("x",encoding="utf8") as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write("\n")
def ref(o):return o["object_id"]+"@"+o["revision_id"]
def main(root,run,out):
 root=root.resolve();run=run.resolve();out=out.resolve()
 require(out.is_relative_to(root/"runs/B2/U3-B/C2") and not out.exists() and not out.is_relative_to(run),"NEW_AUDIT_SLICE")
 c1=root/"runs/B2/U3-B/C1/real_001"
 c1f=load(c1/"C1FreezeReceipt.json");require(c1f["unblinding_authorized_by_pi"],"C1_AUTHORIZATION")
 c1p=c1/"private/DevelopmentDisagreementRecords.jsonl";require(sha(c1p)==c1f["output_file_hashes"]["private/DevelopmentDisagreementRecords.jsonl"],"C1_FROZEN_CASES")
 cases=list(lines(c1p));require(len(cases)==44,"C1_CASES")
 old={};sources={c["source_ref"] for c in cases}
 for c in cases:
  for group in ("shared","critic_hard_negative_overlap","generator_unreviewed","generator_other_target_scopes"):
   for x in c[group]:
    require(x["generator_ref"] not in old,"C1_DUP_EDGE")
    old[x["generator_ref"]]={"review_id":c["review_id"],"source_legacy_ref":c["source_ref"],"source_label":c["source_native_label"],"group":group,"target_label":x["target_label"],"target_key":x["target_key"],"u2c_route":x["u2c_route"],"critic_conflict_type":x.get("critic_conflict_type")}
 require(len(old)==355,"C1_EDGE_COUNT")
 p=run/"private/partition_manifest.json";r=load(run/"C2ExecutionReport.json")
 require(sha(p)==r["partition_manifest_sha256"],"C2_MANIFEST")
 m=load(p);tree=run/"private/typed_partitions";selected=[];scopes=[];allids=set();allrisks=0
 diag=load(root/"runs/B2/U3-B/C1/validation_001/private/FoodOnScopeDiagnosis.json")
 six={x["target_key"][1] for x in diag};policy=load(root/"configs/udf/u3c2/C2_Policy_v0.1.json")
 negatives={"http://purl.obolibrary.org/obo/"+x for x in policy["foodon"]["negative_probe_ids"]}
 for rel,x in m.items():
  if not rel.endswith(("/SemanticRiskAssessment.jsonl","/ScopeAssessment.jsonl")):continue
  f=tree/rel;require(sha(f)==x["sha256"],"PARTITION_DRIFT")
  for o in lines(f):
   z=o["payload"]
   if o["kind"]=="ScopeAssessment":
    if z["iri"] in six|negatives or (z["asserted_core_member"] and z["scope_status"]=="HOLD_EXCLUSION_BRANCH_OVERLAP"):scopes.append(o)
   else:
    allrisks+=1
    if z["cohort"]!="U3A_EXPOSED_44":continue
    prior=z["prior_candidate_ref"];require(prior in old and prior not in allids and z["source_legacy_ref"]==old[prior]["source_legacy_ref"] and z["source_legacy_ref"] in sources,"AUDIT_SLICE_SCOPE")
    allids.add(prior);selected.append({"c1_evidence":old[prior],"c2_assessment":o})
 require(allids==set(old) and allrisks==35710,"AUDIT_SLICE_COMPLETENESS")
 require({x["payload"]["iri"] for x in scopes}>=six|negatives,"SCOPE_SLICE_COMPLETENESS")
 out.mkdir(parents=True);private=out/"private";private.mkdir()
 put(private/"Exposed44RiskAuditSlice.json",selected);put(private/"FoodOnScopeAuditSlice.json",scopes)
 neg=[x for x in selected if x["c1_evidence"]["group"]=="critic_hard_negative_overlap"]
 amber=[x["c2_assessment"]["payload"] for x in neg if x["c1_evidence"]["u2c_route"]=="AMBER"]
 nontrivial=sum(bool(x["explicit_conflicts"] or x["unresolved_conditions"] or "COMPONENT_WHOLE_OR_FORM_MISMATCH_CANDIDATE" in x["role_conditions"]) for x in amber)
 report={"status":"PASS_BOUNDED_AUDIT_SLICE_PREPARATION","exposed_c1_cases":len(cases),"exposed_prior_edges":len(selected),"scope_probe_records":len(scopes),"c1_negative_overlap":len(neg),"amber_with_specific_additional_flags":nontrivial,"amber_grain_only":len(amber)-nontrivial,"new_blind_cases_disclosed":0,"new_blind_hidden_candidate_records_disclosed":0,"slice_hashes":{x.name:sha(x) for x in sorted(private.iterdir())},"scope_limit":"Engineering audit of previously unblinded C1 records, code and public ontology. No independent audit of hidden new cohort, no expert Gold."}
 put(out/"AuditSlicePreparationReport.json",report);print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--run",type=P.Path,required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.run,x.out)
