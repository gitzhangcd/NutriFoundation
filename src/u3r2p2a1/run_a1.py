#!/usr/bin/env python3
"""A1: source-bound typed qualifier records and exact R1 policy re-evaluation.

Does not fabricate R1 VerifiedRiskOverlay records. Novel edges lack an original
VerifiedGate identity and remain HOLD, even if a policy-only check is eligible.
Generation never opens reserved32 review packets or outcomes.
"""
import argparse, json, sys, re, os
from collections import defaultdict, Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"u3c2r"))
sys.path.insert(0,str(HERE.parent/"u3r2p2"))
from risk_v2 import evaluate as r1_evaluate, features
from run_p2_portable_v2 import (read,lines,put,putl,sha,dg,require,query,set_lexicon,
    parse_standards,Standards,key,peel_conflict,BASE,SCOPES,EXT)
from run_r2 import ref,verify_revision,native_key,target_key_scope,peel
from conditional_p2_portable_v2 import assess
R1=Path("runs/B2/U3-B/C2/R1/real_001")
U2=Path("runs/B1/U2-C/real_001/private")
U3=Path("runs/B2/U3-B/real_001/private")
R2=BASE/"real_001";P2=BASE/"P2"
PARENT=P2/"portable_v2_001"
COND=P2/"portable_v2_conditional_001"
POLICY=Path("configs/udf/u3c2r/R1_Policy_v0.1.json")
PROFILE=Path("configs/udf/u3r2p2a1/A1_Profile_v0.1.json")
ANIMAL={"pork","pig","beef","cattle","veal","lamb","mutton","goat","chicken","turkey","duck","goose","tuna","mackerel","salmon","cod","shrimp","crab"}
ORGAN={"liver","kidney","heart","lung","tongue","brain","spleen","gizzard"}
def literal_en(label,terms):
 return [{"surface":m.group(),"start":m.start(),"end":m.end(),"value":m.group().casefold()} for m in re.finditer(r"\b(?:"+"|".join(sorted(map(re.escape,terms),key=lambda x:(-len(x),x)))+r")\b",label,re.I)]
def translated_spans(label,hypotheses,terms):
 out=[]
 for h in hypotheses:
  require(label[h["start"]:h["end"]]==h["source_span"],"TRANSLATION_SPAN_DRIFT")
  hits=literal_en(h["english_hypothesis"],terms)
  if hits:out.append({"source_span":h["source_span"],"start":h["start"],"end":h["end"],"english_hypothesis":h["english_hypothesis"],"candidate_mentions":[x["value"] for x in hits]})
 return out
def slot(value,status,basis):
 return {"value":value,"status":status,"basis":basis}
def typed(label,grain,anchor,*,q=None,native_state=None):
 f=features(label);ps=peel(label)
 if q is not None:
  species=translated_spans(label,q["label_hypotheses"],ANIMAL)
  organ=translated_spans(label,q["label_hypotheses"],ORGAN)
  evid="BILINGUAL_HYPOTHESIS_NOT_VERIFIED"
  comp=[x["source_ingredient"] for x in q["reference_recipe_components"]]
  recipe=slot(comp,"REFERENCE_RECIPE_NOT_PHYSICAL_COMPOSITION" if comp else "UNKNOWN",
    q["context_locator"] if comp else None)
  alias=slot(q["native_alias_raw"],"RAW_ALIAS_NOT_EQUIVALENCE" if q["native_alias_raw"] else "NOT_EXPRESSED",anchor)
  resid=slot(q["untranslated_label_residual"],"RESIDUAL_PRESERVED",anchor)
 else:
  species=literal_en(label,ANIMAL);organ=literal_en(label,ORGAN)
  evid="NATIVE_LABEL_MENTION_NOT_TAXONOMIC_IDENTITY"
  recipe=slot(None,"UNKNOWN",None);alias=slot(None,"NOT_EVALUATED_IN_TYPED_RECORD",None)
  resid=slot(label,"COMPLETE_NATIVE_LABEL_PRESERVED",anchor)
 return {"food_identity":slot(label,"NATIVE_LABEL_ONLY",anchor),
  "semantic_grain":slot(grain,"NATIVE_REGISTRY_ROLE",anchor),
  "species":slot(species,evid if species else "UNKNOWN",anchor),
  "edible_part":slot(organ,evid if organ else "UNKNOWN",anchor),
  "processing":slot(f["explicit_mentions"],"NATIVE_LABEL_MENTIONS" if f["explicit_mentions"] else "UNKNOWN",anchor),
  "cooking_state":slot(f["current_state"],"UNKNOWN" if f["current_state"]=="UNKNOWN" else "NATIVE_LABEL_STATE_ONLY",anchor),
  "native_state_metadata":slot(native_state,"AS_RECORDED_NOT_VALIDATED" if native_state is not None else "NOT_EXPRESSED",anchor),
  "source_origin":slot(f["origin_mentions"],"NATIVE_LABEL_MENTIONS" if f["origin_mentions"] else "UNKNOWN",anchor),
  "negations":slot(f["negative_mentions"],"NATIVE_LABEL_MENTIONS" if f["negative_mentions"] else "NOT_EXPRESSED",anchor),
  "peel_state":slot(ps,"UNKNOWN" if ps=="UNKNOWN" else "NATIVE_LABEL_STATE_ONLY",anchor),
  "form":slot(f["form_mentions"],"NATIVE_LABEL_MENTIONS" if f["form_mentions"] else "UNKNOWN",anchor),
  "recipe_components":recipe,"aliases":alias,"label_residual":resid,
  "unresolved_state_conditions":f["unresolved_state"],"verified_physical_identity":False,
  "verified_nutrient_transfer":False,"mapping_release":"HOLD"}
def check_source(s,packet,ctx,q):
 a=s["payload"]
 require(a["native_label"]==packet["source_native_label"]==ctx["native_label"]==q["source_label"],"SOURCE_LABEL_DRIFT")
 require(a["native_kind"]==packet["native_kind"]==ctx["source_grain"]==q["source_kind"],"SOURCE_ROLE_DRIFT")
 require(a["native_namespace"]==packet["source_scope"]==ctx["source_scope"],"SOURCE_NAMESPACE_DRIFT")
 require(a["artifact_sha256"]==packet["artifact_sha256"]==ctx["artifact_sha256"]==q["artifact_sha256"],"SOURCE_ARTIFACT_DRIFT")
 require(a["source_locator"]==packet["source_locator"]==ctx["source_locator"]==q["source_locator"],"SOURCE_LOCATOR_DRIFT")
 require(a["source_anchor_ref"]==packet["source_anchor_ref"]==ctx["source_anchor_ref"]==q["source_anchor_ref"],"SOURCE_ANCHOR_DRIFT")
 require(a["native_aliases"]==packet["native_aliases"],"SOURCE_ALIAS_DRIFT")
 require(ctx["native_ingredient_names"]==packet["reference_recipe_ingredient_names"]==[i["source_ingredient"] for i in q["reference_recipe_components"]],"RECIPE_CONTEXT_DRIFT")
 require(ctx["context_locator"]==packet["context_locator"]==q["context_locator"],"CONTEXT_LOCATOR_DRIFT")
 require(ctx["source_ref"]==ref(s) and ctx["source_legacy_ref"]==q["source_ref"],"SOURCE_REF_DRIFT")
 require(query(packet)==q,"FROZEN_QUERY_RECONSTRUCTION_DRIFT")
def admission(old,decision,flags):
 # R1 policy-only eligibility is distinct from verified runtime authorization.
 require(decision["mapping_release"]==decision["nutrient_transfer"]==decision["scientific_equivalence"]=="HOLD","R1_RELEASE")
 require(decision["relation"]=="UNRESOLVED","R1_RELATION")
 if decision["disposition"]=="BLOCK_EXPLICIT_CONFLICT":return "HOLD_R1_EXPLICIT_CONFLICT"
 if decision["disposition"]=="HOLD_SCOPE_OR_UNREGISTERED_ROLE":return "HOLD_R1_SCOPE_OR_ROLE"
 if flags:return "HOLD_TYPED_OR_INHERITED_RISK"
 if not decision["review_eligible"]:return "HOLD_R1_UNRESOLVED_CONDITIONS"
 return "HOLD_NEW_EDGE_RUNTIME_IDENTITY_REQUIRED" if old is None else "HOLD_ORIGINAL_RUNTIME_SHORTLIST_REQUIRED"
def navigation_priority(d):
 return 1 if d["disposition"] in ("HOLD_R1_EXPLICIT_CONFLICT","HOLD_R1_SCOPE_OR_ROLE","HOLD_TYPED_OR_INHERITED_RISK") else 0
class Inputs:
 def __init__(self,root,profile,ph):
  self.root=root;self.pins={}
  require(sha(profile)==ph,"PROFILE_HASH")
  self.pin(str(profile.relative_to(root)),ph);self.p=read(profile)
  require(self.p["scientific_release_authorized"] is False,"PROFILE_RELEASE")
  for p,h in self.p["pins"].items():self.pin(p,h)
  self.fr=read(root/PARENT/"CandidateFreeze.json")
  self.cr=read(root/COND/"ConditionalFreeze.json")
  self.parent=read(root/P2/"P2DevelopmentAdmissionReceipt.json")
  require(self.fr["private_hashes"]==self.parent["replay"]["private_artifact_hashes"],"PARENT_PRIVATE_IDENTITIES")
  require(self.fr["query_count"]==19 and not self.fr["mapping_release"] and not self.fr["reserved32_semantics_read"],"PARENT_SCOPE")
  require(self.cr["parent_freeze_sha256"]==sha(root/PARENT/"CandidateFreeze.json") and self.cr["reserved32_outcomes_read"]==0,"CONDITIONAL_PARENT")
  for p,h in self.fr["input_fences"].items():self.pin(p,h)
  for path,rc in ((PARENT,self.fr),(COND,self.cr)):
   for p,h in rc["private_hashes"].items():self.pin(str(path/"private"/p),h)
  rec=read(root/R1/"R1ExecutionFreezeReceipt.json")
  for rel,k in [("R1ExecutionReport.json","report_sha256"),("R1_Contract.schema.json","schema_sha256"),("controller_private/partition_manifest.json","partition_manifest_sha256"),("controller_private/InputFence.json","input_fence_sha256")]:self.pin(str(R1/rel),rec[k])
  require(rec["scientific_release"] is False,"R1_RELEASE")
  for p,h in read(root/R1/"controller_private/InputFence.json").items():self.pin(p,h)
  self.policy=read(root/POLICY)
  set_lexicon(read(root/P2/"private/DevelopmentLexicon_v0.1.json"))
 def pin(self,rel,h):
  p=self.root/rel
  require(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(self.root),"UNSAFE_PATH")
  require(self.pins.get(rel,h)==h,"PIN_DISAGREEMENT")
  if rel not in self.pins:require(sha(p)==h,"PIN_DRIFT:"+rel);self.pins[rel]=h
  return p
 def partition(self,base,kind):
  rel=str(base/"partition_manifest.json");require(rel in self.pins,"MANIFEST_NOT_TRUSTED")
  m=read(self.root/rel)
  for k,v in sorted(m.items()):
   if not k.endswith("/"+kind+".jsonl"):continue
   f=self.pin(str(base/"typed_partitions"/k),v["sha256"]);n=0
   require(f.stat().st_size==v["bytes"],"PARTITION_SIZE")
   for x in lines(f):
    verify_revision(x);require(x["kind"]==kind and x["purpose"]=="CURATION_DEV" and x["governance"]["release_status"]=="HOLD","PARTITION_SCOPE");n+=1;yield x
   require(n==v["rows"],"PARTITION_COUNT")
 def check(self):
  require(all(sha(self.root/p)==h for p,h in self.pins.items()),"INPUT_MUTATION")
def derive(root,profile,ph):
 a=Inputs(root,profile,ph);qs={x["review_id"]:x for x in lines(root/PARENT/"private/QueryHypotheses.jsonl")}
 require(len(qs)==19 and len({q["source_ref"] for q in qs.values()})==19,"DEV19")
 refs={q["source_ref"] for q in qs.values()}
 packet={x["review_id"]:x for x in read(root/R2/"reviewer_source_only/R2Review44.json") if x["review_id"] in qs}
 require(set(packet)==set(qs),"DEV_PACKET")
 cs=defaultdict(list)
 for c in lines(root/PARENT/"private/CandidateQuestions.jsonl"):
  require(c["review_id"] in qs and c["query_digest"]==dg(qs[c["review_id"]]),"CANDIDATE_QUERY_BINDING")
  require(c["mapping_release"]==c["measurement_transfer"]=="HOLD" and not c["accepted_equivalence"] and not c["development_concept_review_authorized"],"CANDIDATE_RELEASE")
  cs[(c["review_id"],tuple(c["target_key"]))].append(c)
 require(len(cs)==4500 and sum(map(len,cs.values()))==7007,"CANDIDATE_COUNT")
 targets={k for _,k in cs}
 un=read(root/R2/"controller_private/FrozenTargetUniverse.json");original={tuple(k) for k in un["original"]};extension={tuple(k) for k in un["extension"]}
 require(len(original)==28845 and len(extension)==1174 and not original&extension and targets<=original|extension,"FROZEN_UNIVERSE")
 # Read frozen registry; project only 19 sources and selected native targets.
 sources={};native={};legacy_targets={}
 for x in a.partition(U2,"NativeVocabularyRecord"):
  l=x["governance"]["legacy_ref"];p=x["payload"]
  if l in refs:require(l not in sources,"SOURCE_DUPLICATE");sources[l]=x
  if p["native_namespace"] in SCOPES:
   k=tuple(target_key_scope(native_key(p)))
   if k in targets:require(k not in native,"TARGET_DUPLICATE");native[k]=x;legacy_targets[l]=k
 require(set(sources)==refs and set(native)==targets&original,"NATIVE_ENDPOINTS")
 ctx={}
 for x in a.partition(U3,"QueryContextRecord"):
  p=x["payload"];l=p["source_legacy_ref"]
  if l in refs:require(l not in ctx,"CONTEXT_DUPLICATE");ctx[l]=p
 require(set(ctx)==refs,"CONTEXT_CLOSURE")
 source_records={};qbyref={q["source_ref"]:q for q in qs.values()}
 for rid,q in qs.items():
  s=sources[q["source_ref"]];check_source(s,packet[rid],ctx[q["source_ref"]],q)
  p=s["payload"];anchor={"native_ref":ref(s),"artifact_sha256":p["artifact_sha256"],"locator":p["source_locator"],"source_anchor_ref":p["source_anchor_ref"]}
  source_records[rid]={"review_id":rid,"source_ref":q["source_ref"],"qualifiers":typed(p["native_label"],p["native_kind"],anchor,q=q,native_state=p["metadata"].get("food_state")),"rights_domains":s["governance"]["rights_domains"]}
 # Full R1 original scope is independently replayed by inherited verifier;
 # use pinned immutable overlays, exact native ref and raw standard label below.
 scope_ref={};scope_iri={}
 for x in a.partition(R1/"controller_private","VerifiedScopeOverlay"):
  p=x["payload"];require(p["iri"] not in scope_iri,"SCOPE_DUPLICATE");scope_ref[ref(x)]=x;scope_iri[p["iri"]]=x
 require(len(scope_iri)==40107,"SCOPE_COUNT")
 old={}
 for x in a.partition(R1/"controller_private","VerifiedRiskOverlay"):
  p=x["payload"];l=p["source_legacy_ref"]
  if l not in refs or p["cohort"] not in ("U3B_FROZEN_284","C2_EXTENSION_U3B_284"):continue
  if p["target_legacy_ref"]:k=legacy_targets.get(p["target_legacy_ref"])
  else:
   sc=scope_ref[p["scope_ref"]]["payload"];k=("FoodOn","2026-09-20",sc["iri"])
  if k not in targets:continue
  rid=qbyref[l]["review_id"];z=(rid,k)
  if z not in cs:continue
  require(z not in old and p["source_ref"]==ref(sources[l]),"OLD_R1_IDENTITY")
  old[z]=x
 vocab,_=parse_standards(Standards(root))
 target_records={}
 for k in sorted(targets):
  v=vocab[key(k[0],k[2])];require(not v["deprecated"],"DEPRECATED_TARGET")
  so=scope_iri[k[2]] if k[0]=="FoodOn" else None
  if k in original:
   n=native[k];p=n["payload"];label=p["native_label"];grain=p["native_kind"];targetref=ref(n)
   anchor={"native_ref":targetref,"artifact_sha256":p["artifact_sha256"],"locator":p["source_locator"],"raw_standard_locator":v["locator"],"source_anchor_ref":p["source_anchor_ref"]}
   rights=n["governance"]["rights_domains"]
  else:
   require(so is not None and so["payload"]["scope_status"]=="EXTENSION_TYPED_RETRIEVAL_ONLY","EXTENSION_SCOPE")
   label=so["payload"]["native_label"];grain="ONTOLOGY_TYPED_EXTENSION_CATEGORY";targetref=ref(so)
   anchor={"scope_ref":targetref,"artifact_sha256":so["payload"]["snapshot_sha256"],"raw_standard_locator":v["locator"]}
   rights=so["governance"]["rights_domains"]
  require(label.strip()==v["label"].strip(),"NATIVE_RAW_LABEL_DRIFT")
  if so:require(so["payload"]["native_label"].strip()==label.strip(),"SCOPE_LABEL_DRIFT")
  target_records[k]={"target_key":list(k),"target_ref":targetref,"target_scope_ref":ref(so) if so else None,
    "scope_status":so["payload"]["scope_status"] if so else None,"native_label":label,"native_kind":grain,"raw_standard_label":v["label"],"raw_standard_locator":v["locator"],
    "qualifiers":typed(label,grain,anchor),"rights_domains":rights}
 risk=[];prior_verified=0
 for (rid,k),rr in sorted(cs.items()):
  q=qs[rid];s=sources[q["source_ref"]];t=target_records[k];o=old.get((rid,k));z=o["payload"] if o else None
  require(all(c["target_locator"]==t["raw_standard_locator"] and c["target_native_label"]==t["raw_standard_label"] for c in rr),"CANDIDATE_TARGET_ANCHOR")
  is_new=o is None
  require(all((c["route"]=="HOLD_NEW_EDGE_R1_NOT_RUN")==is_new for c in rr),"PRIOR_MEMBERSHIP_DRIFT")
  prior_red=bool(z and "UPSTREAM_RED_REQUIRES_REVIEW_NEVER_AUTO_CLEAR" in z["unresolved_conditions"])
  d=r1_evaluate({"label":s["payload"]["native_label"],"grain":s["payload"]["native_kind"]},{"label":t["native_label"],"grain":t["native_kind"]},a.policy,t["scope_status"],prior_red)
  if z:
   require(z["target_ref"]==t["target_ref"] and z["scope_ref"]==t["target_scope_ref"] and all(z[x]==y for x,y in d.items()),"OLD_R1_REEVALUATION_DRIFT");prior_verified+=1
  # Hypothesis-only checks cannot upgrade native authority or R1 policy.
  fl=assess(q,rr[0])
  flags=fl["potential_conflict_flags"]
  result={"review_id":rid,"target_key":list(k),"source_ref":ref(s),"target_ref":t["target_ref"],"target_scope_ref":t["target_scope_ref"],
   "source_qualifier_digest":dg(source_records[rid]),"target_qualifier_digest":dg(t),"prior_verified_r1_ref":ref(o) if o else None,
   "edge_kind":"NEW_EDGE" if is_new else "PRIOR_R1_EDGE","prior_red":prior_red,
   "r1_policy_evaluation":d,"typed_potential_conflicts":flags,"typed_questions":fl["condition_questions"],
   "question_family":fl["question_family"],"disposition":admission(o,d,flags),"r1_runtime_concept_review_authorized":False,
   "accepted_equivalence":False,"candidate_relation":"UNRESOLVED","mapping_release":"HOLD","nutrient_transfer":"HOLD",
   "rights_domains":sorted(set(source_records[rid]["rights_domains"]+t["rights_domains"]))}
  result["record_sha256"]=dg(result);risk.append(result)
 require(prior_verified==2427 and len(risk)-prior_verified==2073,"NEW_EDGE_CLOSURE")
 idx={(r["review_id"],tuple(r["target_key"])):r for r in risk}
 ranks=[]
 for r in lines(root/PARENT/"private/Ranks.jsonl"):
  require(r["review_id"] in qs,"RANK_CASE")
  orig=r["targets"];require(len(orig)<=r["pool_budget"] and len(set(map(tuple,orig)))==len(orig),"RANK_BUDGET")
  if r["arm"] not in ("SOURCE_SPARSE","HYBRID"):continue
  # Stable partition, same membership and same cap; explicit/typed risk goes to tail.
  order=sorted(orig,key=lambda k:navigation_priority(idx[(r["review_id"],tuple(k))]))
  require(set(map(tuple,orig))==set(map(tuple,order)),"RANK_MEMBERSHIP")
  ranks.append({**r,"arm":r["arm"]+"_A1_RISK_TAIL","targets":order})
 require(len(ranks)==152,"RANK_GROUP_COUNT")
 a.check()
 return a,source_records,target_records,risk,ranks
def generate(root,profile,ph,out):
 require(not out.exists() and out.is_relative_to(root/P2/"A1"),"NEW_A1_DIRECTORY")
 a,s,t,r,rr=derive(root,profile,ph)
 out.mkdir(parents=True,mode=0o700);p=out/"private";p.mkdir(mode=0o700)
 putl(p/"SourceQualifiers.jsonl",[s[k] for k in sorted(s)]);putl(p/"TargetQualifiers.jsonl",[t[k] for k in sorted(t)])
 putl(p/"NewEdgeRiskRecords.jsonl",r);putl(p/"RiskTailRanks.jsonl",rr)
 for f in p.iterdir():os.chmod(f,0o600)
 f={"profile_sha256":ph,"method_sha256":sha(Path(__file__)),"input_fences":a.pins,"private_hashes":{x.name:sha(x) for x in p.iterdir()},
 "sources":len(s),"distinct_targets":len(t),"distinct_edges":len(r),"prior_edges":2427,"new_edges":2073,"reserved32_review_packet_or_outcomes_parsed":False,
 "scientific_release":False,"runtime_admission":"HOLD"}
 put(out/"A1FreezeReceipt.json",f);print("A1_GENERATED",len(s),len(t),len(r),sha(out/"A1FreezeReceipt.json"))
def compare(root,out,freeze_sha):
 f=read(out/"A1FreezeReceipt.json")
 require(sha(out/"A1FreezeReceipt.json")==freeze_sha and f["method_sha256"]==sha(Path(__file__)),"A1_TRUST_ANCHOR")
 require(all(sha(root/p)==h for p,h in f["input_fences"].items()),"INPUT_DRIFT")
 require(all(sha(out/"private"/p)==h for p,h in f["private_hashes"].items()),"PRIVATE_DRIFT")
 risks=list(lines(out/"private/NewEdgeRiskRecords.jsonl"));idx={(r["review_id"],tuple(r["target_key"])):r for r in risks}
 require(len(idx)==len(risks)==4500,"RISK_IDENTITY")
 for r in risks:
  z=dict(r);h=z.pop("record_sha256");require(dg(z)==h and not r["r1_runtime_concept_review_authorized"] and not r["accepted_equivalence"] and r["mapping_release"]==r["nutrient_transfer"]=="HOLD","RISK_RELEASE_OR_HASH")
 ids={r["review_id"] for r in risks}
 pos=defaultdict(set);neg=defaultdict(set)
 # Only exposed first19 reference outcomes, after candidates frozen.
 for r in lines(root/BASE/"P1/real_001/private/ReferenceGapAttribution.jsonl"):
  if r["review_id"] in ids and r["domain"]=="ORIGINAL":pos[r["review_id"]].add(tuple(r["target_key"]))
 cfg=read(root/"configs/audit/tasks/B2_U3R2_REF44_Gemini_001.json")
 for r in lines(root/cfg["output"]["directory"]/"ReviewRecords.jsonl"):
  if r["review_id"] in ids:neg[r["review_id"]]={tuple(c["target_key"]) for c in r["hard_negatives"]}
 require(len(ids)==19 and len(pos)==18 and sum(map(len,pos.values()))==43,"REFERENCE_DENOMINATOR")
 def summary(rs):
  return {"edges":len(rs),"r1_policy_dispositions":dict(Counter(r["r1_policy_evaluation"]["disposition"] for r in rs)),
   "r1_policy_review_eligible":sum(r["r1_policy_evaluation"]["review_eligible"] for r in rs),
   "runtime_review_authorized":sum(r["r1_runtime_concept_review_authorized"] for r in rs),
   "final_dispositions":dict(Counter(r["disposition"] for r in rs)),
   "typed_flagged":sum(bool(r["typed_potential_conflicts"]) for r in rs),
   "critic_positive":sum(tuple(r["target_key"]) in pos[r["review_id"]] for r in rs),
   "critic_negative":sum(tuple(r["target_key"]) in neg[r["review_id"]] for r in rs),
   "risk_tail_critic_positive":sum(navigation_priority(r)==1 and tuple(r["target_key"]) in pos[r["review_id"]] for r in rs),
   "risk_tail_critic_negative":sum(navigation_priority(r)==1 and tuple(r["target_key"]) in neg[r["review_id"]] for r in rs)}
 ranks=list(lines(root/PARENT/"private/Ranks.jsonl"))+list(lines(root/COND/"private/Ranks.jsonl"))+list(lines(out/"private/RiskTailRanks.jsonl"))
 metrics=[]
 for arm in sorted({r["arm"] for r in ranks}):
  for k in [1,3,5,12,"POOL"]:
   cc=defaultdict(set)
   for r in ranks:
    if r["arm"]==arm and r["scope"]!="FOODON_EXTENSION":
     cc[r["review_id"]].update(tuple(t) for t in (r["targets"] if k=="POOL" else r["targets"][:k]))
   require(set(cc)==ids,"RANK_CASE_CLOSURE")
   metrics.append({"arm":arm,"k_per_scope":k,"reference_cases":18,"reference_edges":43,
    "reference_hit_cases":sum(bool(cc[i]&pos[i]) for i in ids),"reference_edges_hit":sum(len(cc[i]&pos[i]) for i in ids),
    "candidate_edges":sum(map(len,cc.values())),"critic_negative_overlap":sum(len(cc[i]&neg[i]) for i in ids),
    "unjudged":sum(len(cc[i]-pos[i]-neg[i]) for i in ids),
    "risk_tail_edges":sum(navigation_priority(idx[(i,t)]) for i in ids for t in cc[i])})
 sr=list(lines(out/"private/SourceQualifiers.jsonl"));tr=list(lines(out/"private/TargetQualifiers.jsonl"))
 z={"status":"PASS_BOUNDED_TYPED_QUALIFIER_AND_R1_POLICY_REEVALUATION / SCIENTIFIC_AND_NEW_RUNTIME_ADMISSION_HOLD",
  "sources":len(sr),"distinct_targets":len(tr),"all":summary(risks),"new":summary([r for r in risks if r["edge_kind"]=="NEW_EDGE"]),
  "prior":summary([r for r in risks if r["edge_kind"]=="PRIOR_R1_EDGE"]),
  "source_dimension_status":{k:dict(Counter(s["qualifiers"][k]["status"] for s in sr)) for k in ("species","edible_part","processing","cooking_state","recipe_components","native_state_metadata")},
  "metrics":metrics,"reserved32_outcomes_read":0,"expert_gold":0,"mapping_releases":0,
  "limitations":["R1 policy invoked unchanged; new edge cannot use original VerifiedGate without separate persisted runtime identity and shortlist contract.","Typed fields preserve literal mentions or translation hypotheses, not verified taxonomic or physical facts.","Reference overlap only; critic is incomplete and exposed; no scientific recall/precision.","Risk-tail order changes navigation only; all edges remain non-admitted."]}
 put(out/"A1DevelopmentReport.json",z)
 print(json.dumps({k:v for k,v in z.items() if k!="metrics"},ensure_ascii=False))
 print("METRICS",json.dumps([m for m in metrics if m["k_per_scope"] in (1,12,"POOL")],ensure_ascii=False))
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("phase",choices=["generate","compare"]);ap.add_argument("--root",type=Path,default=Path("."));ap.add_argument("--profile",type=Path,default=PROFILE);ap.add_argument("--profile-sha");ap.add_argument("--freeze-sha");ap.add_argument("--out",type=Path,required=True);x=ap.parse_args()
 if x.phase=="generate":require(x.profile_sha,"PROFILE_SHA_REQUIRED");generate(x.root.resolve(),x.profile.resolve(),x.profile_sha,x.out.resolve())
 else:require(x.freeze_sha,"FREEZE_SHA_REQUIRED");compare(x.root.resolve(),x.out.resolve(),x.freeze_sha)
