#!/usr/bin/env python3
"""A2 AGY source-first reference construction. Frozen query protocol, separate
from the evaluated ranker. No rank/answer inputs; no controller comparison."""
import argparse,os,json,time,hashlib,subprocess
from pathlib import Path
from jsonschema import Draft202012Validator
from agy_synthetic_broker import ACP,sha,save,MODEL
from agy_raw_standard_browser import Standards,require,canon,json_answer,queries_ok,validate_records,S,PREFIX
BASE=Path("runs/B2/U3-B/C2/R2/P2/A2")
SCHEMA="schemas/udf/u3r2/R2ReferenceReview_v0.1.schema.json"
PREP_SHA="38b36cd2e44d5c538ad8a18bf560229532cf06e46dc58a36c870c4b9ac1be1f4"
FREEZE_SHA="cc43ec13416ddf6fb35ee960ba937e9606e184ce2e36ea2448fbdfaa524bff26"
PROBE="agy_authenticated_probe_006"
PROFILE_SHA="120596ea758bb45345a1a715550c282a07ff0bced471013e0e21ff102ed0f8f1"
def load(p):return json.loads(p.read_text(encoding="utf8"))
def raw(p,s):
 with p.open("x",encoding="utf8") as f:f.write(s)
 os.chmod(p,0o600)
def error_code(ex):
 if isinstance(ex,ValueError) and not isinstance(ex,json.JSONDecodeError):
  s=str(ex)
  if s.startswith("SCHEMA:"):return s[:150]
  if s and len(s)<120 and all(c.isupper() or c.isdigit() or c in "_:" for c in s):return s
 return type(ex).__name__
def verify(root):
 a=root/BASE/"local_001";stage=a/"reviewer_staging";prep=load(a/"PreparationFreeze.json");fr=load(a/"A2RetrievalFreezeReceipt.json")
 require(sha(a/"PreparationFreeze.json")==PREP_SHA and sha(a/"A2RetrievalFreezeReceipt.json")==FREEZE_SHA and fr["reference_results_read"]==0,"PARENT_FREEZE")
 require(len(prep["reviewer_staging_sha256"])==9 and all(sha(stage/k)==v for k,v in prep["reviewer_staging_sha256"].items()),"STAGING_DRIFT")
 require(set(str(p.relative_to(stage)) for p in stage.rglob("*") if p.is_file())==set(prep["reviewer_staging_sha256"]),"STAGING_FILE_SET")
 p=root/BASE/PROBE;z=load(p/"ProbeReceipt.json")
 require(z["status"]=="PASS_ACTUAL_SYNTHETIC_WORKER" and z["model_id"]==MODEL and not z["source_sent"] and sha(p/"AGYProbe.sb")==PROFILE_SHA,"ACTUAL_WORKER_GATE")
 return stage,prep,p
def main(root,out):
 require(not out.exists() and out.is_relative_to(root/BASE),"NEW_REVIEW_DIRECTORY")
 stage,prep,probe=verify(root);task=load(stage/"A2ReviewTask.json")
 require(task["case_count"]==32 and task["status"]=="PREPARED_NOT_AUTHORIZED_NOT_DISPATCHED","TASK_ID")
 source=load(stage/task["source_packet"]);require(len(source)==32 and len({r["review_id"] for r in source})==32,"SOURCE32")
 schema=load(stage/SCHEMA);Draft202012Validator.check_schema(schema);val=Draft202012Validator(schema)
 standards=Standards(stage,task["allowed_inputs"])
 out.mkdir(mode=0o700,parents=True);private=out/"reviewer_private";private.mkdir(mode=0o700);runtime=out/"runtime";runtime.mkdir(mode=0o700)
 method={"task_id":task["task_id"],"model_id":MODEL,"method_sha256":sha(Path(__file__)),"browser_sha256":sha(Path(__file__).with_name("agy_raw_standard_browser.py")),"acp_broker_sha256":sha(Path(__file__).with_name("agy_synthetic_broker.py")),"probe_profile_sha256":PROFILE_SHA,
 "source_packet_sha256":task["allowed_inputs"][task["source_packet"]],"allowed_input_sha256":prep["reviewer_staging_sha256"],"batch_size":4,"max_queries_per_standard_per_case":5,"per_term_raw_results":5,
 "search":"Reviewer-authored queries; exact native ID, normalized label or alias, whole phrase or all-token conjunction, deterministic tie break, full raw standards, no tested ranking inputs.",
 "case_order":"Original packet order, fresh ACP session each batch, same declared model. At most one structural repair per stage.",
 "owner_authorized":"D01 local isolation; D02 research/designated external processing; AGY selected; native login completed",
 "tool_requests_authorized":False,"unblind_authorized":False,"scientific_reference_qualified":False,"mapping_release_authorized":False}
 save(out/"ReviewerMethodFreeze.json",method)
 home=root/BASE/"agy_login_001/fresh_home";agy=Path.home()/".local/bin/agy"
 records=[];notes=[];runs=[];failure=None;sent=0
 print("A2 raw authorities parsed; 32 source cases verified; method frozen before prompt.",flush=True)
 for n,start in enumerate(range(0,32,4),1):
  batch=source[start:start+4];rt=runtime/("batch_%02d"%n);rt.mkdir(mode=0o700);work=rt/"empty_workspace";work.mkdir(mode=0o700);tmp=rt/"tmp";tmp.mkdir(mode=0o700)
  pf=rt/"AGYReview.sb";raw(pf,(probe/"AGYProbe.sb").read_text().replace(str(probe),str(rt)))
  env={"PATH":"/opt/homebrew/bin:/usr/bin:/bin","HOME":str(home),"TMPDIR":str(tmp),"LANG":"en_US.UTF-8","TERM":"dumb"}
  sb=["/usr/bin/sandbox-exec","-f",str(pf)]
  def cat(p):return subprocess.run(sb+["/bin/cat",str(p)],env=env,cwd=work,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5).returncode
  syn=work/"read_probe.txt";raw(syn,"A2_READ_PROBE\n")
  require(cat(syn)==0,"ALLOWED_RUNTIME_READ")
  forbid=[stage/task["source_packet"],root/BASE/"local_001/controller_private/RetrievalInput32.json",root/"runs/B2/U3-B/C2/R2/P2/A1/reserved32_retrieval_001/Ranks.jsonl",root/"runs/B2/U3-B/C2/R2/P2/private/DevelopmentLexicon_v0.1.json",root/"runs/B2/U3-B/C2/R2/real_001/reviewer_source_only/R2Review44.json"]
  require(all(p.is_file() and cat(p)!=0 for p in forbid),"REVIEWER_OS_BOUNDARY")
  args=sb+[str(agy),"acp","--stdio","--process-per-session","--sandbox=false","--include-default-customizations=false","--disable-telemetry","--app-data-dir","antigravity-cli","--gemini-dir",".gemini","--log-file",str(rt/"acp.log")]
  acp=ACP(args,work,env,lambda _:False);started=time.monotonic();bid=private/("batch_%02d"%n);bid.mkdir(mode=0o700)
  call_id=2
  def prompt(t,name):
   nonlocal call_id
   call_id+=1;begin=len(acp.chunks);ev=len(acp.events);req=len(acp.requests)
   raw(bid/(name+"_prompt.txt"),t)
   r=acp.call(call_id,"session/prompt",{"sessionId":sid,"prompt":[{"type":"text","text":t}]},175)
   answer="".join(acp.chunks[begin:]);raw(bid/(name+"_raw.txt"),answer)
   require(len(acp.events)==ev and len(acp.requests)==req,"UNEXPECTED_AGENT_TOOL_USE")
   require(r.get("result",{}).get("stopReason")=="end_turn","ACP_PROMPT_NOT_COMPLETED")
   return answer
  try:
   x=acp.call(1,"initialize",{"protocolVersion":1,"clientCapabilities":{},"clientInfo":{"name":"a2-independent-reference","version":"0.1"}});require(bool(x.get("result")),"ACP_INITIALIZE")
   y=acp.call(2,"session/new",{"cwd":str(work),"mcpServers":[]},55);v=y.get("result",{});sid=v.get("sessionId");require(sid and v.get("models",{}).get("currentModelId")==MODEL,"ACP_MODEL_OR_SESSION")
   print("A2 review batch %d/8: fresh AGY session, %d source cases"%(n,len(batch)),flush=True)
   common="Independent source-first scientific Critic for B2-U3R2-REF32-A2-001. Do not call tools or use prior conversations, external search, tested candidates or other context. This is a developmental reference, not Gold. Copy immutable source identity. Unknown is not negative. Do not infer physical composition, nutrient transfer or equivalence. Only use the original source records and raw authority rows returned by this broker. "
   qprompt=common+"Exact task rules:\n"+json.dumps(task["rules"],ensure_ascii=False)+"\nSource-only records:\n"+canon(batch)+"\nIndependently choose 1-5 distinct English terms per system per case for all three standards. Include variants/synonyms and specificity where appropriate. Native IDs may be queries but cannot be assumed true. Broker searches actual raw label/alias or native ID, exact equality/whole phrase/all-token match, up to 5 records per term. Return ONLY JSON {\"queries\":[{\"review_id\":\"...\",\"systems\":{\"FoodOn\":[\"...\"],\"FDC_SR_Legacy\":[\"...\"],\"FNDDS\":[\"...\"]}}]}. No prose, no tool calls."
   sent+=len(batch);a=prompt(qprompt,"queries_1")
   try:q=queries_ok(json_answer(a),batch)
   except (ValueError,TypeError,KeyError):
    a=prompt("Structural retry only: return complete JSON query envelope, all exact case identities and all three systems, 1-5 distinct terms each; no tools or prose.","queries_2")
    q=queries_ok(json_answer(a),batch)
   hits={rid:{sys:standards.search(sys,terms) for sys,terms in d.items()} for rid,d in q.items()};save(bid/"ActualSearchResults.json",hits)
   anchors={r["review_id"]:{"artifact_sha256":r["artifact_sha256"],"locator":canon(r["source_locator"]),"role":"SOURCE_EXPLICIT"} for r in batch}
   fprompt=common+"Actual reviewer-authored queries and retrieved rows below are NOT the evaluated retrieval output. Choose up to 3 supported/ambiguous candidates and 3 hard negatives per standard, never forced; record unresolved/SEARCH_INCOMPLETE where appropriate. Keep exact query_terms per system, exact target IDs/native labels/locators, and TARGET_EXPLICIT evidence artifact_sha256 and locator from returned rows. SOURCE_EXPLICIT requires exact supplied source anchor; otherwise use inference with evidence or UNRESOLVED. Set reviewer_minutes to 0 if unobserved (actual batch wall time recorded separately). Preserve conditions, SOURCE_RELATION_TO_TARGET, HOLD transfer and all scientific-release flags false. Return ONLY JSON {\"records\":[...],\"review_note\":\"brief actual limitations\"}, every case exactly once, conform to exact schema. No tools.\nSchema:\n"+canon(schema)+"\nSource anchors:\n"+canon(anchors)+"\nActual queries:\n"+canon(q)+"\nActual returned raw rows:\n"+canon(hits)
   a=prompt(fprompt,"review_1")
   try:obj=json_answer(a);rr=validate_records(obj,batch,q,hits,standards,val,task["allowed_inputs"])
   except (ValueError,TypeError,KeyError) as e:
    a=prompt("Structural/native-carrier validation error: "+error_code(e)+". Correct ONLY format, identity, exact locator/evidence or schema issues using the same supplied source and raw rows. Preserve substantive judgments. Return complete JSON envelope with all four records. No tools or new searches.","review_2")
    obj=json_answer(a);rr=validate_records(obj,batch,q,hits,standards,val,task["allowed_inputs"])
   raw(bid/"ReviewRecords.jsonl","".join(canon(r)+"\n" for r in rr));records.extend(rr);notes.append(obj["review_note"])
   runs.append({"batch":n,"cases":len(rr),"model_id":MODEL,"session_id_sha256":hashlib.sha256(sid.encode()).hexdigest(),"wall_seconds":round(time.monotonic()-started,3),"tool_requests":len(acp.requests),"tool_updates":len(acp.events),"os_denied_reads":len(forbid)})
   save(bid/"BatchReceipt.json",{"status":"STRUCTURAL_AND_NATIVE_REFERENCE_CHECK_PASS","cases":len(rr),"records_sha256":sha(bid/"ReviewRecords.jsonl"),"model_id":MODEL,"wall_seconds":runs[-1]["wall_seconds"],"no_tested_results_read":True})
   print("A2 review batch %d/8 frozen; completed records %d/32"%(n,len(records)),flush=True)
  except Exception as e:
   failure=error_code(e);print("A2 review batch %d stopped; completed records %d/32; code %s"%(n,len(records),failure),flush=True);break
  finally:acp.close()
 require(all(sha(stage/k)==h for k,h in prep["reviewer_staging_sha256"].items()),"POST_STAGE_DRIFT")
 complete=len(records)==32 and failure is None
 raw(private/"ReviewRecords.jsonl","".join(canon(r)+"\n" for r in records))
 raw(private/"ReviewReport.md","# A2 AGY independent source-first review\n\nStatus: "+("REVIEW_FROZEN" if complete else "HOLD_INCOMPLETE")+"\n\nCases: "+str(len(records))+"/32. Bounded reviewer-driven raw authority search, not exhaustive. No scientific accuracy/recall, Gold, or mapping release. Fresh ACP sessions; provider historical exposure unknown. Batch wall time recorded. No evaluated rank comparison.\n\n"+"\n\n".join("## Batch "+str(i+1)+"\n\n"+t for i,t in enumerate(notes))+"\n")
 manifest={"task_id":task["task_id"],"reviewer_runtime":"AGY ACP 1.5.18","model_identity":MODEL,"model_identity_basis":"ACP declaration; no independent backend attestation","source_only":True,"input_hashes":prep["reviewer_staging_sha256"],
 "actual_accessed_paths":sorted([task["source_packet"],"A2ReviewTask.json",SCHEMA,*[PREFIX+x for x in ["FoodOn.owl","FDC_SR_2018.zip","FNDDS_2015_16.zip","FNDDS_ARS_foods_2015_16.xlsx"]]]),
 "source_projection_method":"Original source rows plus exact task rules and response schema; reviewer-generated terms, independent deterministic raw authority lookup. Audit/normative files verified but not injected in full. No agent tool permissions.",
 "prior_exposure_declared":True,"prior_exposure":"Isolated HOME with synthetic readiness sessions; project/model-family historical exposure and provider training unknown. No strict confirmatory blind claim.",
 "confirmatory_blind_claimed":False,"actual_model_sessions":runs,"completed_cases":len(records),"source_cases_transmitted":sent,"failure":failure,"forbidden_access_count":0 if complete else None,
 "reviewer_method_sha256":sha(out/"ReviewerMethodFreeze.json"),"input_hashes_unchanged":True,"scientific_reference_qualified":False,"mapping_release_authorized":False,"controller_comparison_authorized":False}
 save(private/"ExecutionManifest.json",manifest)
 receipt={"task_id":task["task_id"],"status":"REVIEW_FROZEN" if complete else "HOLD_INCOMPLETE","completed_cases":len(records),"source_cases_transmitted":sent,"output_file_hashes":{p.name:sha(p) for p in [private/"ExecutionManifest.json",private/"ReviewRecords.jsonl",private/"ReviewReport.md"]},
 "raw_batch_files_sha256":{str(p.relative_to(private)):sha(p) for p in private.glob("batch_*/*") if p.is_file()},"model_id":MODEL,"reference_qualification":"STRUCTURAL_NATIVE_LOCATOR_ONLY" if complete else "INCOMPLETE",
 "scientific_reference_qualified":False,"mapping_release_authorized":False,"unblind_authorized":False,"controller_outcomes_read":0,"comparison_executed":False}
 save(private/"CriticFreezeReceipt.json",receipt)
 public={"status":receipt["status"],"completed_cases":len(records),"source_cases_transmitted":sent,"model_id":MODEL,"raw_standard_counts":{s:len(standards.rows[s]) for s in S},"completed_batches":len(runs),"actual_reference_receipt_sha256":sha(private/"CriticFreezeReceipt.json"),"reviewer_method_sha256":sha(out/"ReviewerMethodFreeze.json"),"failure":failure,"scientific_reference_qualified":False,"mapping_release":0,"unblind":False,"generalization_validated":False,"stage_hashes_unchanged":True}
 save(out/"A2AGYReviewExecutionSummary.json",public);print(json.dumps(public,ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args();main(Path.cwd().resolve(),a.out.resolve())
