#!/usr/bin/env python3
"""Read-only R2 replay. Synthetic review/evaluation tests are not expert answers."""
import sys,pathlib as P,json,argparse,copy
from collections import Counter
sys.path.insert(0,str(P.Path(__file__).resolve().parents[2]/"src/u3r2"))
from run_r2 import *
from compare_reference import compare_case,aggregate,validate_reference,Standards,parse_standards
from expert_schema_v3 import build
from jsonschema import Draft202012Validator,FormatChecker
def main(root,profile,ph,run,freeze_sha,out):
 root=root.resolve();run=run.resolve();out=out.resolve()
 require(not out.exists() and out.is_relative_to(root/C2/"R2") and not out.is_relative_to(run),"NEW_VALIDATION_DIR")
 receipt=run/"R2GeneratorFreezeReceipt.json";require(sha(receipt)==freeze_sha,"FREEZE_HASH");f=read(receipt)
 require(f["profile_sha256"]==ph and f["mapping_release_authorized"] is False and all(sha(run/k)==v for k,v in f["files"].items()),"RUN_FROZEN_OUTPUTS")
 a=Inputs(root,profile,ph);z=a.main();priv=run/"controller_private"
 require(read(priv/"InputFence.json")==a.fences,"REPLAY_FENCE")
 require(read(run/"reviewer_source_only/R2Review44.json")==z["first"] and read(run/"reserved_source_only/R2Calibration32.json")==z["second"],"SOURCE_PACKET_REPLAY")
 require(canon(read(priv/"ControllerComparisonIndex.json"))==canon(z["comparators"]),"COMPARATOR_REPLAY")
 require(canon(read(priv/"FrozenTargetUniverse.json"))==canon({"original":z["universe"],"extension":z["extension_universe"]}),"TARGET_UNIVERSE_REPLAY")
 require(list(lines(priv/"RankedArms.jsonl"))==z["arms"],"ARM_EXACT_REPLAY")
 expected={x["proposal_id"]:x for x in z["risks"]};seen=set()
 schema=read(root/"schemas/udf/u3r2/R2CandidateQuestion_v0.1.schema.json");Draft202012Validator.check_schema(schema);v=Draft202012Validator(schema)
 for domain,x in read(priv/"ProposalManifest.json").items():
  p=(run/x["file"]).resolve();require(p.is_relative_to(priv.resolve()) and sha(p)==x["sha256"],"PROPOSAL_FILE_HASH")
  n=0
  for r in lines(p):
   k=r["proposal_id"];require(k not in seen and k in expected and r==expected[k] and v.is_valid(r),"QUESTION_REPLAY")
   d=r["rights_domains"];require(domain==(d[0] if len(d)==1 else "MIXED_RESTRICTED_"+dg(d)[:16]),"RIGHTS_PARTITION")
   w=dict(r);h=w.pop("content_sha256");require(dg(w)==h,"QUESTION_CONTENT_HASH")
   seen.add(k);n+=1
  require(n==x["rows"],"PROPOSAL_ROWS")
 require(seen==set(expected),"QUESTION_CLOSURE")
 tests=[]
 def pos(n,fn):
  try:require(fn() is not False,"ASSERTION");tests.append({"test":n,"pass":True,"observed":"ACCEPT"})
  except Exception as e:tests.append({"test":n,"pass":False,"observed":str(e)[:150]})
 def neg(n,fn):pos(n,lambda:not fn())
 pos("R1-A2 32 pinned inputs 3 frozen outputs",lambda:a.audit["allowed_inputs"]==32 and a.audit["output_files"]==3)
 pos("34766 question rows exact source rederive and strict schema",lambda:len(seen)==34766)
 pos("4544 frozen arm lists exact replay",lambda:len(z["arms"])==4544)
 pos("44 and reserved 32 source-only projections distinct",lambda:len({x["source_ref"] for x in z["first"]+z["second"]})==76)
 pos("new cohort 44 includes 19 current and 25 old-only",lambda:sum(x["current_model_query"] for x in z["comparators"] if x["batch"]=="ORIGINAL_NEW44")==19)
 pos("stratified 32 sample all current, four 8-case strata",lambda:len(z["sample"])==4 and all(x["selected_count"]==8 for x in z["sample"]) and sum(x["current_model_query"] for x in z["comparators"] if x["batch"]=="RESERVED_STRATIFIED32")==32)
 forbidden={"candidate_refs","target_ref","ranked_targets","review_route","prior_candidate_ref","source_cohort","r1_disposition","stratum"}
 pos("no generator decisions or strata in reviewer packets",lambda:all(not forbidden&set(x) for x in z["first"]+z["second"]))
 pos("typed questions never contain prior RED or explicit conflicts",lambda:all(expected[k]["proposal_route"]=="QUESTION_ONLY" and not expected[k]["explicit_conflicts"] and not expected[k]["prior_red"] for row in z["arms"] if row["arm"]=="TYPED_QUESTION" for k in row["ranked_proposal_ids"]))
 pos("all 284 R1 abstentions preserved",lambda:all(not x["r1_review_eligible"] and not x["development_concept_review_authorized"] for x in z["risks"]))
 pos("target universes independently preserved and disjoint",lambda:len(z["universe"])==28845 and len(z["extension_universe"])==1174 and not set(map(tuple,z["universe"]))&set(map(tuple,z["extension_universe"])))
 for x,y in [("apple (peeled)","apple (unpeeled)"),("苹果(去皮)","苹果(带皮)")]:
  pos("peeled regression "+x,lambda x=x,y=y:peel_conflict(x,y))
 pos("no current peel assertion from source history",lambda:peel("apple made from peeled apples")=="UNKNOWN")
 pos("negated peel does not trigger peeled",lambda:peel("苹果未去皮")=="UNPEELED" and peel("apple not peeled")=="UNPEELED")
 for x,y in [("米饭","cooked rice"),("炒饭","fried rice")]:
  pos("implicit alias conditional review signal "+x,lambda x=x,y=y:complete_alias(x,y,a.aliases)=="AUTHORED_ALIAS_IMPLICIT_COOKING_REQUIRES_REVIEW")
 r=next(x for x in z["risks"] if x["proposal_route"]=="QUESTION_ONLY")
 neg("candidate cannot become accepted equivalence",lambda:v.is_valid({**r,"accepted_equivalence":True}))
 neg("candidate cannot become scientific review authorized",lambda:v.is_valid({**r,"development_concept_review_authorized":True}))
 neg("question route rejects explicit conflict",lambda:v.is_valid({**r,"explicit_conflicts":["TEST"]}))
 neg("candidate cannot become formal release",lambda:v.is_valid({**r,"mapping_release":"ALLOW"}))
 # Reference response schemas: test-only known source identity and actual standard
 # IDs. No synthetic reference or review is persisted or used for metrics.
 rs=read(root/"schemas/udf/u3r2/R2ReferenceReview_v0.1.schema.json");Draft202012Validator.check_schema(rs);rv=Draft202012Validator(rs,format_checker=FormatChecker())
 task=z["first"][0];d={"value":None,"state":"UNRESOLVED","evidence_refs":[]}
 rr={**{k:task[k] for k in ("review_id","source_ref","source_scope","source_native_label","native_kind")},
  "source_dimensions":{k:copy.deepcopy(d) for k in ("base_food","entity_grain","food_state","preparation","species_variety","edible_part","composition","regional_scope")},"evidence":[],"independent_candidates":[],"hard_negatives":[],
  "search_attempts":[{"target_system":x,"query_terms":[],"search_method":"SYNTHETIC_TEST_ONLY","result":"INSUFFICIENT_SOURCE"} for x in ("FoodOn","FDC_SR_Legacy","FNDDS")],
  "case_disposition":"HOLD_INSUFFICIENT_EVIDENCE","local_concept_extension":"NOT_PROPOSED","unresolved_reasons":["SYNTHETIC_TEST_ONLY"],"reviewer_minutes":0,"review_status":"CRITIC_DRAFT","accepted_equivalence":False,"mapping_release_authorized":False,"scientific_reference_qualified":False,"purpose":"CURATION_DEV_ONLY"}
 pos("unresolved retained in reference contract",lambda:rv.is_valid(rr))
 neg("source explicit null cannot pass reference schema",lambda:rv.is_valid({**rr,"source_dimensions":{**rr["source_dimensions"],"food_state":{"value":None,"state":"SOURCE_EXPLICIT","evidence_refs":[]}}}))
 neg("reference cannot be expert gold",lambda:rv.is_valid({**rr,"scientific_reference_qualified":True}))
 # Select a real candidate target solely to verify native identity and evidence
 # parser. The synthetic relation below is not a scientific claim.
 authorities={x["path"]:x["sha256"] for x in read(root/"configs/udf/u3c2r/R1_Policy_v0.1.json")["expert_target_files"]}
 require(all(sha(root/p)==h for p,h in authorities.items()),"REFERENCE_STANDARD_HASH")
 vocab,vc=parse_standards(Standards(root));k=next(k for k,t in vocab.items() if k[0]=="foodon:2026-09-20:food_product" and not t["deprecated"]);t=vocab[k]
 target=["FoodOn","2026-09-20",k[1]];c={"target_key":target,"target_native_label":t["label"],"target_locator":t["locator"],"relation":"CONDITIONAL","direction":"SOURCE_RELATION_TO_TARGET","conditions":["TEST_ONLY"],"rationale":"SYNTHETIC_TEST_ONLY","evidence_refs":[0],"applicability":"CONDITIONAL_CONCEPT_CANDIDATE","measurement_transfer":"HOLD"}
 rr2={**rr,"case_disposition":"CONDITIONAL_OR_AMBIGUOUS","evidence":[{"artifact_sha256":authorities["runs/B2/U3-A/inputs/FoodOn.owl"],"locator":t["locator"],"observation":"TEST_ONLY","role":"TARGET_EXPLICIT"}],"independent_candidates":[c]}
 pos("synthetic response binds real native target id and locator",lambda:validate_reference(rr2,task,rv,vocab,authorities))
 neg("conditional candidate needs explicit conditions",lambda:rv.is_valid({**rr2,"independent_candidates":[{**c,"conditions":[]}]}))
 neg("HOLD cannot assert supported exact candidate",lambda:rv.is_valid({**rr,"evidence":rr2["evidence"],"independent_candidates":[{**c,"relation":"EXACT","applicability":"CONCEPT_CANDIDATE_ONLY"}]}))
 def rejects(response):
  try:validate_reference(response,task,rv,vocab,authorities);return False
  except ValueError:return True
 pos("reference evidence index out of range rejected",lambda:rejects({**rr2,"independent_candidates":[{**c,"evidence_refs":[99]}]}))
 pos("fake native target rejected",lambda:rejects({**rr2,"independent_candidates":[{**c,"target_key":["FoodOn","2026-09-20","FAKE_ID"]}]}))
 # Synthetic unit checks of evaluation denominator, not actual data results.
 cmp={"batch":"TEST","current_model_query":True,"old_u2c_candidates":[],"current_comparators":[{"target_scope":"foodon:2026-09-20:food_product","arm":"LABEL","ranked_targets":[target]}]}
 cm=compare_case(rr2,cmp,{tuple(target)},set(),[{"target_key":target}]);ag=aggregate([cm])
 pos("source-only reference hit not called scientific recall",lambda:ag["scientific_recall"]=="NOT_ESTIMABLE" and ag["precision"]=="NOT_ESTIMABLE_FROM_SOURCE_ONLY_REVIEW" and any(x["reference_hit"]==1 for x in ag["arm_statistics"]))
 cm2=compare_case(rr,cmp,{tuple(target)},set(),[{"target_key":target}]);ag2=aggregate([cm2])
 pos("zero reference denominator stays null",lambda:all(x["reference_hit_fraction"] is None for x in ag2["arm_statistics"]))
 # Expert draft v0.3 two contradictions. Do not provision or use authorization.
 old=read(root/"schemas/udf/u3c2r/ExpertAdjudicationResponse_v0.2.schema.json");new=read(root/"schemas/udf/u3r2/ExpertAdjudicationResponse_v0.3.schema.json");require(new==build(old),"EXPERT_SCHEMA_DRAFT_REPLAY")
 ev0=Draft202012Validator(old);ev1=Draft202012Validator(new)
 base={"task_ref":"test@"+("0"*64),"review_id":"TEST","source_legacy_ref":"test@"+("0"*64),"reviewer_id":"TEST_NOT_REVIEWER","reviewer_role":"TEST","qualification_evidence_ref":"TEST","utc":"2026-11-27T00:00:00Z","evidence":[{"source_sha256":"0"*64,"source_locator":"TEST","quotation_or_observation":"TEST","evidence_role":"TARGET_EXPLICIT"}],"reviewer_minutes":0,"review_status":"EXPERT_DRAFT_PENDING_FREEZE","mapping_release_authorized":False,"scientific_reference_qualified":False}
 ca={"target_system":"FoodOn","target_version":"2026-09-20","target_native_id":"TEST","target_label":"TEST","target_locator":"TEST","relation":"EXACT","direction":"SOURCE_RELATION_TO_TARGET","conditions":[],"evidence_refs":[0],"task_applicability":"CONCEPT_ONLY","measurement_transfer":"HOLD"}
 ini=dict(base,phase="INITIAL_SOURCE_FIRST",prior_candidate_exposure="UNKNOWN",source_reconstruction={k:copy.deepcopy(d) for k in rr["source_dimensions"]},independent_candidates=[ca],unresolved_reasons=["TEST"],initial_disposition="HOLD_INSUFFICIENT_EVIDENCE")
 post=dict(base,phase="POST_INITIAL_COMPARISON",initial_frozen_sha256="0"*64,comparison_packet_sha256="0"*64,explicit_unblind_authorization_ref="TEST",edge_judgments=[{"comparison_evidence_key":"TEST","verdict":"REJECT_AS_EQUIVALENCE","relation":"EXACT","direction":"SOURCE_RELATION_TO_TARGET","conditions":[],"rationale":"TEST","evidence_refs":[0]}],remaining_uncertainties=[],changed_initial_judgment=False,change_reason=None)
 pos("old expert schema accepts HOLD+EXACT, v0.3 rejects",lambda:ev0.is_valid(ini) and not ev1.is_valid(ini))
 pos("old expert schema accepts REJECT+EXACT, v0.3 rejects",lambda:ev0.is_valid(post) and not ev1.is_valid(post))
 pos("expert unresolved response remains structurally valid",lambda:ev1.is_valid({**ini,"independent_candidates":[]}))
 a.check();require(all(sha(run/k)==v for k,v in f["files"].items()),"RUN_MUTATION")
 out.mkdir(parents=True)
 report={"status":"PASS_R2_READ_ONLY_REPLAY_AND_DEVELOPMENT_CONTRACTS" if all(x["pass"] for x in tests) else "FAIL_R2_VALIDATION","tests_passed":sum(x["pass"] for x in tests),"tests_total":len(tests),"tests":tests,"candidate_questions_replayed":len(seen),"ranked_arm_groups_replayed":len(z["arms"]),"review_packets_replayed":76,"input_fences_unchanged":len(a.fences),"independent_reviews_completed":0,"mapping_release_count":0,"expert_schema_v0_3_activated":False,"phase_b_per_edge_binding":"HOLD_EA_P0","note":"Same-code deterministic rederive from frozen inputs plus schema and synthetic regression probes; not independent scientific review."}
 put(out/"R2ValidationReport.json",report);print(json.dumps({k:v for k,v in report.items() if k!="tests"},ensure_ascii=False))
 for x in tests:
  if not x["pass"]:print("FAIL",x)
 require(report["tests_total"]==report["tests_passed"],"R2_TEST_FAILURE")
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--profile-sha",required=True);a.add_argument("--run",type=P.Path,required=True);a.add_argument("--freeze-sha",required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.profile,x.profile_sha,x.run,x.freeze_sha,x.out)
