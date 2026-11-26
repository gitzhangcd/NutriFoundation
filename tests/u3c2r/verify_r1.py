#!/usr/bin/env python3
"""Actual R1 read-only verified gate replay and regression probes.
Synthetic response structures are test-only; no fake reviewer assignments.
"""
import sys,pathlib as P,json,copy,argparse,collections as C
sys.path.insert(0,str(P.Path(__file__).resolve().parents[2]/"src/u3c2r"))
from runtime_v2 import *
from risk_v2 import evaluate,features
from expert_gate_v2 import ExpertResponseGate,validate_schema,validate_bound_content,StandardInput,parse_standards,SCHEMA
def run(root,profile,ph,run,receipt_sha,packet,out):
 root=root.resolve();out=out.resolve()
 require(not out.exists() and out.is_relative_to(root/"runs/B2/U3-B/C2/R1") and not out.is_relative_to(run.resolve()),"NEW_VALIDATION_DIR")
 before={str(f.relative_to(run)):sha(f) for f in run.rglob("*") if f.is_file()}
 gate=VerifiedGate(root,profile,ph,run,receipt_sha);a=gate._a
 requests=C.Counter();risk_objects=[o for o in gate._records.values() if o["kind"]=="VerifiedRiskOverlay"]
 for o in risk_objects:
  for p in ("CURATION_INSPECT","DEVELOPMENT_CONCEPT_REVIEW","NUTRIENT_TRANSFER","MAPPING_RELEASE"):
   r=gate.request(p,ref(o));requests[(p,r["decision"])]+=1
 require(requests[("CURATION_INSPECT","ALLOW")]==len(risk_objects) and requests[("NUTRIENT_TRANSFER","HOLD")]==requests[("MAPPING_RELEASE","HOLD")]==len(risk_objects),"ACTUAL_GATE_COUNT")
 require(requests[("DEVELOPMENT_CONCEPT_REVIEW","ALLOW")]==sum(len(x["payload"]["shortlist_refs"]) for x in a.queries.values()),"REVIEW_SHORTLIST_GATE")
 tests=[]
 def check(name,fn,negative=None):
  try:
   require(fn() is not False,"ASSERTION");observed="ACCEPT";ok=negative is None
  except Exception as e:
   observed=str(e)[:180];ok=negative is not None and observed.startswith(negative)
  tests.append({"test":name,"expected":negative or "ACCEPT","actual":observed,"pass":ok})
 def pos(n,f):check(n,f)
 def neg(n,c,f):check(n,f,c)
 def mutate(o,fn):
  z=copy.deepcopy(o);fn(z);return seal(z)
 # Reproduce both bypasses on original real C2 schema/validator before fixing.
 sys.path.insert(0,str(root/"src/u3c2"))
 from run_c2 import validate as old_validate,validators as old_validators
 old_schema=load(root/C2/"real_001/C2_Contract.schema.json");ov=old_validators(old_schema)
 oldreg=dict(a.registry)
 # Old validator checks provenance refs as well as dependencies; recover actual
 # existing baseline projection endpoints from U2-C partitions for this probe.
 def populate_refs(refs):
  missing=set(refs)-set(oldreg)
  if not missing:return
  for kind in ("SourceSnapshotDraft","VocabularyAnchorDraft","SourceArtifact","SourceAnchor"):
   for o in a.partition(U2,kind,a.p["pins"][U2+"/private/partition_manifest.json"]):
    if ref(o) in missing:oldreg[ref(o)]=o;missing.remove(ref(o))
   if not missing:break
  if missing:
   base=root/"runs/B2/U3-A/real_002/private";mp=base/"collection_manifest.json";m=load(a.pin(str(mp.relative_to(root)),a.p["pins"]["runs/B2/U3-A/real_002/private/collection_manifest.json"]))
   for k in ("VocabularyAnchorDraft.jsonl","SourceSnapshotDraft.jsonl","NativeVocabularyRecord.jsonl"):
    if k not in m:continue
    f=a.pin(str((base/"typed_collections"/k).relative_to(root)),m[k]["sha256"])
    for o in lines(f):
     if ref(o) in missing:revision_ok(o);oldreg[ref(o)]=o;missing.remove(ref(o))
    if not missing:break
  require(not missing,"OLD_PROBE_REF_MISSING:"+str(sorted(missing)))
 oldscope=next(o for o in a.c2["ScopeAssessment"] if o["payload"]["iri"].endswith("FOODON_00003365"))
 populate_refs(oldscope["dependency_refs"]+oldscope["provenance_refs"])
 forge_scope=mutate(oldscope,lambda o:o["payload"].update(scope_status="CORE_RETAINED_DEV",exclusion_roots=[],witnesses=[{"root":o["payload"]["iri"],"steps":[]}]))
 pos("old actual scope self-root forgery reproduced",lambda:old_validate(forge_scope,ov,oldreg))
 newsc=a.scopes[oldscope["payload"]["iri"]]
 neg("resealed R1 excluded actual scope cannot promote","R1_RECOMPUTE_MISMATCH",lambda:a.verify_exact(mutate(newsc,lambda o:o["payload"].update(scope_status="CORE_RETAINED_DEV")),newsc,a.registry))
 oldred=next(o for o in a.c2["SemanticRiskAssessment"] if o["payload"]["cohort"]=="U3A_EXPOSED_44" and o["payload"]["disposition"]=="BLOCK_EXPLICIT_CONFLICT")
 populate_refs(oldred["dependency_refs"]+oldred["provenance_refs"])
 fake=mutate(oldred,lambda z:z["payload"].update(explicit_conflicts=[],unresolved_conditions=[],role_conditions=[],identity_evidence=["FORGED_ANCHOR"],disposition="REVIEW_ELIGIBLE_DEV_ONLY",concept_review_eligible=True,scope_assessment_ref=None))
 pos("old real RED resealed risk accepted by old structural validator",lambda:old_validate(fake,ov,oldreg))
 z=a.risks[ref(oldred)]
 def forged_risk():
  return a.verify_exact(mutate(z,lambda o:o["payload"].update(explicit_conflicts=[],unresolved_conditions=[],role_conditions=[],full_label_evidence="NORMALIZED_COMPLETE_SURFACE",disposition="COMPLETE_SURFACE_REVIEW_ONLY",review_eligible=True,scope_ref=None)),z,a.registry)
 neg("new gate recomputation rejects resealed actual RED","R1_RECOMPUTE_MISMATCH",forged_risk)
 neg("scientific release mutation rejected by strict schema","R1_SCHEMA",lambda:a.verify_exact(mutate(z,lambda o:o["payload"].update(mapping_release="ALLOW")),z,a.registry))
 q=next(o for o in a.queries.values() if o["payload"]["shortlist_refs"])
 missing=q["payload"]["shortlist_refs"][0]
 neg("query shortlist dependency stripping rejected","R1_RECOMPUTE_MISMATCH",lambda:a.verify_exact(mutate(q,lambda o:o.update(dependency_refs=[r for r in o["dependency_refs"] if r!=missing])),q,a.registry))
 pos("public runtime refuses unknown/forged risk ref",lambda:gate.request("DEVELOPMENT_CONCEPT_REVIEW",ref(fake))["decision"]=="HOLD")
 pos("all scientific-purpose requests held",lambda:requests[("MAPPING_RELEASE","HOLD")]==requests[("NUTRIENT_TRANSFER","HOLD")]==35710)
 neg("untrusted execution receipt rejected before derivation","UNTRUSTED_EXECUTION_RECEIPT",lambda:VerifiedGate(root,profile,ph,run,"0"*64))
 pos("entire persisted overlay rederived",lambda:len(gate._records)==76473 and len(a.scopes)==40107 and len(a.risks)==35710 and len(a.queries)==656)
 pos("old five actual audit mismatches held",lambda:a.summarize()["five_audit_mismatches_held"]==5)
 pos("old 23 hard-negative overlaps not review admitted",lambda:sum(x["count"] for x in a.summarize()["c1_critic_negative_routes"])==23)
 pos("six genuine FOODON-prefix exclusion probes",lambda:len(a.scope_stats["foodon_prefix_exclusion_probes"])==6 and all(x["scope_status"].startswith("HOLD") and "FOODON_" in x["iri"] for x in a.scope_stats["foodon_prefix_exclusion_probes"]))
 pos("103 organism-food overlaps retained as dual-role review-only",lambda:a.scope_stats["core_overlap_organism_role_review"]==103)
 p=a.policy
 def ev(x,y,g="INGREDIENT_REFERENCE",h="ONTOLOGY_FOOD_PRODUCT_CLASS"):
  return evaluate({"label":x,"grain":g},{"label":y,"grain":h},p,"CORE_RETAINED_DEV")
 for x,y in [("奶油","食用油"),("酱油","植物油"),("鱿鱼","鱼"),("海绵蛋糕","鸡蛋"),("sweet potato","potato"),("water spinach","spinach"),("apple","apple juice"),("egg","egg powder"),("bread","white bread"),("crab cakes","Crab cake sandwich, on bun"),("oil","corn oil"),("cottage cheese","cottage cheese (dry)")]:
  pos("residual HOLD: "+x+" / "+y,lambda x=x,y=y:not ev(x,y)["review_eligible"])
 for x,y in [("不加盐坚果","无盐坚果"),("未煮熟马铃薯","马铃薯(生)"),("Beans, boiled, from dried","Beans, fresh")]:
  pos("negation/origin not explicit contradiction: "+x,lambda x=x,y=y:not ev(x,y)["explicit_conflicts"] and not ev(x,y)["review_eligible"])
 pos("non-fried Chinese phrase does not assert frying",lambda:"fried" not in features("非油炸方便面")["explicit_mentions"] and "NOT_FRIED" in features("非油炸方便面")["negative_mentions"])
 pos("true explicit raw/boiled blocked",lambda:ev("马铃薯(煮)","potato (raw)")["disposition"]=="BLOCK_EXPLICIT_CONFLICT")
 pos("complete bilingual phrase supports only review",lambda:ev("马铃薯(煮)","potato (boiled)")["disposition"]=="COMPLETE_SURFACE_REVIEW_ONLY" and ev("马铃薯(煮)","potato (boiled)")["scientific_equivalence"]=="HOLD")
 pos("registered cross-role review not direct",lambda:ev("apple pie","apple pie","RECIPE_REFERENCE")["disposition"]=="CONDITIONAL_RELATION_REVIEW_ONLY")
 pos("unregistered cross-role same-name held",lambda:ev("rice","rice","BRANDED_PRODUCT_SNAPSHOT")["disposition"]=="HOLD_SCOPE_OR_UNREGISTERED_ROLE")
 # Expert packet verification on actual newly prepared task records.
 er=load(packet/"ExpertPacketR1Report.json");qa=packet/"reviewer_source_only/ExpertSourceFirstQueue.json";qb=packet/"controller_restricted/ExpertComparisonHidden.json"
 tasks=load(qa);post=load(qb);target_manifest=load(packet/"reviewer_source_only/TargetReferenceManifest.json")["reference_inputs"]
 require(sha(qa)==er["phase_a_queue_sha256"] and sha(qb)==er["phase_b_packet_sha256"],"EXPERT_PACKET_FENCE")
 pos("36 actual tasks with one uniform role set, no candidate opinion fields",lambda:len(tasks)==36 and len({tuple(x["required_roles"]) for x in tasks})==1 and all(not {"critic_expert_recommended","critic_hard_negative_overlap","old_review_id","priority_evidence","critic_relation"}&set(x) for x in tasks))
 pos("36 separated phase pairs and 130 stable evidence cards",lambda:{x["task_ref"] for x in tasks}=={x["task_ref"] for x in post} and sum(len(x["priority_evidence"]) for x in post)==130)
 pos("actual source and public target hashes unchanged",lambda:all(sha(root/x["source_access"]["path"])==x["source_artifact_sha256"] for x in tasks) and all(sha(root/x["path"])==x["sha256"] for x in target_manifest))
 neg("no real authorization bundle: expert runtime refuses dispatch","EXPERT_AUTHORITY_NOT_PROVISIONED",lambda:ExpertResponseGate(root,packet,sha(packet/"ExpertPacketR1Report.json")))
 s=load(root/SCHEMA);require(sha(root/SCHEMA)==er["response_schema_sha256"],"EXPERT_SCHEMA_HASH")
 # Test-only response based on actual task ID; reviewer identifiers explicitly
 # synthetic. Never saved as an expert answer, no authorization bundle generated.
 task=tasks[0];h="0"*64;dim={"value":None,"state":"UNRESOLVED","evidence_refs":[]}
 base={"task_ref":task["task_ref"],"review_id":task["review_id"],"source_legacy_ref":task["source_legacy_ref"],"reviewer_id":"SYNTHETIC_TEST_NOT_REVIEWER","reviewer_role":"SYNTHETIC_TEST_ONLY","qualification_evidence_ref":"SYNTHETIC_UNQUALIFIED","utc":"2026-11-27T00:00:00Z","evidence":[],"reviewer_minutes":0,"review_status":"EXPERT_DRAFT_PENDING_FREEZE","mapping_release_authorized":False,"scientific_reference_qualified":False}
 resp=dict(base,phase="INITIAL_SOURCE_FIRST",prior_candidate_exposure="UNKNOWN",source_reconstruction={k:copy.deepcopy(dim) for k in ("base_food","entity_grain","food_state","preparation","species_variety","edible_part","composition","regional_scope")},independent_candidates=[],unresolved_reasons=["TEST_ONLY"],initial_disposition="HOLD_INSUFFICIENT_EVIDENCE")
 pos("valid synthetic unresolved schema",lambda:validate_schema(resp,s))
 neg("source explicit null without evidence rejected","EXPERT_RESPONSE_SCHEMA",lambda:validate_schema({**resp,"source_reconstruction":{**resp["source_reconstruction"],"food_state":{"value":None,"state":"SOURCE_EXPLICIT","evidence_refs":[]}}},s))
 neg("unresolved non-null value rejected","EXPERT_RESPONSE_SCHEMA",lambda:validate_schema({**resp,"source_reconstruction":{**resp["source_reconstruction"],"food_state":{"value":"raw","state":"UNRESOLVED","evidence_refs":[]}}},s))
 neg("candidate disposition with empty candidate set rejected","EXPERT_RESPONSE_SCHEMA",lambda:validate_schema({**resp,"initial_disposition":"CANDIDATE_CONCEPT_ONLY"},s))
 overflow={**resp,"source_reconstruction":{**resp["source_reconstruction"],"food_state":{"value":"test","state":"EXPERT_INFERENCE","evidence_refs":[99]}}}
 pos("overflow structure alone is syntactically valid",lambda:validate_schema(overflow,s))
 neg("actual bound runtime rejects out of range evidence index","EVIDENCE_INDEX_OUT_OF_RANGE",lambda:validate_bound_content(overflow,task,{},target_manifest))
 vocab,vc=parse_standards(StandardInput(root))
 # Real target ID/locator from pinned raw standards; not an actual scientific claim.
 k=next(k for k,v in vocab.items() if k[0]=="foodon:2026-09-20:food_product" and not v["deprecated"]);t=vocab[k]
 sample_c={"target_system":"FoodOn","target_version":"2026-09-20","target_native_id":k[1],"target_label":t["label"],"target_locator":t["locator"],"relation":"CONDITIONAL","direction":"SOURCE_RELATION_TO_TARGET","conditions":["TEST_ONLY_NOT_EXPERT_JUDGMENT"],"evidence_refs":[0],"task_applicability":"CONDITIONAL_CONCEPT_ONLY","measurement_transfer":"HOLD"}
 evidence={"source_sha256":target_manifest[0]["sha256"],"source_locator":t["locator"],"quotation_or_observation":"TEST_ONLY","evidence_role":"TARGET_EXPLICIT"}
 tr={**resp,"evidence":[evidence],"independent_candidates":[sample_c],"initial_disposition":"CONDITIONAL_OR_AMBIGUOUS"}
 pos("synthetic structure with real target ID and locator checked",lambda:validate_schema(tr,s) is None and validate_bound_content(tr,task,vocab,target_manifest) is None)
 neg("conditional relation without conditions rejected","EXPERT_RESPONSE_SCHEMA",lambda:validate_schema({**tr,"independent_candidates":[{**sample_c,"conditions":[]}]},s))
 neg("actual target ID mutation rejected","EXPERT_TARGET_ID_UNVERIFIED",lambda:validate_bound_content({**tr,"independent_candidates":[{**sample_c,"target_native_id":"FOODON_FAKE"}]},task,vocab,target_manifest))
 neg("actual target locator mutation rejected","EXPERT_TARGET_LABEL_LOCATOR",lambda:validate_bound_content({**tr,"independent_candidates":[{**sample_c,"target_locator":"wrong"}]},task,vocab,target_manifest))
 neg("wrong target release rejected","EXPERT_TARGET_VERSION",lambda:validate_bound_content({**tr,"independent_candidates":[{**sample_c,"target_version":"2027"}]},task,vocab,target_manifest))
 postresp=dict(base,phase="POST_INITIAL_COMPARISON",initial_frozen_sha256=h,comparison_packet_sha256=h,explicit_unblind_authorization_ref="TEST_ONLY",edge_judgments=[{"comparison_evidence_key":"TEST","verdict":"CONDITIONAL_RELATION","relation":"CONDITIONAL","direction":"SOURCE_RELATION_TO_TARGET","conditions":[],"rationale":"TEST","evidence_refs":[0]}],evidence=[evidence],remaining_uncertainties=[],changed_initial_judgment=False,change_reason=None)
 neg("post conditional with empty conditions rejected","EXPERT_RESPONSE_SCHEMA",lambda:validate_schema(postresp,s))
 postresp["edge_judgments"][0]["conditions"]=["TEST_ONLY"]
 neg("unchanged initial with spurious change reason rejected","EXPERT_RESPONSE_SCHEMA",lambda:validate_schema({**postresp,"change_reason":"TEST"},s))
 pos("old input fences and run output unchanged",lambda:all(sha(run/k)==v for k,v in before.items()))
 # Include original provenance inputs loaded for reproductions; validation fence recheck.
 a.check_fences()
 out.mkdir(parents=True);report={"status":"PASS_R1_RUNTIME_REPLAY_AND_AUDIT_REGRESSIONS / SCIENTIFIC_AND_EXPERT_DISPATCH_HOLD" if all(x["pass"] for x in tests) else "FAIL_R1_VALIDATION","typed_objects_replayed":len(gate._records),"risk_records":len(risk_objects),"queries":len(a.queries),"tests_total":len(tests),"tests_passed":sum(x["pass"] for x in tests),"tests":tests,"gate_requests":[{"purpose":k[0],"decision":k[1],"count":n} for k,n in sorted(requests.items())],"old_scope_and_risk_bypass_tests_reproduced":sum(x["pass"] for x in tests if x["test"].startswith("old actual scope") or x["test"].startswith("old real RED")),"expert_tasks_prepared":len(tasks),"expert_authority_provisioned":False,"expert_actual_reviews":0,"mapping_release_count":0,"limitations":["whole-label rule deliberately conservative; no U3-B candidate admitted in frozen 284, not scientific accuracy","no full OWL reasoning or new embedding retrieval","expert structural/content tests are synthetic with actual source identity, no real authority/qualification or actual response","same-account directory isolation is not proof of access control","prior C2 validator vulnerabilities reproduced; new verified application entry must be used by future consumers"]}
 put(out/"R1ValidationReport.json",report)
 print(json.dumps({k:v for k,v in report.items() if k!="tests"},ensure_ascii=False),flush=True)
 for t in tests:
  if not t["pass"]:print("FAIL",t,flush=True)
 require(report["tests_total"]==report["tests_passed"],"R1_TEST_FAILURE")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=P.Path,default=P.Path("."));p.add_argument("--profile",type=P.Path,required=True);p.add_argument("--profile-sha",required=True);p.add_argument("--run",type=P.Path,required=True);p.add_argument("--receipt-sha",required=True);p.add_argument("--packet",type=P.Path,required=True);p.add_argument("--out",type=P.Path,required=True)
 x=p.parse_args();run(x.root,x.profile.resolve(),x.profile_sha,x.run.resolve(),x.receipt_sha,x.packet.resolve(),x.out)
