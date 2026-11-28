"""Independent reviewer-driven raw-standard lookup. No candidate pools, prior
review outcomes, tested-method lexicon, or frozen target universe are inputs."""
import csv,io,json,re,unicodedata,collections
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as E
S=("FoodOn","FDC_SR_Legacy","FNDDS")
VERSION={"FoodOn":"2026-09-20","FDC_SR_Legacy":"2018-04","FNDDS":"2015-16"}
PREFIX="runs/B2/U3-A/inputs/"
def require(x,code):
 if not x:raise ValueError(code)
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def norm(s):return " ".join(re.findall(r"[^\W_]+",unicodedata.normalize("NFKC",str(s)).casefold(),flags=re.UNICODE))
def json_answer(s):
 x=s.strip();fence=chr(96)*3
 if x.startswith(fence):
  a=x.splitlines();require(a[-1].strip()==fence,"MALFORMED_FENCE");x="\n".join(a[1:-1])
 return json.loads(x)
class Standards:
 def __init__(self,root,hashes):
  self.rows={a:[] for a in S};self.by={}
  def add(sys,id,label,loc,source,aliases=(),definition=""):
   k=(sys,VERSION[sys],str(id));require(k not in self.by,"DUPLICATE_RAW_ID")
   row={"target_key":list(k),"target_native_label":label,"target_locator":loc,"artifact_sha256":hashes[source]}
   if aliases:row["raw_aliases"]=list(aliases)
   if definition:row["raw_definition"]=definition[:450]
   self.by[k]=row
   forms=[norm(label)]+[norm(a) for a in aliases if a]
   self.rows[sys].append((row,forms,[set(f.split()) for f in forms]))
  rdf="{http://www.w3.org/1999/02/22-rdf-syntax-ns#}";owl="{http://www.w3.org/2002/07/owl#}";rdfs="{http://www.w3.org/2000/01/rdf-schema#}"
  path=PREFIX+"FoodOn.owl";tree=E.parse(root/path).getroot()
  for e in tree.findall(owl+"Class"):
   iri=e.get(rdf+"about");label=e.find(rdfs+"label")
   if not iri or label is None or not label.text:continue
   if any(c.tag==owl+"deprecated" and (c.text or "").lower()=="true" for c in e):continue
   alias=[c.text for c in e if c.text and c.tag.rsplit("}",1)[-1] in ("hasExactSynonym","hasRelatedSynonym","hasBroadSynonym","hasNarrowSynonym")]
   definition=next((c.text for c in e if c.text and c.tag.rsplit("}",1)[-1]=="IAO_0000115"),"")
   add("FoodOn",iri,label.text,path+"#rdf:about="+iri,path,alias,definition)
  def csv_member(path,name):
   with ZipFile(root/path) as z:
    mm=[m for m in z.namelist() if Path(m).name==name];require(len(mm)==1,"RAW_CSV_MEMBER")
    with z.open(mm[0]) as f:rows=list(csv.DictReader(io.TextIOWrapper(f,encoding="utf-8-sig",newline="")))
    return mm[0],rows
  path=PREFIX+"FDC_SR_2018.zip";m,rs=csv_member(path,"food.csv")
  for i,r in enumerate(rs,2):add("FDC_SR_Legacy",r["fdc_id"],r["description"],path+"!"+m+":row:"+str(i),path)
  path=PREFIX+"FNDDS_2015_16.zip";_,foods=csv_member(path,"food.csv");ms,sur=csv_member(path,"survey_fndds_food.csv")
  fs={r["fdc_id"]:r["description"] for r in foods};require(len(fs)==len(foods),"DUPLICATE_FDC")
  xlsx=PREFIX+"FNDDS_ARS_foods_2015_16.xlsx";ns="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}";ars={}
  with ZipFile(root/xlsx) as z:
   wb=E.fromstring(z.read("xl/workbook.xml"));require([x.get("name") for x in wb.iter(ns+"sheet")][0]=="Foods and Beverages","ARS_SHEET")
   ss=[''.join(x.itertext()) for x in E.fromstring(z.read("xl/sharedStrings.xml")).findall(ns+"si")]
   sh=E.fromstring(z.read("xl/worksheets/sheet1.xml"))
   for r in sh.iter(ns+"row"):
    rn=int(r.get("r"));d={}
    if rn<=2:continue
    for c in r.findall(ns+"c"):
     v=c.find(ns+"v")
     if v is None:continue
     val=v.text or "";val=ss[int(val)] if c.get("t")=="s" else val
     d[re.match(r"[A-Z]+",c.get("r","")).group()]=val
    if not d.get("A"):continue
    require(d["A"] not in ars,"DUPLICATE_ARS_CODE");ars[d["A"]]=(rn,d.get("B",""),d.get("C",""))
  for i,r in enumerate(sur,2):
   code=r["food_code"];require(code in ars and r["fdc_id"] in fs,"FNDDS_JOIN")
   rn,label,extra=ars[code];require(fs[r["fdc_id"]].strip()==label.strip(),"FNDDS_LABEL_MISMATCH")
   loc=path+"!"+ms+":row:"+str(i)+" | "+xlsx+"!Foods and Beverages:row:"+str(rn)
   add("FNDDS",code,fs[r["fdc_id"]],loc,path,[extra] if extra else [])
  require(all(self.rows[s] for s in S),"EMPTY_AUTHORITY")
 def search(self,system,terms,cap=5):
  out={}
  for term in terms:
   q=norm(term);qt=set(q.split());found=[]
   if not q:out[term]=[];continue
   for row,forms,toks in self.rows[system]:
    id=row["target_key"][2];label=forms[0]
    if term==id:score=(0,0,0,id)
    elif q==label:score=(1,0,0,id)
    elif q in forms[1:]:score=(2,0,0,id)
    elif any(" "+q+" " in " "+a+" " for a in forms):score=(3,min(len(a) for a in forms if " "+q+" " in " "+a+" "),len(label),id)
    elif any(qt<=t for t in toks):score=(4,min(len(t-qt) for t in toks if qt<=t),len(label),id)
    else:continue
    found.append((score,row))
   found.sort(key=lambda x:x[0]);out[term]=[r for _,r in found[:cap]]
  return out
def queries_ok(obj,batch):
 require(isinstance(obj,dict) and set(obj)=={"queries"} and isinstance(obj["queries"],list),"QUERY_ENVELOPE")
 ids={x["review_id"] for x in batch};out={}
 for r in obj["queries"]:
  require(isinstance(r,dict) and set(r)=={"review_id","systems"} and r["review_id"] in ids and r["review_id"] not in out,"QUERY_ID")
  q=r["systems"];require(isinstance(q,dict) and set(q)==set(S),"QUERY_SYSTEMS")
  for a in q.values():require(isinstance(a,list) and 1<=len(a)<=5 and len(a)==len(set(a)) and all(isinstance(x,str) and 0<len(x.strip())<=140 for x in a),"QUERY_TERMS")
  out[r["review_id"]]=q
 require(set(out)==ids,"QUERY_CLOSURE");return out
def validate_records(obj,batch,query,hits,standards,validator,hashes):
 require(isinstance(obj,dict) and set(obj)=={"records","review_note"} and isinstance(obj["review_note"],str) and isinstance(obj["records"],list),"REVIEW_ENVELOPE")
 by={x["review_id"]:x for x in batch};records=obj["records"];require(len(records)==len(by),"REVIEW_COUNT");seen=set()
 for r in records:
  errs=list(validator.iter_errors(r))
  if errs:raise ValueError("SCHEMA:"+"/".join(str(x) for x in errs[0].absolute_path)+":"+errs[0].validator)
  rid=r["review_id"];require(rid in by and rid not in seen,"REVIEW_ID");seen.add(rid);s=by[rid]
  require(all(r[k]==s[k] for k in ("review_id","source_ref","source_scope","source_native_label","native_kind")),"SOURCE_IDENTITY")
  allowed=set(hashes.values())|{s["artifact_sha256"]};ev=r["evidence"]
  require(all(x["artifact_sha256"] in allowed for x in ev),"EVIDENCE_ARTIFACT")
  source_locator=canon(s["source_locator"])
  def refs(ii):
   require(all(type(i)==int and 0<=i<len(ev) for i in ii),"EVIDENCE_INDEX");return [ev[i] for i in ii]
  for d in r["source_dimensions"].values():
   ee=refs(d["evidence_refs"])
   if d["state"]=="SOURCE_EXPLICIT":require(any(x["role"]=="SOURCE_EXPLICIT" and x["artifact_sha256"]==s["artifact_sha256"] and x["locator"]==source_locator for x in ee),"SOURCE_EVIDENCE_LOCATOR")
  attempts={x["target_system"]:x for x in r["search_attempts"]}
  require(set(attempts)==set(S),"SEARCH_SYSTEM_CLOSURE")
  require(all(attempts[k]["query_terms"]==query[rid][k] for k in S),"ACTUAL_QUERY_MISMATCH")
  retrieved={tuple(t["target_key"]) for ss in hits[rid].values() for rs in ss.values() for t in rs}
  pos=set();neg=set()
  for field,ids in (("independent_candidates",pos),("hard_negatives",neg)):
   cnt=collections.Counter()
   for c in r[field]:
    k=tuple(c["target_key"]);require(k in retrieved and k in standards.by and k not in ids,"NATIVE_TARGET_NOT_RETRIEVED_OR_DUPLICATE")
    v=standards.by[k];require(c["target_native_label"]==v["target_native_label"] and c["target_locator"]==v["target_locator"],"TARGET_LABEL_OR_LOCATOR")
    es=refs(c["evidence_refs"]);require(any(e["role"]=="TARGET_EXPLICIT" and e["artifact_sha256"]==v["artifact_sha256"] and e["locator"]==v["target_locator"] for e in es),"TARGET_EXPLICIT_EVIDENCE")
    ids.add(k);cnt[k[0]]+=1
   require(all(n<=3 for n in cnt.values()),"REFERENCE_MAX3_PER_SYSTEM")
  require(not pos&neg,"POS_NEG_CONFLICT")
 require(seen==set(by),"REVIEW_ID_CLOSURE");return records
