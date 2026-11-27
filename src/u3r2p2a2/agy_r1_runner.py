#!/usr/bin/env python3
"""A2.5-R1 per-case AGY reference execution with append-only checkpoint recovery.
No tested rank or comparison access; no scientific promotion."""
import argparse,fcntl,hashlib,json,os,subprocess,time
from pathlib import Path
from jsonschema import Draft202012Validator
from agy_synthetic_broker import ACP,sha,MODEL
from agy_raw_standard_browser import Standards,S,canon,require,json_answer,queries_ok,validate_records
from agy_reference_broker import BASE,SCHEMA,PREP_SHA,FREEZE_SHA,PROFILE_SHA,verify,load
from agy_r1_transport import project,query_prompt,review_prompt,table
OLD_RECEIPT="0c34c871bb9be9c76cf308b83807117dda07faaa02737870083ff157517c923f"
OLD_METHOD="56b060354db262b8981b6e2f5a97deccbd51918d5ba8022425a1f37a73d47993"
BINARY_SHA="89d0b97a9ebcefcaebbdfe4ffeb2de877ef92ee4504de188e35a38489136be13"
def put(p,s):
 # Atomic no-replacement publish (hardlink after fsync); interrupted temp files
 # are never treated as committed receipts.
 tmp=p.with_name("."+p.name+".tmp-"+os.urandom(8).hex())
 with os.fdopen(os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w",encoding="utf8") as f:f.write(s);f.flush();os.fsync(f.fileno())
 try:os.link(tmp,p)
 finally:tmp.unlink()
 fd=os.open(p.parent,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
def obj(p,x):put(p,canon(x)+"\n")
def err(e):
 if isinstance(e,ValueError) and not isinstance(e,json.JSONDecodeError):
  s=str(e)
  if s.startswith("SCHEMA:"):return s[:160]
  if len(s)<100 and all(c.isupper() or c.isdigit() or c in "_:" for c in s):return s
 return type(e).__name__
def filepin(p,h):require(p.is_file() and not p.is_symlink() and sha(p)==h,"PIN_DRIFT");return p
def digest(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def parent(root,source,standards):
 old=root/BASE/"agy_reference_001";priv=old/"reviewer_private"
 rc=load(filepin(priv/"CriticFreezeReceipt.json",OLD_RECEIPT))
 require(rc["status"]=="HOLD_INCOMPLETE" and rc["completed_cases"]==0 and rc["controller_outcomes_read"]==0,"PARENT_STATE")
 for k,h in {**rc["output_file_hashes"],**rc["raw_batch_files_sha256"]}.items():filepin(priv/k,h)
 oldm=load(filepin(old/"ReviewerMethodFreeze.json",OLD_METHOD))
 for field,name in (("method_sha256","agy_reference_broker.py"),("browser_sha256","agy_raw_standard_browser.py"),("acp_broker_sha256","agy_synthetic_broker.py")):filepin(Path(__file__).with_name(name),oldm[field])
 p=priv/"batch_01";raw=p/"queries_1_raw.txt";hfile=p/"ActualSearchResults.json"
 q=queries_ok(json_answer(raw.read_text()),source[:4]);h=load(hfile)
 require(set(h)==set(q),"PARENT_QUERY_CLOSURE")
 recomputed={i:{s:standards.search(s,t) for s,t in z.items()} for i,z in q.items()}
 require(recomputed==h,"PARENT_HIT_REPLAY")
 return q,h,{"receipt_sha256":OLD_RECEIPT,"method_sha256":OLD_METHOD,"query_raw_sha256":sha(raw),"hits_sha256":sha(hfile),"recovered_cases":4,"old_completed_cases":0}
def metadata(root,stage,prep,source,parent_meta):
 return {"version":"A2.5-R1-v0.1","task_id":"B2-U3R2-REF32-A2-001","model_id":MODEL,"code_sha256":{n:sha(Path(__file__).with_name(n)) for n in ("agy_r1_runner.py","agy_r1_transport.py","agy_raw_standard_browser.py","agy_synthetic_broker.py","agy_reference_broker.py")},
 "source_count":32,"source_packet_order_sha256":digest([digest(s) for s in source]),"original_retrieval_freeze_sha256":FREEZE_SHA,"parent":parent_meta,"allowed_inputs":prep["reviewer_staging_sha256"],
 "granularity":"one case, separate fresh ACP session for each query/review attempt; first four exact query/hit checkpoints inherited",
 "transport":"indexed evidence carriers; dedup repeated raw rows without dropping matches; deterministic projection to original response schema; no controller semantic values",
 "search_caps":{"terms_per_system":5,"records_per_term":5,"candidates_per_system":3,"negatives_per_system":3},"prompt_timeout_seconds":150,"max_attempts_per_stage":2,
 "retry_rule":"only first structural repair in fresh session with prior raw answer; terminal incomplete attempt retry requires explicit flag; uncertain launch without terminal receipt stops, never replay automatically",
 "scope":"bounded developmental reference; no tested retrieval outcomes, no Gold, no comparison/unblind","owner_authorized":True,"scientific_release_authorized":False}
class Journal(list):
 def __init__(self,f):super().__init__();self.f=f
 def append(self,x):
  if not isinstance(x,str):raise ValueError("NON_TEXT_CHUNK")
  self.f.write(x);self.f.flush();super().append(x)
def read_attempt(a,method_sha,kind,source_sha):
 launch=load(a/"Launch.json");require(launch["method_sha256"]==method_sha and launch["stage"]==kind and launch["source_sha256"]==source_sha,"ATTEMPT_BINDING")
 filepin(a/"Prompt.txt",launch["prompt_sha256"])
 # An incomplete launch is never silently retried.
 require((a/"Terminal.json").is_file(),"UNCERTAIN_DISPATCH_STOP")
 t=load(a/"Terminal.json");require(t["launch_sha256"]==sha(a/"Launch.json"),"TERMINAL_PARENT")
 filepin(a/"RawResponse.txt",t["raw_sha256"]);return t
def invoke(root,run,case,idx,kind,number,prompt,method_sha,source_sha,stage,task,probe):
 a=case/("%s_attempt_%02d"%(kind,number));require(not a.exists(),"ATTEMPT_EXISTS");a.mkdir(mode=0o700)
 rt=run/"runtime"/("%03d_%s_%02d"%(idx,kind,number));rt.mkdir(mode=0o700,parents=True);work=rt/"empty_workspace";work.mkdir(mode=0o700);tmp=rt/"tmp";tmp.mkdir(mode=0o700)
 pf=rt/"AGYReview.sb";put(pf,(probe/"AGYProbe.sb").read_text().replace(str(probe),str(rt)))
 home=root/BASE/"agy_login_001/fresh_home";agy=Path.home()/".local/bin/agy"
 env={"PATH":"/opt/homebrew/bin:/usr/bin:/bin","HOME":str(home),"TMPDIR":str(tmp),"LANG":"en_US.UTF-8","TERM":"dumb"}
 sb=["/usr/bin/sandbox-exec","-f",str(pf)]
 def cat(p):return subprocess.run(sb+["/bin/cat",str(p)],env=env,cwd=work,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5).returncode
 syn=work/"read_probe.txt";put(syn,"A2_R1_SYNTHETIC\n")
 require(cat(syn)==0,"ALLOWED_RUNTIME_READ")
 forbidden=[stage/task["source_packet"],root/BASE/"local_001/controller_private/RetrievalInput32.json",root/"runs/B2/U3-B/C2/R2/P2/A1/reserved32_retrieval_001/Ranks.jsonl",root/"runs/B2/U3-B/C2/R2/P2/private/DevelopmentLexicon_v0.1.json",root/"runs/B2/U3-B/C2/R2/real_001/reviewer_source_only/R2Review44.json",case/"QueryFreeze.json"]
 require(all(cat(p)!=0 for p in forbidden if p.is_file()),"OS_BOUNDARY")
 put(a/"Prompt.txt",prompt)
 args=sb+[str(agy),"acp","--stdio","--process-per-session","--sandbox=false","--include-default-customizations=false","--disable-telemetry","--app-data-dir","antigravity-cli","--gemini-dir",".gemini","--log-file",str(rt/"acp.log")]
 obj(a/"Launch.json",{"method_sha256":method_sha,"stage":kind,"source_sha256":source_sha,"case_ordinal":idx,"attempt":number,"prompt_sha256":sha(a/"Prompt.txt"),"profile_sha256":sha(pf),"declared_model_required":MODEL,"tool_permission":False})
 start=time.monotonic();sent=False;stop=None;model=None;error=None;session_hash=None;ev=0;req=0
 with os.fdopen(os.open(a/"RawResponse.txt",os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),"w",encoding="utf8") as f:
  acp=None
  try:
   acp=ACP(args,work,env,lambda _:False)
   x=acp.call(1,"initialize",{"protocolVersion":1,"clientCapabilities":{},"clientInfo":{"name":"a2-r1-case-review","version":"0.1"}});require(bool(x.get("result")),"ACP_INIT")
   y=acp.call(2,"session/new",{"cwd":str(work),"mcpServers":[]},55);v=y.get("result",{});sid=v.get("sessionId");model=v.get("models",{}).get("currentModelId")
   require(sid and model==MODEL,"ACP_MODEL_OR_SESSION");session_hash=hashlib.sha256(sid.encode()).hexdigest()
   acp.chunks=Journal(f)
   # Record intent before first real prompt; if the process dies, never assume
   # it was not sent.
   obj(a/"DispatchIntent.json",{"session_id_sha256":session_hash,"model_id":model,"prompt_sha256":sha(a/"Prompt.txt")});sent=True
   r=acp.call(3,"session/prompt",{"sessionId":sid,"prompt":[{"type":"text","text":prompt}]},150)
   stop=r.get("result",{}).get("stopReason");ev=len(acp.events);req=len(acp.requests)
   if stop!="end_turn":error="ACP_PROMPT_NOT_COMPLETED"
   elif ev or req:error="UNEXPECTED_AGENT_TOOL_USE"
  except Exception as e:error=err(e)
  finally:
   if acp:acp.close()
   f.flush();os.fsync(f.fileno())
 t={"launch_sha256":sha(a/"Launch.json"),"status":"RESPONSE_COMPLETE" if not error and sent and stop=="end_turn" else "FAILED_TERMINAL",
 "sent":sent,"model_id":model,"session_id_sha256":session_hash,"stop_reason":stop,"tool_updates":ev,"tool_requests":req,"error":error,"wall_seconds":round(time.monotonic()-start,3),"raw_sha256":sha(a/"RawResponse.txt")}
 if sent:t["dispatch_intent_sha256"]=sha(a/"DispatchIntent.json")
 obj(a/"Terminal.json",t);return t
def attempt_response(case,kind,srcsha,method_sha,parse,base_prompt,invoke_fn,retry):
 # Each stage has at most two attempts. Reconstruct previous successful
 # structural validation from original raw bytes; no cherry-picking.
 for n in (1,2):
  a=case/("%s_attempt_%02d"%(kind,n))
  if not a.exists():
   if n==2:
    prev=case/("%s_attempt_01"%kind);t=read_attempt(prev,method_sha,kind,srcsha)
    v=load(prev/"Validation.json")
    require(v["terminal_sha256"]==sha(prev/"Terminal.json"),"VALIDATION_PARENT")
    if t["status"]!="RESPONSE_COMPLETE" and not retry:raise ValueError("TERMINAL_RETRY_REQUIRES_AUTH")
    p=base_prompt
    if t["status"]=="RESPONSE_COMPLETE":
     p+="\nStructural repair only ("+v["error"]+"). Preserve substantive judgments. Prior response follows; correct formatting/field binding only:\n"+(prev/"RawResponse.txt").read_text()
   else:p=base_prompt
   t=invoke_fn(kind,n,p)
  else:t=read_attempt(a,method_sha,kind,srcsha)
  value=None;failure=t["error"]
  if t["status"]=="RESPONSE_COMPLETE":
   require(t["model_id"]==MODEL and t["stop_reason"]=="end_turn" and t["tool_updates"]==t["tool_requests"]==0,"RESPONSE_SCOPE")
   try:value=parse(json_answer((a/"RawResponse.txt").read_text()));failure=None
   except Exception as e:failure=err(e)
  v={"terminal_sha256":sha(a/"Terminal.json"),"status":"PASS" if failure is None and value is not None else "HOLD","error":failure}
  if v["status"]=="PASS":v["projection_sha256"]=digest(value)
  vp=a/"Validation.json"
  if vp.exists():require(load(vp)==v,"VALIDATION_REPLAY")
  else:obj(vp,v)
  if v["status"]=="PASS":return value,{"attempt":n,"terminal_sha256":sha(a/"Terminal.json"),"validation_sha256":sha(vp),"raw_sha256":t["raw_sha256"]}
  if t["status"]!="RESPONSE_COMPLETE" and not retry:raise ValueError(failure or "RESPONSE_HOLD")
 raise ValueError("ATTEMPT_BUDGET_EXHAUSTED")
def main(root,run,limit,retry):
 require(run.is_relative_to(root/BASE) and run.name.startswith("agy_r1_"),"RUN_SCOPE")
 stage,prep,probe=verify(root);task=load(stage/"A2ReviewTask.json");source=load(stage/task["source_packet"])
 require(len(source)==32 and len({r["review_id"] for r in source})==32,"SOURCE32")
 filepin(Path.home()/".local/bin/agy",BINARY_SHA)
 schema=load(stage/SCHEMA);Draft202012Validator.check_schema(schema);val=Draft202012Validator(schema)
 standards=Standards(stage,task["allowed_inputs"]);oq,oh,pm=parent(root,source,standards)
 method=metadata(root,stage,prep,source,pm)
 run.mkdir(mode=0o700,exist_ok=True);require(not run.is_symlink(),"RUN_SYMLINK")
 lock=run/".controller.lock"
 with lock.open("a") as l:
  fcntl.flock(l,fcntl.LOCK_EX|fcntl.LOCK_NB)
  mf=run/"ReviewerMethodFreeze.json"
  if mf.exists():require(load(mf)==method,"METHOD_DRIFT")
  else:obj(mf,method)
  mh=sha(mf);priv=run/"reviewer_private";priv.mkdir(mode=0o700,exist_ok=True)
  summaries=run/"summaries";summaries.mkdir(mode=0o700,exist_ok=True)
  count=0;new=0;recovered=0;replayed=0;failure=None;query_count=0
  print("R1 method frozen; old query/hit checkpoint exact replay 4/4",flush=True)
  for i,s in enumerate(source,1):
   if new>=limit and not (priv/("case_%03d"%i)/"CaseFreeze.json").is_file():break
   c=priv/("case_%03d"%i);c.mkdir(mode=0o700,exist_ok=True);ss=digest(s);rid=s["review_id"];qp=c/"QueryFreeze.json";recordp=c/"ReviewRecord.json"
   def inv(kind,n,prompt):return invoke(root,run,c,i,kind,n,prompt,mh,ss,stage,task,probe)
   try:
    if i<=4:
     q=oq[rid];hits=oh[rid]
     qr={"method_sha256":mh,"source_sha256":ss,"origin":"PARENT_EXACT_REPLAY","parent":pm,"query":q,"hits":hits}
     if qp.exists():require(load(qp)==qr,"QUERY_REPLAY")
     else:obj(qp,qr)
     recovered+=1
    else:
     def parse_q(x):return queries_ok(x,[s])[rid]
     q,ar=attempt_response(c,"query",ss,mh,parse_q,query_prompt(s,task["rules"]),inv,retry)
     hits={sys:standards.search(sys,terms) for sys,terms in q.items()}
     qr={"method_sha256":mh,"source_sha256":ss,"origin":"AGY_CASE_QUERY","attempt":ar,"query":q,"hits":hits}
     if qp.exists():require(load(qp)==qr,"QUERY_REPLAY")
     else:obj(qp,qr)
    query_count+=1
    def parse_r(x):
     full=project(x,s,q,hits)
     rec=validate_records(full,[s],{rid:q},{rid:hits},standards,val,task["allowed_inputs"])[0]
     return {"record":rec,"review_note":full["review_note"]}
    cf=c/"CaseFreeze.json";exists=cf.exists()
    if exists:
     # Verify existing case by exact re-derivation from frozen raw response.
     old=load(cf);require(old["method_sha256"]==mh and old["source_sha256"]==ss and old["query_freeze_sha256"]==sha(qp),"CASE_PARENT")
     ar=old["review_attempt"];a=c/("review_attempt_%02d"%ar["attempt"]);t=read_attempt(a,mh,"review",ss)
     filepin(a/"Terminal.json",ar["terminal_sha256"]);filepin(a/"Validation.json",ar["validation_sha256"]);filepin(a/"RawResponse.txt",ar["raw_sha256"])
     require(t["status"]=="RESPONSE_COMPLETE" and t["model_id"]==MODEL and not t["tool_requests"] and not t["tool_updates"],"CASE_RESPONSE")
     z=parse_r(json_answer((a/"RawResponse.txt").read_text()))
     require(load(filepin(recordp,old["record_sha256"]))==z["record"] and load(a/"Validation.json")["projection_sha256"]==digest(z),"CASE_RECOMPUTE")
     replayed+=1
    else:
     z,ar=attempt_response(c,"review",ss,mh,parse_r,review_prompt(s,q,hits,task["rules"]),inv,retry)
     if recordp.exists():require(load(recordp)==z["record"],"UNFROZEN_RECORD_DRIFT")
     else:obj(recordp,z["record"])
     obj(cf,{"status":"CASE_STRUCTURAL_NATIVE_REFERENCE_FROZEN","case_ordinal":i,"method_sha256":mh,"source_sha256":ss,"query_freeze_sha256":sha(qp),"review_attempt":ar,"record_sha256":sha(recordp),"review_note_sha256":digest(z["review_note"]),"scientific_reference_qualified":False,"mapping_release_authorized":False})
     new+=1
    count+=1;print("R1 case %02d/32 frozen; new=%d replay=%d"%(i,new,replayed),flush=True)
   except Exception as e:
    failure=err(e);print("R1 stopped at case %02d; reason %s"%(i,failure),flush=True);break
  require(all(sha(stage/k)==h for k,h in prep["reviewer_staging_sha256"].items()),"POST_STAGE_DRIFT")
  # Recheck historical receipts and raw checkpoints, no old artifact changes.
  parent(root,source,standards)
  s={"status":"REVIEW_FROZEN" if count==32 and failure is None else ("HOLD_EXECUTION_FAILURE" if failure else "PARTIAL_CHECKPOINT_FROZEN"),"completed_cases":count,"new_cases":new,"replayed_cases":replayed,"query_checkpoints_verified":query_count,"parent_query_cases_recovered":recovered,"failure":failure,"method_sha256":mh,
   "retrieval_freeze_sha256":FREEZE_SHA,"stage_hashes_unchanged":True,"prior_review_files_unchanged":True,"case_freeze_hashes":{p.parent.name:sha(p) for p in sorted(priv.glob("case_*/CaseFreeze.json"))},
   "scientific_reference_qualified":False,"mapping_release":0,"comparison_executed":False,"unblind":False}
  require(len(s["case_freeze_hashes"])==count,"CASE_COUNT_CLOSURE")
  if count==32 and failure is None:
   final=priv/"Final";final.mkdir(mode=0o700,exist_ok=True)
   rr="".join(canon(load(priv/("case_%03d"%i)/"ReviewRecord.json"))+"\n" for i in range(1,33))
   def exact(p,text):
    if p.exists():require(p.read_text()==text,"FINAL_DRIFT")
    else:put(p,text)
   exact(final/"ReviewRecords.jsonl",rr)
   exact(final/"ReviewReport.md","# A2.5-R1 AGY independent reference\n\n32/32 structurally and native-locator validated records; bounded raw-authority search. Reviewer-selected semantic decisions; deterministic carrier expansion. Earlier four-case failed review and query reuse retained. No scientific Gold, unblind, or retrieval comparison. Provider model identity declared by ACP, not backend attestation. Prior model exposure unknown.\n")
   manifest={"task_id":task["task_id"],"model_id":MODEL,"reviewer_runtime":"AGY ACP","method_sha256":mh,"case_freeze_hashes":s["case_freeze_hashes"],"source_count":32,"input_hashes":prep["reviewer_staging_sha256"],"prior_exposure_declared":True,"confirmatory_blind_claimed":False,"source_only":True,"mapping_release_authorized":False}
   exact(final/"ExecutionManifest.json",canon(manifest)+"\n")
   receipt={"status":"REVIEW_FROZEN","completed_cases":32,"task_id":task["task_id"],"output_file_hashes":{n:sha(final/n) for n in ("ReviewRecords.jsonl","ReviewReport.md","ExecutionManifest.json")},"scientific_reference_qualified":False,"mapping_release_authorized":False,"unblind_authorized":False,"comparison_executed":False}
   exact(final/"CriticFreezeReceipt.json",canon(receipt)+"\n");s["reference_receipt_sha256"]=sha(final/"CriticFreezeReceipt.json")
  n=len(list(summaries.glob("Run_*.json")))+1
  obj(summaries/("Run_%03d.json"%n),s)
  print(json.dumps(s,ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);p.add_argument("--limit",type=int,default=1);p.add_argument("--retry-terminal-failure",action="store_true");a=p.parse_args()
 require(1<=a.limit<=32,"LIMIT");main(Path.cwd().resolve(),a.out.resolve(),a.limit,a.retry_terminal_failure)
