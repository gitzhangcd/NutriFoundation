#!/usr/bin/env python3
"""Real C2 versioned scope, risk/abstention and expert task preparation.
All outputs are development records. No new scientific reference or release.
"""
import argparse,copy,sys,pathlib as P,json,collections as C,hashlib
from datetime import datetime,timezone
HERE=P.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/"u3b"),str(HERE.parent/"u2c")]
from run_u3b import Encoder,top
from core import *
from runtime import verify
from admission import Admission
from jsonschema import Draft202012Validator,FormatChecker
import numpy as np
from scope import parse,scope,B
from risk import decide
V="UDF-U3C2-ENVELOPE-0.1"
C1="runs/B2/U3-B/C1"
U3="runs/B2/U3-B"
FO="foodon:2026-09-20:food_product"
def putl(path,rows):
 with path.open("x",encoding="utf8") as f:
  for x in rows:f.write(canon(x)+"\n")
def shape(p):return {"type":"object","properties":p,"required":list(p),"additionalProperties":False}
def schema(root):
 old=load(root/"schemas/udf/u2c/UDF_U2C_UnifiedContract_v0.1.schema.json")
 d={k:copy.deepcopy(old["$defs"][k]) for k in ("ref","slot","CommonEnvelope")}
 S={"type":"string"};R={"$ref":"#/$defs/ref"};STR={"type":"array","items":S};I={"type":"integer","minimum":0};N={"type":"number"};B1={"type":"boolean"}
 H={"type":"string","pattern":"^[a-f0-9]{64}$"};NR={"anyOf":[R,{"type":"null"}]};NULLS={"type":["string","null"]};DRAFT={"const":"CURATION_DEV"}
 f=shape({"base_mentions":STR,"process_mentions":STR,"modifier_mentions":STR,"component_mentions":STR,"state":{"enum":["CONFLICTING_LABEL","RAW_EXPLICIT","COOKED_EXPLICIT","UNKNOWN"]},"native_grain":S,"feature_origin":{"const":"BOUNDED_LEXICAL_MENTION_NOT_TAXONOMY_OR_RECIPE_TRUTH"}})
 step=shape({"child":S,"parent":S,"axiom_kind":{"enum":["ASSERTED_NAMED_SUBCLASS","NAMED_EQUIVALENT_CLASS","NAMED_EQUIVALENT_CLASS_REVERSE","NECESSARY_NAMED_INTERSECTION_CONJUNCT"]}})
 pp={
 "ScopeAssessment":shape({"iri":S,"native_label":S,"deprecated":B1,"scope_status":{"enum":["HOLD_NON_FOODON_OR_UNLABELED_OR_DEPRECATED","HOLD_EXCLUSION_BRANCH_OVERLAP","HOLD_NONFOOD_OR_NONIDENTITY_ROLE","CORE_RETAINED_DEV","EXTENSION_TYPED_RETRIEVAL_ONLY","HOLD_SCOPE_UNRESOLVED"]},"roles":STR,"exclusion_roots":STR,"asserted_core_member":B1,"bounded_product_reachable":B1,
 "witnesses":{"type":"array","items":shape({"root":S,"steps":{"type":"array","items":step}})},"locator":S,"purpose":DRAFT,"mapping_release_authorized":{"const":False},"snapshot_sha256":H}),
 "SemanticRiskAssessment":shape({"source_ref":R,"target_ref":R,"prior_candidate_ref":NR,"source_legacy_ref":R,"target_legacy_ref":NR,"scope_assessment_ref":NR,
 "cohort":{"enum":["U3A_EXPOSED_44","U3B_FROZEN_284","C2_EXTENSION_U3B_284","C2_EXTENSION_C1_44"]},"target_scope":S,
 "rank_in_frozen_pool":{"type":["integer","null"],"minimum":1},"extension_label_rank":{"type":["integer","null"],"minimum":1},"extension_context_rank":{"type":["integer","null"],"minimum":1},
 "extension_label_cosine":{"type":["number","null"],"minimum":-1.000001,"maximum":1.000001},"extension_context_cosine":{"type":["number","null"],"minimum":-1.000001,"maximum":1.000001},
 "source_dimensions":f,"target_dimensions":f,"explicit_conflicts":STR,"unresolved_conditions":STR,"role_conditions":STR,"identity_evidence":STR,
 "disposition":{"enum":["BLOCK_EXPLICIT_CONFLICT","HOLD_ROLE_OR_SCOPE","HOLD_MISSING_OR_AMBIGUOUS_CONDITION","HOLD_NO_OBSERVABLE_IDENTITY_ANCHOR","REVIEW_ELIGIBLE_DEV_ONLY"]},
 "concept_review_eligible":B1,"concept_equivalence":{"const":"HOLD"},"nutrient_transfer":{"const":"HOLD"},"physical_identity":{"const":"HOLD"},"training":{"const":"HOLD"},"mapping_release":{"const":"HOLD"},"navigation":{"const":"CURATION_DEV_ONLY"},"source_relation_to_target":{"const":"UNRESOLVED"}}),
 "QueryAdmissionDecision":shape({"source_ref":R,"source_legacy_ref":R,"cohort":S,"pool_count":I,"eligible_count":I,"shortlist_refs":{"type":"array","items":R,"uniqueItems":True},"query_status":{"enum":["DEVELOPMENT_REVIEW_AVAILABLE","ABSTAIN_NO_ELIGIBLE_CANDIDATE_IN_RETRIEVED_POOL"]},"scope_note":{"const":"POOL_ONLY_NOT_PROOF_OF_NO_VALID_TARGET"},"scientific_mapping_release":{"const":"HOLD"}}),
 "ExpertTaskDraft":shape({"review_id":S,"source_ref":R,"source_legacy_ref":R,"source_scope":S,"source_native_label":S,"source_native_kind":S,"source_locator":{"type":"object"},"source_artifact_sha256":H,
 "required_roles":STR,"questions":STR,"initial_review_status":{"const":"NOT_ADJUDICATED"},"post_initial_comparison_required":{"const":True},"scientific_reference_qualified":{"const":False},"mapping_release_authorized":{"const":False}})
 }
 e=d["CommonEnvelope"]["properties"];e["kind"]={"enum":list(pp)};e["schema_version"]={"const":V};e["contract_version"]={"const":V};e["governance"]["properties"]["stage"]={"const":"U3-B-C2"};e["governance"]["properties"]["policy_version"]={"const":V}
 for k,p in pp.items():d[k]={"allOf":[{"$ref":"#/$defs/CommonEnvelope"},{"properties":{"kind":{"const":k},"payload":p}}]}
 s={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:nutrifoundation:udf:u3c2:0.1","$defs":d,"oneOf":[{"$ref":"#/$defs/"+k} for k in pp]}
 Draft202012Validator.check_schema(s);return s
def validators(s):
 return {k:Draft202012Validator({"$schema":s["$schema"],"$defs":s["$defs"],"$ref":"#/$defs/"+k},format_checker=FormatChecker()) for k in s["$defs"]["CommonEnvelope"]["properties"]["kind"]["enum"]}
def obj(kind,key,p,clock,prov,dep,rights):
 return seal({"object_id":"u3c2:"+kind+":"+digest([V,key])[:40],"kind":kind,"schema_version":V,"contract_version":V,"lifecycle":"DRAFT","producer_role":"U3C2_CONTROLLER","created_time":clock,"clock_axis":"AUDIT_UTC","provenance_refs":uniq(prov),"dependency_refs":uniq(dep),"source_class":"REAL_DATA","instance_class":"MIXED_CONSTRUCTED","purpose_release_ref":pending("development only; expert qualification absent"),"purpose":"CURATION_DEV","supersedes_ref":na("first C2 revision"),"payload":p,
 "governance":{"legacy_ref":None,"legacy_schema_version":None,"stage":"U3-B-C2","construction_class":"DRV","verification_scope":"PINNED_SOURCE_AND_POLICY_REPLAY","rights_domains":sorted(set(rights)),"release_status":"HOLD","policy_version":V}})
def validate(o,vs,registry):
 er=next(vs[o["kind"]].iter_errors(o),None)
 require(er is None,"C2_SCHEMA:"+("" if er is None else str(er.validator)+":"+"/".join(map(str,er.absolute_path))))
 revision_ok(o)
 require(all(r in registry for r in o["dependency_refs"]+o["provenance_refs"]),"C2_REF_MISSING")
 p=o["payload"]
 if o["kind"]=="ScopeAssessment":
  require(not p["mapping_release_authorized"],"SCOPE_RELEASE")
  for x in p["witnesses"]:
   a=p["iri"]
   for st in x["steps"]:require(st["child"]==a,"WITNESS_CHAIN");a=st["parent"]
   require(a==x["root"],"WITNESS_ROOT")
  require(not (p["scope_status"] in ("CORE_RETAINED_DEV","EXTENSION_TYPED_RETRIEVAL_ONLY") and (p["deprecated"] or p["exclusion_roots"] or not p["native_label"] or not p["witnesses"])),"SCOPE_INELIGIBLE")
 elif o["kind"]=="SemanticRiskAssessment":
  a=lookup(registry,p["source_ref"],"NativeVocabularyRecord");b=lookup(registry,p["target_ref"])
  require(b["kind"] in ("NativeVocabularyRecord","ScopeAssessment"),"TARGET_KIND")
  require(a["governance"]["legacy_ref"]==p["source_legacy_ref"],"SOURCE_IDENTITY")
  if b["kind"]=="NativeVocabularyRecord":require(b["governance"]["legacy_ref"]==p["target_legacy_ref"],"TARGET_IDENTITY")
  else:require(p["target_legacy_ref"] is None and p["scope_assessment_ref"]==p["target_ref"],"EXTENSION_IDENTITY")
  if p["scope_assessment_ref"]:lookup(registry,p["scope_assessment_ref"],"ScopeAssessment")
  needed=[p["source_ref"],p["target_ref"]]+[p[k] for k in ("prior_candidate_ref","scope_assessment_ref") if p[k]]
  require(set(needed)<=set(o["dependency_refs"]),"REQUIRED_RISK_DEPENDENCY")
  require(p["concept_review_eligible"]==(p["disposition"]=="REVIEW_ELIGIBLE_DEV_ONLY") and (not p["explicit_conflicts"] or p["disposition"]=="BLOCK_EXPLICIT_CONFLICT"),"RISK_DISPOSITION")
  require(not p["concept_review_eligible"] or (not p["unresolved_conditions"] and not p["role_conditions"] and bool(p["identity_evidence"])),"RISK_UNSUPPORTED_ELIGIBILITY")
 elif o["kind"]=="QueryAdmissionDecision":
  require(p["query_status"]==("DEVELOPMENT_REVIEW_AVAILABLE" if p["shortlist_refs"] else "ABSTAIN_NO_ELIGIBLE_CANDIDATE_IN_RETRIEVED_POOL"),"ABSTENTION_STATUS")
  require(p["eligible_count"]<=p["pool_count"] and len(p["shortlist_refs"])<=p["eligible_count"],"QUERY_COUNTS")
  for r in p["shortlist_refs"]:
   x=lookup(registry,r,"SemanticRiskAssessment")["payload"];require(x["source_ref"]==p["source_ref"] and x["cohort"]==p["cohort"] and x["concept_review_eligible"],"SHORTLIST_ELIGIBILITY")
 elif o["kind"]=="ExpertTaskDraft":
  a=lookup(registry,p["source_ref"],"NativeVocabularyRecord")["payload"]
  require(p["source_native_label"]==a["native_label"] and p["source_locator"]==a["source_locator"] and p["source_artifact_sha256"]==a["artifact_sha256"],"EXPERT_SOURCE_IDENTITY")

class Runner:
 def __init__(self,root,profile,out):
  self.root=root;self.profile=profile;self.out=out;self.p=load(profile);self.fences={}
  require(self.p["release_authorized"] is False,"RELEASE")
  for path,h in self.p["pins"].items():self.pin(path,h)
  self.pin(str(profile.relative_to(root)));self.pol=load(self.pin(self.p["policy"]))
  self.pin(self.p["u2c_manifest"],self.p["u2c_manifest_sha256"])
  for path in sorted((root/"src/u3c2").glob("*.py")):self.pin(str(path.relative_to(root)))
  # Exact old C1 freeze and its entire input fence; verify without reopening Critic contents.
  r=load(root/C1/"real_001/C1FreezeReceipt.json")
  for rel,h in r["output_file_hashes"].items():self.pin(C1+"/real_001/"+rel,h)
  for rel,h in load(root/C1/"real_001/private/InputFence.json").items():self.pin(rel,h)
  f=load(root/U3/"freeze_001/GeneratorFreezeReceipt.json")
  for rel,h in f["output_file_hashes"].items():self.pin(rel,h)
  require(r["unblinding_authorized_by_pi"] and f["mapping_release_authorized"] is False,"UPSTREAM_SCOPE")
  self.clock=datetime.now(timezone.utc).isoformat()
  self.rt,vr=verify(root,root/self.p["u2c_manifest"],root/self.p["u2c_run"]);self.adm=Admission(self.rt);self.replayed=vr["all_replayed"]
  self.registry=dict(self.rt.b.idx);self.views={};self.records=[];self.schema=schema(root);self.vs=validators(self.schema)
  self.native={ref(o):o for o in self.rt.b.by["NativeVocabularyRecord"]}
  self.scopes={};self.risks=C.defaultdict(list);self.baseline_edges={};self.legacy_scores={}
  print("U2C_FULL_REPLAY",self.replayed,flush=True)
 def pin(self,path,h=None):
  q=self.root/path;p=q.resolve()
  require(p.is_relative_to(self.root) and q.is_file() and not q.is_symlink(),"INPUT_PATH")
  a=sha(p);require(h is None or a==h,"INPUT_HASH:"+str(path))
  k=str(p.relative_to(self.root));require(k not in self.fences or self.fences[k]==a,"INPUT_REOPEN");self.fences[k]=a;return p
 def view(self,r):
  if r not in self.views:
   o=self.adm.view(r);self.views[r]=o;self.registry[ref(o)]=o
  return self.views[r]
 def add(self,o):
  validate(o,self.vs,self.registry);r=ref(o);require(r not in self.registry,"DUPLICATE_C2_RECORD");self.registry[r]=o;self.records.append(o);return o
 def scope_run(self):
  v=parse(self.root/"runs/B2/U3-A/inputs/FoodOn.owl")
  old={o["payload"]["native_key"] for o in self.native.values() if o["payload"]["native_namespace"]==FO}
  sx=[o for o in self.rt.b.by["SourceSnapshotDraft"] if o["payload"]["scope"]==FO];require(len(sx)==1,"FOODON_SNAPSHOT")
  s=self.view(ref(sx[0]));sr=ref(s);payloads,stats=scope(v,self.pol,old)
  for iri,p in payloads.items():
   p["snapshot_sha256"]=sx[0]["payload"]["sha256"]
   o=self.add(obj("ScopeAssessment",[p["snapshot_sha256"],iri,self.pol["version"]],p,self.clock,[sr],[sr],["FOODON_LICENSE_REVIEW"]))
   self.scopes[iri]=o
  six=load(self.root/C1/"validation_001/private/FoodOnScopeDiagnosis.json")
  recovered=sum(payloads[x["target_key"][1]]["scope_status"]=="EXTENSION_TYPED_RETRIEVAL_ONLY" for x in six)
  require(recovered==len(six),"C1_SCOPE_RECOVERY")
  negative=[]
  for i in self.pol["foodon"]["negative_probe_ids"]:
   p=payloads[B+i];require(p["scope_status"].startswith("HOLD"),"NONFOOD_SCOPE_ADMITTED");negative.append(i)
  stats.update({"c1_excluded_unique_classes":len(six),"c1_classes_in_typed_extension":recovered,"negative_probes_held":len(negative),"old_scope_ids_preserved":len(old),"raw_scope_assessments":len(payloads)})
  self.scope_stats=stats;print("SCOPE",json.dumps(stats),flush=True)
 def load_u3(self):
  u=self.root/U3/"real_001/private";m=load(u/"partition_manifest.json")
  self.u3rows=C.defaultdict(list)
  for rel,x in m.items():
   f=self.pin(str((u/"typed_partitions"/rel).relative_to(self.root)),x["sha256"])
   rr=list(lines(f));require(len(rr)==x["rows"] and f.stat().st_size==x["bytes"],"U3B_COLLECTION")
   for o in rr:
    revision_ok(o);require(o["purpose"]=="CURATION_DEV" and o["governance"]["release_status"]=="HOLD","U3B_RELEASE")
    require(ref(o) not in self.registry,"U3B_DUPLICATE");self.registry[ref(o)]=o;self.u3rows[o["kind"]].append(o)
  require(len(self.u3rows["SemanticCandidateRecord"])==29081 and len(self.u3rows["QueryContextRecord"])==284,"U3B_BASELINE")
  self.cases=list(lines(self.root/C1/"real_001/private/DevelopmentDisagreementRecords.jsonl"));require(len(self.cases)==44,"C1_CASES")
  self.c1_by={c["source_ref"]:c for c in self.cases}
  self.risk_by_prior={}
 def assess(self,sr,tr,prior,cohort,target_scope,rank,oldred=False,ext=None):
  s=self.view(sr);a=s["payload"];sref=ref(s)
  if tr is not None:
   t=self.view(tr);b=t["payload"];tref=ref(t);label=b["native_label"];grain=b["native_kind"]
   so=self.scopes.get(b["native_key"]) if target_scope==FO else None
  else:
   so=ext["scope_obj"];t=so;tref=ref(so);label=so["payload"]["native_label"];grain="ONTOLOGY_TYPED_EXTENSION_CATEGORY"
  scope_status=so["payload"]["scope_status"] if so else None
  d=decide({"label":a["native_label"],"grain":a["native_kind"]},{"label":label,"grain":grain},self.pol["risk"],scope_status,oldred)
  p={"source_ref":sref,"target_ref":tref,"prior_candidate_ref":prior,"source_legacy_ref":sr,"target_legacy_ref":tr,"scope_assessment_ref":ref(so) if so else None,
  "cohort":cohort,"target_scope":target_scope,"rank_in_frozen_pool":rank,"extension_label_rank":ext.get("label_rank") if ext else None,"extension_context_rank":ext.get("context_rank") if ext else None,"extension_label_cosine":ext.get("label_cosine") if ext else None,"extension_context_cosine":ext.get("context_cosine") if ext else None,**d}
  dep=[sref,tref]+([prior] if prior else [])+([ref(so)] if so else [])
  prov=[a["source_anchor_ref"]]+([b["source_anchor_ref"]] if tr else so["provenance_refs"])
  o=self.add(obj("SemanticRiskAssessment",[cohort,sref,tref,prior or "extension"],p,self.clock,prov,dep,s["governance"]["rights_domains"]+t["governance"]["rights_domains"]+["MODEL_LICENSE_REVIEW"] if "EXTENSION" in cohort or cohort=="U3B_FROZEN_284" else s["governance"]["rights_domains"]+t["governance"]["rights_domains"]))
  self.risks[(cohort,sr)].append(o)
  if prior:self.risk_by_prior[prior]=o
  return o
 def historical_risk(self):
  # Entire old 44, not just the 23 Critic overlaps. Read admitted source/target refs.
  for c in self.cases:
   sr=c["source_ref"]
   all_rows=c["shared"]+c["critic_hard_negative_overlap"]+c["generator_unreviewed"]+c["generator_other_target_scopes"]
   for z in all_rows:
    e=self.rt.b.idx[z["generator_ref"]];a=e["payload"];t=self.rt.b.idx[a["target_ref"]]["payload"]
    require(a["source_ref"]==sr,"C1_SOURCE")
    self.assess(sr,a["target_ref"],z["generator_ref"],"U3A_EXPOSED_44",t["native_namespace"],a["rank"],z["u2c_route"]=="RED")
  require(sum(len(v) for (c,r),v in self.risks.items() if c=="U3A_EXPOSED_44")==355,"C1_EDGE_COUNT")
  for n,o in enumerate(self.u3rows["SemanticCandidateRecord"],1):
   p=o["payload"];self.assess(p["source_legacy_ref"],p["target_legacy_ref"],ref(o),"U3B_FROZEN_284",p["target_scope"],p["pool_rank"],p["review_route"]=="RED")
   if n%10000==0:print("REAL_U3B_EDGES_RESCREENED",n,flush=True)
 def extension(self):
  p=load(self.root/"configs/udf/u3b/U3B_PilotProfile_v0.1.json")
  d=self.root/p["model_dir"];m=load(self.pin(str((d/"ModelManifest.json").relative_to(self.root)),p["model_manifest_sha256"]))
  for x in m["files"]:self.pin(str((d/x["file"]).relative_to(self.root)),x["sha256"])
  enc=Encoder(d,p)
  ids=sorted(i for i,o in self.scopes.items() if o["payload"]["scope_status"]=="EXTENSION_TYPED_RETRIEVAL_ONLY")
  require(bool(ids),"EXTENSION_EMPTY")
  tm=enc.encode(["passage: "+self.scopes[i]["payload"]["native_label"] for i in ids])
  q=[]
  for o in self.u3rows["QueryContextRecord"]:
   z=o["payload"];q.append(("C2_EXTENSION_U3B_284",z["source_legacy_ref"],z["label_query"],z["context_query"]))
  for c in self.cases:
   label="query: "+c["source_native_label"];q.append(("C2_EXTENSION_C1_44",c["source_ref"],label,label))
  mat=enc.encode([x[2] for x in q]+[x[3] for x in q]);n=len(q);scores=mat@tm.T
  K=self.pol["risk"]["extension_top_k_per_form"]
  for i,(cohort,sr,_,_) in enumerate(q):
   a={j:k+1 for k,j in enumerate(top(scores[i],K,ids))};b={j:k+1 for k,j in enumerate(top(scores[i+n],K,ids))}
   for j in sorted(set(a)|set(b),key=lambda j:(-(1/(60+a[j]) if j in a else 0)-(1/(60+b[j]) if j in b else 0),ids[j])):
    x={"scope_obj":self.scopes[ids[j]],"label_rank":a.get(j),"context_rank":b.get(j),"label_cosine":float(scores[i,j]),"context_cosine":float(scores[i+n,j])}
    self.assess(sr,None,None,cohort,"foodon:2026-09-20:typed_extension",None,ext=x)
  print("EXTENSION_RETRIEVAL",len(ids),n,sum(len(v) for (c,r),v in self.risks.items() if "EXTENSION" in c),flush=True)
 def query_decisions(self):
  # Include original unmatched queries in denominators.
  for c in self.cases:self.risks.setdefault(("U3A_EXPOSED_44",c["source_ref"]),[])
  for q in self.u3rows["QueryContextRecord"]:self.risks.setdefault(("U3B_FROZEN_284",q["payload"]["source_legacy_ref"]),[])
  summaries=C.defaultdict(C.Counter)
  for (cohort,sr),rs in sorted(self.risks.items()):
   a=self.view(sr);eligible=[o for o in rs if o["payload"]["concept_review_eligible"]];by=C.defaultdict(list)
   for x in eligible:by[x["payload"]["target_scope"]].append(x)
   sel=[]
   for k,xs in sorted(by.items()):sel.extend(sorted(xs,key=lambda o:(o["payload"]["rank_in_frozen_pool"] or 99999,o["object_id"]))[:self.pol["risk"]["shortlist_per_query_scope"]])
   z={"source_ref":ref(a),"source_legacy_ref":sr,"cohort":cohort,"pool_count":len(rs),"eligible_count":len(eligible),"shortlist_refs":[ref(o) for o in sel],"query_status":"DEVELOPMENT_REVIEW_AVAILABLE" if sel else "ABSTAIN_NO_ELIGIBLE_CANDIDATE_IN_RETRIEVED_POOL","scope_note":"POOL_ONLY_NOT_PROOF_OF_NO_VALID_TARGET","scientific_mapping_release":"HOLD"}
   self.add(obj("QueryAdmissionDecision",[cohort,a["object_id"]],z,self.clock,[a["payload"]["source_anchor_ref"]],[ref(a)]+[ref(x) for x in sel],a["governance"]["rights_domains"]+["DERIVED_REVIEW_RESTRICTED"]))
   s=summaries[cohort];s["queries"]+=1;s["pool_edges"]+=len(rs);s["eligible_edges"]+=len(eligible);s["shortlist_edges"]+=len(sel);s["queries_abstained"]+=not bool(sel);s["queries_with_review_candidate"]+=bool(sel)
   for o in rs:s[o["payload"]["disposition"]]+=1
  return {k:dict(v) for k,v in summaries.items()}
 def expert(self):
  pri=load(self.root/C1/"real_001/private/ExpertReviewQueue.json");require(len(pri)==36 and len({x["review_id"] for x in pri})==36,"EXPERT_QUEUE")
  byid={c["review_id"]:c for c in self.cases};first=[];post=[];stats=C.Counter()
  qs=["独立解释来源食品的对象粒度、明确的食物状态和必要限定。未知信息保留未知。","在允许的原件中核对适用目标ID、方向与条件；可以返回无合格目标。","区分概念关联、同一物理实例、营养值可比性；本任务不授权营养值迁移。"]
  for q in pri:
   c=byid[q["review_id"]];a=self.view(c["source_ref"]);p=a["payload"];rid=q["review_id"]
   roles=["FOOD_ONTOLOGY_OR_FOOD_SCIENCE"]
   if c["critic_expert_recommended"] or c["critic_hard_negative_overlap"]:roles.append("NUTRITION_COMPOSITION_OR_MEASUREMENT_AS_NEEDED")
   if p["native_kind"] in ("RECIPE_REFERENCE","RECIPE_VARIANT_LABEL","MENU_ITEM_REFERENCE"):roles.append("REGIONAL_RECIPE_EXPERT_AS_NEEDED")
   z={"review_id":rid,"source_ref":ref(a),"source_legacy_ref":c["source_ref"],"source_scope":p["native_namespace"],"source_native_label":p["native_label"],"source_native_kind":p["native_kind"],"source_locator":p["source_locator"],"source_artifact_sha256":p["artifact_sha256"],"required_roles":roles,"questions":qs,"initial_review_status":"NOT_ADJUDICATED","post_initial_comparison_required":True,"scientific_reference_qualified":False,"mapping_release_authorized":False}
   o=self.add(obj("ExpertTaskDraft",[rid,a["object_id"]],z,self.clock,[p["source_anchor_ref"]],[ref(a)],a["governance"]["rights_domains"]+["DERIVED_REVIEW_RESTRICTED"]));first.append(o)
   # Post-initial packet, limited priority edges; full old comparison remains accessible only after authorization.
   entries=[]
   for x in sorted(c["critic_hard_negative_overlap"],key=lambda v:(v["u2c_route"]!="RED",-v["ranking_score"],v["generator_ref"])):
    entries.append({"kind":"HARD_NEGATIVE_OVERLAP","generator_ref":x["generator_ref"],"risk_ref":ref(self.risk_by_prior[x["generator_ref"]]),"target_key":x["target_key"],"target_label":x["target_label"],"critic_reason":x["critic_rationale"]})
   for x in c["shared"]:
    entries.append({"kind":"SHARED_TARGET_RELATION_COMPARISON","generator_ref":x["generator_ref"],"risk_ref":ref(self.risk_by_prior[x["generator_ref"]]),"target_key":x["target_key"],"target_label":x["target_label"],"critic_reason":x["critic_reason"]})
   for x in c["critic_only"]:
    entries.append({"kind":"CRITIC_ONLY_CANDIDATE","target_system":x["target_system"],"target_native_id":x["target_native_id"],"target_native_label":x["target_native_label"],"target_source_locator":x["target_source_locator"],"critic_relation":x["source_relation_to_target"],"critic_reason":x["relation_reason"]})
   for x in c["generator_unreviewed"]:
    entries.append({"kind":"UNREVIEWED_GENERATOR_CANDIDATE","generator_ref":x["generator_ref"],"risk_ref":ref(self.risk_by_prior[x["generator_ref"]]),"target_key":x["target_key"],"target_label":x["target_label"]})
   mx=self.pol["expert"]["max_evidence_edges_per_priority_case"];post.append({"review_id":rid,"expert_task_ref":ref(o),"priority_evidence":entries[:mx],"additional_evidence_count":max(0,len(entries)-mx),"full_evidence_locator":C1+"/real_001/private/DevelopmentDisagreementRecords.jsonl#review_id="+rid,"exposure_condition":"AFTER_INDEPENDENT_INITIAL_JUDGMENT_FREEZE_AND_EXPLICIT_AUTHORIZATION","adjudication":"PENDING"})
   stats["source_first_tasks"]+=1;stats["priority_evidence_cards"]+=min(len(entries),mx);stats["additional_evidence_items"]+=max(0,len(entries)-mx);stats["cases_with_more_evidence"]+=len(entries)>mx
  require({x["payload"]["review_id"] for x in first}=={x["review_id"] for x in post} and len(first)==36,"EXPERT_PACKET_CLOSURE")
  self.first=first;self.post=post
  return dict(stats)
 def finish(self):
  self.scope_run();self.load_u3();self.historical_risk();self.extension()
  q=self.query_decisions();e=self.expert()
  risk_overlap=C.Counter()
  for c in self.cases:
   for x in c["critic_hard_negative_overlap"]:
    z=self.risk_by_prior[x["generator_ref"]]["payload"];risk_overlap[(x["u2c_route"],z["disposition"])]+=1
  require(sum(risk_overlap.values())==23,"C1_NEGATIVE_OVERLAP")
  # Actual six recovered class targets: check whether the supplemental retrieval returned
  # each of the seven source-target edges, separately from scope inclusion.
  outside=load(self.root/C1/"real_001/private/CriticOutsideTargetUniverse.json");byid={c["review_id"]:c for c in self.cases};hits=0
  for x in outside:
   sr=byid[x["review_id"]]["source_ref"];tr=ref(self.scopes[x["target_key"][1]])
   hits+=any(o["payload"]["target_ref"]==tr for o in self.risks[("C2_EXTENSION_C1_44",sr)])
  self.rt.b.verify_files()
  require(all(sha(self.root/p)==h for p,h in self.fences.items()),"INPUT_FENCE")
  self.out.mkdir(parents=True);priv=self.out/"private";priv.mkdir();tree=priv/"typed_partitions";tree.mkdir()
  files={};by=C.defaultdict(list)
  for o in self.records:
   rights=o["governance"]["rights_domains"];part=rights[0] if len(rights)==1 else "MIXED_RESTRICTED_"+digest(rights)[:16];by[part+"/"+o["kind"]+".jsonl"].append(o)
  for rel,rs in sorted(by.items()):
   f=tree/rel;f.parent.mkdir(parents=True,exist_ok=True);putl(f,rs);files[rel]={"rows":len(rs),"sha256":sha(f),"bytes":f.stat().st_size}
  put(priv/"partition_manifest.json",files)
  put(priv/"ExpertSourceFirstQueue.json",[o["payload"]|{"task_ref":ref(o)} for o in self.first]);put(priv/"ExpertComparisonHidden.json",self.post)
  put(priv/"InputFence.json",self.fences);put(self.out/"C2_Contract.schema.json",self.schema)
  report={"status":"PASS_BOUNDED_C2_DEVELOPMENT_REMEDIATION / EXPERT_AND_RELEASE_HOLD","version":V,"utc":self.clock,"u2c_replayed_objects":self.replayed,"admitted_u2c_views":len(self.views),"scope":self.scope_stats,
  "cohort_results":q,"actual_c1_critic_overlap_routes":[{"old_route":k[0],"new_disposition":k[1],"edges":v} for k,v in sorted(risk_overlap.items())],
  "c1_excluded_edges_in_extension_topk":hits,"c1_excluded_edges_total":len(outside),"expert_packet":e,"typed_objects":len(self.records),"typed_kind_counts":dict(C.Counter(o["kind"] for o in self.records)),"rights_partitions":len({x.split("/")[0] for x in files}),
  "schema_validated_objects":len(self.records),"input_fence_count":len(self.fences),"source_inputs_unchanged":True,"partition_manifest_sha256":sha(priv/"partition_manifest.json"),"profile_sha256":sha(self.profile),"policy_sha256":sha(self.root/self.p["policy"]),
  "expert_adjudication_completed":0,"independent_reference_count":0,"accepted_equivalence":0,"mapping_release_count":0,"science_release_count":0,
  "limitations":["bounded necessary named axiom expansion, no complete OWL reasoner","candidate-only scope lanes, no ontology equivalence or blanket admission","lexical mention extraction and conservative rule routing, not verified taxonomy/recipe semantics","abstention refers only to evidence in retrieved pool, not proof no valid target","extension separate scores; no reranking historical quantized scores","C1 original 44 exposed development; U3B new independent queue unchanged, no independent result read","expert source-first packet prepared, no qualified reviewer judgments or formal blind access control","no precision, recall, nutritional transfer or B3 calculation"]}
  put(self.out/"C2ExecutionReport.json",report)
  print(json.dumps(report,ensure_ascii=False),flush=True)
def main(root,profile,out):
 root=root.resolve();profile=profile.resolve();out=out.resolve()
 require(not out.exists() and out.is_relative_to(root/"runs/B2/U3-B/C2"),"NEW_C2_RUN")
 Runner(root,profile,out).finish()
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.profile,x.out)
