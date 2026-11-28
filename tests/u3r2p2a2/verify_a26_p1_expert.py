#!/usr/bin/env python3
"""P1 expert envelope and actual authorization-chain tests: fictional inputs only."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src/u3r2p2a2"))
from verify_a26_p1 import fixture,decisions,obj,sha,h
import a26_p1_import as imp
import a26_p1_expert as ex
from unittest.mock import patch
from jsonschema import Draft202012Validator
class TestExpert(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=fixture()[-1][0]
  cls.schema=json.loads((ROOT/"schemas/udf/u3r2/A26P1ExpertAdjudication_v0.1.schema.json").read_text())
  Draft202012Validator.check_schema(cls.schema);cls.validator=Draft202012Validator(cls.schema)
 def setUp(self):
  self.original=copy.deepcopy(type(self).original);self.queue={"ordinal":1,"reference_record_sha256":h("record"),"dimensions":[{"dimension":k} for k in ex.DIMS],"edges":[{"field":f,"zero_based_index":i} for f in ("independent_candidates","hard_negatives") for i,_ in enumerate(self.original[f])]}
  self.task={"task_id":"B2-U3R2-REF32-A26-P1-EXPERT","source_packet_sha256":h("source"),"phase_a":{"allowed_inputs":{"fictional":h("input")}}}
  self.phase_a=h("phase-a");self.r={"version":"A2.6-P1-EXPERT-ADJUDICATION-v0.1","task_id":self.task["task_id"],"phase":"B_REFERENCE_ADJUDICATION","reviewer_id":"fictional-expert","qualification_basis":"Fictional","conflict_of_interest":"None in fictional test","prior_exposure":"Fictional","source_only_freeze_sha256":self.phase_a,"case_ordinal":1,"source_packet_sha256":self.task["source_packet_sha256"],"reference_record_sha256":self.queue["reference_record_sha256"],"items":[],"overall_disposition":"UNRESOLVED","signed_attestation":"Synthetic","no_rank_access":True,"scientific_release_authorized":False}
  for k in ex.expected_items(self.queue):
   self.r["items"].append({"field":k[0],"item_key":k[1],"decision":"UNRESOLVED","reason_code":"INSUFFICIENT_SOURCE","rationale":"Fictional uncertainty","evidence":[],"proposed_judgment":None,"measurement_transfer":"HOLD"})
 def item(self,field,k):return next(x for x in self.r["items"] if x["field"]==field and x["item_key"]==k)
 def check(self):return ex.validate_phase_b(self.r,self.queue,self.original,self.phase_a,self.task,self.validator,"fictional-expert")
 def accept(self,field,k,ix,reason="SUPPORTED_BY_BOTH_SIDES"):
  d=self.item(field,k);d.update(decision="ACCEPT",reason_code=reason,evidence=[self.original["evidence"][j] for j in ix]);return d
 def test_complete_unknown_preserved(self):
  z=self.check();self.assertEqual(z["items_verified"],10);self.assertFalse(z["scientific_truth_validated"])
 def test_missing_item(self):
  self.r["items"].pop()
  with self.assertRaises(ValueError):self.check()
 def test_duplicate_item(self):
  self.r["items"][-1]=self.r["items"][0]
  with self.assertRaises(ValueError):self.check()
 def test_wrong_phase_a(self):
  self.r["source_only_freeze_sha256"]=h("wrong")
  with self.assertRaises(ValueError):self.check()
 def test_wrong_reference(self):
  self.r["reference_record_sha256"]=h("wrong")
  with self.assertRaises(ValueError):self.check()
 def test_fabricated_evidence(self):
  d=self.accept("independent_candidates","0",[0,1]);d["evidence"]=[dict(d["evidence"][0],observation="invented"),d["evidence"][1]]
  with self.assertRaises(ValueError):self.check()
 def test_correct_double_anchor(self):
  self.accept("independent_candidates","0",[0,1]);self.assertEqual(self.check()["decisions"]["ACCEPT"],1)
 def test_wrong_target_anchor(self):
  self.accept("independent_candidates","0",[0,2])
  with self.assertRaises(ValueError):self.check()
 def test_unknown_condition_not_negative(self):
  self.accept("hard_negatives","0",[0,2],"UNKNOWN_CONDITION")
  with self.assertRaises(ValueError):self.check()
 def test_explicit_conflict_accept_contract(self):
  self.accept("hard_negatives","0",[0,2],"EXPLICIT_CONFLICT");self.check()
 def test_unresolved_other_not_negative(self):
  self.original["hard_negatives"][0]["conflict_type"]="UNRESOLVED_OTHER";self.accept("hard_negatives","0",[0,2],"EXPLICIT_CONFLICT")
  with self.assertRaises(ValueError):self.check()
 def test_source_from_target_rejected(self):
  d=self.accept("source_dimensions","base_food",[1]);d.update(decision="REVISE",proposed_judgment={"value":"fictional target claim","state":"SOURCE_EXPLICIT"})
  with self.assertRaises(ValueError):self.check()
 def test_related_applicability_mismatch(self):
  self.original["independent_candidates"][0]["applicability"]="RELATED_ONLY";self.accept("independent_candidates","0",[0,1])
  with self.assertRaises(ValueError):self.check()
 def test_revise_unknown_negative_separate(self):
  d=self.accept("hard_negatives","0",[0,2],"UNKNOWN_CONDITION");d.update(decision="REVISE",proposed_judgment={"edge_disposition":"REVIEWED_UNRESOLVED"});self.check()
 def test_measurement_transfer_blocked(self):
  self.r["items"][0]["measurement_transfer"]="AUTHORIZED"
  with self.assertRaises(ValueError):self.check()
 def test_phase_a_contract(self):
  rec={"version":"A2.6-P1-EXPERT-PHASE-A-FREEZE-v0.1","status":"SOURCE_ONLY_REVIEW_FROZEN","task_id":self.task["task_id"],"reviewer_id":"fictional-expert","source_packet_sha256":self.task["source_packet_sha256"],"input_hashes":self.task["phase_a"]["allowed_inputs"],"completed_cases":32,"rank_access":False,"agy_reference_access":False,"prior_risk_label_access":False,"scientific_release_authorized":False,"signed_attestation":"Synthetic","output_file_hashes":{"SourceOnlyReviewRecords.jsonl":h("rows"),"PhaseAExecutionManifest.json":h("manifest")}}
  ex.validate_phase_a_freeze(rec,self.task,"fictional-expert")
  rec["agy_reference_access"]=True
  with self.assertRaises(ValueError):ex.validate_phase_a_freeze(rec,self.task,"fictional-expert")
 def test_wrong_phase_a_reviewer(self):
  self.r["reviewer_id"]="other"
  with self.assertRaisesRegex(ValueError,"PHASE_A_REVIEWER_BINDING"):self.check()
 def test_queue_omits_original_edge(self):
  self.queue["edges"].pop();self.r["items"].pop()
  with self.assertRaisesRegex(ValueError,"EXPERT_QUEUE_ORIGINAL_CLOSURE"):self.check()
class TestAuthChain(unittest.TestCase):
 def make(self):
  g,r,s,e,_=decisions();files={}
  def add(path,x):
   b=obj(x);files[path]=b;return sha(b)
  p0=add(imp.P0/"A26P0QualificationReceipt.json",{"status":"PASS_AUDIT_EXECUTED / HOLD_SCIENTIFIC_QUALIFICATION_AND_COMPARISON","comparison_authorized":False})
  gate=add(imp.P0/"A26P0QualificationGate.json",{"status":"HOLD_SYNTHETIC"})
  a=Path("src/u3r2p2a2/score_a2.py");b=Path("src/u3r2/compare_reference.py")
  files[a]=b"fictional scorer";files[b]=b"fictional support"
  csha=add(imp.P1/"A26P1ImportContract.json",{"version":imp.CONTRACT_VERSION,"status":"ENGINEERING_READY_OWNER_AUTHORIZATION_PENDING","p0_gate_sha256":gate,"final_reference_receipt_sha256":imp.FINAL,"retrieval_receipt_sha256":imp.RET,"semantic_route":imp.ROUTE,"real_import_executed":False,"semantic_policy_sha256":s["policy_sha256"],"code_sha256":{str(a):sha(files[a]),str(b):sha(files[b])}})
  p1=add(imp.P1/"A26P1EngineeringReceipt.json",{"status":"PASS_ENGINEERING_PREPARATION / HOLD_OWNER_DECISIONS_AND_UNBLIND","p0_receipt_sha256":p0,"comparison_authorized":False,"import_contract_sha256":csha})
  g.update(p1_receipt_sha256=p1,import_contract_sha256=csha,rights_decision_sha256=add(imp.AUTH/"RightsDecision.json",r),semantic_decision_sha256=add(imp.AUTH/"SemanticDecision.json",s))
  add(imp.AUTH/"RightsEvidenceBundle.json",e);gsha=add(imp.AUTH/"ImportGrant.json",g)
  return files,{"P0_SHA":p0,"P0_GATE":gate,"SCORE":sha(files[a]),"SUPPORT_SHA":sha(files[b])},p1,gsha
 def run_auth(self,files,pins,p1,gsha):
  reads=[]
  def rd(root,path,want):
   self.assertFalse(path in (imp.PACKET,imp.UNIVERSE) or path.name in ("Ranks.jsonl","QueryHypotheses.jsonl","ReviewRecords.jsonl"))
   reads.append(path);b=files[path]
   if sha(b)!=want:raise ValueError("PIN_DRIFT")
   return b
  with patch.multiple(imp,**pins):
   g,c=imp.require_auth(Path("/fictional"),gsha,p1,read=rd)
  return g,c,reads
 def test_valid_chain_metadata_only(self):
  g,c,paths=self.run_auth(*self.make());self.assertTrue(g["import_authorized"]);self.assertGreater(len(paths),8)
 def test_wrong_grant_pin(self):
  files,pins,p1,gsha=self.make()
  with self.assertRaises(ValueError):self.run_auth(files,pins,p1,h("wrong"))
 def test_changed_rights_pin(self):
  files,pins,p1,gsha=self.make();files[imp.AUTH/"RightsDecision.json"]+=b" "
  with self.assertRaises(ValueError):self.run_auth(files,pins,p1,gsha)
 def test_changed_contract_code(self):
  files,pins,p1,gsha=self.make();files[Path("src/u3r2p2a2/score_a2.py")]+=b" "
  with self.assertRaises(ValueError):self.run_auth(files,pins,p1,gsha)
if __name__=="__main__":unittest.main(verbosity=1)
