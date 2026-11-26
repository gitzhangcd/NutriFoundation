#!/usr/bin/env python3
"""C1: frozen independent Critic verification and scoped development comparison.
No official scientific qualification. Raw records and case-level disagreements remain local.
"""
import argparse, csv, io, json, pathlib as P, hashlib, re, zipfile, posixpath
import xml.etree.ElementTree as E
from collections import Counter, defaultdict
from datetime import datetime,timezone

V="UDF-U3B-C1-DEV-COMPARISON-0.1"
EXT={"FoodOn":"foodon:2026-09-20:food_product","FDC_SR_Legacy":"fdc:sr_legacy:2018-04","FNDDS":"fndds:2015-16:fdc_carrier"}
VERS={"FoodOn":"2026-09-20","FDC_SR_Legacy":"2018-04","FNDDS":"2015-16"}
BASE="runs/B2/U3-A/inputs/"
REL={"EXACT","CLOSE","BROADER_TARGET","NARROWER_TARGET","RELATED","CONDITIONAL","AMBIGUOUS","UNRESOLVED"}
def require(ok,code):
 if not ok:raise ValueError(code)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def seal(o):
 z=dict(o);z.pop("revision_id",None);return hashlib.sha256(canon(z).encode()).hexdigest()
def ref(o):return o["object_id"]+"@"+o["revision_id"]
def read(p):return json.loads(p.read_text(encoding="utf8"))
def lines(p):
 with p.open(encoding="utf8") as f:
  return [json.loads(x) for x in f if x.strip()]
def put(p,x):
 with p.open("x",encoding="utf8") as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write("\n")
def putl(p,x):
 with p.open("x",encoding="utf8") as f:
  for o in x:f.write(canon(o)+"\n")
def now():return datetime.now(timezone.utc).isoformat()
def rows(z,name):
 matches=[n for n in z.namelist() if P.PurePosixPath(n).name==name];require(len(matches)==1,"CSV_MEMBER_AMBIGUOUS")
 n=matches[0]
 with z.open(n) as f:r=list(csv.DictReader(io.TextIOWrapper(f,encoding="utf-8-sig",newline="")))
 return n,r
def unique(rs,k):
 d={}
 for r in rs:
  v=r[k];require(v and v not in d,"DUPLICATE_NATIVE_KEY");d[v]=r
 return d
def key(system,id):return (EXT[system],str(id))
def ck(x):return key(x["target_system"],x["target_native_id"])
def nk(x):
 ns=x["native_namespace"]
 if ns=="fndds:2015-16:ars_carrier":ns=EXT["FNDDS"]
 return ns,str(x["native_key"])
def countpairs(pairs):
 return [{"group":list(k) if isinstance(k,tuple) else k,"count":v} for k,v in sorted(Counter(pairs).items(),key=lambda x:str(x[0]))]

class Inputs:
 def __init__(self,root,profile):
  self.root=root.resolve();self.p=read(profile);self.fences={}
  require(self.p["version"]==V and self.p["mapping_release_authorized"] is False and bool(self.p["pi_authorization"]),"PROFILE_OR_AUTHORIZATION")
  self.pin(profile.relative_to(self.root),sha(profile))
 def pin(self,path,h=None):
  q=self.root/P.Path(path);p=q.resolve()
  require(p.is_relative_to(self.root) and q.is_file() and not q.is_symlink(),"UNSAFE_INPUT_PATH")
  actual=sha(p);require(h is None or actual==h,"PINNED_INPUT_CHANGED:"+str(path))
  k=str(p.relative_to(self.root));require(k not in self.fences or self.fences[k]==actual,"INPUT_REOPEN_DRIFT")
  self.fences[k]=actual;return p
 def check(self):
  require(all(sha(self.root/p)==h for p,h in self.fences.items()),"INPUT_CHANGED_DURING_RUN")

def parse_standards(inp):
 root=inp.root
 # Full named OWL classes, including the exact original definitions. Keep non-food
 # members distinguishable; the B2 universe is checked later, not presumed.
 rdf="{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
 owl="{http://www.w3.org/2002/07/owl#}"
 rdfs="{http://www.w3.org/2000/01/rdf-schema#}"
 obo="{http://purl.obolibrary.org/obo/}"
 oio="{http://www.geneontology.org/formats/oboInOwl#}"
 p=root/BASE/"FoodOn.owl";tree=E.parse(p).getroot();voc={};versions=[]
 for e in tree:
  if e.tag==owl+"Ontology":
   versions += [x.get(rdf+"resource",x.text) for x in e if x.tag in (owl+"versionIRI",owl+"versionInfo")]
  if e.tag!=owl+"Class" or not e.get(rdf+"about"):continue
  id=e.get(rdf+"about");labels=[x.text for x in e.findall(rdfs+"label") if x.text]
  if not labels:continue
  require(key("FoodOn",id) not in voc,"DUPLICATE_OWL_IRI")
  voc[key("FoodOn",id)]={"label":labels[0],"definitions":[x.text for x in e.findall(obo+"IAO_0000115") if x.text],
   "aliases":[x.text for x in e if x.tag.startswith(oio) and "Synonym" in x.tag and x.text],
   "locator":BASE+"FoodOn.owl#rdf:about="+id,"deprecated":any(x.text=="true" for x in e.findall(owl+"deprecated"))}
 require(any("2026-09-20" in str(x) for x in versions),"FOODON_VERSION")
 with zipfile.ZipFile(root/BASE/"FDC_SR_2018.zip") as z:
  member,food=rows(z,"food.csv");unique(food,"fdc_id")
  for i,r in enumerate(food,2):
   require(r["data_type"]=="sr_legacy_food","FDC_TYPE")
   voc[key("FDC_SR_Legacy",r["fdc_id"])]={"label":r["description"],"definitions":[],"aliases":[],"locator":BASE+"FDC_SR_2018.zip!"+member+":row:"+str(i),"deprecated":False}
 with zipfile.ZipFile(root/BASE/"FNDDS_2015_16.zip") as z:
  _,food=rows(z,"food.csv");member,survey=rows(z,"survey_fndds_food.csv");fs=unique(food,"fdc_id");ss=unique(survey,"food_code")
  require(len(fs)==len(ss) and set(fs)=={x["fdc_id"] for x in survey},"FNDDS_FK")
  require(all(x["start_date"]=="2015-01-01" and x["end_date"]=="2016-12-31" for x in survey),"FNDDS_CYCLE")
  for i,r in enumerate(survey,2):
   voc[key("FNDDS",r["food_code"])]={"label":fs[r["fdc_id"]]["description"],"definitions":[],"aliases":[],"locator":BASE+"FNDDS_2015_16.zip!"+member+":row:"+str(i),"deprecated":False}
 # Independent XLSX parsing from raw archive; no dataframe row-index assumption.
 m="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
 rel="{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
 with zipfile.ZipFile(root/BASE/"FNDDS_ARS_foods_2015_16.xlsx") as z:
  wb=E.fromstring(z.read("xl/workbook.xml"));rr=E.fromstring(z.read("xl/_rels/workbook.xml.rels"))
  rels={a.get("Id"):a.get("Target") for a in rr}
  sh=[x for x in wb.iter(m+"sheet") if x.get("name")=="Foods and Beverages"];require(len(sh)==1,"ARS_SHEET")
  t=rels[sh[0].get(rel+"id")];path=t.lstrip("/") if t.startswith("/") else posixpath.normpath("xl/"+t)
  strings=["".join(x.text or "" for x in a.iter(m+"t")) for a in E.fromstring(z.read("xl/sharedStrings.xml"))]
  count=0;seen=set()
  for row in E.fromstring(z.read(path)).iter(m+"row"):
   rn=int(row.get("r"));d={}
   for c in row.findall(m+"c"):
    v=c.find(m+"v")
    text="".join(x.text or "" for x in c.iter(m+"t")) if c.get("t")=="inlineStr" else (v.text if v is not None else "")
    if c.get("t")=="s":text=strings[int(text)]
    d[re.match(r"[A-Z]+",c.get("r")).group()]=text
   if rn<=2 or not d.get("A"):continue
   k=key("FNDDS",d["A"]);require(k in voc and k not in seen,"ARS_CODE");seen.add(k)
   x=voc[k];require(x["label"].strip()==d["B"].strip(),"ARS_DESCRIPTION")
   x["locator"]+=" | "+BASE+"FNDDS_ARS_foods_2015_16.xlsx!Foods and Beverages:row:"+str(rn)
   if d.get("C"):x["aliases"].append(d["C"])
   count+=1
 require(count==len(ss),"ARS_COUNT")
 return voc,{"FoodOn_named_labeled_classes":sum(k[0]==EXT["FoodOn"] for k in voc),"FDC_food_records":len(fs) if False else len([k for k in voc if k[0]==EXT["FDC_SR_Legacy"]]),"FNDDS_food_codes":len(ss),"FNDDS_ARS_same_cycle_records":count,"FoodOn_version":versions}

def version_ok(x):
 s=x["target_system"];v=x["target_version"]
 if s=="FNDDS":return isinstance(v,str) and v.startswith("2015-16") and ("same-cycle" in v or v=="2015-16")
 return v==VERS[s]

def verify_critic(inp):
 p=inp.p;root=inp.root;cfg=read(inp.pin(p["task_config"]["path"],p["task_config"]["sha256"]))
 inp.pin(p["protocol"]["path"],p["protocol"]["sha256"])
 cr=root/p["critic"]["run"];receipt=read(inp.pin(str((cr/"CriticFreezeReceipt.json").relative_to(root)),p["critic"]["receipt_sha256"]))
 require(receipt["status"]=="REVIEW_FROZEN" and receipt["task_id"]==cfg["task_id"] and receipt["baseline"]==cfg["baseline"],"CRITIC_FREEZE_IDENTITY")
 names={x["file"] for x in cfg["output"]["required"]}-{"CriticFreezeReceipt.json"}
 require(set(receipt["frozen_output_files"])==names,"FROZEN_OUTPUT_SET")
 for n,a in receipt["frozen_output_files"].items():
  require(a["path"]==str((cr/n).relative_to(root)),"FROZEN_OUTPUT_PATH")
  q=inp.pin(a["path"],a["sha256"]);require(q.stat().st_size==a["bytes"],"FROZEN_OUTPUT_SIZE")
 em=read(cr/"ExecutionManifest.json");require(em["task_id"]==cfg["task_id"] and em["baseline"]==cfg["baseline"] and em["reviewer"]==receipt["reviewer"]=="Gemini" and em["model_version"]==receipt["model_version"],"EXECUTION_IDENTITY")
 inputs={x["path"]:x["sha256"] for x in cfg["allowed_inputs"]}
 for arr in (receipt["input_identities"],em["allowed_inputs_verified"]):
  require(len(arr)==len(inputs) and {a["path"]:a["sha256"] for a in arr}==inputs and all(a["verified"] is True for a in arr),"CRITIC_INPUT_DECLARATION")
  for x in arr:require(inp.pin(x["path"],x["sha256"]).stat().st_size==x["bytes"],"CRITIC_INPUT_SIZE")
 require(set(em["actual_accessed_paths"])<=set(inputs)|{p["protocol"]["path"],p["task_config"]["path"]} and em["forbidden_inputs_accessed"]==[] and em["forbidden_access_count"]==0 and em["existing_files_modified"]==0,"REPORTED_ACCESS_BOUNDARY")
 exp=receipt["exposure_and_limitations"];require(exp["previous_u3a_code_audit_exposure"] and exp["confirmatory_strict_blindness_claimed"] is False and exp["independent_accuracy_or_recall_claimed"] is False and exp["unblinding_performed"] is False and exp["mapping_or_research_release_authorized"] is False,"EXPOSURE_OR_RELEASE")
 src=[]
 for x in cfg["allowed_inputs"]:
  if "expected_rows" in x:
   r=read(root/x["path"]);require(len(r)==x["expected_rows"],"SOURCE_QUEUE_SIZE");src+=r
 sq=unique(src,"review_id");require(len(sq)==44==len({x["source_ref"] for x in src}),"SOURCE_IDENTITY_COUNT")
 rec=lines(cr/"IndependentReviewRecords.jsonl");recix=unique(rec,"review_id");require(set(recix)==set(sq),"REVIEW_ID_SET")
 spec=cfg["review_task"]["record_fields"];cs=[];hs=[];payload_issues=Counter()
 for rid,x in recix.items():
  s=sq[rid]
  for a,b in [("source_ref","source_ref"),("source_scope","source_scope"),("source_native_label","source_native_label"),("source_native_kind","native_kind")]:
   require(x[a]==s[b],"REVIEW_SOURCE_MISMATCH")
  require(set(x)==set(spec) and set(x["semantic_reconstruction"])==set(spec["semantic_reconstruction"]) and set(x["bilingual_expansion"])==set(spec["bilingual_expansion"]),"REVIEW_FIELDS")
  require(x["accepted_equivalence"] is False and x["mapping_release_authorized"] is False and x["purpose"]=="CURATION_DEV_ONLY" and x["review_status"]=="CRITIC_DRAFT","CRITIC_RELEASE")
  require(x["overall_review_route"] in ("GREEN","AMBER","RED","HOLD") and isinstance(x["recommended_expert_review"],bool),"CRITIC_ROUTE")
  # Task config specifies field names, not array/object types. Record legacy draft
  # prompt type differences separately; do not rewrite the frozen artifact.
  for k in ("composition_constraints","regional_constraints","field_evidence"):
   if not isinstance(x["semantic_reconstruction"][k],list):payload_issues[k+"_not_array"]+=1
  require(isinstance(x["independent_candidates"],list) and isinstance(x["hard_negative_candidates"],list),"CANDIDATE_LIST")
  require(x["independent_candidates"] or x["unresolved_reasons"],"EMPTY_CASE_WITHOUT_REASON")
  require(max(Counter(z["target_system"] for z in x["independent_candidates"]).values(),default=0)<=3,"PER_STANDARD_TOP3")
  require(len({ck(z) for z in x["independent_candidates"]})==len(x["independent_candidates"]) and len({ck(z) for z in x["hard_negative_candidates"]})==len(x["hard_negative_candidates"]),"DUPLICATE_CRITIC_TARGET")
  require(not ({ck(z) for z in x["independent_candidates"]}&{ck(z) for z in x["hard_negative_candidates"]}),"CRITIC_POS_NEG_CONFLICT")
  for field,out in [("independent_candidates",cs),("hard_negative_candidates",hs)]:
   for z in x[field]:
    require(z["target_system"] in EXT and version_ok(z),"CRITIC_TARGET_VERSION")
    if field=="independent_candidates":
     require(set(z)==set(spec["independent_candidates"]) and z["source_relation_to_target"] in REL and z["review_route"] in ("GREEN","AMBER","RED","HOLD") and bool(z["evidence_refs"]) and bool(z["relation_reason"]),"CRITIC_CANDIDATE_FIELDS")
    else:require(bool(z["rationale"]) and bool(z["conflict_type"]),"HARD_NEGATIVE_EVIDENCE")
    out.append({"review_id":rid,"source_ref":x["source_ref"],"source_scope":x["source_scope"],"source_native_label":x["source_native_label"],**z})
 c0=read(cr/"IndependentCandidateRegistry.json");h0=read(cr/"HardNegativeRegistry.json")
 require(c0["task_id"]==h0["task_id"]==cfg["task_id"] and Counter(map(canon,cs))==Counter(map(canon,c0["candidates"])) and Counter(map(canon,hs))==Counter(map(canon,h0["hard_negatives"])),"CRITIC_REGISTRY_MISMATCH")
 cc=receipt["completion_counts"];num={"completed_cases":len(rec),"unique_review_ids":len(recix),"unique_source_refs":len({x["source_ref"] for x in rec}),"cases_with_candidates":sum(bool(x["independent_candidates"]) for x in rec),"cases_without_candidates_retained_unresolved":sum(not x["independent_candidates"] for x in rec),"independent_candidates_total":len(cs),"hard_negatives_total":len(hs),"route_counts":dict(Counter(x["overall_review_route"] for x in rec)),"recommended_expert_review_count":sum(x["recommended_expert_review"] for x in rec)}
 require(all(cc[k]==v for k,v in num.items()),"CRITIC_RECEIPT_COUNT_MISMATCH")
 require(c0["total_candidates"]==len(cs) and h0["total_hard_negatives"]==len(hs),"REGISTRY_COUNT")
 # Target ID membership, primary label, exact locator and optional definition check.
 voc,raw_counts=parse_standards(inp);checks=[];problems=[];field_counts=Counter()
 for field,rr in (("candidate",cs),("hard_negative",hs)):
  for x in rr:
   k=ck(x);a=voc.get(k)
   z={"review_id":x["review_id"],"target_key":list(k),"role":field,"id_exists":a is not None,
      "label_trim_matches":bool(a and a["label"].strip()==x["target_native_label"].strip()),
      "locator_matches":bool(a and a["locator"]==x["target_source_locator"]),"active_class":bool(a and not a["deprecated"])}
   if x.get("target_definition") is None:z["definition_status"]="NOT_SUPPLIED"
   elif a is not None and x["target_definition"] in a["definitions"]:z["definition_status"]="VERBATIM_SOURCE_DEFINITION"
   elif a is not None and x["target_definition"] in a["aliases"]:z["definition_status"]="SOURCE_ADDITIONAL_DESCRIPTION_NOT_DEFINITION"
   else:z["definition_status"]="NOT_EXACTLY_VERIFIED"
   for f in ("id_exists","label_trim_matches","locator_matches","active_class"):
    if z[f]:field_counts[field+"_"+f]+=1
    else:problems.append({"review_id":x["review_id"],"target_key":list(k),"role":field,"issue":f})
   field_counts[z["definition_status"]]+=1
   checks.append(z)
 require(cc["target_ids_verified"]+cc["target_ids_unverified"]==len(checks),"REPORTED_ID_COUNT")
 # ID, label and locator all must hold before reading hidden candidate content.
 gate=not problems
 result={"status":"PASS_CRITIC_FREEZE_AND_NATIVE_TARGET_VERIFICATION" if gate else "HOLD_CRITIC_NATIVE_TARGET_VERIFICATION",
  "task_id":cfg["task_id"],"frozen_outputs_verified":len(names),"allowed_inputs_verified":len(inputs),"source_only_identity_verified":len(rec),
  "registry_rows_verified":len(cs)+len(hs),"critic_candidates":len(cs),"critic_hard_negatives":len(hs),"critic_counts":num,
  "candidate_relations":dict(Counter(x["source_relation_to_target"] for x in cs)),
  "candidate_target_systems":dict(Counter(x["target_system"] for x in cs)),
  "hard_negative_target_systems":dict(Counter(x["target_system"] for x in hs)),
  "native_target_checks":dict(field_counts),"target_identity_issues":len(problems),"raw_standard_counts":raw_counts,
  "previous_prompt_type_differences":dict(payload_issues),"reported_forbidden_access":0,"access_independently_proven":False,
  "historical_exposure":True,"model_version":"UNAVAILABLE_EXACT_BUILD","independent_reference_count":0,"scientific_release_authorized":False}
 inp.check()
 return result,recix,sq,voc,checks,problems

def compare(inp,recix,sq,voc):
 p=inp.p;root=inp.root;g=p["generator"];run=root/g["run"];priv=run/"private";u=p["u2c"];ur=root/u["run"]
 inp.pin(str((run/"B2AdmissionReceipt.json").relative_to(root)),g["receipt_sha256"])
 inp.pin(u["receipt_path"],u["receipt_sha256"]);inp.pin(p["u3b_frozen_receipt"]["path"],p["u3b_frozen_receipt"]["sha256"])
 m=read(inp.pin(str((priv/"collection_manifest.json").relative_to(root)),g["manifest_sha256"]))
 by={}
 for name in ("NativeVocabularyRecord.jsonl","AlignmentRecord.jsonl"):
  a=m[name];f=inp.pin(str((priv/"typed_collections"/name).relative_to(root)),a["sha256"])
  require(f.stat().st_size==a["bytes"],"GENERATOR_COLLECTION_SIZE")
  rr=lines(f);require(len(rr)==a["rows"] and all(seal(x)==x["revision_id"] for x in rr),"GENERATOR_COLLECTION_REVISION")
  by[name]={ref(x):x for x in rr};require(len(by[name])==len(rr),"GENERATOR_DUPLICATE_REF")
 native=by["NativeVocabularyRecord.jsonl"];edges=by["AlignmentRecord.jsonl"]
 # The two hidden packets are opened only in compare(), called after verification gate.
 hidden=[]
 for a in g["hidden"]:hidden+=read(inp.pin(a["path"],a["sha256"]))
 hi=unique(hidden,"review_id");require(set(hi)==set(sq),"HIDDEN_SOURCE_PAIR")
 routes=unique(lines(inp.pin(str((priv/"CandidateQueryRoutes.jsonl").relative_to(root)),g["routes_sha256"])),"source_ref")
 refs={z for h in hidden for z in h["candidate_refs"]};require(len(refs)==sum(len(h["candidate_refs"]) for h in hidden),"HIDDEN_DUPLICATE_EDGE")
 bm=read(inp.pin(str((ur/"private/partition_manifest.json").relative_to(root)),u["partition_manifest_sha256"]))
 current={}
 for rel,x in bm.items():
  if not rel.endswith("/AlignmentRecord.jsonl"):continue
  f=inp.pin(str((ur/"private/typed_partitions"/rel).relative_to(root)),x["sha256"])
  rr=lines(f);require(len(rr)==x["rows"] and f.stat().st_size==x["bytes"],"U2C_EDGE_COUNT")
  for o in rr:
   l=o["governance"]["legacy_ref"]
   if l not in refs:continue
   require(l not in current and seal(o)==o["revision_id"] and o["purpose"]=="CURATION_DEV" and o["governance"]["release_status"]=="HOLD","U2C_EDGE_PROJECTION")
   require(o["payload"]["source_ref"]==edges[l]["payload"]["source_ref"] and o["payload"]["target_ref"]==edges[l]["payload"]["target_ref"],"U2C_ENDPOINT_DRIFT")
   current[l]=o
 require(set(current)==refs,"U2C_PROJECTION_COVERAGE")
 target_universe={nk(x["payload"]) for x in native.values() if x["payload"]["native_namespace"] in set(EXT.values())}
 all_gen=C=Counter();case_results=[];expert_queue=[];matrix=Counter();relation_pairs=Counter();risk_pair=Counter();hard_types=Counter();crit_outside=[];absence=[]
 for rid,s in sq.items():
  c=recix[rid];sr=s["source_ref"];n=native[sr]["payload"]
  require(n["native_label"]==s["source_native_label"] and n["native_kind"]==s["native_kind"] and n["native_namespace"]==s["source_scope"],"GENERATOR_SOURCE_IDENTITY")
  er=hi[rid]["candidate_refs"];require(set(er)==set(routes[sr]["candidate_refs"]) and len(er)==routes[sr]["candidate_count"],"HIDDEN_ROUTE_CLOSURE")
  gen={};local=[];ger=[]
  for r in er:
   e=edges[r];a=e["payload"];b=current[r]["payload"];require(a["source_ref"]==sr and a["target_ref"] in native and a["relation_type"]==a["source_relation_to_target"]=="UNRESOLVED" and a["accepted_equivalence"] is False and a["physical_instance_link"] is False,"GENERATOR_EDGE_BOUNDARY")
   t=native[a["target_ref"]]["payload"];k=nk(t)
   z={"target_key":list(k),"target_label":t["native_label"],"generator_ref":r,"u2c_ref":ref(current[r]),"original_proposal":a["proposed_relation"],"u2c_proposal":b["proposed_relation"],"legacy_route":a["review_route"],"u2c_route":b["review_route"],"ranking_score":a["ranking_score"],"rank":a["rank"]}
   if k[0] in EXT.values():
    require(k in target_universe and k in voc and voc[k]["label"].strip()==t["native_label"].strip(),"GENERATOR_TARGET_RAW_DRIFT")
    require(k not in gen,"GENERATOR_DUPLICATE_TARGET")
    gen[k]=z
   else:local.append(z)
  cs={ck(x):x for x in c["independent_candidates"]};hs={ck(x):x for x in c["hard_negative_candidates"]};gs=set(gen);ps=set(cs);ns=set(hs)
  common=gs&ps;conflict=gs&ns;unknown=gs-ps-ns;critic_only=ps-gs;in_scope=ps&target_universe
  require(len(gs)==len(common)+len(conflict)+len(unknown),"COMPARISON_PARTITION")
  matrix[(bool(er),bool(cs))]+=1
  vals={"generator_all":len(er),"generator_external":len(gs),"generator_other_scope":len(local),"critic_candidates":len(ps),"critic_hard_negatives":len(ns),
    "critic_candidates_in_generator_target_universe":len(in_scope),"critic_candidates_outside_generator_target_universe":len(ps-target_universe),
    "shared_candidate_ids":len(common),"generator_hits_critic_hard_negative":len(conflict),"generator_not_reviewed_by_critic":len(unknown),"critic_only_candidate_ids":len(critic_only),
    "critic_only_in_generator_universe":len(critic_only&target_universe)}
  all_gen.update(vals)
  all_gen["cases_with_generator"]+=bool(er);all_gen["cases_with_generator_external"]+=bool(gs);all_gen["cases_with_critic_candidate"]+=bool(ps)
  all_gen["cases_with_shared_candidate"]+=bool(common);all_gen["cases_with_hard_negative_overlap"]+=bool(conflict)
  all_gen["cases_with_both_external_candidates"]+=bool(gs and ps);all_gen["cases_with_both_but_no_shared_id"]+=bool(gs and ps and not common)
  all_gen["cases_with_critic_only_in_generator_universe"]+=bool(critic_only&target_universe)
  all_gen["cases_with_critic_no_candidate_generator_external"]+=bool(gs and not ps)
  shared=[];hard=[]
  for k in sorted(common):
   z=gen[k];v=cs[k];relation_pairs[(z["original_proposal"],v["source_relation_to_target"])]+=1
   all_gen["shared_proposed_relation_exact_string_match"]+=z["original_proposal"]==v["source_relation_to_target"]
   shared.append({**z,"critic_relation":v["source_relation_to_target"],"critic_route":v["review_route"],"critic_reason":v["relation_reason"],"critic_conditions":v["required_conditions"],"critic_conflicts":v["semantic_conflicts"]})
  for k in sorted(conflict):
   z=gen[k];v=hs[k];hard_types[v["conflict_type"]]+=1;risk_pair[(z["legacy_route"],z["u2c_route"])]+=1
   all_gen["hard_negative_overlap_old_amber"]+=z["legacy_route"]=="AMBER"
   all_gen["hard_negative_overlap_u2c_amber"]+=z["u2c_route"]=="AMBER"
   all_gen["hard_negative_overlap_u2c_red"]+=z["u2c_route"]=="RED"
   all_gen["hard_negative_overlap_old_score_ge_0_9"]+=z["ranking_score"]>=0.9
   hard.append({**z,"critic_conflict_type":v["conflict_type"],"critic_rationale":v["rationale"]})
  for k in ps-target_universe:crit_outside.append({"review_id":rid,"target_key":list(k),"reason":"OUTSIDE_GENERATOR_TARGET_UNIVERSE"})
  status="PRIORITY_EXPERT_REVIEW" if c["recommended_expert_review"] or conflict else "DEVELOPMENT_DISAGREEMENT_REVIEW"
  a={"review_id":rid,"source_ref":sr,"source_scope":s["source_scope"],"source_native_label":s["source_native_label"],"counts":vals,"critic_overall_route":c["overall_review_route"],"critic_expert_recommended":c["recommended_expert_review"],"shared":shared,"critic_hard_negative_overlap":hard,"critic_only":[cs[k] for k in sorted(critic_only)],"generator_unreviewed":[gen[k] for k in sorted(unknown)],"generator_other_target_scopes":local,"critic_unresolved_reasons":c["unresolved_reasons"],"status":status,"adjudication":"PENDING","accepted_equivalence":False,"mapping_release_authorized":False}
  case_results.append(a)
  if status=="PRIORITY_EXPERT_REVIEW":expert_queue.append({"review_id":rid,"source_ref":sr,"reason":["CRITIC_EXPERT_RECOMMENDATION"]*bool(c["recommended_expert_review"])+["GENERATOR_CRITIC_HARD_NEGATIVE_OVERLAP"]*bool(conflict),"status":"NOT_ADJUDICATED"})
 # Bounded literal probes test whether a broad 'absent from all standards' statement is defensible.
 # They are diagnostics only: a label/alias hit does not establish semantic equivalence.
 probe_terms={"B2-DEV-032":["poutine"],"B2-DEV-033":["oyakodon","chicken and egg on rice"],"B2-DEV-036":["omurice","omelet with fried rice","omelette with fried rice"],"B2-DEV-019":["nitraria"],"B2-DEV-031":["gyoza","potsticker","pot sticker"],"B2-DEV-010":["cashew chicken","chicken with cashew"],"B2-RED-SUP-003":["potato, steamed","potatoes, steamed","steamed potato"]}
 for rid,terms in probe_terms.items():
  if rid not in sq:continue
  hits=[]
  for k,v in voc.items():
   if v["deprecated"]:continue
   if any(t.casefold() in s.casefold() for t in terms for s in [v["label"]]+v["aliases"]):
    hits.append({"target_key":list(k),"label":v["label"],"locator":v["locator"],"in_generator_target_universe":k in target_universe})
  absence.append({"review_id":rid,"terms":terms,"literal_label_or_alias_hits":hits,"interpretation":"POTENTIAL_COUNTEREXAMPLES_REVIEW_REQUIRED" if hits else "NO_LITERAL_HIT_NOT_PROOF_OF_ABSENCE"})
 require(all_gen["generator_external"]==all_gen["shared_candidate_ids"]+all_gen["generator_hits_critic_hard_negative"]+all_gen["generator_not_reviewed_by_critic"],"EXTERNAL_COMPARISON_CLOSURE")
 require(all_gen["critic_candidates"]==all_gen["shared_candidate_ids"]+all_gen["critic_only_candidate_ids"],"CRITIC_COMPARISON_CLOSURE")
 result={"status":"PASS_FROZEN_DEVELOPMENT_COMPARISON / EXPERT_ADJUDICATION_HOLD","cases":len(case_results),"comparison_scope":"U3-A original 44; no U3-B new query evaluation","candidate_counts":dict(all_gen),
 "generator_critic_case_presence":countpairs({k for k in []}) if False else [{"generator_any":k[0],"critic_any":k[1],"cases":v} for k,v in sorted(matrix.items())],
 "shared_proposal_relation_pairs":[{"generator_proposed_relation":k[0],"critic_relation":k[1],"count":v} for k,v in sorted(relation_pairs.items())],
 "hard_negative_overlap_routes":[{"original_route":k[0],"u2c_route":k[1],"count":v} for k,v in sorted(risk_pair.items())],
 "hard_negative_overlap_types":dict(hard_types),"priority_expert_cases":len(expert_queue),"critic_only_outside_universe":len(crit_outside),
 "literal_absence_probes":[{"review_id":x["review_id"],"hit_count":len(x["literal_label_or_alias_hits"]),"interpretation":x["interpretation"]} for x in absence],
 "independent_accuracy_recall":"NOT_ESTIMABLE","adjudicated_reference_count":0,"accepted_equivalence":0,"mapping_releases":0,"scientific_releases":0,
 "remaining":["Critic suggestions and negatives not expert truth","Generator candidates unreviewed by Critic are neither accepted nor rejected","No U3-B dense retrieval quality estimate from these 44","High-risk semantics, target applicability, source rights and independent expert adjudication remain HOLD"]}
 inp.check()
 return result,case_results,expert_queue,absence,crit_outside

def main(root,profile,out):
 root=root.resolve();out=out.resolve();require(not out.exists() and out.is_relative_to(root/"runs/B2/U3-B/C1"),"NEW_C1_DIRECTORY")
 inp=Inputs(root,profile.resolve())
 f,r,q,v,checks,problems=verify_critic(inp)
 out.mkdir(parents=True);priv=out/"private";priv.mkdir()
 put(out/"CriticFreezeVerificationReport.json",f);putl(priv/"CriticNativeTargetChecks.jsonl",checks);put(priv/"CriticTargetIssues.json",problems)
 print("FREEZE_VERIFICATION",json.dumps(f,ensure_ascii=False),flush=True)
 if problems:
  print("HOLD_NO_COMPARISON",len(problems),flush=True);return
 x,cr,eq,ab,oo=compare(inp,r,q,v)
 putl(priv/"DevelopmentDisagreementRecords.jsonl",cr);put(priv/"ExpertReviewQueue.json",eq);put(priv/"LiteralAbsenceProbe.json",ab);put(priv/"CriticOutsideTargetUniverse.json",oo)
 put(out/"DevelopmentComparisonReport.json",x)
 inp.check()
 put(priv/"InputFence.json",inp.fences)
 files={str(z.relative_to(out)):sha(z) for z in sorted(out.rglob("*")) if z.is_file()}
 receipt={"status":"PASS_C1_DEVELOPMENT_COMPARISON / SCIENTIFIC_QUALIFICATION_HOLD","utc":now(),"profile_sha256":sha(profile),"verified_input_files":len(inp.fences),"output_file_hashes":files,
 "critic_frozen_cases":f["source_only_identity_verified"],"case_comparisons":x["cases"],"priority_expert_cases":x["priority_expert_cases"],"accepted_equivalence":0,"mapping_release_authorized":False,
 "unblinding_authorized_by_pi":True,"prior_exposure_declared":True,"original_inputs_unchanged":True}
 put(out/"C1FreezeReceipt.json",receipt)
 print("COMPARISON",json.dumps(x,ensure_ascii=False),flush=True)
 print("C1_FREEZE",json.dumps({k:v for k,v in receipt.items() if k!="output_file_hashes"},ensure_ascii=False),flush=True)

if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--out",type=P.Path,required=True)
 x=a.parse_args();main(x.root,x.profile,x.out)
