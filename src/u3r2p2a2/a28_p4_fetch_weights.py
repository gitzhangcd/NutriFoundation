#!/usr/bin/env python3
"""A2.8-P4 public-weight download recovery. No source records or reference inputs.
Resume only verified ranges; complete SHA256 required before publishing RuntimeManifest.
This is runtime preparation, not inference or scientific validation.
"""
from pathlib import Path
import json,hashlib,os,urllib.request,time,concurrent.futures,subprocess,sys
RT=Path("runs/B2/U3-B/C2/R2/P2/A2/p4_local_runtime_001")
REPO="mlx-community/Qwen3-4B-Instruct-2507-4bit"
REV="50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b"
SIZE=2263022417
SHA="2a73c6c248601ab904e035548abd8e6abb65ea27dcb5f342fb0a8910eb44173f"
CHUNK=8*1024*1024
NAMES=("README.md","added_tokens.json","chat_template.jinja","config.json","generation_config.json","merges.txt","model.safetensors","model.safetensors.index.json","special_tokens_map.json","tokenizer.json","tokenizer_config.json","vocab.json")
URL=f"https://huggingface.co/{REPO}/resolve/{REV}/"
def sha_file(p,git=False):
 h=hashlib.sha1() if git else hashlib.sha256()
 if git:h.update(("blob "+str(p.stat().st_size)+"\0").encode())
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1048576),b""):h.update(x)
 return h.hexdigest()
def save(p,x):
 raw=(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,"wb") as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return hashlib.sha256(raw).hexdigest()
def get_meta():
 with urllib.request.urlopen(f"https://huggingface.co/api/models/{REPO}/revision/{REV}?blobs=true",timeout=10) as f:x=json.load(f)
 assert x["sha"]==REV
 m={a["rfilename"]:a for a in x["siblings"]}
 assert m["model.safetensors"]["lfs"]["sha256"]==SHA and m["model.safetensors"]["size"]==SIZE
 return m
def verify(p,m):
 return p.is_file() and not p.is_symlink() and p.stat().st_size==m["size"] and (sha_file(p)==m["lfs"]["sha256"] if m.get("lfs") else sha_file(p,git=True)==m["blobId"])
def intervals():return [(a,min(a+CHUNK,SIZE)-1) for a in range(0,SIZE,CHUNK)]
def read_journal(path,fd):
 done={}
 if not path.exists():return done
 for line in path.read_text().splitlines():
  x=json.loads(line);a,b=x["start"],x["end"]
  assert (a,b) in intervals() and a not in done
  raw=os.pread(fd,b-a+1,a)
  assert len(raw)==b-a+1 and hashlib.sha256(raw).hexdigest()==x["sha256"],"JOURNAL_RANGE_DRIFT"
  done[a]=x
 return done
def fetch(pair,deadline):
 a,b=pair;n=b-a+1
 if time.monotonic()>deadline:return None
 try:
  req=urllib.request.Request(URL+"model.safetensors",headers={"Range":f"bytes={a}-{b}","Accept-Encoding":"identity"})
  with urllib.request.urlopen(req,timeout=12) as f:
   assert f.status==206 and f.headers.get("Content-Range")==f"bytes {a}-{b}/{SIZE}"
   raw=f.read(n+1)
  assert len(raw)==n
  return a,b,raw
 except Exception:return None
def main(seconds):
 assert 1<=seconds<=600 and RT.is_dir()
 meta=get_meta();model=RT/"model";model.mkdir(mode=0o700,exist_ok=True)
 for n in NAMES:
  if n=="model.safetensors":continue
  p=model/n
  if not p.exists():
   with urllib.request.urlopen(URL+n,timeout=12) as f:raw=f.read(meta[n]["size"]+1)
   assert len(raw)==meta[n]["size"]
   with p.open("xb") as o:o.write(raw)
  assert verify(p,meta[n]),"SMALL_FILE_PIN"
 if not (model/"model.safetensors").exists():
  part=RT/"model.safetensors.resumable.part";journal=RT/"ResumableRangeJournal.jsonl"
  if part.exists():
   assert part.is_file() and not part.is_symlink() and part.stat().st_size==SIZE
   fd=os.open(part,os.O_RDWR)
  else:
   assert not journal.exists();fd=os.open(part,os.O_RDWR|os.O_CREAT|os.O_EXCL,0o600);os.ftruncate(fd,SIZE)
  deadline=time.monotonic()+seconds;attempted=0;failures=0
  try:
   done=read_journal(journal,fd)
   todo=iter([x for x in intervals() if x[0] not in done])
   with journal.open("a",encoding="utf8") as log,concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    pending={}
    def refill():
     while len(pending)<8 and time.monotonic()<deadline:
      item=next(todo,None)
      if item is None:break
      pending[ex.submit(fetch,item,deadline)]=item
    refill()
    while pending:
     ready,_=concurrent.futures.wait(pending,return_when=concurrent.futures.FIRST_COMPLETED)
     for f in ready:
      pending.pop(f);attempted+=1;res=f.result()
      if res is None:failures+=1;continue
      a,b,raw=res;offset=0
      while offset<len(raw):
       n=os.pwrite(fd,raw[offset:],a+offset);assert n>0;offset+=n
      os.fsync(fd)
      row={"start":a,"end":b,"sha256":hashlib.sha256(raw).hexdigest()}
      log.write(json.dumps(row,separators=(",",":"))+"\n");log.flush();os.fsync(log.fileno());done[a]=row
      if len(done)%8==0 or len(done)==len(intervals()):print(json.dumps({"verified_chunks":len(done),"expected_chunks":len(intervals()),"verified_bytes":sum(x["end"]-x["start"]+1 for x in done.values())}),flush=True)
     refill()
   total=sum(x["end"]-x["start"]+1 for x in done.values())
   print(json.dumps({"status":"COMPLETE_RANGES" if total==SIZE else "PARTIAL_RANGES_SAVED","verified_chunks":len(done),"expected_chunks":len(intervals()),"verified_bytes":total,"attempted_this_run":attempted,"failed_this_run":failures}),flush=True)
  finally:os.close(fd)
  if total!=SIZE:return
  assert sha_file(part)==SHA,"COMPLETE_WEIGHT_SHA"
  os.rename(part,model/"model.safetensors")
 assert verify(model/"model.safetensors",meta["model.safetensors"])
 for n in NAMES:assert verify(model/n,meta[n])
 files=[{"file":n,"sha256":sha_file(model/n),"bytes":(model/n).stat().st_size} for n in NAMES]
 py=RT/"venv/bin/python"
 c="import importlib.metadata as m,platform,json; print(json.dumps({'python_version':platform.python_version(),'installed_distributions':{x.metadata['Name']:x.version for x in m.distributions()}}))"
 x=subprocess.run([str(py),"-B","-c",c],capture_output=True,text=True,check=True)
 env=json.loads(x.stdout)
 versions={k.lower():v for k,v in env["installed_distributions"].items()}
 for k,v in {"mlx-lm":"0.26.2","mlx":"0.26.5","transformers":"4.55.4","huggingface-hub":"0.34.4","numpy":"2.2.6","tokenizers":"0.21.4"}.items():assert versions[k]==v
 m={"version":"A2.8-P4-LOCAL-RUNTIME-v0.1","status":"PUBLIC_MODEL_AND_RUNTIME_PINNED","repo":REPO,"revision":REV,"license_model_card":"Apache-2.0","base_model":"Qwen/Qwen3-4B-Instruct-2507","model_files":files,**env,"local_model_inference_verified":False,"source_data_uploaded":False,"download_recovery":"VERIFIED_RESUMABLE_RANGES","published_weight_sha256":SHA,"all_files_verified_against_published_metadata":True}
 h=save(RT/"RuntimeManifest.json",m);print(json.dumps({"status":m["status"],"manifest_sha256":h,"files_verified":len(files),"weight_bytes":SIZE}),flush=True)
if __name__=="__main__":main(int(sys.argv[1]))
