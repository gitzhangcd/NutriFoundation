#!/usr/bin/env python3
"""Versioned C2-R1 verified local consumer boundary.
No caller-provided 'verified' dictionary; root profile + controller-pinned receipt
are the trust anchors. All overlays rederived from frozen source/old edges.
This is application verification, not a sandbox against arbitrary local Python.
"""
import argparse,sys,pathlib as P,json,hashlib,copy,collections as C,os
from datetime import datetime,timezone
from jsonschema import Draft202012Validator,FormatChecker
HERE=P.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"u2c"))
from core import canon,digest,ref,revision_ok,seal,require,sha,load,lines,put,pending,na,uniq
from scope_v2 import derive
from risk_v2 import evaluate
V="UDF-U3C2R-ENVELOPE-0.1"
C2="runs/B2/U3-B/C2"
C1="runs/B2/U3-B/C1"
U3="runs/B2/U3-B"
U2="runs/B1/U2-C/real_001"
FO="foodon:2026-09-20:food_product"
def shape(p):return {"type":"object","properties":p,"required":list(p),"additionalProperties":False}
def schema(root):
 old=load(root/C2/"real_001/C2_Contract.schema.json")
 d={k:copy.deepcopy(old["$defs"][k]) for k in ("ref","slot","CommonEnvelope")}
 S={"type":"string"};R={"$ref":"#/$defs/ref"};NR={"anyOf":[R,{"type":"null"}]};B={"type":"boolean"};I={"type":"integer","minimum":0};STR={"type":"array","items":S};RARR={"type":"array","items":R,"uniqueItems":True}
 H={"type":"string","pattern":"^[a-f0-9]{64}$"}
 f=shape({"normalized_complete_label":S,"current_state":{"enum":["RAW_EXPLICIT","COOKED_EXPLICIT","UNKNOWN","AMBIGUOUS"]},"explicit_mentions":STR,"origin_mentions":STR,"negative_mentions":STR,"unresolved_state":STR,"form_mentions":STR})
 pp={
 "VerifiedScopeOverlay":shape({"prior_scope_ref":R,"iri":S,"native_label":S,"scope_status":{"enum":["CORE_RETAINED_DEV","EXTENSION_TYPED_RETRIEVAL_ONLY","DUAL_ROLE_ORGANISM_REVIEW_ONLY","HOLD_EXCLUSION_BRANCH_OVERLAP","HOLD_NONFOOD_OR_NONIDENTITY_ROLE","HOLD_SCOPE_UNRESOLVED","HOLD_NON_FOODON_OR_UNLABELED_OR_DEPRECATED"]},"review_role":S,"original_scope_status":S,"original_asserted_core_member":B,"snapshot_sha256":H,"mapping_release":{"const":"HOLD"}}),
 "VerifiedRiskOverlay":shape({"prior_risk_ref":R,"source_ref":R,"target_ref":R,"scope_ref":NR,"prior_candidate_ref":NR,"source_legacy_ref":R,"target_legacy_ref":NR,"cohort":S,"target_scope":S,"rank_in_frozen_pool":{"type":["integer","null"],"minimum":1},"extension_pool_rank":{"type":["integer","null"],"minimum":1},
 "source_dimensions":f,"target_dimensions":f,"full_label_evidence":{"enum":["NORMALIZED_COMPLETE_SURFACE","AUTHORED_COMPLETE_BILINGUAL_PAIR","NONE"]},"explicit_conflicts":STR,"unresolved_conditions":STR,"role_conditions":STR,"role_policy_mode":S,"disposition":{"enum":["BLOCK_EXPLICIT_CONFLICT","HOLD_SCOPE_OR_UNREGISTERED_ROLE","HOLD_UNRESOLVED_CONDITIONS","CONDITIONAL_RELATION_REVIEW_ONLY","COMPLETE_SURFACE_REVIEW_ONLY"]},"review_eligible":B,"scientific_equivalence":{"const":"HOLD"},"nutrient_transfer":{"const":"HOLD"},"physical_identity":{"const":"HOLD"},"training":{"const":"HOLD"},"mapping_release":{"const":"HOLD"},"relation":{"const":"UNRESOLVED"}}),
 "VerifiedQueryOverlay":shape({"prior_query_ref":R,"source_ref":R,"source_legacy_ref":R,"cohort":S,"pool_count":I,"eligible_count":I,"shortlist_refs":RARR,"query_status":{"enum":["DEVELOPMENT_REVIEW_AVAILABLE","ABSTAIN_NO_ELIGIBLE_CANDIDATE_IN_RETRIEVED_POOL"]},"mapping_release":{"const":"HOLD"}})}
 e=d["CommonEnvelope"]["properties"];e["kind"]={"enum":list(pp)};e["schema_version"]={"const":V};e["contract_version"]={"const":V};e["governance"]["properties"]["stage"]={"const":"U3-B-C2-R1"};e["governance"]["properties"]["policy_version"]={"const":V}
 for k,p in pp.items():d[k]={"allOf":[{"$ref":"#/$defs/CommonEnvelope"},{"properties":{"kind":{"const":k},"payload":p}}]}
 s={"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:nutrifoundation:udf:u3c2r:0.1","$defs":d,"oneOf":[{"$ref":"#/$defs/"+k} for k in pp]}
 Draft202012Validator.check_schema(s);return s
def validators(s):
 return {k:Draft202012Validator({"$schema":s["$schema"],"$defs":s["$defs"],"$ref":"#/$defs/"+k},format_checker=FormatChecker()) for k in s["$defs"]["CommonEnvelope"]["properties"]["kind"]["enum"]}
def obj(kind,old,p,clock,dep,rights,prov):
 return seal({"object_id":"u3c2r:"+kind+":"+digest([V,old["object_id"]])[:40],"kind":kind,"schema_version":V,"contract_version":V,"lifecycle":"DRAFT","producer_role":"U3C2R_VERIFIED_CONTROLLER","created_time":clock,"clock_axis":"AUDIT_UTC","provenance_refs":uniq(prov),"dependency_refs":uniq(dep),"source_class":"REAL_DATA","instance_class":"MIXED_CONSTRUCTED","purpose_release_ref":pending("development only"),"purpose":"CURATION_DEV","supersedes_ref":na("versioned overlay; old record preserved"),"payload":p,"governance":{"legacy_ref":ref(old),"legacy_schema_version":old["schema_version"],"stage":"U3-B-C2-R1","construction_class":"DRV","verification_scope":"RECOMPUTED_FROM_PINNED_INPUT","rights_domains":sorted(set(rights)),"release_status":"HOLD","policy_version":V}})
def dump_lines(p,rs):
 with p.open("x",encoding="utf8") as f:
  for o in rs:f.write(canon(o)+"\n")
def utc():return datetime.now(timezone.utc).isoformat()
class Inputs:
 def __init__(self,root,profile,profile_hash):
  self.root=root.resolve();self.fences={};self.registry={};self.native={};self.c2={};self.prior={};self.profile_path=profile.resolve()
  self.pin(str(self.profile_path.relative_to(self.root)),profile_hash)
  self.p=load(profile);require(self.p["release_authorized"] is False,"PROFILE_RELEASE")
  for k,h in self.p["pins"].items():self.pin(k,h)
  self.policy=load(self.pin(self.p["policy"]))
  # C2 frozen audit receipt and scope fence, all exact paths/hashes.
  cfg=load(self.root/"configs/audit/tasks/B2_U3B_C2_Impl_Gemini_001.json")
  cr=self.root/C2/"CriticAudit_Gemini_001";f=load(cr/"CriticFreezeReceipt.json")
  require(f["task_id"]==cfg["task_id"] and f["qualification_decision"]=="HOLD","AUDIT_IDENTITY")
  for k,h in f["output_file_hashes"].items():self.pin(str((cr/k).relative_to(self.root)),h)
  for x in cfg["allowed_inputs"]:self.pin(x["path"],x["sha256"])
  self.audit=f;self.findings=list(lines(cr/"AuditFindings.jsonl"))
  require(len(self.findings)==12 and dict(C.Counter(x["severity"] for x in self.findings))==f["counts"]["findings_by_severity"],"AUDIT_FINDINGS")
  for k,h in load(self.root/C2/"real_001/private/InputFence.json").items():self.pin(k,h)
  c1=load(self.root/C1/"real_001/C1FreezeReceipt.json")
  for rel,h in c1["output_file_hashes"].items():self.pin(C1+"/real_001/"+rel,h)
  self.old_policy=load(self.root/self.policy["baseline_c2_policy"])
  self.schema=schema(self.root);self.vs=validators(self.schema)
 def pin(self,rel,h=None):
  q=self.root/rel;p=q.resolve()
  require(p.is_relative_to(self.root) and q.is_file() and not q.is_symlink(),"UNSAFE_PIN")
  a=sha(p);require(h is None or a==h,"PIN_CHANGED:"+str(rel))
  k=str(p.relative_to(self.root));require(k not in self.fences or self.fences[k]==a,"REOPEN_DRIFT");self.fences[k]=a;return p
 def partition(self,base,kind,manifest_hash=None):
  base=self.root/base;mp=base/"private/partition_manifest.json";m=load(self.pin(str(mp.relative_to(self.root)),manifest_hash))
  for rel,x in sorted(m.items()):
   if not rel.endswith("/"+kind+".jsonl"):continue
   f=self.pin(str((base/"private/typed_partitions"/rel).relative_to(self.root)),x["sha256"])
   require(f.stat().st_size==x["bytes"],"PARTITION_SIZE");n=0
   for o in lines(f):
    revision_ok(o);require(o["kind"]==kind and o["purpose"]=="CURATION_DEV","OBJECT_KIND_PURPOSE")
    n+=1;yield o
   require(n==x["rows"],"PARTITION_COUNT")
 def load_old(self):
  self.c2_report=load(self.root/C2/"real_001/C2ExecutionReport.json")
  for o in self.partition(U2,"NativeVocabularyRecord",self.p["pins"][U2+"/private/partition_manifest.json"]):
   r=ref(o);l=o["governance"]["legacy_ref"]
   require(r not in self.registry and l not in self.native and o["governance"]["release_status"]=="HOLD","NATIVE_DUPLICATE")
   self.registry[r]=o;self.native[l]=o
  require(len(self.native)==65592,"NATIVE_COUNT")
  # Resolve actual original U3-A generator and U3-B candidate endpoint identities.
  base=self.root/"runs/B2/U3-A/real_002/private";m=load(self.pin(str((base/"collection_manifest.json").relative_to(self.root)),self.p["pins"]["runs/B2/U3-A/real_002/private/collection_manifest.json"]))
  f=self.pin(str((base/"typed_collections/AlignmentRecord.jsonl").relative_to(self.root)),m["AlignmentRecord.jsonl"]["sha256"])
  for o in lines(f):revision_ok(o);self.prior[ref(o)]=o
  for o in self.partition(U3+"/real_001","SemanticCandidateRecord",self.p["pins"][U3+"/real_001/private/partition_manifest.json"]):self.prior[ref(o)]=o
  require(len(self.prior)==17079+29081,"PRIOR_EDGE_COUNT")
  for kind,n in (("ScopeAssessment",40107),("SemanticRiskAssessment",35710),("QueryAdmissionDecision",656),("ExpertTaskDraft",36)):
   rr=list(self.partition(C2+"/real_001",kind,self.c2_report["partition_manifest_sha256"]))
   require(len(rr)==n,"C2_KIND_COUNT")
   self.c2[kind]=rr
   for o in rr:
    r=ref(o);require(r not in self.registry and o["governance"]["release_status"]=="HOLD","C2_OBJECT_DUPLICATE");self.registry[r]=o
  self.registry.update(self.prior)
  self.cases=list(lines(self.root/C1/"real_001/private/DevelopmentDisagreementRecords.jsonl"));require(len(self.cases)==44,"C1_CASE_COUNT")
  self.old_routes={}
  for c in self.cases:
   for k in ("shared","critic_hard_negative_overlap","generator_unreviewed","generator_other_target_scopes"):
    for z in c[k]:
     self.old_routes[z["generator_ref"]]=(c["source_ref"],z["u2c_route"],z["target_key"])
  require(len(self.old_routes)==355,"C1_EDGE_COUNT")
  print("PINNED_INPUTS_AND_OLD_RECORDS",len(self.fences),len(self.native),len(self.prior),flush=True)
 def verify_exact(self,actual,expected,registry):
  er=next(self.vs[actual["kind"]].iter_errors(actual),None)
  require(er is None,"R1_SCHEMA:"+("" if er is None else str(er.validator)))
  revision_ok(actual)
  require(all(x in registry for x in actual["dependency_refs"]),"R1_DEPENDENCY_CLOSURE")
  require(canon(actual)==canon(expected),"R1_RECOMPUTE_MISMATCH")
  return actual
 def derive(self,clock):
  self.load_old();self.clock=clock;self.records={};self.scopes={};self.risks={};self.queries={};self.groups=C.defaultdict(list)
  oldfo={o["payload"]["native_key"] for o in self.native.values() if o["payload"]["native_namespace"]==FO}
  raw=self.pin("runs/B2/U3-A/inputs/FoodOn.owl",self.policy["expert_target_files"][0]["sha256"])
  orig,new,self.scope_stats=derive(raw,self.old_policy,self.policy,oldfo)
  self.scope_raw=orig
  # Old scope objects must themselves exactly match policy/OWL-derived original
  # (witness roots AND every named edge AND exclusion status). No caller witness trust.
  for o in self.c2["ScopeAssessment"]:
   p=o["payload"];iri=p["iri"];require(iri in orig and iri not in self.scopes,"SCOPE_IDENTITY")
   require(canon(p)==canon({**orig[iri],"snapshot_sha256":self.policy["expert_target_files"][0]["sha256"]}),"OLD_SCOPE_RAW_RECOMPUTE_MISMATCH")
   z={"prior_scope_ref":ref(o),**new[iri],"snapshot_sha256":p["snapshot_sha256"],"mapping_release":"HOLD"}
   x=obj("VerifiedScopeOverlay",o,z,clock,[ref(o)],o["governance"]["rights_domains"],o["provenance_refs"])
   self.add(x);self.scopes[iri]=x
  require(len(self.scopes)==len(orig)==40107,"SCOPE_CLOSURE")
  print("SCOPE_REDERIVED",len(self.scopes),flush=True)
  # Preserve every candidate edge, not only the old shortlist.
  for i,o in enumerate(self.c2["SemanticRiskAssessment"],1):
   p=o["payload"];s=self.native[p["source_legacy_ref"]];require(ref(s)==p["source_ref"],"SOURCE_ENDPOINT")
   sr=ref(s);tr=p["target_legacy_ref"];pr=p["prior_candidate_ref"];scope_o=None;ext_rank=None
   if tr:
    t=self.native[tr];require(ref(t)==p["target_ref"] and p["target_scope"]==t["payload"]["native_namespace"],"TARGET_ENDPOINT")
    tp=t["payload"];label=tp["native_label"];grain=tp["native_kind"];targetref=ref(t)
    if tp["native_namespace"]==FO:
     scope_o=self.scopes[tp["native_key"]];require(p["scope_assessment_ref"]==scope_o["payload"]["prior_scope_ref"],"FOODON_SCOPE_BINDING")
    else:require(p["scope_assessment_ref"] is None,"NON_FOODON_SCOPE_BINDING")
   else:
    require(p["cohort"].startswith("C2_EXTENSION") and p["target_ref"]==p["scope_assessment_ref"],"EXTENSION_TARGET")
    old_scope=self.registry[p["target_ref"]]["payload"];scope_o=self.scopes[old_scope["iri"]];require(old_scope["scope_status"]=="EXTENSION_TYPED_RETRIEVAL_ONLY","EXTENSION_OLD_SCOPE")
    label=old_scope["native_label"];grain="ONTOLOGY_TYPED_EXTENSION_CATEGORY";targetref=ref(scope_o);t=scope_o
    ranks=[x for x in (p["extension_label_rank"],p["extension_context_rank"]) if x is not None];require(bool(ranks),"EXTENSION_RANK");ext_rank=min(ranks)
   red=False
   if pr:
    a=self.prior[pr]["payload"]
    if p["cohort"]=="U3A_EXPOSED_44":
     require(pr in self.old_routes and self.old_routes[pr][0]==p["source_legacy_ref"] and a["source_ref"]==p["source_legacy_ref"] and a["target_ref"]==tr,"C1_PRIOR_IDENTITY")
     red=self.old_routes[pr][1]=="RED"
    else:
     require(p["cohort"]=="U3B_FROZEN_284" and a["source_legacy_ref"]==p["source_legacy_ref"] and a["target_legacy_ref"]==tr and a["source_ref"]==sr and a["target_ref"]==targetref,"U3B_PRIOR_IDENTITY")
     red=a["review_route"]=="RED"
   else:require(p["cohort"].startswith("C2_EXTENSION"),"MISSING_PRIOR_CANDIDATE")
   a=s["payload"];ss=scope_o["payload"]["scope_status"] if scope_o else None
   z={"prior_risk_ref":ref(o),"source_ref":sr,"target_ref":targetref,"scope_ref":ref(scope_o) if scope_o else None,"prior_candidate_ref":pr,"source_legacy_ref":p["source_legacy_ref"],"target_legacy_ref":tr,"cohort":p["cohort"],"target_scope":p["target_scope"],"rank_in_frozen_pool":p["rank_in_frozen_pool"],"extension_pool_rank":ext_rank,**evaluate({"label":a["native_label"],"grain":a["native_kind"]},{"label":label,"grain":grain},self.policy,ss,red)}
   deps=[ref(o),sr,targetref]+([ref(scope_o)] if scope_o else [])+([pr] if pr else [])
   x=obj("VerifiedRiskOverlay",o,z,clock,deps,o["governance"]["rights_domains"],o["provenance_refs"])
   self.add(x);self.risks[ref(o)]=x;self.groups[(z["cohort"],z["source_legacy_ref"])].append(x)
   if i%10000==0:print("RISK_REDERIVED",i,flush=True)
  require(len(self.risks)==35710,"RISK_CLOSURE")
  for o in self.c2["QueryAdmissionDecision"]:
   p=o["payload"];k=(p["cohort"],p["source_legacy_ref"]);require(k not in self.queries,"QUERY_DUPLICATE")
   rr=self.groups[k];require(len(rr)==p["pool_count"],"QUERY_POOL_CLOSURE")
   s=self.native[p["source_legacy_ref"]];require(ref(s)==p["source_ref"],"QUERY_SOURCE")
   b=C.defaultdict(list)
   for x in rr:
    if x["payload"]["review_eligible"]:b[x["payload"]["target_scope"]].append(x)
   sel=[]
   for _,rs in sorted(b.items()):
    sel+=sorted(rs,key=lambda a:(a["payload"]["rank_in_frozen_pool"] or a["payload"]["extension_pool_rank"] or 99999,a["object_id"]))[:self.policy["max_review_edges_per_scope"]]
   z={"prior_query_ref":ref(o),"source_ref":ref(s),"source_legacy_ref":p["source_legacy_ref"],"cohort":p["cohort"],"pool_count":len(rr),"eligible_count":sum(map(len,b.values())),"shortlist_refs":[ref(x) for x in sel],"query_status":"DEVELOPMENT_REVIEW_AVAILABLE" if sel else "ABSTAIN_NO_ELIGIBLE_CANDIDATE_IN_RETRIEVED_POOL","mapping_release":"HOLD"}
   x=obj("VerifiedQueryOverlay",o,z,clock,[ref(o),ref(s)]+z["shortlist_refs"],o["governance"]["rights_domains"],o["provenance_refs"])
   self.add(x);self.queries[k]=x
  require(len(self.queries)==656 and set(self.groups)==set(self.queries),"QUERY_CLOSURE")
  self.check_fences()
  return self
 def add(self,o):
  r=ref(o);require(r not in self.registry,"NEW_OBJECT_DUPLICATE")
  self.verify_exact(o,o,self.registry);self.registry[r]=o;self.records[r]=o
 def check_fences(self):
  require(all(sha(self.root/p)==h for p,h in self.fences.items()),"FENCE_CHANGED")
 def summarize(self):
  c=C.defaultdict(C.Counter);scope_counts=C.Counter()
  for k,q in self.queries.items():
   co=k[0];p=q["payload"];a=c[co];a["queries"]+=1;a["pool_edges"]+=p["pool_count"];a["eligible_edges"]+=p["eligible_count"];a["shortlist_edges"]+=len(p["shortlist_refs"]);a["queries_with_review"]+=bool(p["shortlist_refs"]);a["abstentions"]+=not bool(p["shortlist_refs"])
   for r in self.groups[k]:
    z=r["payload"];a[z["disposition"]]+=1
    if z["review_eligible"]:scope_counts[(co,z["target_scope"],z["disposition"])]+=1
  old_eligible=0;old_retained=0;bad_held=0;old_changed=[]
  badkeys={("B2-DEV-016","chicken egg jam"),("B2-DEV-020","cottage cheese (dry)"),("B2-DEV-020","cottage cheese (creamed)"),("B2-DEV-021","corn oil"),("B2-DEV-021","gingelly oil")}
  bad=set()
  slice0=load(self.root/C2/"audit_slice_001/private/Exposed44RiskAuditSlice.json")
  for x in slice0:
   old=x["c2_assessment"];p=old["payload"];z=self.risks[ref(old)]["payload"];a=x["c1_evidence"]
   if p["concept_review_eligible"]:
    old_eligible+=1;old_retained+=z["review_eligible"]
   if (a["review_id"],a["target_label"]) in badkeys:
    bad.add(ref(old));bad_held+=not z["review_eligible"]
  require(old_eligible==11 and len(bad)==5 and bad_held==5,"EXPOSED_FIVE_REGRESSION")
  neg=C.Counter()
  for x in slice0:
   a=x["c1_evidence"]
   if a["group"]=="critic_hard_negative_overlap":
    z=self.risks[ref(x["c2_assessment"])]["payload"];neg[(a["u2c_route"],z["disposition"])]+=1
    require(not z["review_eligible"],"C1_NEGATIVE_REVIEW_ADMITTED")
  return {"scope":self.scope_stats,"cohorts":{k:dict(v) for k,v in c.items()},"eligible_by_target_scope":[{"cohort":k[0],"scope":k[1],"review_mode":k[2],"count":v} for k,v in sorted(scope_counts.items())],
    "old_exposed_eligible":old_eligible,"old_exposed_eligible_still_reviewable":old_retained,"five_audit_mismatches_held":bad_held,"c1_critic_negative_routes":[{"old_route":k[0],"new_disposition":k[1],"count":v} for k,v in sorted(neg.items())]}
def execute(root,profile,profile_hash,out):
 root=root.resolve();out=out.resolve();require(not out.exists() and out.is_relative_to(root/"runs/B2/U3-B/C2/R1"),"NEW_R1_DIRECTORY")
 a=Inputs(root,profile,profile_hash).derive(utc());out.mkdir(parents=True);private=out/"controller_private";private.mkdir(mode=0o700);tree=private/"typed_partitions";tree.mkdir(mode=0o700)
 by=C.defaultdict(list)
 for o in a.records.values():
  rights=o["governance"]["rights_domains"];part=rights[0] if len(rights)==1 else "MIXED_RESTRICTED_"+digest(rights)[:16];by[part+"/"+o["kind"]+".jsonl"].append(o)
 m={}
 for rel,rr in sorted(by.items()):
  f=tree/rel;f.parent.mkdir(mode=0o700,parents=True,exist_ok=True);dump_lines(f,rr);os.chmod(f,0o600);m[rel]={"rows":len(rr),"sha256":sha(f),"bytes":f.stat().st_size}
 put(private/"partition_manifest.json",m);put(private/"InputFence.json",a.fences);put(out/"R1_Contract.schema.json",a.schema)
 report={"status":"PASS_BOUNDED_R1_EXECUTION / EXPERT_AND_RELEASE_HOLD","utc":a.clock,"profile_sha256":profile_hash,"policy_sha256":sha(root/a.p["policy"]),"typed_objects":len(a.records),"kind_counts":dict(C.Counter(o["kind"] for o in a.records.values())),"input_fences":len(a.fences),"rights_partitions":len({x.split("/")[0] for x in m}),"partition_manifest_sha256":sha(private/"partition_manifest.json"),"scope_and_risk":a.summarize(),"audit_findings_count":len(a.findings),"new_embedding_run":False,"scientific_release":False}
 put(out/"R1ExecutionReport.json",report);a.check_fences()
 receipt={"status":"R1_EXECUTION_FROZEN_AWAITING_VERIFIED_RUNTIME_REPLAY","profile_sha256":profile_hash,"report_sha256":sha(out/"R1ExecutionReport.json"),"schema_sha256":sha(out/"R1_Contract.schema.json"),"partition_manifest_sha256":report["partition_manifest_sha256"],"input_fence_sha256":sha(private/"InputFence.json"),"scientific_release":False}
 put(out/"R1ExecutionFreezeReceipt.json",receipt)
 print("R1_EXECUTION",json.dumps(report,ensure_ascii=False),flush=True);print("EXECUTION_RECEIPT_SHA",sha(out/"R1ExecutionFreezeReceipt.json"),flush=True)

class VerifiedGate:
 """Construct from immutable run + externally supplied controller trust hashes.
 Only actual persisted, exact-recomputed records can be requested. Never pass
 caller-created risk or query dictionaries into this consumer entry.
 """
 def __init__(self,root,profile,profile_hash,run,receipt_hash):
  self.root=root.resolve();run=run.resolve();require(run.is_relative_to(self.root/"runs/B2/U3-B/C2/R1"),"RUN_SCOPE")
  rec=run/"R1ExecutionFreezeReceipt.json";require(sha(rec)==receipt_hash,"UNTRUSTED_EXECUTION_RECEIPT")
  r=load(rec);require(r["profile_sha256"]==profile_hash and r["scientific_release"] is False,"RECEIPT_SCOPE")
  rpt=run/"R1ExecutionReport.json";require(sha(rpt)==r["report_sha256"],"REPORT_HASH");self.report=load(rpt)
  priv=run/"controller_private";mp=priv/"partition_manifest.json";require(sha(mp)==r["partition_manifest_sha256"] and sha(priv/"InputFence.json")==r["input_fence_sha256"] and sha(run/"R1_Contract.schema.json")==r["schema_sha256"],"RUN_HASH")
  a=Inputs(self.root,profile,profile_hash).derive(self.report["utc"]);self._a=a;require(load(priv/"InputFence.json")==a.fences,"FENCE_REPLAY")
  require(canon(load(run/"R1_Contract.schema.json"))==canon(a.schema),"SCHEMA_REPLAY")
  m=load(mp);tree=priv/"typed_partitions";require(set(m)=={str(x.relative_to(tree)) for x in tree.rglob("*.jsonl")},"RUN_PARTITION_SET")
  self._records={};self._selected=set()
  for rel,x in sorted(m.items()):
   p=(tree/rel).resolve();require(p.is_relative_to(tree.resolve()) and sha(p)==x["sha256"] and p.stat().st_size==x["bytes"],"RUN_PARTITION_HASH")
   n=0
   for o in lines(p):
    k=ref(o);require(k not in self._records and k in a.records,"RECORD_NOT_RECOMPUTED")
    a.verify_exact(o,a.records[k],a.registry)
    self._records[k]=o;n+=1
    if o["kind"]=="VerifiedQueryOverlay":self._selected.update(o["payload"]["shortlist_refs"])
   require(n==x["rows"],"RUN_PARTITION_COUNT")
  require(set(self._records)==set(a.records) and len(self._records)==self.report["typed_objects"] and a.summarize()==self.report["scope_and_risk"],"RUN_FULL_REPLAY")
  a.check_fences()
 def request(self,purpose,r):
  if purpose not in ("CURATION_INSPECT","DEVELOPMENT_CONCEPT_REVIEW"):return {"decision":"HOLD","reason":"PURPOSE_NOT_AUTHORIZED"}
  o=self._records.get(r)
  if not o or o["kind"]!="VerifiedRiskOverlay":return {"decision":"HOLD","reason":"UNVERIFIED_RISK_REF"}
  if purpose=="CURATION_INSPECT":return {"decision":"ALLOW","reason":"CURATION_ONLY"}
  if r in self._selected and o["payload"]["review_eligible"]:return {"decision":"ALLOW","reason":o["payload"]["disposition"]}
  return {"decision":"HOLD","reason":o["payload"]["disposition"] if not o["payload"]["review_eligible"] else "NOT_SHORTLISTED"}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=P.Path,default=P.Path("."));p.add_argument("--profile",type=P.Path,required=True);p.add_argument("--profile-sha",required=True);p.add_argument("--out",type=P.Path,required=True)
 x=p.parse_args();execute(x.root,x.profile.resolve(),x.profile_sha,x.out)
