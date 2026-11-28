#!/usr/bin/env python3
"""R3.5: exact source-free runtime requalification; never dispatch a real case.
The original R3 diagnostic source, all original scientific evidence, and
the previous region-precondition failure are immutable. New run only."""
import argparse,fcntl,hashlib,json
from pathlib import Path
from types import SimpleNamespace
import agy_r3_diagnostics as d
v=d.v
r2=d.r2
VERSION="A2.5-R3.5-REQUALIFICATION-v0.1"
PARENT_RECEIPT="baeede1435a88cfbdd0993ad72d6c456b5ca28cf43e9f3343947cf799d1e3f6c"
def req(x,c):v.require(x,c)
def main(root,out):
 original,stage,probe,task=d.verify_original(root)
 parent=root/v.BASE/"agy_r3_diag_001"
 prior=v.load(v.filepin(parent/"A2R3DiagnosticResolutionReceipt.json",PARENT_RECEIPT))
 mf=v.load(v.filepin(parent/"DiagnosticFreeze.json",prior["diagnostic_freeze_sha256"]))
 prior_exec=v.load(v.filepin(parent/"DiagnosticExecutionReceipt.json",prior["diagnostic_execution_receipt_sha256"]))
 gate=v.load(v.filepin(parent/"R3ResolutionGate.json",prior["resolution_gate_sha256"]))
 v.filepin(Path(d.__file__),prior["diagnostic_code_sha256"])
 req(gate["third_attempt_authorized"] is False and gate["real_reference_dispatch_budget"]==0,"PARENT_GATE")
 req(prior_exec["completed_diagnostics"]==1 and prior_exec["passed_diagnostics"]==0 and prior_exec["real_case_dispatches"]==0,"PARENT_DIAG_STATE")
 pa=parent/"synthetic_01_nonce/query_attempt_01"
 v.filepin(pa/"Terminal.json",prior["nonce_terminal_sha256"])
 v.filepin(pa/"DiagnosticValidation.json",prior["nonce_validation_sha256"])
 v.filepin(pa/"RawResponse.txt",prior["identical_response_sha256"])
 oldpins=r2.tree_pins(parent)
 req(out==(root/v.BASE/"agy_r3_diag_002").resolve() and not out.exists(),"NEW_DIAGNOSTIC_DIRECTORY_ONLY")
 s,rules,q,hits,by,hashes=d.fixture()
 expected={"diagnostic":"R3_SYNTHETIC_NONCE_71A9","status":"ready","integers":[2,5,11]}
 schema=v.load(stage/v.SCHEMA);v.Draft202012Validator.check_schema(schema);val=v.Draft202012Validator(schema)
 def review_parse(j):
  full=v.project(j,s,q,hits)
  rec=v.validate_records(full,[s],{s["review_id"]:q},{s["review_id"]:hits},SimpleNamespace(by=by),val,hashes)
  req(len(rec)==1,"SYNTHETIC_REVIEW_COUNT")
 jobs=[
  ("nonce","query","This is a source-free synthetic transport diagnostic. No tools, no previous context. Return exactly this JSON object, with no other text: "+v.canon(expected),lambda j:req(j==expected,"NONCE_MISMATCH")),
  ("query","query",v.query_prompt(s,rules),lambda j:v.queries_ok(j,[s])),
  ("review","review",v.review_prompt(s,q,hits,rules),review_parse)]
 prompts=[{"name":n,"stage":k,"prompt_sha256":hashlib.sha256(p.encode()).hexdigest(),"prompt_bytes":len(p.encode())} for n,k,p,_ in jobs]
 fixture_sha=v.digest({"source":s,"rules":rules,"q":q,"hits":hits})
 req(prompts==mf["prompts"] and fixture_sha==mf["fixture_sha256"],"EXACT_DIAGNOSTIC_PROMPT_DRIFT")
 req(v.MODEL==mf["model_id"] and v.PROMPT_TIMEOUT==mf["timeout_seconds"]==210,"MODEL_OR_DEADLINE_DRIFT")
 def preserve():
  d.verify_original(root)
  req(r2.tree_pins(parent)==oldpins,"ORIGINAL_DIAGNOSTIC_DRIFT")
 with (original/".controller.lock").open("a") as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  preserve()
  out.mkdir(mode=0o700)
  manifest={"version":VERSION,"parent_diagnostic_receipt_sha256":PARENT_RECEIPT,"parent_diagnostic_freeze_sha256":prior["diagnostic_freeze_sha256"],"parent_resolution_gate_sha256":prior["resolution_gate_sha256"],"scientific_method_sha256":d.METHOD,"prior_retry_receipt_sha256":d.PRIOR,"original_diagnostic_code_sha256":prior["diagnostic_code_sha256"],"requalification_code_sha256":v.sha(Path(__file__)),"prior_diagnostic_file_count":len(oldpins),"prior_diagnostic_file_set_sha256":r2.pinset_digest(oldpins),"model_id":v.MODEL,"same_frozen_ACP_invoke":True,"timeout_seconds":v.PROMPT_TIMEOUT,"synthetic_only":True,"fixture_sha256":fixture_sha,"prompts":prompts,"exact_original_prompts":True,"diagnostic_dispatch_budget":3,"real_case_dispatch_budget":0,"retry_budget":0,"stop_on_any_failed_prerequisite":True,"third_attempt_authorized":False}
  v.obj(out/"DiagnosticFreeze.json",manifest);mh=v.sha(out/"DiagnosticFreeze.json")
  print(json.dumps({"status":"R3_5_REQUALIFICATION_FROZEN","manifest_sha256":mh,"prompt_sizes":[p["prompt_bytes"] for p in prompts],"old_diagnostic_files":len(oldpins),"real_case_dispatch_budget":0}),flush=True)
  results=[]
  for idx,(name,kind,prompt,parse) in enumerate(jobs,1):
   preserve()
   req(hashlib.sha256(prompt.encode()).hexdigest()==prompts[idx-1]["prompt_sha256"],"PROMPT_DRIFT")
   case=out/("synthetic_%02d_%s"%(idx,name));case.mkdir(mode=0o700)
   ss=v.digest({"diagnostic":name,"fixture_sha256":fixture_sha})
   t=v.invoke(root,out,case,idx,kind,1,prompt,mh,ss,stage,task,probe)
   a=case/(kind+"_attempt_01")
   req(v.read_attempt(a,mh,kind,ss)==t,"TERMINAL_PIN")
   raw=(a/"RawResponse.txt").read_text(errors="replace")
   passed=False;error=t["error"]
   if t["status"]=="RESPONSE_COMPLETE":
    try:
     req(t["sent"] and t["rpc_returned"] and t["model_id"]==v.MODEL and t["stop_reason"]=="end_turn" and t["tool_requests"]==t["tool_updates"]==0,"DIAG_TERMINAL_SCOPE")
     parse(v.json_answer(raw));passed=True;error=None
    except Exception as e:error=v.err(e)
   row={"name":name,"status":"PASS" if passed else "HOLD","terminal_status":t["status"],"stop_reason":t["stop_reason"],"rpc_returned":t["rpc_returned"],"rpc_error_code":t["rpc_error_code"],"declared_model":t["model_id"],"sent_intent":t["sent"],"prompt_wall_seconds":t["prompt_wall_seconds"],"response_bytes":(a/"RawResponse.txt").stat().st_size,"tool_requests":t["tool_requests"],"tool_updates":t["tool_updates"],"validation_error":error,"terminal_sha256":v.sha(a/"Terminal.json"),"raw_response_sha256":v.sha(a/"RawResponse.txt"),"matches_prior_location_rejection_bytes":(a/"RawResponse.txt").read_bytes()==(pa/"RawResponse.txt").read_bytes(),"response_diagnostic":d.classify(raw)}
   v.obj(a/"DiagnosticValidation.json",row)
   results.append(row)
   print(json.dumps({"diagnostic":row},ensure_ascii=False),flush=True)
   if not passed:break
  preserve()
  passed=len(results)==3 and all(x["status"]=="PASS" for x in results)
  final={"version":VERSION,"status":"PASS_RUNTIME_REQUALIFICATION" if passed else "HOLD_RUNTIME_REQUALIFICATION","diagnostic_method_sha256":mh,"parent_diagnostic_receipt_sha256":PARENT_RECEIPT,"scientific_method_sha256":d.METHOD,"original_prompt_hashes_match":True,"planned_diagnostics":3,"dispatched_diagnostics":len(results),"passed_diagnostics":sum(x["status"]=="PASS" for x in results),"not_dispatched_diagnostics":3-len(results),"results":results,"original_diagnostic_files_unchanged":len(oldpins),"original_private_files_unchanged":230,"original_runtime_files_unchanged":124,"original_retry_contract_files_unchanged":3,"real_reference_cases":15,"real_query_checkpoints":16,"real_case_dispatches":0,"case_016_remaining_attempt_budget":0,"third_attempt_authorized":False,"comparison_executed":False,"unblind":False,"mapping_release":0,"scientific_reference_qualified":False}
  v.obj(out/"RequalificationExecutionReceipt.json",final);print(json.dumps(final,ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 main(Path.cwd().resolve(),a.out.resolve())
