"""A2 predeclared reference-overlap scoring (pure functions, no real-data CLI).
Call only after separately authorized, source-verified reviewer import.
Synthetic tests are not independent reference results.
"""
from collections import defaultdict,Counter
from pathlib import Path
import sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/"u3r2"))
from compare_reference import supported,require
ARMS=("SOURCE_SPARSE","BASELINE_FUSION","HYBRID")
SCOPES=("FoodOn","FDC_SR_Legacy","FNDDS","FOODON_EXTENSION")
KS=(1,3,5,12,"POOL")
def verify_rank_index(ranks,ids,original,extension):
 require(not original&extension,"UNIVERSE_OVERLAP")
 idx={}
 for r in ranks:
  k=(r["review_id"],r["scope"],r["arm"]);require(k not in idx,"DUP_RANK_GROUP")
  targets=[tuple(x) for x in r["targets"]];require(len(targets)==len(set(targets))<=r["pool_budget"],"RANK_BUDGET")
  sc=r["scope"]
  require(sc in SCOPES and all(t in (extension if sc=="FOODON_EXTENSION" else original) and (sc=="FOODON_EXTENSION" or t[0]==sc) for t in targets),"RANK_SCOPE")
  idx[k]=targets
 require(set(idx)=={(i,s,a) for i in ids for s in SCOPES for a in ARMS},"RANK_CLOSURE")
 return idx
def score(ranks,references,original,extension,expected_ids,*,sensitivity=False):
 """No qualification or access grant here. Reference inputs must already have
 been checked by controller against actual schema, source and standard evidence.
 This function computes exact overlap, not scientific precision or recall.
 """
 ids=set(expected_ids);refs={r["review_id"]:r for r in references}
 require(len(refs)==len(references) and set(refs)==ids and ids,"REFERENCE_CASE_CLOSURE")
 idx=verify_rank_index(ranks,ids,original,extension)
 pos={};neg={};reviewed={}
 for i,r in refs.items():
  p0={tuple(x["target_key"]) for x in r["independent_candidates"]};n={tuple(x["target_key"]) for x in r["hard_negatives"]}
  require(not p0&n and len(p0)==len(r["independent_candidates"]) and len(n)==len(r["hard_negatives"]),"REFERENCE_POS_NEG_CLOSURE")
  reviewed[i]=p0|n;neg[i]=n
  r1={**r,"independent_candidates":[x for x in r["independent_candidates"] if x["relation"]!="RELATED" and x["applicability"]!="RELATED_ONLY"]} if sensitivity else r
  pos[i]=supported(r1)
 report=[];hits={};per=[]
 for domain,u in (("ORIGINAL",original),("EXTENSION",extension)):
  scs=[s for s in SCOPES if (s=="FOODON_EXTENSION")== (domain=="EXTENSION")]
  den={i for i in ids if pos[i]&u}
  for a in ARMS:
   for k in KS:
    stat=Counter();h=set()
    for i in sorted(ids):
     cand={t for s in scs for t in (idx[i,s,a] if k=="POOL" else idx[i,s,a][:k])}
     p=pos[i]&u;n=neg[i]&u
     if cand&p:h.add(i)
     stat["candidate_edges"]+=len(cand);stat["reference_edges"]+=len(p)
     stat["reference_edges_hit"]+=len(cand&p);stat["negative_overlap"]+=len(cand&n)
     stat["unreviewed_edges"]+=len(cand-reviewed[i]);stat["reviewed_neither_supported_nor_negative"]+=len((cand&reviewed[i])-p-n)
     stat["residual_not_supported_or_negative"]+=len(cand-p-n)
     stat["cases_with_candidates"]+=bool(cand)
     per.append({"case":i,"domain":domain,"arm":a,"k":k,"has_supported_reference":bool(p),"hit":bool(cand&p),"candidate_count":len(cand),"supported_edges":len(p),"supported_hits":len(cand&p),"negative_overlap":len(cand&n)})
    require(stat["candidate_edges"]==stat["reference_edges_hit"]+stat["negative_overlap"]+stat["residual_not_supported_or_negative"],"METRIC_CLOSURE")
    require(stat["residual_not_supported_or_negative"]==stat["unreviewed_edges"]+stat["reviewed_neither_supported_nor_negative"],"RESIDUAL_CLOSURE")
    hits[domain,a,k]=h
    report.append({"domain":domain,"arm":a,"k_per_scope":k,"cases":len(ids),"reference_case_denominator":len(den),"reference_hit_cases":len(h),
     "reference_hit_fraction":len(h)/len(den) if den else None,**dict(stat)})
  for a in ARMS:
   seq=[hits[domain,a,k] for k in KS];require(all(x<=y for x,y in zip(seq,seq[1:])),"NONMONOTONE_HIT")
 paired=[]
 for domain,u in (("ORIGINAL",original),("EXTENSION",extension)):
  d={i for i in ids if pos[i]&u};h=hits[domain,"SOURCE_SPARSE",12]
  for a in ARMS[1:]:
   g=hits[domain,a,12]
   paired.append({"domain":domain,"k_per_scope":12,"primary":"SOURCE_SPARSE","comparator":a,"reference_case_denominator":len(d),
    "both_hit":len(h&g),"primary_only":len(h-g),"comparator_only":len(g-h),"neither_hit":len(d-(h|g)),
    "paired_hit_difference":(len(h)-len(g))/len(d) if d else None})
 outscope=sum(len(p-(original|extension)) for p in pos.values())
 return {"sensitivity_excluding_related":sensitivity,"metrics":report,"paired_at12":paired,
  "supported_outside_frozen_universes":outscope,"scientific_precision_recall":"NOT_ESTIMABLE","scientific_mapping_release":False},per
