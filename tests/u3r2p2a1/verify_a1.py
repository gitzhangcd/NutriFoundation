"""Synthetic A1 guards. No real source labels, targets or reviewer outcomes."""
import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src/u3r2p2a1"))
from run_a1 import typed,translated_spans,admission,navigation_priority,r1_evaluate,check_source
from source_only_retrieval import check_packet,rank_group,SOURCE_FIELDS,HINT_FIELDS
from run_p2_portable_v2 import query,set_lexicon,toks
set_lexicon({"鹅":"goose","心":"heart","汤":"soup","白菜":"cabbage","水":"water","干":"dried"})
def src(label,kind="INGREDIENT_REFERENCE",components=None):
 return {"review_id":"R","source_ref":"S","source_scope":"X","source_native_label":label,
 "native_kind":kind,"source_locator":"L","artifact_sha256":"H","source_anchor_ref":"A","native_aliases":[],
 "reference_recipe_ingredient_names":components or [],"context_locator":"CL" if components else None,
 "context_note":"reference only","question":"source only","status":"NOT_REVIEWED"}
def q(label,kind="INGREDIENT_REFERENCE",components=None):return query(src(label,kind,components))
def policy():
 return {"whole_label_aliases":[],"role_policy":{"other_pairs":[["INGREDIENT_REFERENCE","COMPOSITION_REFERENCE"],["RECIPE_REFERENCE","COMPOSITION_REFERENCE"]]}}
def r1(s,t,sg="INGREDIENT_REFERENCE",tg="COMPOSITION_REFERENCE",scope=None,red=False):
 return r1_evaluate({"label":s,"grain":sg},{"label":t,"grain":tg},policy(),scope,red)
class TestA1(unittest.TestCase):
 def test_source_species_hypothesis(self):
  t=typed("鹅心","INGREDIENT_REFERENCE","A",q=q("鹅心"))
  self.assertEqual(t["species"]["status"],"BILINGUAL_HYPOTHESIS_NOT_VERIFIED")
  self.assertEqual(t["species"]["value"][0]["source_span"],"鹅")
 def test_edible_part_hypothesis(self):
  self.assertEqual(typed("鹅心","INGREDIENT_REFERENCE","A",q=q("鹅心"))["edible_part"]["value"][0]["candidate_mentions"],["heart"])
 def test_target_literal_span(self):
  t=typed("Goose heart","COMPOSITION_REFERENCE","L")
  s=t["species"]["value"][0];self.assertEqual("Goose heart"[s["start"]:s["end"]],s["surface"])
  self.assertFalse(t["verified_physical_identity"])
 def test_unknown_not_negative(self):
  t=typed("unknown","COMPOSITION_REFERENCE","L")
  self.assertEqual(t["species"]["status"],"UNKNOWN")
  self.assertEqual(t["cooking_state"]["status"],"UNKNOWN")
 def test_negation_not_current_fried(self):
  t=typed("not fried food","COMPOSITION_REFERENCE","L")
  self.assertIn("NOT_FRIED",t["negations"]["value"])
  self.assertNotIn("fried",t["processing"]["value"])
 def test_origin_not_current_raw(self):
  t=typed("prepared from raw food","COMPOSITION_REFERENCE","L")
  self.assertIn("raw",t["source_origin"]["value"])
  self.assertEqual(t["cooking_state"]["value"],"UNKNOWN")
 def test_recipe_not_physical(self):
  t=typed("汤","RECIPE_REFERENCE","L",q=q("汤","RECIPE_REFERENCE",["白菜","水"]))
  self.assertEqual(t["recipe_components"]["status"],"REFERENCE_RECIPE_NOT_PHYSICAL_COMPOSITION")
  self.assertFalse(t["verified_nutrient_transfer"])
 def test_bad_span_fails(self):
  with self.assertRaisesRegex(ValueError,"TRANSLATION_SPAN_DRIFT"):translated_spans("鹅",[{"start":0,"end":1,"source_span":"鸭","english_hypothesis":"goose"}],{"goose"})
 def test_raw_cooked_r1_block(self):
  d=r1("raw fish","cooked fish")
  self.assertEqual(admission(None,d,[]),"HOLD_R1_EXPLICIT_CONFLICT")
 def test_role_block(self):
  d=r1("raw fish","raw fish",tg="UNREGISTERED")
  self.assertEqual(admission(None,d,[]),"HOLD_R1_SCOPE_OR_ROLE")
 def test_scope_block(self):
  d=r1("raw fish","raw fish",scope="HOLD_NONFOOD_OR_NONIDENTITY_ROLE")
  self.assertEqual(admission(None,d,[]),"HOLD_R1_SCOPE_OR_ROLE")
 def test_full_label_residual(self):
  d=r1("raw fish","raw fish sandwich")
  self.assertIn("UNRESOLVED_COMPLETE_LABEL_RESIDUAL",d["unresolved_conditions"])
  self.assertEqual(admission(None,d,[]),"HOLD_R1_UNRESOLVED_CONDITIONS")
 def test_prior_red_not_cleared(self):
  d=r1("raw fish","raw fish",red=True)
  self.assertFalse(d["review_eligible"])
  self.assertEqual(admission({"old":True},d,[]),"HOLD_R1_UNRESOLVED_CONDITIONS")
 def test_new_eligible_not_authorized(self):
  d=r1("raw fish","raw fish")
  self.assertTrue(d["review_eligible"])
  self.assertEqual(admission(None,d,[]),"HOLD_NEW_EDGE_RUNTIME_IDENTITY_REQUIRED")
 def test_old_eligible_shortlist_required(self):
  self.assertEqual(admission({"old":True},r1("raw fish","raw fish"),[]),"HOLD_ORIGINAL_RUNTIME_SHORTLIST_REQUIRED")
 def test_typed_hypothesis_not_release(self):
  self.assertEqual(admission(None,r1("raw fish","raw fish"),["POTENTIAL_CONFLICT"]),"HOLD_TYPED_OR_INHERITED_RISK")
 def test_release_forgery(self):
  d=r1("raw fish","raw fish");d["mapping_release"]="ALLOW"
  with self.assertRaisesRegex(ValueError,"R1_RELEASE"):admission(None,d,[])
 def test_tail_stable(self):
  z=[{"id":1,"disposition":"HOLD_R1_UNRESOLVED_CONDITIONS"},{"id":2,"disposition":"HOLD_R1_EXPLICIT_CONFLICT"},{"id":3,"disposition":"HOLD_R1_UNRESOLVED_CONDITIONS"}]
  self.assertEqual([x["id"] for x in sorted(z,key=navigation_priority)],[1,3,2])
 def packet(self):
  rs=[]
  for sc in ("FoodOn","FDC_SR_Legacy","FNDDS","FOODON_EXTENSION"):
   n=12 if sc=="FOODON_EXTENSION" else 20
   for i in range(1,n+1):rs.append({"review_id":"R","scope":sc,"target_key":[sc,"v",str(i)],"label_rank":i,"context_rank":i,"frozen_pool_rank":i,"fusion_score":1/i})
  return {"purpose":"SOURCE_ONLY_RETRIEVAL_EXPERIMENT","source_records":[src("鹅心")],"dense_rank_hints":rs,"reviewer_results_included":False,"mapping_release":False}
 def test_source_packet(self):self.assertEqual(len(check_packet(self.packet())),4)
 def test_reference_leak_rejected(self):
  z=self.packet();z["reference_results"]=[]
  with self.assertRaisesRegex(ValueError,"PACKET_FIELDS"):check_packet(z)
 def test_case_review_status_rejected(self):
  z=self.packet();z["source_records"][0]["status"]="REVIEWED"
  with self.assertRaisesRegex(ValueError,"SOURCE_FIELDS_OR_STATUS"):check_packet(z)
 def test_hidden_target_field_rejected(self):
  z=self.packet();z["dense_rank_hints"][0]["correct_answer"]=True
  with self.assertRaisesRegex(ValueError,"HINT_FIELDS_OR_SCOPE"):check_packet(z)
 def test_missing_rank_rejected(self):
  z=self.packet();z["dense_rank_hints"].pop()
  with self.assertRaisesRegex(ValueError,"DENSE_HINT_RANK_CLOSURE"):check_packet(z)
 def test_synthetic_rank_budget(self):
  old=[{"target_key":["A","v","1"],"label_rank":1,"context_rank":1,"frozen_pool_rank":1,"fusion_score":1.0}]
  docs=[{"key":("A","v","2"),"label":toks("goose heart"),"definition":set(),"aliases":[]}]
  ranks=rank_group(q("鹅心"),docs,{},old,"A")
  self.assertEqual(ranks["SOURCE_SPARSE"],[("A","v","2")])
  self.assertTrue(all(len(v)<=1 for v in ranks.values()))
if __name__=="__main__":unittest.main()
