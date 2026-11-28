"""Synthetic checks; no model, private cases or target reference access."""
import sys,unittest,json,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src/u3r2p2a2"))
import a28_p4_channels as m
def source():
 return {"review_id":"toy","source_ref":"toy-source","source_scope":"toy","source_native_label":"番茄炒蛋","native_kind":"RECIPE_REFERENCE","source_locator":{"row":1},"artifact_sha256":"a"*64,"source_anchor_ref":"toy-anchor","native_aliases":[{"text":"西红柿炒鸡蛋","type":"NATIVE"}],"reference_recipe_ingredient_names":["西红柿","鸡蛋"],"context_locator":{},"context_note":"toy","question":"toy","status":"NOT_REVIEWED"}
def answer():
 return {"identity":[{"q":"tomato and egg dish","e":["N"]}],"state":[{"q":"stir fried","e":["N"]}],"composition":[{"q":"tomato","e":["I1"]},{"q":"egg","e":["I2"]}],"region":[]}
def n(s):return len(s.split())+2
class Test(unittest.TestCase):
 def test_source_only_projection(self):
  s=source();p=m.evidence(s);self.assertEqual(set(p),{"source_role","evidence"});self.assertNotIn("toy-source",json.dumps(p));self.assertEqual([x["id"] for x in p["evidence"]],["N","A1","I1","I2"])
 def test_reject_reference_field(self):
  s=source();s["references"]=[] 
  with self.assertRaises(ValueError):m.evidence(s)
 def test_reject_rank_field(self):
  s=source();s["dense_rank_hints"]=[]
  with self.assertRaises(ValueError):m.evidence(s)
 def test_valid_structure(self):
  a=m.validate(json.dumps(answer()),m.evidence(source()));self.assertEqual(a["identity"][0]["status"],"RETRIEVAL_HYPOTHESIS")
 def test_unknown_anchor(self):
  a=answer();a["identity"][0]["e"]=["I9"]
  with self.assertRaises(ValueError):m.validate(json.dumps(a),m.evidence(source()))
 def test_ingredient_identity(self):
  a=answer();a["identity"][0]["e"]=["I1"]
  with self.assertRaises(ValueError):m.validate(json.dumps(a),m.evidence(source()))
 def test_ingredient_state(self):
  a=answer();a["state"][0]["e"]=["I1"]
  with self.assertRaises(ValueError):m.validate(json.dumps(a),m.evidence(source()))
 def test_no_database_id(self):
  a=answer();a["identity"][0]["q"]="FoodOn tomato"
  with self.assertRaises(ValueError):m.validate(json.dumps(a),m.evidence(source()))
 def test_no_claim(self):
  a=answer();a["identity"][0]["q"]="equivalent tomato"
  with self.assertRaises(ValueError):m.validate(json.dumps(a),m.evidence(source()))
 def test_extra_keys(self):
  a=answer();a["target_id"]="bogus"
  with self.assertRaises(ValueError):m.validate(json.dumps(a),m.evidence(source()))
 def test_duplicate_key(self):
  with self.assertRaises(ValueError):m.strict_load('{"identity":[],"identity":[]}')
 def test_fenced_json(self):
  self.assertEqual(m.strict_load("\x60\x60\x60json\n"+json.dumps(answer())+"\n\x60\x60\x60"),answer())
 def test_abstain(self):
  e=m.evidence(source());h=m.validate(json.dumps({c:[] for c in m.CHANNELS}),e);q,st=m.channel_views(h,e,["query: x","query: y"],n);self.assertTrue(st["identity_abstain"]);self.assertIsNone(q["M0"]);self.assertEqual(q["O0"],"query: x")
 def test_channel_identity(self):
  e=m.evidence(source());h=m.validate(json.dumps(answer()),e);q,st=m.channel_views(h,e,["query: x","query: y"],n);self.assertIn("tomato and egg dish",q["C"]);self.assertIsNone(q["R"]);self.assertEqual(q["O1"],"query: y")
 def test_budget(self):
  for a in m.ARMS:
   for s,k in [("FoodOn",40),("FOODON_EXTENSION",24)]:self.assertEqual(sum(x["topk"] for x in m.slot_plan(a,s).values()),k)
 def test_no_reallocation(self):
  plan=m.slot_plan("L11","FoodOn");self.assertEqual(plan["I"]["topk"],5);self.assertEqual(plan["O0"]["topk"],10)
  self.assertEqual(m.fuse("L11","FoodOn",{"O0":[("a",),("b",)]},1),[("a",)])
 def test_ranking_cap(self):
  self.assertEqual(len(m.fuse("L10","FoodOn",{"O0":[("a",),("b",)],"M0":[("b",),("c",)]},2)),2)
 def test_duplicate_target_rejected(self):
  with self.assertRaises(ValueError):m.fuse("L10","FoodOn",{"O0":[("a",),("a",)]},2)
 def test_oversized_slot_rejected(self):
  with self.assertRaises(ValueError):m.fuse("L11","FoodOn",{"I":[(str(i),) for i in range(6)]},10)
if __name__=="__main__":unittest.main()
