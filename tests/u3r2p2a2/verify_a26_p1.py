#!/usr/bin/env python3
"""P1 synthetic-only adversarial contract tests. No real input read."""
import copy,hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src/u3r2p2a2"))
import a26_p1_import as m
import a26_p1_semantic_policy as sem
import agy_raw_standard_browser as browser
from jsonschema import Draft202012Validator
def h(s):return hashlib.sha256(s.encode()).hexdigest()
def obj(x):return m.canon(x)
def sha(b):return m.sha_bytes(b)
def decisions():
 evidence={"version":"A2.6-P1-RIGHTS-EVIDENCE-INDEX-v0.1","custodian_id":"synthetic-custodian","scope":"32_NUTRIDATA_AND_PINNED_AUTHORITIES","entries":[{"document_id":"fictional","document_sha256":h("fictional"),"description":"Synthetic evidence only","local_record_locator":"fictional-only"}]}
 r={"version":"A2.6-P1-RIGHTS-DECISION-v0.1","decision":"DOCUMENTED_LOCAL_DEVELOPMENT_USE_PERMITTED","reference_receipt_sha256":m.FINAL,"scope":evidence["scope"],"custodian_id":evidence["custodian_id"],"documentary_basis":"Synthetic only","evidence_bundle_sha256":sha(obj(evidence)),"documentary_basis_verified_by_custodian":True,"valid_for_this_run":True,"local_development_import":True,"expert_access":False,"external_transfer":False,"publication":False,"commercial_use":False,"mapping_release":False,"restrictions":"Local synthetic-only test","signed_attestation":"fictional-custodian-attestation"}
 s={"version":"A2.6-P1-SEMANTIC-DECISION-v0.1","route":sem.ROUTE,"reference_receipt_sha256":m.FINAL,"policy_version":sem.VERSION,"policy_sha256":h("synthetic-policy"),"owner_id":"synthetic-owner","expert_work_deferred":True,"no_gold_claim":True,"original_primary_unchanged":True,"conservative_secondary_required":True,"signed_attestation":"fictional-only"}
 expected={"p1_receipt_sha256":h("p1"),"import_contract_sha256":h("contract"),"reference_receipt_sha256":m.FINAL,"retrieval_receipt_sha256":m.RET}
 g={"version":m.GRANT_VERSION,"status":"EXPLICIT_PI_AUTHORIZATION","run_id":"comparison_import_001","scope":"LOCAL_DEVELOPMENT_IMPORT_ONLY","rights_decision_sha256":sha(obj(r)),"semantic_decision_sha256":sha(obj(s)),"owner_id":"synthetic-owner","owner_attestation":"fictional-only","import_authorized":True,"scoring_authorized":False,"unblind_scope":"CONTROLLER_ONLY_NO_SCORE_NO_EXPORT","mapping_release_authorized":False,**expected}
 return g,r,s,evidence,expected
def fixture():
 src=[]
 for i in range(32):
  scope="nutridata:ingredient" if i<16 else "nutridata:dish"
  src.append({"review_id":f"synthetic-{i:02d}","source_ref":f"fictional-{i}@"+h(str(i)),"source_scope":scope,"source_native_label":f"fictional food {i}","native_kind":"INGREDIENT_REFERENCE" if i<16 else "RECIPE_REFERENCE","source_locator":{"excel_row":i+2,"field":"name"},"artifact_sha256":h("synthetic-source"),"source_anchor_ref":"fictional-anchor","native_aliases":[],"reference_recipe_ingredient_names":[],"context_locator":{"excel_row":i+2,"quantity_not_used":True},"context_note":"Synthetic only","question":"Synthetic only","status":"NOT_REVIEWED"})
 by={}
 for scope,n in zip(m.SCOPES,(10000,9000,9845,1174)):
  system="FoodOn" if scope=="FOODON_EXTENSION" else scope
  by[scope]=[(system,m.VERSIONS[system],f"urn:fictional:{scope}:{j:05d}") for j in range(n)]
 u={"original":[list(t) for sc in m.SCOPES[:3] for t in by[sc]],"extension":[list(t) for t in by[m.SCOPES[3]]]}
 o=set(map(tuple,u["original"]));e=set(map(tuple,u["extension"]))
 native={t:{"target_native_label":"fictional target","target_locator":t[2],"artifact_sha256":h(t[0])} for t in o|e}
 hints=[];ranks=[];left=1571
 for s in src:
  i=s["review_id"]
  for sc in m.SCOPES:
   n=12 if sc=="FOODON_EXTENSION" else 20;extra=min(left,n);left-=extra;cap=n+extra
   keys=by[sc][:cap]
   for j,t in enumerate(keys):
    hints.append({"review_id":i,"scope":sc,"target_key":list(t),"label_rank":j+1 if j<n else None,"context_rank":j-extra+1 if j>=extra else None,"frozen_pool_rank":None if sc=="FOODON_EXTENSION" else j+1,"fusion_score":float(1000-j)})
   for arm,keys2 in zip(m.ARMS,(keys,[] if i.endswith("0") else keys[:2],list(reversed(keys)))):
    ranks.append({"review_id":i,"scope":sc,"arm":arm,"pool_budget":cap,"targets":[list(t) for t in keys2]})
 assert left==0 and len(hints)==3875 and len(ranks)==384
 packet={"purpose":"SOURCE_ONLY_RETRIEVAL_EXPERIMENT","source_records":src,"dense_rank_hints":hints,"reviewer_results_included":False,"mapping_release":False}
 refs=[]
 for s in src:
  t=by["FoodOn"][0];n=by["FoodOn"][1]
  evidence=[{"artifact_sha256":s["artifact_sha256"],"locator":m.canon(s["source_locator"]).decode().strip(),"observation":"fictional source","role":"SOURCE_EXPLICIT"}]
  for k in (t,n):evidence.append({"artifact_sha256":native[k]["artifact_sha256"],"locator":native[k]["target_locator"],"observation":"fictional target","role":"TARGET_EXPLICIT"})
  dims={k:{"value":None,"state":"UNRESOLVED","evidence_refs":[]} for k in sem.DIMS}
  dims["base_food"]={"value":"fictional","state":"SOURCE_EXPLICIT","evidence_refs":[0]}
  edge=lambda k,j:{"target_key":list(k),"target_native_label":native[k]["target_native_label"],"target_locator":native[k]["target_locator"],"rationale":"Fictional rationale","evidence_refs":[0,j]}
  refs.append({**{k:s[k] for k in ("review_id","source_ref","source_scope","source_native_label","native_kind")},"source_dimensions":dims,"evidence":evidence,"independent_candidates":[{**edge(t,1),"relation":"CLOSE","direction":"SOURCE_RELATION_TO_TARGET","conditions":[],"applicability":"CONCEPT_CANDIDATE_ONLY","measurement_transfer":"HOLD"}],"hard_negatives":[{**edge(n,2),"conflict_type":"TARGET_SPECIFIC_CONDITION"}],"search_attempts":[{"target_system":k,"query_terms":["fictional"],"search_method":"fictional","result":"CANDIDATES_FOUND" if k=="FoodOn" else "NO_SUPPORTED_TARGET_IN_REVIEWED_MATERIAL"} for k in m.VERSIONS],"case_disposition":"CANDIDATE_CONCEPT_ONLY","local_concept_extension":"NOT_PROPOSED","unresolved_reasons":[],"reviewer_minutes":0,"review_status":"CRITIC_DRAFT","accepted_equivalence":False,"mapping_release_authorized":False,"scientific_reference_qualified":False,"purpose":"CURATION_DEV_ONLY"})
 return src,packet,u,native,ranks,refs
def full_fixture():
 src,packet,u,native,ranks,refs=fixture()
 files={}
 def add(path,b):
  files[path]=b;return sha(b)
 srcsha=add(m.ST/m.SOURCE,obj(src));pktsha=add(m.PACKET,obj(packet));usha=add(m.UNIVERSE,obj(u))
 schema=(ROOT/m.SCHEMA).read_bytes();scsha=add(m.ST/m.SCHEMA,schema)
 tasksha=add(m.ST/"A2ReviewTask.json",obj({"allowed_inputs":{}}))
 prep={"retrieval_packet_sha256":pktsha,"source_packet_sha256":srcsha,"dense_hint_rows":3875,"reviewer_staging_sha256":{str(m.SOURCE):srcsha,str(m.SCHEMA):scsha,"A2ReviewTask.json":tasksha}}
 prep_sha=add(m.B/"local_001/PreparationFreeze.json",obj(prep))
 runner_sha=h("fictional-runner");pol={"primary_arm":"SOURCE_SPARSE","comparators":["BASELINE_FUSION","HYBRID"],"pins":{str(m.UNIVERSE):usha,"src/u3r2p2a1/source_only_retrieval.py":runner_sha}}
 pol_sha=add(m.POLPATH,obj(pol))
 rb=b"".join(obj(x) for x in ranks);qb=b"".join(obj({"review_id":s["review_id"],"synthetic":True}) for s in src)
 outsha={"Ranks.jsonl":sha(rb),"QueryHypotheses.jsonl":sha(qb)}
 rec={"method_sha256":runner_sha,"packet_sha256":pktsha,"groups":384,"source_records":32,"reviewer_results_read":False,"mapping_release":False,"source_only":True,"output_sha256":outsha}
 for rr in m.RANKRUNS:
  add(rr/"Ranks.jsonl",rb);add(rr/"QueryHypotheses.jsonl",qb);recsha=add(rr/"RetrievalReplayReceipt.json",obj(rec))
 fr={"prep_sha256":prep_sha,"policy_sha256":pol_sha,"reference_results_read":0,"cases":32,"retrieval_run":str(m.RANKRUNS[0]),"replay_run":str(m.RANKRUNS[1]),"retrieval_output_sha256":outsha,"retrieval_receipt_sha256":recsha,"replay_receipt_sha256":recsha,"source_packet_sha256":srcsha}
 ret_sha=add(m.B/"local_001/A2RetrievalFreezeReceipt.json",obj(fr))
 rr=m.RUN/"reviewer_private/Final";case_hashes={f"case_{i+1:03d}":h(str(i)) for i in range(32)}
 fp={"ReviewRecords.jsonl":add(rr/"ReviewRecords.jsonl",b"".join(obj(x) for x in refs)),"ReviewReport.md":add(rr/"ReviewReport.md",b"Fictional only\n"),"ExecutionManifest.json":add(rr/"ExecutionManifest.json",obj({"case_freeze_hashes":case_hashes,"source_count":32,"method_sha256":m.METHOD}))}
 fp["CriticFreezeReceipt.json"]=add(rr/"CriticFreezeReceipt.json",obj({"status":"REVIEW_FROZEN","completed_cases":32,"scientific_reference_qualified":False,"mapping_release_authorized":False,"unblind_authorized":False,"comparison_executed":False,"output_file_hashes":dict(fp)}))
 final_sha=add(m.RUN/"A2FinalReferenceFreezeReceipt.json",obj({"completed_cases":32,"complete_reference_set":True,"scientific_reference_qualified":False,"comparison_executed":False,"unblind_authorized":False,"scientific_method_sha256":m.METHOD,"case_freeze_hashes":case_hashes,"final_file_hashes":fp}))
 return files,native,{"PREP":prep_sha,"POL":pol_sha,"RET":ret_sha,"FINAL":final_sha}
class TestP1(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.src,cls.packet,cls.u,cls.native,cls.ranks,cls.refs=fixture()
  cls.o,cls.e=m.universe(cls.u,set(cls.native))
  cls.ids,cls.budgets,cls.base=m.reconstruct_budgets(cls.packet,cls.src,cls.o,cls.e)
  cls.validator=Draft202012Validator(json.loads((ROOT/m.SCHEMA).read_text()))
 def rcheck(self,r):return m.validate_ranks(r,self.ids,self.budgets,self.base,self.o,self.e)
 def pcheck(self,p):return m.reconstruct_budgets(p,self.src,self.o,self.e)
 def test_01_valid_decisions(self):
  g,r,s,e,x=decisions();m.validate_rights_evidence(e,r);m.validate_decisions(g,r,s,sha(obj(e)),x)
 def test_02_missing_rights(self):
  g,r,s,e,x=decisions();r["local_development_import"]=False
  with self.assertRaises(ValueError):m.validate_decisions(g,r,s,sha(obj(e)),x)
 def test_03_rights_evidence_empty(self):
  g,r,s,e,x=decisions();e["entries"]=[]
  with self.assertRaises(ValueError):m.validate_rights_evidence(e,r)
 def test_04_evidence_wrong_custodian(self):
  g,r,s,e,x=decisions();e["custodian_id"]="other"
  with self.assertRaises(ValueError):m.validate_rights_evidence(e,r)
 def test_05_rights_evidence_hash(self):
  g,r,s,e,x=decisions()
  with self.assertRaises(ValueError):m.validate_decisions(g,r,s,h("wrong"),x)
 def test_06_no_scoring_authority(self):
  g,r,s,e,x=decisions();g["scoring_authorized"]=True
  with self.assertRaises(ValueError):m.validate_decisions(g,r,s,sha(obj(e)),x)
 def test_07_no_release(self):
  g,r,s,e,x=decisions();r["publication"]=True
  with self.assertRaises(ValueError):m.validate_decisions(g,r,s,sha(obj(e)),x)
 def test_08_expert_route_blocked(self):
  g,r,s,e,x=decisions();s["route"]=sem.OTHER_ROUTE
  with self.assertRaises(ValueError):m.validate_decisions(g,r,s,sha(obj(e)),x)
 def test_09_wrong_run(self):
  g,r,s,e,x=decisions();g["run_id"]="other"
  with self.assertRaises(ValueError):m.validate_decisions(g,r,s,sha(obj(e)),x)
 def test_10_wrong_p1_digest(self):
  g,r,s,e,x=decisions();g["p1_receipt_sha256"]=h("wrong")
  with self.assertRaises(ValueError):m.validate_decisions(g,r,s,sha(obj(e)),x)
 def test_11_pending_grant(self):
  g,r,s,e,x=decisions();g["status"]="PENDING"
  with self.assertRaises(ValueError):m.validate_decisions(g,r,s,sha(obj(e)),x)
 def test_12_missing_grant_no_read(self):
  with self.assertRaises(ValueError):m.require_auth(Path("/fictional"),"",h("p1"),read=lambda *a: self.fail("read before valid digest"))
 def test_13_failed_auth_no_consume_or_load(self):
  def fail(*a):raise ValueError("NO_AUTH")
  with self.assertRaises(ValueError):m.guarded_import(Path("/fictional"),h("g"),h("p"),authorize=fail,consume=lambda *a:self.fail("consume"),load=lambda *a:self.fail("protected read"))
 def test_14_consume_before_load(self):
  calls=[]
  def auth(*a):calls.append("auth");return {},{}
  def consume(*a):calls.append("consume")
  def load(*a):calls.append("load");return 1
  self.assertEqual(m.guarded_import(Path("/fictional"),h("g"),h("p"),authorize=auth,consume=consume,load=load),1)
  self.assertEqual(calls,["auth","consume","load"])
 def test_15_consume_failure_no_load(self):
  def consume(*a):raise FileExistsError
  with self.assertRaises(FileExistsError):m.guarded_import(Path("/fictional"),h("g"),h("p"),authorize=lambda *a:({},{}),consume=consume,load=lambda *a:self.fail("protected read"))
 def test_16_valid_real_format_synthetic(self):
  self.assertTrue(self.rcheck(self.ranks));self.assertEqual(sum(self.budgets.values()),3875);self.assertEqual(len(self.budgets),128)
  m.validate_reference_bindings(self.refs,self.src,self.validator,self.native)
 def test_17_float_budget(self):
  r=copy.deepcopy(self.ranks);r[0]["pool_budget"]=float(r[0]["pool_budget"])
  with self.assertRaises(ValueError):self.rcheck(r)
 def test_18_bool_budget(self):
  r=copy.deepcopy(self.ranks);r[0]["pool_budget"]=True
  with self.assertRaises(ValueError):self.rcheck(r)
 def test_19_unequal_budget(self):
  r=copy.deepcopy(self.ranks);r[1]["pool_budget"]+=1
  with self.assertRaises(ValueError):self.rcheck(r)
 def test_20_missing_group(self):
  with self.assertRaises(ValueError):self.rcheck(self.ranks[:-1])
 def test_21_duplicate_group(self):
  r=copy.deepcopy(self.ranks);r[-1]=r[0]
  with self.assertRaises(ValueError):self.rcheck(r)
 def test_22_wrong_identity(self):
  r=copy.deepcopy(self.ranks);r[0]["review_id"]="other"
  with self.assertRaises(ValueError):self.rcheck(r)
 def test_23_31_case(self):
  with self.assertRaises(ValueError):m.expected_sources(self.src[:-1])
 def test_24_duplicate_id(self):
  s=copy.deepcopy(self.src);s[1]["review_id"]=s[0]["review_id"]
  with self.assertRaises(ValueError):m.expected_sources(s)
 def test_25_wrong_source_packet(self):
  p=copy.deepcopy(self.packet);p["source_records"][0]["source_native_label"]="other"
  with self.assertRaises(ValueError):self.pcheck(p)
 def test_26_duplicate_hint(self):
  p=copy.deepcopy(self.packet);p["dense_rank_hints"].append(p["dense_rank_hints"][0])
  with self.assertRaises(ValueError):self.pcheck(p)
 def test_27_missing_dense_rank(self):
  p=copy.deepcopy(self.packet);p["dense_rank_hints"][0]["label_rank"]=None
  with self.assertRaises(ValueError):self.pcheck(p)
 def test_28_wrong_version(self):
  r=copy.deepcopy(self.ranks);r[0]["targets"][0][1]="other"
  with self.assertRaises(ValueError):self.rcheck(r)
 def test_29_duplicate_target(self):
  r=copy.deepcopy(self.ranks);r[0]["targets"][1]=r[0]["targets"][0]
  with self.assertRaises(ValueError):self.rcheck(r)
 def test_30_wrong_scope(self):
  r=copy.deepcopy(self.ranks);r[0]["targets"][0]=self.u["extension"][0]
  with self.assertRaises(ValueError):self.rcheck(r)
 def test_31_baseline_order(self):
  r=copy.deepcopy(self.ranks);r[0]["targets"].reverse()
  with self.assertRaises(ValueError):self.rcheck(r)
 def test_32_universe_overlap(self):
  u=copy.deepcopy(self.u);u["extension"][0]=u["original"][0]
  with self.assertRaises(ValueError):m.universe(u,set(self.native))
 def test_33_unknown_native(self):
  u=copy.deepcopy(self.u);u["original"][0][-1]="unknown"
  with self.assertRaises(ValueError):m.universe(u,set(self.native))
 def test_34_reference_order(self):
  with self.assertRaises(ValueError):m.validate_reference_bindings(self.refs[::-1],self.src,self.validator,self.native)
 def test_35_reference_locator(self):
  r=copy.deepcopy(self.refs);r[0]["independent_candidates"][0]["target_locator"]="wrong"
  with self.assertRaises(ValueError):m.validate_reference_bindings(r,self.src,self.validator,self.native)
 def test_36_reference_missing_source_anchor(self):
  r=copy.deepcopy(self.refs);r[0]["independent_candidates"][0]["evidence_refs"]=[1]
  with self.assertRaises(ValueError):m.validate_reference_bindings(r,self.src,self.validator,self.native)
 def test_37_reference_release(self):
  r=copy.deepcopy(self.refs);r[0]["mapping_release_authorized"]=True
  with self.assertRaises(ValueError):m.validate_reference_bindings(r,self.src,self.validator,self.native)
 def test_38_duplicate_json_keys(self):
  with self.assertRaises(ValueError):m.strict_json(b'{"a":1,"a":2}')
 def test_39_nonfinite(self):
  with self.assertRaises(ValueError):m.strict_json(b'{"a":NaN}')
 def test_40_snapshot_drift_symlink(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d).resolve();(p/"a").write_bytes(b"fictional");(p/"b").symlink_to(p/"a")
   self.assertEqual(m.snapshot(p,Path("a"),sha(b"fictional")),b"fictional")
   with self.assertRaises(ValueError):m.snapshot(p,Path("a"),h("wrong"))
   with self.assertRaises(ValueError):m.snapshot(p,Path("b"),sha(b"fictional"))
   with self.assertRaises(ValueError):m.snapshot(p,Path("../a"),sha(b"fictional"))
 def test_41_io_fence(self):
  root=Path("/synthetic-project");out=root/m.DEST;state,hook=m.io_gate(root,out)
  for path in (m.PACKET,m.UNIVERSE,m.RANKRUNS[0]/"Ranks.jsonl",m.RANKRUNS[1]/"QueryHypotheses.jsonl",m.RUN/"reviewer_private/Final/ReviewRecords.jsonl"):
   with self.assertRaises(PermissionError):hook("open",(str(root/path),"r",os.O_RDONLY))
  self.assertEqual(state["protected_reads"],0)
  state["committing"]=True
  hook("open",(str(out/"AuthorizationConsumed.json"),"w",os.O_WRONLY))
  with self.assertRaises(PermissionError):hook("open",(str(root/m.PACKET),"r",os.O_RDONLY))
  state["committing"]=False;state["activated"]=True
  hook("open",(str(root/m.PACKET),"r",os.O_RDONLY))
  with self.assertRaises(PermissionError):hook("open",(str(root/m.B/"agy_login_001/private"),"r",os.O_RDONLY))
  with self.assertRaises(ValueError):hook("open",(str(root/m.PACKET),"w",os.O_WRONLY))
  with self.assertRaises(PermissionError):hook("socket.connect",())
 def test_42_complete_mock_import(self):
  files,native,pins=full_fixture();events=[]
  def read(root,p,h0):
   b=files[p];self.assertEqual(sha(b),h0);events.append(p);return b
  original=m.jsonl
  def parse(b):
   self.assertTrue(all(rr/name in events for rr in m.RANKRUNS for name in ("Ranks.jsonl","QueryHypotheses.jsonl")))
   return original(b)
  with patch.multiple(m,**pins),patch.object(browser,"Standards",return_value=SimpleNamespace(by=native)),patch.object(m,"jsonl",side_effect=parse):
   z=m.guarded_import(Path("/fictional"),h("g"),h("p"),authorize=lambda *a:({},{}),consume=lambda *a:None,load=lambda root,g,c,permit:m.import_protected(root,g,c,permit,read=read))
  self.assertEqual(len(z["ranks"]),384);self.assertEqual(len(z["expected_ids"]),32);self.assertEqual(len(z["trusted_budgets"]),128)
  self.assertFalse(z["comparison_executed"]);self.assertFalse(z["scoring_authorized"])
 def test_43_replay_drift_before_parse(self):
  files,native,pins=full_fixture();files[m.RANKRUNS[1]/"Ranks.jsonl"]+=b" "
  def read(root,p,h0):
   b=files[p]
   if sha(b)!=h0:raise ValueError("PIN_DRIFT")
   return b
  with patch.multiple(m,**pins),patch.object(m,"jsonl",side_effect=AssertionError("parsed before all hashes")),patch.object(browser,"Standards",side_effect=AssertionError("read standards before hashes")):
   with self.assertRaisesRegex(ValueError,"PIN_DRIFT"):m.guarded_import(Path("/fictional"),h("g"),h("p"),authorize=lambda *a:({},{}),consume=lambda *a:None,load=lambda root,g,c,permit:m.import_protected(root,g,c,permit,read=read))
 def test_44_conservative_secondary(self):
  from score_a2 import score
  before=obj(self.refs);projected,c=sem.conservative_projection(self.refs)
  self.assertEqual(obj(self.refs),before);self.assertEqual(c,{"TARGET_SPECIFIC_CONDITION":32})
  raw,_=score(self.ranks,self.refs,self.o,self.e,self.ids,sensitivity=True)
  sec,_=score(self.ranks,projected,self.o,self.e,self.ids,sensitivity=True)
  for a,b in zip(raw["metrics"],sec["metrics"]):
   self.assertEqual(a["reference_case_denominator"],b["reference_case_denominator"]);self.assertEqual(a["reference_hit_cases"],b["reference_hit_cases"])
   self.assertEqual(a["unreviewed_edges"],b["unreviewed_edges"])
   self.assertEqual(a["negative_overlap"]-b["negative_overlap"],b["reviewed_neither_supported_nor_negative"]-a["reviewed_neither_supported_nor_negative"])
 def test_45_unresolved_other_demoted(self):
  r=copy.deepcopy(self.refs);r[0]["hard_negatives"][0]["conflict_type"]="UNRESOLVED_OTHER"
  a,c=sem.conservative_projection(r);self.assertEqual(c["UNRESOLVED_OTHER"],1);self.assertEqual(a[0]["independent_candidates"][-1]["applicability"],"UNRESOLVED")
 def test_46_no_silent_gold(self):
  r=copy.deepcopy(self.refs);p,_=sem.conservative_projection(r);self.assertTrue(all(not x["scientific_reference_qualified"] for x in p))
 def test_47_direct_loader_blocked_before_read(self):
  with self.assertRaisesRegex(ValueError,"IMPORT_PERMIT_REQUIRED"):m.import_protected(Path("/fictional"),{},{},read=lambda *a:self.fail("protected read"))
if __name__=="__main__":unittest.main(verbosity=1)
