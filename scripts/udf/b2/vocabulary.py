#!/usr/bin/env python3
"""B2 U3-A: versioned source vocabularies and provenance families, development only.
All row-level outputs stay local. No original rows are modified, no equivalence accepted.
"""
import pathlib as P, csv, io, json, zipfile, hashlib, collections as C, re, sys
import xml.etree.ElementTree as E
from datetime import datetime, timezone
HERE=P.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/"b1b"),str(HERE.parent/"b1"),str(HERE.parent/"b0")]
from run_b1b import verify_inputs
from profile_nutridata_core_links import read_core
from profile_nutridata import M,sheets,read_rows
from contract import canon,digest,require,ContractError
VERSION="UDF-B2-VOCAB-DRAFT-0.1"
NOW=datetime.now(timezone.utc).isoformat()
PUB=P.Path("source_data/public_samples")
IN=P.Path("runs/B2/U3-A/inputs")
BASE=P.Path("runs/B1/U2-B/real_003")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def blob(p):
 b=p.read_bytes();return hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf8"))
def write_json(p,x):
 with p.open("x",encoding="utf8") as h:json.dump(x,h,ensure_ascii=False,indent=2,allow_nan=False);h.write("\n")
def write_lines(p,rows):
 with p.open("x",encoding="utf8") as h:
  for r in rows:h.write(canon(r)+"\n")
def lines(p):
 with p.open(encoding="utf-8-sig") as f:return [(i,s.rstrip("\r\n")) for i,s in enumerate(f,1) if s.strip()]
def zrows(p,name):
 with zipfile.ZipFile(p) as z:
  ms=[x for x in z.namelist() if P.PurePosixPath(x).name==name];require(len(ms)==1,"ZIP_MEMBER_UNIQUE")
  with z.open(ms[0]) as h:
   r=csv.DictReader(io.TextIOWrapper(h,encoding="utf-8-sig",newline=""))
   require(len(set(r.fieldnames))==len(r.fieldnames),"CSV_DUPLICATE_HEADER")
   return ms[0],list(r)
def unique(rows,key):
 d={}
 for r in rows:
  k=r[key];require(bool(k) and k not in d,"NONUNIQUE_NATIVE_KEY");d[k]=r
 return d
def obj(kind,key,payload,provenance=(),dependencies=(),real=False,origin="CON",source_class="REAL_DATA"):
 # Logical identity is snapshot scoped; revision includes the actual audit time.
 o={"object_id":"b2:"+kind+":"+digest([VERSION,key])[:40],"kind":kind,"schema_version":VERSION,"contract_version":VERSION,
    "lifecycle":"DRAFT","producer_role":"B2_CANDIDATE_ADAPTER","created_time":NOW,"clock_axis":"AUDIT_UTC",
    "source_class":source_class,"instance_class":"REAL_SOURCE_GROUNDED" if real else "MIXED_CONSTRUCTED","construction_class":origin,
    "provenance_refs":list(dict.fromkeys(provenance)),"dependency_refs":list(dict.fromkeys(dependencies)),
    "purpose":"CURATION_DEV","purpose_release_ref":{"tag":"PENDING","reason":"no release authorized"},"supersedes_ref":{"tag":"NOT_APPLICABLE","reason":"first draft revision","policy_ref":VERSION},"release_status":"HOLD","payload":payload}
 o["revision_id"]=digest(o);return o
def ref(o):return o["object_id"]+"@"+o["revision_id"]
def verify_obj(o):
 x=dict(o);h=x.pop("revision_id");require(digest(x)==h,"REVISION_MISMATCH")
 require(o["lifecycle"]=="DRAFT" and o["purpose"]=="CURATION_DEV" and o["release_status"]=="HOLD","RELEASE_BLOCKED")
def lang(x):
 return "zh_or_mixed" if re.search(r"[\u3400-\u9fff]",x) else "non_zh"
def string(x):return x if isinstance(x,str) else str(x)
def snapshot_id(scope,h):return scope+"@sha256:"+h
# Conservative family resolution. A common family is not proof of the same physical sample.
def nd_family(label):
 if label.startswith("《中国食物成分表》"):return "CHINA_FOOD_COMPOSITION_TABLE","DECLARED_EDITION","POTENTIAL_SHARED_UPSTREAM"
 if label=="美国农业部食物营养成分数据":return "USDA_COMPOSITION","DECLARED_AGENCY_RELEASE_UNKNOWN","POTENTIAL_SHARED_UPSTREAM"
 if label=="内部数据":return "NUTRIDATA_INTERNAL_UNRESOLVED","DECLARED_INTERNAL_UNKNOWN_METHOD","INDEPENDENCE_UNRESOLVED"
 if label in ("台湾","日本"):return "REGIONAL_COMPOSITION_"+("TAIWAN" if label=="台湾" else "JAPAN"),"REGION_ONLY","INDEPENDENCE_UNRESOLVED"
 if label=="《中国功能食品原料基本成分数据表》":return "CN_FUNCTIONAL_INGREDIENT_TABLE","DECLARED_COMPILATION","INDEPENDENCE_UNRESOLVED"
 if label=="成都市食品药品检验研究院":return "CN_CHENGDU_TEST_INSTITUTE","DECLARED_INSTITUTE_METHOD_UNKNOWN","INDEPENDENCE_UNRESOLVED"
 if label:return "COMMERCIAL_OR_ORGANIZATION_DECLARED","DECLARED_ORGANIZATION","INDEPENDENCE_UNRESOLVED"
 return "UNRESOLVED_SOURCE","NO_SOURCE_LABEL","INDEPENDENCE_UNRESOLVED"
def independent_guard(families):
 require(all(x["independence_status"]=="INDEPENDENCE_VERIFIED_FOR_TASK" for x in families),"INDEPENDENCE_NOT_QUALIFIED")
 require(len({x["potential_family"] for x in families})==len(families),"DEPENDENT_SOURCE_FAMILY")
class Inventory:
 def __init__(self,root):
  self.root=root;self.art={};self.records=[];self.by_scope=C.defaultdict(list);self.family_links=[];self.family_records={}
  self.stats={};self.component_counter=C.Counter();self.foodon_classes={};self.nd_sources=C.Counter();self.foodon_edges=[];self.snapshot_objects={};self.anchors=[]
  self.u2a,_,self.resolver=verify_inputs(root)
  expected={"B1BAdmissionReceipt.json":"6302a500486fd2fd5d34ad1f13979266da74b2df","ComponentConceptRegistry.json":"538c6c107e52589d230c932634e9dcc1e8bdf2b5","MeasurementDefinitionRegistry.json":"da17cf66673863be779f3c5534c74165273ee096"}
  for name,h in expected.items():require(blob(root/BASE/name)==h,"U2B_FENCE_CHANGED")
  self.old_components=load(root/BASE/"ComponentConceptRegistry.json")
  self.old_definitions=load(root/BASE/"MeasurementDefinitionRegistry.json")
  self.nd={x["file"]:x for x in load(root/"runs/B0/U1-A/NutriData_real_001/private/NativeFileManifest.json")}
  self.pub={}
  for r in load(root/"runs/B0/U1-A/public_samples_001/PublicSampleAudit_shareable.json")["records"]:
   for f in r["files"]:self.pub[(r["asset_id"],f["run"],f["file"])]=f
  self.external={x["file"]:x for x in load(root/IN/"AcquisitionManifest.json")["records"] if x["status"]=="DOWNLOADED"}
  self.external.update({x["file"]:x for x in load(root/IN/"FoodOnAcquisition.json") if x["status"]=="DOWNLOADED"})
  require(set(self.external)=={"FoodOn.owl","FDC_SR_2018.zip","FNDDS_2015_16.zip","FNDDS_ARS_foods_2015_16.xlsx"},"EXTERNAL_INPUT_INCOMPLETE")
 def register(self,scope,path,expected,role,version,source_url=None):
  p=self.root/path
  require(p.is_file() and not p.is_symlink() and sha(p)==expected,"SOURCE_ARTIFACT_HASH")
  if scope in self.art:require(self.art[scope]["sha256"]==expected,"SCOPE_SNAPSHOT_CONFLICT")
  self.art[scope]={"scope":scope,"file":path.name,"path":str(path),"sha256":expected,"bytes":p.stat().st_size,
      "snapshot_id":snapshot_id(scope,expected),"source_role":role,"version":version,"source_url":source_url}
  if scope not in self.snapshot_objects:self.snapshot_objects[scope]=obj("SourceSnapshotDraft",self.art[scope]["snapshot_id"],self.art[scope],real=True,origin="OBS")
  return p
 def public(self,scope,i,name,run="20261125_run001"):
  a=f"NDF-G{i:03d}";m=self.pub[(a,run,name)]
  return self.register(scope,PUB/run/a/name,m["sha256"],m["role"],"B0_PUBLIC_SNAPSHOT_ORIGINAL_VERSION_UNVERIFIED",m.get("source_url_no_query"))
 def ext(self,scope,name):
  m=self.external[name]
  return self.register(scope,IN/name,m["sha256"],"OFFICIAL_STANDARD_SNAPSHOT",m.get("versions",m.get("version_declared")),m["url"])
 def add(self,scope,key,label,kind,locator,aliases=None,meta=None):
  require(scope in self.art and isinstance(label,str) and label.strip(),"VOCAB_FIELD")
  a=self.art[scope];p={"native_namespace":scope,"snapshot_id":a["snapshot_id"],"artifact_sha256":a["sha256"],
    "native_key":string(key),"native_label":label,"label_language":lang(label),"native_kind":kind,
    "native_aliases":aliases or [],"source_locator":locator,"metadata":meta or {},
    "qualification":"NATIVE_VOCABULARY_ONLY","global_concept_identity":"UNRESOLVED"}
  snap=ref(self.snapshot_objects[scope]);derived="aggregate_from_label_column" in locator or "derived_from_archive_group_hist" in locator
  anchor=obj("VocabularyAnchorDraft",[a["snapshot_id"],string(key),kind,locator],{"source_snapshot_ref":snap,"artifact_sha256":a["sha256"],"locator":locator,"native_key":string(key),"scope":scope,"resolution":"NATIVE_LOGICAL_LOCATOR_OR_DECLARED_AGGREGATE","qualification":"CURATION_DEV_ONLY"},(snap,),(snap,),real=True,origin="DRV" if derived else "OBS")
  self.anchors.append(anchor);p["source_anchor_ref"]=ref(anchor)
  o=obj("NativeVocabularyRecord",[a["snapshot_id"],string(key),kind,locator],p,(ref(anchor),),(snap,ref(anchor)),real=True,origin="DRV" if derived else "OBS");self.records.append(o);self.by_scope[scope].append(o);return o
 def family(self,source,source_label,potential,status,independence,evidence):
  k=(source,source_label)
  if k not in self.family_records:
   p={"carrier_scope":source,"reported_source_label":source_label,"potential_family":potential,
      "relation_status":status,"independence_status":independence,"evidence":evidence,"independent_measurement_claim":False}
   sr=ref(self.snapshot_objects[source]);self.family_records[k]=obj("SourceFamily",[self.art[source]["snapshot_id"],source_label],p,(sr,),(sr,))
  return self.family_records[k]
 def family_link(self,o,f):
  self.family_links.append(obj("SourceFamilyBinding",[o["object_id"],f["object_id"]],{"native_ref":ref(o),"source_family_ref":ref(f),"qualification":"DECLARED_OR_POTENTIAL_DEPENDENCE_ONLY"},tuple(o["provenance_refs"]),(ref(o),ref(f)),origin="DRV"))
 def nutridata(self):
  for prefix,scope,kind in [("01-","nutridata:ingredient","INGREDIENT_REFERENCE"),("02-","nutridata:dish","RECIPE_REFERENCE")]:
   fs=[k for k in self.nd if k.startswith(prefix)];require(len(fs)==1,"ND_CORE_FILE")
   m=self.nd[fs[0]];p=self.register(scope,P.Path("source_data/excel-Nutridata")/fs[0],m["sha256"],"NUTRIDATA_NATIVE","LOCAL_SNAPSHOT_VENDOR_VERSION_UNRESOLVED")
   keys=set()
   for rn,d,j,l in read_core(p):
    k=d["item_id"];require(k not in keys and str(j["id"])==str(k),"ND_BUSINESS_KEY");keys.add(k)
    aliases=[{"text":j["alias"],"type":"NATIVE_ALIAS_RAW_UNPARSED"}] if isinstance(j.get("alias"),str) and j["alias"].strip() else []
    source_label=str(j.get("source","") or "")
    o=self.add(scope,k,j["name"],kind,{"excel_row":rn,"field":"detail_json.name"},aliases,{"internal_row_id":d["id"],"native_code":j.get("code"),"food_state":"UNRESOLVED_FROM_LABEL","source_label":source_label})
    fam,status,ind=nd_family(source_label)
    if kind=="RECIPE_REFERENCE":fam,status,ind="NUTRIDATA_RECIPE_LINEAGE_UNRESOLVED","RECIPE_CARRIER_ONLY","INDEPENDENCE_UNRESOLVED"
    f=self.family(scope,source_label,fam,status,ind,{"artifact_sha256":m["sha256"],"path":"detail_json.source","basis":"native declaration only"})
    self.family_link(o,f)
    self.nd_sources[(scope,source_label)]+=1
    for g,vs in j.get("nutritionMap",{}).items():
     for i,v in enumerate(vs):
      if isinstance(v,dict) and v.get("desc") is not None:
       self.component_counter[(scope,str(v["desc"]),str(v.get("unit","")))]+=1
   require(len(keys)==(3446 if prefix=="01-" else 22180),"ND_CORE_COUNTS")
 def foodon(self):
  scope="foodon:2026-09-20:food_product";p=self.ext(scope,"FoodOn.owl")
  R="{http://www.w3.org/1999/02/22-rdf-syntax-ns#}";O="{http://www.w3.org/2002/07/owl#}";L="{http://www.w3.org/2000/01/rdf-schema#}"
  I="{http://www.geneontology.org/formats/oboInOwl#}"
  depth=0;all_named=0;classes={};versions=[]
  for event,e in E.iterparse(p,events=("start","end")):
   if event=="start":depth+=1;continue
   if depth==2 and e.tag==O+"Ontology":versions=[v.get(R+"resource",v.text) for v in e if v.tag in (O+"versionIRI",O+"versionInfo")]
   if depth==2 and e.tag==O+"Class" and e.get(R+"about"):
    all_named+=1;iri=e.get(R+"about");labels=[x.text for x in e.findall(L+"label") if x.text]
    ps=[v.get(R+"resource") for v in e.findall(L+"subClassOf") if v.get(R+"resource")]
    sy=[{"text":v.text,"type":v.tag[len(I):]} for v in e if v.tag.startswith(I) and "Synonym" in v.tag and v.text]
    deprec=any(x.text=="true" for x in e.findall(O+"deprecated"))
    require(iri not in classes,"FOODON_DUPLICATE_IRI")
    classes[iri]={"label":labels[0] if labels else None,"parents":ps,"synonyms":sy,"deprecated":deprec}
   if depth==2:e.clear()
   depth-=1
  require(any("2026-09-20" in str(v) for v in versions),"FOODON_VERSION")
  root="http://purl.obolibrary.org/obo/FOODON_00001002"
  require(classes[root]["label"]=="food product","FOODON_ROOT")
  kids=C.defaultdict(list)
  for k,v in classes.items():
   for a in v["parents"]:kids[a].append(k)
  seen={root};q=[root]
  while q:
   a=q.pop()
   for k in kids[a]:
    if k not in seen:seen.add(k);q.append(k)
  # Use only named asserted subClassOf closure. No reasoner or restrictions inferred.
  keep={k for k in seen if k.startswith("http://purl.obolibrary.org/obo/FOODON_") and classes[k]["label"] and not classes[k]["deprecated"]}
  for k in sorted(keep):
   v=classes[k]
   self.add(scope,k,v["label"],"ONTOLOGY_FOOD_PRODUCT_CLASS",{"rdf_about":k},v["synonyms"],
      {"asserted_named_parents":[x for x in v["parents"]],"deprecated":False,"root":root})
   for parent in v["parents"]:
    if parent in keep:self.foodon_edges.append((k,parent))
  self.foodon_classes={k:classes[k] for k in keep}
  self.stats["foodon"]={"version":versions,"named_classes":all_named,"labeled_named_classes":sum(bool(x["label"]) for x in classes.values()),"asserted_descendants_including_root":len(seen),
    "active_foodon_food_product_classes":len(keep),"named_edges_in_selected_subgraph":len(self.foodon_edges),"scope":"asserted named subclass closure; excludes other/imported classes and deprecated entries; no reasoning"}
 def usda(self):
  sr="fdc:sr_legacy:2018-04";p=self.ext(sr,"FDC_SR_2018.zip")
  member,food=zrows(p,"food.csv");_,ndb=zrows(p,"sr_legacy_food.csv");parent=unique(ndb,"fdc_id");foods=unique(food,"fdc_id")
  require(set(foods)==set(parent),"FDC_SR_CROSSWALK")
  fam=self.family(sr,"USDA SR Legacy 2018-04","USDA_COMPOSITION","OFFICIAL_RELEASE","POTENTIAL_SHARED_UPSTREAM",{"artifact_sha256":self.art[sr]["sha256"],"release":"2018-04"})
  for i,r in enumerate(food,2):
   k=r["fdc_id"];require(r["data_type"]=="sr_legacy_food","FDC_DATA_TYPE")
   o=self.add(sr,k,r["description"],"COMPOSITION_REFERENCE",{"member":member,"csv_record":i},meta={"NDB_number":parent[k]["NDB_number"],"food_category_id":r["food_category_id"],"publication_date":r["publication_date"]})
   self.family_link(o,fam)
  _,nut=zrows(p,"nutrient.csv");self.fdc_nutrients=unique(nut,"id")
  _,drv=zrows(p,"food_nutrient_derivation.csv");_,src=zrows(p,"food_nutrient_source.csv")
  drv=unique(drv,"id");src=unique(src,"id")
  # Counts for source lineage, not unique experiments.
  m,values=zrows(p,"food_nutrient.csv");dcount=C.Counter();ncounts=C.Counter();orph=C.Counter()
  for v in values:
   if v["fdc_id"] not in foods:orph["food"]+=1
   if v["nutrient_id"] not in self.fdc_nutrients:orph["nutrient"]+=1
   ncounts[v["nutrient_id"]]+=1
   did=v.get("derivation_id","");dcount[did]+=1
  self.fdc_nutrient_counts=ncounts
  self.stats["fdc_sr"]={"food_rows":len(food),"ndb_crosswalk_rows":len(ndb),"distinct_ndb_numbers":len({x["NDB_number"] for x in ndb}),"nutrient_dictionary_rows":len(nut),"food_nutrient_rows":len(values),"distinct_measured_or_reported_nutrient_ids":len(ncounts),"orphan_counts":dict(orph),"derivation_counts":[{"derivation_id":k,"rows":v,"source_code":src.get(drv.get(k,{}).get("source_id",""),{}).get("code"),"description":drv.get(k,{}).get("description","UNRESOLVED_OR_MISSING")} for k,v in sorted(dcount.items())],"source_independence":"not determined from derivation codes"}
  del values
  fd="fndds:2015-16:fdc_carrier";p=self.ext(fd,"FNDDS_2015_16.zip")
  fm,food=zrows(p,"food.csv");sm,survey=zrows(p,"survey_fndds_food.csv");fs=unique(food,"fdc_id");ss=unique(survey,"fdc_id")
  require(set(fs)==set(ss),"FNDDS_FDC_PARENT_JOIN")
  cycles=C.Counter((r["start_date"],r["end_date"]) for r in survey)
  require(set(cycles)=={("2015-01-01","2016-12-31")},"FNDDS_WRONG_CYCLE")
  fc=unique(survey,"food_code");require(all(re.fullmatch(r"\d{8}",k) for k in fc),"FNDDS_CODE_FORMAT")
  f=self.family(fd,"FNDDS 2015-16 via FoodData Central","USDA_COMPOSITION","OFFICIAL_DERIVED_RELEASE","POTENTIAL_SHARED_UPSTREAM",{"source":"USDA ARS 2015-16 documentation: SR28 accessed 2017-10-02 or other sources; FDC archive same cycle"})
  self.fndds_fdc={}
  for i,r in enumerate(survey,2):
   key=r["food_code"];a=fs[r["fdc_id"]]
   o=self.add(fd,key,a["description"],"DIETARY_SURVEY_CODE",{"member":sm,"csv_record":i},meta={"fdc_id":r["fdc_id"],"food_member":fm,"start_date":r["start_date"],"end_date":r["end_date"],"wweia_category_code":r["wweia_category_code"]})
   self.family_link(o,f);self.fndds_fdc[key]=o
  # ARS separate carrier, same release family, never an independent measurement.
  ars="fndds:2015-16:ars_carrier";ap=self.ext(ars,"FNDDS_ARS_foods_2015_16.xlsx")
  f=self.family(ars,"FNDDS 2015-16 ARS quick-view","USDA_COMPOSITION","OFFICIAL_SAME_RELEASE_CARRIER","POTENTIAL_SHARED_UPSTREAM",{"source":"USDA ARS Foods and Beverages 2015-2016; same cycle, not independent"})
  self.fndds_ars={};duplicates=0
  with zipfile.ZipFile(ap) as z:
   ss=["".join(t.text or "" for t in si.iter(M+"t")) for si in E.fromstring(z.read("xl/sharedStrings.xml"))]
   for sh,_,path in sheets(z):
    if sh!="Foods and Beverages":continue
    for rn,row in read_rows(z,path,ss):
     if rn<=2:continue
     d={c:v[0] for c,v in row.items()};k=d.get("A")
     if not k:continue
     require(re.fullmatch(r"\d{8}",k) is not None and d.get("B"),"ARS_FOOD_CODE")
     if k in self.fndds_ars:duplicates+=1;raise ContractError("ARS_DUPLICATE_CODE")
     aliases=[{"text":d["C"],"type":"ARS_ADDITIONAL_DESCRIPTION_RAW"}] if d.get("C") else []
     o=self.add(ars,k,d["B"],"DIETARY_SURVEY_CODE",{"sheet":sh,"excel_row":rn},aliases,{"wweia_category_code":d.get("E"),"wweia_category_description":d.get("F"),"fortification_code":d.get("D")})
     self.family_link(o,f);self.fndds_ars[k]=o
  overlap=set(self.fndds_fdc)&set(self.fndds_ars)
  nameeq=sum(self.fndds_fdc[k]["payload"]["native_label"].strip()==self.fndds_ars[k]["payload"]["native_label"].strip() for k in overlap)
  raw_eq=sum(self.fndds_fdc[k]["payload"]["native_label"]==self.fndds_ars[k]["payload"]["native_label"] for k in overlap)
  self.stats["fndds"]={"fdc_rows":len(self.fndds_fdc),"ars_rows":len(self.fndds_ars),"common_codes":len(overlap),"common_code_name_raw_exact":raw_eq,"common_code_name_trimmed_exact":nameeq,"whitespace_only_differences":nameeq-raw_eq,
    "fdc_only_codes":len(set(self.fndds_fdc)-overlap),"ars_only_codes":len(set(self.fndds_ars)-overlap),"version":"2015-16","same_release_carriers_not_independent":True}
 def public_vocab(self):
  def record(scope,key,label,kind,loc,aliases=None,meta=None):return self.add(scope,key,label,kind,loc,aliases,meta)
  p=self.public("food101:class",1,"dataset_infos.json");x=load(p);labs=x["default"]["features"]["label"]["names"]
  require(len(labs)==101,"FOOD101_LABELS")
  for i,k in enumerate(labs):record("food101:class",i,k,"VISUAL_FOOD_CLASS",{"json_pointer":"/default/features/label/names/"+str(i)})
  for i,fn in [(2,"zip_02_category.txt"),(3,"zip_01_category.txt")]:
   s=f"uec{i}:mirror:class";p=self.public(s,i,fn)
   for rn,line in lines(p):
    if rn==1:continue
    key,label=line.split(None,1);require(key.isdigit(),"UEC_LABEL")
    record(s,key,label,"VISUAL_FOOD_CLASS",{"line":rn})
   require(len(self.by_scope[s])==(100 if i==2 else 256),"UEC_COUNT")
  s="isia500:class";p=self.public(s,5,"zip_01_ISIAFood500_classLabel.txt")
  for rn,line in lines(p):
   label,k=line.rsplit(None,1);require(k.isdigit(),"ISIA_LABEL");record(s,k,label,"VISUAL_FOOD_CLASS",{"line":rn})
  for i,s,k in [(6,"food11:corrected_mirror","COARSE_FOOD_CATEGORY"),(14,"food5k:corrected_mirror","FOOD_PRESENCE_CLASS")]:
   p=self.public(s,i,"archive_class_index.json","20261125_run002");x=load(p);labs=sorted({v.split("/",1)[1] for v in x["group_hist"]})
   for lab in labs:record(s,lab,lab,k,{"derived_from_archive_group_hist":lab},meta={"group_hist_source":True})
  s="fruits360:current_directory";p=self.public(s,9,"training_categories.json")
  for i,x in enumerate(load(p)):
   if x.get("type")=="dir":record(s,x["name"],x["name"],"VISUAL_VARIETY_CLASS",{"json_pointer":"/"+str(i)+"/name"},meta={"case_sensitive_native_id":True})
  s="nutrition5k:ingredient";p=self.public(s,13,"ingredients_metadata.csv")
  with p.open(encoding="utf-8-sig",newline="") as f:
   for i,r in enumerate(csv.DictReader(f),2):record(s,r["id"],r["ingr"],"INGREDIENT_REFERENCE",{"csv_record":i},meta={"native_id_transform":"ingr_+zero_pad_10"})
  f=self.family(s,"Nutrition5k USDA ingredient composition","USDA_COMPOSITION","DECLARED_AGENCY_RELEASE_UNKNOWN","POTENTIAL_SHARED_UPSTREAM",{"source":"Nutrition5k README: per-gram USDA nutrition reference; exact edition unresolved"})
  for o in self.by_scope[s]:self.family_link(o,f)
  s="menumatch:menu";p=self.public(s,17,"zip_02_items_info.txt")
  for rn,line in lines(p):
   if rn==1:continue
   v=[x.strip() for x in line.split(";") if x.strip()];require(len(v)==4,"MENU_WIDTH")
   record(s,v[1],v[0],"MENU_ITEM_REFERENCE",{"line":rn},meta={"restaurant":v[3]})
  f=self.family(s,"Menu-Match restaurant menu calorie reference","MENU_LABEL_SOURCE","DECLARED_MENU_REFERENCE","INDEPENDENCE_UNRESOLVED",{"source":"B0 original items_info and README"})
  for o in self.by_scope[s]:self.family_link(o,f)
  for i,s,run,fields in [(12,"xiachufang:mirror","20261125_run001",("name","dish")),(18,"recipenlg:alternative_mirror","20261125_run002",("title",))]:
   p=self.public(s,i,"hf_rows.json",run)
   for j,x in enumerate(load(p)["rows"]):
    y=x["row"];label=y[fields[0]]
    if isinstance(label,str) and label.strip():record(s,x["row_idx"],label,"RECIPE_VARIANT_LABEL",{"json_pointer":"/rows/"+str(j)+"/row/"+fields[0]},meta={"dish_label":y.get("dish"),"mirror_original_equivalence":"UNRESOLVED"})
  for file,pointer,s,vals in [("product_737628064502.json","/product","off:single",lambda x:[x["product"]]),("search_breakfast_cereals.json","/products","off:search",lambda x:x["products"])]:
   p=self.public(s,16,file)
   f=self.family(s,"OFF current API product nutrition label","PRODUCT_LABEL_CARRIER","LABEL_SOURCE_NOT_ASSAY","INDEPENDENCE_UNRESOLVED",{"source":"OFF API snapshot; not historical product measurement"})
   for i,x in enumerate(vals(load(p))):
    o=record(s,x["code"],x["product_name"],"BRANDED_PRODUCT_SNAPSHOT",{"json_pointer":pointer+(("/"+str(i)) if pointer=="/products" else "")},meta={"market":x.get("countries_tags"),"brand":x.get("brands")});self.family_link(o,f)
  s="epic100:noun";p=self.public(s,22,"EPIC_100_noun_classes.csv")
  with p.open(encoding="utf-8-sig",newline="") as f:
   for i,r in enumerate(csv.DictReader(f),2):record(s,r["id"],r["key"],"MIXED_ACTION_OBJECT_VOCABULARY",{"csv_record":i},meta={"food_domain":"UNQUALIFIED"})
  # FoodX numeric class IDs without trusted name mapping; retain coverage but no inferred labels.
  s="foodx251:mirror_class_ids";p=self.public(s,7,"train_info_dirty.csv")
  with p.open(encoding="utf-8-sig",newline="") as h:
   c=C.Counter(x[1] for x in csv.reader(h))
  for k in sorted(c):record(s,k,k,"UNNAMED_VISUAL_CLASS_ID",{"aggregate_from_label_column":k},meta={"training_index_count":c[k],"class_name_status":"HOLD"})
 def snapme_audit(self):
  s="snapme:linkfile:2015-16";p=self.public(s,4,"master_SNAPME_linkfile.csv","20261125_run002")
  c=C.Counter();code_counts=C.Counter();private=[];orphan=set();fdc_missing=set();name_different=0
  fam=self.family(s,"SNAPMe ASA24-2020 reported food attributes","USDA_COMPOSITION","DERIVED_DIETARY_CARRIER","POTENTIAL_SHARED_UPSTREAM",{"source":"U2-B ASA24-2020/FNDDS 2015-16; reported observations, not independent chemical measurements"})
  with p.open(encoding="utf-8-sig",newline="") as f:
   for rn,r in enumerate(csv.DictReader(f),2):
    k=r["FoodCode"];code_counts[k]+=1
    if not re.fullmatch(r"\d{8}",k):st="HOLD_CODE_DOMAIN_UNRESOLVED"
    elif k not in self.fndds_ars:st="HOLD_ARS_TARGET_ORPHAN";orphan.add(k)
    elif k not in self.fndds_fdc:st="ARS_ONLY_CODE_MATCH_FDC_HOLD";fdc_missing.add(k)
    elif self.fndds_ars[k]["payload"]["native_label"].strip()!=self.fndds_fdc[k]["payload"]["native_label"].strip():st="HOLD_SAME_CODE_CARRIER_DESCRIPTION_CONFLICT"
    else:st="SAME_CYCLE_CODE_MATCH_CANDIDATE"
    c[st]+=1
    a=self.fndds_ars.get(k);b=self.fndds_fdc.get(k)
    if a and r["Food_Description"].strip()!=a["payload"]["native_label"].strip():name_different+=1
    private.append(obj("NativeCodeLinkCandidate",[self.art[s]["snapshot_id"],rn],{"source_snapshot":self.art[s]["snapshot_id"],"source_locator":{"csv_record":rn,"field":"FoodCode"},"native_code":k,
     "target_ars_ref":ref(a) if a else None,"target_fdc_ref":ref(b) if b else None,"target_cycle":"2015-16","status":st,"relation_type":"NATIVE_RECORD_LINK_CANDIDATE","measurement_and_aggregation":"HOLD","same_physical_instance":False},(ref(self.snapshot_objects[s]),),tuple([ref(self.snapshot_objects[s]),ref(fam)]+[ref(z) for z in (a,b) if z]),origin="DRV"))
  self.snapme_links=private
  self.stats["snapme"]={"records":len(private),"distinct_code_tokens":len(code_counts),"status_rows":dict(c),"distinct_ars_orphans":len(orphan),"distinct_fdc_missing":len(fdc_missing),"source_description_not_exact_ars_rows":name_different,"aggregation":"HOLD","source_cycle_basis":"U2-B ASA24-2020; FNDDS 2015-16"}
  require(len(private)==4761,"SNAPME_COUNT")
 def verify(self):
  for a in self.art.values():require(sha(self.root/a["path"])==a["sha256"],"SOURCE_HASH_CHANGED")
  refs={ref(o):o for o in self.records};require(len(refs)==len(self.records),"DUPLICATE_VOCAB_REVISION")
  for o in self.records:verify_obj(o)
  for s,rows in self.by_scope.items():
   require(len({r["payload"]["native_key"] for r in rows})==len(rows),"NATIVE_KEY_COLLISION")
  for e in self.family_links:require(e["payload"]["native_ref"] in refs,"FAMILY_ORPHAN")
  return refs
 def run(self):
  self.nutridata();self.foodon();self.usda();self.public_vocab();self.snapme_audit();self.verify()
  return self
