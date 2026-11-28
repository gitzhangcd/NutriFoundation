"""Synthetic tests only: no development vocabulary or source records."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src/u3r2p2"))
from run_p2_portable_v2 import query, fused_rank, route, set_lexicon
from conditional_p2_portable_v2 import assess, reorder
set_lexicon({"鸭":"duck","心":"heart","南瓜":"pumpkin","去皮":"peeled","干":"dried","煮":"cooked","汤":"soup","白菜":"cabbage","水":"water"})
def q(label,kind="INGREDIENT_REFERENCE",ingredients=None):
 return query({"source_native_label":label,"source_ref":"S","review_id":"T","native_kind":kind,"source_locator":"L","source_anchor_ref":"A","artifact_sha256":"H","reference_recipe_ingredient_names":ingredients or []})
def c(label,rank=1,route="HOLD_NEW_EDGE_R1_NOT_RUN"):
 return {"target_native_label":label,"rank":rank,"route":route}
class TestP2(unittest.TestCase):
 def test_source_trace(self):
  x=q("鸭心")
  self.assertEqual(x["identity_tokens"],["duck","heart"])
  self.assertEqual(x["label_hypotheses"][0]["source_span"],"鸭")
  self.assertEqual(x["mapping_release"],"HOLD")
 def test_untranslated(self):
  self.assertTrue(q("某未知食品")["untranslated_label_residual"])
 def test_state_kept(self):
  self.assertIn("dried",q("南瓜(干)")["qualifier_tokens"])
 def test_recipe_components(self):
  x=q("汤","RECIPE_REFERENCE",["白菜","水"])
  self.assertEqual(len(x["reference_recipe_components"]),2)
 def test_peel(self):
  self.assertIn("EXPLICIT_PEEL_CONFLICT",assess(q("南瓜(去皮)"),c("pumpkin with skin"))["potential_conflict_flags"])
 def test_species(self):
  self.assertIn("POTENTIAL_EXPLICIT_SPECIES_CONFLICT",assess(q("鸭心"),c("chicken heart"))["potential_conflict_flags"])
 def test_organ(self):
  self.assertIn("POTENTIAL_EXPLICIT_ORGAN_CONFLICT",assess(q("鸭心"),c("duck kidney"))["potential_conflict_flags"])
 def test_raw_cooked(self):
  self.assertIn("POTENTIAL_EXPLICIT_RAW_COOKED_CONFLICT",assess(q("南瓜(煮)"),c("pumpkin raw"))["potential_conflict_flags"])
 def test_unknown_not_conflict(self):
  self.assertFalse(assess(q("南瓜"),c("pumpkin raw"))["potential_conflict_flags"])
 def test_inherited(self):
  self.assertEqual(assess(q("鸭心"),c("duck heart",route="HOLD_INHERITED_R1"))["priority"],3)
 def test_recipe_not_identity(self):
  x=assess(q("汤","RECIPE_REFERENCE",["白菜"]),c("cabbage"))
  self.assertEqual(x["question_family"],"COMPONENT_RELATED_QUESTION_NOT_DISH_EQUIVALENCE")
 def test_rerank_no_drop(self):
  x=reorder(q("鸭心"),[c("chicken heart",1),c("duck heart",2)])
  self.assertEqual([r["target_native_label"] for r in x],["duck heart","chicken heart"])
  self.assertTrue(all(r["mapping_release"]=="HOLD" for r in x))
 def test_no_promotion(self):
  x=assess(q("鸭心"),c("duck heart"))
  self.assertFalse(x["accepted_equivalence"]);self.assertFalse(x["development_concept_review_authorized"])
  self.assertTrue(x["r1_revalidation_required"])
 def test_fusion_budget(self):
  x=fused_rank([("A","v","a"),("A","v","b")],[{"target_key":["A","v","c"],"label_rank":1,"context_rank":None}],2)
  self.assertEqual(len(x),2);self.assertEqual(len(set(x)),2)
 def test_new_edge_hold(self):
  self.assertEqual(route(q("鸭心"),{"native_label":"duck heart"},None),"HOLD_NEW_EDGE_R1_NOT_RUN")
if __name__=="__main__":unittest.main()
