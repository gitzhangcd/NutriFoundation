#!/usr/bin/env python3
"""A2.8 post-freeze local developmental comparison; never re-run A2.6 or claim Gold."""
import sys,json,collections
from pathlib import Path
from a28_prepare import B,P,OUT,snap,j,sha,canon,save,need,PINS,SCOPES
from a28_generate import DEST,CONTRACT,ARMS
EV=B/"candidate_recovery_evaluation_001"
ALL=("H0",)+ARMS
KS=(1,3,5,12,"POOL")
def supported(x):return x["relation"] in {"EXACT","CLOSE","BROADER_TARGET","NARROWER_TARGET","RELATED","CONDITIONAL"} and x["applicability"]!="UNRESOLVED"
def nonrelated(x):return supported(x) and x["relation"]!="RELATED" and x["applicability"]!="RELATED_ONLY"
def idx(rows):
 d={(r["review_id"],r["scope"],r["arm"]):r for r in rows}
 need(len(d)==len(rows),"RANK_DUP");return d
def main(receipt_sha):
 need(not EV.exists(),"OUTPUT_EXISTS")
 # Candidate freeze is opened and verified before any historical reference.
 fr=j(DEST/"CandidateFreezeReceipt.json",receipt_sha)
 need(fr["status"]=="PASS_SOURCE_ONLY_FACTORIAL_RANK_FREEZE" and fr["reference_outputs_read"]==0 and fr["historical_rank_outputs_read"]==0 and fr["rank_groups"]==816,"FREEZE")
 ct=j(CONTRACT,fr["contract_sha256"]);need(ct["status"]=="FROZEN_DEVELOPMENT_ONLY","CONTRACT")
 for p,h in ct["code_sha256"].items():snap(p,h)
 for p,h in fr["input_sha256"].items():snap(p,h)
 ranks=[json.loads(x) for x in snap(DEST/"PrivateRanks.jsonl",fr["rank_sha256"]).splitlines()]
 qr=j(OUT/"QueryFreezeReceipt.json",fr["query_receipt_sha256"])
 q=j(OUT/"PrivateQueryViews51.json",qr["private_query_views_sha256"])
 cohorts={c:{x["review_id"] for x in q["queries"] if x["cohort"]==c} for c in ("EXPOSED19","EXPOSED32")}
 need(len(cohorts["EXPOSED19"])==19 and len(cohorts["EXPOSED32"])==32 and not cohorts["EXPOSED19"]&cohorts["EXPOSED32"],"COHORT")
 ids=set.union(*cohorts.values());budgets={(x["review_id"],x["scope"]):x["pool_budget"] for x in q["budgets"]}
 u=j("runs/B2/U3-B/C2/R2/real_001/controller_private/FrozenTargetUniverse.json","311ce55e814aae9ea473609811b9be621f42d52bf2eedf68fcca610adb6f8163")
 o=set(map(tuple,u["original"]));e=set(map(tuple,u["extension"]));by={s:{t for t in o if t[0]==s} for s in SCOPES[:3]};by[SCOPES[3]]=e
 need(len(o)==28845 and len(e)==1174 and not o&e,"UNIVERSE")
 new=idx(ranks);need(set(new)=={(i,s,a) for i in ids for s in SCOPES for a in ARMS},"NEW_GROUPS")
 # Historical H0 from the exact 19 replay and 32 sealed import.
 drec=j(P/"A1/retrieval_replay_001/RetrievalReplayReceipt.json","0de511fe7b673810ec3f8042c2511827e0f1313608cdb05fd9dcc64e30b3dba2")
 drows=[json.loads(x) for x in snap(P/"A1/retrieval_replay_001/Ranks.jsonl",drec["output_sha256"]["Ranks.jsonl"]).splitlines()]
 ir=j(B/"comparison_import_001/ImportReceipt.json","2a3309d40fe9b18d9d96a7999e43241253abee7fdb0939ae08beda36434220b8")
 bundle=j(B/"comparison_import_001/PrivateComparisonInputBundle.json",ir["private_bundle_sha256"])
 need(set(bundle["expected_ids"])==cohorts["EXPOSED32"],"IMPORT_CASES")
 hrows=[{**r,"arm":"H0"} for r in drows+bundle["ranks"] if r["arm"]=="BASELINE_FUSION"]
 historical=idx(hrows);need(set(historical)=={(i,s,"H0") for i in ids for s in SCOPES},"HIST_GROUPS")
 rank_index={**new,**historical}
 for (i,s,a),r in rank_index.items():
  t=list(map(tuple,r["targets"]));need(r["pool_budget"]==budgets[i,s] and len(t)==len(set(t))<=budgets[i,s] and set(t)<=by[s],"CANDIDATE_CONTRACT")
 # Preserve source identities of both reference systems; no comparison of raw references across cohorts.
 p1=P.parent/"P1/real_001"
 f=j(p1/"P1FreezeReceipt.json","4f8a6402bc4a34e5e1058670c735bbf78aabef26c949b3e6dc6a53c9fc630ae5")
 cpath=P.parent/"Reference44_Gemini_001"
 cr=j(cpath/"CriticFreezeReceipt.json",f["critic_receipt_sha256"])
 need(cr["status"]=="REVIEW_FROZEN" and cr["completed_cases"]==44,"DEV19_REF")
 refs19=[json.loads(x) for x in snap(cpath/"ReviewRecords.jsonl",cr["output_file_hashes"]["ReviewRecords.jsonl"]).splitlines()]
 refs={x["review_id"]:x for x in refs19 if x["review_id"] in cohorts["EXPOSED19"]}
 refs.update({x["review_id"]:x for x in bundle["references"]})
 need(set(refs)==ids,"REFERENCE_CLOSURE")
 qix={x["review_id"]:x for x in q["queries"]}
 for i,r in refs.items():need(r["source_ref"]==qix[i]["source_ref"] and r["scientific_reference_qualified"] is False,"REFERENCE_IDENTITY")
 # Independent 19 baseline support membership cross-check against the earlier frozen P1 edge attribution.
 gap=[json.loads(x) for x in snap(p1/"private/ReferenceGapAttribution.jsonl",f["output_file_hashes"]["private/ReferenceGapAttribution.jsonl"]).splitlines()]
 gset={(x["review_id"],tuple(x["target_key"])) for x in gap if x["review_id"] in cohorts["EXPOSED19"] and x["domain"]=="ORIGINAL"}
 pset={(i,tuple(x["target_key"])) for i in cohorts["EXPOSED19"] for x in refs[i]["independent_candidates"] if supported(x) and tuple(x["target_key"]) in o}
 need(gset==pset and len(pset)==43,"DEV19_REFERENCE_PIN")
 metrics=[];private=[];bridge={};factorial=[];paired=[]
 for c,cs in cohorts.items():
  h_exact=0;h_sets=0;inter=0;union=0
  for i in cs:
   for s in SCOPES:
    x=list(map(tuple,rank_index[i,s,"H0"]["targets"]));y=list(map(tuple,rank_index[i,s,"G0"]["targets"]))
    h_exact+=x==y;h_sets+=set(x)==set(y);inter+=len(set(x)&set(y));union+=len(set(x)|set(y))
  bridge[c]={"groups":len(cs)*4,"identical_sequences":h_exact,"identical_candidate_sets":h_sets,"micro_candidate_jaccard":inter/union if union else None}
  modes=["RAW_PRIMARY","RAW_NONRELATED"]+(["CONSERVATIVE_SECONDARY"] if c=="EXPOSED32" else [])
  for mode in modes:
   pos={};neg={};reviewed={}
   for i in cs:
    r=refs[i];p0={tuple(x["target_key"]) for x in r["independent_candidates"]};n0={tuple(x["target_key"]) for x in r["hard_negatives"]}
    need(len(p0)==len(r["independent_candidates"]) and len(n0)==len(r["hard_negatives"]) and not p0&n0,"REF_SET")
    pos[i]={tuple(x["target_key"]) for x in r["independent_candidates"] if (supported(x) if mode=="RAW_PRIMARY" else nonrelated(x))}
    neg[i]={tuple(x["target_key"]) for x in r["hard_negatives"] if not(mode=="CONSERVATIVE_SECONDARY" and x["conflict_type"] in ("TARGET_SPECIFIC_CONDITION","UNRESOLVED_OTHER"))};reviewed[i]=p0|n0
   for domain,universe,scopes in [("ORIGINAL",o,SCOPES[:3]),("EXTENSION",e,SCOPES[3:])]:
    den={i for i in cs if pos[i]&universe};edges=sum(len(pos[i]&universe) for i in cs);hits={}
    for a in ALL:
     for k in KS:
      z=collections.Counter();h=set()
      for i in sorted(cs):
       cand={tuple(t) for s in scopes for t in (rank_index[i,s,a]["targets"] if k=="POOL" else rank_index[i,s,a]["targets"][:k])}
       p=pos[i]&universe;n=neg[i]&universe
       hit=bool(cand&p)
       if hit:h.add(i)
       z["candidate_edges"]+=len(cand);z["reference_edges_hit"]+=len(cand&p);z["negative_overlap"]+=len(cand&n);z["unreviewed_edges"]+=len(cand-reviewed[i]);z["reviewed_neither"]+=len((cand&reviewed[i])-p-n);z["cases_with_candidates"]+=bool(cand)
       private.append({"cohort":c,"report":mode,"domain":domain,"arm":a,"k":k,"review_id":i,"has_reference":bool(p),"hit":hit,"reference_edges":len(p),"reference_hits":len(cand&p),"negative_overlap":len(cand&n),"candidate_edges":len(cand)})
      need(z["candidate_edges"]==sum(z[t] for t in ("reference_edges_hit","negative_overlap","unreviewed_edges","reviewed_neither")),"METRIC_CLOSURE")
      hits[a,k]=h
      metrics.append({"cohort":c,"report":mode,"domain":domain,"arm":a,"k":k,"cases":len(cs),"reference_cases":len(den),"reference_edges":edges,"hit_cases":len(h),"reference_hit_fraction":len(h)/len(den) if den else None,**dict(z)})
     need(all(hits[a,x]<=hits[a,y] for x,y in zip(KS,KS[1:])),"MONOTONE")
    for k in (12,"POOL"):
     f0,f1,f2,f3=[len(hits[a,k]) for a in ARMS]
     factorial.append({"cohort":c,"report":mode,"domain":domain,"k":k,"denominator":len(den),"query_only_delta_cases":f1-f0,"target_only_delta_cases":f2-f0,"query_delta_with_multisurface":f3-f2,"target_delta_with_reconstructed_query":f3-f1,"joint_delta_cases":f3-f0,"interaction_delta_cases":f3-f2-f1+f0})
     for a,b in (("G1","G0"),("G2","G0"),("G3","G0"),("G3","G2"),("G3","G1")):
      x,y=hits[a,k],hits[b,k]
      paired.append({"cohort":c,"report":mode,"domain":domain,"k":k,"treatment":a,"control":b,"both":len(x&y),"treatment_only":len(x-y),"control_only":len(y-x),"neither":len(den-(x|y))})
 # Reconcile H0 against already observed history before writing new results.
 for c,hits,edges,den in [("EXPOSED19",4,4,18),("EXPOSED32",7,11,22)]:
  z=next(x for x in metrics if x["cohort"]==c and x["report"]=="RAW_PRIMARY" and x["domain"]=="ORIGINAL" and x["arm"]=="H0" and x["k"]=="POOL")
  need((z["hit_cases"],z["reference_edges_hit"],z["reference_cases"])==(hits,edges,den),"H0_RECONCILIATION")
 z=next(x for x in metrics if x["cohort"]=="EXPOSED32" and x["report"]=="RAW_PRIMARY" and x["domain"]=="ORIGINAL" and x["arm"]=="H0" and x["k"]==12)
 need((z["hit_cases"],z["reference_edges_hit"],z["negative_overlap"])==(5,7,13),"H0_TOP12")
 need(len(metrics)==250 and len(factorial)==20 and len(paired)==100 and len(private)==6700,"OUTPUT_CLOSURE") # 19*2*2*5*5 + 32*3*2*5*5
 for p,h in PINS.items():need(sha(Path(p).read_bytes())==h,"POST_DRIFT")
 EV.mkdir(mode=0o700)
 result={"status":"PASS_BOUNDED_DEVELOPMENT_FACTORIAL_COMPARISON","metrics":metrics,"factorial":factorial,"paired":paired,"historical_bridge":bridge,"scientific_precision_recall":"NOT_ESTIMABLE","mapping_release":0,"new_confirmation_set":False}
 ah=save(EV/"AggregateComparison.json",result);ph=save(EV/"PrivateCaseComparison.jsonl",b"".join(canon(x) for x in private))
 r={"status":result["status"],"candidate_receipt_sha256":receipt_sha,"aggregate_sha256":ah,"private_case_sha256":ph,"metric_rows":len(metrics),"factorial_rows":len(factorial),"paired_rows":len(paired),"private_case_rows":len(private),"input_sha256":PINS,"old_experiments_modified":False,"scientific_reference_qualified":False,"mapping_release":0}
 h=save(EV/"EvaluationReceipt.json",r)
 # Summaries only; no case identifiers.
 print(json.dumps({"receipt_sha256":h,"aggregate_sha256":ah,"counts":{k:r[k] for k in ("metric_rows","factorial_rows","paired_rows","private_case_rows")},"historical_bridge":bridge,"original_primary":[x for x in metrics if x["domain"]=="ORIGINAL" and x["report"]=="RAW_PRIMARY" and x["k"] in (12,"POOL")],"original_primary_factorial":[x for x in factorial if x["domain"]=="ORIGINAL" and x["report"]=="RAW_PRIMARY"]},ensure_ascii=False,separators=(",",":")))
if __name__=="__main__":main(sys.argv[1])
