#!/usr/bin/env python3
"""Independent persisted-output verification and bounded qualification gate.
No critic hidden outputs, no clinical/reference/measurement authorization.
"""
import argparse, pathlib as P, sys, copy, collections as C, math, json
sys.path.insert(0,str(P.Path(__file__).resolve().parents[2]/"src/u3b"))
from run_u3b import *
from runtime import verify
from admission import Admission
def main(root,profile,run,out):
 root=root.resolve();run=run.resolve();out=out.resolve()
 require(not out.exists() and out.is_relative_to(root/"runs/B2/U3-B") and not out.is_relative_to(run),"NEW_VERIFY_OUTPUT")
 p=readj(profile);rpt=readj(run/"U3BGeneratorReport.json");require(rpt["profile_sha256"]==sha(profile),"PILOT_PROFILE_DRIFT")
 b=p["baseline"];rt,r=verify(root,file(root,b["manifest"],b["manifest_sha256"]),root/b["run"]);adm=Admission(rt)
 priv=run/"private";tree=priv/"typed_partitions";m=readj(priv/"partition_manifest.json");require(sha(priv/"partition_manifest.json")==rpt["partition_manifest_sha256"],"PILOT_MANIFEST")
 require(set(m)=={str(f.relative_to(tree)) for f in tree.rglob("*.jsonl")},"PILOT_PARTITION_SET")
 schema=readj(run/"U3B_PilotContract.schema.json");require(canon(schema)==canon(make_schema(root)),"PILOT_SCHEMA_DRIFT")
 vs=validator(schema);by=C.defaultdict(list);registry=dict(rt.b.idx);rows=[];targets={}
 for path,v in sorted(m.items()):
  f=file(tree,path,v["sha256"]);require(f.stat().st_size==v["bytes"],"PILOT_FILE_SIZE");rr=list(lines(f));require(len(rr)==v["rows"],"PILOT_COUNT")
  for o in rr:
   rights=o["governance"]["rights_domains"];part=rights[0] if len(rights)==1 else "MIXED_RESTRICTED_"+digest(rights)[:16]
   require(path==part+"/"+o["kind"]+".jsonl","RIGHTS_PARTITION")
   require(ref(o) not in registry,"DUPLICATE_PILOT_REVISION");registry[ref(o)]=o;rows.append(o);by[o["kind"]].append(o)
 require(len(rows)==rpt["typed_objects"] and len(by["PilotMethod"])==1,"PILOT_OBJECT_COUNT")
 q=by["QueryContextRecord"];edges=by["SemanticCandidateRecord"];method=by["PilotMethod"][0]
 for row in q+edges:
  pay=row["payload"]
  for key in (("source_legacy_ref",) if row["kind"]=="QueryContextRecord" else ("source_legacy_ref","target_legacy_ref")):
   k=pay[key]
   if k not in targets:
    z=adm.view(k);targets[k]=z;registry[ref(z)]=z
 for o in rows:validate_obj(o,vs,registry)
 excluded=set()
 for x in p["excluded_queues"]:excluded|={z["source_ref"] for z in readj(file(root,x["path"],x["sha256"]))}
 require(len(excluded)==44 and not excluded&{x["payload"]["source_legacy_ref"] for x in q},"ORIGINAL_REVIEW_QUEUE_LEAKAGE")
 ctx=get_ctx(root,rt,[targets[o["payload"]["source_legacy_ref"]] for o in q],p)
 for o in q:
  z=o["payload"];v=ctx[z["source_ref"]]
  require(z["native_alias_raw"]==v["aliases"] and z["native_ingredient_names"]==v["ingredients"] and z["context_locator"]==v["locator"],"QUERY_CONTEXT_REPLAY")
 groups=C.defaultdict(list)
 for o in edges:groups[(o["payload"]["query_ref"],o["payload"]["target_scope"])].append(o)
 require(len(groups)==len(q)*len(p["target_scopes"]),"QUERY_SCOPE_COUNT")
 selected=C.Counter();red=C.Counter();ablation=C.Counter();maxerr=0;scope=C.Counter()
 for key,rr in groups.items():
  rr=sorted(rr,key=lambda x:x["payload"]["pool_rank"]);ss=[o["payload"] for o in rr]
  require([z["pool_rank"] for z in ss]==list(range(1,len(ss)+1)) and len({z["target_ref"] for z in ss})==len(ss),"POOL_RANK_CLOSURE")
  for field in ("label_rank","context_rank"):
   a=sorted(z[field] for z in ss if z[field] is not None)
   require(a==list(range(1,p["pre_rank_top_k_per_form_per_scope"]+1)),"PRE_RANK_TOPK_INCOMPLETE")
  def score(z):return (1/(60+z["label_rank"]) if z["label_rank"] else 0)+(1/(60+z["context_rank"]) if z["context_rank"] else 0)
  require(all(abs(z["fusion_score"]-score(z))<1e-12 for z in ss),"FUSION_SCORE_DRIFT")
  expected=sorted(ss,key=lambda z:(-score(z),-max(z["label_cosine"],z["context_cosine"]),z["target_legacy_ref"]))
  require([z["target_ref"] for z in ss]==[z["target_ref"] for z in expected],"FUSION_RANK_DRIFT")
  allowed=[z for z in ss if z["review_route"]!="RED"][:p["output_top_k_per_scope"]]
  require([z["target_ref"] for z in ss if z["selected_rank"] is not None]==[z["target_ref"] for z in allowed],"SHORTLIST_RANK_DRIFT")
  require([z["selected_rank"] for z in allowed]==list(range(1,len(allowed)+1)),"SHORTLIST_RANK_SEQUENCE")
  for z in ss:
   if z["selected_rank"]:selected[key[0]]+=1
   if z["review_route"]=="RED":red[key[0]]+=1
  a=next(z for z in ss if z["label_rank"]==1);b1=next(z for z in ss if z["context_rank"]==1)
  ablation["scope_pairs"]+=1;ablation["top1_changed"]+=a["target_ref"]!=b1["target_ref"]
  ablation["label_top1_red"]+=a["review_route"]=="RED";ablation["context_top1_red"]+=b1["review_route"]=="RED"
  ablation["fused_top1_red_before_screen"]+=ss[0]["review_route"]=="RED"
  scope[key[1]]+=len(rr)
 # Real inference spot replay, same pinned model, original texts. Re-encoding with different batch
 # padding may cause tiny quantization differences; this is a numeric tolerance, not a scientific threshold.
 mm=readj(file(root,str((P.Path(p["model_dir"])/"ModelManifest.json")),p["model_manifest_sha256"]))
 for x in mm["files"]:file(root,str(P.Path(p["model_dir"])/x["file"]),x["sha256"])
 enc=Encoder(root/p["model_dir"],p)
 spot=[]
 for key,rr in sorted(groups.items()):
  if len(spot)>=36:break
  spot.append(sorted(rr,key=lambda x:x["payload"]["pool_rank"])[0])
 lhs=[];rhs=[]
 for o in spot:
  z=o["payload"];qq=registry[z["query_ref"]]["payload"];t=registry[z["target_ref"]]["payload"]
  lhs.extend([qq["label_query"],qq["context_query"]]);rhs.extend(["passage: "+t["native_label"]]*2)
 qa=enc.encode(lhs);ta=enc.encode(rhs)
 differences=[]
 for i,o in enumerate(spot):
  z=o["payload"];differences += [abs(float(qa[2*i]@ta[2*i])-z["label_cosine"]),abs(float(qa[2*i+1]@ta[2*i+1])-z["context_cosine"])]
 # Dynamic int8 activations may be batch-dependent; explicitly diagnose and retain differences.
 within=sum(x<=0.02 for x in differences);require(within==len(differences),"MODEL_NUMERIC_REPLAY_TOLERANCE")
 # Same candidate/reference IDs, not semantic correctness.
 blind=readj(priv/"ReviewSourceOnlyQueue.json");hid=readj(priv/"ReviewCandidatesHidden.json")
 require(len(blind)==len(hid)==rpt["review_queue"]["new_sources"],"REVIEW_PACKET_COUNT")
 require(len({x["source_ref"] for x in blind})==len(blind) and not excluded&{x["source_ref"] for x in blind},"REVIEW_PACKET_OVERLAP")
 require({x["review_id"] for x in blind}=={x["review_id"] for x in hid},"REVIEW_PAIR_CLOSURE")
 require(all(set(x)=={"review_id","source_ref","source_scope","source_native_label","native_kind","question","status"} and x["status"]=="NOT_REVIEWED" for x in blind),"REVIEW_SOURCE_ONLY_FIELDS")
 tests=[]
 def pos(name,f):
  try:require(f() is not False,"ASSERTION");tests.append({"name":name,"expected":"ACCEPT","actual":"ACCEPT","pass":True})
  except Exception as e:tests.append({"name":name,"expected":"ACCEPT","actual":str(e)[:100],"pass":False})
 def neg(name,code,f):
  try:f();tests.append({"name":name,"expected":code,"actual":"ACCEPT","pass":False})
  except ContractError as e:tests.append({"name":name,"expected":code,"actual":str(e),"pass":str(e).startswith(code)})
  except Exception as e:tests.append({"name":name,"expected":code,"actual":type(e).__name__+":"+str(e)[:100],"pass":False})
 def mut(o,fn):a=copy.deepcopy(o);fn(a);return seal(a)
 a=next(o for o in edges if o["payload"]["selected_rank"])
 red_edge=next((o for o in edges if o["payload"]["review_route"]=="RED"),None)
 pos("all persisted records and revision refs validated",lambda:len(rows)==rpt["typed_objects"])
 pos("all U2-C endpoint views admitted and pinned",lambda:len(targets)>len(q))
 pos("real native context re-read for every query",lambda:len(ctx)==len(q))
 pos("pre-ranking label and context pools retained",lambda:len(groups)==len(q)*3)
 pos("all shortlist ranks exactly replayed",lambda:sum(selected.values())==rpt["shortlist_edges"])
 pos("real local ONNX score replay within explicit numeric tolerance",lambda:within==len(differences))
 pos("new queue excludes original 44",lambda:len(blind)>0 and len(excluded)==44)
 pos("new candidates remain HOLD, not equivalent",lambda:all(not x["payload"]["accepted_equivalence"] and x["payload"]["measurement_qualification"]=="HOLD" for x in edges))
 neg("forged exact semantic equivalence","U3B_SCHEMA",lambda:validate_obj(mut(a,lambda z:z["payload"].update(accepted_equivalence=True,source_relation_to_target="EXACT")),vs,registry))
 neg("candidate promoted into physical instance","U3B_SCHEMA",lambda:validate_obj(mut(a,lambda z:z["payload"].update(physical_instance_link=True)),vs,registry))
 neg("training purpose inserted","U3B_SCHEMA",lambda:validate_obj(mut(a,lambda z:z["payload"].update(permitted_purposes=["TRAIN"])),vs,registry))
 neg("false calibrated score","U3B_SCHEMA",lambda:validate_obj(mut(a,lambda z:z["payload"].update(score_interpretation="CALIBRATED_PROBABILITY")),vs,registry))
 neg("missing source dependency despite valid hash","U3B_REQUIRED_DEPENDENCY",lambda:validate_obj(mut(a,lambda z:z.update(dependency_refs=[v for v in z["dependency_refs"] if v!=z["payload"]["source_ref"]])),vs,registry))
 neg("wrong target source anchor","U3B_ANCHOR_MISMATCH",lambda:validate_obj(mut(a,lambda z:z["payload"].update(target_anchor_ref=z["payload"]["source_anchor_ref"])),vs,registry))
 neg("wrong source grain","U3B_ENDPOINT_MISMATCH",lambda:validate_obj(mut(a,lambda z:z["payload"].update(source_grain="FOOD_INSTANCE")),vs,registry))
 neg("rights dependency stripped","U3B_RIGHTS_DEPENDENCY",lambda:validate_obj(mut(a,lambda z:z["governance"].update(rights_domains=["MODEL_LICENSE_REVIEW"])),vs,registry))
 neg("extra unregistered payload field","U3B_SCHEMA",lambda:validate_obj(mut(a,lambda z:z["payload"].update(fake_gold=True)),vs,registry))
 neg("raw label changed despite seal","U3B_QUERY_SOURCE",lambda:validate_obj(mut(q[0],lambda z:z["payload"].update(native_label="fabricated")),vs,registry))
 if red_edge:
  neg("actual rule conflict removed from pre-rank evidence","U3B_CONFLICT_OMITTED",lambda:validate_obj(mut(red_edge,lambda z:z["payload"].update(risk_flags=[])),vs,registry))
  neg("actual rule conflict promoted to shortlist","U3B_CONFLICT_SHORTLISTED",lambda:validate_obj(mut(red_edge,lambda z:z["payload"].update(review_route="AMBER",selected_rank=1,candidate_status="SHORTLIST_PENDING")),vs,registry))
 pos("explicit Chinese hard negative raw/cooked","" and None or (lambda:bool(conflicts("生鸡肉","cooked chicken"))))
 pos("explicit Chinese fresh/frozen","" and None or (lambda:bool(conflicts("冻鱼","fresh fish"))))
 pos("avoid raw substring in 花生/生菜",lambda:"raw" not in qualifiers("花生") and "raw" not in qualifiers("生菜"))
 # Real U2-C scientific gate remains unavailable, not silently bypassed.
 pos("U2-C mapping release entry HOLD",lambda:adm.request("mapping_release",[q[0]["payload"]["source_legacy_ref"]])["decision"]=="HOLD")
 require(all(t["pass"] for t in tests),"PILOT_INTEGRATION_FAILURE:"+str([t["name"] for t in tests if not t["pass"]]))
 # Compare old paired candidate membership in the same fixed target scope; this is rank overlap only.
 old={x["source_ref"]:x for x in lines(file(root,p["old_routes"]["path"],p["old_routes"]["sha256"]))}
 old_edges=rt.b.idx
 shortlisted=C.defaultdict(set);pooled=C.defaultdict(set)
 for o in edges:
  z=o["payload"];pooled[z["source_legacy_ref"]].add(z["target_legacy_ref"])
  if z["selected_rank"]:shortlisted[z["source_legacy_ref"]].add(z["target_legacy_ref"])
 paired=C.defaultdict(C.Counter)
 for o in q:
  z=o["payload"];rr=z["source_legacy_ref"]
  if z["cohort"]!="PAIRED_DEV":continue
  a=paired[z["source_scope"]];a["queries"]+=1;a["baseline_any_candidate"]+=bool(old[rr]["candidate_count"]);a["new_any_shortlist"]+=bool(shortlisted[rr])
  olds={old_edges[e]["payload"]["target_ref"] for e in old[rr]["candidate_refs"] if e in old_edges}
  olds={x for x in olds if x in rt.b.idx and rt.b.idx[x]["payload"]["native_namespace"] in p["target_scopes"]}
  a["old_external_candidate_edges"]+=len(olds);a["old_edges_retrieved_in_new_pool"]+=len(olds&pooled[rr]);a["old_edges_in_new_shortlist"]+=len(olds&shortlisted[rr])
  a["new_neighbor_for_previously_unmatched"]+=not old[rr]["candidate_count"] and bool(shortlisted[rr])
 # No result file or critic output is read here. Presence is not validity and no unblinding.
 receipt_exists=(root/p["critique_dir"]/"CriticFreezeReceipt.json").is_file()
 result={"status":"PASS_BOUNDED_GENERATOR_CONFORMANCE / INDEPENDENT_REVIEW_HOLD","object_replays":len(rows),"native_query_context_replays":len(ctx),"candidate_edges_validated":len(edges),
 "all_scope_pool_rank_replays":len(groups),"onnx_spot_pairs":len(spot),"onnx_score_comparisons":len(differences),"onnx_tolerance":0.02,"onnx_max_abs_score_difference":max(differences),
 "tests_total":len(tests),"tests_passed":sum(t["pass"] for t in tests),"tests":tests,"paired_comparison":{k:dict(v) for k,v in paired.items()},
 "context_ablation":dict(ablation),"new_review_queue_sources":len(blind),"old_review_queue_unchanged":True,"critic_receipt_present_at_verification":receipt_exists,
 "independent_reviews_completed":0,"independent_reference_count":0,"mapping_releases":0,"precision_recall":"NOT_ESTIMABLE",
 "qualification_gate":{"structure":"PASS","local_model_retrieval":"PASS","pre_rank_conflict_retention":"PASS","independent_semantic_reference":"HOLD","scientific_mapping_release":"HOLD"},
 "limitations":["rank-only fixed top-k; no independent accuracy","spot re-encoding not full independent model rerun","risk detection is partial explicit lexical-state checking","no verified access-control isolation; packets separated","independent Critic freeze must be validated before unblinding"]}
 rt.b.verify_files();require(all(sha(root/x["path"])==x["sha256"] for x in p["excluded_queues"]),"UPSTREAM_QUEUE_CHANGED")
 out.mkdir(parents=True);put(out/"U3BValidationReport.json",result);print(json.dumps({k:v for k,v in result.items() if k!="tests"},ensure_ascii=False),flush=True)
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--run",type=P.Path,required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.profile.resolve(),x.run,x.out)
