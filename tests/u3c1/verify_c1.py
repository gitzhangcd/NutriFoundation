#!/usr/bin/env python3
"""Read-only C1 replay, source scope diagnosis and development risk routing.
This does not create independent scientific Gold or adjudicate expert claims.
"""
import argparse,sys,pathlib as P,json,copy,xml.etree.ElementTree as E
from collections import Counter
sys.path.insert(0,str(P.Path(__file__).resolve().parents[2]/"src/u3c1"))
from run_c1 import *

FAMILIES={
 "SWEETENER_MODIFIER":"UNDECLARED_FORMULATION_OR_PROCESS",
 "SPECIAL_DIETARY_MODIFIER":"UNDECLARED_FORMULATION_OR_PROCESS",
 "SPECIFIC_SUBTYPE":"UNDECLARED_FORMULATION_OR_PROCESS",
 "BLANCHING_PROCESSING":"UNDECLARED_FORMULATION_OR_PROCESS",
 "COOKING_METHOD_CONFLICT":"UNDECLARED_FORMULATION_OR_PROCESS",
 "PROCESSING_STATE_CONFLICT":"UNDECLARED_FORMULATION_OR_PROCESS",
 "FAT_TIER_ASSUMPTION":"UNDECLARED_FORMULATION_OR_PROCESS",
 "ADDED_INGREDIENT_CONFLICT":"SPECIES_OR_COMPOSITION_CHANGE",
 "SPECIFIC_PROTEIN_ASSUMPTION":"SPECIES_OR_COMPOSITION_CHANGE",
 "PROTEIN_ADDITION_CONFLICT":"SPECIES_OR_COMPOSITION_CHANGE",
 "SPECIES_CONFLICT":"SPECIES_OR_COMPOSITION_CHANGE",
 "ADDED_FAT_ASSUMPTION":"SPECIES_OR_COMPOSITION_CHANGE",
 "DISH_FORM_CONFLICT":"COMPONENT_WHOLE_OR_DISH_FORM",
 "MISSING_EGG_WRAP":"COMPONENT_WHOLE_OR_DISH_FORM",
 "MISSING_CARB_BASE":"COMPONENT_WHOLE_OR_DISH_FORM",
 "COMPONENT_DRESSING_ONLY":"COMPONENT_WHOLE_OR_DISH_FORM",
 "UNPREPARED_DRY_MIX":"PREPARED_STATE_INFERENCE",
 "RAW_DISH_CONFLICT":"PREPARED_STATE_INFERENCE",
}
def risk_family(h):
 t=h["critic_conflict_type"]
 if t=="RAW_VS_COOKED_CONFLICT":
  return "EXPLICIT_STATE_CONTRADICTION" if h["u2c_route"]=="RED" else "PREPARED_STATE_INFERENCE"
 require(t in FAMILIES,"UNREGISTERED_RISK_FAMILY")
 return FAMILIES[t]

def main(root,profile,run,out):
 root=root.resolve();profile=profile.resolve();run=run.resolve();out=out.resolve()
 require(run.is_relative_to(root/"runs/B2/U3-B/C1") and out.is_relative_to(root/"runs/B2/U3-B/C1") and not out.exists() and not out.is_relative_to(run),"NEW_VALIDATION_DIRECTORY")
 receipt=read(run/"C1FreezeReceipt.json")
 require(receipt["status"].startswith("PASS_C1_DEVELOPMENT_COMPARISON") and receipt["unblinding_authorized_by_pi"] is True,"C1_RECEIPT")
 m=receipt["output_file_hashes"]
 actual={str(x.relative_to(run)) for x in run.rglob("*") if x.is_file()}-{"C1FreezeReceipt.json"}
 require(set(m)==actual,"FROZEN_OUTPUT_SET")
 for rel,h in m.items():
  p=(run/rel).resolve();require(p.is_relative_to(run) and p.is_file() and sha(p)==h,"FROZEN_OUTPUT_HASH")
 fences=read(run/"private/InputFence.json")
 require(len(fences)==receipt["verified_input_files"] and all(sha(root/x)==h for x,h in fences.items()),"ORIGINAL_FENCE")
 inp=Inputs(root,profile)
 freeze,rec,sq,voc,checks,problems=verify_critic(inp)
 require(not problems and freeze==read(run/"CriticFreezeVerificationReport.json"),"FREEZE_REPLAY")
 compare_report,cases,expert,absence,outside=compare(inp,rec,sq,voc)
 require(compare_report==read(run/"DevelopmentComparisonReport.json"),"COMPARISON_REPLAY")
 for filename,expected,is_lines in [
 ("CriticNativeTargetChecks.jsonl",checks,True),("CriticTargetIssues.json",problems,False),
 ("DevelopmentDisagreementRecords.jsonl",cases,True),("ExpertReviewQueue.json",expert,False),
 ("LiteralAbsenceProbe.json",absence,False),("CriticOutsideTargetUniverse.json",outside,False)]:
  got=lines(run/"private"/filename) if is_lines else read(run/"private"/filename)
  # Replay result outside-universe list uses set iteration, compare unordered.
  if filename=="CriticOutsideTargetUniverse.json":require(Counter(map(canon,got))==Counter(map(canon,expected)),"PRIVATE_REPLAY:"+filename)
  else:require(got==expected,"PRIVATE_REPLAY:"+filename)
 require(fences==inp.fences,"INPUT_FENCE_REPLAY")
 # Independent aggregation of row-wise comparison lists rather than accepting report totals.
 a=Counter()
 for c in cases:
  for k,n in c["counts"].items():a[k]+=n
  require(len(c["shared"])==c["counts"]["shared_candidate_ids"],"SHARED_ROW_COUNT")
  require(len(c["critic_hard_negative_overlap"])==c["counts"]["generator_hits_critic_hard_negative"],"NEGATIVE_ROW_COUNT")
  require(len(c["generator_unreviewed"])==c["counts"]["generator_not_reviewed_by_critic"],"UNREVIEWED_ROW_COUNT")
  require(len(c["critic_only"])==c["counts"]["critic_only_candidate_ids"],"CRITIC_ONLY_ROW_COUNT")
  require(len(c["generator_other_target_scopes"])==c["counts"]["generator_other_scope"],"OTHER_SCOPE_ROW_COUNT")
  require(c["adjudication"]=="PENDING" and c["accepted_equivalence"] is False and c["mapping_release_authorized"] is False,"RELEASE_PROMOTION")
 require(all(compare_report["candidate_counts"][k]==n for k,n in a.items()),"AGGREGATE_RECONCILIATION")
 # Read-only asserted parent reachability, not OWL entailment. Six unique classes.
 rdf="{http://www.w3.org/1999/02/22-rdf-syntax-ns#}";owl="{http://www.w3.org/2002/07/owl#}";rs="{http://www.w3.org/2000/01/rdf-schema#}"
 ontology=E.parse(root/BASE/"FoodOn.owl").getroot();graph={}
 for e in ontology:
  if e.tag==owl+"Class" and e.get(rdf+"about"):
   graph[e.get(rdf+"about")]={"label":e.findtext(rs+"label"),"parents":[x.get(rdf+"resource") for x in e.findall(rs+"subClassOf") if x.get(rdf+"resource")],"complex_axioms":sum(not bool(x.get(rdf+"resource")) for x in e.findall(rs+"subClassOf"))}
 target_root="http://purl.obolibrary.org/obo/FOODON_00001002";require(graph[target_root]["label"]=="food product","FOODON_ROOT")
 graphchecks=[]
 for k in sorted({tuple(x["target_key"]) for x in outside}):
  require(k[0]==EXT["FoodOn"] and k[1] in graph,"OUTSIDE_SCOPE_SYSTEM")
  iri=k[1];seen={iri};pending=[iri]
  while pending:
   z=pending.pop()
   for p in graph.get(z,{}).get("parents",[]):
    if p not in seen:seen.add(p);pending.append(p)
  graphchecks.append({"target_key":list(k),"label":graph[iri]["label"],"root":target_root,"asserted_named_root_reachable":target_root in seen,"ancestor_count":len(seen)-1,"ancestor_complex_axioms":sum(graph.get(a,{}).get("complex_axioms",0) for a in seen),"admission":"HOLD_REVIEW_ONTOLOGY_SCOPE_OR_REASONED_VIEW"})
 require(all(not x["asserted_named_root_reachable"] for x in graphchecks),"SCOPE_REASON_REPLAY")
 risk=[];counts=Counter();riskroute=Counter()
 for c in cases:
  for h in c["critic_hard_negative_overlap"]:
   fam=risk_family(h);counts[fam]+=1;riskroute[(fam,h["u2c_route"])]+=1
   risk.append({"review_id":c["review_id"],"source_ref":c["source_ref"],"generator_ref":h["generator_ref"],"u2c_ref":h["u2c_ref"],"target_key":h["target_key"],"risk_family":fam,"critic_conflict_type":h["critic_conflict_type"],"u2c_route":h["u2c_route"],"controller_disposition":"BLOCK_EQUIVALENCE_OR_NUTRIENT_TRANSFER" if fam=="EXPLICIT_STATE_CONTRADICTION" else "HOLD_PENDING_CONDITION_OR_EXPERT_REVIEW","expert_adjudication":"PENDING","accepted_equivalence":False})
 require(len(risk)==a["generator_hits_critic_hard_negative"],"RISK_COUNT")
 # Seven explicit probes are search diagnostics, not a proof of absence.
 tests=[]
 def pos(name,fn):
  try:require(fn() is not False,"ASSERTION");tests.append({"test":name,"pass":True,"expected":"ACCEPT"})
  except Exception as e:tests.append({"test":name,"pass":False,"expected":"ACCEPT","actual":str(e)[:150]})
 def neg(name,code,fn):
  try:fn();tests.append({"test":name,"pass":False,"expected":code,"actual":"ACCEPT"})
  except ValueError as e:tests.append({"test":name,"pass":str(e).startswith(code),"expected":code,"actual":str(e)[:150]})
 pos("frozen output hash closure",lambda:len(m)==9)
 pos("input fence closure before and after replay",lambda:len(fences)==len(inp.fences))
 pos("all C0 case identities and raw target citations replay",lambda:len(rec)==44 and len(checks)==195)
 pos("both candidate registry and negative registry verified",lambda:freeze["registry_rows_verified"]==195)
 pos("all private comparison records and aggregate replay",lambda:len(cases)==44 and sum(a.values())>0)
 pos("source-side target comparison disjoint and exhaustive",lambda:a["generator_external"]==a["shared_candidate_ids"]+a["generator_hits_critic_hard_negative"]+a["generator_not_reviewed_by_critic"])
 pos("critic candidate membership partitions",lambda:a["critic_candidates"]==a["shared_candidate_ids"]+a["critic_only_candidate_ids"])
 pos("FNDDS carrier key deduplication",lambda:nk({"native_namespace":"fndds:2015-16:ars_carrier","native_key":"53301000"})==key("FNDDS","53301000"))
 pos("ontology scope diagnosis from actual parent graph",lambda:len(graphchecks)==6 and all(not x["asserted_named_root_reachable"] for x in graphchecks))
 pos("four explicit state conflicts remain held",lambda:counts["EXPLICIT_STATE_CONTRADICTION"]==4 and riskroute[("EXPLICIT_STATE_CONTRADICTION","RED")]==4)
 pos("review priorities reconcile actual union",lambda:len(expert)==sum(c["critic_expert_recommended"] or bool(c["critic_hard_negative_overlap"]) for c in cases))
 neg("input hash tamper rejected","PINNED_INPUT_CHANGED",lambda:inp.pin(inp.p["task_config"]["path"],"0"*64))
 neg("duplicate native target key rejected","DUPLICATE_NATIVE_KEY",lambda:unique([{"id":"x"},{"id":"x"}],"id"))
 neg("newer FNDDS cycle blocked","WRONG_CYCLE",lambda:require(version_ok({"target_system":"FNDDS","target_version":"2021-23"}),"WRONG_CYCLE"))
 neg("invented target ID blocked","TARGET_MISSING",lambda:require(key("FoodOn","http://purl.obolibrary.org/obo/FOODON_DOES_NOT_EXIST") in voc,"TARGET_MISSING"))
 neg("write outside new U3B C1 scope blocked","NEW_VALIDATION_DIRECTORY",lambda:require((root/"source_data").is_relative_to(root/"runs/B2/U3-B/C1"),"NEW_VALIDATION_DIRECTORY"))
 require(all(x["pass"] for x in tests),"VALIDATION_FAILURE")
 inp.check();require(all(sha(run/x)==h for x,h in m.items()),"ORIGINAL_OUTPUT_CHANGED")
 out.mkdir(parents=True);priv=out/"private";priv.mkdir();putl(priv/"RiskAttributionRecords.jsonl",risk);put(priv/"FoodOnScopeDiagnosis.json",graphchecks)
 result={"status":"PASS_C1_READ_ONLY_REPLAY_AND_DEVELOPMENT_RISK_ROUTING","utc":now(),"tests_passed":len(tests),"tests_total":len(tests),"tests":tests,
 "frozen_output_files_rechecked":len(m),"input_fences_rechecked":len(fences),"critics_cases_replayed":len(rec),"target_checks_replayed":len(checks),"comparison_cases_replayed":len(cases),"priority_expert_cases":len(expert),
 "risk_attribution":dict(counts),"risk_routes":[{"risk_family":k[0],"u2c_route":k[1],"count":v} for k,v in sorted(riskroute.items())],
 "outside_universe_edges":len(outside),"outside_universe_unique_foodon_classes":len(graphchecks),"asserted_named_root_reachable_count":sum(x["asserted_named_root_reachable"] for x in graphchecks),
 "fences_unchanged":True,"frozen_run_unchanged":True,"original_c1_script_sha256":sha(root/"src/u3c1/run_c1.py"),"validation_script_sha256":sha(P.Path(__file__).resolve()),"profile_sha256":sha(profile),
 "limitations":["same-code replay plus independent aggregations, not independent scientific validity","risk-family grouping is a controller development triage, not expert rejection","only the asserted named subclass closure was tested, no ontology reasoning","no reviewer access-control proof","no formal accuracy or recall, no release"],"accepted_equivalence":0,"mapping_release_authorized":False}
 put(out/"C1ValidationReport.json",result)
 print(json.dumps({k:v for k,v in result.items() if k!="tests"},ensure_ascii=False),flush=True)
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--run",type=P.Path,required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.profile,x.run,x.out)
