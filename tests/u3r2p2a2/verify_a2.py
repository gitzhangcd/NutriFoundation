"""A2 synthetic guard tests; no actual reserved records or independent outcomes."""
import unittest,sys,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src/u3r2p2a2"))
from score_a2 import score,verify_rank_index,ARMS,SCOPES
from prepare_a2 import check_sources,SOURCE_FIELDS
def packet():
 out=[]
 for i in range(32):
  s={k:None for k in SOURCE_FIELDS};s.update(review_id=str(i),source_ref="S"+str(i),source_scope="nutridata:ingredient" if i<16 else "nutridata:dish",status="NOT_REVIEWED")
  out.append(s)
 return out
O1=("FoodOn","v","x");O2=("FoodOn","v","y");E=("FoodOn","v","ext");OUT=("FoodOn","v","outside")
U={O1,O2};V={E}
def fixture():
 ids={"A","B","C"};ranks=[]
 for i in sorted(ids):
  for s in SCOPES:
   for a in ARMS:
    t=[]
    if s=="FoodOn":t=[O1] if a=="SOURCE_SPARSE" else [O2]
    if s=="FOODON_EXTENSION" and a=="HYBRID":t=[E]
    ranks.append({"review_id":i,"scope":s,"arm":a,"pool_budget":2,"targets":[list(x) for x in t]})
 def c(t,r="EXACT",ap="CONCEPT_ONLY"):return {"target_key":list(t),"relation":r,"applicability":ap}
 refs=[{"review_id":"A","independent_candidates":[c(O1),c(OUT),c(E,"RELATED","RELATED_ONLY")],"hard_negatives":[{"target_key":list(O2)}]},
 {"review_id":"B","independent_candidates":[c(O2)],"hard_negatives":[]},
 {"review_id":"C","independent_candidates":[],"hard_negatives":[]}]
 return ranks,refs,ids
class TestA2(unittest.TestCase):
 def test_reserved_identity(self):check_sources(packet(),[])
 def test_duplicate_reserved(self):
  p=packet();p[1]["review_id"]=p[0]["review_id"]
  with self.assertRaisesRegex(ValueError,"RESERVED_CASE_CLOSURE"):check_sources(p,[])
 def test_overlap(self):
  p=packet()
  with self.assertRaisesRegex(ValueError,"DEVELOPMENT_SOURCE_OVERLAP"):check_sources(p,[p[0]])
 def test_schema_no_review(self):
  p=packet();p[0]["status"]="REVIEWED"
  with self.assertRaisesRegex(ValueError,"SOURCE_SCHEMA"):check_sources(p,[])
 def test_scope_balance(self):
  p=packet();p[0]["source_scope"]="nutridata:dish"
  with self.assertRaisesRegex(ValueError,"SOURCE_STRATA"):check_sources(p,[])
 def m(self,domain,arm,k,sensitivity=False):
  r,f,ids=fixture();d,_=score(r,f,U,V,ids,sensitivity=sensitivity)
  return next(x for x in d["metrics"] if x["domain"]==domain and x["arm"]==arm and x["k_per_scope"]==k)
 def test_reference_denominator(self):
  m=self.m("ORIGINAL","SOURCE_SPARSE",12);self.assertEqual(m["reference_case_denominator"],2);self.assertEqual(m["reference_hit_cases"],1)
 def test_outside(self):
  r,f,i=fixture();d,_=score(r,f,U,V,i);self.assertEqual(d["supported_outside_frozen_universes"],1)
 def test_negative_overlap(self):
  self.assertEqual(self.m("ORIGINAL","HYBRID",12)["negative_overlap"],1)
 def test_unreviewed_not_negative(self):
  m=self.m("ORIGINAL","SOURCE_SPARSE",12);self.assertEqual(m["negative_overlap"],0);self.assertEqual(m["unreviewed_edges"],2)
 def test_extension_separate(self):
  self.assertEqual(self.m("EXTENSION","HYBRID",12)["reference_hit_cases"],1)
 def test_related_sensitivity_null(self):
  m=self.m("EXTENSION","HYBRID",12,True);self.assertIsNone(m["reference_hit_fraction"]);self.assertEqual(m["reviewed_neither_supported_nor_negative"],1)
 def test_pair(self):
  r,f,i=fixture();d,_=score(r,f,U,V,i);x=next(x for x in d["paired_at12"] if x["domain"]=="ORIGINAL" and x["comparator"]=="HYBRID")
  self.assertEqual((x["both_hit"],x["primary_only"],x["comparator_only"],x["neither_hit"]),(0,1,1,0))
 def test_missing_ref(self):
  r,f,i=fixture()
  with self.assertRaisesRegex(ValueError,"REFERENCE_CASE_CLOSURE"):score(r,f[:-1],U,V,i)
 def test_positive_negative_conflict(self):
  r,f,i=fixture();f[0]["hard_negatives"].append({"target_key":list(O1)})
  with self.assertRaisesRegex(ValueError,"REFERENCE_POS_NEG_CLOSURE"):score(r,f,U,V,i)
 def test_rank_duplicate(self):
  r,f,i=fixture()
  with self.assertRaisesRegex(ValueError,"DUP_RANK_GROUP"):score(r+[r[0]],f,U,V,i)
 def test_rank_budget(self):
  r,f,i=fixture();x=next(x for x in r if x["targets"]);x["pool_budget"]=0
  with self.assertRaisesRegex(ValueError,"RANK_BUDGET"):score(r,f,U,V,i)
 def test_rank_outside(self):
  r,f,i=fixture();x=next(x for x in r if x["targets"]);x["targets"]=[list(OUT)]
  with self.assertRaisesRegex(ValueError,"RANK_SCOPE"):score(r,f,U,V,i)
 def test_missing_group(self):
  r,f,i=fixture()
  with self.assertRaisesRegex(ValueError,"RANK_CLOSURE"):score(r[:-1],f,U,V,i)
if __name__=="__main__":unittest.main()
