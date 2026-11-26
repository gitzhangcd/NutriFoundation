#!/usr/bin/env python3
"""Frozen R2 development comparisons. Candidate questions never bypass R1 admission.
No new model call, no critic response read, no accepted alignment or expert Gold."""
import argparse,hashlib,json,pathlib as P,sys,re,unicodedata,os
from collections import Counter,defaultdict
from datetime import datetime,timezone
from jsonschema import Draft202012Validator
V="UDF-U3R2-DEV-CALIBRATION-0.1"
U3="runs/B2/U3-B"; C2=U3+"/C2"; R1=C2+"/R1"
SCOPES={"foodon:2026-09-20:food_product","fdc:sr_legacy:2018-04","fndds:2015-16:fdc_carrier"}
EXT="foodon:2026-09-20:typed_extension"
ARMS=("LABEL","CONTEXT","FUSION","TYPED_QUESTION")
KS=(1,3,5,12)
def require(x,c):
 if not x:raise ValueError(c)
def sha(p):
 h=hashlib.sha256()
 with P.Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def dg(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def read(p):return json.loads(P.Path(p).read_text(encoding="utf8"))
def lines(p):
 with P.Path(p).open(encoding="utf8") as f:
  for l in f:
   if l.strip():yield json.loads(l)
def put(p,x):
 with p.open("x",encoding="utf8") as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write("\n")
def putl(p,rs):
 with p.open("x",encoding="utf8") as f:
  for x in rs:f.write(canon(x)+"\n")
def ref(o):return o["object_id"]+"@"+o["revision_id"]
def verify_revision(o):
 x=dict(o);h=x.pop("revision_id");require(h==dg(x),"REVISION_HASH")
def norm(s):return re.sub(r"[\W_]+"," ",unicodedata.normalize("NFKC",str(s)).casefold()).strip()
def peel(label):
 s=unicodedata.normalize("NFKC",label).casefold()
 # Explicit current form. Negated removal is not peeled; source histories are
 # kept unresolved rather than promoted into current state.
 s=re.sub(r"\b(?:made\s+)?from\s+(?:peeled|unpeeled)\b"," ",s)
 u=bool(re.search(r"\b(?:unpeeled|not\s+peeled|with\s+skin|peel\s+eaten)\b",s)) or any(t in s for t in ("带皮","未去皮","不去皮"))
 clean=re.sub(r"\bnot\s+peeled\b"," ",s).replace("未去皮","").replace("不去皮","")
 p=bool(re.search(r"\b(?:peeled|skinless|peel\s+not\s+eaten)\b",clean)) or "去皮" in clean
 return "AMBIGUOUS" if p and u else "PEELED" if p else "UNPEELED" if u else "UNKNOWN"
def peel_conflict(a,b):return {peel(a),peel(b)}=={"PEELED","UNPEELED"}
def complete_alias(a,b,aliases):
 a,b=norm(a),norm(b)
 if a and a==b:return "COMPLETE_SURFACE"
 if any({a,b}=={norm(x),norm(y)} for x,y in aliases):
  return "AUTHORED_ALIAS_IMPLICIT_COOKING_REQUIRES_REVIEW" if any(norm(a)==norm(t) or norm(b)==norm(t) for t in ("米饭","炒饭")) else "AUTHORED_WHOLE_LABEL_PAIR"
 return "UNRESOLVED_LABEL_RESIDUAL"
def native_key(p):
 ns=p["native_namespace"]
 if ns=="fndds:2015-16:ars_carrier":ns="fndds:2015-16:fdc_carrier"
 return [ns,str(p["native_key"])]
def target_key_scope(k):
 if k[0].startswith("foodon:"):return ["FoodOn","2026-09-20",k[1]]
 if k[0]=="fdc:sr_legacy:2018-04":return ["FDC_SR_Legacy","2018-04",k[1]]
 if k[0]=="fndds:2015-16:fdc_carrier":return ["FNDDS","2015-16",k[1]]
 return None
def eligible_question(p,ss,peel_block,prior_red):
 # Only navigational hypothesis prioritization. This does not confer even
 # R1's development concept admission; arbitrary residuals remain unresolved.
 if peel_block or p["explicit_conflicts"] or prior_red:return "HOLD_EXPLICIT_OR_PRIOR_RED"
 if ss is not None and ss not in ("CORE_RETAINED_DEV","EXTENSION_TYPED_RETRIEVAL_ONLY","DUAL_ROLE_ORGANISM_REVIEW_ONLY"):
  return "HOLD_SCOPE"
 if p["role_policy_mode"]=="NOT_REGISTERED":return "HOLD_UNREGISTERED_ROLE"
 return "QUESTION_ONLY"
class Inputs:
 def __init__(self,root,profile,expected_hash):
  self.root=root.resolve();self.fences={};self.profile=self.pin(str(profile.resolve().relative_to(self.root)),expected_hash);self.p=read(profile)
  require(self.p["version"]==V and self.p["scientific_release_authorized"] is False,"PROFILE_RELEASE")
  for path,h in self.p["pins"].items():self.pin(path,h)
  self.aliases=read(self.root/"configs/udf/u3c2r/R1_Policy_v0.1.json")["whole_label_aliases"]
  self.audit=self.audit_verify()
  self.records={}
 def pin(self,rel,expected=None):
  q=self.root/rel;p=q.resolve();require(q.is_file() and not q.is_symlink() and p.is_relative_to(self.root),"INPUT_PATH")
  h=sha(p);require(expected is None or h==expected,"PIN_DRIFT:"+str(rel))
  k=str(p.relative_to(self.root));require(k not in self.fences or self.fences[k]==h,"REOPEN_DRIFT");self.fences[k]=h;return p
 def audit_verify(self):
  cp="configs/audit/tasks/B2_U3B_C2_R1_Recheck_Gemini_001.json";cfg=read(self.root/cp);d=self.root/cfg["output"]["directory"];r=read(d/"CriticFreezeReceipt.json")
  a={x["path"]:x["sha256"] for x in cfg["allowed_inputs"]};a[cp]=sha(self.root/cp);a[cfg["protocol"]]=sha(self.root/cfg["protocol"])
  for p,h in a.items():self.pin(p,h)
  require(set(r["output_file_hashes"])=={"ExecutionManifest.json","AuditFindings.jsonl","AuditReport.md"},"AUDIT_OUTPUT_SET")
  for k,h in r["output_file_hashes"].items():
   f=self.pin(str((d/k).relative_to(self.root)),h);require(f.stat().st_size==r["output_file_bytes"][k],"AUDIT_OUTPUT_SIZE")
  m=read(d/"ExecutionManifest.json");ff=list(lines(d/"AuditFindings.jsonl"))
  require(r["task_id"]==m["task_id"]==cfg["task_id"] and m["task_config_sha256"]==a[cp],"AUDIT_ID")
  require(m["verified_input_hashes"]==a and set(m["actual_accessed_paths"])==set(a),"AUDIT_ACCESS_DECLARATION")
  require(len(ff)==r["counts"]["findings_total"]==len({x["finding_id"] for x in ff}) and dict(Counter(x["severity"] for x in ff))==r["counts"]["findings_by_severity"],"AUDIT_COUNTS")
  require(all(r["governance_declarations"].values()) and r["qualification_decision"]=="HOLD","AUDIT_SCOPE")
  require(r["counts"]["prior_red_core_counterexamples_blocked"]==5 and not any(x["severity"]=="RED" for x in ff),"RED_RECHECK_BLOCK")
  return {"status":r["status"],"allowed_inputs":len(a)-2,"output_files":len(r["output_file_hashes"]),"findings":len(ff),"severity":dict(Counter(x["severity"] for x in ff)),"reproduction":dict(Counter(x["reproduction_status"] for x in ff)),"prior_red_counterexamples_blocked":5,"access_independently_proven":False}
 def partition(self,base,kind,priv="private"):
  path=self.root/base/priv;mp=path/"partition_manifest.json";m=read(self.pin(str(mp.relative_to(self.root))))
  for rel,x in sorted(m.items()):
   if not rel.endswith("/"+kind+".jsonl"):continue
   f=self.pin(str((path/"typed_partitions"/rel).relative_to(self.root)),x["sha256"]);require(f.stat().st_size==x["bytes"],"PARTITION_SIZE")
   n=0
   for o in lines(f):
    verify_revision(o);require(o["kind"]==kind and o["purpose"]=="CURATION_DEV" and o["governance"]["release_status"]=="HOLD","PARTITION_PURPOSE")
    yield o;n+=1
   require(n==x["rows"],"PARTITION_COUNT")
 def check(self):
  require(all(sha(self.root/k)==v for k,v in self.fences.items()),"INPUT_FENCE_MUTATED")
 def main(self):
  # Verify upstream generator and R1 execution receipts, not merely current report.
  fr=read(self.root/U3/"freeze_001/GeneratorFreezeReceipt.json")
  for k,h in fr["output_file_hashes"].items():self.pin(k,h)
  rr=read(self.root/R1/"real_001/R1ExecutionFreezeReceipt.json")
  for path,k in [(R1+"/real_001/R1ExecutionReport.json","report_sha256"),(R1+"/real_001/R1_Contract.schema.json","schema_sha256"),(R1+"/real_001/controller_private/partition_manifest.json","partition_manifest_sha256"),(R1+"/real_001/controller_private/InputFence.json","input_fence_sha256")]:self.pin(path,rr[k])
  require(rr["scientific_release"] is False and fr["mapping_release_authorized"] is False,"UPSTREAM_RELEASE")
  nat={};natref={}
  for o in self.partition("runs/B1/U2-C/real_001","NativeVocabularyRecord"):
   r=o["governance"]["legacy_ref"];require(r not in nat,"DUPLICATE_NATIVE");nat[r]=o;natref[ref(o)]=o
  require(len(nat)==65592,"NATIVE_COUNT")
  queries={}
  for o in self.partition(U3+"/real_001","QueryContextRecord"):
   p=o["payload"];r=p["source_legacy_ref"];require(r not in queries and ref(nat[r])==p["source_ref"] and nat[r]["payload"]["native_label"]==p["native_label"],"QUERY_IDENTITY");queries[r]=p
  require(len(queries)==284,"QUERY_COUNT")
  # Select by fixed source cohort, before reading any candidate/risk score.
  sourceq=read(self.root/U3/"real_001/private/ReviewSourceOnlyQueue.json")
  original=read(self.root/"runs/B2/U3-A/real_002/private/ReviewSourceOnlyQueue.json")+read(self.root/"runs/B2/U3-A/review_queue_audit_001/private/ReviewSourceOnlyRedSupplement.json")
  excl={x["source_ref"] for x in original+sourceq}
  require(len(sourceq)==44 and len(original)==44 and len(excl)==88,"ORIGINAL_QUEUE_CLOSURE")
  strata=defaultdict(list)
  for r,p in queries.items():
   if r not in excl:strata[(p["cohort"],p["source_scope"])].append(r)
  n=self.p["review_design"]["supplement_per_stratum"];salt=self.p["review_design"]["selection_salt"]
  sample=[];sampling=[]
  for k,rs in sorted(strata.items()):
   require(len(rs)>=n,"STRATUM_TOO_SMALL")
   ids=sorted(rs,key=lambda r:dg([salt,nat[r]["object_id"]]))[:n];sample+=ids
   sampling.append({"cohort":k[0],"source_scope":k[1],"eligible_source_count":len(rs),"selected_count":len(ids),"selection_fraction":len(ids)/len(rs)})
  require(len(sample)==len(set(sample))==32 and not set(sample)&excl,"SUPPLEMENT_ISOLATION")
  # Source-only projection from actual native data + frozen reference recipe context.
  def source_record(r,rid):
   o=nat[r];p=o["payload"];q=queries.get(r)
   require(p["artifact_sha256"] and p["source_anchor_ref"],"SOURCE_ANCHOR")
   return {"review_id":rid,"source_ref":r,"source_scope":p["native_namespace"],"source_native_label":p["native_label"],"native_kind":p["native_kind"],
    "source_locator":p["source_locator"],"artifact_sha256":p["artifact_sha256"],"source_anchor_ref":p["source_anchor_ref"],
    "native_aliases":p["native_aliases"],"reference_recipe_ingredient_names":q["native_ingredient_names"] if q else [],
    "context_locator":q["context_locator"] if q else None,"context_note":"Native reference recipe names are not verified physical composition; absent fields remain unknown.",
    "question":"Independently recover source meaning and actual supported standard targets; record direction and conditions or unresolved; never infer nutrient transfer.","status":"NOT_REVIEWED"}
  first=[]
  for x in sourceq:
   z=source_record(x["source_ref"],x["review_id"]);require(all(z[k]==x[k] for k in ("source_ref","source_scope","source_native_label","native_kind")),"OLD_SOURCE_PACKET_IDENTITY");first.append(z)
  second=[source_record(r,"R2-CAL-"+str(i+1).zfill(3)) for i,r in enumerate(sorted(sample,key=lambda r:dg([salt,"NEUTRAL_ORDER",r])))]
  require(len({x["review_id"] for x in first+second})==76,"PACKET_IDS")
  scope={};oldscope={}
  for o in self.partition(R1+"/real_001","VerifiedScopeOverlay","controller_private"):
   p=o["payload"];scope[ref(o)]=p;oldscope[p["prior_scope_ref"]]=p
  require(len(scope)==40107,"SCOPE_COUNT")
  prior={}
  for o in self.partition(U3+"/real_001","SemanticCandidateRecord"):
   prior[ref(o)]=o["payload"]
  require(len(prior)==29081,"GENERATOR_EDGE_COUNT")
  c2ext={}
  for o in self.partition(C2+"/real_001","SemanticRiskAssessment"):
   p=o["payload"]
   if p["cohort"]=="C2_EXTENSION_U3B_284":c2ext[ref(o)]=p
  require(len(c2ext)==5685,"EXTENSION_EDGE_COUNT")
  risks=[];groups=defaultdict(list);counts=Counter()
  for o in self.partition(R1+"/real_001","VerifiedRiskOverlay","controller_private"):
   p=o["payload"];co=p["cohort"]
   if co not in ("U3B_FROZEN_284","C2_EXTENSION_U3B_284"):continue
   sr=p["source_legacy_ref"];require(sr in queries and ref(nat[sr])==p["source_ref"],"RISK_SOURCE")
   s=nat[sr]["payload"];ss=scope[p["scope_ref"]]["scope_status"] if p["scope_ref"] else None
   if co=="U3B_FROZEN_284":
    pr=prior[p["prior_candidate_ref"]];t=nat[p["target_legacy_ref"]]
    require(pr["source_legacy_ref"]==sr and pr["target_legacy_ref"]==p["target_legacy_ref"] and ref(t)==p["target_ref"],"PRIOR_ENDPOINT")
    tp=t["payload"];tk=native_key(tp);label=tp["native_label"];tg=tp["native_kind"];oldred=pr["review_route"]=="RED"
    lr,cr,frank=pr["label_rank"],pr["context_rank"],pr["pool_rank"];fscore=pr["fusion_score"]
   else:
    pr=c2ext[p["prior_risk_ref"]];sp=scope[p["target_ref"]]
    require(pr["source_legacy_ref"]==sr and sp["scope_status"]=="EXTENSION_TYPED_RETRIEVAL_ONLY","EXTENSION_ENDPOINT")
    tk=[EXT,sp["iri"]];label=sp["native_label"];tg="ONTOLOGY_TYPED_EXTENSION_CATEGORY";oldred=False
    lr,cr=pr["extension_label_rank"],pr["extension_context_rank"];frank=None;fscore=(1/(60+lr) if lr else 0)+(1/(60+cr) if cr else 0)
   key=target_key_scope(tk);require(key is not None,"NATIVE_TARGET_KEY")
   pb=peel_conflict(s["native_label"],label);al=complete_alias(s["native_label"],label,self.aliases)
   route=eligible_question(p,ss,pb,oldred)
   needs=list(p["unresolved_conditions"])+list(p["role_conditions"])
   if al=="AUTHORED_ALIAS_IMPLICIT_COOKING_REQUIRES_REVIEW":needs.append("VERIFY_IMPLICIT_COOKING_STATE_FROM_SOURCE_EVIDENCE")
   if peel(s["native_label"])!=peel(label):needs.append("VERIFY_EDIBLE_PART_OR_PEEL_STATE")
   row={"proposal_id":"r2:"+dg([V,ref(o)])[:40],"r1_risk_ref":ref(o),"source_ref":p["source_ref"],"source_legacy_ref":sr,
    "target_ref":p["target_ref"],"target_key":key,"target_scope":p["target_scope"],"source_grain":s["native_kind"],"target_grain":tg,
    "label_rank":lr,"context_rank":cr,"frozen_pool_rank":frank,"fusion_score":fscore,
    "r1_review_eligible":p["review_eligible"],"r1_disposition":p["disposition"],"scope_status":ss,"prior_red":oldred,
    "explicit_conflicts":sorted(set(p["explicit_conflicts"]+(["EXPLICIT_PEELED_UNPEELED"] if pb else []))),
    "source_peel":peel(s["native_label"]),"target_peel":peel(label),"label_evidence":al,"condition_questions":sorted(set(needs)),
    "proposal_route":route,"candidate_relation":"UNRESOLVED","question_type":"ASSESS_DIRECTION_AND_CONDITIONS_OR_UNRESOLVED",
    "permitted_purpose":"CURATION_INSPECT_ONLY","development_concept_review_authorized":False,"accepted_equivalence":False,"measurement_transfer":"HOLD","mapping_release":"HOLD","rights_domains":o["governance"]["rights_domains"]}
   row["content_sha256"]=dg(row);risks.append(row);groups[(sr,p["target_scope"])].append(row);counts[(co,route)]+=1
  require(len(risks)==29081+5685 and len(groups)==284*4 and not any(x["r1_review_eligible"] for x in risks),"POOL_CLOSURE")
  ids={x["proposal_id"]:x for x in risks};require(len(ids)==len(risks),"PROPOSAL_ID_DUPLICATE")
  arms=[];stats=Counter();same_top=Counter()
  for (sr,ts),pool in sorted(groups.items()):
   require(len({tuple(x["target_key"]) for x in pool})==len(pool),"POOL_TARGET_DUPLICATE")
   label=sorted([x for x in pool if x["label_rank"]],key=lambda x:x["label_rank"])
   ctx=sorted([x for x in pool if x["context_rank"]],key=lambda x:x["context_rank"])
   fused=sorted(pool,key=lambda x:(x["frozen_pool_rank"] or 99999,-x["fusion_score"],x["proposal_id"]))
   # For extension no stored common rank: RRF ties use stable native target ID.
   if ts==EXT:fused=sorted(pool,key=lambda x:(-x["fusion_score"],x["target_key"]))
   k=12 if ts==EXT else 20
   require([x["label_rank"] for x in label]==list(range(1,k+1)) and [x["context_rank"] for x in ctx]==list(range(1,k+1)),"FROZEN_PER_FORM_TOPK")
   pos={x["proposal_id"]:i for i,x in enumerate(fused)}
   typed=sorted([x for x in fused if x["proposal_route"]=="QUESTION_ONLY"],key=lambda x:(x["label_evidence"]=="UNRESOLVED_LABEL_RESIDUAL",pos[x["proposal_id"]]))
   for a,rs in zip(ARMS,(label,ctx,fused,typed)):
    rank=[x["proposal_id"] for x in rs[:max(KS)]]
    z={"source_legacy_ref":sr,"target_scope":ts,"arm":a,"ranked_proposal_ids":rank,"pool_count":len(pool),"candidate_question_only":True,"mapping_release":"HOLD"}
    z["content_sha256"]=dg(z);arms.append(z)
    co=queries[sr]["cohort"];ns=queries[sr]["source_scope"]
    for kk in KS:
     pp=rs[:kk];stats[(co,ns,ts,a,kk,"groups")]+=1;stats[(co,ns,ts,a,kk,"proposal_edges")]+=len(pp);stats[(co,ns,ts,a,kk,"groups_with_proposal")]+=bool(pp)
     stats[(co,ns,ts,a,kk,"explicit_or_prior_red_edges")]+=sum(bool(x["explicit_conflicts"] or x["prior_red"]) for x in pp)
   same_top[("LABEL_CONTEXT","groups")]+=1;same_top[("LABEL_CONTEXT","same_top1")]+=label[0]["proposal_id"]==ctx[0]["proposal_id"]
  # Old-risk 25 cases use frozen old U2-C candidate refs, not current model results.
  hid=read(self.root/U3/"real_001/private/ReviewCandidatesHidden.json");hix={x["review_id"]:x for x in hid};require(set(hix)=={x["review_id"] for x in first},"REVIEW_PAIR_CLOSURE")
  needed={r for h in hid for r in h["u2c_prior_candidate_refs"]}
  old={}
  for o in self.partition("runs/B1/U2-C/real_001","AlignmentRecord"):
   if ref(o) not in needed:continue
   p=o["payload"];t=nat[p["target_ref"]]["payload"];old[ref(o)]={"source_legacy_ref":p["source_ref"],"target_key":target_key_scope(native_key(t)),"route":p["review_route"],"prior_ref":ref(o)}
  require(set(old)==needed,"OLD_RISK_EDGE_CLOSURE")
  armidx=defaultdict(list)
  for z in arms:armidx[z["source_legacy_ref"]].append(z)
  comp=[]
  for packet,tag in [(first,"ORIGINAL_NEW44"),(second,"RESERVED_STRATIFIED32")]:
   for x in packet:
    sr=x["source_ref"];h=hix.get(x["review_id"]);oset=[old[r] for r in h["u2c_prior_candidate_refs"]] if h else []
    require(all(z["source_legacy_ref"]==sr for z in oset),"OLD_PAIR_SOURCE")
    cmp={"review_id":x["review_id"],"source_ref":sr,"batch":tag,"current_model_query":sr in queries,
     "old_u2c_candidates":oset,"current_comparators":[{"target_scope":a["target_scope"],"arm":a["arm"],"ranked_targets":[ids[r]["target_key"] for r in a["ranked_proposal_ids"]]} for a in armidx[sr]],
     "source_cohort":queries[sr]["cohort"] if sr in queries else None,"status":"REFERENCE_NOT_AVAILABLE"}
    comp.append(cmp)
  require(sum(x["current_model_query"] for x in comp if x["batch"]=="ORIGINAL_NEW44")==19,"OLD_CURRENT_MODEL_OVERLAP")
  # Use raw target universe identities, not candidate ranks, for future absence attribution.
  universe={tuple(target_key_scope(native_key(o["payload"]))) for o in nat.values() if o["payload"]["native_namespace"] in SCOPES}
  ext_universe={("FoodOn","2026-09-20",p["iri"]) for p in scope.values() if p["scope_status"]=="EXTENSION_TYPED_RETRIEVAL_ONLY"}
  require(len(universe)==28845 and len(ext_universe)==1174,"TARGET_UNIVERSE")
  self.check()
  return {"first":first,"second":second,"sample":sampling,"risks":risks,"arms":arms,"comparators":comp,"universe":sorted(universe),"extension_universe":sorted(ext_universe),"counts":counts,"stats":stats,"top1":same_top}
def main(root,profile,ph,out):
 root=root.resolve();out=out.resolve();require(not out.exists() and out.is_relative_to(root/C2/"R2"),"NEW_RUN_DIRECTORY")
 a=Inputs(root,profile,ph);z=a.main();out.mkdir(parents=True)
 pub=out/"reviewer_source_only";pub.mkdir(mode=0o700);reserve=out/"reserved_source_only";reserve.mkdir(mode=0o700);priv=out/"controller_private";priv.mkdir(mode=0o700)
 put(pub/"R2Review44.json",z["first"]);put(reserve/"R2Calibration32.json",z["second"])
 # Preserve rights partitioning of candidate hypotheses. Only aggregate stats leave local.
 tree=priv/"proposal_partitions";tree.mkdir(mode=0o700);by=defaultdict(list);manifest={}
 for x in z["risks"]:
  rights=x["rights_domains"];d=rights[0] if len(rights)==1 else "MIXED_RESTRICTED_"+dg(rights)[:16];by[d].append(x)
 for d,rs in sorted(by.items()):
  f=tree/(d+".jsonl");putl(f,rs);os.chmod(f,0o600);manifest[d]={"file":str(f.relative_to(out)),"rows":len(rs),"sha256":sha(f)}
 put(priv/"ProposalManifest.json",manifest);putl(priv/"RankedArms.jsonl",z["arms"]);put(priv/"ControllerComparisonIndex.json",z["comparators"]);put(priv/"FrozenTargetUniverse.json",{"original":z["universe"],"extension":z["extension_universe"]})
 a.check();put(priv/"InputFence.json",a.fences)
 stats=[]
 for k in sorted({x[:-1] for x in z["stats"]}):
  stats.append({"cohort":k[0],"source_scope":k[1],"target_scope":k[2],"arm":k[3],"k":k[4],**{metric:z["stats"][k+(metric,)] for metric in ("groups","proposal_edges","groups_with_proposal","explicit_or_prior_red_edges")}})
 summary={"status":"PASS_R2_FROZEN_DEVELOPMENT_COMPARATORS / INDEPENDENT_REFERENCE_AND_SCIENTIFIC_RELEASE_HOLD","version":V,"utc":datetime.now(timezone.utc).isoformat(),"profile_sha256":ph,
  "audit":a.audit,"input_files":len(a.fences),"original_query_count":284,"original_pool_edges":29081,"extension_pool_edges":5685,"candidate_questions":len(z["risks"]),"ranked_arm_groups":len(z["arms"]),"original_target_universe":len(z["universe"]),"extension_target_universe":len(z["extension_universe"]),
  "risk_route_counts":[{"cohort":k[0],"route":k[1],"count":v} for k,v in sorted(z["counts"].items())],"peel_conflict_edges":sum("EXPLICIT_PEELED_UNPEELED" in x["explicit_conflicts"] for x in z["risks"]),
  "implicit_alias_edges":sum(x["label_evidence"]=="AUTHORED_ALIAS_IMPLICIT_COOKING_REQUIRES_REVIEW" for x in z["risks"]),
  "coverage_by_stratum":stats,"label_context_top1_same":z["top1"][("LABEL_CONTEXT","same_top1")],"label_context_groups":z["top1"][("LABEL_CONTEXT","groups")],
  "review":{"first_44":44,"first_current_model":19,"first_old_only":25,"reserved_32":32,"strata":z["sample"],"original_queue_overlap":0,"reviewer_results_read":0,"independent_reference_count":0,"actual_expert_count":0,"reserved_32_dispatch":"HOLD_UNTIL_FIRST_DEVELOPMENT_REVIEW_AND_METHOD_FREEZE"},
  "rights_partitions":len(manifest),"scientific_equivalence":0,"development_concept_review_authorizations":0,"mapping_release_count":0,"precision_recall":"NOT_ESTIMABLE",
  "limitations":["Question navigation does not relax R1 verified admission; no mapping is approved.","Same frozen candidate pools; no new model inference or calibrated threshold; label/context/fusion arms are raw comparators and may include conflict rows.","44 risk-enriched cases and 32 stratified supplement are separate development sets; source-only reference retrieval is incomplete, not formal Gold.","Current model questions and old risk-only reviews are not one comparative cohort.","No independent reference has been returned; no actual coverage of correct mappings measured."]}
 put(out/"R2ExecutionReport.json",summary)
 paths=[out/"R2ExecutionReport.json",pub/"R2Review44.json",reserve/"R2Calibration32.json",priv/"ProposalManifest.json",priv/"RankedArms.jsonl",priv/"ControllerComparisonIndex.json",priv/"FrozenTargetUniverse.json",priv/"InputFence.json"]
 put(out/"R2GeneratorFreezeReceipt.json",{"status":"GENERATOR_COMPARATORS_FROZEN / REFERENCE_HOLD","profile_sha256":ph,"files":{str(f.relative_to(out)):sha(f) for f in paths},"reviewer_has_not_received_hidden_comparators":True,"mapping_release_authorized":False})
 # Compact output only, no private source or target text.
 a.check();print(json.dumps({k:v for k,v in summary.items() if k!="coverage_by_stratum"},ensure_ascii=False),flush=True)
 print("R2_FREEZE_SHA",sha(out/"R2GeneratorFreezeReceipt.json"),flush=True)
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--root",type=P.Path,default=P.Path("."));a.add_argument("--profile",type=P.Path,required=True);a.add_argument("--profile-sha",required=True);a.add_argument("--out",type=P.Path,required=True);x=a.parse_args();main(x.root,x.profile.resolve(),x.profile_sha,x.out)
