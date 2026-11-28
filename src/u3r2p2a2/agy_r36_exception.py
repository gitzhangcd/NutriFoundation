#!/usr/bin/env python3
"""R3.6 one-case execution-budget exception; frozen science and transport unchanged.
Both earlier case 016 attempts remain immutable. No fourth attempt or implicit
authorization for later terminal retries. Continuation uses the R2 adapter."""
import argparse,fcntl,hashlib,json,subprocess,sys
from pathlib import Path
import agy_r3_diagnostics as diag
r2=diag.r2
v=diag.v
VERSION="A2.5-R3.6-EXECUTION-EXCEPTION-v0.1"
PRIOR=diag.PRIOR
METHOD=diag.METHOD
REQUAL="222a4e937744b19b8e7530ab1d47ae2fbec5cd84ceb1d08ebc3367f68e3c5516"
PARENT_DIAG="baeede1435a88cfbdd0993ad72d6c456b5ca28cf43e9f3343947cf799d1e3f6c"
REGION_ERROR="48db176cfe9c77b78bece39c26e86b39c267f3e3125580c55963930efe9d4430"
OWNER_AUTH="Explicit owner authorization: versioned exhausted-budget exception for exactly one additional ordinal 016 semantic review, preserve both historical attempts, same original prompt/query/scientific method and 210-second deadline, continue 017–020 only after validation; no automatic fourth attempt."
ORDINAL=16
ATTEMPT=3
def req(x,c):v.require(x,c)
def scope(c,binding):
 req(c["version"]==VERSION and c["ordinal"]==16 and c["stage"]=="review" and c["attempt"]==3 and c["additional_dispatch_budget"]==1,"EXCEPTION_SCOPE")
 req(c["binding"]==binding and c["owner_authorization"]==OWNER_AUTH,"EXCEPTION_BINDING")
 req(c["original_attempt_budget"]==2 and c["timeout_seconds"]==210 and c["scientific_method_sha256"]==METHOD and c["requalification_receipt_sha256"]==REQUAL,"EXCEPTION_METHOD")
 req(c["fourth_attempt_authorized"] is False and c["comparison_authorized"] is False and c["mapping_release_authorized"] is False and c["remote_exactly_once_claimed"] is False,"EXCEPTION_BOUNDARY")
def consumption(d,c,binding):
 scope(c,binding)
 return {"version":VERSION,"contract_sha256":v.sha(d/"ExceptionContract.json"),"ordinal":16,"stage":"review","attempt":3,"budget_consumed":1,"prompt_sha256":binding["prompt_sha256"],"query_freeze_sha256":binding["query_freeze_sha256"],"automatic_redispatch":False}
def consume(d,c,binding,case,run):
 z=consumption(d,c,binding)
 req(not (d/"AuthorizationConsumed.json").exists(),"EXCEPTION_ALREADY_CONSUMED")
 req(not (d/"OutcomeReceipt.json").exists() and not (case/"CaseFreeze.json").exists(),"OUTCOME_EXISTS")
 req(not (case/"review_attempt_03").exists() and not (case/"review_attempt_04").exists() and not (run/"runtime/016_review_03").exists(),"EXCEPTION_ATTEMPT_EXISTS")
 v.obj(d/"AuthorizationConsumed.json",z)
 return z
def check_consumed(d,c,binding):
 req(v.load(d/"AuthorizationConsumed.json")==consumption(d,c,binding),"EXCEPTION_CONSUMPTION_BINDING")
def requal(root):
 p=root/v.BASE/"agy_r3_diag_002";old=root/v.BASE/"agy_r3_diag_001"
 z=v.load(v.filepin(p/"A2R35RuntimeRequalificationReceipt.json",REQUAL))
 req(z["status"]=="PASS_RUNTIME_REQUALIFICATION" and z["passed_diagnostics"]==z["offline_validation_replay_passed"]==3 and z["real_case_dispatches"]==0 and z["third_attempt_authorized"] is False,"REQUALIFICATION_GATE")
 req(z["scientific_method_sha256"]==METHOD and z["prior_retry_receipt_sha256"]==PRIOR and z["declared_model"]==v.MODEL and z["timeout_seconds"]==v.PROMPT_TIMEOUT==210,"REQUALIFICATION_METHOD")
 oldr=v.load(v.filepin(old/"A2R3DiagnosticResolutionReceipt.json",PARENT_DIAG))
 v.filepin(old/"R3ResolutionGate.json",oldr["resolution_gate_sha256"])
 v.filepin(Path(diag.__file__),oldr["diagnostic_code_sha256"])
 f=v.load(v.filepin(p/"DiagnosticFreeze.json",z["diagnostic_freeze_sha256"]))
 e=v.load(v.filepin(p/"RequalificationExecutionReceipt.json",z["execution_receipt_sha256"]))
 v.filepin(root/"src/u3r2p2a2/agy_r3_requalification.py",z["requalification_code_sha256"])
 om=v.load(v.filepin(old/"DiagnosticFreeze.json",oldr["diagnostic_freeze_sha256"]))
 req(f["prompts"]==om["prompts"] and f["fixture_sha256"]==om["fixture_sha256"] and e["results"]==z["results"] and e["passed_diagnostics"]==3,"REQUALIFICATION_LINEAGE")
 req(len(r2.tree_pins(old))==14 and r2.pinset_digest(r2.tree_pins(old))==f["prior_diagnostic_file_set_sha256"],"ORIGINAL_DIAGNOSTIC_DRIFT")
 req(v.sha(old/"synthetic_01_nonce/query_attempt_01/RawResponse.txt")==REGION_ERROR,"REGION_ERROR_BINDING")
 for i,row in enumerate(z["results"],1):
  name=("nonce","query","review")[i-1];kind="review" if i==3 else "query"
  req(row["name"]==name and row["status"]=="PASS" and row["validation_error"] is None and row["matches_prior_location_rejection_bytes"] is False,"REQUALIFICATION_RESULT")
  a=p/("synthetic_%02d_%s"%(i,name))/(kind+"_attempt_01")
  v.filepin(a/"Prompt.txt",f["prompts"][i-1]["prompt_sha256"])
  t=v.load(v.filepin(a/"Terminal.json",row["terminal_sha256"]))
  v.filepin(a/"RawResponse.txt",row["raw_response_sha256"])
  req(v.load(a/"DiagnosticValidation.json")==row and t["status"]=="RESPONSE_COMPLETE" and t["sent"] and t["rpc_returned"] and t["stop_reason"]=="end_turn" and t["model_id"]==v.MODEL and t["tool_requests"]==t["tool_updates"]==0,"REQUALIFICATION_TERMINAL")
 return z
def context(root,run):
 req(run==(root/v.BASE/"agy_r1_002").resolve() and not run.is_symlink(),"RUN_SCOPE")
 prior=v.load(v.filepin(run/"A2FrozenExecutionSegment_005R1RetryReceipt.json",PRIOR))
 req(prior["completed_cases"]==15 and prior["query_checkpoints"]==16 and prior["next_ordinal"]==16 and prior["further_retry_authorized"] is False,"PRIOR_SCOPE")
 v.filepin(run/"summaries/Run_019.json",prior["budget_exhausted_replay_summary_sha256"])
 v.filepin(run/"ReviewerMethodFreeze.json",METHOD)
 r2x=r2.context(root,run)
 r2.verify_accepted(root,run,run/"recovery_r2_008",r2x)
 qual=requal(root)
 priv=run/"reviewer_private";case=priv/"case_016"
 stage=r2x["stage"];task=r2x["task"];source=v.load(stage/task["source_packet"]);s=source[15];ss=v.digest(s);rid=s["review_id"]
 standards=v.Standards(stage,task["allowed_inputs"])
 qa=case/"query_attempt_01";qt=v.read_attempt(qa,METHOD,"query",ss)
 req(qt["status"]=="RESPONSE_COMPLETE" and qt["model_id"]==v.MODEL and qt["stop_reason"]=="end_turn" and qt["tool_requests"]==qt["tool_updates"]==0,"QUERY_RESPONSE")
 q=v.queries_ok(v.json_answer((qa/"RawResponse.txt").read_text()),[s])[rid]
 qv=v.load(qa/"Validation.json")
 req(qv=={"terminal_sha256":v.sha(qa/"Terminal.json"),"status":"PASS","error":None,"projection_sha256":v.digest(q)},"QUERY_VALIDATION")
 ar={"attempt":1,"terminal_sha256":v.sha(qa/"Terminal.json"),"validation_sha256":v.sha(qa/"Validation.json"),"raw_sha256":qt["raw_sha256"]}
 hits={k:standards.search(k,t) for k,t in q.items()}
 qp=case/"QueryFreeze.json";v.filepin(qp,prior["query_freeze_sha256"])
 req(v.load(qp)=={"method_sha256":METHOD,"source_sha256":ss,"origin":"AGY_CASE_QUERY","attempt":ar,"query":q,"hits":hits},"QUERY_REPLAY")
 prompt=v.review_prompt(s,q,hits,task["rules"])
 previous=[];sessions=[]
 for n in (1,2):
  a=case/("review_attempt_%02d"%n);st=prior["case_016_attempt_%02d"%n]
  t=v.read_attempt(a,METHOD,"review",ss);l=v.load(a/"Launch.json");val=v.load(a/"Validation.json")
  req(l["case_ordinal"]==16 and l["attempt"]==n and not l["tool_permission"] and t["sent"] and t["model_id"]==v.MODEL,"PRIOR_ATTEMPT_SCOPE")
  req((a/"Prompt.txt").read_bytes()==prompt.encode("utf8"),"ORIGINAL_PROMPT_DRIFT")
  req(v.sha(a/"Terminal.json")==st["terminal_sha256"] and v.sha(a/"Validation.json")==st["validation_sha256"] and t["raw_sha256"]==st["raw_response_sha256"] and val["status"]=="HOLD" and val["terminal_sha256"]==v.sha(a/"Terminal.json"),"PRIOR_ATTEMPT_PIN")
  if n==1:req(t["status"]=="FAILED_TERMINAL" and t["error"]=="ACP_TIMEOUT" and val["error"]=="ACP_TIMEOUT","PRIOR_TIMEOUT")
  else:req(t["status"]=="RESPONSE_COMPLETE" and t["stop_reason"]=="end_turn" and val["error"]=="JSONDecodeError" and t["raw_sha256"]==REGION_ERROR,"PRIOR_REGION_REJECTION")
  intent=v.load(a/"DispatchIntent.json");req(intent["session_id_sha256"]==t["session_id_sha256"] and intent["prompt_sha256"]==v.sha(a/"Prompt.txt"),"PRIOR_INTENT_BINDING")
  sessions.append(t["session_id_sha256"])
  previous.append({"attempt":n,"terminal_sha256":v.sha(a/"Terminal.json"),"validation_sha256":v.sha(a/"Validation.json"),"raw_sha256":t["raw_sha256"]})
 req(len(set(sessions))==2,"PRIOR_SESSION_DISTINCT")
 val=v.Draft202012Validator(v.load(stage/v.SCHEMA))
 def parse(x):
  full=v.project(x,s,q,hits)
  rec=v.validate_records(full,[s],{rid:q},{rid:hits},standards,val,task["allowed_inputs"])[0]
  return {"record":rec,"review_note":full["review_note"]}
 binding={"query_freeze_sha256":v.sha(qp),"source_sha256":ss,"prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),"original_attempts":previous,"original_session_hashes":sessions,"provider_reported_prior_error":"LOCATION_FAILED_PRECONDITION_400"}
 return {"prior":prior,"r2x":r2x,"case":case,"priv":priv,"stage":stage,"task":task,"probe":r2x["probe"],"binding":binding,"prompt":prompt,"parse":parse,"qual":qual}
def verify_contract(root,run,d,x):
 c=v.load(d/"ExceptionContract.json");scope(c,x["binding"])
 req(c["prior_retry_receipt_sha256"]==PRIOR and c["controller_code_sha256"]==v.sha(Path(__file__)),"EXCEPTION_CODE_DRIFT")
 test=root/"tests/u3r2p2a2/verify_a2_r36.py"
 req(c["test_code_sha256"]==v.sha(test),"EXCEPTION_TEST_DRIFT")
 tr=v.load(v.filepin(d/"SyntheticTestReceipt.json",c["synthetic_test_receipt_sha256"]))
 req(tr["status"]=="PASS" and tr["controller_code_sha256"]==c["controller_code_sha256"] and tr["test_code_sha256"]==c["test_code_sha256"],"EXCEPTION_TEST_PIN")
 for key,loc,count,prior_key in [
  ("original_private_pins",x["priv"],230,"private_file_set_sha256"),
  ("original_runtime_pins",run/"runtime",124,"runtime_file_set_sha256"),
  ("original_retry_pins",run/"retry_016_segment_005r1",3,"retry_contract_file_set_sha256")]:
  pins=c[key];req(len(pins)==count and r2.pinset_digest(pins)==x["prior"][prior_key],"EXCEPTION_ORIGINAL_SET")
  r2.pin_subset(loc,pins)
 for k,name,count in [("diagnostic_001_pins","agy_r3_diag_001",14),("diagnostic_002_pins","agy_r3_diag_002",33)]:
  req(len(c[k])==count and r2.tree_pins(root/v.BASE/name)==c[k],"DIAGNOSTIC_EVIDENCE_DRIFT")
 req(v.sha(run/"recovery_r2_008/OutcomeReceipt.json")==c["r2_outcome_sha256"],"R2_LINEAGE_DRIFT")
 r2.verify_contract(root,run,run/"recovery_r2_008",x["r2x"])
 req(not (x["case"]/"review_attempt_04").exists(),"FOURTH_ATTEMPT_FORBIDDEN")
 return c
def prepare(root,run,d,x):
 req(not d.exists(),"EXCEPTION_CONTRACT_EXISTS")
 diag.verify_original(root)
 req(not (x["case"]/"review_attempt_03").exists() and not (x["case"]/"CaseFreeze.json").exists(),"EXCEPTION_ATTEMPT_EXISTS")
 r2.check_live(run)
 test=root/"tests/u3r2p2a2/verify_a2_r36.py"
 t=subprocess.run([sys.executable,"-B",str(test)],cwd=root,capture_output=True,text=True,timeout=60)
 req(t.returncode==0 and "Ran " in t.stderr and "OK" in t.stderr,"R36_SYNTHETIC_TESTS")
 d.mkdir(mode=0o700)
 v.obj(d/"SyntheticTestReceipt.json",{"status":"PASS","controller_code_sha256":v.sha(Path(__file__)),"test_code_sha256":v.sha(test),"unittest_summary":t.stderr.strip().splitlines()[-3:]})
 c={"version":VERSION,"ordinal":16,"stage":"review","attempt":3,"additional_dispatch_budget":1,"original_attempt_budget":2,"timeout_seconds":210,"scientific_method_sha256":METHOD,"prior_retry_receipt_sha256":PRIOR,"requalification_receipt_sha256":REQUAL,"owner_authorization":OWNER_AUTH,"binding":x["binding"],"controller_code_sha256":v.sha(Path(__file__)),"test_code_sha256":v.sha(test),"synthetic_test_receipt_sha256":v.sha(d/"SyntheticTestReceipt.json"),"original_private_pins":r2.tree_pins(x["priv"]),"original_runtime_pins":r2.tree_pins(run/"runtime"),"original_retry_pins":r2.tree_pins(run/"retry_016_segment_005r1"),"diagnostic_001_pins":r2.tree_pins(root/v.BASE/"agy_r3_diag_001"),"diagnostic_002_pins":r2.tree_pins(root/v.BASE/"agy_r3_diag_002"),"r2_outcome_sha256":v.sha(run/"recovery_r2_008/OutcomeReceipt.json"),"fourth_attempt_authorized":False,"comparison_authorized":False,"mapping_release_authorized":False,"remote_exactly_once_claimed":False}
 v.obj(d/"ExceptionContract.json",c)
 verify_contract(root,run,d,x)
 print(json.dumps({"status":"R36_EXCEPTION_FROZEN","contract_sha256":v.sha(d/"ExceptionContract.json"),"additional_dispatch_budget":1,"synthetic_tests":t.stderr.strip().splitlines()[-3:],"prior_attempts_preserved":2}),flush=True)
def finish(root,run,d,x):
 c=verify_contract(root,run,d,x);check_consumed(d,c,x["binding"])
 case=x["case"];a=case/"review_attempt_03"
 req((a/"Terminal.json").is_file(),"EXCEPTION_UNCERTAIN_DISPATCH_STOP")
 t=v.read_attempt(a,METHOD,"review",x["binding"]["source_sha256"]);l=v.load(a/"Launch.json")
 req(l["case_ordinal"]==16 and l["attempt"]==3 and l["declared_model_required"]==v.MODEL and not l["tool_permission"],"EXCEPTION_LAUNCH_SCOPE")
 req((a/"Prompt.txt").read_bytes()==x["prompt"].encode("utf8"),"EXCEPTION_PROMPT_DRIFT")
 if t["sent"]:
  i=v.load(a/"DispatchIntent.json")
  req(i["model_id"]==v.MODEL and i["prompt_sha256"]==x["binding"]["prompt_sha256"] and i["session_id_sha256"]==t["session_id_sha256"] and i["session_id_sha256"] not in x["binding"]["original_session_hashes"],"EXCEPTION_SESSION_BINDING")
 value=None;failure=t["error"] or "RESPONSE_HOLD"
 if t["status"]=="RESPONSE_COMPLETE":
  req(t["sent"] and t["rpc_returned"] and t["model_id"]==v.MODEL and t["stop_reason"]=="end_turn" and t["tool_updates"]==t["tool_requests"]==0 and not t["error"],"EXCEPTION_RESPONSE_SCOPE")
  try:value=x["parse"](v.json_answer((a/"RawResponse.txt").read_text()));failure=None
  except Exception as e:failure=v.err(e)
 vv={"terminal_sha256":v.sha(a/"Terminal.json"),"status":"PASS" if value is not None and failure is None else "HOLD","error":failure}
 if vv["status"]=="PASS":vv["projection_sha256"]=v.digest(value)
 r2.exact_or_append(a/"Validation.json",vv)
 lineage={"execution_exception_version":VERSION,"exception_contract_sha256":v.sha(d/"ExceptionContract.json"),"authorization_consumed_sha256":v.sha(d/"AuthorizationConsumed.json"),"prior_retry_receipt_sha256":PRIOR,"requalification_receipt_sha256":REQUAL}
 cf=case/"CaseFreeze.json";recordp=case/"ReviewRecord.json"
 if vv["status"]=="PASS":
  r2.exact_or_append(recordp,value["record"])
  ar={"attempt":3,"terminal_sha256":v.sha(a/"Terminal.json"),"validation_sha256":v.sha(a/"Validation.json"),"raw_sha256":t["raw_sha256"]}
  r2.exact_or_append(cf,{"status":"CASE_STRUCTURAL_NATIVE_REFERENCE_FROZEN","case_ordinal":16,"method_sha256":METHOD,"source_sha256":x["binding"]["source_sha256"],"query_freeze_sha256":x["binding"]["query_freeze_sha256"],"review_attempt":ar,"record_sha256":v.sha(recordp),"review_note_sha256":v.digest(value["review_note"]),"scientific_reference_qualified":False,"mapping_release_authorized":False,"execution_exception":lineage})
 else:req(not cf.exists() and not recordp.exists(),"FAILED_EXCEPTION_HAS_RECORD")
 verify_contract(root,run,d,x)
 out={"version":VERSION,"status":"PASS_EXCEPTION_CASE_FROZEN" if cf.exists() else "HOLD_EXCEPTION_FAILED","ordinal":16,"attempt":3,"method_sha256":METHOD,"prior_attempts_preserved":2,"query_freeze_sha256":x["binding"]["query_freeze_sha256"],"same_original_prompt":True,"terminal_sha256":v.sha(a/"Terminal.json"),"validation_sha256":v.sha(a/"Validation.json"),"response_bytes":(a/"RawResponse.txt").stat().st_size,"prompt_wall_seconds":t["prompt_wall_seconds"],"terminal_status":t["status"],"stop_reason":t["stop_reason"],"validation_error":failure,"sent_intent":t["sent"],"case_freeze_sha256":v.sha(cf) if cf.exists() else None,"completed_at_exception":16 if cf.exists() else 15,"query_checkpoints":16,"new_query_dispatches":0,"authorization_budget_consumed":1,"fourth_attempt_authorized":False,"scientific_reference_qualified":False,"comparison_executed":False,"unblind":False,**lineage}
 r2.exact_or_append(d/"OutcomeReceipt.json",out)
 print(json.dumps(out,ensure_ascii=False),flush=True)
 return out
def main(root,run,mode,start=0,limit=0):
 d=run/"exception_r36_016"
 with (run/".controller.lock").open("a") as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  x=context(root,run)
  if mode=="prepare":prepare(root,run,d,x);return
  if mode=="execute":
   c=verify_contract(root,run,d,x)
   diag.verify_original(root)
   r2.check_live(run);consume(d,c,x["binding"],x["case"],run)
   print("R36 one-shot authorization consumed; only ordinal 016 review attempt 03",flush=True)
   v.invoke(root,run,x["case"],16,"review",3,x["prompt"],METHOD,x["binding"]["source_sha256"],x["stage"],x["task"],x["probe"])
   finish(root,run,d,x);return
  accepted=finish(root,run,d,x)
  if mode=="finalize":return
  oh=v.sha(d/"OutcomeReceipt.json");base=r2.tree_pins(x["priv"]);rt=r2.tree_pins(run/"runtime")
  count=len(list(x["priv"].glob("case_*/CaseFreeze.json")))
  req(all((x["priv"]/("case_%03d"%i)/"CaseFreeze.json").is_file() for i in range(1,count+1)),"CONTIGUOUS_CASES")
  before=set((run/"summaries").glob("Run_*.json"))
  if mode=="continue":
   req(accepted["status"]=="PASS_EXCEPTION_CASE_FROZEN","EXCEPTION_NOT_ACCEPTED")
   ir=v.load(d/"InitialReplayReceipt.json")
   req(ir["status"]=="PASS_ZERO_DISPATCH_REPLAY" and ir["completed_cases"]==16 and ir["outcome_sha256"]==oh and ir["new_dispatches"]==0,"INITIAL_REPLAY_REQUIRED")
   v.filepin(run/"summaries"/ir["summary_name"],ir["summary_sha256"])
   req(start==count+1 and 17<=start<=32 and 1<=limit<=33-start,"CONTINUATION_RANGE")
  else:req(mode=="replay" and start==limit==0,"MODE")
 oldinvoke=v.invoke;calls=[]
 def guard(*args,**kwargs):
  req(mode=="continue" and len(args)>=7 and start<=args[3]<start+limit and args[4] in ("query","review") and args[5] in (1,2),"CONTINUATION_DISPATCH_SCOPE")
  v.filepin(d/"OutcomeReceipt.json",oh)
  verify_contract(root,run,d,x)
  calls.append((args[3],args[4],args[5]))
  return oldinvoke(*args,**kwargs)
 v.invoke=guard
 try:r2.main(root,run,mode,limit)
 finally:v.invoke=oldinvoke
 with (run/".controller.lock").open("a") as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  verify_contract(root,run,d,x);v.filepin(d/"OutcomeReceipt.json",oh)
  r2.pin_subset(x["priv"],base);r2.pin_subset(run/"runtime",rt)
  new=set((run/"summaries").glob("Run_*.json"))-before;req(len(new)==1,"SUMMARY_CLOSURE")
  p=next(iter(new));z=v.load(p)
  req(not z["comparison_executed"] and not z["unblind"] and not z["mapping_release"],"SCIENTIFIC_BOUNDARY")
  req(z["completed_cases"]>=count and (accepted["case_freeze_sha256"] is None or z["case_freeze_hashes"]["case_016"]==accepted["case_freeze_sha256"]),"EXCEPTION_REPLAY_CLOSURE")
  receipt={"version":VERSION,"status":"PASS_ZERO_DISPATCH_REPLAY" if mode=="replay" else "CONTINUATION_VERIFIED","completed_cases":z["completed_cases"],"new_cases":z["new_cases"],"query_checkpoints":z["query_checkpoints_verified"],"new_dispatches":len(calls),"failure":z["failure"],"outcome_sha256":oh,"summary_name":p.name,"summary_sha256":v.sha(p),"case_freeze_hashes":z["case_freeze_hashes"]}
  if mode=="replay":
   req(not calls and z["new_cases"]==0 and z["replayed_cases"]==count and r2.tree_pins(x["priv"])==base and r2.tree_pins(run/"runtime")==rt,"ZERO_DISPATCH_REPLAY")
   if accepted["status"]=="PASS_EXCEPTION_CASE_FROZEN" and not (d/"InitialReplayReceipt.json").exists():
    req(count==16 and z["failure"] is None,"INITIAL_REPLAY_SCOPE");v.obj(d/"InitialReplayReceipt.json",receipt)
   else:v.obj(d/("Replay_"+p.stem+".json"),receipt)
  else:v.obj(d/("Continuation_"+p.stem+".json"),receipt)
 print(json.dumps(receipt,ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--mode",choices=["prepare","execute","finalize","replay","continue"],required=True);p.add_argument("--start",type=int,default=0);p.add_argument("--limit",type=int,default=0);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 main(Path.cwd().resolve(),a.out.resolve(),a.mode,a.start,a.limit)
