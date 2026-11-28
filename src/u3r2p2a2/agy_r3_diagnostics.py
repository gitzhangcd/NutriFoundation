#!/usr/bin/env python3
"""A2.5-R3: source-free AGY transport diagnostics. No real case dispatch.
All fixtures fictional, no comparator or actual authority records are loaded into prompts.
Frozen v0.2 ACP invocation reused verbatim; one call per diagnostic, no retries."""
import argparse,fcntl,hashlib,json,os,re,sys
from pathlib import Path
from types import SimpleNamespace
import agy_r2_recovery as r2
v=r2.v
VERSION="A2.5-R3-DIAGNOSTIC-v0.1"
PRIOR="5252b23f7b24f58deb00f12e8e40a41e2dca34e278dee9aa6863ce86e9e56fac"
METHOD="08056819875d23e3c507b72d55eca479319fe737dbf4d7fa45bedc78ad2a6bd8"
def req(x,c):v.require(x,c)
def fixture():
 # Fictional concept and fictional authority rows; no existing records,
 # no sampled source text, no retrieval outcomes and no case 016 details.
 s={"review_id":"SYNTH-R3-ALPHA","source_ref":"synthetic@"+("a"*64),"source_scope":"fixture","source_native_label":"imaginary zorbfruit, peeled, steamed","native_kind":"INGREDIENT_REFERENCE","artifact_sha256":"a"*64,"source_locator":{"row":1},"native_aliases":["fictional zorbfruit"],"reference_recipe_ingredient_names":[],"context_note":"Invented diagnostic fixture; not an actual food or a real standard entry."}
 rules=["All source and authority entries are fictional synthetic test records. Do not use real-world knowledge. Return the exact JSON transport structure. Do not search, use tools or consult prior sessions. Unknown source facts remain unresolved. This diagnostic is not a scientific reference."]
 q={k:["zorbfruit","peeled zorbfruit","steamed zorbfruit"] for k in v.S}
 hits={};by={};hashes={}
 # 45 unique synthetic records. Evidence keys deliberately use invented IDs.
 variants=["peeled steamed zorbfruit","unpeeled raw zorbfruit","zorbfruit juice","zorbfruit seed powder","sweetened zorbfruit composite"]
 for si,sysname in enumerate(v.S):
  hh={};art=str(si+1)*64;hashes["fixture:"+sysname]=art
  for ti,term in enumerate(q[sysname]):
   rows=[]
   for ri,label in enumerate(variants):
    k=[sysname,("2026-09-20","2018-04","2015-16")[si],"urn:synthetic:r3:%d:%d:%d"%(si,ti,ri)]
    row={"target_key":k,"target_native_label":label+" (fictional entry %d)"%(ti+1),"target_locator":"fixture:%s:row:%d"%(sysname,ti*5+ri+1),"artifact_sha256":art,"raw_aliases":["imaginary "+label],"raw_definition":"Synthetic diagnostic-only entry. The named preparation, edible part, or mixture is exactly as labeled. No additional composition, species, origin or nutrient amount is asserted."}
    by[tuple(k)]=row;rows.append(row)
   hh[term]=rows
  hits[sysname]=hh
 return s,rules,q,hits,by,hashes
def classify(raw):
 # Only nonsemantic technical markers, not arbitrary response text.
 low=raw.lower();patterns={"quota":r"quota|rate.limit|resource.exhausted|too many requests|usage.limit","auth":r"unauthenticated|authentication.failed|invalid.token|token.expired|sign.in|log.in","provider":r"model.unavailable|service.unavailable|internal.server.error|overloaded|try again later","http_429":r"\b429\b","http_503":r"\b503\b","safety":r"safety.filter|content.filter|blocked.prompt"}
 try:shape=type(v.json_answer(raw)).__name__
 except Exception:shape="NOT_JSON"
 return {"shape":shape,"recognized_marker_counts":{k:len(re.findall(p,low)) for k,p in patterns.items()}}
def verify_original(root):
 run=root/v.BASE/"agy_r1_002";d=run/"recovery_r2_008";priv=run/"reviewer_private"
 prior=v.load(v.filepin(run/"A2FrozenExecutionSegment_005R1RetryReceipt.json",PRIOR))
 req(prior["completed_cases"]==15 and prior["query_checkpoints"]==16 and prior["next_ordinal"]==16 and prior["further_retry_authorized"] is False,"PRIOR_SCOPE")
 m=v.load(v.filepin(run/"ReviewerMethodFreeze.json",METHOD))
 for k,h in m["code_sha256"].items():v.filepin(root/"src/u3r2p2a2"/k,h)
 for k,h in m["prior_R1_failure_pins"].items():v.filepin(root/v.BASE/"agy_r1_001"/k,h)
 stage,prep,probe=v.verify(root)
 for k,h in prep["reviewer_staging_sha256"].items():v.filepin(stage/k,h)
 v.filepin(root/v.BASE/"local_001/A2RetrievalFreezeReceipt.json",v.FREEZE_SHA)
 r2p=v.load(v.filepin(run/"A2R2RecoveryExecutionReceipt.json",prior["case_008_recovery_receipt_sha256"]))
 v.filepin(root/"src/u3r2p2a2/agy_r2_recovery.py",r2p["runner_code_sha256"])
 for k,h in r2p["recovery_artifact_sha256"].items():v.filepin(d/k,h)
 rec=v.load(d/"Reconciliation.json")
 r2.pin_subset(priv,rec["original_private_file_pins"]);r2.pin_subset(run/"runtime/008_review_01",rec["original_runtime_file_pins"])
 req(not (priv/"case_008/review_attempt_01/Terminal.json").exists(),"ORIGINAL_008_UNKNOWN")
 for key,loc,count in [("private_file_set_sha256",priv,230),("runtime_file_set_sha256",run/"runtime",124),("retry_contract_file_set_sha256",run/"retry_016_segment_005r1",3)]:
  pins=r2.tree_pins(loc);req(len(pins)==count and r2.pinset_digest(pins)==prior[key],"ORIGINAL_SET_DRIFT")
 v.filepin(run/"summaries/Run_019.json",prior["budget_exhausted_replay_summary_sha256"])
 req(not (priv/"case_016/CaseFreeze.json").exists() and not (priv/"case_017").exists(),"REAL_CASE_SCOPE")
 req(sorted(x.name for x in (priv/"case_016").glob("review_attempt_*"))==["review_attempt_01","review_attempt_02"],"REAL_ATTEMPT_SCOPE")
 req(v.load(run/"retry_016_segment_005r1/AuthorizationConsumed.json")["budget_consumed"]==1,"OLD_GRANT")
 v.filepin(Path.home()/".local/bin/agy",v.BINARY_SHA)
 # Only source packet pathname used for sandbox read-denial probe; no packet
 # content, actual source cases or authority row content used here.
 task=v.load(stage/"A2ReviewTask.json")
 return run,stage,probe,task
def main(root,out):
 original,stage,probe,task=verify_original(root)
 req(out==(root/v.BASE/"agy_r3_diag_001").resolve() and not out.exists(),"DIAG_SCOPE_OR_EXISTS")
 with (original/".controller.lock").open("a") as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  out.mkdir(mode=0o700)
  s,rules,q,hits,by,hashes=fixture()
  expected={"diagnostic":"R3_SYNTHETIC_NONCE_71A9","status":"ready","integers":[2,5,11]}
  jobs=[
   ("nonce","query","This is a source-free synthetic transport diagnostic. No tools, no previous context. Return exactly this JSON object, with no other text: "+v.canon(expected),lambda j:req(j==expected,"NONCE_MISMATCH")),
   ("query","query",v.query_prompt(s,rules),lambda j:v.queries_ok(j,[s])),
   ("review","review",v.review_prompt(s,q,hits,rules),None),
  ]
  schema=v.load(stage/v.SCHEMA);v.Draft202012Validator.check_schema(schema);val=v.Draft202012Validator(schema)
  def validate_review(j):
   full=v.project(j,s,q,hits)
   rec=v.validate_records(full,[s],{s["review_id"]:q},{s["review_id"]:hits},SimpleNamespace(by=by),val,hashes)
   return {"projected_records":len(rec),"schema_and_synthetic_locator_validation":"PASS"}
  jobs[-1]=(jobs[-1][0],jobs[-1][1],jobs[-1][2],validate_review)
  manifest={"version":VERSION,"scientific_method_sha256":METHOD,"prior_retry_receipt_sha256":PRIOR,"diagnostic_code_sha256":v.sha(Path(__file__)),"model_id":v.MODEL,"same_frozen_ACP_invoke":True,"timeout_seconds":v.PROMPT_TIMEOUT,"synthetic_only":True,"real_case_dispatch_budget":0,"diagnostic_dispatch_budget":len(jobs),"retry_budget":0,"fixture_sha256":v.digest({"source":s,"rules":rules,"q":q,"hits":hits}),"prompts":[{"name":name,"stage":kind,"prompt_sha256":hashlib.sha256(p.encode()).hexdigest(),"prompt_bytes":len(p.encode())} for name,kind,p,_ in jobs],"no_scientific_promotion":True}
  v.obj(out/"DiagnosticFreeze.json",manifest);mh=v.sha(out/"DiagnosticFreeze.json")
  print(json.dumps({"status":"R3_DIAGNOSTIC_FROZEN","method_sha256":mh,"prompt_sizes":[(j["name"],j["prompt_bytes"]) for j in manifest["prompts"]],"synthetic_authority_rows":len(by),"real_case_dispatches":0}),flush=True)
  results=[]
  for idx,(name,kind,prompt,parse) in enumerate(jobs,1):
   case=out/("synthetic_%02d_%s"%(idx,name));case.mkdir(mode=0o700)
   ss=v.digest({"diagnostic":name,"fixture_sha256":manifest["fixture_sha256"]})
   t=v.invoke(root,out,case,idx,kind,1,prompt,mh,ss,stage,task,probe)
   a=case/(kind+"_attempt_01");raw=(a/"RawResponse.txt").read_text(errors="replace")
   read=v.read_attempt(a,mh,kind,ss);req(read==t,"TERMINAL_PIN")
   error=t["error"];passed=False
   if t["status"]=="RESPONSE_COMPLETE":
    try:
     req(t["sent"] and t["rpc_returned"] and t["model_id"]==v.MODEL and t["stop_reason"]=="end_turn" and t["tool_requests"]==t["tool_updates"]==0,"DIAG_TERMINAL_SCOPE")
     parse(v.json_answer(raw));passed=True;error=None
    except Exception as e:error=v.err(e)
   row={"name":name,"status":"PASS" if passed else "HOLD","terminal_status":t["status"],"stop_reason":t["stop_reason"],"rpc_returned":t["rpc_returned"],"rpc_error_code":t["rpc_error_code"],"declared_model":t["model_id"],"sent_intent":t["sent"],"prompt_wall_seconds":t["prompt_wall_seconds"],"response_bytes":(a/"RawResponse.txt").stat().st_size,"tool_requests":t["tool_requests"],"tool_updates":t["tool_updates"],"validation_error":error,"terminal_sha256":v.sha(a/"Terminal.json"),"raw_response_sha256":v.sha(a/"RawResponse.txt"),"response_diagnostic":classify(raw)}
   v.obj(a/"DiagnosticValidation.json",row);results.append(row)
   print(json.dumps({"diagnostic":row},ensure_ascii=False),flush=True)
   # If the simple session/nonce call fails, stop without consuming the more
   # complex diagnostic calls. Otherwise run both independently; no retry.
   if idx==1 and not passed:break
  verify_original(root)
  final={"status":"PASS_SOURCE_FREE_RUNTIME_DIAGNOSTICS" if len(results)==3 and all(x["status"]=="PASS" for x in results) else "HOLD_DIAGNOSTIC_FAILURE","version":VERSION,"diagnostic_method_sha256":mh,"scientific_method_sha256":METHOD,"prior_retry_receipt_sha256":PRIOR,"completed_diagnostics":len(results),"passed_diagnostics":sum(x["status"]=="PASS" for x in results),"results":results,"synthetic_authority_rows":len(by),"original_private_pins":230,"original_runtime_pins":124,"original_retry_contract_pins":3,"real_reference_cases":15,"real_query_checkpoints":16,"real_case_dispatches":0,"case_016_remaining_attempt_budget":0,"third_attempt_authorized":False,"comparison_executed":False,"unblind":False,"mapping_release":0,"scientific_reference_qualified":False}
  v.obj(out/"DiagnosticExecutionReceipt.json",final);print(json.dumps(final,ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 main(Path.cwd().resolve(),a.out.resolve())
