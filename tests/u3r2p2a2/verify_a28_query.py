"""Synthetic-only tests. No actual records or target references."""
import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src/u3r2p2a2"))
import a28_query as m
def fixture():
 s={"review_id":"toy","source_ref":"toy-source","source_scope":"toy","source_native_label":"烤马铃薯","native_kind":"RECIPE_REFERENCE","source_locator":{"row":1},"artifact_sha256":"a"*64,"source_anchor_ref":"toy-anchor","native_aliases":[{"text":"土豆","type":"NATIVE"}],"reference_recipe_ingredient_names":["马铃薯","油"],"context_locator":{},"context_note":"reference only","question":"toy","status":"NOT_REVIEWED"}
 return s,{"label_query":"query: 烤马铃薯","context_query":"query: 烤马铃薯 别名：土豆","state_tokens":["baked"]},{"马铃薯":"potato","土豆":"potato","烤":"baked"}
class Test(unittest.TestCase):
 def test_source_label_preserved(self):
  s,c,l=fixture();q=m.reconstruct(s,c,l);self.assertEqual(q["q0"],[c["label_query"],c["context_query"]]);self.assertTrue(all(x.startswith(c["label_query"]) for x in q["q1"]))
 def test_hypothesis_spans(self):
  s,c,l=fixture();q=m.reconstruct(s,c,l)
  for h in q["hypotheses"]:
   field=h["field"];v=s[field] if h["index"] is None else s[field][h["index"]]
   if isinstance(v,dict):v=v["text"]
   self.assertEqual(v[h["start"]:h["end"]],h["source_span"]);self.assertEqual(l[h["source_span"]],h["english_hypothesis"])
 def test_unknown_identity_not_fabricated(self):
  s,c,l=fixture();s["source_native_label"]="未知菜";s["native_aliases"]=[];s["reference_recipe_ingredient_names"]=[];c={"label_query":"query: 未知菜","context_query":"query: 未知菜","state_tokens":[]}
  q=m.reconstruct(s,c,l);self.assertEqual(q["hypotheses"],[]);self.assertTrue(all("未知菜" in x for x in q["q1"]))
 def test_recipe_role(self):
  s,c,l=fixture();q=m.reconstruct(s,c,l);self.assertEqual(q["composition_status"],"REFERENCE_RECIPE_NOT_PHYSICAL_COMPOSITION");self.assertFalse(q["accepted_equivalence"]);self.assertFalse(q["mapping_release"])
 def test_reference_field_rejected(self):
  s,c,l=fixture();s["independent_candidates"]=[]
  with self.assertRaises(ValueError):m.reconstruct(s,c,l)
 def test_rank_field_rejected(self):
  s,c,l=fixture();s["dense_rank_hints"]=[]
  with self.assertRaises(ValueError):m.reconstruct(s,c,l)
 def test_unknown_kind_rejected(self):
  s,c,l=fixture();s["native_kind"]="PHYSICAL_MEAL"
  with self.assertRaises(ValueError):m.reconstruct(s,c,l)
 def test_invalid_alias_rejected(self):
  s,c,l=fixture();s["native_aliases"]=[{"text":"x","type":"NATIVE","target_id":"bad"}]
  with self.assertRaises(ValueError):m.reconstruct(s,c,l)
 def test_history_identity_rejected(self):
  s,c,l=fixture();c["label_query"]="query: different"
  with self.assertRaises(ValueError):m.reconstruct(s,c,l)
 def test_input_immutable(self):
  s,c,l=fixture();b=copy.deepcopy((s,c,l));m.reconstruct(s,c,l);self.assertEqual((s,c,l),b)
 def test_surface_role(self):
  p,e=m.surface("Generic food",["z","a","a","b","d"],["definition"])
  self.assertEqual(p,"passage: Generic food");self.assertIn("a; b; d",e);self.assertNotIn("; z",e);self.assertIn("definition",e)
 def test_no_extra_surface(self):
  self.assertEqual(m.surface("Generic",[],[]),("passage: Generic",None))
 def test_fusion_unique_cap(self):
  self.assertEqual(len(m.fused([0,1,2],[2,1,3],2,[1,.8,.6,.4],[.4,.8,1,.6])),2)
  self.assertEqual(m.fused([0,1],[1,0],1,[1,.8],[.8,1]),[0])
if __name__=="__main__":unittest.main()
