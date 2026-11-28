#!/usr/bin/env python3
"""Freeze A2.6-P0 audit decision and local expert adjudication handoff.
No scoring of real ranks or comparator access, no model or reviewer dispatch."""
import ast,collections as C,fcntl,json,os,sys
from pathlib import Path
from audit_a26_p0 import B,RUN,ST,OUT,FINAL_SHA,METHOD,PREP,RET,POL,need,load,sha,pin,tree,digest,fence
def save(p,x):
 with p.open("x",encoding="utf8") as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write("\n")
 os.chmod(p,0o600)
def main(root):
 out=root/OUT;r=root/RUN;priv=r/"reviewer_private";rt=r/"runtime"
 reads,blocked,dispatch,hook=fence(root,out);sys.addaudithook(hook)
 with (r/".controller.lock").open("r") as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  final=load(pin(r/"A2FinalReferenceFreezeReceipt.json",FINAL_SHA))
  p=out/"A26P0AuditAggregate.json";a=load(p)
  need(a["final_reference_receipt_sha256"]==FINAL_SHA and a["scientific_method_sha256"]==METHOD and a["retrieval_freeze_receipt_sha256"]==RET and a["retrieval_policy_sha256"]==POL,"AUDIT_BASELINE")
  need(a["reference_audit"]["reference_records_verified"]==32 and a["source_audit"]["raw_rows_verified"]==32 and a["reference_audit"]["reference_only_counts"]["edges_with_direct_source_and_target_anchor"]==386,"AUDIT_COUNTS")
  need(not a["scientific_reference_qualified"] and not a["developmental_comparison_authorized"] and not a["comparison_executed"] and not a["unblind_authorized"],"AUDIT_SCOPE")
  need(a["audit_boundary"]["actual_retrieval_results_read"]==a["audit_boundary"]["actual_scores_computed"]==a["audit_boundary"]["forbidden_open_attempts"]==0,"AUDIT_NO_UNBLIND")
  pin(root/"src/u3r2p2a2/audit_a26_p0.py",a["audit_code_sha256"]);pin(root/"src/u3r2p2a2/a26_score_contract_tests.py",a["synthetic_test_code_sha256"])
  pin(root/"src/u3r2p2a2/score_a2.py",a["score_code_sha256"]);pin(root/"src/u3r2/compare_reference.py",a["support_code_sha256"])
  private_pins=tree(priv);runtime_pins=tree(rt)
  need(len(private_pins)==488 and digest(private_pins)=="b0bbe2b77535e5e119c2ccf6cffe97de421987a450bd0138f5311fa4dfb3c94d","PRIVATE_DRIFT")
  need(len(runtime_pins)==260 and digest(runtime_pins)=="a0251a20a370eb01d200122605367503a01848b22e885ec4f38ad79969d2a3ab","RUNTIME_DRIFT")
  need(tree(priv/"Final")==final["final_file_hashes"],"FINAL_DRIFT")
  # Historical execution audit. Derive sentinel bytes from the pinned code,
  # not a manually transcribed expected literal.
  pr=root/B/"agy_authenticated_probe_006";probe=load(pr/"ProbeReceipt.json")
  base=pin(pr/"AGYProbe.sb","120596ea758bb45345a1a715550c282a07ff0bced471013e0e21ff102ed0f8f1").read_text()
  need(probe["status"]=="PASS_ACTUAL_SYNTHETIC_WORKER" and probe["denied_read_blocked"] and probe["denied_write_blocked"] and probe["forbidden_probe_read_denied"] and probe["outer_sandbox_required"] and not probe["inner_terminal_sandbox"] and not probe["source_sent"],"PROBE_GATE")
  method=load(pin(r/"ReviewerMethodFreeze.json",METHOD))
  runner=pin(root/"src/u3r2p2a2/agy_r1_runner_v2.py",method["code_sha256"]["agy_r1_runner_v2.py"])
  fn=next(x for x in ast.parse(runner.read_text()).body if isinstance(x,ast.FunctionDef) and x.name=="invoke")
  lit=[x.args[1].value for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=="put" and len(x.args)==2 and isinstance(x.args[0],ast.Name) and x.args[0].id=="syn" and isinstance(x.args[1],ast.Constant)]
  need(len(lit)==1,"SENTINEL_LITERAL")
  sessions=set();counts=C.Counter()
  for c in sorted(priv.glob("case_*")):
   i=int(c.name.split("_")[1])
   for attempt in sorted(c.glob("*_attempt_*")):
    kind,_,num=attempt.name.split("_");runtime=rt/("%03d_%s_%s"%(i,kind,num));l=load(attempt/"Launch.json");di=load(attempt/"DispatchIntent.json")
    need(l["profile_sha256"]==sha(runtime/"AGYReview.sb") and (runtime/"AGYReview.sb").read_text()==base.replace(str(pr),str(runtime)),"PROFILE_BINDING")
    need((runtime/"empty_workspace/read_probe.txt").read_bytes()==lit[0].encode(),"SENTINEL")
    need(l["case_ordinal"]==i and l["stage"]==kind and l["attempt"]==int(num) and not l["tool_permission"],"LAUNCH")
    need(di["prompt_sha256"]==l["prompt_sha256"]==sha(attempt/"Prompt.txt") and di["model_id"]==l["declared_model_required"]==method["model_id"],"DISPATCH")
    need(di["session_id_sha256"] not in sessions,"SESSION_REUSE");sessions.add(di["session_id_sha256"]);counts["profile_and_dispatch_bindings"]+=1
    if (attempt/"Terminal.json").is_file():
     t=load(attempt/"Terminal.json");need(t["tool_requests"]==t["tool_updates"]==0 and t["session_id_sha256"]==di["session_id_sha256"],"TOOL_OR_SESSION")
     counts["known_terminal_no_tool_use"]+=1
    else:
     need(i==8 and attempt.name=="review_attempt_01","UNKNOWN_TERMINAL_SCOPE")
     counts["unknown_original_terminal"]+=1
  need(counts=={"profile_and_dispatch_bindings":65,"known_terminal_no_tool_use":64,"unknown_original_terminal":1},"EXECUTION_ACCOUNTING")
  # Prepare local queue. No raw text/IDs/authority keys in public outputs.
  screen=load(out/"PrivateOrdinalScreening.json")
  need(len(screen)==32 and [x["ordinal"] for x in screen]==list(range(1,33)),"ORDINAL_QUEUE")
  queue=[];edge_flags=C.Counter();dim_flags=C.Counter()
  for i,scr in enumerate(screen,1):
   c=priv/("case_%03d"%i);pin(c/"CaseFreeze.json",final["case_freeze_hashes"][c.name])
   cf=load(c/"CaseFreeze.json");r0=load(pin(c/"ReviewRecord.json",cf["record_sha256"]))
   dims=[];edges=[]
   for k,x in r0["source_dimensions"].items():
    flags=[]
    if x["state"]=="EXTERNAL_SUPPORTED":flags.append("TARGET_SUPPORTED_SOURCE_DIMENSION_REVIEW")
    if x["state"]=="SEMANTIC_INFERENCE" and k in ("food_state","species_variety","edible_part","composition","regional_scope"):flags.append("SENSITIVE_DIMENSION_INFERENCE_REVIEW")
    dim_flags.update(flags);dims.append({"dimension":k,"evidence_refs":x["evidence_refs"],"screening_flags":flags,"expert_status":"PENDING"})
   for field in ("independent_candidates","hard_negatives"):
    for n,x in enumerate(r0[field]):
     flags=[]
     if field=="independent_candidates":
      if x["relation"]!="RELATED" and x["applicability"]=="RELATED_ONLY":flags.append("NONRELATED_RELATION_RELATED_ONLY_REVIEW")
     else:
      if x["conflict_type"]=="UNRESOLVED_OTHER":flags.append("UNRESOLVED_OTHER_COUNTED_AS_NEGATIVE_REVIEW")
      if x["conflict_type"]=="TARGET_SPECIFIC_CONDITION":flags.append("TARGET_CONDITION_NEGATIVE_REVIEW")
     edge_flags.update(flags)
     edges.append({"field":field,"zero_based_index":n,"evidence_refs":x["evidence_refs"],"screening_flags":flags,"expert_status":"PENDING"})
   queue.append({"ordinal":i,"source_packet_ordinal":i,"case_freeze_sha256":sha(c/"CaseFreeze.json"),"reference_record_sha256":sha(c/"ReviewRecord.json"),"reference_path":str((c/"ReviewRecord.json").relative_to(root)),"dimensions":dims,"edges":edges,"phase_a_source_only":"NOT_ASSIGNED","phase_b_reference_adjudication":"NOT_ASSIGNED"})
  expected=a["reference_audit"]["screening_flag_counts"];need(dict(edge_flags+dim_flags)==expected,"QUEUE_FLAG_CLOSURE")
  need(sum(len(x["dimensions"]) for x in queue)==256 and sum(len(x["edges"]) for x in queue)==386,"QUEUE_COUNTS")
  need(not blocked and not dispatch,"AUDIT_FENCE_VIOLATION")
  need(tree(priv)==private_pins and tree(rt)==runtime_pins,"POST_AUDIT_DRIFT")
  q=out/"PrivateAdjudicationQueue.json"
  save(q,{"version":"A2.6-P0-PRIVATE-ADJUDICATION-QUEUE-v0.1","status":"PREPARED_NOT_ASSIGNED_NOT_DISPATCHED","cases":queue})
  handoff={"version":"A2.6-P0-EXPERT-HANDOFF-v0.1","status":"PREPARED_NOT_ASSIGNED_NOT_DISPATCHED","reference_receipt_sha256":FINAL_SHA,"private_queue_sha256":sha(q),"cases":32,"dimension_cells":256,"candidate_edges":111,"hard_negative_edges":275,"priority_flag_counts":expected,"priority":"Resolve UNRESOLVED_OTHER negative, non-RELATED/RELATED_ONLY compatibility, explicit support versus missing target conditions, and sensitive source-dimension inferences before deciding comparison scope; retain all original records.","phase_a":{"reviewer":"PI-appointed qualified food ontology/nutrition expert; independent of evaluated ranker","inputs":"Source-only packet, pinned three authority versions, original task rules; no AGY reference or tested retrieval/rank output","required":"Independent judgments and evidence; explicit unresolved; preserve all 32 cases","status":"NOT_ASSIGNED"},"phase_b":{"reviewer":"Qualified expert(s) independently adjudicate frozen AGY references against source and authority rows; preserve disagreement","inputs":"Source and authority evidence, immutable AGY reference records and local ordinal queue; no tested retrieval/rank output","required":"Separate signed/hashed accept, revise, abstain or unresolved decisions; never overwrite AGY record or infer nutrient transfer","status":"NOT_ASSIGNED"},"gold_requirement":"For scientific Gold, independent qualified human decisions with discrepancy adjudication and rights clearance; not achieved by programmatic checks or model agreement.","developmental_scope":"The original protocol allows separately authorized developmental overlap without expert Gold. Require PI-documented allowed use, explicit handling of flagged reference semantics and import guard before any actual comparison. Full expert adjudication is a scientific qualification path, not a retroactive alteration of frozen primary metrics.","new_expert_dispatch":False,"new_model_dispatch":False,"comparison_executed":False,"unblind_authorized":False}
  hp=out/"A26P0ExpertHandoff.json";save(hp,handoff)
  gate={"version":"A2.6-P0-COMPARISON-GATE-v0.1","status":"HOLD_SCIENTIFIC_QUALIFICATION_AND_COMPARISON_AUTHORIZATION","reference_receipt_sha256":FINAL_SHA,"audit_aggregate_sha256":sha(p),"expert_handoff_sha256":sha(hp),"stages":{"P0.1":"PASS_SOURCE_PROVENANCE_AND_NATIVE_CARRIER","P0.2":"PASS_RULE_SCREENING / HOLD_SUBSTANTIVE_EXPERT_SEMANTIC_QUALIFICATION","P0.3":"PASS_BOUNDED_LOCAL_SOURCE_FIRST_CONTROLS / HOLD_STRICT_CONFIRMATORY_INDEPENDENCE_AND_RIGHTS","P0.4":"PASS_FROZEN_SCORING_ARITHMETIC / HOLD_REAL_IMPORT_CONTRACT","P0.5":"HOLD_NO_COMPARISON_AUTHORIZATION"},"historical_local_execution":{"profile_and_dispatch_bindings":65,"distinct_dispatch_session_hashes":len(sessions),"known_terminal_no_tool_use":64,"original_unknown_terminal":1,"source_free_synthetic_probe_denied_reads_and_writes":True,"actual_per_attempt_denial_inferred_from_frozen_controller_launch_order":True,"independent_historical_OS_access_log_available":False,"provider_backend_attested":False,"prior_exposure_unknown":True},"qualification":{"structural_native_reference":True,"developmental_reference_set_complete":True,"developmental_comparison_gate_passed":False,"scientific_reference_qualified":False,"expert_gold_count":0,"strict_confirmatory_blindness_proven":False,"external_dataset_validation":False,"rights_unresolved_cases":32},"pre_unblind_requirements":{"Q1":"PI/data custodian documented rights and purpose-specific authorization for local developmental comparison, expert access if used, and downstream use; prior execution consent is not license.","Q2":"Freeze adjudication policy for 1 UNRESOLVED_OTHER negative, 88 target-condition negatives, 3 non-RELATED/RELATED_ONLY entries, 3 target-supported source dimensions, 36 sensitive inferences. Retain original scorer/reference definitions; any separate adjudicated overlay/sensitivity must be versioned before ranks exposed, not silently reclassify.","Q3":"Implement fail-closed comparison importer in separate version; exact immutable 32 expected identities, reference/receipt/policy/score hashes, exact 384 groups (32 x 4 x 3), verified original/extension target universes 28845/1174, disjointness and native versions, trusted per-case/scope pool budget reconstructed from frozen dense hint union, integer and identical across arms; verify both rank output hashes before reading any contents; preserve empty groups and exact order. No data reads in this audit.","Q4":"PI separately explicitly authorizes a specific immutable comparison run and scope. No generic bool flag substitutes for versioned owner decision and trusted input receipt.","Q5":"Only after Q1–Q4 pass, compute original predeclared reference overlap; preserve original and extension separate, K per scope, shared supported-reference denominator, all arms, hard-negative/unreviewed/reviewed neither distinction and non-RELATED sensitivity. No precision/recall, causal claim, winner tuning, mapping release or generalization claim."},"scientific_reference_qualified":False,"comparison_authorized":False,"comparison_executed":False,"unblind_authorized":False,"mapping_release":0,"generalization_validated":False,"next":"A2.6-P1 | Pre-unblind adjudication policy, rights decision & authorized import contract validation"}
  gp=out/"A26P0QualificationGate.json";save(gp,gate)
  receipt={"version":"A2.6-P0-QUALIFICATION-RECEIPT-v0.1","status":"PASS_AUDIT_EXECUTED / HOLD_SCIENTIFIC_QUALIFICATION_AND_COMPARISON","final_reference_receipt_sha256":FINAL_SHA,"scientific_method_sha256":METHOD,"retrieval_freeze_receipt_sha256":RET,"policy_sha256":POL,"audit_aggregate_sha256":sha(p),"qualification_gate_sha256":sha(gp),"expert_handoff_sha256":sha(hp),"private_ordinal_screening_sha256":sha(out/"PrivateOrdinalScreening.json"),"private_read_set_sha256":sha(out/"PrivateReadSet.json"),"private_adjudication_queue_sha256":sha(q),"audit_code_sha256":a["audit_code_sha256"],"synthetic_test_code_sha256":a["synthetic_test_code_sha256"],"finalization_code_sha256":sha(Path(__file__)),"source_rows_verified":32,"reference_records_verified":32,"double_anchored_edges":386,"semantic_expert_review_completed":0,"local_dispatch_bindings_verified":65,"known_no_tool_terminals":64,"private_files_unchanged":488,"runtime_files_unchanged":260,"final_files_unchanged":4,"project_read_paths_second_phase":len(reads),"new_model_dispatches":0,"tested_rank_lists_read":0,"real_retrieval_results_read":0,"real_scores_computed":0,"actual_target_universe_read":False,"forbidden_open_attempts":len(blocked),"network_or_subprocess_attempts":len(dispatch),"scientific_reference_qualified":False,"comparison_authorized":False,"comparison_executed":False,"unblind_authorized":False,"mapping_release":0,"limitations":["Structural/native evidence validation and rule-based screens are not expert entailment judgments.","Observed local controls and distinct session identifiers do not attest provider backend identity or historical exposure.","Source rights are unresolved; no transfer or scientific publication right inferred.","Proposed synthetic import guard is not an implemented real comparator-import authorization mechanism."]}
  save(out/"A26P0QualificationReceipt.json",receipt)
  need(not blocked and not dispatch,"FINAL_FENCE")
  print(json.dumps({"status":receipt["status"],"receipt_sha256":sha(out/"A26P0QualificationReceipt.json"),"gate_sha256":sha(gp),"handoff_sha256":sha(hp),"local_private_queue_cases":32,"local_private_queue_edge_items":386,"local_private_queue_dimension_items":256,"flag_counts":expected,"profile_bindings":65,"known_no_tool_terminals":64,"no_unblind":True,"comparison_authorized":False,"expert_review_dispatched":False}),flush=True)
if __name__=="__main__":main(Path.cwd().resolve())
