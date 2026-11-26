#!/usr/bin/env python3
"""P1 read-only full replay, denominator reconciliation and exact-carrier regressions."""
import sys,pathlib as P,argparse,copy,math
from collections import Counter
sys.path.insert(0,str(P.Path(__file__).resolve().parents[2]/"src/u3r2p1"))
from run_p1 import *
def main(root,profile,ph,generator,run,freeze_sha,out):
 root=root.resolve();profile=profile.resolve();generator=generator.resolve();run=run.resolve();out=out.resolve()
 require(not out.exists() and out.is_relative_to(root/BASE/"P1") and not out.is_relative_to(run),"NEW_VALIDATION_DIRECTORY")
 rf=run/"P1FreezeReceipt.json";require(sha(rf)==freeze_sha,"P1_FREEZE_HASH");receipt=read(rf)
 m=receipt["output_file_hashes"];require(set(m)=={str(x.relative_to(run)) for x in run.rglob("*") if x.is_file()}-{"P1FreezeReceipt.json"} and all(sha(run/k)==h for k,h in m.items()),"OUTPUT_CLOSURE")
 f,p,q,r,vocab,auth,val,ver,add,checks=verify_inputs(root,profile,ph,generator)
 report,cases,gaps,old=derive_comparison(f,root,generator,q,r)
 require(canon(ver)==canon(read(run/"P1ReferenceVerificationReport.json")) and canon(report)==canon(read(run/"P1ComparisonReport.json")),"REPORT_REPLAY")
 for name,rows in [("CarrierLocatorAddenda.jsonl",add),("NativeTargetChecks.jsonl",checks),("ReferenceComparisonRecords.jsonl",cases),("ReferenceGapAttribution.jsonl",gaps),("OldRiskNegativeOverlap.jsonl",old)]:
  require(canon(list(lines(run/"private"/name)))==canon(rows),"ROW_REPLAY:"+name)
 require(f.hashes==read(run/"private/InputFence.json") and len(f.hashes)==receipt["input_fence_count"],"INPUT_FENCE_REPLAY")
 tests=[]
 def test(n,fn):
  try:require(fn() is not False,"ASSERTION");tests.append({"test":n,"pass":True})
  except Exception as e:tests.append({"test":n,"pass":False,"observed":str(e)[:180]})
 def deny(n,fn,code):
  def wrapped():
   try:fn();return False
   except ValueError as e:return str(e).startswith(code)
  test(n,wrapped)
 test("all 7 allowed inputs and 3 critic outputs byte matched",lambda:ver["allowed_inputs_verified"]==7 and ver["frozen_outputs_verified"]==3)
 test("44 actual unique case records and 243 raw target references",lambda:len(q)==len(r)==44 and len(checks)==243 and all(x["native_identity_verified"] and x["original_cited_locator_verified"] for x in checks))
 test("original strict locator deviation retained",lambda:ver["original_strict_cases_passed"]==1 and ver["original_strict_cases_failed"]==43 and len(add)==83)
 test("83 controller addenda never attribute ARS citation to reviewer",lambda:all(not x["reviewer_ars_citation_claimed"] and not x["semantic_judgment_changed"] and x["controller_verified_ars_sha256"]==auth[ARS] for x in add))
 test("FNDDS same-cycle raw counts",lambda:ver["raw_standard_counts"]["FNDDS_food_codes"]==ver["raw_standard_counts"]["FNDDS_ARS_same_cycle_records"]==8690)
 test("111 supported source-target proposals not equal to gold",lambda:len(gaps)==111 and all(not x["reference_is_expert_gold"] and not x["mapping_release"] for x in gaps))
 test("19 current and 25 old-only not merged",lambda:sum(x["current_model_query"] for x in cases)==19 and sum(not x["current_model_query"] for x in cases)==25 and all(not x["arms"] for x in cases if not x["current_model_query"]))
 g=[x for x in gaps if x["group"]=="CURRENT_19"];z=Counter(x["membership"] for x in g)
 test("current 46 references exhaustive 4+39+3 partition",lambda:len(g)==46 and z=={"IN_RETRIEVED_POOL":4,"IN_UNIVERSE_NOT_IN_RETRIEVED_POOL":39,"OUTSIDE_FROZEN_UNIVERSES":3})
 test("four retrieved references were held by R1, all R2 question-only",lambda:sum(x["membership"]=="IN_RETRIEVED_POOL" and x["r1_review_eligible"] is False and x["r2_proposal_route"]=="QUESTION_ONLY" for x in g)==4)
 test("old-only 223 targets partition 28+27+168",lambda:any(x["group"]=="OLD_ONLY_25" and x.get("old_unique_external_targets")==223 and x.get("old_supported_target_overlap")==28 and x.get("old_negative_target_overlap")==27 and x.get("old_unjudged_targets")==168 for x in report["group_counts"]))
 test("all primary arms use fixed 18 in-universe query references",lambda:all(x["query_has_review_reference"]==18 for x in report["primary_preplanned"]["arm_statistics"] if x["domain"]=="original"))
 test("extension no positive reference denominator stays null",lambda:all(x["reference_hit_fraction"] is None for x in report["primary_preplanned"]["arm_statistics"] if x["domain"]=="extension"))
 test("top-k results monotone within arms and same denominator",lambda:all(all(a<=b for a,b in zip(v,v[1:])) for v in [[x["queries_with_hit"] for x in report["combined_secondary"] if x["domain"]=="ALL_DOMAINS" and x["arm"]==arm] for arm in ARMS]))
 test("unreviewed candidate edges excluded from precision",lambda:report["primary_preplanned"]["precision"]=="NOT_ESTIMABLE_FROM_SOURCE_ONLY_REVIEW" and report["scientific_precision_recall"]=="NOT_ESTIMABLE")
 test("reserved32 not compared",lambda:receipt["reserved32_outcomes_read"]==0 and len(cases)==44 and all(x["batch"]=="ORIGINAL_NEW44" for x in cases))
 # Actual-reference mutations in memory; no frozen byte changes.
 rid=next(i for i,x in r.items() if any(c["target_key"][0]=="FNDDS" for c in x["independent_candidates"]))
 base=r[rid];i=next(i for i,c in enumerate(base["independent_candidates"]) if c["target_key"][0]=="FNDDS")
 def mut(fn):
  x=copy.deepcopy(base);fn(x,x["independent_candidates"][i]);return resolve_reference(x,q[rid],val,vocab,auth)
 deny("wrong CSV row not repairable",lambda:mut(lambda x,c:c.update(target_locator=c["target_locator"]+"0")),"FNDDS_NOT_EXACT_CSV_LOCATOR")
 deny("wrong cycle not repairable",lambda:mut(lambda x,c:c["target_key"].__setitem__(1,"2021-23")),"REFERENCE_TARGET_ID_VERSION")
 deny("wrong native label not repairable",lambda:mut(lambda x,c:c.update(target_native_label="SYNTHETIC_WRONG_LABEL")),"REFERENCE_TARGET_LABEL")
 deny("fabricated ID not repairable",lambda:mut(lambda x,c:c["target_key"].__setitem__(2,"00000000")),"REFERENCE_TARGET_ID_VERSION")
 deny("missing actual CSV evidence not repairable",lambda:mut(lambda x,c:c.update(evidence_refs=[])),"FNDDS_CSV_EVIDENCE_NOT_EXACT")
 deny("evidence index out of range rejected",lambda:mut(lambda x,c:c.update(evidence_refs=[len(x["evidence"])])),"EVIDENCE_INDEX")
 deny("forged scientific qualification rejected",lambda:mut(lambda x,c:x.update(scientific_reference_qualified=True)),"REFERENCE_SCHEMA")
 f.check();test("127 pinned inputs and 8 frozen outputs unchanged",lambda:len(f.hashes)==127 and len(m)==8 and all(sha(run/k)==h for k,h in m.items()))
 require(all(x["pass"] for x in tests),"P1_TEST_FAILURE:"+str([x for x in tests if not x["pass"]]))
 out.mkdir(parents=True)
 result={"status":"PASS_P1_READ_ONLY_REPLAY_AND_LOCATOR_REGRESSIONS / SCIENTIFIC_QUALIFICATION_HOLD","tests_total":len(tests),"tests_passed":sum(x["pass"] for x in tests),"tests":tests,"review_records_replayed":len(r),"native_target_references_replayed":len(checks),"carrier_addenda_replayed":len(add),"case_comparisons_replayed":len(cases),"gap_attributions_replayed":len(gaps),"input_fences_unchanged":len(f.hashes),"frozen_output_files_rechecked":len(m),"reserved32_outcomes_read":0,"expert_gold_count":0,"mapping_release_count":0,"limitations":["same-code replay plus independent arithmetic checks; no independent semantic Gold","carrier resolution is controller provenance, not original strict format acceptance","explicit unblind authorization required; prior exposure and access declaration retained"]}
 put(out/"P1ValidationReport.json",result);print(json.dumps({k:v for k,v in result.items() if k!="tests"},ensure_ascii=False))
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--profile-sha",required=True);a.add_argument("--generator",type=P.Path,required=True);a.add_argument("--run",type=P.Path,required=True);a.add_argument("--freeze-sha",required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.profile,x.profile_sha,x.generator,x.run,x.freeze_sha,x.out)
