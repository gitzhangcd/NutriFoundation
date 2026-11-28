#!/usr/bin/env python3
"""A2 controller-only preparation and pre-reference retrieval freeze.
Local restricted CURATION_DEV; no external reviewer dispatch or outcome access.
Reuses the exact A1 runner, lexicon, target universe and scoring method.
"""
import argparse,sys,os,json,shutil,subprocess
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"u3r2p2a1"))
sys.path.insert(0,str(HERE.parent/"b0"))
from source_only_retrieval import check_packet, trusted, STANDARDS, SOURCE_FIELDS, SCOPES
from run_p2_portable_v2 import read,lines,put,putl,sha,dg,require,EXT
from run_r2 import ref,verify_revision
B=Path("runs/B2/U3-B/C2/R2");R=B/"real_001";A=B/"P2/A2";A1=B/"P2/A1"
POL=Path("configs/udf/u3r2p2a1/RetrievalPolicyFreeze_v0.1.json")
POL_SHA="58c53ab63cf4ac25d030d78e03dcdded8a51fb5a5802e7623ee75bd93af5ddc6"
A1_AD=A1/"A1AdmissionReceipt.json";A1_AD_SHA="dacb48d6f2b13354f7b936d4df8bcc9438f64d6db39227bbe94c105a6a5a99da"
A1_FR=A1/"dev_001/A1FreezeReceipt.json";A1_FR_SHA="ff1ca4b3f86c2cecaff738fc57776bc12ca059b620016642cfd788a22f8ca1f6"
R2_FR=R/"R2GeneratorFreezeReceipt.json";R2_FR_SHA="6b2afe8524c50edc9bb861141fbe720302aa92e466f0c3604695b52334666901"
SRC=R/"reserved_source_only/R2Calibration32.json";SRC_SHA="c8a65e45fe8ae4b2435ff5296889441fbe56f672ea1890a611f9d2057eae6a4a"
U2=Path("runs/B1/U2-C/real_001/private");U3=Path("runs/B2/U3-B/real_001/private")
MAN=Path("runs/B0/U1-A/NutriData_real_001/private/NativeFileManifest.json")
SCHEMA=Path("schemas/udf/u3r2/R2ReferenceReview_v0.1.schema.json")
OLD_TASK=Path("configs/audit/tasks/B2_U3R2_REF44_Gemini_001.json")
RUNNER=Path("src/u3r2p2a1/source_only_retrieval.py")
PROTOCOL=Path("configs/audit/IndependentAuditProtocol_v0.1.md")
class Fence:
 def __init__(self,root):self.root=root;self.pins={}
 def pin(self,rel,h):
  rel=str(rel);require(self.pins.get(rel,h)==h,"PIN_CONFLICT")
  p=trusted(self.root,Path(rel),h);self.pins[rel]=h;return p
 def check(self):
  for rel,h in self.pins.items():trusted(self.root,Path(rel),h)
 def partition(self,base,kind):
  mp=str(base/"partition_manifest.json");require(mp in self.pins,"UNTRUSTED_MANIFEST")
  for k,v in sorted(read(self.root/mp).items()):
   if not k.endswith("/"+kind+".jsonl"):continue
   p=self.pin(base/"typed_partitions"/k,v["sha256"])
   require(p.stat().st_size==v["bytes"],"PARTITION_BYTES");n=0
   for o in lines(p):
    n+=1;verify_revision(o)
    require(o["kind"]==kind and o["purpose"]=="CURATION_DEV" and o["governance"]["release_status"]=="HOLD","PARTITION_SCOPE")
    yield o
   require(n==v["rows"],"PARTITION_COUNT")
def check_sources(src,first):
 require(len(src)==32 and len({x["review_id"] for x in src})==len({x["source_ref"] for x in src})==32,"RESERVED_CASE_CLOSURE")
 require(not {x["source_ref"] for x in src}&{x["source_ref"] for x in first},"DEVELOPMENT_SOURCE_OVERLAP")
 require(not {x["review_id"] for x in src}&{x["review_id"] for x in first},"DEVELOPMENT_ID_OVERLAP")
 require(all(set(x)==SOURCE_FIELDS and x["status"]=="NOT_REVIEWED" for x in src),"SOURCE_SCHEMA")
 require(Counter(x["source_scope"] for x in src)=={"nutridata:ingredient":16,"nutridata:dish":16},"SOURCE_STRATA")
def raw_check(p,ss,ns,source_objects):
 # Raw workbook parsing is local-only; synthetic validation must not import it.
 from profile_nutridata_core_links import read_core
 wanted={x["source_locator"]["excel_row"]:x for x in ss};require(len(wanted)==len(ss),"SOURCE_ROW_DUP")
 seen=set()
 for rn,row,j,_ in read_core(p):
  if rn not in wanted:continue
  s=wanted[rn];n=source_objects[s["source_ref"]]["payload"];c=s["context_locator"]
  require(str(row["item_id"])==str(n["native_key"]) and str(j["name"])==s["source_native_label"],"RAW_SOURCE_ID_LABEL")
  al=[j["alias"]] if isinstance(j.get("alias"),str) and j["alias"].strip() else []
  require(al==[x["text"] for x in s["native_aliases"]],"RAW_ALIAS_DRIFT")
  require(c["excel_row"]==rn and c["quantity_not_used"] is True,"RAW_CONTEXT_LOCATOR")
  names=[x["name"] for x in j.get("major",[])[:c["ingredient_limit"]] if isinstance(x.get("name"),str) and x["name"].strip()] if ns.endswith(":dish") else []
  require(names==s["reference_recipe_ingredient_names"],"RAW_RECIPE_DRIFT");seen.add(rn)
 require(seen==set(wanted),"RAW_ROW_MISSING")
def copy_pinned(src,dst,h):
 require(not dst.exists() and not src.is_symlink() and sha(src)==h,"COPY_SOURCE_OR_DEST")
 dst.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 with src.open("rb") as i,dst.open("xb") as o:shutil.copyfileobj(i,o)
 os.chmod(dst,0o600);require(sha(dst)==h,"COPY_DRIFT")
def prepare(root,out):
 require(not out.exists() and out.is_relative_to(root/A),"NEW_A2_DIR")
 f=Fence(root);pol=read(f.pin(POL,POL_SHA))
 require(pol["status"]=="FROZEN_BOUNDED_RETRIEVAL_EXPERIMENT_ONLY" and pol["primary_arm"]=="SOURCE_SPARSE" and pol["comparators"]==["BASELINE_FUSION","HYBRID"] and pol["scientific_release_authorized"] is False and pol["reserved32_dispatch_authorized"] is False,"POLICY_SCOPE")
 for p,h in pol["pins"].items():f.pin(p,h)
 ad=read(f.pin(A1_AD,A1_AD_SHA));af=read(f.pin(A1_FR,A1_FR_SHA))
 require(ad["retrieval_experiment_policy_frozen"] and not ad["method_final_scientific_freeze"] and ad["reserved32_outcomes_read"]==0,"A1_SCOPE")
 for p,h in af["input_fences"].items():f.pin(p,h)
 g=read(f.pin(R2_FR,R2_FR_SHA));require(not g["mapping_release_authorized"],"R2_RELEASE")
 for p,h in g["files"].items():f.pin(R/p,h)
 src=read(f.pin(SRC,SRC_SHA));first=read(root/R/"reviewer_source_only/R2Review44.json");check_sources(src,first)
 ids={x["source_ref"] for x in src};rid={x["source_ref"]:x["review_id"] for x in src}
 # Read registry rows locally; never emit case names/IDs or reviewer outcomes.
 f.pin(U2/"partition_manifest.json","305341af924c55d6945ac7bd8aeecf7043137756f5bd128761122ce0dc06bbb3")
 f.pin(U3/"partition_manifest.json","2c2f27f1a505539bf97457c9472e027714ef39bcc874390ae96fb031616ec96c")
 native={};ctx={}
 for x in f.partition(U2,"NativeVocabularyRecord"):
  l=x["governance"]["legacy_ref"]
  if l in ids:require(l not in native,"NATIVE_DUP");native[l]=x
 for x in f.partition(U3,"QueryContextRecord"):
  p=x["payload"];l=p["source_legacy_ref"]
  if l in ids:require(l not in ctx,"CONTEXT_DUP");ctx[l]=p
 require(set(native)==set(ctx)==ids,"SOURCE_REGISTRY_CLOSURE")
 strata=Counter();rights=Counter()
 for s in src:
  n=native[s["source_ref"]];p=n["payload"];q=ctx[s["source_ref"]]
  require(p["native_label"]==q["native_label"]==s["source_native_label"] and p["native_kind"]==q["source_grain"]==s["native_kind"] and p["native_namespace"]==q["source_scope"]==s["source_scope"],"SOURCE_NATIVE_ID")
  for k in ("artifact_sha256","source_locator","source_anchor_ref"):require(p[k]==q[k]==s[k],"SOURCE_ANCHOR")
  require(q["source_ref"]==ref(n) and p["native_aliases"]==s["native_aliases"] and q["native_ingredient_names"]==s["reference_recipe_ingredient_names"] and q["context_locator"]==s["context_locator"],"SOURCE_CONTEXT")
  strata[(q["cohort"],q["source_scope"])]+=1
  rights.update(n["governance"]["rights_domains"])
 require(len(strata)==4 and set(strata.values())=={8},"STRATIFIED_SAMPLE")
 require(rights=={"NUTRIDATA_RIGHTS_UNRESOLVED":32},"RIGHTS_PROFILE_CHANGED_REVIEW_REQUIRED")
 # Reopen actual underlying raw workbooks and check source rows/context names.
 mf=read(f.pin(MAN,"7c7edd6944fb746d630a6e4155b0cca1de520f5c2c4a8fcb56b1632f287aff7b"))
 f.pin("src/b0/profile_nutridata_core_links.py","80cee2a15e37da39da9328199563c56c198bb622cc66c2896936758ccc7d4512")
 hashes={x["artifact_sha256"] for x in src};raws={}
 for m in mf:
  if m["sha256"] not in hashes:continue
  path=Path("source_data/excel-Nutridata")/m["file"]
  p=f.pin(path,m["sha256"]);require(p.stat().st_size==m["size_bytes"],"RAW_BYTES")
  ss=[s for s in src if s["artifact_sha256"]==m["sha256"]];ns={s["source_scope"] for s in ss}
  require(len(ns)==1 and m["sha256"] not in raws,"RAW_SCOPE")
  raw_check(p,ss,next(iter(ns)),native);raws[m["sha256"]]=len(ss)
 require(set(raws)==hashes and sum(raws.values())==32,"RAW_CLOSURE")
 # Only original frozen ranks enter retrieval. No reference or score keys passed.
 hints=[]
 for x in read(root/R/"controller_private/ProposalManifest.json").values():
  p=f.pin(R/x["file"],x["sha256"]);n=0
  for row in lines(p):
   n+=1
   if row["source_legacy_ref"] not in rid:continue
   sc="FOODON_EXTENSION" if row["target_scope"]==EXT else row["target_key"][0]
   hints.append({"review_id":rid[row["source_legacy_ref"]],"scope":sc,**{k:row[k] for k in ("target_key","label_rank","context_rank","frozen_pool_rank","fusion_score")}})
  require(n==x["rows"],"HINT_PARTITION_ROWS")
 packet={"purpose":"SOURCE_ONLY_RETRIEVAL_EXPERIMENT","source_records":src,"dense_rank_hints":hints,"reviewer_results_included":False,"mapping_release":False}
 groups=check_packet(packet);require(len(groups)==128,"HINT_GROUPS")
 f.pin(SCHEMA,"8b79406d0e2b08ca3d86def180e32f3881faaa0e1b38a7e53216861281014076")
 f.pin(PROTOCOL,"93abd373e58a0666dc4b58009a1fb2c96e25ad31f4124f2704153730f7c33789")
 # Stage exactly source-only review inputs separately, only on local machine.
 # No native raw NutriData XLSX, rank hints, controller receipts, development refs or code.
 out.mkdir(mode=0o700,parents=True);cp=out/"controller_private";cp.mkdir(mode=0o700);rp=out/"reviewer_staging";rp.mkdir(mode=0o700)
 pkt=cp/"RetrievalInput32.json";put(pkt,packet);os.chmod(pkt,0o600)
 allow={str(SRC):SRC_SHA,str(SCHEMA):f.pins[str(SCHEMA)],str(PROTOCOL):f.pins[str(PROTOCOL)],**STANDARDS}
 # Add only the normative spec from prior review protocol (no earlier comparator report).
 spec=Path("docs/AI_Nutri_Unified_Data_Foundation_v2.1.md")
 f.pin(spec,"3c0ef69f9ecff2178830c0b4d43253dae5c161d7308c86bc2b6be5e6a68b26ed");allow[str(spec)]=f.pins[str(spec)]
 for rel,h in allow.items():copy_pinned(root/rel,rp/rel,h)
 # Preserve the original canonical locator path conventions.
 task={"task_id":"B2-U3R2-REF32-A2-001","status":"PREPARED_NOT_AUTHORIZED_NOT_DISPATCHED",
 "purpose":"INDEPENDENT_SOURCE_FIRST_REFERENCE_CANDIDATES_ONLY",
 "case_count":32,"reviewer":"UNASSIGNED","allowed_inputs":allow,
 "source_packet":str(SRC),"response_schema":str(SCHEMA),"reference_protocol":"R2 schema and same-cycle locator validation; explicit unknowns, at most three proposals and three hard negatives per standard per case, no forced mappings.",
 "canonical_locator_contract":{"FoodOn":"runs/B2/U3-A/inputs/FoodOn.owl#rdf:about=<full IRI>",
 "FDC_SR_Legacy":"runs/B2/U3-A/inputs/FDC_SR_2018.zip!<exact food.csv member>:row:<logical record header=1>",
 "FNDDS":"runs/B2/U3-A/inputs/FNDDS_2015_16.zip!<exact survey_fndds_food.csv member>:row:<logical record header=1> | runs/B2/U3-A/inputs/FNDDS_ARS_foods_2015_16.xlsx!Foods and Beverages:row:<actual row>"},
 "rules":["Copy case identity exactly. Read only authorized source packet and fixed standards. Reconstruct eight dimensions as explicit source, inferred, external or unknown. Do not infer physical composition, weights, current state, species or nutrient amounts.",
 "Independently search all three standards with recorded terms, native IDs, exact labels, versions and locators. Up to 3 actual candidates and 3 difficult negatives per standard; no target required; no-supported-target refers only to material reviewed.",
 "Use relation direction SOURCE_RELATION_TO_TARGET, preserve conditions/unknowns; no accepted equivalence, nutrient transfer, or scientific Gold.",
 "Use exact response schema. SOURCE_EXPLICIT artifact hash is case artifact SHA and locator compact sorted canonical JSON of source_locator. TARGET_EXPLICIT uses actual allowed standard artifact SHA and exact candidate locator. Evidence indices zero-based. FNDDS composite locator required; controller may add verified same-cycle carrier locator only under prior explicit exception, never mutate response.",
 "Do not read any candidate list, dense hints, ranking, prior reviewer response, lexicon, method code, full private raw sources or another agent's context. No external search or network unless separately authorized.",
 "Declare actual reviewer identity/build, exposure history, actual read set, execution method and limitations; do not claim strict confirmatory blind if not established. Do not review until controller grants real access and authorization."],
 "required_outputs":["ExecutionManifest.json","ReviewRecords.jsonl","ReviewReport.md","CriticFreezeReceipt.json"],
 "release_authorized":False,"external_transfer_authorized":False,"reviewer_acl_verified":False,
 "rights_status":"NUTRIDATA_RIGHTS_UNRESOLVED","stop":"Freeze complete reviewer bytes and stop; no controller comparison without separate explicit PI authorization."}
 taskpath=rp/"A2ReviewTask.json";put(taskpath,task);os.chmod(taskpath,0o600)
 # Local owner-only modes reduce accidental disclosure but are not separate-account ACL.
 require(set(str(p.relative_to(rp)) for p in rp.rglob("*") if p.is_file())==set(allow)|{"A2ReviewTask.json"},"REVIEWER_FILE_SET")
 for rel,h in allow.items():require(sha(rp/rel)==h,"REVIEWER_COPY_DRIFT")
 f.check()
 prep={"status":"LOCAL_PROJECTION_READY_REVIEWER_DISPATCH_HOLD","policy_sha256":POL_SHA,"source_packet_sha256":SRC_SHA,"case_count":32,
 "strata":[{"cohort":k[0],"source_scope":k[1],"n":v} for k,v in sorted(strata.items())],
 "source_identity_verified":32,"raw_workbooks_verified":len(raws),"raw_rows_verified":32,"development_overlap":0,
 "rights_domains":dict(rights),"local_only":True,"external_transfer_authorized":False,"reviewer_acl_verified":False,
 "dense_hint_rows":len(hints),"retrieval_groups":len(groups),"retrieval_packet_sha256":sha(pkt),
 "reviewer_staging_sha256":{**allow,"A2ReviewTask.json":sha(taskpath)},"input_fences":f.pins,
 "reserved_review_outcomes_read":0,"independent_reference_count":0,"mapping_release":0}
 put(out/"PreparationFreeze.json",prep)
 print("A2_PREPARED",json.dumps({k:v for k,v in prep.items() if k not in ("input_fences","reviewer_staging_sha256")},ensure_ascii=False),"FREEZE",sha(out/"PreparationFreeze.json"))
def summarize(root,out,prep_sha,retrieval,replay):
 require(sha(out/"PreparationFreeze.json")==prep_sha,"PREPARATION_PIN");p=read(out/"PreparationFreeze.json")
 f=Fence(root)
 for rel,h in p["input_fences"].items():f.pin(rel,h)
 for rel,h in p["reviewer_staging_sha256"].items():require(sha(out/"reviewer_staging"/rel)==h,"REVIEWER_DRIFT")
 require(sha(out/"controller_private/RetrievalInput32.json")==p["retrieval_packet_sha256"],"PACKET_DRIFT")
 receipts=[]
 for rr in (retrieval,replay):
  z=read(rr/"RetrievalReplayReceipt.json");require(z["method_sha256"]==f.pins[str(RUNNER)] and z["packet_sha256"]==p["retrieval_packet_sha256"] and z["groups"]==384 and z["source_records"]==32 and not z["reviewer_results_read"] and not z["mapping_release"],"RETRIEVAL_RECEIPT")
  require(set(z["output_sha256"])=={"Ranks.jsonl","QueryHypotheses.jsonl"} and all(sha(rr/x)==h for x,h in z["output_sha256"].items()),"RETRIEVAL_BYTES");receipts.append(z)
 require(receipts[0]["output_sha256"]==receipts[1]["output_sha256"],"RETRIEVAL_NONDETERMINISM")
 ranks=list(lines(retrieval/"Ranks.jsonl"));qs=list(lines(retrieval/"QueryHypotheses.jsonl"))
 src=read(out/"controller_private/RetrievalInput32.json")["source_records"];ids={s["review_id"] for s in src}
 require(len(qs)==32 and {q["review_id"] for q in qs}==ids,"QUERY_CLOSURE")
 arms=("BASELINE_FUSION","SOURCE_SPARSE","HYBRID")
 require(len(ranks)==384 and {(r["review_id"],r["scope"],r["arm"]) for r in ranks}=={(i,s,a) for i in ids for s in SCOPES for a in arms},"RANK_CLOSURE")
 u=read(root/R/"controller_private/FrozenTargetUniverse.json");orig={tuple(x) for x in u["original"]};ext={tuple(x) for x in u["extension"]}
 for r in ranks:
  ks=[tuple(t) for t in r["targets"]];require(len(ks)==len(set(ks))<=r["pool_budget"],"RANK_BUDGET")
  require(all(t in (ext if r["scope"]=="FOODON_EXTENSION" else orig) and (r["scope"]=="FOODON_EXTENSION" or t[0]==r["scope"]) for t in ks),"RANK_SCOPE")
 stats=[]
 for arm in arms:
  for domain in ("ORIGINAL","EXTENSION"):
   rs=[r for r in ranks if r["arm"]==arm and (r["scope"]=="FOODON_EXTENSION")== (domain=="EXTENSION")]
   for k in (1,3,5,12,"POOL"):
    cnt=Counter()
    for r in rs:cnt[r["review_id"]]+=len(r["targets"] if k=="POOL" else r["targets"][:k])
    stats.append({"arm":arm,"domain":domain,"k_per_scope":k,"cases":32,"groups":len(rs),"candidate_edges":sum(cnt.values()),"cases_with_candidates":sum(n>0 for n in cnt.values()),"groups_empty":sum(not r["targets"] for r in rs),"reference_hit":None,"reference_denominator":None})
 lexical={"cases_with_identity_tokens":sum(bool(q["identity_tokens"]) for q in qs),"cases_without_identity_tokens":sum(not q["identity_tokens"] for q in qs),
 "cases_with_label_hypotheses":sum(bool(q["label_hypotheses"]) for q in qs),
 "cases_with_any_untranslated_residual":sum(bool(q["untranslated_label_residual"].strip("()[]（）【】，、, ")) for q in qs),
 "cases_with_alias_tokens":sum(bool(q["alias_tokens"]) for q in qs),"cases_with_component_tokens":sum(bool(q["component_tokens"]) for q in qs)}
 f.check()
 report={"status":"PASS_RESERVED32_LOCAL_RETRIEVAL_FROZEN / INDEPENDENT_REFERENCE_AND_GENERALIZATION_HOLD","policy_sha256":POL_SHA,"preparation_sha256":prep_sha,
 "cases":32,"groups":384,"retrieval_artifacts_byte_identical":2,"query_lexical_coverage":lexical,"pre_reference_metrics":stats,"reference_hit_at12":None,
 "independent_reference_records":0,"reviewer_dispatched":False,"reviewer_outcomes_read":0,"rights_status":"NUTRIDATA_RIGHTS_UNRESOLVED",
 "limitations":["Aggregate candidate coverage is not reference recall or correctness.","Same NutriData source family and prior 284 baseline universe; reserved sample disjoint by source ID from first44, not externally held-out dataset or proof of all prior model exposure absence.","Local restricted development only; source rights unresolved. Independent reviewer permissions, ACL and data transfer not established."]}
 put(out/"A2PreReferenceReport.json",report)
 fr={"status":"RETRIEVAL_FROZEN_BEFORE_REFERENCE / REVIEWER_DISPATCH_HOLD","policy_sha256":POL_SHA,"prep_sha256":prep_sha,
 "retrieval_run":str(retrieval.relative_to(root)),"replay_run":str(replay.relative_to(root)),
 "retrieval_receipt_sha256":sha(retrieval/"RetrievalReplayReceipt.json"),"replay_receipt_sha256":sha(replay/"RetrievalReplayReceipt.json"),
 "retrieval_output_sha256":receipts[0]["output_sha256"],"aggregate_report_sha256":sha(out/"A2PreReferenceReport.json"),
 "source_packet_sha256":SRC_SHA,"reviewer_staging_sha256":p["reviewer_staging_sha256"],
 "cases":32,"reference_results_read":0,"reviewer_dispatch_authorized":False,"mapping_release_authorized":False}
 put(out/"A2RetrievalFreezeReceipt.json",fr)
 print("A2_FROZEN",sha(out/"A2RetrievalFreezeReceipt.json"),json.dumps({"lexical":lexical,"pool_and_top12":[r for r in stats if r["k_per_scope"] in (12,"POOL")]},ensure_ascii=False))
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("phase",choices=["prepare","summarize"]);a.add_argument("--root",type=Path,default=Path("."));a.add_argument("--out",type=Path,required=True);a.add_argument("--prep-sha");a.add_argument("--retrieval",type=Path);a.add_argument("--replay",type=Path);x=a.parse_args()
 if x.phase=="prepare":prepare(x.root.resolve(),x.out.resolve())
 else:require(x.prep_sha and x.retrieval and x.replay,"REPLAY_ARGS_REQUIRED");summarize(x.root.resolve(),x.out.resolve(),x.prep_sha,x.retrieval.resolve(),x.replay.resolve())
