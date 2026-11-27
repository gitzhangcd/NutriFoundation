#!/usr/bin/env python3
"""A2.5-R2 controller-only reconciliation for ordinal 008.
The frozen v0.2 science, browser, transport and ACP invoke are unchanged.
The first attempt remains UNKNOWN, not a fabricated model terminal.
One additional local dispatch may be authorized; remote exactly-once is
not asserted. After consumption, recovery is read/validate only."""
import argparse,fcntl,hashlib,json,os,subprocess,sys
from pathlib import Path
import agy_r1_runner_v2 as v
VERSION="A2.5-R2-EXECUTION-v0.1"
METHOD_SHA="08056819875d23e3c507b72d55eca479319fe737dbf4d7fa45bedc78ad2a6bd8"
RECOVERY_SHA="9791895608de2c95d0c3d2d58f8be59b57986cf879a1471fdddc1a83170b8e2a"
ORDINAL=8
STAGE="review"
ATTEMPT=2
OWNER_AUTH="User explicitly authorized A2.5-R2 versioned interrupted-dispatch recovery, preserving all case 008 history and the existing query/scientific method, exactly one additional semantic-review execution; continue original order only after validation."
def req(x,c):v.require(x,c)
def tree_pins(d):
 req(d.is_dir() and not d.is_symlink(),"PIN_DIRECTORY")
 out={}
 for p in sorted(d.rglob("*")):
  req(not p.is_symlink(),"PIN_SYMLINK")
  if p.is_file():out[str(p.relative_to(d))]=v.sha(p)
 return out
def pin_subset(d,pins):
 req(isinstance(pins,dict) and bool(pins),"PIN_SET")
 for k,h in pins.items():
  p=Path(k);req(not p.is_absolute() and ".." not in p.parts,"PIN_PATH")
  v.filepin(d/p,h)
def pinset_digest(pins):
 return hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def exact_or_append(p,z):
 if p.exists():req(not p.is_symlink() and v.load(p)==z,"APPEND_ONLY_DRIFT")
 else:v.obj(p,z)
def original_attempt(case,mh,ss,prompt,query_sha):
 req(v.sha(case/"QueryFreeze.json")==query_sha,"QUERY_PIN")
 a=case/"review_attempt_01"
 req(set(p.name for p in a.iterdir())=={"Launch.json","Prompt.txt","DispatchIntent.json","RawResponse.txt"},"FIRST_ATTEMPT_FILE_SET")
 req(all(p.is_file() and not p.is_symlink() for p in a.iterdir()),"FIRST_ATTEMPT_REGULAR")
 req(not (a/"Terminal.json").exists() and not (a/"Validation.json").exists(),"ORIGINAL_TERMINAL_PRESENT")
 l=v.load(a/"Launch.json");i=v.load(a/"DispatchIntent.json")
 req(l["method_sha256"]==mh and l["source_sha256"]==ss and l["case_ordinal"]==ORDINAL and l["stage"]==STAGE and l["attempt"]==1 and not l["tool_permission"],"ORIGINAL_LAUNCH_SCOPE")
 req(l["declared_model_required"]==v.MODEL==i["model_id"],"ORIGINAL_MODEL")
 req(v.sha(a/"Prompt.txt")==l["prompt_sha256"]==i["prompt_sha256"],"ORIGINAL_PROMPT_PIN")
 req((a/"Prompt.txt").read_bytes()==prompt.encode("utf8"),"ORIGINAL_PROMPT_DRIFT")
 req((a/"RawResponse.txt").stat().st_size==0,"ORIGINAL_RESPONSE_NOT_EMPTY")
 return {"launch_sha256":v.sha(a/"Launch.json"),"dispatch_intent_sha256":v.sha(a/"DispatchIntent.json"),"prompt_sha256":v.sha(a/"Prompt.txt"),"raw_response_sha256":v.sha(a/"RawResponse.txt"),"query_freeze_sha256":query_sha,"source_sha256":ss,"old_session_sha256":i["session_id_sha256"],"native_ACP_terminal_outcome":"UNKNOWN"}
def scope(c,original,method):
 req(c["version"]==VERSION and c["method_sha256"]==method and c["ordinal"]==ORDINAL and c["stage"]==STAGE and c["attempt"]==ATTEMPT and c["additional_dispatch_budget"]==1,"AUTH_SCOPE")
 req(c["original"]==original and c["owner_authorization"]==OWNER_AUTH,"AUTH_BINDING")
 req(c["remote_exactly_once_claimed"] is False and c["comparison_authorized"] is False and c["scientific_release_authorized"] is False,"AUTH_BOUNDARY")
def consume(d,c,original,method):
 scope(c,original,method)
 req(not (d/"AuthorizationConsumed.json").exists(),"AUTH_ALREADY_CONSUMED")
 req(not (d/"OutcomeReceipt.json").exists(),"OUTCOME_EXISTS")
 z={"version":VERSION,"contract_sha256":v.sha(d/"RecoveryContract.json"),"reconciliation_sha256":v.sha(d/"Reconciliation.json"),"ordinal":ORDINAL,"stage":STAGE,"attempt":ATTEMPT,"prompt_sha256":original["prompt_sha256"],"query_freeze_sha256":original["query_freeze_sha256"],"additional_dispatch_budget_consumed":1,"automatic_redispatch":False}
 v.obj(d/"AuthorizationConsumed.json",z)
 return z
def check_consumed(d,c,original,mh):
 scope(c,original,mh)
 z=v.load(d/"AuthorizationConsumed.json")
 req(z=={"version":VERSION,"contract_sha256":v.sha(d/"RecoveryContract.json"),"reconciliation_sha256":v.sha(d/"Reconciliation.json"),"ordinal":ORDINAL,"stage":STAGE,"attempt":ATTEMPT,"prompt_sha256":original["prompt_sha256"],"query_freeze_sha256":original["query_freeze_sha256"],"additional_dispatch_budget_consumed":1,"automatic_redispatch":False},"CONSUMPTION_BINDING")
 return z
def check_live(run):
 ps=subprocess.run(["/bin/ps","-axo","pid=,ppid=,command="],capture_output=True,text=True,check=True).stdout.splitlines()
 # Local observation only; it cannot attest to remote billing or termination.
 other=[l for l in ps if ("agy_r1_runner_v2.py" in l and "agy_r1_002" in l) or str(run/"runtime") in l]
 req(not other,"LIVE_MATCHING_RUNTIME")
 return {"matching_local_processes":0,"remote_terminal_outcome":"UNKNOWN","controller_lock_held":True}
def context(root,run):
 req(run==(root/v.BASE/"agy_r1_002").resolve() and not run.is_symlink(),"RUN_SCOPE")
 stage,prep,probe=v.verify(root);task=v.load(stage/"A2ReviewTask.json");source=v.load(stage/task["source_packet"])
 req(len(source)==32 and len({s["review_id"] for s in source})==32,"SOURCE32")
 v.filepin(Path.home()/".local/bin/agy",v.BINARY_SHA)
 for k,h in v.R1_PRIOR_PINS.items():v.filepin(root/v.BASE/"agy_r1_001"/k,h)
 standards=v.Standards(stage,task["allowed_inputs"]);oq,oh,pm=v.parent(root,source,standards)
 mh=v.sha(run/"ReviewerMethodFreeze.json")
 req(mh==METHOD_SHA and v.load(run/"ReviewerMethodFreeze.json")==v.metadata(root,stage,prep,source,pm),"METHOD_DRIFT")
 prev=v.load(v.filepin(run/"A2FrozenExecutionSegment_003R1RecoveryReceipt.json",RECOVERY_SHA))
 req(prev["completed_cases"]==7 and prev["query_checkpoints_verified"]==8 and not prev["comparison_executed"],"RECOVERY_PARENT")
 v.filepin(run/"summaries/Run_008.json",prev["recovery_summary_sha256"])
 priv=run/"reviewer_private";case=priv/"case_008";s=source[7];ss=v.digest(s);rid=s["review_id"];qa=case/"query_attempt_01"
 qt=v.read_attempt(qa,mh,"query",ss)
 req(qt["status"]=="RESPONSE_COMPLETE" and qt["model_id"]==v.MODEL and qt["stop_reason"]=="end_turn" and qt["tool_requests"]==qt["tool_updates"]==0,"QUERY_RESPONSE")
 q=v.queries_ok(v.json_answer((qa/"RawResponse.txt").read_text()),[s])[rid]
 qv=v.load(qa/"Validation.json")
 req(qv=={"terminal_sha256":v.sha(qa/"Terminal.json"),"status":"PASS","error":None,"projection_sha256":v.digest(q)},"QUERY_VALIDATION")
 ar={"attempt":1,"terminal_sha256":v.sha(qa/"Terminal.json"),"validation_sha256":v.sha(qa/"Validation.json"),"raw_sha256":qt["raw_sha256"]}
 hits={k:standards.search(k,t) for k,t in q.items()}
 qp=case/"QueryFreeze.json";query_sha=prev["case_008"]["query_freeze_sha256"]
 v.filepin(qp,query_sha)
 req(v.load(qp)=={"method_sha256":mh,"source_sha256":ss,"origin":"AGY_CASE_QUERY","attempt":ar,"query":q,"hits":hits},"QUERY_REPLAY")
 prompt=v.review_prompt(s,q,hits,task["rules"])
 orig=original_attempt(case,mh,ss,prompt,query_sha)
 for k in ("launch_sha256","dispatch_intent_sha256","prompt_sha256","raw_response_sha256","query_freeze_sha256"):req(orig[k]==prev["case_008"][k],"ORIGINAL_RECOVERY_PIN")
 schema=v.load(stage/v.SCHEMA);v.Draft202012Validator.check_schema(schema);val=v.Draft202012Validator(schema)
 def parse(x):
  full=v.project(x,s,q,hits)
  rec=v.validate_records(full,[s],{rid:q},{rid:hits},standards,val,task["allowed_inputs"])[0]
  return {"record":rec,"review_note":full["review_note"]}
 return {"stage":stage,"prep":prep,"probe":probe,"task":task,"priv":priv,"case":case,"source_sha":ss,"method_sha":mh,"prev":prev,"original":orig,"prompt":prompt,"parse":parse}
def prepare(root,run,d,x):
 req(not d.exists(),"R2_CONTRACT_EXISTS")
 req(not (x["case"]/"CaseFreeze.json").exists() and not (x["case"]/"review_attempt_02").exists(),"CASE_ALREADY_RECOVERED_OR_ATTEMPTED")
 req(not (run/"runtime/008_review_02").exists(),"RECOVERY_RUNTIME_EXISTS")
 live=check_live(run)
 pins=tree_pins(x["priv"])
 req(len(pins)==98 and pinset_digest(pins)==x["prev"]["private_checkpoint_file_set_sha256"],"RECOVERY_PRIVATE_PIN_SET")
 runtime=tree_pins(run/"runtime/008_review_01")
 req(len(runtime)==4,"ORIGINAL_RUNTIME_SET")
 # Tests are actually run in the project Python before preparing authorization.
 test= root/"tests/u3r2p2a2/verify_a2_r2.py"
 t=subprocess.run([sys.executable,"-B",str(test)],cwd=root,capture_output=True,text=True,timeout=60)
 req(t.returncode==0 and "Ran " in t.stderr and "OK" in t.stderr,"R2_SYNTHETIC_TESTS")
 d.mkdir(mode=0o700)
 v.obj(d/"SyntheticTestReceipt.json",{"status":"PASS","test_code_sha256":v.sha(test),"runner_code_sha256":v.sha(Path(__file__)),"unittest_summary":t.stderr.strip().splitlines()[-3:]})
 rec={"version":VERSION,"status":"UNCERTAIN_DISPATCH_NO_TERMINAL_RECONCILED_FOR_BOUNDED_RECOVERY","original":x["original"],"prior_recovery_receipt_sha256":RECOVERY_SHA,"original_private_file_pins":pins,"original_runtime_file_pins":runtime,"local_observation":live,"native_terminal_written":False,"remote_completion_or_billing_attested":False}
 v.obj(d/"Reconciliation.json",rec)
 contract={"version":VERSION,"method_sha256":x["method_sha"],"ordinal":ORDINAL,"stage":STAGE,"attempt":ATTEMPT,"additional_dispatch_budget":1,"original":x["original"],"owner_authorization":OWNER_AUTH,"reconciliation_sha256":v.sha(d/"Reconciliation.json"),"synthetic_test_receipt_sha256":v.sha(d/"SyntheticTestReceipt.json"),"controller_code_sha256":v.sha(Path(__file__)),"test_code_sha256":v.sha(test),"remote_exactly_once_claimed":False,"comparison_authorized":False,"scientific_release_authorized":False}
 v.obj(d/"RecoveryContract.json",contract)
 print(json.dumps({"status":"R2_CONTRACT_FROZEN","contract_sha256":v.sha(d/"RecoveryContract.json"),"reconciliation_sha256":v.sha(d/"Reconciliation.json"),"original_private_pins":len(pins),"original_runtime_pins":len(runtime),"authorization_budget":1,"synthetic_tests":t.stderr.strip().splitlines()[-3:]}),flush=True)
def verify_contract(root,run,d,x):
 c=v.load(d/"RecoveryContract.json");scope(c,x["original"],x["method_sha"])
 req(c["controller_code_sha256"]==v.sha(Path(__file__)) and c["test_code_sha256"]==v.sha(root/"tests/u3r2p2a2/verify_a2_r2.py"),"R2_CODE_DRIFT")
 rec=v.load(v.filepin(d/"Reconciliation.json",c["reconciliation_sha256"]))
 tr=v.load(v.filepin(d/"SyntheticTestReceipt.json",c["synthetic_test_receipt_sha256"]))
 req(tr["status"]=="PASS" and tr["runner_code_sha256"]==c["controller_code_sha256"] and tr["test_code_sha256"]==c["test_code_sha256"],"R2_TEST_PIN")
 req(rec["version"]==VERSION and rec["original"]==x["original"] and rec["prior_recovery_receipt_sha256"]==RECOVERY_SHA and rec["native_terminal_written"] is False and rec["remote_completion_or_billing_attested"] is False,"RECONCILIATION_PIN")
 pins=rec["original_private_file_pins"]
 req(len(pins)==98 and pinset_digest(pins)==x["prev"]["private_checkpoint_file_set_sha256"],"RECOVERY_PRIVATE_PIN_SET")
 pin_subset(x["priv"],pins)
 req(tree_pins(run/"runtime/008_review_01")==rec["original_runtime_file_pins"],"ORIGINAL_RUNTIME_DRIFT")
 return c
def finish(root,run,d,x):
 c=verify_contract(root,run,d,x);check_consumed(d,c,x["original"],x["method_sha"])
 case=x["case"];a=case/"review_attempt_02"
 req((a/"Terminal.json").is_file(),"RECOVERY_ATTEMPT_UNCERTAIN_STOP")
 t=v.read_attempt(a,x["method_sha"],STAGE,x["source_sha"])
 l=v.load(a/"Launch.json")
 req(l["case_ordinal"]==ORDINAL and l["attempt"]==ATTEMPT and l["declared_model_required"]==v.MODEL and not l["tool_permission"],"RECOVERY_LAUNCH_SCOPE")
 req((a/"Prompt.txt").read_bytes()==x["prompt"].encode("utf8"),"RECOVERY_PROMPT_DRIFT")
 if t["sent"]:
  i=v.load(a/"DispatchIntent.json");req(i["prompt_sha256"]==x["original"]["prompt_sha256"] and i["model_id"]==v.MODEL and i["session_id_sha256"]==t["session_id_sha256"] and i["session_id_sha256"]!=x["original"]["old_session_sha256"],"RECOVERY_SESSION_BINDING")
 z=None;failure=t["error"]
 if t["status"]=="RESPONSE_COMPLETE":
  req(t["sent"] and t["rpc_returned"] and t["model_id"]==v.MODEL and t["stop_reason"]=="end_turn" and t["tool_requests"]==t["tool_updates"]==0 and not t["error"],"RECOVERY_RESPONSE_SCOPE")
  try:z=x["parse"](v.json_answer((a/"RawResponse.txt").read_text()));failure=None
  except Exception as e:failure=v.err(e)
 vv={"terminal_sha256":v.sha(a/"Terminal.json"),"status":"PASS" if z is not None and failure is None else "HOLD","error":failure}
 if vv["status"]=="PASS":vv["projection_sha256"]=v.digest(z)
 exact_or_append(a/"Validation.json",vv)
 lineage={"recovery_version":VERSION,"recovery_contract_sha256":v.sha(d/"RecoveryContract.json"),"reconciliation_sha256":v.sha(d/"Reconciliation.json"),"authorization_consumed_sha256":v.sha(d/"AuthorizationConsumed.json")}
 cf=case/"CaseFreeze.json"
 if vv["status"]=="PASS":
  recordp=case/"ReviewRecord.json";exact_or_append(recordp,z["record"])
  ar={"attempt":ATTEMPT,"terminal_sha256":v.sha(a/"Terminal.json"),"validation_sha256":v.sha(a/"Validation.json"),"raw_sha256":t["raw_sha256"]}
  exact_or_append(cf,{"status":"CASE_STRUCTURAL_NATIVE_REFERENCE_FROZEN","case_ordinal":ORDINAL,"method_sha256":x["method_sha"],"source_sha256":x["source_sha"],"query_freeze_sha256":x["original"]["query_freeze_sha256"],"review_attempt":ar,"record_sha256":v.sha(recordp),"review_note_sha256":v.digest(z["review_note"]),"scientific_reference_qualified":False,"mapping_release_authorized":False,"execution_recovery":lineage})
 else:req(not cf.exists() and not (case/"ReviewRecord.json").exists(),"FAILED_RECOVERY_HAS_RECORD")
 verify_contract(root,run,d,x)
 out={"version":VERSION,"status":"PASS_RECOVERY_CASE_FROZEN" if cf.exists() else "HOLD_RECOVERY_ATTEMPT_FAILED","ordinal":ORDINAL,"attempt":ATTEMPT,"method_sha256":x["method_sha"],"original_terminal_outcome":"UNKNOWN","original_terminal_written":False,"recovery_terminal_sha256":v.sha(a/"Terminal.json"),"recovery_validation_sha256":v.sha(a/"Validation.json"),"response_bytes":(a/"RawResponse.txt").stat().st_size,"prompt_wall_seconds":t["prompt_wall_seconds"],"stop_reason":t["stop_reason"],"error":failure,"sent_intent":t["sent"],"case_freeze_sha256":v.sha(cf) if cf.exists() else None,"completed_cases":8 if cf.exists() else 7,"query_checkpoints":8,"new_query_dispatches":0,"authorization_budget_consumed":1,"scientific_reference_qualified":False,"comparison_executed":False,"unblind":False,**lineage}
 exact_or_append(d/"OutcomeReceipt.json",out)
 print(json.dumps(out,ensure_ascii=False),flush=True)
 return out
def verify_accepted(root,run,d,x):
 # Exact recomputation, no invocation. Verify actual second terminal and
 # deterministic record expansion; first attempt remains UNKNOWN.
 out=finish(root,run,d,x)
 req(out["status"]=="PASS_RECOVERY_CASE_FROZEN","RECOVERY_NOT_ACCEPTED")
 return out
def main(root,run,mode,limit=0):
 d=run/"recovery_r2_008"
 with (run/".controller.lock").open("a") as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  x=context(root,run)
  if mode=="prepare":prepare(root,run,d,x);return
  if mode=="execute":
   c=verify_contract(root,run,d,x)
   req(not (x["case"]/"CaseFreeze.json").exists() and not (x["case"]/"review_attempt_02").exists() and not (run/"runtime/008_review_02").exists(),"RECOVERY_ATTEMPT_EXISTS")
   check_live(run);consume(d,c,x["original"],x["method_sha"])
   print("R2 authorization consumed; dispatching exactly one original-prompt AGY review for ordinal 008",flush=True)
   v.invoke(root,run,x["case"],ORDINAL,STAGE,ATTEMPT,x["prompt"],x["method_sha"],x["source_sha"],x["stage"],x["task"],x["probe"])
   finish(root,run,d,x);return
  if mode=="finalize":finish(root,run,d,x);return
  accepted=verify_accepted(root,run,d,x)
  outcome_sha=v.sha(d/"OutcomeReceipt.json")
  baseline=tree_pins(x["priv"]);prior_summaries=set((run/"summaries").glob("Run_*.json"))
  if mode=="continue":
   replay=v.load(d/"InitialReplayReceipt.json")
   req(replay["status"]=="PASS_ZERO_DISPATCH_REPLAY" and replay["completed_cases"]==8 and replay["outcome_receipt_sha256"]==outcome_sha and replay["new_dispatches"]==0,"RECOVERY_REPLAY_REQUIRED")
   v.filepin(run/"summaries"/replay["summary_name"],replay["summary_sha256"])
   req(1<=limit<=24,"CONTINUATION_LIMIT")
  else:req(mode=="replay" and limit==0,"MODE")
 old_invoke=v.invoke;calls=[]
 def guarded(*args,**kwargs):
  req(mode=="continue","REPLAY_DISPATCH_FORBIDDEN")
  # Original v0.2 main owns the controller lock here. It must never dispatch
  # 008 again or extend terminal-retry authority to a later case.
  req(len(args)>=7 and args[3]>=9 and args[4] in ("query","review") and args[5] in (1,2),"CONTINUATION_DISPATCH_SCOPE")
  v.filepin(d/"OutcomeReceipt.json",outcome_sha)
  verify_contract(root,run,d,x)
  calls.append((args[3],args[4],args[5]))
  return old_invoke(*args,**kwargs)
 v.invoke=guarded
 try:v.main(root,run,limit,False)
 finally:v.invoke=old_invoke
 with (run/".controller.lock").open("a") as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  verify_contract(root,run,d,x);v.filepin(d/"OutcomeReceipt.json",outcome_sha)
  pin_subset(x["priv"],baseline)
  new=set((run/"summaries").glob("Run_*.json"))-prior_summaries;req(len(new)==1,"SUMMARY_CLOSURE")
  p=next(iter(new));z=v.load(p)
  req(z["completed_cases"]>=8 and z["case_freeze_hashes"]["case_008"]==accepted["case_freeze_sha256"] and not z["comparison_executed"] and not z["unblind"],"RECOVERY_REPLAY_CLOSURE")
  if mode=="replay":
   req(not calls and z["new_cases"]==0 and z["replayed_cases"]==z["completed_cases"] and tree_pins(x["priv"])==baseline,"ZERO_DISPATCH_REPLAY")
   receipt={"version":VERSION,"status":"PASS_ZERO_DISPATCH_REPLAY","completed_cases":z["completed_cases"],"query_checkpoints":z["query_checkpoints_verified"],"new_dispatches":0,"outcome_receipt_sha256":outcome_sha,"summary_name":p.name,"summary_sha256":v.sha(p),"case_freeze_hashes":z["case_freeze_hashes"]}
   if not (d/"InitialReplayReceipt.json").exists():
    req(z["completed_cases"]==8 and z["failure"] is None,"INITIAL_REPLAY_SCOPE");v.obj(d/"InitialReplayReceipt.json",receipt)
   else:v.obj(d/("Replay_"+p.stem+".json"),receipt)
  else:
   receipt={"version":VERSION,"status":"CONTINUATION_VERIFIED","completed_cases":z["completed_cases"],"new_cases":z["new_cases"],"new_dispatches":len(calls),"failure":z["failure"],"outcome_receipt_sha256":outcome_sha,"summary_name":p.name,"summary_sha256":v.sha(p)}
   v.obj(d/("Continuation_"+p.stem+".json"),receipt)
 print(json.dumps(receipt,ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--mode",choices=["prepare","execute","finalize","replay","continue"],required=True);p.add_argument("--limit",type=int,default=0);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 main(Path.cwd().resolve(),a.out.resolve(),a.mode,a.limit)
