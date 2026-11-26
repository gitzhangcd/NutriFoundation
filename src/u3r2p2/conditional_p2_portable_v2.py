#!/usr/bin/env python3
"""Bounded R2-P2 conditional question routing on frozen initial pools.
All rules are general surface hypotheses, not semantic approvals or R1 replacement.
No reviewer answer or target ID used by route() or rerank()."""
import argparse, json, sys
from pathlib import Path
from collections import Counter, defaultdict
from run_p2_portable_v2 import BASE,P1,read,lines,put,putl,sha,dg,require,toks,peel_conflict
ANIMALS={"pork","pig","beef","cattle","veal","lamb","mutton","goat","chicken","turkey","duck","goose","tuna","mackerel","salmon","cod","shrimp","crab"}
ANIMAL_CANON={"pig":"pork","cattle":"beef","veal":"beef","mutton":"lamb"}
ORGANS={"liver","kidney","heart","lung","tongue","brain","spleen","gizzard"}
COOKED={"cooked","roasted","baked","braised","fried","boiled","steamed","grilled"}
def animals(ts):return {ANIMAL_CANON.get(t,t) for t in ts&ANIMALS}
def assess(q,c):
 ident=set(q["identity_tokens"]);qual=set(q["qualifier_tokens"]);t=toks(c["target_native_label"])
 parts=[set(x) for x in q["component_tokens"]]
 ingredients=q["source_kind"]=="INGREDIENT_REFERENCE"
 animal_s,animal_t=animals(ident),animals(t)
 hard=[];questions=[]
 # Preserve all existing holds; new candidates remain R1-not-run, even if not visibly conflicting.
 if c["route"]=="HOLD_INHERITED_R1":hard.append("INHERITED_R1_HOLD")
 if peel_conflict(q["source_label"],c["target_native_label"]):hard.append("EXPLICIT_PEEL_CONFLICT")
 if ingredients and (("raw" in qual and t&COOKED and "raw" not in t) or ("raw" in t and qual&COOKED and not t&COOKED)):
  hard.append("POTENTIAL_EXPLICIT_RAW_COOKED_CONFLICT")
 if ingredients and len(animal_s)==len(animal_t)==1 and not animal_s&animal_t:
  hard.append("POTENTIAL_EXPLICIT_SPECIES_CONFLICT")
 if ingredients and len(ident&ORGANS)==len(t&ORGANS)==1 and not ident&t&ORGANS:
  hard.append("POTENTIAL_EXPLICIT_ORGAN_CONFLICT")
 # Never interpret missing qualifiers as proof of contradiction or equivalence.
 if qual-t:questions.append("VERIFY_SOURCE_QUALIFIER_APPLICABILITY")
 if t&COOKED and not qual&COOKED:questions.append("VERIFY_TARGET_COOKING_STATE")
 if t&ORGANS and not ident&ORGANS:questions.append("VERIFY_TARGET_EDIBLE_PART")
 if animal_t and not animal_s:questions.append("VERIFY_TARGET_SPECIES")
 if q.get("untranslated_label_residual","").strip("()[]（）【】，、, "):questions.append("RESOLVE_SOURCE_LABEL_RESIDUAL")
 if q.get("native_alias_raw"):questions.append("VERIFY_NATIVE_ALIAS_CONTEXT")
 shared=ident&t
 matched_parts=sum(bool(x and x<=t) for x in parts)
 if not ingredients:
  questions+=["VERIFY_DISH_IDENTITY_VS_INGREDIENT_ROLE","VERIFY_RECIPE_COMPOSITION_AND_PREPARATION"]
  if shared:
   hypothesis="DISH_OR_CONDITIONAL_COMPOSITION_QUESTION";priority=0
  elif matched_parts:
   hypothesis="COMPONENT_RELATED_QUESTION_NOT_DISH_EQUIVALENCE";priority=1
  else:
   hypothesis="UNRESOLVED_DISH_OR_COMPONENT";priority=2
 else:
  questions+=["VERIFY_IDENTITY_SPECIES_EDIBLE_PART_FORM","VERIFY_TARGET_SCOPE_AND_DIRECTION"]
  if ident and ident<=t:
   hypothesis="IDENTITY_OR_CONDITIONAL_DIRECTION_QUESTION";priority=0
  elif shared or animal_s&animal_t:
   hypothesis="BROADER_NARROWER_OR_RELATED_QUESTION";priority=1
  else:
   hypothesis="UNRESOLVED_IDENTITY_OR_ALIAS";priority=2
 # Rerank surface hypotheses, not mappings; even high priority retains HOLD.
 if hard:priority=3;hypothesis="HOLD_CONFLICT_OR_INHERITED_RISK"
 return {"priority":priority,"question_family":hypothesis,"potential_conflict_flags":sorted(set(hard)),
  "condition_questions":sorted(set(questions)),"candidate_relation":"UNRESOLVED","r1_disposition":c["route"],
  "r1_revalidation_required":True,"accepted_equivalence":False,"development_concept_review_authorized":False,"measurement_transfer":"HOLD","mapping_release":"HOLD"}
def reorder(q,rows):
 z=[{**c,**assess(q,c),"original_rank":c["rank"]} for c in rows]
 z.sort(key=lambda x:(x["priority"],x["original_rank"]))
 for i,x in enumerate(z,1):x["rank"]=i
 return z
def generate(root,old,out):
 require(not out.exists() and out.is_relative_to(root/BASE/"P2"),"NEW_RUN")
 fr=read(old/"CandidateFreeze.json")
 require(all(sha(root/p)==h for p,h in fr["input_fences"].items()),"FROZEN_INPUT_DRIFT")
 require(all(sha(old/"private"/p)==h for p,h in fr["private_hashes"].items()),"FROZEN_CANDIDATES_DRIFT")
 require(fr["mapping_release"] is False and not fr["reserved32_semantics_read"],"OLD_RELEASE")
 qs={q["review_id"]:q for q in lines(old/"private/QueryHypotheses.jsonl")};require(len(qs)==19,"DEV19")
 groups=defaultdict(list)
 for c in lines(old/"private/CandidateQuestions.jsonl"):
  if c["arm"] not in ("SOURCE_SPARSE","HYBRID"):continue
  require(c["query_digest"]==dg(qs[c["review_id"]]) and not c["accepted_equivalence"] and c["mapping_release"]=="HOLD","SOURCE_BINDING")
  groups[(c["review_id"],c["scope"],c["arm"])].append(c)
 # Zero-hit source/scope groups retained explicitly.
 ranks=[r for r in lines(old/"private/Ranks.jsonl") if r["arm"] in ("SOURCE_SPARSE","HYBRID")]
 require(len(ranks)==19*4*2,"RANK_GROUPS")
 rr=[];allrows=[]
 for r in ranks:
  rid,scope,arm=r["review_id"],r["scope"],r["arm"];g=groups[(rid,scope,arm)]
  require([c["target_key"] for c in g]==r["targets"],"RANK_TARGET_ID")
  z=reorder(qs[rid],g)
  require({tuple(x["target_key"]) for x in z}=={tuple(x["target_key"]) for x in g} and len(z)<=r["pool_budget"],"BUDGET_OR_MEMBERSHIP_DRIFT")
  newarm=arm+"_CONDITIONAL"
  allrows.extend({**x,"arm":newarm} for x in z)
  rr.append({**r,"arm":newarm,"targets":[x["target_key"] for x in z]})
 require(all(not x["accepted_equivalence"] and not x["development_concept_review_authorized"] and x["r1_revalidation_required"] and x["mapping_release"]=="HOLD" for x in allrows),"RELEASE")
 out.mkdir(parents=True,mode=0o700);p=out/"private";p.mkdir(mode=0o700)
 putl(p/"ConditionalQuestions.jsonl",allrows);putl(p/"Ranks.jsonl",rr)
 put(out/"ConditionalFreeze.json",{"method_sha256":sha(Path(__file__)),"parent_freeze_sha256":sha(old/"CandidateFreeze.json"),
  "parent_report_sha256":sha(old/"P2DevelopmentReport.json"),"private_hashes":{x.name:sha(x) for x in p.iterdir()},
  "cases":19,"candidate_rows":len(allrows),"reserved32_outcomes_read":0,"mapping_release":False,"method_status":"SECOND_DEV_VARIANT_NOT_FINAL"})
def evaluate(root,old,out):
 f=read(out/"ConditionalFreeze.json")
 require(f["method_sha256"]==sha(Path(__file__)) and f["parent_freeze_sha256"]==sha(old/"CandidateFreeze.json"),"METHOD_DRIFT")
 require(all(sha(out/"private"/p)==h for p,h in f["private_hashes"].items()),"CANDIDATE_DRIFT")
 fr=read(old/"CandidateFreeze.json")
 require(all(sha(root/p)==h for p,h in fr["input_fences"].items()),"FROZEN_INPUT_DRIFT")
 rows=list(lines(out/"private/ConditionalQuestions.jsonl"));rr=list(lines(out/"private/Ranks.jsonl"))
 ids={r["review_id"] for r in rr};require(len(ids)==19,"DEV19")
 pos=defaultdict(set);neg=defaultdict(set);types={}
 for r in lines(root/P1/"private/ReferenceGapAttribution.jsonl"):
  if r["review_id"] in ids and r["domain"]=="ORIGINAL":pos[r["review_id"]].add(tuple(r["target_key"]))
 cfg=read(root/"configs/audit/tasks/B2_U3R2_REF44_Gemini_001.json")
 for r in lines(root/cfg["output"]["directory"]/"ReviewRecords.jsonl"):
  if r["review_id"] not in ids:continue
  for c in r["hard_negatives"]:
   t=tuple(c["target_key"]);neg[r["review_id"]].add(t);types[(r["review_id"],t)]=c["conflict_type"]
 require(sum(map(len,pos.values()))==43 and len(pos)==18,"REFERENCE_DENOMINATOR")
 report=[]
 for arm in ("SOURCE_SPARSE_CONDITIONAL","HYBRID_CONDITIONAL"):
  for k in [1,3,5,12,"POOL"]:
   cand=defaultdict(set)
   for r in rr:
    if r["arm"]!=arm or r["scope"]=="FOODON_EXTENSION":continue
    cand[r["review_id"]].update(tuple(t) for t in (r["targets"] if k=="POOL" else r["targets"][:k]))
   require(set(cand)==ids,"CASE_SET")
   report.append({"arm":arm,"k_per_scope":k,"reference_cases":18,"reference_edges":43,"reference_hit_cases":sum(bool(cand[i]&pos[i]) for i in ids),
    "reference_edges_hit":sum(len(cand[i]&pos[i]) for i in ids),"candidate_edges":sum(map(len,cand.values())),
    "critic_negative_overlap":sum(len(cand[i]&neg[i]) for i in ids),"unjudged_edges":sum(len(cand[i]-pos[i]-neg[i]) for i in ids)})
 hold={}
 for arm in ("SOURCE_SPARSE_CONDITIONAL","HYBRID_CONDITIONAL"):
  a=[r for r in rows if r["arm"]==arm and r["scope"]!="FOODON_EXTENSION"]
  b=[r for r in a if r["potential_conflict_flags"]]
  hold[arm]={"all_edges":len(a),"flagged_edges":len(b),
   "flagged_critic_negative":sum(tuple(r["target_key"]) in neg[r["review_id"]] for r in b),
   "flagged_critic_positive":sum(tuple(r["target_key"]) in pos[r["review_id"]] for r in b),
   "flagged_negative_types":dict(Counter(types[(r["review_id"],tuple(r["target_key"]))] for r in b if tuple(r["target_key"]) in neg[r["review_id"]])),
   "question_families":dict(Counter(r["question_family"] for r in a))}
  require(all(r["mapping_release"]=="HOLD" and r["candidate_relation"]=="UNRESOLVED" and not r["accepted_equivalence"] for r in a),"NO_RELEASE")
 z={"status":"CONDITIONAL_NAVIGATION_DEV_ONLY","metrics":report,"conflict_flags":hold,"reserved32_outcomes_read":0,"expert_gold":0,"mapping_releases":0,
  "limitations":["Surface checks are tentative; candidate sets unchanged; no scientific equivalence or conditional mapping accepted.","First19 exposed development cases; no independent performance.","New candidate R1 risk/scope qualification not executed."]}
 put(out/"P2ConditionalReport.json",z);print(json.dumps(z,ensure_ascii=False))
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("phase",choices=["generate","evaluate"]);a.add_argument("--root",type=Path,default=Path("."));a.add_argument("--parent",type=Path,required=True);a.add_argument("--out",type=Path,required=True);x=a.parse_args()
 (generate if x.phase=="generate" else evaluate)(x.root.resolve(),x.parent.resolve(),x.out.resolve())
