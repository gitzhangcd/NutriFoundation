#!/usr/bin/env python3
"""Freeze validated generator outputs and verify the separate review packet closure.
Does not read Critic outputs; no unblinding or scientific release.
"""
import argparse,json,collections as C,pathlib as P,sys
sys.path.insert(0,str(P.Path(__file__).resolve().parents[2]/"src/u3b"))
from run_u3b import *
def main(root,profile,run,validation,out):
 root=root.resolve();run=run.resolve();validation=validation.resolve();out=out.resolve()
 require(out.is_relative_to(root/"runs/B2/U3-B") and not out.exists() and not out.is_relative_to(run),"NEW_FREEZE_DIRECTORY")
 p=readj(profile);r=readj(run/"U3BGeneratorReport.json");v=readj(validation/"U3BValidationReport.json")
 require(r["status"]=="PASS_BOUNDED_MULTILINGUAL_GENERATOR_PILOT" and v["status"].startswith("PASS_BOUNDED_GENERATOR_CONFORMANCE") and v["tests_passed"]==v["tests_total"],"UPSTREAM_GENERATOR_VALIDATION")
 priv=run/"private";m=readj(priv/"partition_manifest.json");require(sha(priv/"partition_manifest.json")==r["partition_manifest_sha256"],"PILOT_MANIFEST")
 candidates=C.defaultdict(set);short=C.defaultdict(set);queries={};candidate_count=0
 for rel,x in m.items():
  f=file(priv/"typed_partitions",rel,x["sha256"]);require(f.stat().st_size==x["bytes"],"PILOT_SIZE")
  for o in lines(f):
   revision_ok(o);z=o["payload"]
   if o["kind"]=="SemanticCandidateRecord":
    rr=z["source_legacy_ref"];candidates[rr].add(ref(o));candidate_count+=1
    if z["selected_rank"]:short[rr].add(ref(o))
   elif o["kind"]=="QueryContextRecord":queries[z["source_legacy_ref"]]=z
 require(candidate_count==r["pre_rank_pool_edges"] and len(queries)==r["query_count"],"GENERATOR_COUNT")
 oldq=[]
 for x in p["excluded_queues"]:oldq+=readj(file(root,x["path"],x["sha256"]))
 excluded={x["source_ref"] for x in oldq};require(len(excluded)==len(oldq)==44,"OLD_QUEUE")
 q=readj(priv/"ReviewSourceOnlyQueue.json");h=readj(priv/"ReviewCandidatesHidden.json");ix={x["review_id"]:x for x in h};requested={x["source_ref"] for x in q}
 require(len(q)==len(h)==len(ix)==len(requested)==44 and not excluded&requested,"REVIEW_QUEUE_CLOSURE")
 base=root/p["baseline"]["run"]/"private";bm=readj(file(root,str((base/"partition_manifest.json").relative_to(root)),p["baseline"]["partition_manifest_sha256"]));tree=base/"typed_partitions"
 native={};prior=C.defaultdict(set);red=set();high=set()
 for rel,x in bm.items():
  if not rel.endswith(("/NativeVocabularyRecord.jsonl","/AlignmentRecord.jsonl")):continue
  f=file(tree,rel,x["sha256"])
  for o in lines(f):
   z=o["payload"];legacy=o["governance"]["legacy_ref"]
   if o["kind"]=="NativeVocabularyRecord":
    if legacy in requested:native[legacy]=z
   elif o["kind"]=="AlignmentRecord":
    rr=z["source_ref"]
    if rr in requested:prior[rr].add(ref(o))
    if z["review_route"]=="RED":red.add(rr)
    elif z["ranking_score"]>=0.9:high.add(rr)
 require(len(native)==len(requested),"QUEUE_NATIVE_ENDPOINT")
 strata=C.Counter()
 for x in q:
  rr=x["source_ref"];y=ix[x["review_id"]];z=native[rr]
  require(set(x)=={"review_id","source_ref","source_scope","source_native_label","native_kind","question","status"} and x["status"]=="NOT_REVIEWED","SOURCE_ONLY_FIELDS")
  require(x["source_scope"]==z["native_namespace"] and x["source_native_label"]==z["native_label"] and x["native_kind"]==z["native_kind"],"SOURCE_ONLY_IDENTITY")
  require(set(y["new_shortlist_refs"])==short[rr] and set(y["new_pre_rank_pool_refs"])==candidates[rr] and set(y["u2c_prior_candidate_refs"])==prior[rr],"HIDDEN_CANDIDATE_CLOSURE")
  st=y["stratum"];strata[st]+=1
  if st=="NEW_U2C_RULE_RED":require(rr in red-excluded,"REVIEW_RED_STRATUM")
  elif st=="HIGH_SCORE_AMBER":require(rr in high-red-excluded,"REVIEW_AMBER_STRATUM")
  else:require(rr in queries and queries[rr]["cohort"]=="FRESH_DEV","REVIEW_FRESH_STRATUM")
 require({x["source_ref"] for x in q if ix[x["review_id"]]["stratum"]=="NEW_U2C_RULE_RED"}==red-excluded,"NEW_RED_COVERAGE")
 paths=[profile,root/"configs/udf/u3b/U3B_ReviewQualificationProtocol_v0.1.json",root/"src/u3b/run_u3b.py",root/"tests/u3b/verify_u3b.py",P.Path(__file__).resolve(),
        root/p["model_dir"]/"ModelManifest.json",run/"U3BGeneratorReport.json",run/"U3B_PilotContract.schema.json",validation/"U3BValidationReport.json",
        priv/"partition_manifest.json",priv/"ReviewSourceOnlyQueue.json",priv/"ReviewCandidatesHidden.json"]
 hashes={str(x.relative_to(root)):sha(x) for x in paths}
 out.mkdir(parents=True)
 receipt={"status":"GENERATOR_FROZEN_DEVELOPMENT_ONLY / INDEPENDENT_REVIEW_HOLD","utc":datetime.now(timezone.utc).isoformat(),"generator_run":str(run.relative_to(root)),"validation_run":str(validation.relative_to(root)),
 "profile_sha256":sha(profile),"model_manifest_sha256":p["model_manifest_sha256"],"output_file_hashes":hashes,"typed_objects":r["typed_objects"],"generator_candidates":r["pre_rank_pool_edges"],
 "original_44_unchanged":True,"new_review_queue_sources":len(q),"new_review_queue_strata":dict(strata),"source_only_and_hidden_pairs_verified":len(q),
 "new_queue_source_overlap_original":0,"critic_content_read":False,"independent_review_completed":0,"adjudicated_reference_count":0,
 "mapping_release_authorized":False,"scientific_release_authorized":False,"note":"Only verified generator freeze. File separation is not proven access control. No unblinding performed."}
 put(out/"GeneratorFreezeReceipt.json",receipt);print(json.dumps({k:v for k,v in receipt.items() if k!="output_file_hashes"},ensure_ascii=False))
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--run",type=P.Path,required=True);a.add_argument("--validation",type=P.Path,required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.profile.resolve(),x.run,x.validation,x.out)
