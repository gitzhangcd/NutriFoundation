"""v0.2 display projection and dispatch intent pin guards, synthetic only."""
import sys,unittest,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src/u3r2p2a2"))
from verify_a2_r1 import fixture
from agy_r1_transport import table,project
from agy_r1_transport_v2 import review_prompt
from agy_r1_runner_v2 import put,obj,read_attempt
from agy_synthetic_broker import sha
class TestR1V2(unittest.TestCase):
 def test_full_semantic_row_projection(self):
  s,q,h,z=fixture()
  r=h["FoodOn"]["term"][0]
  r["raw_aliases"]=["alias A"];r["raw_definition"]="synthetic definition"
  h["FoodOn"]["alias"][0]=dict(r)
  p=review_prompt(s,q,h,[])
  rows=json.loads(p.split("Raw semantic rows, columns [row,system,version,native_id,label,raw_aliases,raw_definition]:\n",1)[1])
  self.assertEqual(rows,[[1,*r["target_key"],r["target_native_label"],r["raw_aliases"],r["raw_definition"]]])
  self.assertNotIn(r["artifact_sha256"],p);self.assertNotIn(r["target_locator"],p)
  z["disposition"]="CANDIDATE_CONCEPT_ONLY"
  z["candidates"]=[{"row":1,"relation":"CLOSE","conditions":[],"rationale":"synthetic","applicability":"CONCEPT_CANDIDATE_ONLY","evidence_refs":[0,1]}]
  rec=project(z,s,q,h)["records"][0];self.assertEqual(rec["independent_candidates"][0]["target_locator"],r["target_locator"])
  self.assertEqual(rec["evidence"][1]["artifact_sha256"],r["artifact_sha256"])
 def test_dispatch_intent_tamper_fails(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d);put(a/"Prompt.txt","synthetic");obj(a/"Launch.json",{"method_sha256":"m","source_sha256":"s","stage":"review","prompt_sha256":sha(a/"Prompt.txt")})
   obj(a/"DispatchIntent.json",{"prompt_sha256":sha(a/"Prompt.txt")})
   put(a/"RawResponse.txt","");obj(a/"Terminal.json",{"launch_sha256":sha(a/"Launch.json"),"sent":True,"raw_sha256":sha(a/"RawResponse.txt"),"dispatch_intent_sha256":sha(a/"DispatchIntent.json")})
   read_attempt(a,"m","review","s")
   (a/"DispatchIntent.json").write_text("modified")
   with self.assertRaisesRegex(ValueError,"PIN_DRIFT"):read_attempt(a,"m","review","s")
if __name__=="__main__":unittest.main()
