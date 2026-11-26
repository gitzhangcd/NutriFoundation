"""Development-reference comparison; no gold or scientific release.
Use after a separate, PI-authorized frozen review. Never treat an unlisted edge as false.
Source-only review hits are reference overlap, not scientific recall or precision."""
import pathlib as P,sys,json,argparse
from collections import Counter,defaultdict
from jsonschema import Draft202012Validator,FormatChecker
from run_r2 import *
sys.path.insert(0,str(P.Path(__file__).resolve().parents[1]/"u3c1"))
from run_c1 import parse_standards,key
SYSTEM_VERSION={"FoodOn":"2026-09-20","FDC_SR_Legacy":"2018-04","FNDDS":"2015-16"}
REL_SUPPORTED={"EXACT","CLOSE","BROADER_TARGET","NARROWER_TARGET","RELATED","CONDITIONAL"}
class Standards:
 def __init__(self,root):self.root=root
def indexes(response,refs):
 require(all(type(i) is int and 0<=i<len(response["evidence"]) for i in refs),"EVIDENCE_INDEX")
 return [response["evidence"][i] for i in refs]
def validate_reference(r,task,validator,vocab,authorities):
 require(validator.is_valid(r),"REFERENCE_SCHEMA")
 require(all(r[k]==task[k] for k in ("review_id","source_ref","source_scope","source_native_label","native_kind")),"REFERENCE_SOURCE_IDENTITY")
 require({x["target_system"] for x in r["search_attempts"]}==set(SYSTEM_VERSION),"REFERENCE_SEARCH_SCOPE")
 allowed=set(authorities.values())|{task["artifact_sha256"]}
 require(all(x["artifact_sha256"] in allowed for x in r["evidence"]),"REFERENCE_EVIDENCE_SOURCE")
 for d in r["source_dimensions"].values():
  e=indexes(r,d["evidence_refs"])
  if d["state"]=="SOURCE_EXPLICIT":require(any(x["role"]=="SOURCE_EXPLICIT" and x["artifact_sha256"]==task["artifact_sha256"] and x["locator"]==canon(task["source_locator"]) for x in e),"REFERENCE_SOURCE_LOCATOR")
 pos=set();neg=set()
 for field,seen in (("independent_candidates",pos),("hard_negatives",neg)):
  per=Counter()
  for c in r[field]:
   system,version,id=c["target_key"];require(version==SYSTEM_VERSION[system],"REFERENCE_TARGET_VERSION")
   k=key(system,id);require(k in vocab and tuple(c["target_key"]) not in seen,"REFERENCE_TARGET_ID")
   v=vocab[k];require(not v["deprecated"] and c["target_native_label"].strip()==v["label"].strip() and c["target_locator"]==v["locator"],"REFERENCE_TARGET_LOCATOR")
   ev=indexes(r,c["evidence_refs"])
   hs={h for path,h in authorities.items() if path in v["locator"]}
   require(any(x["artifact_sha256"] in hs and x["role"]=="TARGET_EXPLICIT" and x["locator"]==v["locator"] for x in ev),"REFERENCE_TARGET_EVIDENCE")
   seen.add(tuple(c["target_key"]));per[system]+=1
  require(all(n<=3 for n in per.values()),"REFERENCE_TOP3_LIMIT")
 require(not pos&neg,"REFERENCE_POS_NEG_CONFLICT")
 return True
def supported(r):
 return {tuple(x["target_key"]) for x in r["independent_candidates"] if x["relation"] in REL_SUPPORTED and x["applicability"]!="UNRESOLVED"}
def compare_case(r,cmp,universe,ext_universe,pool):
 """Target membership and overlap; pool includes all retained pre-rank candidates."""
 positive=supported(r);negative={tuple(x["target_key"]) for x in r["hard_negatives"]}
 relevant={"original":positive&universe,"extension":positive&ext_universe}
 pool={tuple(x["target_key"]) for x in pool}
 outside=positive-(universe|ext_universe)
 rows=[];classes=Counter()
 for t in positive:
  if t in outside:classes["OUTSIDE_FROZEN_UNIVERSES"]+=1
  elif not cmp["current_model_query"]:classes["NO_CURRENT_MODEL_QUERY"]+=1
  elif t not in pool:classes["IN_UNIVERSE_NOT_IN_RETRIEVED_POOL"]+=1
  else:classes["IN_RETRIEVED_POOL"]+=1
 for ar in ARMS:
  for domain,refset in relevant.items():
   # FoodOn extension and original separately; no score merges.
   rr=[x for x in cmp["current_comparators"] if x["arm"]==ar and ((x["target_scope"]==EXT)==(domain=="extension"))]
   for k in KS:
    candidate={tuple(z) for x in rr for z in x["ranked_targets"][:k]}
    if cmp["current_model_query"]:
     rows.append({"arm":ar,"domain":domain,"k_per_scope":k,"query_has_review_reference":bool(refset),
       "query_has_proposals":bool(candidate),"reference_hit":bool(refset&candidate),"reference_edges":len(refset),"reference_edges_hit":len(refset&candidate),
       "hard_negative_overlap":len(negative&candidate),"candidate_edges":len(candidate)})
 old={tuple(x["target_key"]) for x in cmp["old_u2c_candidates"] if x["target_key"] is not None}
 return {"review_id":r["review_id"],"source_ref":r["source_ref"],"batch":cmp["batch"],"current_model_query":cmp["current_model_query"],
   "critic_disposition":r["case_disposition"],"supported_targets":len(positive),"reference_classes":dict(classes),
   "old_candidate_overlap":len(old&positive),"old_negative_overlap":len(old&negative),"arms":rows,
   "unresolved_not_error":True,"scientific_reference_qualified":False,"mapping_release_authorized":False}
def aggregate(cases):
 totals=defaultdict(Counter);by=Counter()
 for c in cases:
  by[(c["batch"],c["current_model_query"],c["critic_disposition"])]+=1
  for a in c["arms"]:
   z=totals[(c["batch"],a["arm"],a["domain"],a["k_per_scope"])]
   for k in ("query_has_review_reference","query_has_proposals","reference_hit","reference_edges","reference_edges_hit","hard_negative_overlap","candidate_edges"):z[k]+=a[k]
   z["query_count"]+=1
 return {"status":"DEVELOPMENT_REFERENCE_OVERLAP_ONLY / SCIENTIFIC_REFERENCE_HOLD",
  "case_dispositions":[{"batch":k[0],"current_model_query":k[1],"disposition":k[2],"count":v} for k,v in sorted(by.items())],
  "arm_statistics":[{"batch":k[0],"arm":k[1],"domain":k[2],"k_per_scope":k[3],**dict(v),"reference_hit_fraction":v["reference_hit"]/v["query_has_review_reference"] if v["query_has_review_reference"] else None} for k,v in sorted(totals.items())],
  "precision":"NOT_ESTIMABLE_FROM_SOURCE_ONLY_REVIEW","scientific_recall":"NOT_ESTIMABLE","accepted_equivalence":0,"mapping_release_count":0}
def main(root,run,freeze_sha,task_config,task_sha,critic_receipt_sha,out):
 root=root.resolve();run=run.resolve();out=out.resolve();task_config=task_config.resolve()
 require(not out.exists() and out.is_relative_to(root/C2/"R2") and not out.is_relative_to(run),"NEW_COMPARISON_DIRECTORY")
 require(sha(task_config)==task_sha and task_config.is_relative_to(root),"REVIEW_TASK_CONFIG_HASH")
 cfg=read(task_config);require(cfg["task_id"]=="B2-U3R2-REF44-GEMINI-001" and cfg["review_task"]["total_cases"]==44,"REVIEW_TASK_ID")
 d=root/cfg["output"]["directory"];receipt=d/"CriticFreezeReceipt.json";require(sha(receipt)==critic_receipt_sha,"CRITIC_RECEIPT_HASH")
 rc=read(receipt);require(rc["task_id"]==cfg["task_id"] and rc["status"]=="REVIEW_FROZEN" and rc["mapping_release_authorized"] is False,"CRITIC_RECEIPT")
 require(set(rc["output_file_hashes"])=={"ExecutionManifest.json","ReviewRecords.jsonl","ReviewReport.md"},"CRITIC_OUTPUT_SET")
 for n,h in rc["output_file_hashes"].items():require(sha(d/n)==h,"CRITIC_OUTPUT_HASH")
 em=read(d/"ExecutionManifest.json");allow={x["path"]:x["sha256"] for x in cfg["allowed_inputs"]}
 allow[str(task_config.relative_to(root))]=task_sha;allow[cfg["protocol"]]=cfg["protocol_sha256"]
 require(em["task_id"]==cfg["task_id"] and em["input_hashes"]==allow and set(em["actual_accessed_paths"])<=set(allow) and all(sha(root/p)==h for p,h in allow.items()),"CRITIC_INPUT_OR_ACCESS_DECLARATION")
 require(em["prior_exposure_declared"] is True and em["confirmatory_blind_claimed"] is False and em["forbidden_access_count"]==0,"CRITIC_EXPOSURE")
 # Controller receives explicit PI authorization in a separate turn before invocation.
 gf=run/"R2GeneratorFreezeReceipt.json";require(sha(gf)==freeze_sha,"GENERATOR_FREEZE_HASH")
 g=read(gf);require(g["mapping_release_authorized"] is False and all(sha(run/p)==h for p,h in g["files"].items()),"GENERATOR_OUTPUT_HASH")
 tasks=read(run/"reviewer_source_only/R2Review44.json");q={x["review_id"]:x for x in tasks};require(len(q)==44,"TASK_SET")
 rec=list(lines(d/"ReviewRecords.jsonl"));r={x["review_id"]:x for x in rec};require(len(r)==len(rec)==rc["completed_cases"]==44 and set(r)==set(q),"REVIEW_CASE_SET")
 s=read(root/"schemas/udf/u3r2/R2ReferenceReview_v0.1.schema.json");Draft202012Validator.check_schema(s);v=Draft202012Validator(s,format_checker=FormatChecker())
 authorities={x["path"]:x["sha256"] for x in cfg["allowed_inputs"] if x["role"]=="FIXED_PUBLIC_STANDARD"}
 require(len(authorities)==4,"REFERENCE_AUTHORITY_SET")
 vocab,vc=parse_standards(Standards(root))
 for rid,x in r.items():validate_reference(x,q[rid],v,vocab,authorities)
 # Only after native-reference validation open the private comparator index.
 comp={x["review_id"]:x for x in read(run/"controller_private/ControllerComparisonIndex.json") if x["batch"]=="ORIGINAL_NEW44"}
 require(set(comp)==set(q),"COMPARATOR_CASE_SET")
 un=read(run/"controller_private/FrozenTargetUniverse.json");u={tuple(x) for x in un["original"]};e={tuple(x) for x in un["extension"]}
 pool=defaultdict(list);sources={x["source_ref"] for x in tasks}
 for x in read(run/"controller_private/ProposalManifest.json").values():
  p=run/x["file"];require(sha(p)==x["sha256"],"PROPOSAL_PARTITION_HASH")
  for row in lines(p):
   if row["source_legacy_ref"] in sources:pool[row["source_legacy_ref"]].append(row)
 cases=[compare_case(r[rid],comp[rid],u,e,pool[q[rid]["source_ref"]]) for rid in sorted(q)]
 summary=aggregate(cases);summary.update({"verified_reference_cases":len(cases),"raw_standard_counts":vc,"reference_scope":"44 first developmental cases; only 19 current model","independent_gold_count":0,"critic_access_independently_proven":False})
 out.mkdir(parents=True);(out/"private").mkdir(mode=0o700)
 putl(out/"private/ReferenceComparisonRecords.jsonl",cases);put(out/"R2ReferenceComparisonReport.json",summary);print(json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--run",type=P.Path,required=True);a.add_argument("--freeze-sha",required=True);a.add_argument("--task-config",type=P.Path,required=True);a.add_argument("--task-sha",required=True);a.add_argument("--critic-receipt-sha",required=True);a.add_argument("--out",type=P.Path,required=True);a.add_argument("--pi-authorized-unblind",action="store_true");x=a.parse_args()
 require(x.pi_authorized_unblind,"PI_UNBLIND_AUTHORIZATION_REQUIRED");main(x.root,x.run,x.freeze_sha,x.task_config,x.task_sha,x.critic_receipt_sha,x.out)
