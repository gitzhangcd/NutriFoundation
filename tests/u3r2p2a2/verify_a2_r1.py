"""Synthetic execution/transport guards; no real reserved case inputs."""
import sys,unittest,copy,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src/u3r2p2a2"))
from agy_r1_transport import table,project,DIMS
from agy_r1_runner import put,obj,digest,read_attempt,attempt_response
from agy_synthetic_broker import sha,MODEL
from agy_raw_standard_browser import S
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2]
SCHEMA=json.loads((ROOT/"schemas/udf/u3r2/R2ReferenceReview_v0.1.schema.json").read_text())
def fixture():
 s={"review_id":"SYNTH","source_ref":"synthetic@"+("a"*64),"source_scope":"fixture","source_native_label":"synthetic food","native_kind":"INGREDIENT_REFERENCE","artifact_sha256":"a"*64,"source_locator":{"row":1},"native_aliases":[],"reference_recipe_ingredient_names":[],"context_note":"fixture only"}
 r={"target_key":["FoodOn","2026-09-20","urn:synthetic"],"target_native_label":"synthetic food class","target_locator":"fixture#1","artifact_sha256":"b"*64}
 q={k:["term"] for k in S};q["FoodOn"].append("alias")
 h={k:{"term":[]} for k in S};h["FoodOn"]={"term":[r],"alias":[copy.deepcopy(r)]}
 z={"dimensions":{k:{"value":None,"state":"UNRESOLVED","evidence_refs":[]} for k in DIMS},"candidates":[],"negatives":[],"search_results":{k:"NO_SUPPORTED_TARGET_IN_REVIEWED_MATERIAL" for k in S},"disposition":"HOLD_INSUFFICIENT_EVIDENCE","local_concept_extension":"NOT_PROPOSED","unresolved_reasons":["synthetic only"],"review_note":"fixture"}
 z["dimensions"]["base_food"]={"value":"synthetic food","state":"SOURCE_EXPLICIT","evidence_refs":[0]}
 return s,q,h,z
class TestR1(unittest.TestCase):
 def test_dedup_lossless(self):
  s,q,h,z=fixture();r,g=table(h,q);self.assertEqual(len(r),1);self.assertEqual(g["FoodOn"],{"term":[1],"alias":[1]})
 def test_target_drift(self):
  s,q,h,z=fixture();h["FoodOn"]["alias"][0]["target_locator"]="bad"
  with self.assertRaisesRegex(ValueError,"DUPLICATE_TARGET_DRIFT"):table(h,q)
 def test_exact_schema_projection(self):
  s,q,h,z=fixture();r=project(z,s,q,h)["records"][0]
  Draft202012Validator(SCHEMA).validate(r);self.assertEqual(r["source_ref"],s["source_ref"]);self.assertEqual(r["search_attempts"][0]["query_terms"],q["FoodOn"])
 def candidate(self,z):
  z["disposition"]="CANDIDATE_CONCEPT_ONLY";z["candidates"]=[{"row":1,"relation":"CLOSE","conditions":[],"rationale":"fixture judgment","applicability":"CONCEPT_CANDIDATE_ONLY","evidence_refs":[0,1]}]
 def test_scientific_fields_preserved(self):
  s,q,h,z=fixture();self.candidate(z);r=project(z,s,q,h)["records"][0];Draft202012Validator(SCHEMA).validate(r)
  v=r["independent_candidates"][0]
  for k in ["relation","conditions","rationale","applicability"]:self.assertEqual(v[k],z["candidates"][0][k])
  self.assertEqual(v["target_locator"],h["FoodOn"]["term"][0]["target_locator"]);self.assertEqual(v["measurement_transfer"],"HOLD");self.assertFalse(r["accepted_equivalence"])
 def test_missing_evidence(self):
  s,q,h,z=fixture();self.candidate(z);z["candidates"][0]["evidence_refs"]=[0]
  with self.assertRaisesRegex(ValueError,"EDGE_TARGET_EVIDENCE_REQUIRED"):project(z,s,q,h)
 def test_wrong_index(self):
  s,q,h,z=fixture();z["dimensions"]["base_food"]["evidence_refs"]=[2]
  with self.assertRaisesRegex(ValueError,"TRANSPORT_EVIDENCE_REF"):project(z,s,q,h)
 def test_unknown_not_filled(self):
  s,q,h,z=fixture();r=project(z,s,q,h)["records"][0]
  self.assertIsNone(r["source_dimensions"]["species_variety"]["value"])
 def test_pos_neg_disjoint(self):
  s,q,h,z=fixture();self.candidate(z);z["negatives"]=[{"row":1,"conflict_type":"EXPLICIT_CONFLICT","rationale":"fixture","evidence_refs":[1]}]
  with self.assertRaisesRegex(ValueError,"POS_NEG_CONFLICT"):project(z,s,q,h)
 def test_external_requires_target(self):
  s,q,h,z=fixture();z["dimensions"]["base_food"]["state"]="EXTERNAL_SUPPORTED"
  with self.assertRaisesRegex(ValueError,"EXTERNAL_REF"):project(z,s,q,h)
 def test_atomic_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x";put(p,"first")
   with self.assertRaises(FileExistsError):put(p,"second")
   self.assertEqual(p.read_text(),"first")
 def make_attempt(self,c,kind,n,raw,status="RESPONSE_COMPLETE"):
  a=c/("%s_attempt_%02d"%(kind,n));a.mkdir();put(a/"Prompt.txt","prompt");obj(a/"Launch.json",{"method_sha256":"m","stage":kind,"source_sha256":"s","prompt_sha256":sha(a/"Prompt.txt")})
  put(a/"RawResponse.txt",raw);t={"launch_sha256":sha(a/"Launch.json"),"raw_sha256":sha(a/"RawResponse.txt"),"status":status,"model_id":MODEL,"stop_reason":"end_turn" if status=="RESPONSE_COMPLETE" else None,"tool_requests":0,"tool_updates":0,"error":None if status=="RESPONSE_COMPLETE" else "TIMEOUT"};obj(a/"Terminal.json",t);return a,t
 def test_uncertain_dispatch_stops(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d);put(a/"Prompt.txt","prompt");obj(a/"Launch.json",{"method_sha256":"m","stage":"review","source_sha256":"s","prompt_sha256":sha(a/"Prompt.txt")})
   with self.assertRaisesRegex(ValueError,"UNCERTAIN_DISPATCH_STOP"):read_attempt(a,"m","review","s")
 def test_raw_tamper(self):
  with tempfile.TemporaryDirectory() as d:
   a,t=self.make_attempt(Path(d),"review",1,'{"x":1}')
   (a/"RawResponse.txt").write_text("tampered")
   with self.assertRaisesRegex(ValueError,"PIN_DRIFT"):read_attempt(a,"m","review","s")
 def test_success_resume_no_dispatch(self):
  with tempfile.TemporaryDirectory() as d:
   c=Path(d);self.make_attempt(c,"review",1,'{"x":1}')
   def no(*a):self.fail("must not redispatch")
   z,r=attempt_response(c,"review","s","m",lambda x:x,"prompt",no,False)
   z2,r2=attempt_response(c,"review","s","m",lambda x:x,"prompt",no,False);self.assertEqual((z,r),(z2,r2))
 def test_timeout_hold_no_retry(self):
  with tempfile.TemporaryDirectory() as d:
   c=Path(d);self.make_attempt(c,"review",1,"","FAILED_TERMINAL")
   def no(*a):self.fail("must not retry")
   with self.assertRaisesRegex(ValueError,"TIMEOUT"):attempt_response(c,"review","s","m",lambda x:x,"prompt",no,False)
 def test_bounded_repair(self):
  with tempfile.TemporaryDirectory() as d:
   c=Path(d);self.make_attempt(c,"review",1,"not JSON");calls=[]
   def inv(kind,n,p):
    calls.append(n);return self.make_attempt(c,kind,n,'{"x":1}')[1]
   z,r=attempt_response(c,"review","s","m",lambda x:x,"prompt",inv,False)
   self.assertEqual(calls,[2]);self.assertEqual(r["attempt"],2);self.assertEqual(z,{"x":1})
if __name__=="__main__":unittest.main()
