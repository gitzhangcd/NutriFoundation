#!/usr/bin/env python3
"""A2.8-P4 offline source-only inference. Separate synthetic smoke and fixed 51-case run.
Every raw completion is sealed once; no retries, reference inputs or target lookup.
Python audit guard is not an OS-level isolation guarantee.
"""
import sys,os,json,hashlib,collections,time,stat,re
from pathlib import Path
from a28_p4_channels import evidence,messages,validate,channel_views,need,CHANNELS,SYSTEM
ROOT=Path.cwd().resolve();B=Path("runs/B2/U3-B/C2/R2/P2/A2")
RT=B/"p4_local_runtime_001";SOURCE=B/"query_source_projection_001"
TOK=Path("runs/B2/U3-B/inputs/e5-small-xenova/tokenizer.json")
CONTRACT=Path("configs/udf/u3r2p2a2/A28P4LLMExperiment_v0.1.json")
SMOKE=B/"p4_synthetic_smoke_001";REAL=B/"p4_source_hypotheses_001"
def sha(b):return hashlib.sha256(b).hexdigest()
def sha_file(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def pin(p,h):
 p=Path(p);need(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(ROOT),"PIN_PATH")
 b=p.read_bytes();need(sha(b)==h,"PIN_DRIFT");return b
def j(p,h):return json.loads(pin(p,h))
def canon(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
def save(p,x):
 b=canon(x);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,"wb") as f:f.write(b);f.flush();os.fsync(f.fileno())
 return sha(b)
def set_offline():
 for k in list(os.environ):
  if k.upper() in {"HF_TOKEN","HUGGING_FACE_HUB_TOKEN","HUGGINGFACE_HUB_TOKEN","HUGGINGFACE_TOKEN"}:os.environ.pop(k,None)
 os.environ.update({"HF_HUB_OFFLINE":"1","TRANSFORMERS_OFFLINE":"1","HF_HUB_DISABLE_IMPLICIT_TOKEN":"1","HF_HUB_DISABLE_TELEMETRY":"1","DO_NOT_TRACK":"1","HF_HOME":str((RT/"hf_cache").resolve()),"PYTHONNOUSERSITE":"1","TOKENIZERS_PARALLELISM":"false"})
def fence(mode,out):
 allowed={ROOT/p for p in (CONTRACT,RT/"RuntimeManifest.json",TOK)}
 if mode=="real":allowed|={ROOT/p for p in (SOURCE/"ProjectionReceipt.json",SOURCE/"PrivateSourceOnly51.json",SMOKE/"SmokeReceipt.json")}
 state={"denied":0}
 def hook(event,args):
  if event in ("subprocess.Popen","os.system","os.exec","os.posix_spawn","socket.connect","socket.bind","socket.getaddrinfo"):
   state["denied"]+=1;raise PermissionError("NO_EXTERNAL_DISPATCH")
  if event!="open" or isinstance(args[0],int):return
  p=Path(os.fsdecode(args[0])).resolve();m=args[1] or "";fl=args[2] or 0
  writing=any(c in m for c in "wax+") or fl&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
  if p.is_relative_to(ROOT):
   if writing and p.is_relative_to(ROOT/out):return
   if not writing and (p in allowed or p.is_relative_to(ROOT/"src") or p.is_relative_to(ROOT/"configs") or p.is_relative_to(ROOT/RT) or p.is_relative_to(ROOT/out)):return
   state["denied"]+=1;raise PermissionError("PROJECT_IO_DENIED")
  elif writing:
   state["denied"]+=1;raise PermissionError("EXTERNAL_WRITE_DENIED")
 sys.addaudithook(hook);return state
def toy(label,role,aliases,ingredients):
 s={"review_id":"synthetic","source_ref":"synthetic","source_scope":"synthetic","source_native_label":label,"native_kind":role,"source_locator":{},"artifact_sha256":"0"*64,"source_anchor_ref":"synthetic","native_aliases":[{"text":a,"type":"NATIVE"} for a in aliases],"reference_recipe_ingredient_names":ingredients,"context_locator":{},"context_note":"synthetic","question":"synthetic","status":"NOT_REVIEWED"}
 return s,["query: "+label,"query: "+label+" "+role]
def smoke_sources():
 return [toy("芋头（蒸）","INGREDIENT_REFERENCE",[],[]),toy("青椒炒鸡蛋","RECIPE_REFERENCE",[],["青椒","鸡蛋"]),toy("无糖豆浆","INGREDIENT_REFERENCE",[],[]),toy("不明代号食物甲","RECIPE_REFERENCE",[],[])]
def classify_case(model,tokenizer,generate,sampler,token_count,s,q0):
 e=evidence(s)
 prompt=tokenizer.apply_chat_template(messages(e),add_generation_prompt=True,tokenize=False)
 t=time.monotonic()
 raw=generate(model,tokenizer,prompt=prompt,max_tokens=384,sampler=sampler,verbose=False)
 elapsed=round(time.monotonic()-t,3)
 try:
  h=validate(raw,e);valid=True;error=None
 except ValueError as x:
  h=None;valid=False;error=str(x)
  need(re.fullmatch("[A-Z_]+",error) is not None,"ERROR_SANITIZATION")
 views,stats=channel_views(h,e,q0,token_count)
 return {"raw_completion":raw,"completion_sha256":sha(raw.encode()),"evidence":e,"hypotheses":h,"structure_valid":valid,"validation_error":error,"views":views,"view_stats":stats,"runtime_seconds":elapsed,"model_output_hypothesis_only":True,"scientific_mapping_release":False}
def main(mode,contract_sha,runtime_sha,smoke_sha=None,batch=None):
 need(mode in ("smoke","real"),"MODE")
 out=SMOKE if mode=="smoke" else REAL
 # Before imports, prevent network-backed model resolution.
 set_offline();state=fence(mode,out)
 import importlib.metadata
 import mlx.core as mx
 from mlx_lm import load,generate
 from mlx_lm.sample_utils import make_sampler
 from tokenizers import Tokenizer
 ct=j(CONTRACT,contract_sha);need(ct["status"]=="FROZEN_P4_DEVELOPMENT_ONLY","CONTRACT")
 for p,h in ct["code_sha256"].items():pin(p,h)
 need(ct["prompt_sha256"]==sha(SYSTEM.encode()),"PROMPT_DRIFT")
 rt=j(RT/"RuntimeManifest.json",runtime_sha)
 need(rt["repo"]==ct["model"]["repo"] and rt["revision"]==ct["model"]["revision"],"MODEL_REVISION")
 for x in rt["model_files"]:
  p=RT/"model"/x["file"];need(p.is_file() and not p.is_symlink() and p.stat().st_size==x["bytes"] and sha_file(p)==x["sha256"],"MODEL_FILE_DRIFT")
 installed={x.metadata["Name"]:x.version for x in importlib.metadata.distributions()}
 need(installed==rt["installed_distributions"],"RUNTIME_PACKAGE_DRIFT")
 need(ct["generation"]=={"max_new_tokens":384,"temperature":0.0,"seed":20261129,"retries":0},"DECODING_DRIFT")
 mx.random.seed(ct["generation"]["seed"])
 tokraw=pin(TOK,ct["e5_tokenizer_sha256"]);et=Tokenizer.from_str(tokraw.decode());et.no_truncation();et.no_padding()
 token_count=lambda s:len(et.encode(s).ids)
 model,tokenizer=load(str((RT/"model").resolve()))
 sampler=make_sampler(temp=0.0)
 if mode=="smoke":
  need(not out.exists(),"SMOKE_EXISTS")
  out.mkdir(mode=0o700)
  rows=[]
  for i,(s,q0) in enumerate(smoke_sources()):
   x=classify_case(model,tokenizer,generate,sampler,token_count,s,q0)
   rows.append(x);print(json.dumps({"synthetic_case":i+1,"structure_valid":x["structure_valid"],"identity_abstain":x["view_stats"]["identity_abstain"],"runtime_seconds":x["runtime_seconds"]}),flush=True)
  need(state["denied"]==0,"IO_DENIAL")
  h=save(out/"SyntheticCompletions.json",rows)
  n=sum(x["structure_valid"] for x in rows);nonempty=sum(x["structure_valid"] and not x["view_stats"]["identity_abstain"] for x in rows)
  rc={"status":"PASS_LOCAL_GENERATION_SMOKE" if n>=3 and nonempty>=2 else "HOLD_LOCAL_GENERATION_SMOKE","contract_sha256":contract_sha,"runtime_manifest_sha256":runtime_sha,"synthetic_cases":len(rows),"valid_structures":n,"nonabstaining_cases":nonempty,"completion_file_sha256":h,"no_real_source_read":True,"reference_outputs_read":0,"application_io_denials":state["denied"],"mapping_release":0}
  print(json.dumps({**rc,"receipt_sha256":save(out/"SmokeReceipt.json",rc)},ensure_ascii=False),flush=True)
  return
 sm=j(SMOKE/"SmokeReceipt.json",smoke_sha)
 need(sm["status"]=="PASS_LOCAL_GENERATION_SMOKE" and sm["contract_sha256"]==contract_sha and sm["runtime_manifest_sha256"]==runtime_sha,"SMOKE_GATE")
 sr=j(SOURCE/"ProjectionReceipt.json",ct["source_projection_receipt_sha256"])
 p=j(SOURCE/"PrivateSourceOnly51.json",sr["source_only_packet_sha256"])
 need(p["reference_outputs_included"] is False and p["rank_hints_included"] is False and p["mapping_release"] is False,"SOURCE_PACKET")
 rows=sorted(p["rows"],key=lambda x:(x["cohort"],x["source"]["review_id"]))
 need(len(rows)==len({x["source"]["review_id"] for x in rows})==51,"SOURCE_COUNT")
 n=int(batch);bs=ct["batch_size"]
 need(0<=n<(len(rows)+bs-1)//bs,"BATCH_INDEX")
 out.mkdir(mode=0o700,exist_ok=True);dest=out/("batch_"+str(n+1).zfill(2))
 need(not dest.exists(),"BATCH_EXISTS")
 dest.mkdir(mode=0o700)
 summary=collections.Counter();row_hashes={}
 for pos,item in enumerate(rows[n*bs:(n+1)*bs],n*bs):
  s=item["source"];ctx=item["context"]
  x=classify_case(model,tokenizer,generate,sampler,token_count,s,[ctx["label_query"],ctx["context_query"]])
  x.update({"review_id":s["review_id"],"cohort":item["cohort"],"source_ref":s["source_ref"],"source_artifact_sha256":s["artifact_sha256"]})
  name="Case_"+str(pos+1).zfill(3)+".json";row_hashes[name]=save(dest/name,x)
  summary["cases"]+=1;summary["valid"]+=x["structure_valid"];summary["identity_abstain"]+=x["view_stats"]["identity_abstain"];summary["monolithic_truncated_views"]+=x["view_stats"]["monolithic_truncated_views"];summary["omitted_segment_terms"]+=x["view_stats"]["omitted_segment_terms"]
  for c in CHANNELS:summary[c+"_nonempty"]+=bool(x["hypotheses"] and x["hypotheses"][c])
  print(json.dumps({"batch":n+1,"completed_in_batch":summary["cases"],"structure_valid":x["structure_valid"],"identity_abstain":x["view_stats"]["identity_abstain"],"runtime_seconds":x["runtime_seconds"]}),flush=True)
 need(state["denied"]==0,"IO_DENIAL")
 rc={"status":"PASS_SOURCE_ONLY_BATCH_FREEZE","batch":n+1,"contract_sha256":contract_sha,"runtime_manifest_sha256":runtime_sha,"smoke_receipt_sha256":smoke_sha,"source_projection_receipt_sha256":ct["source_projection_receipt_sha256"],"counts":dict(summary),"case_file_hashes":row_hashes,"reference_outputs_read":0,"target_inputs_read":0,"application_io_denials":state["denied"],"mapping_release":0}
 print(json.dumps({"receipt_sha256":save(dest/"BatchReceipt.json",rc),"batch":n+1,"counts":dict(summary)},ensure_ascii=False),flush=True)
if __name__=="__main__":main(*sys.argv[1:])
