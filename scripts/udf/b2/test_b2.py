#!/usr/bin/env python3
"""B2 persisted-candidate conformance and bounded source replay, no scientific Gold."""
import argparse,copy,json,pathlib as P,collections as C,sys,re
from vocabulary import *
from alignment import *
from run_b2 import validate_objects,guard_component,guard_code,closure_check

def read_jsonl(p):
 with p.open(encoding="utf8") as h:return [json.loads(l) for l in h]
def main(root,run):
 root=root.resolve();run=run.resolve();private=run/"private";tbl=private/"typed_collections"
 m=load(private/"collection_manifest.json");objects=[];by={}
 require(set(m)=={p.name for p in tbl.glob("*.jsonl")},"COLLECTION_SET")
 for n,v in sorted(m.items()):
  p=tbl/n;require(p.stat().st_size==v["bytes"] and sha(p)==v["sha256"],"COLLECTION_HASH")
  rows=read_jsonl(p);require(len(rows)==v["rows"] and all(o["kind"]==p.stem for o in rows),"COLLECTION_GRAIN")
  by[p.stem]=rows;objects+=rows
 idx=validate_objects(objects)
 rpt=load(run/"B2RunReport.json")
 require(len(idx)==rpt["typed_objects"]==rpt["persisted_roundtrips"],"REPORT_COUNT")
 # Fresh source extraction independent of stored JSONL values (same extraction implementation).
 v=Inventory(root).run();prior={o["object_id"]:o["payload"] for o in by["NativeVocabularyRecord"]}
 def strip_anchor(p):return {k:x for k,x in p.items() if k!="source_anchor_ref"}
 require(len(prior)==len(v.records) and {o["object_id"] for o in v.records}==set(prior),"NATIVE_ID_DRIFT")
 require(all(canon(strip_anchor(o["payload"]))==canon(strip_anchor(prior[o["object_id"]])) for o in v.records),"NATIVE_SOURCE_REPLAY_DRIFT")
 native=by["NativeVocabularyRecord"];scopes=C.defaultdict(list)
 for o in native:scopes[o["payload"]["native_namespace"]].append(o)
 # Every held short code and same-release crosswalk rechecked by validate_objects.
 code=by["NativeCodeLinkCandidate"];cross=by["FNDDSCarrierCrosswalk"]
 require(len(code)==4761 and sum(o["payload"]["status"]=="SAME_CYCLE_CODE_MATCH_CANDIDATE" for o in code)==4640,"SNAPME_CODE_COUNTS")
 require(len(cross)==8690,"FNDDS_CROSSWALK_COUNTS")
 # Recheck all candidate endpoint closure, and re-run a stratified bounded subset of retrieval.
 edges=by["AlignmentRecord"];groups=C.defaultdict(list)
 for e in edges:
  p=e["payload"];t=idx[p["target_ref"]]["payload"]["native_namespace"];groups[t].append(e)
 replayed=0
 for t,g in sorted(groups.items()):
  ix=Index(scopes[t])
  for e in spread(g,min(12,len(g))):
   p=e["payload"];res=ix.rank(p["query_form"])
   match=[(i,r) for i,r in enumerate(res,1) if ref(r["target"])==p["target_ref"]]
   require(len(match)==1 and match[0][0]==p["rank"] and match[0][1]["score"]==p["ranking_score"] and match[0][1]["matched_form"]==p["matched_target_form"],"CANDIDATE_RANK_REPLAY")
   replayed+=1
 routes=read_jsonl(private/"CandidateQueryRoutes.jsonl");blind=load(private/"ReviewSourceOnlyQueue.json");hidden=load(private/"ReviewCandidatesHidden.json")
 require(len(routes)==rpt["alignment_queries"] and sum(len(x["candidate_refs"]) for x in routes)==len(edges),"QUERY_EDGE_COUNT")
 require(len({r["source_ref"] for r in routes})==len(routes),"QUERY_DUPLICATE")
 for r in routes:
  require(r["candidate_count"]==len(r["candidate_refs"]),"QUERY_COUNT")
  for x in r["candidate_refs"]:require(idx[x]["payload"]["source_ref"]==r["source_ref"],"QUERY_EDGE_SOURCE")
 require(len(blind)==len(hidden)==rpt["review_queue"] and {x["review_id"] for x in blind}=={x["review_id"] for x in hidden},"REVIEW_PAIR")
 require(all("candidate_refs" not in x and "ranking_score" not in x and x["status"]=="NOT_REVIEWED" for x in blind),"REVIEW_EXPOSURE")
 require(closure_check(v.foodon_edges,set(v.foodon_classes))==rpt["foodon_asserted_dag_nodes"],"FOODON_DAG_REPLAY")
 # Actual semantic conflict examples are used for mutation tests; toy examples labeled synthetic.
 e=edges[0];p=e["payload"];c=by["ComponentAlignmentCandidate"][0]["payload"];short=next(o["payload"] for o in code if o["payload"]["status"]=="HOLD_CODE_DOMAIN_UNRESOLVED")
 families=by["SourceFamily"];f=families[0]["payload"];x=copy.deepcopy(f);x["independence_status"]="INDEPENDENCE_VERIFIED_FOR_TASK"
 tests=[]
 def pos(name,fn):
  try:fn();tests.append({"test":name,"expected":"ACCEPT","observed":"ACCEPT","pass":True})
  except Exception as e:tests.append({"test":name,"expected":"ACCEPT","observed":type(e).__name__+":"+str(e)[:100],"pass":False})
 def neg(name,err,fn):
  try:fn();tests.append({"test":name,"expected":err,"observed":"ACCEPT","pass":False})
  except ContractError as e:tests.append({"test":name,"expected":err,"observed":str(e),"pass":str(e)==err})
  except Exception as e:tests.append({"test":name,"expected":err,"observed":type(e).__name__+":"+str(e)[:100],"pass":False})
 pos("all persisted records, anchors, refs and candidates validate",lambda:require(len(idx)==rpt["typed_objects"],"COUNTS"))
 pos("fresh source-native vocabulary replay",lambda:require(len(v.records)==len(prior),"COUNTS"))
 pos("source-aware ranked subset replay",lambda:require(replayed>0,"RANK"))
 pos("real mapping remains unreviewed candidate",lambda:mapping_guard(p))
 pos("real component remains unreviewed candidate",lambda:guard_component(c))
 pos("native FNDDS links and short-code quarantine",lambda:guard_code(short))
 pos("synthetic lexical exact surface query",lambda:require(normalize("Apple_Pie")==normalize("apple pie"),"NORMALIZE"))
 pos("synthetic qualifiers retained",lambda:require(normalize("apple raw")!=normalize("apple cooked") and bool(hard_conflicts("apple raw","apple cooked")),"QUALIFIERS"))
 pos("FoodOn asserted graph is acyclic in selected nodes",lambda:closure_check(v.foodon_edges,set(v.foodon_classes)))
 pos("review queue source-only fields, candidate list separate",lambda:require(all("candidate_refs" not in q for q in blind),"REVIEW"))
 def mut(base,**kw):a=copy.deepcopy(base);a.update(kw);return a
 neg("lexical match promoted to exact","UNREVIEWED_EQUIVALENCE",lambda:mapping_guard(mut(p,relation_type="EXACT",accepted_equivalence=True)))
 neg("candidate directional relation promoted in secondary field","UNREVIEWED_EQUIVALENCE",lambda:mapping_guard(mut(p,source_relation_to_target="EXACT")))
 neg("direction swapped without contract","RELATION_DIRECTION",lambda:mapping_guard(mut(p,direction="TARGET_RELATION_TO_SOURCE")))
 neg("score treated as probability","UNQUALIFIED_RELEASE_OR_SCORE",lambda:mapping_guard(mut(p,score_interpretation="CORRECTNESS_PROBABILITY")))
 neg("invalid rank score","INVALID_RANK_SCORE",lambda:mapping_guard(mut(p,ranking_score=1.2)))
 neg("same name promotes physical instance","INSTANCE_PROMOTION",lambda:mapping_guard(mut(p,physical_instance_link=True)))
 neg("state conflict not routed RED","HARD_CONFLICT_NOT_HELD",lambda:mapping_guard(mut(p,hard_conflicts=["raw<>cooked"],review_route="AMBER")))
 neg("candidate admitted training without review","UNQUALIFIED_RELEASE_OR_SCORE",lambda:mapping_guard(mut(p,permitted_purposes=["TRAIN"])))
 neg("component equivalence without authority","COMPONENT_EQUIVALENCE_NOT_QUALIFIED",lambda:guard_component(mut(c,accepted_equivalence=True,relation_type="EXACT")))
 neg("component unit conversion without basis","COMPONENT_CONVERSION_HOLD",lambda:guard_component(mut(c,conversion="AUTHORIZED")))
 neg("component unit conflict not held","UNIT_CONFLICT_NOT_HELD",lambda:guard_component(mut(c,unit_dimension_candidate_match=False,review_route="AMBER")))
 neg("same source family counted twice","DEPENDENT_SOURCE_FAMILY",lambda:independent_guard([x,x]))
 neg("unknown source lineage counted independently","INDEPENDENCE_NOT_QUALIFIED",lambda:independent_guard([f]))
 neg("short code padded into FNDDS foreign key","SHORT_CODE_JOIN",lambda:guard_code(mut(short,target_fdc_ref="invented")))
 neg("cross-cycle FNDDS join","FNDDS_CYCLE_OR_GRAIN",lambda:guard_code(mut(short,target_cycle="2021-23")))
 neg("same survey food code used as physical intake identity","FNDDS_CYCLE_OR_GRAIN",lambda:guard_code(mut(short,same_physical_instance=True)))
 neg("candidate native code releases intake aggregation","FNDDS_CYCLE_OR_GRAIN",lambda:guard_code(mut(short,measurement_and_aggregation="RELEASED")))
 neg("hierarchy circular dependency","ONTOLOGY_CYCLE",lambda:closure_check([("a","b"),("b","a")],{"a","b"}))
 def tamper_revision():
  z=copy.deepcopy(e);z["payload"]["rank"]=999;verify_obj(z)
 neg("unsealed candidate revision change","REVISION_MISMATCH",tamper_revision)
 def unauthorized_release():
  z=copy.deepcopy(e);z["release_status"]="RELEASED";z.pop("revision_id");z["revision_id"]=digest(z);verify_obj(z)
 neg("resealed released candidate","RELEASE_BLOCKED",unauthorized_release)
 def closure(o):
  seen={}
  def add(r):
   if r in seen:return
   a=idx[r];seen[r]=a
   for rr in a["provenance_refs"]+a["dependency_refs"]:add(rr)
  for r in o["provenance_refs"]+o["dependency_refs"]:add(r)
  return list(seen.values())
 def mutated_obj(o,fn):
  z=copy.deepcopy(o);fn(z);z.pop("revision_id");z["revision_id"]=digest(z);return validate_objects(closure(o)+[z])
 neg("resealed source/target grain mismatch","MAPPING_NAMESPACE_GRAIN",lambda:mutated_obj(e,lambda z:z["payload"].update(source_grain="FOOD_INSTANCE")))
 neg("resealed candidate made real observation","REAL_CONSTRUCTION_INFLATION",lambda:mutated_obj(e,lambda z:z.update(instance_class="REAL_SOURCE_GROUNDED")))
 n=native[0]
 neg("source anchor locator forged and resealed","VOCAB_ANCHOR_MISMATCH",lambda:mutated_obj(n,lambda z:z["payload"].update(source_locator={"line":-1})))
 fdcross=cross[0]
 neg("same-release carriers claimed independent","CARRIER_INDEPENDENCE_INFLATION",lambda:mutated_obj(fdcross,lambda z:z["payload"].update(same_release_not_independent=False)))
 report={"run_id":"B2-U3A-VALIDATION","new_objects_validated":len(idx),"native_source_records_replayed":len(v.records),"stratified_rank_edges_replayed":replayed,
    "fndds_crosswalks_rechecked":len(cross),"snapme_code_links_rechecked":len(code),"review_queue_source_only_pairs_checked":len(blind),
    "total":len(tests),"positive":sum(t["expected"]=="ACCEPT" for t in tests),"negative":sum(t["expected"]!="ACCEPT" for t in tests),"passed":sum(t["pass"] for t in tests),"failed":sum(not t["pass"] for t in tests),"tests":tests,
    "scientific_mapping_precision_recall":"NOT_MEASURED","qualification":"DEVELOPMENT_ONLY"}
 write_json(run/"ContractValidationReport.json",report)
 print(json.dumps({k:v for k,v in report.items() if k!="tests"},ensure_ascii=False),flush=True)
 for t in tests:
  if not t["pass"]:print("FAIL",t)
 require(report["failed"]==0,"B2_CONTRACT_TEST_FAILED")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=P.Path,default=P.Path("."));p.add_argument("--run",type=P.Path,required=True);a=p.parse_args();main(a.root,a.run)
