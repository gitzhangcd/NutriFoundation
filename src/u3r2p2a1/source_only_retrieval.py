#!/usr/bin/env python3
"""Frozen source-only retrieval experiment, not a mapping/admission runtime.

The retrieval process consumes a controller-authorized packet with native
source records and frozen dense rank hints; it has no reviewer result input.
Packet preparation for first19 is separate from retrieval. No reserved dispatch.
"""
import argparse,sys,os,json
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"u3r2p2"))
from run_p2_portable_v2 import (BASE,EXT,read,lines,put,putl,sha,dg,require,
 query,set_lexicon,parse_standards,Standards,target_docs,idfs,score,fused_rank)
P2=BASE/"P2"; A1=P2/"A1"; R2=BASE/"real_001"
UNIVERSE=R2/"controller_private/FrozenTargetUniverse.json"
LEX=P2/"private/DevelopmentLexicon_v0.1.json"
UNIVERSE_SHA="311ce55e814aae9ea473609811b9be621f42d52bf2eedf68fcca610adb6f8163"
LEX_SHA="846b8baa30a8bd1782cf93876163bdd37d625e169497fe77b007df240804b778"
V2_SHA="b62d0adc8ca641307bb8ac0e237aa25b60a55d9e746712fe909e34ed2e78f33b"
STANDARDS={
 "runs/B2/U3-A/inputs/FoodOn.owl":"b897bf64c1b265c422db9ee01e1235c10c0b809e7f02326ef810a52068347edf",
 "runs/B2/U3-A/inputs/FDC_SR_2018.zip":"b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0",
 "runs/B2/U3-A/inputs/FNDDS_2015_16.zip":"9be942b9d181acb62f37ee2f4c259dae642b586b2e4fe29039cfa1847f4d5dd0",
 "runs/B2/U3-A/inputs/FNDDS_ARS_foods_2015_16.xlsx":"a3289f72a032d9453e4f5dcb51e922ff476c07c71b79d32db378070f95af55d9"}
SOURCE_FIELDS={"review_id","source_ref","source_scope","source_native_label","native_kind",
 "source_locator","artifact_sha256","source_anchor_ref","native_aliases",
 "reference_recipe_ingredient_names","context_locator","context_note","question","status"}
HINT_FIELDS={"review_id","scope","target_key","label_rank","context_rank","frozen_pool_rank","fusion_score"}
SCOPES={"FoodOn","FDC_SR_Legacy","FNDDS","FOODON_EXTENSION"}
def trusted(root,rel,h):
 p=root/rel;require(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root) and sha(p)==h,"PIN_DRIFT:"+str(rel));return p
def check_packet(z):
 require(set(z)=={"purpose","source_records","dense_rank_hints","reviewer_results_included","mapping_release"},"PACKET_FIELDS")
 require(z["purpose"]=="SOURCE_ONLY_RETRIEVAL_EXPERIMENT" and z["reviewer_results_included"] is False and z["mapping_release"] is False,"PACKET_SCOPE")
 src=z["source_records"];require(src and len({s["review_id"] for s in src})==len(src)==len({s["source_ref"] for s in src}),"SOURCE_IDS")
 for s in src:
  require(set(s)==SOURCE_FIELDS and s["status"]=="NOT_REVIEWED","SOURCE_FIELDS_OR_STATUS")
  require(isinstance(s["native_aliases"],list) and all(set(a)=={"text","type"} and isinstance(a["text"],str) for a in s["native_aliases"]),"SOURCE_ALIAS_SCHEMA")
  require(isinstance(s["reference_recipe_ingredient_names"],list) and all(isinstance(a,str) for a in s["reference_recipe_ingredient_names"]),"RECIPE_SCHEMA")
 ids={s["review_id"] for s in src};seen=set();groups=defaultdict(list)
 for h in z["dense_rank_hints"]:
  require(set(h)==HINT_FIELDS and h["review_id"] in ids and h["scope"] in SCOPES,"HINT_FIELDS_OR_SCOPE")
  k=(h["review_id"],h["scope"],tuple(h["target_key"]));require(k not in seen,"DUPLICATE_HINT");seen.add(k)
  require(all(x is None or type(x) is int and x>0 for x in (h["label_rank"],h["context_rank"],h["frozen_pool_rank"])),"HINT_RANK")
  require(h["label_rank"] is not None or h["context_rank"] is not None,"HINT_NO_RANK")
  groups[(h["review_id"],h["scope"])].append(h)
 require(set(groups)=={(rid,sc) for rid in ids for sc in SCOPES},"DENSE_HINT_GROUP_CLOSURE")
 for (rid,sc),rs in groups.items():
  n=12 if sc=="FOODON_EXTENSION" else 20
  for f in ("label_rank","context_rank"):
   require(sorted(x[f] for x in rs if x[f] is not None)==list(range(1,n+1)),"DENSE_HINT_RANK_CLOSURE")
 return groups
def rank_group(q,docs,weights,old,scope):
 oi={tuple(x["target_key"]):x for x in old};budget=len(oi);require(budget==len(old),"GROUP_DUPLICATE")
 scored=[]
 for d in docs:
  val,_=score(q,d,weights)
  if val>0:scored.append((d["key"],val))
 scored.sort(key=lambda x:(-x[1],x[0]));sparse=[x[0] for x in scored]
 base=sorted(oi,key=lambda k:(oi[k]["frozen_pool_rank"] or 99999,-oi[k]["fusion_score"],k)) if scope!="FOODON_EXTENSION" else sorted(oi,key=lambda k:(-oi[k]["fusion_score"],k))
 return {"BASELINE_FUSION":base,"SOURCE_SPARSE":sparse[:budget],"HYBRID":fused_rank(sparse,old,budget)}
def prepare_dev(root,out,a1_sha):
 require(not out.exists() and out.is_relative_to(root/A1),"NEW_PROJECTION")
 a1=trusted(root,A1/"dev_001/A1FreezeReceipt.json",a1_sha);f=read(a1)
 for rel,h in f["input_fences"].items():trusted(root,Path(rel),h)
 p=P2/"portable_v2_001";fr=read(root/p/"CandidateFreeze.json")
 qfile=trusted(root,p/"private/QueryHypotheses.jsonl",fr["private_hashes"]["QueryHypotheses.jsonl"])
 qs={r["review_id"]:r for r in lines(qfile)};require(len(qs)==19,"DEV19")
 src=[r for r in read(root/R2/"reviewer_source_only/R2Review44.json") if r["review_id"] in qs]
 require(len(src)==19,"DEV_PACKET")
 sm={r["source_ref"]:r["review_id"] for r in src}
 hints=[]
 for x in read(root/R2/"controller_private/ProposalManifest.json").values():
  p=trusted(root,R2/x["file"],x["sha256"]);n=0
  for r in lines(p):
   n+=1
   if r["source_legacy_ref"] not in sm:continue
   scope="FOODON_EXTENSION" if r["target_scope"]==EXT else r["target_key"][0]
   hints.append({"review_id":sm[r["source_legacy_ref"]],"scope":scope,**{k:r[k] for k in ("target_key","label_rank","context_rank","frozen_pool_rank","fusion_score")}})
  require(n==x["rows"],"HINT_PARTITION_ROWS")
 z={"purpose":"SOURCE_ONLY_RETRIEVAL_EXPERIMENT","source_records":src,"dense_rank_hints":hints,"reviewer_results_included":False,"mapping_release":False}
 check_packet(z)
 out.mkdir(parents=True,mode=0o700);p=out/"RetrievalInput19.json";put(p,z);os.chmod(p,0o600)
 print("PACKET",len(src),len(hints),sha(p))
def run(root,packet,packet_sha,out):
 require(not out.exists() and out.is_relative_to(root/A1),"NEW_RETRIEVAL_OUTPUT")
 require(packet.is_relative_to(root) and sha(packet)==packet_sha,"PACKET_PIN")
 z=read(packet);groups=check_packet(z)
 trusted(root,Path("src/u3r2p2/run_p2_portable_v2.py"),V2_SHA)
 u=read(trusted(root,UNIVERSE,UNIVERSE_SHA));set_lexicon(read(trusted(root,LEX,LEX_SHA)))
 for rel,h in STANDARDS.items():trusted(root,Path(rel),h)
 by=defaultdict(set)
 for k in u["original"]:by[k[0]].add(tuple(k))
 by["FOODON_EXTENSION"]={tuple(k) for k in u["extension"]}
 require(sum(len(v) for k,v in by.items() if k!="FOODON_EXTENSION")==28845 and len(by["FOODON_EXTENSION"])==1174,"UNIVERSE")
 vocab,_=parse_standards(Standards(root));docs=target_docs(root,by,vocab);weights={k:idfs(v) for k,v in docs.items()}
 ranks=[];qrows=[]
 for s in z["source_records"]:
  q=query(s);qrows.append(q)
  for sc,ds in docs.items():
   old=groups[(q["review_id"],sc)]
   require(all(tuple(r["target_key"]) in by[sc] for r in old),"HINT_UNIVERSE")
   for arm,keys in rank_group(q,ds,weights[sc],old,sc).items():
    require(len(keys)<=len(old) and len(keys)==len(set(keys)),"POOL_CAP")
    ranks.append({"review_id":q["review_id"],"scope":sc,"arm":arm,"pool_budget":len(old),"targets":[list(k) for k in keys]})
 require(sha(packet)==packet_sha,"PACKET_CHANGED")
 for rel,h in STANDARDS.items():trusted(root,Path(rel),h)
 out.mkdir(parents=True,mode=0o700);putl(out/"Ranks.jsonl",ranks);putl(out/"QueryHypotheses.jsonl",qrows)
 for p in out.iterdir():os.chmod(p,0o600)
 put(out/"RetrievalReplayReceipt.json",{"method_sha256":sha(Path(__file__)),"packet_sha256":packet_sha,"groups":len(ranks),"source_records":len(qrows),
 "output_sha256":{p.name:sha(p) for p in out.iterdir()},"reviewer_results_read":False,"mapping_release":False,"source_only":True})
 print("RANKS",len(ranks),sha(out/"Ranks.jsonl"),"QUERIES",sha(out/"QueryHypotheses.jsonl"))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("phase",choices=["prepare-dev","run"]);p.add_argument("--root",type=Path,default=Path("."));p.add_argument("--out",type=Path,required=True);p.add_argument("--a1-sha");p.add_argument("--packet",type=Path);p.add_argument("--packet-sha");a=p.parse_args()
 if a.phase=="prepare-dev":require(a.a1_sha,"A1_SHA");prepare_dev(a.root.resolve(),a.out.resolve(),a.a1_sha)
 else:require(a.packet is not None and a.packet_sha,"PACKET_REQUIRED");run(a.root.resolve(),a.packet.resolve(),a.packet_sha,a.out.resolve())
