#!/usr/bin/env python3
"""C2 full deterministic replay and actual-purpose gate tests. No expert promotion."""
import argparse,sys,pathlib as P,copy,json
from collections import Counter,defaultdict
sys.path[:0]=[str(P.Path(__file__).resolve().parents[2]/"src/u3c2"),str(P.Path(__file__).resolve().parent)]
from run_c2 import *
from gate_c2 import DevelopmentGate,verify_decision,verify_query,expected_disposition
from risk import features,decide
def main(root,profile,run,out):
 root=root.resolve();profile=profile.resolve();run=run.resolve();out=out.resolve()
 require(run.is_relative_to(root/"runs/B2/U3-B/C2") and out.is_relative_to(root/"runs/B2/U3-B/C2") and not out.exists() and not out.is_relative_to(run),"NEW_VALIDATION_DIRECTORY")
 rpt=load(run/"C2ExecutionReport.json");priv=run/"private";tree=priv/"typed_partitions"
 require(rpt["status"].startswith("PASS_BOUNDED_C2") and sha(profile)==rpt["profile_sha256"],"C2_REPORT_IDENTITY")
 m=load(priv/"partition_manifest.json");require(sha(priv/"partition_manifest.json")==rpt["partition_manifest_sha256"] and set(m)=={str(f.relative_to(tree)) for f in tree.rglob("*.jsonl")},"C2_PARTITION_MANIFEST")
 fences=load(priv/"InputFence.json");require(len(fences)==rpt["input_fence_count"] and all(sha(root/k)==v for k,v in fences.items()),"C2_INPUT_FENCE")
 original_hashes={str(p.relative_to(run)):sha(p) for p in run.rglob("*") if p.is_file()}
 # Same pinned model and clock, complete replay without writing historical run.
 R=Runner(root,profile,out);R.clock=rpt["utc"]
 R.scope_run();R.load_u3();R.historical_risk();R.extension()
 qsum=R.query_decisions();esum=R.expert()
 require(qsum==rpt["cohort_results"] and esum==rpt["expert_packet"] and R.scope_stats==rpt["scope"],"SUMMARY_REPLAY")
 expected={ref(o):o for o in R.records};require(len(expected)==len(R.records)==rpt["typed_objects"],"EXPECTED_COUNT")
 actual={};by=defaultdict(list);groups=defaultdict(list);queries={}
 for rel,v in sorted(m.items()):
  f=tree/rel;require(sha(f)==v["sha256"] and f.stat().st_size==v["bytes"],"C2_PARTITION_HASH")
  rr=list(lines(f));require(len(rr)==v["rows"],"C2_PARTITION_COUNT")
  for o in rr:
   r=ref(o);require(r not in actual and r in expected and canon(o)==canon(expected[r]),"C2_EXACT_REPLAY")
   rights=o["governance"]["rights_domains"];part=rights[0] if len(rights)==1 else "MIXED_RESTRICTED_"+digest(rights)[:16]
   require(rel==part+"/"+o["kind"]+".jsonl","RIGHTS_PARTITION")
   validate(o,R.vs,R.registry);actual[r]=o;by[o["kind"]].append(o)
   p=o["payload"]
   if o["kind"]=="SemanticRiskAssessment":groups[(p["cohort"],p["source_legacy_ref"])].append(o)
   elif o["kind"]=="QueryAdmissionDecision":queries[(p["cohort"],p["source_legacy_ref"])]=o
 require(set(actual)==set(expected),"C2_OBJECT_CLOSURE")
 # Verify actual persisted candidate semantics from original admitted endpoints,
 # not from caller-supplied disposition. Replay prior RED flags from frozen inputs.
 old_red={}
 for c in R.cases:
  for x in c["shared"]+c["critic_hard_negative_overlap"]+c["generator_unreviewed"]+c["generator_other_target_scopes"]:old_red[x["generator_ref"]]=x["u2c_route"]=="RED"
 u3red={ref(o):o["payload"]["review_route"]=="RED" for o in R.u3rows["SemanticCandidateRecord"]}
 def inputs(o):
  p=o["payload"];a=R.registry[p["source_ref"]];t=R.registry[p["target_ref"]]
  ss=R.registry[p["scope_assessment_ref"]]["payload"]["scope_status"] if p["scope_assessment_ref"] else None
  if p["prior_candidate_ref"]:
   z=p["prior_candidate_ref"]
   if p["cohort"]=="U3A_EXPOSED_44":
    prior=R.registry[z]["payload"];require(prior["source_ref"]==p["source_legacy_ref"] and prior["target_ref"]==p["target_legacy_ref"],"PRIOR_EDGE_IDENTITY")
    red=old_red[z]
   else:
    prior=R.registry[z]["payload"];require(prior["source_legacy_ref"]==p["source_legacy_ref"] and prior["target_legacy_ref"]==p["target_legacy_ref"],"PRIOR_EDGE_IDENTITY")
    red=u3red[z]
  else:
   require(p["cohort"].startswith("C2_EXTENSION") and t["kind"]=="ScopeAssessment" and ss=="EXTENSION_TYPED_RETRIEVAL_ONLY","EXTENSION_TARGET")
   red=False
  return a,t,ss,red
 verified={}
 for o in by["SemanticRiskAssessment"]:
  p=o["payload"];a,t,ss,red=inputs(o);verify_decision(p,a,t,R.pol["risk"],ss,red);verified[ref(o)]=o
 for k,o in queries.items():verify_query(o["payload"],groups[k],R.pol["risk"]["shortlist_per_query_scope"])
 require(len(queries)==656,"QUERY_COHORT_COUNT")
 # Reconcile complete dense supplement union and per-form top-K on persisted rows.
 ext_groups=0
 for (co,sr),rr in groups.items():
  if not co.startswith("C2_EXTENSION"):continue
  ext_groups+=1;K=R.pol["risk"]["extension_top_k_per_form"]
  p=[o["payload"] for o in rr];require(len({x["target_ref"] for x in p})==len(p),"EXTENSION_DUPLICATE")
  for fld in ("extension_label_rank","extension_context_rank"):
   require(sorted(x[fld] for x in p if x[fld] is not None)==list(range(1,K+1)),"EXTENSION_POOL_TOPK_CLOSURE")
 require(ext_groups==328,"EXTENSION_GROUP_COUNT")
 # Source-first packet cannot contain Critic/generator candidate opinions.
 first=load(priv/"ExpertSourceFirstQueue.json");post=load(priv/"ExpertComparisonHidden.json")
 require(first==[o["payload"]|{"task_ref":ref(o)} for o in R.first] and post==R.post,"EXPERT_PACKET_REPLAY")
 require(len(first)==len(post)==36 and len({x["review_id"] for x in first})==36 and {x["review_id"] for x in first}=={x["review_id"] for x in post},"EXPERT_PACKET_CLOSURE")
 forbidden={"critic_reason","generator_ref","risk_ref","priority_evidence","target_native_id","critic_relation","target_key"}
 require(all(not (forbidden&set(x)) and x["initial_review_status"]=="NOT_ADJUDICATED" for x in first),"PRE_REVIEW_LEAK")
 # Actual admission path invoked on every verified record for both development
 # and scientific purpose. No scientific caller may get a candidate through.
 gate=DevelopmentGate(verified,queries)
 requests=Counter()
 for r in verified:
  for p in ("CURATION_INSPECT","DEVELOPMENT_CONCEPT_REVIEW","NUTRIENT_TRANSFER","MAPPING_RELEASE"):
   a=gate.request(p,r);requests[(p,a["decision"])]+=1
 require(requests[("CURATION_INSPECT","ALLOW")]==len(verified) and requests[("DEVELOPMENT_CONCEPT_REVIEW","ALLOW")]==sum(len(x["payload"]["shortlist_refs"]) for x in queries.values()) and requests[("NUTRIENT_TRANSFER","HOLD")]==requests[("MAPPING_RELEASE","HOLD")]==len(verified),"ADMISSION_GATE_COUNTS")
 require(all(sha(root/k)==v for k,v in fences.items()),"UPSTREAM_MUTATION")
 require(all(sha(run/k)==v for k,v in original_hashes.items()),"RUN_MUTATION")
 tests=[]
 def pos(n,fn):
  try:require(fn() is not False,"ASSERTION");tests.append({"test":n,"expected":"ACCEPT","observed":"ACCEPT","pass":True})
  except Exception as ex:tests.append({"test":n,"expected":"ACCEPT","observed":str(ex)[:130],"pass":False})
 def neg(n,code,fn):
  try:fn();tests.append({"test":n,"expected":code,"observed":"ACCEPT","pass":False})
  except Exception as ex:tests.append({"test":n,"expected":code,"observed":str(ex)[:130],"pass":str(ex).startswith(code)})
 def mut(o,fn):z=copy.deepcopy(o);fn(z);return seal(z)
 def ev(a,b,ga="INGREDIENT_REFERENCE",gb="ONTOLOGY_FOOD_PRODUCT_CLASS"):
  return decide({"label":a,"grain":ga},{"label":b,"grain":gb},R.pol["risk"],"CORE_RETAINED_DEV",False)
 scopes={o["payload"]["iri"]:o for o in by["ScopeAssessment"]}
 pos("all 40107 real named class assessments replay",lambda:len(scopes)==40107)
 pos("original named product closure preserved as source membership",lambda:sum(o["payload"]["asserted_core_member"] for o in scopes.values())==12362)
 pos("all C1 six missing classes recovered in typed development lanes",lambda:all(scopes[x["target_key"][1]]["payload"]["scope_status"]=="EXTENSION_TYPED_RETRIEVAL_ONLY" for x in load(root/C1/"validation_001/private/FoodOnScopeDiagnosis.json")))
 pos("all nine real nonfood probes held",lambda:all(scopes[B+i]["payload"]["scope_status"].startswith("HOLD") for i in R.pol["foodon"]["negative_probe_ids"]))
 pos("named intersection necessary consequence only; no union/filler axiom kinds",lambda:all(s["axiom_kind"] in {"ASSERTED_NAMED_SUBCLASS","NAMED_EQUIVALENT_CLASS","NAMED_EQUIVALENT_CLASS_REVERSE","NECESSARY_NAMED_INTERSECTION_CONJUNCT"} for o in scopes.values() for w in o["payload"]["witnesses"] for s in w["steps"]))
 pos("all 355 and 29081 frozen prior candidates retained",lambda:sum(len(x) for (c,_),x in groups.items() if c=="U3A_EXPOSED_44")==355 and sum(len(x) for (c,_),x in groups.items() if c=="U3B_FROZEN_284")==29081)
 pos("all new extension top-K groups replay",lambda:ext_groups==328)
 pos("all 656 query abstention groups replay",lambda:len(queries)==656)
 pos("expert source-first and post-initial packets separate, not adjudicated",lambda:len(first)==36 and len(post)==36)
 pos("explicit raw vs boiled blocks",lambda:ev("马铃薯(煮)","potato (raw)")["disposition"]=="BLOCK_EXPLICIT_CONFLICT")
 pos("unknown cooking state is not explicit contradiction",lambda:not ev("potato","potato boiled")["explicit_conflicts"] and bool(ev("potato","potato boiled")["unresolved_conditions"]))
 pos("generic bread vs rye holds subtype condition not explicit conflict",lambda:not ev("bread","bread rye")["explicit_conflicts"] and bool(ev("bread","bread rye")["unresolved_conditions"]))
 pos("whole salad vs dressing holds component role",lambda:"COMPONENT_WHOLE_OR_FORM_MISMATCH_CANDIDATE" in ev("green salad","salad dressing")["role_conditions"])
 pos("Malabar spinach not silently identical",lambda:"POTENTIAL_SPECIES_DISTINCTION_REQUIRES_AUTHORITY" in ev("spinach","malabar spinach")["unresolved_conditions"])
 pos("tartare name not explicit raw assertion",lambda:features("steak tartare","VISUAL_FOOD_CLASS",R.pol["risk"])["state"]=="UNKNOWN")
 pos("fresh input origin not automatically fresh state",lambda:"fresh" not in features("Spinach, cooked, from fresh","COMPOSITION_REFERENCE",R.pol["risk"])["process_mentions"])
 pos("peanut and lettuce not false raw from Chinese substring",lambda:all(features(x,"INGREDIENT_REFERENCE",R.pol["risk"])["state"]!="RAW_EXPLICIT" for x in ["花生","生菜"]))
 pos("no anchor generates abstention evidence",lambda:ev("apple","potato")["concept_review_eligible"] is False)
 bad=next(o for o in verified.values() if not o["payload"]["concept_review_eligible"])
 red=next(o for o in verified.values() if o["payload"]["explicit_conflicts"])
 sc=next(o for o in scopes.values() if o["payload"]["scope_status"].startswith("HOLD") and o["payload"]["exclusion_roots"])
 neg("forged mapping release blocked by schema","C2_SCHEMA",lambda:validate(mut(bad,lambda z:z["payload"].update(mapping_release="ALLOW")),R.vs,R.registry))
 neg("forged scientific equivalence blocked by schema","C2_SCHEMA",lambda:validate(mut(bad,lambda z:z["payload"].update(concept_equivalence="EXACT")),R.vs,R.registry))
 neg("forged scope admission on excluded actual class","SCOPE_INELIGIBLE",lambda:validate(mut(sc,lambda z:z["payload"].update(scope_status="CORE_RETAINED_DEV")),R.vs,R.registry))
 neg("missing required source dependency","REQUIRED_RISK_DEPENDENCY",lambda:validate(mut(bad,lambda z:z.update(dependency_refs=[r for r in z["dependency_refs"] if r!=z["payload"]["source_ref"]])),R.vs,R.registry))
 def forged():
  z=mut(red,lambda x:x["payload"].update(explicit_conflicts=[],unresolved_conditions=[],role_conditions=[],identity_evidence=["FORGED"],disposition="REVIEW_ELIGIBLE_DEV_ONLY",concept_review_eligible=True));a,t,ss,rd=inputs(red);verify_decision(z["payload"],a,t,R.pol["risk"],ss,rd)
 neg("resealed fabricated eligibility fails real endpoint recomputation","RISK_RECOMPUTE_MISMATCH",forged)
 def forge_query():
  q=next(o for o in queries.values() if not o["payload"]["shortlist_refs"]);z=copy.deepcopy(q["payload"]);z["shortlist_refs"]=[ref(bad)];verify_query(z,groups[(z["cohort"],z["source_legacy_ref"])],R.pol["risk"]["shortlist_per_query_scope"])
 neg("forged shortlist fails actual candidate pool recomputation","QUERY_RECOMPUTE_MISMATCH",forge_query)
 pos("unverified caller record held",lambda:gate.request("DEVELOPMENT_CONCEPT_REVIEW","invented")["decision"]=="HOLD")
 pos("all actual nutrient transfer and mapping requests held",lambda:requests[("NUTRIENT_TRANSFER","HOLD")]==len(verified) and requests[("MAPPING_RELEASE","HOLD")]==len(verified))
 require(all(t["pass"] for t in tests),"C2_TEST_FAILURE:"+str([t for t in tests if not t["pass"]]))
 R.rt.b.verify_files()
 out.mkdir(parents=True);result={"status":"PASS_C2_FULL_REPLAY_AND_DEVELOPMENT_GATE / SCIENTIFIC_QUALIFICATION_HOLD","tests_total":len(tests),"tests_passed":sum(t["pass"] for t in tests),"tests":tests,"object_replays":len(actual),"risk_records_recomputed":len(verified),"query_decisions_replayed":len(queries),"extension_groups_replayed":ext_groups,"extension_full_model_replay":True,"scope_class_replays":len(scopes),"expert_packets_replayed":len(first),"actual_gate_requests":[{"purpose":k[0],"decision":k[1],"count":v} for k,v in sorted(requests.items())],"original_input_fences_unchanged":True,"original_run_unchanged":True,"independent_scientific_reference_count":0,"mapping_release_count":0,"limitations":["same-code full replay and actual gate exercise, not independent scientific validity","rule features are limited lexical evidence, no full OWL reasoner or expert taxonomy","development gate is exercised here, future consumer integration must use verified records","file separation not proven access control"]}
 put(out/"C2ValidationReport.json",result)
 print(json.dumps({k:v for k,v in result.items() if k!="tests"},ensure_ascii=False),flush=True)
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--run",type=P.Path,required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.profile,x.run,x.out)
