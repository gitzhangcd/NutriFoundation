#!/usr/bin/env python3
"""Bounded follow-up attempts and independent source-shape checks for B0.
Raw sample bytes remain in the local workspace. No archive extraction to original paths.
"""
import argparse, pathlib as P, json, urllib.request as U, tarfile, io, csv, collections as C, re, concurrent.futures as F, sys, hashlib
from collect_public_samples import Collect,RemoteZip,req,profile,sha,fetch
def food_select(infos):
 jpg=[v for v in infos if v.filename.lower().endswith((".jpg",".jpeg",".png"))]
 # prefer a training split and distinct class directories/prefixes
 train=[v for v in jpg if "training/" in v.filename.lower() or "train/" in v.filename.lower()]
 if train:jpg=train
 picks=[];groups=set()
 for v in jpg:
  p=P.PurePosixPath(v.filename);g=p.parent.as_posix()
  if re.match(r'^\d+_',p.name):g+="/"+p.name.split("_",1)[0]
  if g not in groups and v.file_size<=2_000_000:
   picks.append(v);groups.add(g)
  if len(picks)==2:break
 if len(picks)<2:picks=jpg[:2]
 return picks
def snap(root):
 c=Collect(root,4)
 url="https://ndownloader.figshare.com/files/44532971"
 target="snapme_db_09Dec2022/snapme_cs_db/master_SNAPME_linkfile.csv"
 try:
  with U.urlopen(req(url,{"Range":"bytes=0-8388607"}),timeout=18) as r:
   b=r.read(8_388_608)
   headers={"http":r.status,"content_range":r.headers.get("Content-Range"),"compressed_prefix_bytes":len(b)}
  if not b.startswith(b"\x1f\x8b"):raise ValueError("not gzip")
  total=0
  with tarfile.open(fileobj=io.BytesIO(b),mode="r|gz") as z:
   for a in z:
    total+=a.size
    if total>15_000_000:raise ValueError("bounded decompressed prefix exhausted")
    if a.name!=target:continue
    if not a.isfile() or a.size>3_000_000:raise ValueError("unexpected target shape")
    f=z.extractfile(a);x=f.read(a.size+1)
    if len(x)!=a.size:raise ValueError("incomplete tar member")
    c.save(x,"master_SNAPME_linkfile.csv",url,"NATIVE_RECORDS",headers,"headered",{"archive_member":target,"complete_member":True,"member_uncompressed_bytes":a.size})
    break
  if not c.rec["files"]:raise ValueError("target not extracted")
 except Exception as e:c.fail("SNAPMe native linkfile",e)
 return c.finish()
def food(root,i,slug):
 c=Collect(root,i)
 u="https://www.kaggle.com/api/v1/datasets/download/"+slug
 try:
  # Inspect directory taxonomy without reading image bodies.
  zf=RemoteZip(u,budget=12_000_000)
  import zipfile
  with zipfile.ZipFile(zf) as z:
   paths=[v.filename for v in z.infolist() if not v.is_dir() and v.filename.lower().endswith((".jpg",".jpeg",".png"))]
   hist=C.Counter()
   for v in paths:
    p=P.PurePosixPath(v);g=p.parent.as_posix()
    if re.match(r'^\d+_',p.name):g+="/"+p.name.split("_",1)[0]
    hist[g]+=1
   c.save(json.dumps({"image_member_count":len(paths),"group_hist":dict(hist)},ensure_ascii=False).encode(),"archive_class_index.json",u,"NATIVE_METADATA",extra={"archive_bytes":zf.size,"range_mode":True})
   for j,v in enumerate(food_select([v for v in z.infolist() if not v.is_dir()])):
    if v.file_size>2_000_000:continue
    x=z.read(v)
    c.save(x,"image_"+str(j)+P.Path(v.filename).suffix.lower(),u,"MIRROR_NATIVE_MEMBERS",extra={"archive_member":v.filename,"member_uncompressed_bytes":v.file_size,"complete_member":True,"member_crc32":f"{v.CRC:08x}"})
   c.rec["archive_range_bytes"]=zf.used
 except Exception as e:c.fail("Kaggle bounded native archive",e)
 c.rec["notes"].append("Candidate regrouped Kaggle mirror of EPFL originals; verify actual class/split taxonomy, not only dataset title.")
 return c.finish()
def recipe(root):
 c=Collect(root,18)
 c.hf("Schmitz005/recipe_nlg_dataset_sample",images=0)
 c.rec["notes"].append("Alternative public sample mirror; source/URL and original RecipeNLG schema still require audit.")
 return c.finish()
def main(root,out):
 if root.exists() or out.exists():raise ValueError("refuse overwrite")
 root.mkdir(parents=True)
 with F.ThreadPoolExecutor(max_workers=4) as e:
  fs=[e.submit(snap,root),e.submit(food,root,6,"trolukovich/food11-image-dataset"),e.submit(food,root,14,"trolukovich/food5k-image-dataset"),e.submit(recipe,root)]
  records=[]
  for f in F.as_completed(fs):
   a=f.result();records.append(a);print(a["asset_id"],a["status"],a["file_count"],a["saved_bytes"],a["attempts"],flush=True)
 records.sort(key=lambda x:x["asset_id"])
 with out.open("x",encoding="utf8") as h:json.dump({"records":records},h,ensure_ascii=False,indent=2)
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,required=True);a.add_argument("--manifest",type=P.Path,required=True);x=a.parse_args();main(x.root,x.manifest)
