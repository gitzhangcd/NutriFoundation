#!/usr/bin/env python3
"""A2.6-P0 pre-unblind, source-only qualification audit.
Never opens tested rank lists, query hypotheses, private lexicon, target
universe, comparator outputs or credentials. No model dispatch. No score
on real reference records. Existing frozen data are read-only."""
import argparse,collections as C,fcntl,hashlib,io,json,os,sys
from pathlib import Path
from contextlib import redirect_stdout
sys.dont_write_bytecode=True
B=Path("runs/B2/U3-B/C2/R2/P2/A2")
RUN=B/"agy_r1_002"
ST=B/"local_001/reviewer_staging"
OUT=B/"qualification_p0_001"
FINAL_SHA="024d90970fa5f7990952bc702e63b5591c5f01e65881c69f8ef338554e9a6834"
METHOD="08056819875d23e3c507b72d55eca479319fe737dbf4d7fa45bedc78ad2a6bd8"
PREP="38b36cd2e44d5c538ad8a18bf560229532cf06e46dc58a36c870c4b9ac1be1f4"
RET="cc43ec13416ddf6fb35ee960ba937e9606e184ce2e36ea2448fbdfaa524bff26"
POL="58c53ab63cf4ac25d030d78e03dcdded8a51fb5a5802e7623ee75bd93af5ddc6"
POLPATH=Path("configs/udf/u3r2p2a1/RetrievalPolicyFreeze_v0.1.json")
NATIVE=Path("runs/B1/U2-C/real_001/private/typed_partitions/NUTRIDATA_RIGHTS_UNRESOLVED/NativeVocabularyRecord.jsonl")
CTX=Path("runs/B2/U3-B/real_001/private/typed_partitions/MIXED_RESTRICTED_f05fbb56a95c4498/QueryContextRecord.jsonl")
FIRST=Path("runs/B2/U3-B/C2/R2/real_001/reviewer_source_only/R2Review44.json")
MAN=Path("runs/B0/U1-A/NutriData_real_001/private/NativeFileManifest.json")
SOURCE=Path("runs/B2/U3-B/C2/R2/real_001/reserved_source_only/R2Calibration32.json")
RAW=[Path("source_data/excel-Nutridata/01-食物成分库.xlsx"),Path("source_data/excel-Nutridata/02-菜肴库.xlsx")]
SUPPORT={"EXACT","CLOSE","BROADER_TARGET","NARROWER_TARGET","RELATED","CONDITIONAL"}
VERSION={"FoodOn":"2026-09-20","FDC_SR_Legacy":"2018-04","FNDDS":"2015-16"}
def need(x,code):
 if not x:raise ValueError(code)
def load(p):return json.loads(p.read_text(encoding="utf8"))
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
 return h.hexdigest()
def pin(p,h):need(p.is_file() and not p.is_symlink() and sha(p)==h,"PIN_DRIFT");return p
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def digest(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def tree(p):
 z={}
 for q in sorted(p.rglob("*")):
  need(not q.is_symlink(),"PIN_SYMLINK")
  if q.is_file():z[str(q.relative_to(p))]=sha(q)
 return z
def subset(p,z):
 for k,h in z.items():
  need(not Path(k).is_absolute() and ".." not in Path(k).parts,"PIN_PATH")
  pin(p/k,h)
def fence(root,out):
 # Python application-level open/dispatch fence, not provider isolation.
 # Directories contain only frozen source-first reviewer data/diagnostics.
 approved_dirs=[root/x for x in (ST,RUN,B/"agy_r1_001",B/"agy_reference_001",B/"agy_r3_diag_001",B/"agy_r3_diag_002")]
 exact={root/x for x in (NATIVE,CTX,FIRST,MAN,SOURCE,*RAW,POLPATH,B/"local_001/PreparationFreeze.json",B/"local_001/A2RetrievalFreezeReceipt.json",B/"local_001/A2AdmissionReceipt.json",B/"agy_authenticated_probe_006/ProbeReceipt.json",B/"agy_authenticated_probe_006/AGYProbe.sb")}
 code_dirs=[root/"src",root/"tests"]
 forbidden=("controller_private","Ranks.jsonl","RetrievalInput32.json","DevelopmentLexicon_v0.1.json","QueryHypotheses.jsonl","agy_login_001","broker_login_001")
 reads=set();blocked=[];dispatch=[]
 def under(p,ds):return any(p==d or p.is_relative_to(d) for d in ds)
 def audit(event,args):
  if event in ("subprocess.Popen","os.system","os.posix_spawn","os.exec","socket.connect","socket.bind","socket.getaddrinfo"):
   dispatch.append(event);raise PermissionError("NO_MODEL_OR_NETWORK_DISPATCH")
  if event=="open":
   if isinstance(args[0],int):return
   try:p=Path(os.fsdecode(args[0])).resolve()
   except (TypeError,ValueError):raise PermissionError("UNKNOWN_PATH")
   mode=args[1] or "";flags=args[2] or 0
   writing=any(c in mode for c in "wax+") or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
   if p.is_relative_to(root):
    rel=str(p.relative_to(root))
    if writing:
     if p.is_relative_to(out):return
     blocked.append("WRITE");raise PermissionError("FROZEN_WRITE_DENIED")
    if any(x in p.parts for x in forbidden) or not (p in exact or under(p,approved_dirs+code_dirs+[out])):
     blocked.append("READ");raise PermissionError("NON_ALLOWLISTED_READ_DENIED")
    reads.add(rel)
   elif writing:
    blocked.append("EXTERNAL_WRITE");raise PermissionError("EXTERNAL_WRITE_DENIED")
   elif p.is_relative_to(Path.home()) and not p.is_relative_to(Path(sys.prefix).resolve()) and not p.is_relative_to(Path(sys.base_prefix).resolve()):
    # No user home, auth files, other projects. Allow pinned AGY executable
    # bytes if an explicit verification ever requires them; no execution.
    if p!= (Path.home()/".local/bin/agy").resolve():
     blocked.append("HOME_READ");raise PermissionError("HOME_READ_DENIED")
 return reads,blocked,dispatch,audit
def source_audit(root,src,prep,prepare,v):
 fs=prep["input_fences"]
 first=load(pin(root/FIRST,fs[str(FIRST)]))
 prepare.check_sources(src,first)
 need(all(s["status"]=="NOT_REVIEWED" for s in first),"FIRST44_NOT_SOURCE_ONLY")
 ids={s["source_ref"] for s in src};native={};ctx={}
 for path,kind,where in [(NATIVE,"NativeVocabularyRecord",native),(CTX,"QueryContextRecord",ctx)]:
  with pin(root/path,fs[str(path)]).open(encoding="utf8") as f:
   for line in f:
    if not line.strip():continue
    row=json.loads(line)
    k=row["governance"]["legacy_ref"] if kind=="NativeVocabularyRecord" else row["payload"]["source_legacy_ref"]
    if k not in ids:continue
    need(k not in where and row["kind"]==kind and row["purpose"]=="CURATION_DEV" and row["governance"]["release_status"]=="HOLD","REGISTRY_SCOPE")
    prepare.verify_revision(row);where[k]=row
 need(set(native)==set(ctx)==ids,"REGISTRY_CLOSURE")
 strata=C.Counter();rights=C.Counter()
 for s in src:
  n=native[s["source_ref"]];p=n["payload"];q=ctx[s["source_ref"]]["payload"]
  need(p["native_label"]==q["native_label"]==s["source_native_label"] and p["native_kind"]==q["source_grain"]==s["native_kind"] and p["native_namespace"]==q["source_scope"]==s["source_scope"],"NATIVE_IDENTITY")
  for k in ("artifact_sha256","source_locator","source_anchor_ref"):need(p[k]==q[k]==s[k],"NATIVE_ANCHOR")
  need(q["source_ref"]==prepare.ref(n) and p["native_aliases"]==s["native_aliases"] and q["native_ingredient_names"]==s["reference_recipe_ingredient_names"] and q["context_locator"]==s["context_locator"],"NATIVE_CONTEXT")
  strata[(q["cohort"],q["source_scope"])]+=1;rights.update(n["governance"]["rights_domains"])
 need(len(strata)==4 and set(strata.values())=={8} and rights=={"NUTRIDATA_RIGHTS_UNRESOLVED":32},"STRATA_RIGHTS")
 mf=load(pin(root/MAN,fs[str(MAN)]));manifest={x["sha256"]:x for x in mf}
 verified=0
 for path in RAW:
  h=fs[str(path)];p=pin(root/path,h)
  need(h in manifest and manifest[h]["file"]==path.name and p.stat().st_size==manifest[h]["size_bytes"],"RAW_MANIFEST")
  ss=[s for s in src if s["artifact_sha256"]==h];need(ss and len({s["source_scope"] for s in ss})==1,"RAW_SOURCE_SCOPE")
  prepare.raw_check(p,ss,ss[0]["source_scope"],native);verified+=len(ss)
 need(verified==32,"RAW32")
 def forms(s):return {v.norm(s["source_native_label"]),*[v.norm(x["text"]) for x in s["native_aliases"]]}-{""}
 first_labels={v.norm(s["source_native_label"]) for s in first};first_forms=set().union(*(forms(s) for s in first))
 return {"source_identity_verified":32,"raw_workbooks_verified":2,"raw_rows_verified":verified,"strata":[{"cohort":k[0],"scope":k[1],"n":n} for k,n in sorted(strata.items())],"rights_domains":dict(rights),"first44_source_id_overlap":0,"first44_review_id_overlap":0,"first44_exact_normalized_label_overlap_cases":sum(v.norm(s["source_native_label"]) in first_labels for s in src),"first44_exact_normalized_label_or_alias_overlap_cases":sum(bool(forms(s)&first_forms) for s in src),"within32_duplicate_normalized_label_cases":sum(n for n in C.Counter(v.norm(s["source_native_label"]) for s in src).values() if n>1),"external_dataset_validation":False,"same_source_family":True}
def audit_refs(root,run,stage,prep,v,r36,src):
 task=load(stage/"A2ReviewTask.json");std=v.Standards(stage,task["allowed_inputs"])
 schema=load(stage/v.SCHEMA);v.Draft202012Validator.check_schema(schema);val=v.Draft202012Validator(schema)
 oq,oh,pm=v.parent(root,src,std)
 method=load(pin(run/"ReviewerMethodFreeze.json",METHOD))
 need(method==v.metadata(root,stage,prep,src,pm),"METHOD_RECONSTRUCTION")
 priv=run/"reviewer_private"
 final=load(pin(run/"A2FinalReferenceFreezeReceipt.json",FINAL_SHA))
 f=priv/"Final";need(tree(f)==final["final_file_hashes"],"FINAL_PACKAGE_DRIFT")
 mf=load(f/"ExecutionManifest.json");cf=load(f/"CriticFreezeReceipt.json")
 need(mf["source_count"]==32 and mf["input_hashes"]==prep["reviewer_staging_sha256"] and mf["source_only"] and mf["prior_exposure_declared"] and not mf["confirmatory_blind_claimed"],"MANIFEST_SCOPE")
 need(cf["status"]=="REVIEW_FROZEN" and cf["completed_cases"]==32 and not any(cf[x] for x in ("scientific_reference_qualified","mapping_release_authorized","unblind_authorized","comparison_executed")),"CRITIC_SCOPE")
 need(all(sha(f/k)==h for k,h in cf["output_file_hashes"].items()),"CRITIC_OUTPUT_HASH")
 replay=load(pin(run/"summaries/Run_031.json",final["zero_dispatch_replay_summary_sha256"]))
 need(replay["completed_cases"]==replay["replayed_cases"]==replay["query_checkpoints_verified"]==32 and replay["new_cases"]==0 and replay["failure"] is None and not replay["comparison_executed"] and not replay["unblind"],"REPLAY_SCOPE")
 need(final["case_freeze_hashes"]==mf["case_freeze_hashes"]==replay["case_freeze_hashes"],"CASE_HASH_CLOSURE")
 rows=[json.loads(x) for x in (f/"ReviewRecords.jsonl").read_text().splitlines() if x.strip()];need(len(rows)==32,"FINAL32")
 stats=C.Counter();states={k:C.Counter() for k in v.project.__globals__["DIMS"]};relations=C.Counter();apps=C.Counter();conflicts=C.Counter();dispos=C.Counter();search=C.Counter();per_sys={k:C.Counter() for k in VERSION};flags=C.Counter();cases=[];sessions=set()
 supported_case=0;any_candidate=0
 for i,(s,r) in enumerate(zip(src,rows),1):
  c=priv/("case_%03d"%i);ss=v.digest(s);rid=s["review_id"]
  frozen=load(pin(c/"CaseFreeze.json",final["case_freeze_hashes"][c.name]));qf=load(pin(c/"QueryFreeze.json",frozen["query_freeze_sha256"]))
  need(frozen["source_sha256"]==qf["source_sha256"]==ss and frozen["method_sha256"]==qf["method_sha256"]==METHOD,"CASE_SOURCE_METHOD")
  if i<=4:
   q=oq[rid];hits=oh[rid];need(qf=={"method_sha256":METHOD,"source_sha256":ss,"origin":"PARENT_EXACT_REPLAY","parent":pm,"query":q,"hits":hits},"PARENT_QUERY")
  else:
   qa=c/"query_attempt_01";t=v.read_attempt(qa,METHOD,"query",ss)
   need(t["status"]=="RESPONSE_COMPLETE" and t["stop_reason"]=="end_turn" and t["sent"] and t["rpc_returned"] and t["tool_requests"]==t["tool_updates"]==0 and t["model_id"]==v.MODEL,"QUERY_TERMINAL")
   need(t["session_id_sha256"] not in sessions,"SESSION_REUSE");sessions.add(t["session_id_sha256"])
   q=v.queries_ok(v.json_answer((qa/"RawResponse.txt").read_text()),[s])[rid]
   qa_v=load(qa/"Validation.json");need(qa_v=={"terminal_sha256":sha(qa/"Terminal.json"),"status":"PASS","error":None,"projection_sha256":v.digest(q)},"QUERY_VALIDATION")
   need((qa/"Prompt.txt").read_text()==v.query_prompt(s,task["rules"]),"QUERY_PROMPT")
   hits={k:std.search(k,z) for k,z in q.items()}
   ar={"attempt":1,"terminal_sha256":sha(qa/"Terminal.json"),"validation_sha256":sha(qa/"Validation.json"),"raw_sha256":t["raw_sha256"]}
   need(qf=={"method_sha256":METHOD,"source_sha256":ss,"origin":"AGY_CASE_QUERY","attempt":ar,"query":q,"hits":hits},"QUERY_REPLAY")
  ar=frozen["review_attempt"];a=c/("review_attempt_%02d"%ar["attempt"]);t=v.read_attempt(a,METHOD,"review",ss)
  need(t["status"]=="RESPONSE_COMPLETE" and t["stop_reason"]=="end_turn" and t["sent"] and t["rpc_returned"] and t["tool_requests"]==t["tool_updates"]==0 and t["model_id"]==v.MODEL,"REVIEW_TERMINAL")
  need(t["session_id_sha256"] not in sessions,"SESSION_REUSE");sessions.add(t["session_id_sha256"])
  need((a/"Prompt.txt").read_text()==v.review_prompt(s,q,hits,task["rules"]),"REVIEW_PROMPT")
  pin(a/"Terminal.json",ar["terminal_sha256"]);pin(a/"Validation.json",ar["validation_sha256"]);pin(a/"RawResponse.txt",ar["raw_sha256"])
  raw=v.json_answer((a/"RawResponse.txt").read_text())
  full=v.project(raw,s,q,hits)
  checked=v.validate_records(full,[s],{rid:q},{rid:hits},std,val,task["allowed_inputs"])[0]
  need(checked==r==load(pin(c/"ReviewRecord.json",frozen["record_sha256"])),"EXACT_RECORD_PROJECTION")
  need(load(a/"Validation.json")["projection_sha256"]==v.digest({"record":r,"review_note":full["review_note"]}) and frozen["review_note_sha256"]==v.digest(full["review_note"]),"PROJECTION_DIGEST")
  need(r["review_status"]=="CRITIC_DRAFT" and r["purpose"]=="CURATION_DEV_ONLY" and not any(r[x] for x in ("accepted_equivalence","mapping_release_authorized","scientific_reference_qualified")),"SCIENTIFIC_SCOPE")
  ev=r["evidence"];sourceobs=v.canon({k:s[k] for k in ("source_native_label","native_kind","native_aliases","reference_recipe_ingredient_names","context_note")})
  native_rows={ (t["artifact_sha256"],t["target_locator"]):t for sys in hits.values() for rs in sys.values() for t in rs}
  for e in ev:
   if e["role"]=="SOURCE_EXPLICIT":need(e["artifact_sha256"]==s["artifact_sha256"] and e["locator"]==v.canon(s["source_locator"]) and e["observation"]==sourceobs,"SOURCE_CARRIER")
   else:
    need(e["role"]=="TARGET_EXPLICIT" and (e["artifact_sha256"],e["locator"]) in native_rows,"TARGET_CARRIER")
    t0=native_rows[e["artifact_sha256"],e["locator"]]
    need(e["observation"]==v.canon({k:t0[k] for k in ("target_native_label","raw_aliases","raw_definition") if k in t0}),"TARGET_OBSERVATION")
  local=C.Counter()
  def flag(k):local[k]+=1;flags[k]+=1
  src_indices={j for j,e in enumerate(ev) if e["role"]=="SOURCE_EXPLICIT"}
  need(len(src_indices)<=1,"SOURCE_CARRIER_DUP")
  stats["cases_with_source_evidence"]+=bool(src_indices)
  stats["evidence_objects"]+=len(ev)
  for k,dd in r["source_dimensions"].items():
   state=dd["state"];states[k][state]+=1;stats["dimension_cells"]+=1
   if state=="SOURCE_EXPLICIT":need(bool(src_indices&set(dd["evidence_refs"])),"SOURCE_DIM_ANCHOR")
   if state=="EXTERNAL_SUPPORTED":need(any(ev[j]["role"]=="TARGET_EXPLICIT" for j in dd["evidence_refs"]),"EXTERNAL_DIM_ANCHOR");flag("TARGET_SUPPORTED_SOURCE_DIMENSION_REVIEW")
   if state=="SEMANTIC_INFERENCE" and k in ("food_state","species_variety","edible_part","composition","regional_scope"):flag("SENSITIVE_DIMENSION_INFERENCE_REVIEW")
   if state!="UNRESOLVED" and not dd["value"].strip():flag("WHITESPACE_DIMENSION")
  pos=r["independent_candidates"];neg=r["hard_negatives"];dispos[r["case_disposition"]]+=1
  stats["candidate_edges"]+=len(pos);stats["hard_negative_edges"]+=len(neg);stats["cases_with_candidates"]+=bool(pos)
  supported=[x for x in pos if x["relation"] in SUPPORT and x["applicability"]!="UNRESOLVED"]
  stats["supported_edges_before_universe_membership"]+=len(supported);stats["cases_with_any_supported_edge_before_universe_membership"]+=bool(supported)
  stats["supported_edges_excluding_related_before_membership"]+=sum(x["relation"]!="RELATED" and x["applicability"]!="RELATED_ONLY" for x in supported)
  for x in pos+neg:
   sys,ver,nid=x["target_key"];need(ver==VERSION[sys] and tuple(x["target_key"]) in std.by,"NATIVE_VERSION_KEY")
   # Explicit exact target evidence AND source support availability.
   target=std.by[tuple(x["target_key"])]
   need(x["target_native_label"]==target["target_native_label"] and x["target_locator"]==target["target_locator"],"NATIVE_LABEL_LOCATOR")
   has_source=bool(src_indices&set(x["evidence_refs"]))
   stats["edges_with_direct_source_and_target_anchor"]+=has_source
   if not has_source:flag("EDGE_SOURCE_ANCHOR_NOT_SELECTED")
   if not x["rationale"].strip():flag("WHITESPACE_RATIONALE")
   per_sys[sys]["edges"]+=1
   if sys=="FNDDS":need(" | " in x["target_locator"] and "Foods and Beverages:row:" in x["target_locator"],"FNDDS_DUAL_LOCATOR")
  for x in pos:
   rel,app=x["relation"],x["applicability"];relations[rel]+=1;apps[app]+=1
   need(x["direction"]=="SOURCE_RELATION_TO_TARGET" and x["measurement_transfer"]=="HOLD","DIRECTION_TRANSFER")
   if rel=="CONDITIONAL" or app=="CONDITIONAL_CONCEPT_CANDIDATE":need(bool(x["conditions"]),"CONDITIONS_REQUIRED")
   if any(not s.strip() for s in x["conditions"]):flag("WHITESPACE_CONDITION")
   if rel in ("AMBIGUOUS","UNRESOLVED") and app!="UNRESOLVED":flag("AMBIGUOUS_RELATION_NONUNRESOLVED_APPLICABILITY")
   if rel=="RELATED" and app not in ("RELATED_ONLY","UNRESOLVED"):flag("RELATED_APPLICABILITY_REVIEW")
   if rel!="RELATED" and app=="RELATED_ONLY":flag("NONRELATED_RELATION_RELATED_ONLY_REVIEW")
   if rel=="EXACT" and any(r["source_dimensions"][k]["state"]=="UNRESOLVED" for k in ("entity_grain","food_state","preparation","species_variety","edible_part","composition")):flag("EXACT_WITH_UNRESOLVED_QUALIFIERS_REVIEW")
   if rel in ("BROADER_TARGET","NARROWER_TARGET"):stats["directional_semantic_edges_requiring_expert"]+=1
  for x in neg:
   conflicts[x["conflict_type"]]+=1
   if x["conflict_type"]=="UNRESOLVED_OTHER":flag("UNRESOLVED_OTHER_COUNTED_AS_NEGATIVE_REVIEW")
   if x["conflict_type"]=="TARGET_SPECIFIC_CONDITION":flag("TARGET_CONDITION_NEGATIVE_REVIEW")
  for a0 in r["search_attempts"]:
   sy=a0["target_system"];res=a0["result"];search[res]+=1;per_sys[sy]["searches"]+=1
   per_sys[sy]["terms"]+=len(q[sy]);per_sys[sy]["returned_rows_with_repetition"]+=sum(map(len,hits[sy].values()))
   per_sys[sy]["distinct_returned_rows_per_case"]+=len({tuple(t["target_key"]) for xs in hits[sy].values() for t in xs})
   per_sys[sy]["terms_at_cap"]+=sum(len(xs)==5 for xs in hits[sy].values())
   ps=[x for x in supported if x["target_key"][0]==sy]
   if res=="NO_SUPPORTED_TARGET_IN_REVIEWED_MATERIAL" and ps:flag("NO_SUPPORTED_SEARCH_WITH_SUPPORTED_EDGE")
   if res=="CANDIDATES_FOUND" and not any(x["target_key"][0]==sy for x in pos):flag("CANDIDATES_FOUND_WITHOUT_RECORDED_CANDIDATE_REVIEW")
   if res in ("INSUFFICIENT_SOURCE","SEARCH_INCOMPLETE"):flag("BOUNDED_SEARCH_UNCERTAINTY")
  if r["case_disposition"]=="CANDIDATE_CONCEPT_ONLY" and not supported:flag("CANDIDATE_DISPOSITION_WITHOUT_SUPPORTED_EDGE_REVIEW")
  stats["cases_reviewer_minutes_unobserved"]+=r["reviewer_minutes"]==0
  cases.append({"ordinal":i,"source_scope":s["source_scope"],"flags":dict(local),"candidate_count":len(pos),"hard_negative_count":len(neg),"support_count_before_membership":len(supported),"expert_semantic_review":"PENDING"})
 need(stats["dimension_cells"]==256 and sum(search.values())==96 and len(sessions)==60,"REFERENCE_ACCOUNTING")
 return {"reference_records_verified":32,"query_checkpoints_rederived":32,"parent_query_reuses":4,"native_authority_counts":{s:len(std.rows[s]) for s in VERSION},"exact_prompt_reconstruction":32,"distinct_accepted_current_run_session_hashes":len(sessions),"schema_native_version_locator_verified":True,"all_final_rows_exact_projection":True,"reference_only_counts":dict(stats),"dimension_state_counts":{k:dict(v) for k,v in states.items()},"relation_counts":dict(relations),"applicability_counts":dict(apps),"hard_negative_conflict_types":dict(conflicts),"case_dispositions":dict(dispos),"search_outcomes":dict(search),"search_scope_counts":{k:dict(x) for k,x in per_sys.items()},"screening_flag_counts":dict(flags),"screened_cases_with_flags":sum(bool(c["flags"]) for c in cases),"cases":cases,"screening_limit":"Rule-based carrier/semantic-consistency flags, not independent human judgments; no actual frozen universe intersection or evaluated-arm statistics."}
def main(root):
 out=root/OUT;run=root/RUN
 need(not out.exists(),"NEW_AUDIT_DIR")
 reads,blocked,dispatch,hook=fence(root,out);sys.addaudithook(hook)
 import agy_r36_exception as a
 import prepare_a2 as prepare
 import agy_raw_standard_browser as browser
 from a26_score_contract_tests import run_synthetic
 v=a.v
 # Lock already exists; open read-only and acquire exclusive lock.
 with (run/".controller.lock").open("r") as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  stage,prep,probe=v.verify(root)
  pin(root/B/"local_001/PreparationFreeze.json",PREP);pin(root/B/"local_001/A2RetrievalFreezeReceipt.json",RET)
  policy=load(pin(root/POLPATH,POL))
  need(policy["primary_arm"]=="SOURCE_SPARSE" and policy["comparators"]==["BASELINE_FUSION","HYBRID"],"FROZEN_ARMS")
  for path,h in policy["pins"].items():
   # No protected universe, lexicon or actual rank reads, even for hashing.
   if path.startswith("src/"):pin(root/path,h)
  src=load(pin(stage/SOURCE,prep["source_packet_sha256"]))
  pin(root/SOURCE,prep["source_packet_sha256"])
  final=load(pin(run/"A2FinalReferenceFreezeReceipt.json",FINAL_SHA));need(final["completed_cases"]==32 and final["complete_reference_set"] and not final["unblind_authorized"] and not final["comparison_executed"],"FINAL_SCOPE")
  oldpriv=tree(run/"reviewer_private");oldrt=tree(run/"runtime")
  need(len(oldpriv)==488 and digest(oldpriv)=="b0bbe2b77535e5e119c2ccf6cffe97de421987a450bd0138f5311fa4dfb3c94d","PRIVATE_SET_DRIFT")
  need(len(oldrt)==260 and digest(oldrt)=="a0251a20a370eb01d200122605367503a01848b22e885ec4f38ad79969d2a3ab","RUNTIME_SET_DRIFT")
  # Verify both special recovery contracts by read-only exact validation.
  # Their helper normally permits append if missing; prohibit any such write.
  def existing(p,z):need(p.is_file() and load(p)==z,"RECOVERY_EXISTING_RECEIPT")
  orig=a.r2.exact_or_append;a.r2.exact_or_append=existing
  try:
   with redirect_stdout(io.StringIO()):
    x=a.context(root,run);z=a.finish(root,run,run/"exception_r36_016",x)
   need(z["status"]=="PASS_EXCEPTION_CASE_FROZEN","EXCEPTION_LINEAGE")
  finally:a.r2.exact_or_append=orig
  retry=load(pin(run/"A2FrozenExecutionSegment_006R1RetryReceipt.json",final["historical_recovery_receipts"]["case_024"]))
  subset(run/"retry_024_segment_006r1",retry["retry_artifact_sha256"])
  need(retry["accepted_attempt"]==2 and retry["third_attempt_authorized"] is False,"RETRY024_SCOPE")
  # The actual scientific case audit is independent of evaluated outcomes.
  src_report=source_audit(root,src,prep,prepare,browser)
  print("P0.1 source-only raw/registry provenance verified 32/32",flush=True)
  ref_report=audit_refs(root,run,stage,prep,v,a,src)
  print("P0.2 32 case projections and semantic consistency screens complete",flush=True)
  scoring=run_synthetic()
  need(not blocked and not dispatch,"AUDIT_FENCE_VIOLATION")
  need(tree(run/"reviewer_private")==oldpriv and tree(run/"runtime")==oldrt,"POST_AUDIT_DRIFT")
  need(not final["scientific_reference_qualified"],"PREMATURE_QUALIFICATION")
  out.mkdir(mode=0o700)
  cases=ref_report.pop("cases")
  audit={"version":"A2.6-P0-PREUNBLIND-AUDIT-v0.1","status":"PASS_PROVENANCE_AND_STRUCTURAL_AUDIT / HOLD_SCIENTIFIC_QUALIFICATION_AND_COMPARISON","final_reference_receipt_sha256":FINAL_SHA,"scientific_method_sha256":METHOD,"retrieval_freeze_receipt_sha256":RET,"retrieval_policy_sha256":POL,"score_code_sha256":sha(root/"src/u3r2p2a2/score_a2.py"),"support_code_sha256":sha(root/"src/u3r2/compare_reference.py"),"audit_code_sha256":sha(Path(__file__)),"synthetic_test_code_sha256":sha(root/"src/u3r2p2a2/a26_score_contract_tests.py"),"source_audit":src_report,"reference_audit":ref_report,"independence":{"source_first":True,"pre_reference_retrieval_freeze_receipt_verified":True,"first44_id_disjoint":True,"prior_exposure_declared":True,"strict_confirmatory_blindness_proven":False,"provider_backend_attested":False,"reviewer_acl_historical_preparation_flag":prep["reviewer_acl_verified"],"actual_runtime_sandbox_evidence":"Frozen code requires per-attempt local read-denial probes and disables tool access; accepted terminal evidence verified, not an independent historical provider access log.","fresh_session_hashes_verified":60,"parent_query_reuse":4,"rights_unresolved_cases":32,"expert_adjudications_completed":0,"original_staging_external_transfer_authorized":prep["external_transfer_authorized"],"owner_runtime_authorization_is_not_legal_license":True},"scoring_synthetic_only":scoring,"audit_boundary":{"application_open_allowlist_enforced":True,"project_read_paths_count":len(reads),"forbidden_open_attempts":len(blocked),"network_or_subprocess_attempts":len(dispatch),"actual_tested_rank_lists_read":0,"actual_retrieval_results_read":0,"actual_scores_computed":0,"actual_target_universe_read":False,"actual_reference_denominator_by_universe_computed":False,"no_model_dispatch":True,"private_file_pins_unchanged":488,"runtime_file_pins_unchanged":260},"scientific_reference_qualified":False,"developmental_comparison_authorized":False,"comparison_executed":False,"unblind_authorized":False,"mapping_release":0,"generalization_validated":False}
  # Case-ordinal-only flags stay local, not uploaded or given to ranking controller.
  v.obj(out/"PrivateOrdinalScreening.json",cases)
  v.obj(out/"A26P0AuditAggregate.json",audit)
  v.obj(out/"PrivateReadSet.json",{"paths":sorted(reads),"note":"Project open events only; not independent OS/provider attestation. No comparator files opened."})
  print(json.dumps(audit,ensure_ascii=False),flush=True)
if __name__=="__main__":
 main(Path.cwd().resolve())
