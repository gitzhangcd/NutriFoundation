#!/usr/bin/env python3
"""A2.7 retrospective local mechanism trace of frozen, already unblinded development evidence.
No import/scorer rerun, new embedding inference, parameter changes, or release.
Deterministically trace the existing sparse and RRF ranking functions in memory and
verify exact agreement with the sealed ranks. Save only new diagnostic artifacts.
"""
import sys,hashlib,json,re,os,collections
from pathlib import Path
from collections import Counter,defaultdict
ROOT=Path.cwd().resolve()
B=Path("runs/B2/U3-B/C2/R2/P2/A2")
P=B.parent; A1=P/"A1"; IMP=B/"comparison_import_001"; SCORE=B/"comparison_score_001"; D=B/"generalization_diagnosis_001"
P1=B/"qualification_p1_001"; P2=B/"comparison_preparation_001"
ARMS=("BASELINE_FUSION","SOURCE_SPARSE","HYBRID")
SCOPES=("FoodOn","FDC_SR_Legacy","FNDDS","FOODON_EXTENSION")
READS={}
def need(ok,code):
 if not ok:raise ValueError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def snap(p,expected):
 p=Path(p);f=ROOT/p
 need(not p.is_absolute() and ".." not in p.parts and f.is_file() and not f.is_symlink() and f.resolve().is_relative_to(ROOT),"INPUT_PATH")
 raw=f.read_bytes()
 need(sha(raw)==expected,"PIN_DRIFT:"+str(p))
 need(str(p) not in READS or READS[str(p)]==expected,"PIN_REPEAT")
 READS[str(p)]=expected
 return raw
def j(p,h):return json.loads(snap(p,h))
def js(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
def save(p,b):
 if not isinstance(b,bytes):b=js(b)
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,"wb") as f:f.write(b);f.flush();os.fsync(f.fileno())
def keyed(items,field):
 d={x[field]:x for x in items};need(len(d)==len(items),"DUPLICATE_ID");return d
def scope(t,o,e):
 if t in e:return "FOODON_EXTENSION"
 if t in o:return t[0]
 return "OUTSIDE"
def support(x):return x["relation"] in {"EXACT","CLOSE","BROADER_TARGET","NARROWER_TARGET","RELATED","CONDITIONAL"} and x["applicability"]!="UNRESOLVED"
def sensitivity(x):return support(x) and x["relation"]!="RELATED" and x["applicability"]!="RELATED_ONLY"
def stage(rank):
 return "POOL_MISS" if rank is None else ("TOP12" if rank<=12 else "BELOW_TOP12")
def prof(qs):
 c=Counter();by=defaultdict(Counter)
 for q in qs:
  x={"cases":1,"identity_nonempty":bool(q["identity_tokens"]),"qualifier_nonempty":bool(q["qualifier_tokens"]),"alias_nonempty":bool(q["alias_tokens"]),"component_nonempty":bool(q["component_tokens"]),"label_span_nonempty":bool(q["label_hypotheses"]),"untranslated_cjk_residual":bool(re.search(r"[\u3400-\u9fff]",q["untranslated_label_residual"])),"no_query_tokens":not(q["identity_tokens"] or q["qualifier_tokens"] or q["alias_tokens"] or q["component_tokens"])}
  for k,v in x.items():c[k]+=int(v);by[q["source_kind"]][k]+=int(v)
 return {"all":dict(c),"by_source_kind":dict(by)}
def main():
 need(not (ROOT/D).exists(),"OUTPUT_EXISTS")
 ir=j(IMP/"ImportReceipt.json","2a3309d40fe9b18d9d96a7999e43241253abee7fdb0939ae08beda36434220b8")
 sr=j(SCORE/"ScoringReceipt.json","002d58501b9ead98ff202e051e947cdf061e49ac03d800a60bf675fe85797710")
 val=j(B/"comparison_score_validation_001/A26P2PostScoringReceipt.json","36df2db239678c36759502369682c4ba77cd1bab046022d65e0b5e3d0934f9d1")
 need(sr["comparison_executed"] and sr["mapping_release"]==0 and sr["scientific_reference_qualified"] is False and sr["import_receipt_sha256"]==READS[str(IMP/"ImportReceipt.json")] and val["scoring_receipt_sha256"]==READS[str(SCORE/"ScoringReceipt.json")],"SCORING_LINEAGE")
 agg=j(SCORE/"AggregateReports.json",sr["output_sha256"]["AggregateReports.json"])
 # Verify the private output as bytes; do not re-run official scoring.
 snap(SCORE/"PrivatePerCaseReports.json",sr["output_sha256"]["PrivatePerCaseReports.json"])
 bundle=j(IMP/"PrivateComparisonInputBundle.json",ir["private_bundle_sha256"])
 need(bundle["version"]=="A2.6-P1-SEALED-IMPORT-v0.1" and bundle["scoring_authorized"] is False and bundle["mapping_release"] is False,"SEALED_SCOPE")
 ct=j(P2/"A26P2AdmissionContract.json","bd8b2ba439f5f48a651e944f1a1f30e2ae4217b4b0efc3e9b740ba4957b6b6e3")
 old=j(P1/"A26P1ImportContract.json","9abd0c2b1a8a08be58562e7464d607f7a4477f3d375286fb315d094d617fa440")
 for p,h in {**old["code_sha256"],**ct["new_code_sha256"]}.items():snap(p,h)
 pol=j("configs/udf/u3r2p2a1/RetrievalPolicyFreeze_v0.1.json","58c53ab63cf4ac25d030d78e03dcdded8a51fb5a5802e7623ee75bd93af5ddc6")
 for p,h in pol["pins"].items():snap(p,h)
 a1=j(A1/"dev_001/A1FreezeReceipt.json","ff1ca4b3f86c2cecaff738fc57776bc12ca059b620016642cfd788a22f8ca1f6")
 snap("src/u3c1/run_c1.py",a1["input_fences"]["src/u3c1/run_c1.py"])
 devrec=j(A1/"retrieval_replay_001/RetrievalReplayReceipt.json","0de511fe7b673810ec3f8042c2511827e0f1313608cdb05fd9dcc64e30b3dba2")
 devq=[json.loads(x) for x in snap(A1/"retrieval_replay_001/QueryHypotheses.jsonl",devrec["output_sha256"]["QueryHypotheses.jsonl"]).splitlines()]
 devr=[json.loads(x) for x in snap(A1/"retrieval_replay_001/Ranks.jsonl",devrec["output_sha256"]["Ranks.jsonl"]).splitlines()]
 need(len(devq)==19 and len(devr)==228 and devrec["source_only"] and not devrec["reviewer_results_read"],"DEV_REPLAY")
 devrep=j(P/"portable_v2_001/P2DevelopmentReport.json","8b66b25c64e1bed0e2856b0c0229f0e8e28f200be2a1f15801baa3fc6a03ab88")
 devfreeze=j(P/"portable_v2_001/CandidateFreeze.json",a1["input_fences"][str(P/"portable_v2_001/CandidateFreeze.json")])
 need(devrec["output_sha256"]["Ranks.jsonl"]==devfreeze["private_hashes"]["Ranks.jsonl"] and devrec["output_sha256"]["QueryHypotheses.jsonl"]==devfreeze["private_hashes"]["QueryHypotheses.jsonl"],"DEV_REPLAY_ORIGINAL")
 prep=j(B/"local_001/PreparationFreeze.json","38b36cd2e44d5c538ad8a18bf560229532cf06e46dc58a36c870c4b9ac1be1f4")
 packet=j(B/"local_001/controller_private/RetrievalInput32.json",prep["retrieval_packet_sha256"])
 need(len(packet["dense_rank_hints"])==3875 and not packet["reviewer_results_included"],"HINTS")
 ret=j(B/"local_001/A2RetrievalFreezeReceipt.json","cc43ec13416ddf6fb35ee960ba937e9606e184ce2e36ea2448fbdfaa524bff26")
 need(ret["prep_sha256"]==READS[str(B/"local_001/PreparationFreeze.json")] and ret["policy_sha256"]==READS["configs/udf/u3r2p2a1/RetrievalPolicyFreeze_v0.1.json"],"RETRIEVAL_LINEAGE")
 need(ir["reference_receipt_sha256"]=="024d90970fa5f7990952bc702e63b5591c5f01e65881c69f8ef338554e9a6834" and ir["retrieval_receipt_sha256"]==READS[str(B/"local_001/A2RetrievalFreezeReceipt.json")],"IMPORT_LINEAGE")
 lex=json.loads(snap(P/"private/DevelopmentLexicon_v0.1.json",pol["pins"][str(P/"private/DevelopmentLexicon_v0.1.json")]))
 need(len(lex)==72,"LEXICON_COUNT")
 # Import the frozen functions after checking their exact bytes. No generator CLI or scorer.
 sys.dont_write_bytecode=True
 sys.path.insert(0,str(ROOT/"src/u3r2p2"))
 sys.path.insert(0,str(ROOT/"src/u3r2p2a1"))
 import run_p2_portable_v2 as v2
 import source_only_retrieval as srank
 v2.set_lexicon(lex)
 ids=bundle["expected_ids"];queries=keyed(bundle["query_hypotheses"],"review_id");refs=keyed(bundle["references"],"review_id");src=keyed(packet["source_records"],"review_id")
 need(len(ids)==len(set(ids))==32 and set(ids)==set(queries)==set(refs)==set(src),"CASE_CLOSURE")
 need(not({x["source_ref"] for x in devq}&{q["source_ref"] for q in queries.values()}),"DEV_SOURCE_OVERLAP")
 for i in ids:
  need(v2.query(src[i])==queries[i],"QUERY_RECONSTRUCTION_DRIFT")
  need(refs[i]["source_ref"]==queries[i]["source_ref"] and refs[i]["native_kind"]==queries[i]["source_kind"],"REFERENCE_BINDING")
 o=set(map(tuple,bundle["original"]));e=set(map(tuple,bundle["extension"]))
 need(len(o)==28845 and len(e)==1174 and not o&e,"UNIVERSE")
 uf=j("runs/B2/U3-B/C2/R2/real_001/controller_private/FrozenTargetUniverse.json",pol["pins"]["runs/B2/U3-B/C2/R2/real_001/controller_private/FrozenTargetUniverse.json"])
 need(set(map(tuple,uf["original"]))==o and set(map(tuple,uf["extension"]))==e,"UNIVERSE_DRIFT")
 by={s:{k for k in o if k[0]==s} for s in SCOPES[:3]};by["FOODON_EXTENSION"]=e
 vocab,vc=v2.parse_standards(v2.Standards(ROOT));docs=v2.target_docs(ROOT,by,vocab);weights={s:v2.idfs(docs[s]) for s in SCOPES}
 hints=srank.check_packet(packet);need(len(hints)==128,"HINT_CLOSURE")
 rmap={(x["review_id"],x["scope"],x["arm"]):x for x in bundle["ranks"]}
 need(set(rmap)=={(i,s,a) for i in ids for s in SCOPES for a in ARMS} and len(bundle["ranks"])==384,"RANK_CLOSURE")
 budgets={(x["review_id"],x["scope"]):x["pool_budget"] for x in bundle["trusted_budgets"]};need(len(budgets)==128,"BUDGET_CLOSURE")
 pos=Counter();outscope=Counter();byrel=Counter();stages=defaultdict(Counter);scope_stage=defaultdict(Counter);sparse_fail=Counter();hybrid_fail=Counter()
 sparse_lex=defaultdict(Counter);hyb_lex=defaultdict(Counter);identity_groups=defaultdict(Counter);kind_groups=defaultdict(Counter);trace=[];rank_agree=0
 case_scope=defaultdict(lambda:defaultdict(set));edge_scope=defaultdict(lambda:defaultdict(set))
 for i in ids:
  q=queries[i];r=refs[i];allpos=[x for x in r["independent_candidates"] if support(x)]
  need(len({tuple(x["target_key"]) for x in allpos})==len(allpos),"REF_DUP")
  pc=Counter(scope(tuple(x["target_key"]),o,e) for x in allpos)
  pos["cases_with_any_support"]+=bool(allpos);pos["cases_with_original_support"]+=sum(pc[s] for s in SCOPES[:3])>0
  pos["cases_with_extension_support"]+=pc["FOODON_EXTENSION"]>0
  pos["cases_with_outside_support"]+=pc["OUTSIDE"]>0
  for x in allpos:
   t=tuple(x["target_key"]);s=scope(t,o,e);pos[s]+=1;byrel[x["relation"]]+=1
   if s=="OUTSIDE":
    native=vocab.get(v2.key(t[0],t[2]))
    need(native is not None and not native["deprecated"] and native["label"].strip()==x["target_native_label"].strip(),"OUTSIDE_NATIVE_MISSING")
    outscope[t[0]]+=1;outscope["all_native_present_nondeprecated"]+=1
    if sensitivity(x):outscope["nonrelated_edges"]+=1
    trace.append({"review_id":i,"target_key":list(t),"scope":"OUTSIDE","relation":x["relation"],"raw_native_standard_verified":True})
  stats={}
  for s in SCOPES:
   oldh=hints[i,s];cap=budgets[i,s];need(cap==len(oldh),"CAP_DRIFT")
   # Trace unchanged scores and rank order; no new model inference or persisted new ranking.
   scores=[]
   for d in docs[s]:
    v,_=v2.score(q,d,weights[s])
    if v>0:scores.append((d["key"],v))
   scores.sort(key=lambda x:(-x[1],x[0]));sparse=[x[0] for x in scores];sm={k:j+1 for j,k in enumerate(sparse)}
   oi={tuple(x["target_key"]):x for x in oldh}
   dense={k for k,x in oi.items() if x["label_rank"] or x["context_rank"]}
   prehyb=set(sparse[:20])|dense
   base=sorted(oi,key=lambda k:(oi[k]["frozen_pool_rank"] or 99999,-oi[k]["fusion_score"],k)) if s!="FOODON_EXTENSION" else sorted(oi,key=lambda k:(-oi[k]["fusion_score"],k))
   lists={"BASELINE_FUSION":base,"SOURCE_SPARSE":sparse[:cap],"HYBRID":v2.fused_rank(sparse,oldh,cap)}
   for a,ls in lists.items():
    need(ls==list(map(tuple,rmap[i,s,a]["targets"])) and cap==rmap[i,s,a]["pool_budget"],"RANK_REPLAY_DRIFT")
    rank_agree+=1
   idx={a:{t:j+1 for j,t in enumerate(ls)} for a,ls in lists.items()}
   stats[s]=bool(lists["SOURCE_SPARSE"])
   for x in allpos:
    t=tuple(x["target_key"])
    if scope(t,o,e)!=s:continue
    domain="EXTENSION" if s=="FOODON_EXTENSION" else "ORIGINAL"
    ranks={a:idx[a].get(t) for a in ARMS}
    for a,k in ranks.items():
     z=stage(k);stages[(domain,a)][z]+=1;scope_stage[(s,a)][z]+=1
     if k is not None:
      edge_scope[(domain,"POOL")][a].add((i,t));case_scope[(domain,"POOL")][a].add(i)
      if k<=12:edge_scope[(domain,"TOP12")][a].add((i,t));case_scope[(domain,"TOP12")][a].add(i)
    sp=sm.get(t)
    sr="NO_POSITIVE_LEXICAL_SCORE" if sp is None else ("POSITIVE_BEYOND_POOL_CAP" if sp>cap else ("RETAINED_BELOW_TOP12" if sp>12 else "TOP12"))
    hr=stage(ranks["HYBRID"]) if ranks["HYBRID"] is not None else ("RRF_CAP_EXCLUDED" if t in prehyb else "NOT_IN_FUSION_INPUT")
    sparse_lex[domain][sr]+=1;hyb_lex[domain][hr]+=1
    if domain=="ORIGINAL":sparse_fail[sr]+=1;hybrid_fail[hr]+=1
    trace.append({"review_id":i,"target_key":list(t),"scope":s,"relation":x["relation"],"ranks":ranks,"uncapped_sparse_rank":sp,"pool_cap":cap,"dense_input_member":t in dense,"sparse_top20_member":sp is not None and sp<=20,"sparse_mechanism":sr,"hybrid_mechanism":hr})
  for g in (identity_groups["IDENTITY_PRESENT" if q["identity_tokens"] else "IDENTITY_ABSENT"],kind_groups[q["source_kind"]]):
   g["cases"]+=1;g["original_sparse_has_candidates"]+=any(stats[s] for s in SCOPES[:3])
   g["original_reference_cases"]+=sum(pc[s] for s in SCOPES[:3])>0
   g["original_sparse_top12_hit"]+=i in case_scope["ORIGINAL","TOP12"]["SOURCE_SPARSE"]
   g["original_baseline_top12_hit"]+=i in case_scope["ORIGINAL","TOP12"]["BASELINE_FUSION"]
   g["original_hybrid_top12_hit"]+=i in case_scope["ORIGINAL","TOP12"]["HYBRID"]
 need(rank_agree==384 and len(trace)==111 and sum(pos[s] for s in SCOPES[:3])==100 and pos["FOODON_EXTENSION"]==1 and pos["OUTSIDE"]==10,"DIAGNOSIS_CLOSURE")
 # Cross-check diagnostic decomposition against original frozen aggregate, not a second official score.
 ncheck=0
 for x in agg["reports"]["RAW_PRIMARY"]["metrics"]:
  k=x["k_per_scope"];a=x["arm"];d=x["domain"]
  if k not in (12,"POOL"):continue
  typ="TOP12" if k==12 else "POOL"
  need(x["reference_edges_hit"]==len(edge_scope[d,typ][a]) and x["reference_hit_cases"]==len(case_scope[d,typ][a]),"AGGREGATE_DRIFT")
  ncheck+=1
 need(ncheck==12,"METRIC_CHECK_CLOSURE")
 for (d,a),z in stages.items():need(sum(z.values())==(100 if d=="ORIGINAL" else 1),"EDGE_STAGE_CLOSURE")
 def complement(sets):
  b=sets["BASELINE_FUSION"];h=sets["HYBRID"];s=sets["SOURCE_SPARSE"]
  return {"baseline_hybrid_shared":len(b&h),"baseline_only_vs_hybrid":len(b-h),"hybrid_only_vs_baseline":len(h-b),"sparse_baseline_shared":len(s&b),"sparse_only_vs_baseline":len(s-b),"all_arm_union_oracle":len(b|h|s),"none_of_three":None}
 overlap={}
 for typ in ("TOP12","POOL"):
  ce=complement(case_scope["ORIGINAL",typ]);ee=complement(edge_scope["ORIGINAL",typ])
  ce["none_of_three"]=pos["cases_with_original_support"]-ce["all_arm_union_oracle"]
  ee["none_of_three"]=100-ee["all_arm_union_oracle"]
  overlap[typ]={"cases":ce,"edges":ee}
 # Count observed raw reference relation types by target scope; no names.
 st={d:{a:dict(stages[d,a]) for a in ARMS} for d in ("ORIGINAL","EXTENSION")}
 summary={"version":"A2.7-LOCAL-DIAGNOSIS-v0.1","status":"PASS_RETROSPECTIVE_MECHANISM_DIAGNOSIS","cases":32,"dev_cases":19,"rank_groups_exactly_reproduced":rank_agree,"aggregate_hit_checks":ncheck,"query_coverage":{"exposed19":prof(devq),"reserved32_now_exposed":prof(queries.values())},"identity_groups":dict(identity_groups),"source_kind_groups":dict(kind_groups),"reference_distribution":dict(pos),"reference_relations":dict(byrel),"edge_stages":st,"edge_stages_by_scope":{s:{a:dict(scope_stage[s,a]) for a in ARMS} for s in SCOPES},"sparse_mechanism_by_domain":dict(sparse_lex),"hybrid_mechanism_by_domain":dict(hyb_lex),"outside_native_standard":dict(outscope),"method_complementarity_original":overlap,"dev19_original_pool":[{k:x[k] for k in ("arm","reference_edges_hit","reference_edges","reference_hit_cases","reference_cases","candidate_edges")} for x in devrep["metrics"] if x["k_per_scope"]=="POOL"],"native_standard_counts":vc,"limitations":["Retrospective diagnostic on exposed development data; reference is unqualified AI, not expert Gold.","Sparse positive-score/rank attribution is deterministic conditional on frozen lexicon/scorer/universe; no causal attribution to lexicon alone.","Union is a post-hoc unequal-budget oracle, not an evaluated method or a deployment guarantee.","Outside-universe edges present in raw standards; not proof of ontology absence; scope eligibility requires distinct scientific review.","No new retrieval parameters or embedding inference; no official scorer/import rerun; no data publication or mapping release."]}
 # Verify all pinned files unchanged, including code and both official scoring outputs.
 for p,h in list(READS.items()):need(sha((ROOT/p).read_bytes())==h,"POST_INPUT_DRIFT")
 dest=ROOT/D;dest.mkdir(mode=0o700)
 save(dest/"A27DiagnosticAggregate.json",summary)
 save(dest/"PrivateReferenceEdgeTrace.jsonl",b"".join(js(x) for x in trace))
 receipt={"version":"A2.7-DIAGNOSTIC-RECEIPT-v0.1","status":"PASS_RETROSPECTIVE_DIAGNOSIS","source_scoring_receipt_sha256":READS[str(SCORE/"ScoringReceipt.json")],"pinned_input_files":len(READS),"verified_rank_groups":rank_agree,"verified_aggregate_checks":ncheck,"reference_edge_trace_rows":len(trace),"input_hashes":READS,"output_sha256":{f.name:sha(f.read_bytes()) for f in dest.iterdir()},"diagnostic_script_sha256":sha(Path(__file__).read_bytes()),"official_scoring_rerun":False,"new_embedding_inference":False,"method_parameters_changed":False,"protected_records_exported":False,"scientific_reference_qualified":False,"mapping_release":0}
 save(dest/"A27DiagnosticReceipt.json",receipt)
 # stdout excludes every private key, label and individual record.
 print(json.dumps({"summary":summary,"receipt_sha256":sha((dest/"A27DiagnosticReceipt.json").read_bytes()),"aggregate_sha256":receipt["output_sha256"]["A27DiagnosticAggregate.json"],"pinned_input_files":len(READS)},ensure_ascii=False,separators=(",",":")))
if __name__=="__main__":main()
