"""Independent synthetic-only A2 scoring contract audit.
No real data, file read of real results, comparison authorization, or CLI.
The oracle implements the frozen definition independently of score_a2."""
import collections as C
import copy,io,random,sys,unittest
from pathlib import Path
from score_a2 import score,ARMS,SCOPES,KS
SUPPORTED={"EXACT","CLOSE","BROADER_TARGET","NARROWER_TARGET","RELATED","CONDITIONAL"}
def check(x,msg):
 if not x:raise AssertionError(msg)
def fixture(seed,n=32):
 g=random.Random(seed)
 ids=[f"synthetic-{i:02d}" for i in range(n)]
 by={s:[(s if s!="FOODON_EXTENSION" else "FoodOn","fictional-v",s+str(i)) for i in range(16)] for s in SCOPES}
 original=set().union(*(set(by[s]) for s in SCOPES[:3]));extension=set(by[SCOPES[3]])
 outside=("FoodOn","fictional-v","outside")
 ranks=[];refs=[];budgets={}
 for i in ids:
  for s in SCOPES:
   cap=g.randrange(0,17);budgets[(i,s)]=cap
   for arm in ARMS:
    targets=g.sample(by[s],g.randrange(cap+1))
    ranks.append({"review_id":i,"scope":s,"arm":arm,"pool_budget":cap,"targets":[list(t) for t in targets]})
  targets=sorted(original|extension|{outside});sample=g.sample(targets,g.randrange(0,13));sep=g.randrange(len(sample)+1)
  rs=[]
  for t in sample[:sep]:
   rel=g.choice(sorted(SUPPORTED|{"AMBIGUOUS","UNRESOLVED"}))
   app=g.choice(["CONCEPT_CANDIDATE_ONLY","CONDITIONAL_CONCEPT_CANDIDATE","RELATED_ONLY","UNRESOLVED"])
   rs.append({"target_key":list(t),"relation":rel,"applicability":app})
  refs.append({"review_id":i,"independent_candidates":rs,"hard_negatives":[{"target_key":list(t)} for t in sample[sep:]]})
 return ranks,refs,original,extension,ids,budgets
def oracle(ranks,refs,original,extension,ids,sensitivity):
 refs={x["review_id"]:x for x in refs}
 ranks={(x["review_id"],x["scope"],x["arm"]):[tuple(t) for t in x["targets"]] for x in ranks}
 result={};hitsets={};pairs={}
 positives={};negatives={};alljudged={}
 for i in ids:
  x=refs[i];positives[i]=set();negatives[i]={tuple(t["target_key"]) for t in x["hard_negatives"]}
  alljudged[i]={tuple(t["target_key"]) for t in x["independent_candidates"]}|negatives[i]
  for t in x["independent_candidates"]:
   if t["relation"] not in SUPPORTED or t["applicability"]=="UNRESOLVED":continue
   if sensitivity and (t["relation"]=="RELATED" or t["applicability"]=="RELATED_ONLY"):continue
   positives[i].add(tuple(t["target_key"]))
 for domain,u,scs in [("ORIGINAL",original,SCOPES[:3]),("EXTENSION",extension,SCOPES[3:])]:
  eligible={i for i in ids if positives[i]&u}
  for arm in ARMS:
   for k in KS:
    hit=set()
    totals={s:0 for s in ("candidate_edges","reference_edges","reference_edges_hit","negative_overlap","unreviewed_edges","reviewed_neither_supported_nor_negative","residual_not_supported_or_negative","cases_with_candidates")}
    for i in ids:
     candidate=set()
     for scope in scs:
      seq=ranks[i,scope,arm];candidate.update(seq if k=="POOL" else seq[:k])
     p=positives[i]&u;n=negatives[i]&u
     totals["reference_edges"]+=len(p);totals["candidate_edges"]+=len(candidate);totals["cases_with_candidates"]+=int(bool(candidate))
     for t in candidate:
      if t in p:totals["reference_edges_hit"]+=1;hit.add(i)
      elif t in n:totals["negative_overlap"]+=1
      else:
       totals["residual_not_supported_or_negative"]+=1
       if t in alljudged[i]:totals["reviewed_neither_supported_nor_negative"]+=1
       else:totals["unreviewed_edges"]+=1
    hitsets[domain,arm,k]=hit
    result[domain,arm,k]={"domain":domain,"arm":arm,"k_per_scope":k,"cases":len(ids),"reference_case_denominator":len(eligible),"reference_hit_cases":len(hit),"reference_hit_fraction":len(hit)/len(eligible) if eligible else None,**totals}
  for arm in ARMS[1:]:
   a=hitsets[domain,ARMS[0],12];b=hitsets[domain,arm,12]
   pairs[domain,arm]={"domain":domain,"k_per_scope":12,"primary":ARMS[0],"comparator":arm,"reference_case_denominator":len(eligible),"both_hit":len(a&b),"primary_only":len(a-b),"comparator_only":len(b-a),"neither_hit":len(eligible-a-b),"paired_hit_difference":(len(a)-len(b))/len(eligible) if eligible else None}
 return result,pairs,sum(len(x-(original|extension)) for x in positives.values())
def audit_preconditions(ranks,expected_ids,trusted_budgets):
 """Pure proposed comparison-import guard; caller must bind the trusted
 expected_ids and budgets to immutable real preparation artifacts AFTER
 explicit separate authorization. Synthetic tests only here."""
 check(len(expected_ids)==32 and len(set(expected_ids))==32,"EXACT_32_ID_CONTRACT")
 keys={(i,s) for i in expected_ids for s in SCOPES}
 check(set(trusted_budgets)==keys,"TRUSTED_BUDGET_CLOSURE")
 for (i,s),b in trusted_budgets.items():
  # Frozen dense rank hints are two lists of length 20 or 12.
  limit=24 if s=="FOODON_EXTENSION" else 40
  check(type(b) is int and 0<=b<=limit,"TRUSTED_BUDGET_TYPE_OR_RANGE")
 seen=set()
 for r in ranks:
  k=(r["review_id"],r["scope"]);g=(*k,r["arm"])
  check(k in keys and r["arm"] in ARMS and g not in seen,"GROUP_SCOPE")
  seen.add(g)
  check(type(r["pool_budget"]) is int and r["pool_budget"]==trusted_budgets[k] and len(r["targets"])<=trusted_budgets[k],"TRUSTED_CAP_MISMATCH")
 check(seen=={(i,s,a) for i,s in keys for a in ARMS},"RANK_GROUP_CLOSURE")
 return True
def raises(f):
 try:f()
 except (ValueError,AssertionError):return True
 return False
def run_synthetic():
 root=Path(__file__).resolve().parents[2]
 sys.path.insert(0,str(root/"tests/u3r2p2a2"))
 from verify_a2 import TestA2
 stream=io.StringIO()
 old=unittest.TextTestRunner(stream=stream,verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestA2))
 check(old.wasSuccessful() and old.testsRun==18,"INHERITED_SYNTHETIC_TESTS")
 count=0;metrics=0;pairs=0
 for seed in range(16):
  ranks,refs,u,e,ids,budgets=fixture(seed)
  check(audit_preconditions(ranks,ids,budgets),"PRECONDITION_FIXTURE")
  for sensitivity in (False,True):
   a,per=score(ranks,refs,u,e,ids,sensitivity=sensitivity)
   x,y,out=oracle(ranks,refs,u,e,ids,sensitivity)
   check({(m["domain"],m["arm"],m["k_per_scope"]):m for m in a["metrics"]}==x,"INDEPENDENT_ORACLE_METRICS")
   check({(m["domain"],m["comparator"]):m for m in a["paired_at12"]}==y,"INDEPENDENT_ORACLE_PAIRED")
   check(a["supported_outside_frozen_universes"]==out and a["scientific_precision_recall"]=="NOT_ESTIMABLE" and not a["scientific_mapping_release"],"INDEPENDENT_ORACLE_OUTSIDE")
   check(len(per)==32*2*3*5,"PER_CASE_CLOSURE")
   count+=1;metrics+=len(x);pairs+=len(y)
 ranks,refs,u,e,ids,budgets=fixture(99)
 # Targeted, independent boundary cases with no eligible references.
 empty=[{"review_id":i,"independent_candidates":[],"hard_negatives":[]} for i in ids]
 ar,_=score(ranks,empty,u,e,ids);check(all(m["reference_case_denominator"]==0 and m["reference_hit_fraction"] is None for m in ar["metrics"]),"ZERO_DENOM")
 check(all(x["paired_hit_difference"] is None for x in ar["paired_at12"]),"ZERO_PAIRED_DENOM")
 # All three original scopes can independently contribute K; not global K.
 # Constructed synthetic example uses 2 candidates per scope, 1 per scope at K=1.
 custom,cr,cu,ce,ci,cb=fixture(101)
 sample=ci[0]
 for x in custom:
  if x["review_id"]==sample and x["scope"] in SCOPES[:3]:
   x["targets"]=[list(t) for t in sorted(cu) if t[0]==x["scope"]][:2];x["pool_budget"]=2
 a,per=score(custom,cr,cu,ce,ci)
 check(next(x for x in per if x["case"]==sample and x["domain"]=="ORIGINAL" and x["arm"]==ARMS[0] and x["k"]==1)["candidate_count"]==3,"K_PER_SCOPE")
 # Reproduce known pure-core limitations WITHOUT modifying the frozen scorer.
 bad=copy.deepcopy(ranks);bad[0]["pool_budget"]+=1
 score(bad,refs,u,e,ids)
 check(raises(lambda:audit_preconditions(bad,ids,budgets)),"GUARD_UNEQUAL_CAP")
 badfloat=copy.deepcopy(ranks);badfloat[0]["pool_budget"]=float(badfloat[0]["pool_budget"])
 score(badfloat,refs,u,e,ids)
 check(raises(lambda:audit_preconditions(badfloat,ids,budgets)),"GUARD_FLOAT_CAP")
 score(ranks,refs,u,e,ids+[ids[0]])
 check(raises(lambda:audit_preconditions(ranks,ids+[ids[0]],budgets)),"GUARD_DUP_ID")
 smallids=ids[:-1];smallr=[x for x in ranks if x["review_id"] in smallids];smallf=[x for x in refs if x["review_id"] in smallids]
 score(smallr,smallf,u,e,smallids)
 check(raises(lambda:audit_preconditions(smallr,smallids,{k:v for k,v in budgets.items() if k[0] in smallids})),"GUARD_31_CASE")
 check(raises(lambda:audit_preconditions(ranks[:-1],ids,budgets)),"GUARD_MISSING_GROUP")
 # The core intentionally treats every listed hard negative as a negative,
 # including UNRESOLVED_OTHER. That is a qualification issue, not a new metric.
 target=sorted(u)[0];neg=[{"review_id":i,"independent_candidates":[],"hard_negatives":[{"target_key":list(target),"conflict_type":"UNRESOLVED_OTHER"}] if i==ids[0] else []} for i in ids]
 r2=copy.deepcopy(ranks)
 for x in r2:
  if x["review_id"]==ids[0] and x["scope"]==target[0] and x["arm"]==ARMS[0]:
   x["pool_budget"]=1;x["targets"]=[list(target)]
 a,_=score(r2,neg,u,e,ids)
 check(next(x for x in a["metrics"] if x["domain"]=="ORIGINAL" and x["arm"]==ARMS[0] and x["k_per_scope"]==1)["negative_overlap"]>=1,"UNRESOLVED_NEGATIVE_COUNTED")
 return {"status":"PASS_FROZEN_METRIC_ARITHMETIC / HOLD_AUTHORIZED_IMPORT_CONTRACT","inherited_tests_passed":old.testsRun,"independent_oracle_runs":count,"metric_rows_exactly_matched":metrics,"paired_rows_exactly_matched":pairs,"targeted_contract_tests_passed":8,"synthetic_only":True,"real_scores_computed":0,"primary":"ORIGINAL domain per-case Reference-Hit@12; K per scope; eligible denominator same across arms","core_contract_gaps_reproduced":["Mismatched per-arm pool_budget accepted if each list satisfies its self-declared cap","Noninteger pool_budget accepted by pure core","Duplicate expected_ids silently collapsed to a set","31-case coherent input accepted; fixed 32-case identity binding must be external"],"proposed_guard_synthetic_validated":True,"real_import_gate_implemented":False,"unresolved_other_is_counted_as_hard_negative_by_frozen_core":True,"no_change_to_frozen_metrics":True,"confidence_interval_or_power_claim":False}
if __name__=="__main__":
 import json
 print(json.dumps(run_synthetic(),ensure_ascii=False))
