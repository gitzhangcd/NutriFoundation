#!/usr/bin/env python3
"""A2.6-P1 actual protected comparison import. Never scores or dispatches.
Real inputs are opened only after a separately supplied trusted grant digest,
rights and semantic decisions, and the P1 engineering freeze are verified.
No generic --yes flag. Local operator trust boundary, not digital identity proof."""
import argparse,collections as C,fcntl,hashlib,json,math,os,re,stat,sys
from pathlib import Path
from a26_p1_semantic_policy import ROUTE,VERSION as SEMVER,need
B=Path("runs/B2/U3-B/C2/R2/P2/A2")
P0=B/"qualification_p0_001"
P1=B/"qualification_p1_001"
RUN=B/"agy_r1_002"
ST=B/"local_001/reviewer_staging"
AUTH=B/"authorization_p1_001"
DEST=B/"comparison_import_001"
FINAL="024d90970fa5f7990952bc702e63b5591c5f01e65881c69f8ef338554e9a6834"
P0_SHA="dc0d29c58596443165ad3b67b858090b72c21df7daf80858635edeeff908d8ae"
P0_GATE="f3b6d55f93e16d5bd8d1fcda17de879a1595e8c575170343b0a705def36f03c0"
PREP="38b36cd2e44d5c538ad8a18bf560229532cf06e46dc58a36c870c4b9ac1be1f4"
RET="cc43ec13416ddf6fb35ee960ba937e9606e184ce2e36ea2448fbdfaa524bff26"
POL="58c53ab63cf4ac25d030d78e03dcdded8a51fb5a5802e7623ee75bd93af5ddc6"
METHOD="08056819875d23e3c507b72d55eca479319fe737dbf4d7fa45bedc78ad2a6bd8"
POLPATH=Path("configs/udf/u3r2p2a1/RetrievalPolicyFreeze_v0.1.json")
SCORE="f5e6ad137257f3a0ff182ee9c176770f0e38ef4a22a74d4ad6eba675af802d29"
SUPPORT_SHA="84daeb34902d2e77d6ae3f94100314a0d98dae80ce9f540f92eb6bbc603be3e4"
SOURCE=Path("runs/B2/U3-B/C2/R2/real_001/reserved_source_only/R2Calibration32.json")
UNIVERSE=Path("runs/B2/U3-B/C2/R2/real_001/controller_private/FrozenTargetUniverse.json")
PACKET=B/"local_001/controller_private/RetrievalInput32.json"
RANKRUNS=(Path("runs/B2/U3-B/C2/R2/P2/A1/reserved32_retrieval_001"),Path("runs/B2/U3-B/C2/R2/P2/A1/reserved32_retrieval_002"))
ARMS=("BASELINE_FUSION","SOURCE_SPARSE","HYBRID")
SCOPES=("FoodOn","FDC_SR_Legacy","FNDDS","FOODON_EXTENSION")
VERSIONS={"FoodOn":"2026-09-20","FDC_SR_Legacy":"2018-04","FNDDS":"2015-16"}
HINT_FIELDS={"review_id","scope","target_key","label_rank","context_rank","frozen_pool_rank","fusion_score"}
SOURCE_FIELDS={"review_id","source_ref","source_scope","source_native_label","native_kind","source_locator","artifact_sha256","source_anchor_ref","native_aliases","reference_recipe_ingredient_names","context_locator","context_note","question","status"}
SCHEMA=Path("schemas/udf/u3r2/R2ReferenceReview_v0.1.schema.json")
GRANT_VERSION="A2.6-P1-ONE-RUN-IMPORT-GRANT-v0.1"
CONTRACT_VERSION="A2.6-P1-IMPORT-CONTRACT-v0.1"
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def goodsha(x):return isinstance(x,str) and re.fullmatch(r"[0-9a-f]{64}",x) is not None
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()+b"\n"
def strict_json(b):
 def pairs(xs):
  d={}
  for k,v in xs:
   need(k not in d,"DUPLICATE_JSON_KEY");d[k]=v
  return d
 def bad(x):raise ValueError("NONFINITE_JSON")
 return json.loads(b.decode("utf8"),object_pairs_hook=pairs,parse_constant=bad)
def jsonl(b):
 rows=b.splitlines()
 need(rows and all(x.strip() for x in rows),"JSONL_EMPTY_LINE")
 return [strict_json(x) for x in rows]
def secure_path(root,rel):
 need(isinstance(rel,Path) and not rel.is_absolute() and ".." not in rel.parts,"PATH_SCOPE")
 p=root
 for part in rel.parts:
  p=p/part;need(not p.is_symlink(),"SYMLINK_DENIED")
 need(p.resolve().is_relative_to(root),"PATH_ESCAPE")
 return p
def snapshot(root,rel,expected):
 """Immutable byte snapshot: check hash on the exact bytes later parsed.
 No arbitrary paths or output of actual records. Parent directory races by a
 hostile same-account operator are outside this application trust model."""
 need(goodsha(expected),"EXPECTED_SHA")
 p=secure_path(root,rel)
 need(p.is_file(),"REGULAR_FILE")
 fd=os.open(p,os.O_RDONLY|getattr(os,"O_NOFOLLOW",0)|getattr(os,"O_NONBLOCK",0))
 with os.fdopen(fd,"rb") as f:
  before=os.fstat(f.fileno());need(stat.S_ISREG(before.st_mode),"REGULAR_FILE")
  b=f.read();after=os.fstat(f.fileno())
  need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns) and len(b)==before.st_size,"READ_DRIFT")
 need(sha_bytes(b)==expected,"PIN_DRIFT")
 return b
def exact_fields(d,fields,code):
 need(isinstance(d,dict) and set(d)==set(fields),code)
def validate_decisions(grant,rights,semantic,evidence_sha,expected):
 exact_fields(grant,("version","status","run_id","scope","p1_receipt_sha256","import_contract_sha256","rights_decision_sha256","semantic_decision_sha256","reference_receipt_sha256","retrieval_receipt_sha256","owner_id","owner_attestation","import_authorized","scoring_authorized","unblind_scope","mapping_release_authorized"),"GRANT_FIELDS")
 need(grant["version"]==GRANT_VERSION and grant["status"]=="EXPLICIT_PI_AUTHORIZATION" and grant["run_id"]=="comparison_import_001" and grant["scope"]=="LOCAL_DEVELOPMENT_IMPORT_ONLY","GRANT_SCOPE")
 for k,h in expected.items():need(grant[k]==h,"GRANT_PIN")
 need(grant["import_authorized"] is True and grant["scoring_authorized"] is False and grant["mapping_release_authorized"] is False and grant["unblind_scope"]=="CONTROLLER_ONLY_NO_SCORE_NO_EXPORT","GRANT_BOUNDARY")
 need(isinstance(grant["owner_id"],str) and grant["owner_id"].strip() and isinstance(grant["owner_attestation"],str) and grant["owner_attestation"].strip(),"OWNER_ATTESTATION")
 exact_fields(rights,("version","decision","reference_receipt_sha256","scope","custodian_id","documentary_basis","evidence_bundle_sha256","documentary_basis_verified_by_custodian","valid_for_this_run","local_development_import","expert_access","external_transfer","publication","commercial_use","mapping_release","restrictions","signed_attestation"),"RIGHTS_FIELDS")
 need(rights["version"]=="A2.6-P1-RIGHTS-DECISION-v0.1" and rights["decision"]=="DOCUMENTED_LOCAL_DEVELOPMENT_USE_PERMITTED" and rights["reference_receipt_sha256"]==FINAL and rights["scope"]=="32_NUTRIDATA_AND_PINNED_AUTHORITIES","RIGHTS_SCOPE")
 need(rights["evidence_bundle_sha256"]==evidence_sha and goodsha(evidence_sha) and rights["documentary_basis_verified_by_custodian"] is True and rights["valid_for_this_run"] is True and rights["local_development_import"] is True,"RIGHTS_EVIDENCE")
 need(all(rights[k] is False for k in ("external_transfer","publication","commercial_use","mapping_release")) and type(rights["expert_access"]) is bool,"RIGHTS_BOUNDARY")
 need(all(isinstance(rights[k],str) and rights[k].strip() for k in ("custodian_id","documentary_basis","restrictions","signed_attestation")),"RIGHTS_ATTESTATION")
 exact_fields(semantic,("version","route","reference_receipt_sha256","policy_version","policy_sha256","owner_id","expert_work_deferred","no_gold_claim","original_primary_unchanged","conservative_secondary_required","signed_attestation"),"SEMANTIC_FIELDS")
 need(semantic["version"]=="A2.6-P1-SEMANTIC-DECISION-v0.1" and semantic["route"]==ROUTE and semantic["reference_receipt_sha256"]==FINAL and semantic["policy_version"]==SEMVER,"SEMANTIC_SCOPE")
 need(semantic["owner_id"]==grant["owner_id"] and semantic["expert_work_deferred"] is True and semantic["no_gold_claim"] is True and semantic["original_primary_unchanged"] is True and semantic["conservative_secondary_required"] is True and isinstance(semantic["signed_attestation"],str) and semantic["signed_attestation"].strip(),"SEMANTIC_ATTESTATION")
 need(goodsha(semantic["policy_sha256"]),"SEMANTIC_PIN")
def validate_rights_evidence(bundle,rights):
 exact_fields(bundle,("version","custodian_id","entries","scope"),"RIGHTS_EVIDENCE_FIELDS")
 need(bundle["version"]=="A2.6-P1-RIGHTS-EVIDENCE-INDEX-v0.1" and bundle["custodian_id"]==rights["custodian_id"] and bundle["scope"]==rights["scope"],"RIGHTS_EVIDENCE_IDENTITY")
 need(isinstance(bundle["entries"],list) and bool(bundle["entries"]),"RIGHTS_EVIDENCE_EMPTY")
 ids=set()
 for entry in bundle["entries"]:
  exact_fields(entry,("document_id","document_sha256","description","local_record_locator"),"RIGHTS_DOCUMENT_FIELDS")
  need(all(isinstance(entry[k],str) and entry[k].strip() for k in ("document_id","description","local_record_locator")) and goodsha(entry["document_sha256"]) and entry["document_id"] not in ids,"RIGHTS_DOCUMENT_BINDING")
  ids.add(entry["document_id"])
 # This is a hash-bound custodian evidence index, not legal verification.
 # Actual document review, applicability and custody remain human duties.
def key(x,versions=VERSIONS):
 need(isinstance(x,list) and len(x)==3 and all(isinstance(t,str) and t.strip() for t in x) and x[0] in versions and x[1]==versions[x[0]],"NATIVE_KEY_VERSION")
 return tuple(x)
def universe(u,native_keys,sizes=(28845,1174)):
 need(isinstance(u,dict) and "original" in u and "extension" in u and isinstance(u["original"],list) and isinstance(u["extension"],list),"UNIVERSE_FIELDS")
 a=[key(x) for x in u["original"]];b=[key(x) for x in u["extension"]]
 o,e=set(a),set(b)
 need(len(a)==len(o)==sizes[0] and len(b)==len(e)==sizes[1] and not o&e,"UNIVERSE_CARDINALITY_OR_OVERLAP")
 need(all(t[0]=="FoodOn" for t in e) and (o|e)<=native_keys,"UNIVERSE_NATIVE_MEMBERSHIP")
 need({t[0] for t in o}==set(VERSIONS),"UNIVERSE_SYSTEMS")
 return o,e
def expected_sources(src):
 need(isinstance(src,list) and len(src)==32,"SOURCE32")
 for s in src:
  exact_fields(s,SOURCE_FIELDS,"SOURCE_FIELDS")
  need(s["status"]=="NOT_REVIEWED" and isinstance(s["review_id"],str) and s["review_id"].strip() and isinstance(s["source_ref"],str) and s["source_ref"].strip(),"SOURCE_ID")
 ids=[s["review_id"] for s in src]
 need(len(set(ids))==len({s["source_ref"] for s in src})==32,"SOURCE_ID_CLOSURE")
 need(C.Counter(s["source_scope"] for s in src)=={"nutridata:ingredient":16,"nutridata:dish":16},"SOURCE_STRATA")
 return ids
def domain_scope(t,scope,o,e):
 return t in e if scope=="FOODON_EXTENSION" else t in o and t[0]==scope
def reconstruct_budgets(packet,src,o,e):
 exact_fields(packet,("purpose","source_records","dense_rank_hints","reviewer_results_included","mapping_release"),"PACKET_FIELDS")
 need(packet["purpose"]=="SOURCE_ONLY_RETRIEVAL_EXPERIMENT" and packet["reviewer_results_included"] is False and packet["mapping_release"] is False and packet["source_records"]==src,"PACKET_SOURCE_BINDING")
 ids=expected_sources(src);groups=C.defaultdict(list);seen=set()
 need(isinstance(packet["dense_rank_hints"],list),"HINT_ARRAY")
 for row in packet["dense_rank_hints"]:
  exact_fields(row,HINT_FIELDS,"HINT_FIELDS")
  i,s=row["review_id"],row["scope"];t=key(row["target_key"])
  need(i in ids and s in SCOPES and domain_scope(t,s,o,e),"HINT_SCOPE")
  k=(i,s,t);need(k not in seen,"HINT_DUPLICATE");seen.add(k)
  need(all(x is None or type(x) is int and x>0 for x in (row["label_rank"],row["context_rank"],row["frozen_pool_rank"])),"HINT_RANK_TYPE")
  need(row["label_rank"] is not None or row["context_rank"] is not None,"HINT_NO_RANK")
  need(type(row["fusion_score"]) in (int,float) and math.isfinite(row["fusion_score"]),"HINT_SCORE_TYPE")
  groups[i,s].append(row)
 need(set(groups)=={(i,s) for i in ids for s in SCOPES},"HINT_GROUP_CLOSURE")
 budgets={};baseline={}
 for k,rs in groups.items():
  s=k[1];n=12 if s=="FOODON_EXTENSION" else 20
  for name in ("label_rank","context_rank"):
   need(sorted(x[name] for x in rs if x[name] is not None)==list(range(1,n+1)),"HINT_RANK_CLOSURE")
  need(n<=len(rs)<=2*n,"HINT_UNION_CAP")
  budgets[k]=len(rs)
  baseline[k]=[tuple(x["target_key"]) for x in sorted(rs,key=(lambda x:(-x["fusion_score"],tuple(x["target_key"]))) if s=="FOODON_EXTENSION" else (lambda x:(x["frozen_pool_rank"] or 99999,-x["fusion_score"],tuple(x["target_key"]))))]
 return ids,budgets,baseline
def validate_ranks(rows,ids,budgets,baseline,o,e):
 need(len(ids)==len(set(ids))==32 and len(rows)==384,"RANK_384_ID32")
 seen=set()
 for x in rows:
  exact_fields(x,("review_id","scope","arm","pool_budget","targets"),"RANK_FIELDS")
  i,s,a=x["review_id"],x["scope"],x["arm"];k=(i,s);g=(*k,a)
  need(i in ids and s in SCOPES and a in ARMS and g not in seen,"RANK_GROUP")
  seen.add(g);need(type(x["pool_budget"]) is int and x["pool_budget"]==budgets[k],"TRUSTED_BUDGET")
  need(isinstance(x["targets"],list),"RANK_TARGET_ARRAY");ts=[key(t) for t in x["targets"]]
  need(len(ts)==len(set(ts))<=budgets[k] and all(domain_scope(t,s,o,e) for t in ts),"RANK_MEMBERSHIP")
  if a=="BASELINE_FUSION":need(ts==baseline[k],"BASELINE_ORDER_OR_MEMBERSHIP")
 need(seen=={(i,s,a) for i in ids for s in SCOPES for a in ARMS},"RANK_CLOSURE")
 return True
def validate_reference_bindings(refs,src,validator,std):
 need(len(refs)==32 and len(src)==32,"REF32")
 for r,s in zip(refs,src):
  need(validator.is_valid(r) and all(r[k]==s[k] for k in ("review_id","source_ref","source_scope","source_native_label","native_kind")),"REF_SCHEMA_IDENTITY_ORDER")
  need(r["review_status"]=="CRITIC_DRAFT" and not any(r[k] for k in ("accepted_equivalence","mapping_release_authorized","scientific_reference_qualified")),"REF_SCOPE")
  ev=r["evidence"];spos={j for j,z in enumerate(ev) if z["role"]=="SOURCE_EXPLICIT" and z["artifact_sha256"]==s["artifact_sha256"] and z["locator"]==json.dumps(s["source_locator"],ensure_ascii=False,sort_keys=True,separators=(",",":"))}
  p=set();n=set()
  for field,seen in (("independent_candidates",p),("hard_negatives",n)):
   cnt=C.Counter()
   for x in r[field]:
    t=key(x["target_key"]);need(t in std and t not in seen,"REF_NATIVE_KEY_DUP")
    seen.add(t);cnt[t[0]]+=1;z=std[t]
    need(x["target_native_label"]==z["target_native_label"] and x["target_locator"]==z["target_locator"],"REF_NATIVE_LOCATOR")
    jj=x["evidence_refs"];need(all(type(j) is int and 0<=j<len(ev) for j in jj) and bool(spos&set(jj)),"REF_SOURCE_EVIDENCE")
    need(any(ev[j]["role"]=="TARGET_EXPLICIT" and ev[j]["artifact_sha256"]==z["artifact_sha256"] and ev[j]["locator"]==z["target_locator"] for j in jj),"REF_TARGET_EVIDENCE")
   need(all(v<=3 for v in cnt.values()),"REF_CAP")
  need(not p&n,"REF_POLARITY")
def save(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,"wb") as f:f.write(b);f.flush();os.fsync(f.fileno())
def pin_json(root,path,h):return strict_json(snapshot(root,path,h))
def require_auth(root,trusted_grant_sha,trusted_p1_sha,read=snapshot):
 """The ONLY gate before actual protected reads. Reads only fixed aggregate,
 code, and decision files. Hashes supplied from a trusted separate PI turn.
 No auth inferred from existence of a file, flags, or a template."""
 need(goodsha(trusted_grant_sha) and goodsha(trusted_p1_sha),"TRUSTED_GRANT_AND_P1_DIGEST_REQUIRED")
 def j(p,h):return strict_json(read(root,p,h))
 p0=j(P0/"A26P0QualificationReceipt.json",P0_SHA)
 need(p0["status"]=="PASS_AUDIT_EXECUTED / HOLD_SCIENTIFIC_QUALIFICATION_AND_COMPARISON" and not p0["comparison_authorized"],"P0_GATE")
 p1=j(P1/"A26P1EngineeringReceipt.json",trusted_p1_sha)
 need(p1["status"]=="PASS_ENGINEERING_PREPARATION / HOLD_OWNER_DECISIONS_AND_UNBLIND" and p1["p0_receipt_sha256"]==P0_SHA and not p1["comparison_authorized"],"P1_SCOPE")
 contract_sha=p1["import_contract_sha256"];ct=j(P1/"A26P1ImportContract.json",contract_sha)
 need(ct["version"]==CONTRACT_VERSION and ct["status"]=="ENGINEERING_READY_OWNER_AUTHORIZATION_PENDING" and ct["p0_gate_sha256"]==P0_GATE and ct["final_reference_receipt_sha256"]==FINAL and ct["retrieval_receipt_sha256"]==RET and ct["semantic_route"]==ROUTE and not ct["real_import_executed"],"CONTRACT_SCOPE")
 need(ct["code_sha256"]["src/u3r2p2a2/score_a2.py"]==SCORE and ct["code_sha256"]["src/u3r2/compare_reference.py"]==SUPPORT_SHA,"FROZEN_SCORE")
 for path,h in ct["code_sha256"].items():
  need(path.startswith(("src/","tests/","schemas/","docs/","configs/")) and "private" not in Path(path).parts,"CODE_PATH")
  read(root,Path(path),h)
 j(P0/"A26P0QualificationGate.json",P0_GATE)
 grant=j(AUTH/"ImportGrant.json",trusted_grant_sha)
 rights=j(AUTH/"RightsDecision.json",grant["rights_decision_sha256"]);sem=j(AUTH/"SemanticDecision.json",grant["semantic_decision_sha256"])
 evidence=read(root,AUTH/"RightsEvidenceBundle.json",rights["evidence_bundle_sha256"])
 validate_rights_evidence(strict_json(evidence),rights)
 validate_decisions(grant,rights,sem,sha_bytes(evidence),{"p1_receipt_sha256":trusted_p1_sha,"import_contract_sha256":contract_sha,"reference_receipt_sha256":FINAL,"retrieval_receipt_sha256":RET})
 need(sem["policy_sha256"]==ct["semantic_policy_sha256"],"SEMANTIC_POLICY_DRIFT")
 return grant,ct
_PERMIT_SENTINEL=object()
class _ImportPermit:
 def __init__(self,sentinel,root,grant,ct,grant_sha,p1_sha):
  need(sentinel is _PERMIT_SENTINEL,"IMPORT_PERMIT_REQUIRED")
  self.root=root;self.grant=grant;self.ct=ct;self.grant_sha=grant_sha;self.p1_sha=p1_sha
def import_protected(root,grant,ct,permit=None,read=snapshot):
 """Only the guarded entrypoint may call this after authorization and consumption.
 Python application-level protection, not a defense against a hostile local operator.
 All input hashes come from prior immutable receipts, not caller rank data."""
 need(isinstance(permit,_ImportPermit) and permit.root==root and permit.grant is grant and permit.ct is ct,"IMPORT_PERMIT_REQUIRED")
 if read is snapshot:
  marker={"grant_sha256":permit.grant_sha,"p1_receipt_sha256":permit.p1_sha,"run_id":DEST.name,"scope":"LOCAL_DEVELOPMENT_IMPORT_ONLY","scoring_authorized":False}
  need(snapshot(root,DEST/"AuthorizationConsumed.json",sha_bytes(canon(marker)))==canon(marker),"CONSUMPTION_MARKER")
 def j(path,h):return strict_json(read(root,path,h))
 prep=j(B/"local_001/PreparationFreeze.json",PREP);fr=j(B/"local_001/A2RetrievalFreezeReceipt.json",RET);pol=j(POLPATH,POL)
 final=j(RUN/"A2FinalReferenceFreezeReceipt.json",FINAL)
 need(final["completed_cases"]==32 and final["complete_reference_set"] and not final["scientific_reference_qualified"] and not final["comparison_executed"] and not final["unblind_authorized"] and final["scientific_method_sha256"]==METHOD,"FINAL_SCOPE")
 need(fr["prep_sha256"]==PREP and fr["policy_sha256"]==POL and fr["reference_results_read"]==0 and fr["cases"]==32 and (fr["retrieval_run"],fr["replay_run"])==tuple(map(str,RANKRUNS)),"RETRIEVAL_FREEZE_SCOPE")
 need(pol["primary_arm"]=="SOURCE_SPARSE" and pol["comparators"]==["BASELINE_FUSION","HYBRID"],"ARMS")
 need(set(fr["retrieval_output_sha256"])=={"Ranks.jsonl","QueryHypotheses.jsonl"},"RANK_OUTPUT_SET")
 # Verify both complete rank/hypothesis snapshots BEFORE parsing any ranking or
 # hypothesis content. No later reopening from the original protected paths.
 blobs={}
 for i,rr in enumerate(RANKRUNS):
  rec=j(rr/"RetrievalReplayReceipt.json",fr[("retrieval_receipt_sha256","replay_receipt_sha256")[i]])
  need(rec["method_sha256"]==pol["pins"]["src/u3r2p2a1/source_only_retrieval.py"] and rec["packet_sha256"]==prep["retrieval_packet_sha256"] and rec["groups"]==384 and rec["source_records"]==32 and rec["reviewer_results_read"] is False and rec["mapping_release"] is False and rec["source_only"] is True and rec["output_sha256"]==fr["retrieval_output_sha256"],"RETRIEVAL_RECEIPT")
  for name,h in fr["retrieval_output_sha256"].items():blobs[i,name]=read(root,rr/name,h)
 need(all(blobs[0,n]==blobs[1,n] for n in fr["retrieval_output_sha256"]),"RETRIEVAL_BYTE_REPLAY")
 src=j(ST/SOURCE,prep["source_packet_sha256"]);need(prep["source_packet_sha256"]==fr["source_packet_sha256"],"SOURCE_PIN")
 packet=j(PACKET,prep["retrieval_packet_sha256"]);u=j(UNIVERSE,pol["pins"][str(UNIVERSE)])
 for rel,h in prep["reviewer_staging_sha256"].items():read(root,ST/rel,h)
 # Standards constructor reopens staged files. Hash their bytes before and
 # after parsing; no use of tested lexicon, ranker, or controller-private DB.
 from agy_raw_standard_browser import Standards
 from jsonschema import Draft202012Validator
 task=j(ST/"A2ReviewTask.json",prep["reviewer_staging_sha256"]["A2ReviewTask.json"])
 std=Standards(root/ST,task["allowed_inputs"])
 for rel,h in prep["reviewer_staging_sha256"].items():read(root,ST/rel,h)
 o,e=universe(u,set(std.by));ids,budgets,baseline=reconstruct_budgets(packet,src,o,e)
 need(len(packet["dense_rank_hints"])==prep["dense_hint_rows"]==3875 and len(budgets)==128,"FROZEN_HINT_COUNTS")
 rr=RUN/"reviewer_private/Final";fp=final["final_file_hashes"]
 need(set(fp)=={"CriticFreezeReceipt.json","ExecutionManifest.json","ReviewRecords.jsonl","ReviewReport.md"},"FINAL_FILE_SET")
 fbytes={n:read(root,rr/n,h) for n,h in fp.items()}
 cf=strict_json(fbytes["CriticFreezeReceipt.json"]);mf=strict_json(fbytes["ExecutionManifest.json"])
 need(cf["status"]=="REVIEW_FROZEN" and cf["completed_cases"]==32 and not any(cf[k] for k in ("scientific_reference_qualified","mapping_release_authorized","unblind_authorized","comparison_executed")),"CRITIC_SCOPE")
 need(cf["output_file_hashes"]=={n:h for n,h in fp.items() if n!="CriticFreezeReceipt.json"} and mf["case_freeze_hashes"]==final["case_freeze_hashes"] and mf["source_count"]==32 and mf["method_sha256"]==METHOD,"FINAL_BINDING")
 refs=jsonl(fbytes["ReviewRecords.jsonl"]);validator=Draft202012Validator(j(ST/SCHEMA,prep["reviewer_staging_sha256"][str(SCHEMA)]))
 validate_reference_bindings(refs,src,validator,std.by)
 ranks=jsonl(blobs[0,"Ranks.jsonl"]);qs=jsonl(blobs[0,"QueryHypotheses.jsonl"])
 validate_ranks(ranks,ids,budgets,baseline,o,e)
 need(len(qs)==32 and [x["review_id"] for x in qs]==ids,"QUERY_HYPOTHESES_CLOSURE")
 # Validate membership and identity only. Never compute overlap, denominator,
 # metrics, or per-case scientific score here.
 return {"version":"A2.6-P1-SEALED-IMPORT-v0.1","expected_ids":ids,"ranks":ranks,"references":refs,"original":u["original"],"extension":u["extension"],"query_hypotheses":qs,"trusted_budgets":[{"review_id":i,"scope":s,"pool_budget":b} for (i,s),b in sorted(budgets.items())],"semantic_route":ROUTE,"comparison_executed":False,"scoring_authorized":False,"mapping_release":False}
def guarded_import(root,trusted_grant_sha,trusted_p1_sha,authorize=require_auth,consume=None,load=import_protected):
 grant,ct=authorize(root,trusted_grant_sha,trusted_p1_sha)
 need(consume is not None,"ONE_SHOT_CONSUMPTION_REQUIRED")
 consume(grant,ct)
 permit=_ImportPermit(_PERMIT_SENTINEL,root,grant,ct,trusted_grant_sha,trusted_p1_sha)
 return load(root,grant,ct,permit)
def io_gate(root,out):
 """Process-level file-open guard, not an OS sandbox or defense against a
 hostile operator with full access to the local account."""
 state={"activated":False,"committing":False,"protected_reads":0,"denied_reads":0}
 safe={root/p for p in (P0/"A26P0QualificationReceipt.json",P0/"A26P0QualificationGate.json",P1/"A26P1EngineeringReceipt.json",P1/"A26P1ImportContract.json",AUTH/"ImportGrant.json",AUTH/"RightsDecision.json",AUTH/"SemanticDecision.json",AUTH/"RightsEvidenceBundle.json",RUN/".controller.lock")}
 protected={root/p for p in (B/"local_001/PreparationFreeze.json",B/"local_001/A2RetrievalFreezeReceipt.json",POLPATH,RUN/"A2FinalReferenceFreezeReceipt.json",PACKET,UNIVERSE)}
 protected.update(root/rr/name for rr in RANKRUNS for name in ("RetrievalReplayReceipt.json","Ranks.jsonl","QueryHypotheses.jsonl"))
 protected.update(root/RUN/"reviewer_private/Final"/name for name in ("ExecutionManifest.json","ReviewRecords.jsonl","ReviewReport.md","CriticFreezeReceipt.json"))
 def hook(event,args):
  if event in ("subprocess.Popen","os.system","os.posix_spawn","os.exec","socket.connect","socket.bind","socket.getaddrinfo"):raise PermissionError("IMPORT_NO_EXTERNAL_DISPATCH")
  if event!="open" or isinstance(args[0],int):return
  path=Path(os.fsdecode(args[0])).resolve();mode=args[1] or "";flags=args[2] or 0
  writing=any(c in mode for c in "wax+") or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
  if path.is_relative_to(root):
   if writing:
    need((state["activated"] and path.is_relative_to(out)) or (state["committing"] and path==out/"AuthorizationConsumed.json"),"IMPORT_WRITE_DENIED")
    return
   if path in safe or path.is_relative_to(root/"src") or path.is_relative_to(root/"tests") or path.is_relative_to(root/"schemas") or path.is_relative_to(root/"docs") or path.is_relative_to(root/"configs"):
    return
   if state["activated"] and (path in protected or path.is_relative_to(root/ST) or path.is_relative_to(out)):
    state["protected_reads"]+=1;return
   state["denied_reads"]+=1;raise PermissionError("IMPORT_PROTECTED_READ_DENIED")
  if writing:raise PermissionError("IMPORT_EXTERNAL_WRITE_DENIED")
  if path.is_relative_to(Path.home()) and not path.is_relative_to(Path(sys.prefix).resolve()) and not path.is_relative_to(Path(sys.base_prefix).resolve()):raise PermissionError("IMPORT_EXTERNAL_HOME_READ_DENIED")
 return state,hook
def main(root,grant_sha,p1_sha):
 root=root.resolve();out=secure_path(root,DEST)
 state,hook=io_gate(root,out);sys.addaudithook(hook)
 need(not out.exists(),"IMPORT_RUN_ALREADY_EXISTS")
 with secure_path(root,RUN/".controller.lock").open("r") as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  def consume(g,c):
   need(not out.exists(),"IMPORT_RUN_ALREADY_EXISTS")
   out.mkdir(mode=0o700)
   # No protected read is made until this exclusive one-shot marker succeeds.
   state["committing"]=True
   try:
    save(out/"AuthorizationConsumed.json",canon({"grant_sha256":grant_sha,"p1_receipt_sha256":p1_sha,"run_id":out.name,"scope":"LOCAL_DEVELOPMENT_IMPORT_ONLY","scoring_authorized":False}))
   finally:
    state["committing"]=False
   state["activated"]=True
  bundle=guarded_import(root,grant_sha,p1_sha,consume=consume)
  need(state["denied_reads"]==0 and state["activated"],"IMPORT_IO_FENCE")
  private=out/"PrivateComparisonInputBundle.json";raw=canon(bundle);save(private,raw)
  receipt={"status":"PASS_LOCAL_IMPORT_VALIDATED_SEALED / HOLD_SEPARATE_SCORING_AUTHORIZATION","grant_sha256":grant_sha,"p1_receipt_sha256":p1_sha,"authorization_consumed_sha256":sha_bytes((out/"AuthorizationConsumed.json").read_bytes()),"reference_receipt_sha256":FINAL,"retrieval_receipt_sha256":RET,"private_bundle_sha256":sha_bytes(raw),"cases":32,"rank_groups":384,"original_universe_size":28845,"extension_universe_size":1174,"scope_budgets_verified":128,"protected_read_events":state["protected_reads"],"denied_read_events":state["denied_reads"],"comparison_executed":False,"scoring_authorized":False,"scientific_reference_qualified":False,"mapping_release":0}
  save(out/"ImportReceipt.json",canon(receipt));print(json.dumps(receipt),flush=True)
if __name__=="__main__":
 sys.dont_write_bytecode=True
 p=argparse.ArgumentParser();p.add_argument("--trusted-grant-sha256",required=True);p.add_argument("--trusted-p1-receipt-sha256",required=True);a=p.parse_args()
 try:main(Path.cwd(),a.trusted_grant_sha256,a.trusted_p1_receipt_sha256)
 except Exception as e:
  # Don't echo paths, input values or native labels on failed import.
  msg=str(e)
  print(json.dumps({"status":"HOLD_IMPORT_STOPPED","error":msg if re.fullmatch(r"[A-Z0-9_]{1,90}",msg) else type(e).__name__,"comparison_executed":False}),flush=True)
  raise SystemExit(2)
