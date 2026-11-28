#!/usr/bin/env python3
"""A2.8 segmented recovery runner, derived from exact frozen generator. Same scoring/rank functions; one scope per immutable segment."""
import sys,time,collections,json,os
from pathlib import Path
from a28_prepare import B,P,OUT,snap,j,sha,canon,save,need,PINS,SCOPES
from a28_query import surface,fused
ROOT=Path.cwd().resolve()
SEGROOT=B/"candidate_recovery_segmented_001"
DEST=None
RECOVERY=Path("configs/udf/u3r2p2a2/A28SegmentedExecution_v0.1.json")
CONTRACT=Path("configs/udf/u3r2p2a2/A28MechanismExperiment_v0.1.json")
ARMS=("G0","G1","G2","G3")
def top(x,k):
 # numpy exact deterministic argsort; stable original order sorted immutable key.
 import numpy as np
 return list(map(int,np.argsort(-x,kind="stable")[:k]))
def add_io_fence():
 # Application-level audit hook; native libraries are not an OS sandbox.
 allowed={ROOT/p for p in (RECOVERY,CONTRACT,OUT/"QueryFreezeReceipt.json",OUT/"PrivateQueryViews51.json",Path("configs/udf/u3r2p2a1/RetrievalPolicyFreeze_v0.1.json"),Path("runs/B2/U3-B/C2/R2/real_001/controller_private/FrozenTargetUniverse.json"))}
 allowed|={ROOT/"runs/B2/U3-A/inputs"/x for x in ("FoodOn.owl","FDC_SR_2018.zip","FNDDS_2015_16.zip","FNDDS_ARS_foods_2015_16.xlsx")}
 allowed|={ROOT/"runs/B2/U3-B/inputs/e5-small-xenova"/x for x in ("ModelManifest.json","model_quantized.onnx","tokenizer.json","config.json")}
 state={"denied":0}
 def hook(event,args):
  if event in ("subprocess.Popen","os.system","os.exec","os.posix_spawn","socket.connect","socket.bind","socket.getaddrinfo"):
   state["denied"]+=1;raise PermissionError("GENERATION_NO_EXTERNAL_DISPATCH")
  if event!="open" or isinstance(args[0],int):return
  p=Path(os.fsdecode(args[0])).resolve();mode=args[1] or "";flags=args[2] or 0
  writing=any(c in mode for c in "wax+") or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
  if p.is_relative_to(ROOT):
   if writing:
    if p.is_relative_to(ROOT/DEST):return
   elif p in allowed or p.is_relative_to(ROOT/"src") or p.is_relative_to(ROOT/"tests") or p.is_relative_to(ROOT/"docs") or p.is_relative_to(ROOT/"configs"):return
   elif p.is_relative_to(ROOT/DEST):return
   state["denied"]+=1;raise PermissionError("GENERATION_ROOT_IO_DENIED")
  elif writing:
   state["denied"]+=1;raise PermissionError("GENERATION_EXTERNAL_WRITE_DENIED")
 sys.addaudithook(hook)
 return state
def main(contract_sha,scope,recovery_sha):
 global DEST
 need(scope in SCOPES,"SCOPE")
 DEST=SEGROOT/scope
 need(not DEST.exists(),"OUTPUT_EXISTS")
 SEGROOT.mkdir(mode=0o700,exist_ok=True)
 fence=add_io_fence()
 recovery=j(RECOVERY,recovery_sha)
 need(recovery["original_contract_sha256"]==contract_sha and recovery["runner_sha256"]==sha(Path(__file__).read_bytes()) and recovery["scope_execution_only"] is True,"RECOVERY_PIN")
 ct=j(CONTRACT,contract_sha);need(ct["status"]=="FROZEN_DEVELOPMENT_ONLY" and ct["arms"]==list(ARMS),"CONTRACT")
 for p,h in ct["code_sha256"].items():snap(p,h)
 qr=j(OUT/"QueryFreezeReceipt.json",ct["query_receipt_sha256"])
 q=j(OUT/"PrivateQueryViews51.json",qr["private_query_views_sha256"])
 need(qr["reference_outputs_read"]==0 and qr["target_standard_payloads_read"]==0 and q["mapping_release"] is False,"QUERY_SCOPE")
 pol=j("configs/udf/u3r2p2a1/RetrievalPolicyFreeze_v0.1.json","58c53ab63cf4ac25d030d78e03dcdded8a51fb5a5802e7623ee75bd93af5ddc6")
 paths={p:h for p,h in pol["pins"].items() if p.startswith("runs/B2/U3-A/inputs/") or p.endswith("FrozenTargetUniverse.json")}
 for p,h in paths.items():snap(p,h)
 u=j("runs/B2/U3-B/C2/R2/real_001/controller_private/FrozenTargetUniverse.json",paths["runs/B2/U3-B/C2/R2/real_001/controller_private/FrozenTargetUniverse.json"])
 o=set(map(tuple,u["original"]));e=set(map(tuple,u["extension"]));need(len(o)==28845 and len(e)==1174 and not o&e,"UNIVERSE")
 by={s:sorted(t for t in o if t[0]==s) for s in SCOPES[:3]};by[SCOPES[3]]=sorted(e)
 model=Path("runs/B2/U3-B/inputs/e5-small-xenova")
 mm=j(model/"ModelManifest.json","2b052d7fc06fdd4de5505b4e1cd7b11be9a6a6be109781ed12c07402f3949ca9")
 need(mm["revision"]=="761b726dd34fb83930e26aab4e9ac3899aa1fa78","MODEL_REV")
 for x in mm["files"]:snap(model/x["file"],x["sha256"])
 sys.dont_write_bytecode=True
 sys.path.insert(0,str(ROOT/"src/u3b"));sys.path.insert(0,str(ROOT/"src/u3c1"))
 from run_u3b import Encoder
 from run_c1 import parse_standards,key
 import numpy as np,onnxruntime as ort
 from tokenizers import Tokenizer
 from types import SimpleNamespace
 need(ort.__version__=="1.19.2" and np.__version__=="2.0.2","RUNTIME")
 vocab,_=parse_standards(SimpleNamespace(root=ROOT))
 enc=Encoder(model,{"threads":4,"batch_size":128,"max_tokens":64})
 fulltok=Tokenizer.from_file(str(model/"tokenizer.json"));fulltok.no_truncation();fulltok.no_padding()
 def trunc_count(texts):
  return sum(len(x.ids)>64 for x in fulltok.encode_batch(texts))
 rows=q["queries"];ids=[x["review_id"] for x in rows];need(len(ids)==len(set(ids))==51,"CASES")
 budgets={(x["review_id"],x["scope"]):x["pool_budget"] for x in q["budgets"]};need(set(budgets)=={(i,s) for i in ids for s in SCOPES},"BUDGET")
 qtexts=[v for mode in ("q0","q1") for x in rows for v in x[mode]]
 need(len(qtexts)==204 and all(x.startswith("query: ") for x in qtexts),"QUERY_VIEWS")
 start=time.monotonic();qmat=enc.encode(qtexts);need(qmat.shape==(204,384),"QUERY_SHAPE")
 query_truncated={"Q0":trunc_count(qtexts[:102]),"Q1":trunc_count(qtexts[102:])}
 ranks=[];stats={};counts=collections.Counter()
 for s in (scope,):
  ts=by[s];main_text=[];extra_text=[];extra_idx=[]
  for i,t in enumerate(ts):
   x=vocab[key(t[0],t[2])];need(not x["deprecated"],"TARGET_DEPRECATED")
   a,b=surface(x["label"],x["aliases"],x["definitions"]);main_text.append(a)
   if b is not None:extra_idx.append(i);extra_text.append(b)
  t0=time.monotonic();tm=enc.encode(main_text);scores=qmat@tm.T
  expanded=scores.copy()
  if extra_text:
   em=enc.encode(extra_text);alt=qmat@em.T
   expanded[:,extra_idx]=np.maximum(scores[:,extra_idx],alt)
  need(np.isfinite(expanded).all(),"SCORE_FINITE")
  k=12 if s=="FOODON_EXTENSION" else 20
  for i,rid in enumerate(ids):
   cap=budgets[rid,s]
   for a,offset,mat in [("G0",0,scores),("G1",102,scores),("G2",0,expanded),("G3",102,expanded)]:
    x,y=mat[offset+2*i],mat[offset+2*i+1]
    ra,rb=top(x,k),top(y,k);z=fused(ra,rb,cap,x,y)
    need(len(z)==len(set(z))<=cap,"RANK_CAP")
    ranks.append({"review_id":rid,"scope":s,"arm":a,"pool_budget":cap,"targets":[list(ts[j]) for j in z]})
    counts[a]+=len(z)
  stats[s]={"targets":len(ts),"extra_surface_targets":len(extra_text),"main_passages_truncated":trunc_count(main_text),"extra_passages_truncated":trunc_count(extra_text),"inference_and_ranking_seconds":round(time.monotonic()-t0,3)}
  print(json.dumps({"scope":s,"target_count":len(ts),"extra_surfaces":len(extra_text),"completed_rank_groups":len(ranks)}),flush=True)
 need(len(ranks)==204 and len({(x["review_id"],x["scope"],x["arm"]) for x in ranks})==204,"RANK_CLOSURE")
 for p,h in PINS.items():need(sha(Path(p).read_bytes())==h,"POST_INPUT_DRIFT")
 need(fence["denied"]==0,"IO_FENCE")
 DEST.mkdir(mode=0o700)
 rh=save(DEST/"PrivateRanks.jsonl",b"".join(canon(x) for x in ranks))
 receipt={"version":"A2.8-CANDIDATE-RECOVERY-RECEIPT-v0.1","status":"PASS_SINGLE_SCOPE_RANK_FREEZE","scope":scope,"recovery_contract_sha256":recovery_sha,"contract_sha256":contract_sha,"query_receipt_sha256":ct["query_receipt_sha256"],"rank_sha256":rh,"rank_groups":204,"cases":51,"scope_budgets":51,"candidate_counts":dict(counts),"target_stats":stats,"query_truncation":query_truncated,"runtime_seconds":round(time.monotonic()-start,3),"model_revision":mm["revision"],"input_sha256":PINS,"reference_outputs_read":0,"historical_rank_outputs_read":0,"application_io_denials":fence["denied"],"mapping_release":0,"scientific_reference_qualified":False}
 print(json.dumps({"receipt_sha256":save(DEST/"ScopeFreezeReceipt.json",receipt),"rank_sha256":rh,"summary":{k:v for k,v in receipt.items() if k!="input_sha256"}},ensure_ascii=False),flush=True)
if __name__=="__main__":main(sys.argv[1],sys.argv[2],sys.argv[3])
