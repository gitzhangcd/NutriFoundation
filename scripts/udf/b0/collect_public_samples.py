#!/usr/bin/env python3
"""Bounded B0 public-source acquisition. Local-only raw assets, metadata-only public receipts.
Does not accept access agreements, authenticate to gated sources, run remote code, or extract archives wholesale.
"""
import argparse, collections as C, csv, datetime as DT, hashlib, io, json, pathlib as P, re, struct, tarfile, urllib.parse as Q, urllib.request as U, urllib.error, zipfile, zlib, concurrent.futures as F
UA="NutriOne-UDF-B0 research sample audit/0.1"
CAP=25_000_000
NOW=DT.datetime.now(DT.timezone.utc).isoformat()
NAMES=["Food-101","UEC-Food100","UEC-Food256","SNAPMe","ISIA Food-500","Food-11","iFood 2019 / FoodX-251","Food-101N","Fruits-360","Food2K","VIREO Food-172","XiaChuFang","Pre-NeRF 360 / N5k360","Food-5K","FoodieQA","Open Food Facts","Menu-Match","RecipeNLG","eButton","RecipeQA","UNIMIB2016","EPIC-KITCHENS-100"]
def req(u,headers=None):
 return U.Request(u,headers={"User-Agent":UA,"Accept-Encoding":"identity",**(headers or {})})
def fetch(u,cap=CAP,headers=None):
 with U.urlopen(req(u,headers),timeout=16) as r:
  if r.headers.get("Content-Length","").isdigit() and int(r.headers["Content-Length"])>cap:raise ValueError("advertised response exceeds cap")
  b=r.read(cap+1)
  if len(b)>cap:raise ValueError("response exceeds cap")
  return b,{"http":r.status,"content_type":r.headers.get("Content-Type",""),"etag":r.headers.get("ETag"),"last_modified":r.headers.get("Last-Modified"),"retrieval_url":u}
def jget(u,cap=2_000_000):
 b,m=fetch(u,cap);return json.loads(b),b,m
def sha(b):return hashlib.sha256(b).hexdigest()
def type_shape(x,depth=0):
 if depth>=2:return type(x).__name__
 if isinstance(x,dict):return {str(k):type_shape(v,depth+1) for k,v in x.items()}
 if isinstance(x,list):return {"type":"list","first":type_shape(x[0],depth+1) if x else None}
 return type(x).__name__
def mat_shapes(b):
 if len(b)<128 or not b.startswith(b"MATLAB"):return {"mat_format":"unrecognized"}
 en="<" if b[126:128]==b"IM" else ">"
 def elems(v):
  p=0
  while p+8<=len(v):
   t,n=struct.unpack_from(en+"II",v,p)
   if t>>16:
    if en=="<":tt,nn=t&65535,t>>16
    else:tt,nn=t>>16,t&65535
    if nn>4:break
    yield tt,v[p+4:p+4+nn];p+=8
   else:
    if n>len(v)-p-8:break
    yield t,v[p+8:p+8+n]
    p+=8+n if t==15 else 8+((n+7)//8)*8
 def m(v,out):
  for t,x in elems(v):
   if t==15:
    zz=zlib.decompressobj();xx=zz.decompress(x,10_000_001)
    if len(xx)>10_000_000 or zz.unconsumed_tail:raise ValueError("MAT decompression cap")
    m(xx,out)
   if t==14:
    a=list(elems(x))
    if len(a)>=3:
     dims=a[1][1]; nm=a[2][1].decode("utf8","replace")
     out.append({"variable":nm,"shape":list(struct.unpack(en+"i"*(len(dims)//4),dims)) if len(dims)%4==0 else None})
 out=[];m(b[128:],out);return {"mat_format":"MATLAB v5","variables":out}
def profile(b,filename,kind=None):
 try:
  s=filename.lower()
  if s.endswith(".mat"):return mat_shapes(b)
  if s.endswith((".jpg",".jpeg",".png")):
   return {"media_bytes":len(b),"signature":"JPEG" if b.startswith(b"\xff\xd8\xff") else "PNG" if b.startswith(b"\x89PNG\r\n\x1a\n") else "UNRECOGNIZED"}
  if s.endswith(".json"):
   x=json.loads(b)
   if isinstance(x,dict) and isinstance(x.get("rows"),list):
    rows=[v.get("row",{}) for v in x["rows"]]
    return {"viewer_rows":len(rows),"total_reported":x.get("num_rows_total"),"row_fields":list(rows[0]) if rows else [],"field_shapes":type_shape(rows[0]) if rows else {}, "row_indexes":[v.get("row_idx") for v in x["rows"]],"features":[{"name":v.get("name"),"type":v.get("type")} for v in x.get("features",[])]}
   if isinstance(x,list):return {"json_top":"list","records":len(x),"first_record_fields":list(x[0]) if x and isinstance(x[0],dict) else [],"shape":type_shape(x[0]) if x else None}
   if isinstance(x,dict):
    lists={k:len(v) for k,v in x.items() if isinstance(v,list)}
    return {"json_top":"object","keys":list(x)[:60],"list_lengths":lists,"shape":type_shape({k:x[k] for k in list(x)[:18]})}
  if s.endswith((".csv",".tsv",".txt")):
   enc=None
   for candidate in ("utf-8-sig","gb18030"):
    try:t=b.decode(candidate);enc=candidate;break
    except UnicodeDecodeError:pass
   if enc is None:return {"encoding":"UNRESOLVED"}
   lines=[x for x in t.splitlines() if x.strip()]
   if s.endswith((".csv",".tsv")):
    rows=list(csv.reader(io.StringIO(t),delimiter="\t" if s.endswith(".tsv") else ","))
    width=C.Counter(len(x) for x in rows)
    hdr=rows[0] if rows and kind=="headered" else []
    return {"encoding":enc,"nonempty_lines":len(lines),"csv_rows_including_possible_header":len(rows),"column_width_hist":dict(width),"header":hdr,"header_status":"declared_headered" if hdr else "UNCONFIRMED","first_record_width":len(rows[0]) if rows else 0}
   return {"encoding":enc,"nonempty_lines":len(lines),"first_line_tokens":len(lines[0].split()) if lines else 0,"line_token_width_hist":dict(C.Counter(len(x.split()) for x in lines))}
  if s.endswith((".html",".md")):return {"document_only":True,"bytes":len(b)}
  return {"bytes":len(b),"extension":P.Path(filename).suffix}
 except Exception as e:return {"profile_error":type(e).__name__+":"+str(e)[:160]}
class RemoteZip(io.RawIOBase):
 def __init__(self,u,budget=15_000_000):
  self.u=u;self.used=0;self.calls=0;self.budget=budget;self.pos=0
  with U.urlopen(req(u,{"Range":"bytes=0-0"}),timeout=15) as r:
   cr=r.headers.get("Content-Range","")
   if r.status!=206 or not re.fullmatch(r"bytes 0-0/\d+",cr):raise ValueError("HTTP Range unsupported (no full archive fetched)")
   self.size=int(cr.rsplit("/",1)[1]);self.etag=r.headers.get("ETag")
   if len(r.read(2))!=1:raise ValueError("unexpected range length")
  self.used=1;self.calls=1
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,o,w=0):
  p=o if w==0 else self.pos+o if w==1 else self.size+o
  if p<0:raise ValueError("negative seek")
  self.pos=p;return p
 def read(self,n=-1):
  if self.pos>=self.size:return b""
  n=self.size-self.pos if n<0 else min(n,self.size-self.pos)
  if n<=0:return b""
  if self.used+n>self.budget or self.calls>=48:raise ValueError("range budget exceeded")
  start=self.pos;end=start+n-1
  with U.urlopen(req(self.u,{"Range":f"bytes={start}-{end}"}),timeout=15) as r:
   if r.status!=206 or r.headers.get("Content-Range")!=f"bytes {start}-{end}/{self.size}":raise ValueError("incorrect range response")
   e=r.headers.get("ETag")
   if self.etag and e and self.etag!=e:raise ValueError("archive changed between ranges")
   b=r.read(n+1)
  if len(b)!=n:raise ValueError("range length mismatch")
  self.pos+=n;self.used+=n;self.calls+=1
  return b
class Collect:
 def __init__(self,root,i):
  self.i=i;self.id=f"NDF-G{i:03d}";self.root=root/self.id;self.root.mkdir()
  self.rec={"asset_id":self.id,"name":NAMES[i-1],"purpose":"CURATION_DEV_ONLY","files":[],"attempts":[],"notes":[],"status":"NO_RECORD_ACQUIRED","version_relation_to_user_copy":"UNRESOLVED"}
 def fail(self,label,e):self.rec["attempts"].append({"attempt":label,"status":"HOLD","reason":str(e)[:260]})
 def save(self,b,name,url,role,meta=None,kind=None,extra=None):
  if P.Path(name).name!=name:raise ValueError("unsafe output filename")
  if not b:raise ValueError("empty body")
  f=self.root/name
  with f.open("xb") as h:h.write(b)
  p=profile(b,name,kind)
  rec={"file":name,"source_url":url,"role":role,"bytes":len(b),"sha256":sha(b),"profile":p,**(meta or {}),**(extra or {})}
  self.rec["files"].append(rec)
  return rec
 def raw(self,u,name,role="NATIVE_METADATA",cap=CAP,kind=None):
  try:
   b,m=fetch(u,cap)
   if "text/html" in m["content_type"] and not name.endswith(".html"):raise ValueError("HTML instead of requested data")
   if b.startswith(b"version https://git-lfs.github.com/spec/v1"):raise ValueError("Git LFS pointer, not data")
   return self.save(b,name,u,role,m,kind)
  except Exception as e:self.fail(u,e);return None
 def hf(self,repo,role="MIRROR_SAMPLE",split="train",n=12,config=None,images=2):
  try:
   info,_,_=jget("https://huggingface.co/api/datasets/"+repo)
   if info.get("gated"):raise PermissionError("source gated; no access conditions accepted")
   observed=info.get("sha")
   card="https://huggingface.co/datasets/"+repo+"/resolve/"+str(observed)+"/README.md"
   self.raw(card,"hf_README.md","SOURCE_DESCRIPTION",200_000)
   sp,_,_=jget("https://datasets-server.huggingface.co/splits?"+Q.urlencode({"dataset":repo}))
   opts=[x for x in sp.get("splits",[]) if x.get("split")==split and (not config or x.get("config")==config)]
   if not opts:raise ValueError("requested split unavailable")
   opt=opts[0];u="https://datasets-server.huggingface.co/rows?"+Q.urlencode({"dataset":repo,"config":opt["config"],"split":split,"offset":0,"length":n})
   b,m=fetch(u,2_500_000);x=json.loads(b)
   rows=x.get("rows",[])
   if not rows:raise ValueError("viewer returned no rows")
   if any(not isinstance(v.get("row"),dict) for v in rows):raise ValueError("unexpected viewer rows")
   self.save(b,"hf_rows.json",u,role,m,extra={"repository_sha_observed":observed,"viewer_revision_not_guaranteed":True,"split":split,"config":opt["config"],"selection":"first bounded rows; not random; development exposure"})
   self.rec["notes"].append("HF viewer/mirror representation is not a proof of original archive equivalence or revision match.")
   def urls(v):
    if isinstance(v,dict):
     if isinstance(v.get("src"),str) and v["src"].startswith("https://"):yield v["src"]
     for a in v.values():yield from urls(a)
    elif isinstance(v,list):
     for a in v:yield from urls(a)
   for j,u2 in enumerate(list(dict.fromkeys(urls(rows)))[:images]):
    try:
     d,m2=fetch(u2,2_000_000)
     ext=".jpg" if d.startswith(b"\xff\xd8\xff") else ".png" if d.startswith(b"\x89PNG\r\n\x1a\n") else None
     if not ext:raise ValueError("unrecognized media bytes")
     # Signed URLs only appear in local raw response; receipt references that response.
     self.save(d,"sample_image_"+str(j)+ext,u,"SAMPLE_MEDIA",{"http":m2["http"],"content_type":m2["content_type"]},extra={"source_locator":"hf_rows.json media URL ordinal "+str(j)})
    except Exception as e:self.fail("HF media "+str(j),e)
   return True
  except Exception as e:self.fail("HF "+repo,e);return False
 def zip_select(self,u,role,selection,full_cap=8_000_000):
  try:
   zf=RemoteZip(u)
   z=zipfile.ZipFile(zf)
   range_mode=True
  except Exception as e:
   self.fail("range ZIP "+u,e)
   if full_cap<=0:return False
   try:
    b,m=fetch(u,full_cap)
    z=zipfile.ZipFile(io.BytesIO(b));zf=None;range_mode=False
   except Exception as e2:self.fail("bounded ZIP "+u,e2);return False
  try:
   infos=[v for v in z.infolist() if not v.is_dir()]
   chosen=selection(infos)
   if not chosen:raise ValueError("no matching member metadata")
   self.rec["archive_info"]={"url":u,"member_count":len(infos),"range_mode":range_mode,"size":getattr(zf,"size",None),"selected_member_names":[v.filename for v in chosen]}
   for j,v in enumerate(chosen[:12]):
    try:
     cap=2_000_000
     if v.file_size>150_000_000:raise ValueError("member exceeds decompression guard")
     with z.open(v) as f:b=f.read(min(v.file_size,cap))
     suffix=P.Path(v.filename).suffix.lower()
     if not suffix:suffix=".txt"
     if v.file_size>cap and suffix not in (".txt",".csv",".tsv"):raise ValueError("nontext member too large for complete extraction")
     full=len(b)==v.file_size
     if not full:
      idx=b.rfind(b"\n")
      if idx<=0:raise ValueError("no complete newline in prefix")
      b=b[:idx+1]
     nm=f"zip_{j:02d}_"+re.sub(r"[^A-Za-z0-9_.-]","_",P.Path(v.filename).name)
     if not full:nm=nm.rsplit(".",1)[0]+"_prefix"+suffix
     self.save(b,nm,u,role,extra={"archive_member":v.filename,"member_uncompressed_bytes":v.file_size,"member_crc32":f"{v.CRC:08x}","complete_member":full,"range_mode":range_mode})
    except Exception as e:self.fail("ZIP member "+v.filename,e)
   if zf:self.rec["archive_info"].update({"bytes_received":zf.used,"range_requests":zf.calls})
   return any(f["role"]==role for f in self.rec["files"])
  except Exception as e:self.fail("ZIP select "+u,e);return False
  finally:z.close()
 def snapme(self):
  u="https://api.figshare.com/v2/articles/24856449"
  self.raw(u,"figshare_article.json","SOURCE_DESCRIPTION",1_000_000)
  # A compressed tar has no independent member offsets. Inspect a small prefix only.
  u="https://ndownloader.figshare.com/files/44532971"
  try:
   with U.urlopen(req(u,{"Range":"bytes=0-8388607"}),timeout=16) as r:
    b=r.read(8_388_608)
    self.rec["prefix_http"]={"status":r.status,"received_bytes":len(b),"content_range":r.headers.get("Content-Range")}
   if not b.startswith(b"\x1f\x8b"):raise ValueError("not gzip archive prefix")
   names=[];n=0;total=0
   try:
    with tarfile.open(fileobj=io.BytesIO(b),mode="r|gz") as t:
     for v in t:
      if len(names)>=80 or total+v.size>64_000_000:break
      total+=v.size;names.append({"name":v.name,"size":v.size})
      if v.isfile() and v.size<=1_000_000 and v.name.lower().endswith((".csv",".json",".txt",".tsv",".xlsx")) and n<3:
       f=t.extractfile(v)
       if f is None:continue
       data=f.read(v.size+1)
       if len(data)!=v.size:break
       self.save(data,"tar_"+str(n)+"_"+re.sub(r"[^A-Za-z0-9_.-]","_",P.Path(v.name).name),u,"NATIVE_ARCHIVE_SAMPLE",extra={"archive_member":v.name,"selection":"bounded gzip prefix; original local snapshot not verified"})
       n+=1
   except (EOFError,tarfile.ReadError,OSError) as e:self.fail("tar prefix ended",e)
   self.rec["prefix_members_count"]=len(names)
   # Member names may include human data identifiers; local only.
   self.save(json.dumps(names,ensure_ascii=False).encode(),"tar_prefix_member_index.json",u,"ARCHIVE_INDEX_ONLY")
  except Exception as e:self.fail("SNAPMe bounded gzip prefix",e)
 def finish(self):
  roles={x["role"] for x in self.rec["files"]}
  if roles&{"NATIVE_ARCHIVE_SAMPLE","NATIVE_RECORDS","AUTHOR_TOY_SAMPLE","NATIVE_METADATA","SAMPLE_MEDIA","MIRROR_NATIVE_MEMBERS","MIRROR_SAMPLE","DERIVED_MIRROR_SAMPLE"}:
   if roles&{"NATIVE_ARCHIVE_SAMPLE","NATIVE_RECORDS","AUTHOR_TOY_SAMPLE"}:s="SOURCE_RECORDS_OR_AUTHOR_SAMPLE"
   elif roles&{"MIRROR_NATIVE_MEMBERS","MIRROR_SAMPLE","DERIVED_MIRROR_SAMPLE"}:s="MIRROR_SAMPLE_PROVISIONAL"
   else:s="METADATA_OR_MEDIA_ONLY"
   self.rec["status"]=s
  if not self.rec["files"]:self.rec["status"]="HOLD_NO_BYTES"
  self.rec["qualification"]="CURATION_DEV_CANDIDATE_ONLY; NO_RELEASE"
  self.rec["file_count"]=len(self.rec["files"]);self.rec["saved_bytes"]=sum(x["bytes"] for x in self.rec["files"])
  return self.rec
def uec_select(infos):
 names=[v for v in infos if P.Path(v.filename).name.lower() in ("category.txt","category_ja.txt","category_ja_utf8.txt","multiple_food.txt","readme.txt")]
 bb=[v for v in infos if v.filename.lower().endswith("/bb_info.txt")]
 jpg=[v for v in infos if v.filename.lower().endswith((".jpg",".jpeg"))]
 return names[:5]+bb[:2]+jpg[:2]
def meta_select(infos):
 cand=[v for v in infos if v.filename.lower().endswith((".txt",".csv",".json",".tsv",".mat",".xml"))]
 return sorted(cand,key=lambda v:(0 if any(x in v.filename.lower() for x in ("class","category","label","meta","train","test","annotation","split","ingr","menu")) else 1,v.file_size))[:10]
def runone(root,i):
 c=Collect(root,i)
 try:
  if i==1:
   c.raw("https://huggingface.co/datasets/ethz/food101/resolve/ce7ff16231a85be196133cfd01d570e64a41dad0/dataset_infos.json","dataset_infos.json","NATIVE_METADATA")
   r=c.raw("https://s3.amazonaws.com/datasets.huggingface.co/food101/meta/train.txt","train.txt","NATIVE_METADATA",2_000_000)
   if r:r["published_checksum_match"]=r["sha256"]=="2920f7d55473974492b41a01241ccfd71df1b74d29d27b617337f840f58f77ab"
   c.hf("ethz/food101",role="NATIVE_RECORDS")
  elif i in (2,3):
   ver="100" if i==2 else "256"
   u="https://huggingface.co/datasets/kng-research/uecfood256/resolve/5dd3860447882fa13e5150af0037fe672c9dbe4d/dataset"+ver+".zip"
   c.zip_select(u,"MIRROR_NATIVE_MEMBERS",uec_select,0)
   c.notes=[] if False else None
   c.rec["notes"].append("Public mirror original-archive candidate, not verified against user's downloaded ZIP.")
  elif i==4:c.snapme()
  elif i==5:
   u="http://123.57.42.89/Dataset_ict/ISIA_Food500_Dir/dataset/metadata_ISIAFood_500.zip"
   ok=c.zip_select(u,"NATIVE_ARCHIVE_SAMPLE",meta_select,12_000_000)
   if not ok:c.hf("advancedcv/isiafoodcap_all",role="DERIVED_MIRROR_SAMPLE")
  elif i==6:c.hf("cv-talks/food-11")
  elif i==7:
   c.raw("https://raw.githubusercontent.com/SandroErba/FoodX-251/main/dataset/train_info_dirty.csv","train_info_dirty.csv","MIRROR_SAMPLE",3_000_000)
   c.raw("https://raw.githubusercontent.com/SandroErba/FoodX-251/main/README.md","README.md","SOURCE_DESCRIPTION",100_000)
  elif i==8:
   c.raw("https://kuanghuei.github.io/Food-101N/","official.html","SOURCE_DESCRIPTION",500_000)
   c.rec["notes"].append("Original download requires terms acceptance; do not bypass. Food-101 class identity alone is not Food-101N verification labels.")
  elif i==9:
   base="https://api.github.com/repos/fruits-360/fruits-360-100x100/contents/Training?ref=main"
   try:
    x,b,m=jget(base,2_000_000)
    dirs=[a for a in x if a.get("type")=="dir"]
    # Store actual directory list; repo path identities preserved.
    c.save(b,"training_categories.json",base,"NATIVE_METADATA",m)
    if dirs:
     p=dirs[0]["path"];u="https://api.github.com/repos/fruits-360/fruits-360-100x100/contents/"+Q.quote(p)+ "?ref=main"
     x,b,m=jget(u,2_000_000);c.save(b,"first_category_files.json",u,"NATIVE_METADATA",m)
     for j,a in enumerate([v for v in x if v.get("name","").lower().endswith(".jpg")][:2]):
      c.raw(a["download_url"],f"fruit_{j}.jpg","SAMPLE_MEDIA",300_000)
   except Exception as e:c.fail("official GitHub directory",e)
   c.raw("https://raw.githubusercontent.com/fruits-360/fruits-360-meta/main/dictionary.txt","meta_dictionary.txt","NATIVE_METADATA",300_000)
   c.raw("https://raw.githubusercontent.com/fruits-360/fruits-360-meta/main/Meta/Apple%20Golden%201/info.txt","meta_apple_golden_1.txt","NATIVE_RECORDS",100_000)
   c.rec["notes"].append("Current official image/metadata repositories may represent different releases; do not assume version equivalence or object-level pairing.")
  elif i==10:
   c.raw("http://123.57.42.89/FoodProject.html","official.html","SOURCE_DESCRIPTION",500_000)
   c.raw("https://raw.githubusercontent.com/Liuyuxinict/prenet/master/README.md","author_README.md","SOURCE_DESCRIPTION",100_000)
   c.rec["notes"].append("Official page points to agreement/full data; no small native sample/label file found in author repo in this round.")
  elif i==11:
   base="https://raw.githubusercontent.com/PublicRelease/FoodRecog/master/VireoFood-172/"
   c.raw("https://raw.githubusercontent.com/PublicRelease/FoodRecog/master/README.md","author_README.md","SOURCE_DESCRIPTION",100_000)
   c.raw(base+"readMe","author_format.txt","SOURCE_DESCRIPTION",100_000)
   for n in ["train_label.mat","test_label.mat","indexVector_train.mat","indexVector_test.mat","wordIndicator_train.mat","wordIndicator_test.mat","wordVector.mat"]:
    c.raw(base+"Data/"+n,n,"AUTHOR_TOY_SAMPLE" if n!="wordVector.mat" else "NATIVE_METADATA",1_000_000)
   c.rec["notes"].append("Author states first 32 examples (model input toy files). These are processed input matrices, not native image-instance ingredient truth or full 353-dimensional raw labels.")
  elif i==12:c.hf("xzm1999/XiaChuFang_Recipe_Corpus",images=0)
  elif i==13:
   base="https://storage.googleapis.com/nutrition5k_dataset/nutrition5k_dataset/"
   for n in ["dish_metadata_cafe1.csv","dish_metadata_cafe2.csv","ingredients_metadata.csv"]:
    c.raw(base+"metadata/"+n,n,"NUTRITION5K_FALLBACK_METADATA",3_000_000,kind="headered" if n.startswith("ingredients") else None)
   for n in ["rgb_train_ids.txt","rgb_test_ids.txt","depth_train_ids.txt","depth_test_ids.txt"]:
    c.raw(base+"dish_ids/splits/"+n,n,"NUTRITION5K_FALLBACK_METADATA",200_000)
   c.raw("https://raw.githubusercontent.com/amughrabi/N5k360/main/README.md","n5k360_author_README.md","SOURCE_DESCRIPTION",100_000)
   c.raw("https://raw.githubusercontent.com/google-research-datasets/Nutrition5k/main/README.md","nutrition5k_README.md","SOURCE_DESCRIPTION",100_000)
   # Native fallback image and depth for one train ID, not a NeRF-scale certificate.
   try:
    ids=(c.root/"depth_train_ids.txt").read_text().split()
    dish=ids[0]
    if not re.fullmatch(r"dish_\d+",dish):raise ValueError("unexpected dish ID")
    for n in ["rgb.png","depth_raw.png","depth_color.png"]:
     c.raw(base+"imagery/realsense_overhead/"+dish+"/"+n,"fallback_"+dish+"_"+n,"NUTRITION5K_FALLBACK_MEDIA",2_500_000)
    c.rec["notes"].append("N5k360 exact scene metadata/absolute geometry remains HOLD. Original Nutrition5k is an independent, official fallback asset, not a substitute counted as N5k360 native acquisition.")
   except Exception as e:c.fail("fallback media",e)
  elif i==14:c.hf("marwanatef4444/food_5k")
  elif i==15:
   c.raw("https://raw.githubusercontent.com/lyan62/FoodieQA/main/README.md","author_README.md","SOURCE_DESCRIPTION",100_000)
   c.rec["notes"].append("Author HF release requires accepting access conditions; no access agreement or mirror bypass attempted.")
  elif i==16:
   base="https://world.openfoodfacts.org/api/v2/"
   fields="code,product_name,brands,ingredients_text,nutriments,nutrition_data_per,serving_size,quantity,food_groups_tags,allergens_tags,countries_tags"
   c.raw(base+"product/737628064502.json?"+Q.urlencode({"fields":fields}),"product_737628064502.json","NATIVE_RECORDS",500_000)
   c.raw(base+"search?"+Q.urlencode({"categories_tags_en":"breakfast-cereals","page_size":10,"fields":fields}),"search_breakfast_cereals.json","NATIVE_RECORDS",1_000_000)
   c.rec["notes"].append("Current API response, not historical 1.5 TB download version; preserve per-100/serving and label-derived status.")
  elif i==17:
   c.zip_select("https://neelj.com/projects/menumatch/data/menu_match_dataset.zip","NATIVE_ARCHIVE_SAMPLE",meta_select,0)
   if not any(f["role"]=="NATIVE_ARCHIVE_SAMPLE" for f in c.rec["files"]):
    c.raw("https://neelj.com/projects/menumatch/data/","official.html","SOURCE_DESCRIPTION",500_000)
  elif i==18:c.hf("Zappandy/recipe_nlg",images=0)
  elif i==19:
   c.raw("https://www.cambridge.org/core/journals/public-health-nutrition/article/automatic-food-detection-in-egocentric-images-using-artificial-intelligence-technology/CAE3262B945CC45E4B14C06C83A68F42","publication.html","SOURCE_DESCRIPTION",2_000_000)
   c.rec["notes"].append("No raw eButton participant/image label files identified. Published examples do not qualify as raw dataset. No private images requested.")
  elif i==20:
   r=c.raw("https://vision.cs.hacettepe.edu.tr/files/recipeqa/val.json","official_val.json","NATIVE_RECORDS",25_000_000)
   if not r:c.hf("Eitanli/recipe_qa_dataset",role="MIRROR_SAMPLE",images=0)
   c.rec["notes"].append("Public validation or mirror sample used strictly for structure development; exposed items cannot be independent locked evaluation.")
  elif i==21:
   c.zip_select("https://www.kaggle.com/api/v1/datasets/download/dangvanthuc0209/unimib2016","MIRROR_NATIVE_MEMBERS",meta_select,0)
   c.rec["notes"].append("Kaggle archive mirror candidate; no whole archive transfer.")
  elif i==22:
   base="https://raw.githubusercontent.com/epic-kitchens/epic-kitchens-100-annotations/master/"
   for n in ["EPIC_100_train.csv","EPIC_100_verb_classes.csv","EPIC_100_noun_classes.csv","EPIC_100_video_info.csv"]:
    c.raw(base+n,n,"NATIVE_RECORDS" if n.endswith("train.csv") else "NATIVE_METADATA",10_000_000,kind="headered")
  else:raise ValueError("unsupported dataset")
 except Exception as e:c.fail("dataset acquisition",e)
 return c.finish()
def main(root,output):
 if root.exists() or output.exists():raise ValueError("refuse overwrite")
 root.mkdir(parents=True)
 records=[]
 with F.ThreadPoolExecutor(max_workers=6) as ex:
  futures={ex.submit(runone,root,i):i for i in range(1,23)}
  for f in F.as_completed(futures):
   r=f.result();records.append(r)
   print(r["asset_id"],r["status"],r["file_count"],r["saved_bytes"],"attempts",len(r["attempts"]),flush=True)
 records.sort(key=lambda r:r["asset_id"])
 with output.open("x",encoding="utf8") as f:json.dump({"run_time_utc":NOW,"purpose":"CURATION_DEV","records":records},f,ensure_ascii=False,indent=2)
 print("SUMMARY",json.dumps({"status_counts":dict(C.Counter(r["status"] for r in records)),"files":sum(r["file_count"] for r in records),"saved_bytes":sum(r["saved_bytes"] for r in records)},ensure_ascii=False),flush=True)
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,required=True);a.add_argument("--manifest",type=P.Path,required=True);x=a.parse_args();main(x.root,x.manifest)
