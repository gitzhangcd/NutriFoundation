#!/usr/bin/env python3
"""R2-P1: source-only development reference verification and authorized comparison.

Keep the frozen PR64 primary metric. FNDDS single-carrier citation discrepancy
is resolved in a separate controller addendum, never edited in the Critic data.
No independent scientific Gold, new model training, or mapping release.
"""
import sys,pathlib as P,argparse,json,copy,math
from collections import Counter,defaultdict
from datetime import datetime,timezone
sys.path.insert(0,str(P.Path(__file__).resolve().parents[1]/"u3r2"))
from compare_reference import *
BASE="runs/B2/U3-B/C2/R2"
CSV="runs/B2/U3-A/inputs/FNDDS_2015_16.zip"
ARS="runs/B2/U3-A/inputs/FNDDS_ARS_foods_2015_16.xlsx"
def count(rows,k):return dict(Counter(x[k] for x in rows))
def now():return datetime.now(timezone.utc).isoformat()
class Fence:
 def __init__(self,root):self.root=root.resolve();self.hashes={}
 def pin(self,rel,h=None):
  q=self.root/rel;p=q.resolve()
  require(p.is_relative_to(self.root) and q.is_file() and not q.is_symlink(),"UNSAFE_INPUT_PATH")
  a=sha(p);k=str(p.relative_to(self.root))
  require(h is None or a==h,"INPUT_HASH:"+k);require(k not in self.hashes or self.hashes[k]==a,"INPUT_REOPEN:"+k)
  self.hashes[k]=a;return p
 def check(self):require(all(sha(self.root/p)==h for p,h in self.hashes.items()),"INPUT_MUTATION")
def resolve_reference(r,task,validator,vocab,authorities):
 """Exact per-record validation with an explicit narrowly bounded carrier overlay.
 The original CSV locator must exactly match its physical row and cited bytes;
 both canonical carriers were independently recovered by parse_standards.
 For other systems, original strict validation is retained.
 """
 vv=dict(vocab);add=[];targets=[]
 for field in ("independent_candidates","hard_negatives"):
  for c in r[field]:
   system,version,id=c["target_key"];k=key(system,id)
   require(k in vocab and version==SYSTEM_VERSION[system],"REFERENCE_TARGET_ID_VERSION")
   t=vocab[k];require(not t["deprecated"] and c["target_native_label"].strip()==t["label"].strip(),"REFERENCE_TARGET_LABEL")
   loc=c["target_locator"];canonical=t["locator"]
   if loc!=canonical:
    require(system=="FNDDS","NON_FNDDS_LOCATOR_DRIFT")
    parts=canonical.split(" | ")
    require(len(parts)==2 and parts[0].startswith(CSV+"!") and parts[1].startswith(ARS+"!") and loc==parts[0],"FNDDS_NOT_EXACT_CSV_LOCATOR")
    ev=indexes(r,c["evidence_refs"])
    require(any(x["role"]=="TARGET_EXPLICIT" and x["artifact_sha256"]==authorities[CSV] and x["locator"]==loc for x in ev),"FNDDS_CSV_EVIDENCE_NOT_EXACT")
    vv[k]={**t,"locator":loc}
    add.append({"review_id":r["review_id"],"record_field":field,"target_key":c["target_key"],
      "reviewer_original_locator":loc,"reviewer_cited_csv_sha256":authorities[CSV],
      "controller_verified_same_cycle_ars_locator":parts[1],"controller_verified_ars_sha256":authorities[ARS],
      "canonical_combined_locator":canonical,"source_label_trim_equal":True,"method":"EXACT_FOODCODE_SAME_CYCLE_CROSSWALK",
      "reviewer_ars_citation_claimed":False,"semantic_judgment_changed":False,"scientific_release":False})
   targets.append({"review_id":r["review_id"],"role":field,"target_key":c["target_key"],"native_identity_verified":True,
    "original_canonical_locator_exact":loc==canonical,"original_cited_locator_verified":True,
    "controller_combined_locator_verified":True,"semantic_judgment_verified_by_expert":False})
 validate_reference(r,task,validator,vv,authorities)
 return add,targets
def verify_inputs(root,profile,ph,run):
 f=Fence(root);f.pin(str(profile.resolve().relative_to(root)),ph);p=read(profile)
 require(p["version"]=="UDF-U3R2-P1-0.1" and p["scientific_release_authorized"] is False and p["authorization"],"P1_SCOPE")
 for k,h in p["pins"].items():f.pin(k,h)
 task_path="configs/audit/tasks/B2_U3R2_REF44_Gemini_001.json";cfg=read(root/task_path);d=root/cfg["output"]["directory"]
 rc=read(d/"CriticFreezeReceipt.json");require(rc["task_id"]==cfg["task_id"] and rc["status"]=="REVIEW_FROZEN" and rc["completed_cases"]==44 and rc["mapping_release_authorized"] is False and rc["scientific_reference_qualified"] is False,"CRITIC_RECEIPT")
 require(set(rc["output_file_hashes"])=={"ExecutionManifest.json","ReviewRecords.jsonl","ReviewReport.md"},"CRITIC_OUTPUT_SET")
 for k,h in rc["output_file_hashes"].items():
  z=f.pin(str((d/k).relative_to(root)),h);require(z.stat().st_size==rc["output_file_bytes"][k],"OUTPUT_SIZE")
 allow={x["path"]:x["sha256"] for x in cfg["allowed_inputs"]}
 allow[task_path]=p["pins"][task_path];allow[cfg["protocol"]]=cfg["protocol_sha256"]
 for k,h in allow.items():f.pin(k,h)
 em=read(d/"ExecutionManifest.json")
 require(em["task_id"]==rc["task_id"] and em["status"]=="REVIEW_FROZEN" and em["model_identity"]==rc["model_identity"],"MANIFEST_ID")
 require(em["input_hashes"]==rc["input_hashes"]==allow and set(em["actual_accessed_paths"])==set(allow),"ACCESS_DECLARATION")
 require(em["prior_exposure_declared"] and rc["prior_exposure_declared"] and not em["confirmatory_blind_claimed"] and not rc["confirmatory_blind_claimed"] and em["forbidden_access_count"]==em["reserved_cases_accessed"]==0,"EXPOSURE_SCOPE")
 require(all(rc["counts"][k]==0 for k in ("forbidden_access","existing_files_modified","reserved_cases_accessed","accepted_equivalence","scientific_reference_qualified","formal_mapping_release")),"NO_RELEASE_DECLARATION")
 g=read(run/"R2GeneratorFreezeReceipt.json");require(g["mapping_release_authorized"] is False,"GENERATOR_RELEASE")
 for k,h in g["files"].items():f.pin(str((run/k).relative_to(root)),h)
 # Check preserved generator input fences by digest; no reserved32 semantic evaluation.
 for k,h in read(run/"controller_private/InputFence.json").items():f.pin(k,h)
 qrows=read(run/"reviewer_source_only/R2Review44.json");q={x["review_id"]:x for x in qrows}
 rec=list(lines(d/"ReviewRecords.jsonl"));r={x["review_id"]:x for x in rec}
 require(len(q)==len(qrows)==len(r)==len(rec)==44==len({x["source_ref"] for x in rec}) and set(q)==set(r),"CASE_IDENTITIES")
 cs=[c for x in rec for c in x["independent_candidates"]];hs=[c for x in rec for c in x["hard_negatives"]]
 counts={"allowed_inputs_verified":len(allow)-2,"total_accessed_files":len(allow),"completed_cases":len(rec),"unique_review_ids":len(r),
 "total_candidates":len(cs),"candidates_by_system":dict(Counter(x["target_key"][0] for x in cs)),"candidates_by_relation":count(cs,"relation"),
 "total_hard_negatives":len(hs),"hard_negatives_by_system":dict(Counter(x["target_key"][0] for x in hs)),"hard_negatives_by_conflict_type":count(hs,"conflict_type"),
 "case_dispositions":count(rec,"case_disposition"),"local_concept_extension":count(rec,"local_concept_extension"),"total_reviewer_minutes":math.fsum(x["reviewer_minutes"] for x in rec)}
 require(all(rc["counts"][k]==v for k,v in counts.items()),"RECEIPT_COUNT_RECONCILIATION")
 schema=read(root/cfg["review_task"]["response_schema"]);Draft202012Validator.check_schema(schema);validator=Draft202012Validator(schema,format_checker=FormatChecker())
 authorities={x["path"]:x["sha256"] for x in cfg["allowed_inputs"] if x["role"]=="FIXED_PUBLIC_STANDARD"};require(len(authorities)==4,"AUTHORITY_SET")
 vocab,vc=parse_standards(Standards(root));strict=0;add=[];checks=[];errors=Counter()
 for rid in sorted(r):
  x=r[rid]
  try:validate_reference(x,q[rid],validator,vocab,authorities);strict+=1
  except ValueError as ex:
   require(str(ex)=="REFERENCE_TARGET_LOCATOR","ORIGINAL_CONTRACT_FAILURE:"+str(ex));errors[str(ex)]+=1
  a,t=resolve_reference(x,q[rid],validator,vocab,authorities);add+=a;checks+=t
 require(len(checks)==len(cs)+len(hs),"TARGET_CHECK_COUNT")
 require(strict+sum(errors.values())==44 and len(add)==sum(not x["original_canonical_locator_exact"] for x in checks),"LOCATOR_RESOLUTION_CLOSURE")
 f.check()
 verification={"status":"PASS_DEVELOPMENT_REFERENCE_IDENTITY_WITH_CONTROLLER_LOCATOR_ADDENDUM / ORIGINAL_COMPOSITE_LOCATOR_CONFORMANCE_NOT_PASS",
 "reviewer":rc["reviewer"],"model_identity":rc["model_identity"],"frozen_utc":rc["frozen_utc"],"allowed_inputs_verified":len(allow)-2,"frozen_outputs_verified":len(rc["output_file_hashes"]),
 "review_records_verified":len(r),"target_references_verified":len(checks),"candidate_references":len(cs),"hard_negative_references":len(hs),
 "original_strict_cases_passed":strict,"original_strict_cases_failed":44-strict,"original_composite_locator_deviations":len(add),
 "controller_same_cycle_addenda":len(add),"raw_standard_counts":vc,"critic_reported_counts_recomputed":counts,
 "reported_review_elapsed_seconds":(datetime.fromisoformat(rc["frozen_utc"])-datetime.fromisoformat(em["execution_utc_start"])).total_seconds(),
 "reviewer_minutes_interpretation":"self-reported by model; not observed human labor or independent measured cost",
 "historical_exposure":True,"access_independently_proven":False,"original_semantic_decisions_unchanged":True,"scientific_reference_qualified":False}
 return f,p,q,r,vocab,authorities,validator,verification,add,checks

def derive_comparison(f,root,run,q,r):
 # Only first44 semantics are used; the reserved32 digest is checked, no outcome opened.
 comp={x["review_id"]:x for x in read(run/"controller_private/ControllerComparisonIndex.json") if x["batch"]=="ORIGINAL_NEW44"}
 require(set(comp)==set(q),"COMPARATOR_CASE_SET")
 un=read(run/"controller_private/FrozenTargetUniverse.json");u={tuple(x) for x in un["original"]};e={tuple(x) for x in un["extension"]}
 require(len(u)==28845 and len(e)==1174 and not u&e,"UNIVERSE_CLOSURE")
 pool=defaultdict(list);sources={x["source_ref"] for x in q.values()}
 manifest=read(run/"controller_private/ProposalManifest.json")
 for x in manifest.values():
  z=f.pin(str((run/x["file"]).relative_to(root)),x["sha256"]);n=0
  for row in lines(z):
   n+=1
   if row["source_legacy_ref"] in sources:
    v=dict(row);h=v.pop("content_sha256");require(dg(v)==h,"PROPOSAL_CONTENT_HASH")
    require(row["accepted_equivalence"] is False and row["mapping_release"]=="HOLD" and row["development_concept_review_authorized"] is False,"PROPOSAL_RELEASE")
    pool[row["source_legacy_ref"]].append(row)
  require(n==x["rows"],"PARTITION_ROW_COUNT")
 require(sum(x["current_model_query"] for x in comp.values())==19 and len(pool)==19,"CURRENT_MODEL_CASE_COUNT")
 cases=[];sensitivity=[];gaps=[];oldrecords=[];locals_=Counter();scope_counts=Counter();per_group=defaultdict(Counter);paired=defaultdict(Counter);combined=defaultdict(Counter);negative=Counter()
 for rid in sorted(q):
  x=r[rid];c=comp[rid];sr=q[rid]["source_ref"];require(c["source_ref"]==sr==x["source_ref"],"COMPARATOR_SOURCE")
  current=c["current_model_query"];grp="CURRENT_19" if current else "OLD_ONLY_25"
  locals_[(grp,x["local_concept_extension"])]+=1
  cc=compare_case(x,c,u,e,pool[sr]);cases.append(cc)
  x2={**x,"independent_candidates":[z for z in x["independent_candidates"] if z["relation"]!="RELATED" and z["applicability"]!="RELATED_ONLY"]}
  sensitivity.append(compare_case(x2,c,u,e,pool[sr]))
  ps=supported(x);ns={tuple(z["target_key"]) for z in x["hard_negatives"]}
  per_group[grp]["cases"]+=1;per_group[grp]["positive_proposals"]+=len(x["independent_candidates"]);per_group[grp]["supported_reference_edges"]+=len(ps);per_group[grp]["hard_negative_edges"]+=len(ns)
  per_group[grp]["cases_with_supported_reference"]+=bool(ps)
  per_group[grp]["reported_minutes"]+=x["reviewer_minutes"]
  for z in x["independent_candidates"]:
   per_group[(grp,"RELATION")][z["relation"]]+=1
  old=[z for z in c["old_u2c_candidates"] if z["target_key"] is not None]
  oldkeys={tuple(z["target_key"]) for z in old}
  per_group[grp]["old_raw_edges"]+=len(c["old_u2c_candidates"]);per_group[grp]["old_external_edges"]+=len(old)
  per_group[grp]["old_unique_external_targets"]+=len(oldkeys)
  per_group[grp]["old_supported_target_overlap"]+=len(oldkeys&ps)
  per_group[grp]["old_negative_target_overlap"]+=len(oldkeys&ns)
  per_group[grp]["old_unjudged_targets"]+=len(oldkeys-ps-ns)
  per_group[grp]["old_cases_with_supported_overlap"]+=bool(oldkeys&ps)
  per_group[grp]["old_cases_with_negative_overlap"]+=bool(oldkeys&ns)
  for z in old:
   k=tuple(z["target_key"])
   if k in ns:
    oldrecords.append({"review_id":rid,"group":grp,"target_key":z["target_key"],"route":z["route"],"prior_ref":z["prior_ref"],"critic_hard_negative_overlap":True})
  pk={}
  for z in pool[sr]:
   k=tuple(z["target_key"]);require(k not in pk,"POOL_TARGET_DUPLICATE");pk[k]=z
  index={(a["target_scope"],a["arm"]):a["ranked_targets"] for a in c["current_comparators"]}
  if current:require(len(index)==16,"COMPARATOR_ARM_COUNT")
  else:require(not index and not pk,"NO_CURRENT_MODEL_QUERY")
  labels={tuple(z["target_key"]):z for z in x["independent_candidates"]}
  for k in sorted(ps):
   y=labels[k];z=pk.get(k)
   domain="ORIGINAL" if k in u else "EXTENSION" if k in e else "OUTSIDE"
   if not current:reason="NO_CURRENT_MODEL_QUERY"
   elif domain=="OUTSIDE":reason="OUTSIDE_FROZEN_UNIVERSES"
   elif z is None:reason="IN_UNIVERSE_NOT_IN_RETRIEVED_POOL"
   else:reason="IN_RETRIEVED_POOL"
   ranks={}
   if current:
    for arm in ARMS:
     hits=[i+1 for (ts,a),ids in index.items() if a==arm for i,t in enumerate(ids) if tuple(t)==k]
     ranks[arm]=min(hits) if hits else None
   rec={"review_id":rid,"group":grp,"source_scope":x["source_scope"],"source_native_label":x["source_native_label"],"target_key":list(k),"target_native_label":y["target_native_label"],"critic_relation":y["relation"],"applicability":y["applicability"],"domain":domain,"membership":reason,
    "arm_rank_within12":ranks,"r1_review_eligible":z["r1_review_eligible"] if z else None,"r1_disposition":z["r1_disposition"] if z else None,"r2_proposal_route":z["proposal_route"] if z else None,"r2_condition_questions":z["condition_questions"] if z else [],"reference_is_expert_gold":False,"mapping_release":False}
   gaps.append(rec)
  if not current:continue
  for arm in ARMS:
   for k in KS:
    for domain,univ in (("ALL_DOMAINS",u|e),("ORIGINAL",u),("EXTENSION",e)):
     ranked={tuple(t) for (ts,a),ids in index.items() if a==arm and (domain=="ALL_DOMAINS" or (ts==EXT)==(domain=="EXTENSION")) for t in ids[:k]}
     pos=ps&univ;z=combined[(domain,arm,k)]
     z["queries"]+=1;z["queries_with_reference"]+=bool(pos);z["queries_with_hit"]+=bool(pos&ranked);z["reference_edges"]+=len(pos);z["reference_edges_hit"]+=len(pos&ranked);z["proposal_edges"]+=len(ranked);z["critic_negative_overlap"]+=len(ns&ranked)
     z["unjudged_proposals"]+=len(ranked-ps-ns)
    if k==3:
     ranked={tuple(t) for (ts,a),ids in index.items() if a==arm for t in ids[:k]}
     for t in ns&ranked:
      z=pk[t];negative[(arm,z["proposal_route"])]+=1
  for k in KS:
   p0={tuple(t) for (ts,a),ids in index.items() if a=="FUSION" for t in ids[:k]}
   p1={tuple(t) for (ts,a),ids in index.items() if a=="TYPED_QUESTION" for t in ids[:k]}
   if ps&(u|e):paired[k][(bool(ps&p0),bool(ps&p1))]+=1
 primary=aggregate(cases);sens=aggregate(sensitivity)
 summary={"status":"PASS_R2_P1_DEVELOPMENT_REFERENCE_COMPARISON / SCIENTIFIC_QUALIFICATION_HOLD",
 "primary_preplanned":primary,"sensitivity_excluding_related_and_related_only":sens,
 "group_counts":[{"group":k if isinstance(k,str) else k[0],"kind":"CASE_METRICS" if isinstance(k,str) else "RELATION_COUNTS",**dict(v)} for k,v in per_group.items()],
 "local_concept_proposals":[{"group":k[0],"status":k[1],"count":n} for k,n in sorted(locals_.items())],
 "supported_reference_membership":[{"group":k[0],"domain":k[1],"membership":k[2],"edges":n} for k,n in sorted(Counter((x["group"],x["domain"],x["membership"]) for x in gaps).items())],
 "retrieved_reference_routes":[{"route":k[0],"r1_eligible":k[1],"edges":n} for k,n in sorted(Counter((x["r2_proposal_route"],x["r1_review_eligible"]) for x in gaps if x["membership"]=="IN_RETRIEVED_POOL").items())],
 "old_negative_overlap_routes":[{"group":k[0],"route":k[1],"edges":n} for k,n in sorted(Counter((x["group"],x["route"]) for x in oldrecords).items())],
 "combined_secondary":[{"domain":k[0],"arm":k[1],"k_per_scope":k[2],**dict(v),"reference_hit_fraction":v["queries_with_hit"]/v["queries_with_reference"] if v["queries_with_reference"] else None} for k,v in sorted(combined.items())],
 "fusion_vs_typed_paired_hits":[{"k":k,"fusion_hit":a,"typed_hit":b,"cases":n} for k,v in sorted(paired.items()) for (a,b),n in sorted(v.items())],
 "top3_critic_negative_routes":[{"arm":k[0],"r2_proposal_route":k[1],"edges":n} for k,n in sorted(negative.items())],
 "current_model_cases":19,"old_only_cases":25,"expert_gold_count":0,"scientific_precision_recall":"NOT_ESTIMABLE","mapping_release_count":0}
 f.check()
 return summary,cases,gaps,oldrecords
def main(root,profile,ph,run,out):
 root=root.resolve();profile=profile.resolve();run=run.resolve();out=out.resolve()
 require(not out.exists() and out.is_relative_to(root/BASE/"P1"),"NEW_P1_DIRECTORY")
 f,p,q,r,vocab,authorities,val,verification,add,checks=verify_inputs(root,profile,ph,run)
 print("REFERENCE_VERIFIED",json.dumps(verification,ensure_ascii=False),flush=True)
 summary,cases,gaps,oldrecords=derive_comparison(f,root,run,q,r)
 out.mkdir(parents=True);priv=out/"private";priv.mkdir(mode=0o700)
 putl(priv/"CarrierLocatorAddenda.jsonl",add);putl(priv/"NativeTargetChecks.jsonl",checks);putl(priv/"ReferenceComparisonRecords.jsonl",cases)
 putl(priv/"ReferenceGapAttribution.jsonl",gaps);putl(priv/"OldRiskNegativeOverlap.jsonl",oldrecords)
 put(out/"P1ReferenceVerificationReport.json",verification);put(out/"P1ComparisonReport.json",summary)
 f.check();put(priv/"InputFence.json",f.hashes)
 hashes={str(x.relative_to(out)):sha(x) for x in out.rglob("*") if x.is_file()}
 receipt={"status":"PASS_R2_P1_DEVELOPMENT_COMPARISON / ORIGINAL_LOCATOR_FORMAT_DEVIATION_RESOLVED_BY_CONTROLLER / SCIENTIFIC_QUALIFICATION_HOLD",
 "utc":now(),"profile_sha256":ph,"critic_receipt_sha256":p["pins"][BASE+"/Reference44_Gemini_001/CriticFreezeReceipt.json"],
 "generator_receipt_sha256":p["pins"][BASE+"/real_001/R2GeneratorFreezeReceipt.json"],"input_fence_count":len(f.hashes),"output_file_hashes":hashes,
 "reviewed_cases":44,"target_references_verified":len(checks),"controller_locator_addenda":len(add),"current_model_cases":19,"old_only_cases":25,
 "reserved32_outcomes_read":0,"original_inputs_unchanged":True,"mapping_release_authorized":False,"scientific_reference_qualified":False}
 put(out/"P1FreezeReceipt.json",receipt)
 print("P1_SUMMARY",json.dumps({k:v for k,v in summary.items() if k not in ("primary_preplanned","sensitivity_excluding_related_and_related_only","combined_secondary")},ensure_ascii=False),flush=True)
 print("TOP3",json.dumps([x for x in summary["combined_secondary"] if x["k_per_scope"]==3],ensure_ascii=False),flush=True)
 print("P1_FREEZE_SHA",sha(out/"P1FreezeReceipt.json"),flush=True)
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--profile-sha",required=True);a.add_argument("--run",type=P.Path,required=True);a.add_argument("--out",type=P.Path,required=True);a.add_argument("--pi-authorized-unblind",action="store_true");x=a.parse_args()
 require(x.pi_authorized_unblind,"PI_UNBLIND_AUTHORIZATION_REQUIRED");main(x.root,x.profile,x.profile_sha,x.run,x.out)
