"""Synthetic-only P2 tests, no real rank/reference/universe access."""
import copy,hashlib,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src/u3r2p2a2"))
import a26_p2_import as m
import a26_p2_score_plan as plan
import verify_a26_p1 as legacy
import a26_p2_score as sc
import inspect
def h(x):return hashlib.sha256(x.encode()).hexdigest()
def expected():return {"p1_receipt_sha256":m.P1_SHA,"legacy_import_contract_sha256":m.LEGACY_CT_SHA,"owner_direction_sha256":m.GOV_SHA,"owner_selection_sha256":m.SEL_SHA,"reference_receipt_sha256":m.FINAL,"retrieval_receipt_sha256":m.RET}
def grant():
 return {**expected(),"version":m.GRANT_VERSION,"status":"EXPLICIT_PI_AUTHORIZATION","run_id":m.DEST.name,"scope":"LOCAL_DEVELOPMENT_IMPORT_ONLY","p2_contract_sha256":h("synthetic-contract"),"p2_readiness_receipt_sha256":h("synthetic-receipt"),"owner_id":"fictional","owner_attestation":"fictional synthetic only","owner_attests_permitted_local_development_use":True,"independent_documentary_verification":False,"import_authorized":True,"scoring_authorized":False,"unblind_scope":"CONTROLLER_ONLY_NO_SCORE_NO_EXPORT","external_transfer_authorized":False,"publication_authorized":False,"commercial_use_authorized":False,"mapping_release_authorized":False}
class P2(unittest.TestCase):
 def test_owner_grant(self):m.validate_owner_grant(grant(),expected())
 def test_bad_grants(self):
  for k,v in {"owner_attests_permitted_local_development_use":False,"independent_documentary_verification":True,"owner_attestation":"","owner_id":"","scoring_authorized":True,"external_transfer_authorized":True,"publication_authorized":True,"commercial_use_authorized":True,"mapping_release_authorized":True,"import_authorized":False,"run_id":"other","scope":"other","status":"PENDING","version":"A2.6-P1-ONE-RUN-IMPORT-GRANT-v0.1","owner_direction_sha256":h("other"),"p2_contract_sha256":"bad","unblind_scope":"EXPORT"}.items():
   with self.subTest(k=k),self.assertRaises(ValueError):
    g=grant();g[k]=v;m.validate_owner_grant(g,expected())
 def test_no_read_without_digest(self):
  with self.assertRaises(ValueError):m.require_auth(Path("/fictional"),"",m.P1_SHA,read=lambda *a:self.fail("read"))
 def test_no_read_wrong_p1(self):
  with self.assertRaises(ValueError):m.require_auth(Path("/fictional"),h("g"),h("wrong"),read=lambda *a:self.fail("read"))
 def test_wrong_owner_no_protected_read(self):
  g=grant();g["owner_attests_permitted_local_development_use"]=False
  def reader(root,path,sha):
   self.assertEqual(path,m.AUTH/"ImportGrant.json");return m.canon(g)
  with self.assertRaises(ValueError):m.require_auth(Path("/fictional"),h("g"),m.P1_SHA,read=reader)
 def test_consume_failure(self):
  def fail(*a):raise FileExistsError
  with self.assertRaises(FileExistsError):m.guarded_import(Path("/fictional"),h("g"),m.P1_SHA,authorize=lambda *a:({},{}),consume=fail,load=lambda *a:self.fail("protected read"))
 def test_direct_import_denied(self):
  with self.assertRaises(ValueError):m.import_protected(Path("/fictional"),{}, {},read=lambda *a:self.fail("read"))
 def test_protected_import_identical(self):
  self.assertEqual(inspect.getsource(m.import_protected),inspect.getsource(legacy.m.import_protected))
 def test_scoring_requires_digest(self):
  with self.assertRaises(ValueError):sc.require_scoring_auth(Path("/fictional"),"",h("receipt"),read=lambda *a:self.fail("read"))
 def test_scoring_separate_grant(self):
  g={"version":sc.SCORE_VERSION,"status":"EXPLICIT_PI_SCORING_AUTHORIZATION","run_id":sc.SCORE_DEST.name,"scope":"LOCAL_DEVELOPMENT_SCORE_ONLY","owner_id":"fictional","owner_attestation":"synthetic","p2_contract_sha256":h("ct"),"p2_readiness_receipt_sha256":h("ready"),"import_receipt_sha256":h("receipt"),"import_grant_sha256":h("import grant"),"private_bundle_sha256":h("bundle"),"reference_receipt_sha256":m.FINAL,"retrieval_receipt_sha256":m.RET,"scoring_authorized":True,"external_transfer_authorized":False,"publication_authorized":False,"commercial_use_authorized":False,"mapping_release_authorized":False}
  x={"import_receipt_sha256":h("receipt"),"reference_receipt_sha256":m.FINAL,"retrieval_receipt_sha256":m.RET}
  sc.validate_scoring_grant(g,x)
  for k,v in {"scoring_authorized":False,"external_transfer_authorized":True,"publication_authorized":True,"mapping_release_authorized":True,"commercial_use_authorized":True,"scope":"IMPORT_ONLY","import_receipt_sha256":h("other"),"owner_attestation":"","version":m.GRANT_VERSION}.items():
   with self.subTest(k=k),self.assertRaises(ValueError):
    z=dict(g);z[k]=v;sc.validate_scoring_grant(z,x)
  with self.assertRaises(ValueError):sc.validate_scoring_grant(grant(),x)
 def test_scoring_consume_failure_no_bundle(self):
  def fail(*a):raise FileExistsError
  with self.assertRaises(FileExistsError):sc.guarded_score(Path("/fictional"),h("g"),h("r"),fail,read=lambda *a:self.fail("bundle read"),authorize=lambda *a:({},{}))
 def test_complete_admission_chain_synthetic_grant(self):
  # Only repository-safe manifests and code, plus in-memory synthetic grants/receipts.
  ct=(ROOT/m.P2/"A26P2AdmissionContract.json").read_bytes()
  c=m.sha_bytes(ct)
  rr=m.canon({"status":"PASS_SYNTHETIC_PREPARATION / HOLD_EXPLICIT_D04","admission_contract_sha256":c,"real_import_executed":False,"real_scores_computed":0,"synthetic_tests_passed":True})
  g=grant();g["p2_contract_sha256"]=c;g["p2_readiness_receipt_sha256"]=m.sha_bytes(rr)
  gb=m.canon(g)
  memory={m.AUTH/"ImportGrant.json":gb,m.P2/"A26P2ReadinessReceipt.json":rr}
  old=m.strict_json((ROOT/m.P1/"A26P1ImportContract.json").read_bytes())
  safe={m.P2/"A26P2AdmissionContract.json",m.GOV,m.SEL,m.P0/"A26P0QualificationReceipt.json",m.P0/"A26P0QualificationGate.json",m.P1/"A26P1EngineeringReceipt.json",m.P1/"A26P1ImportContract.json"}|set(map(Path,old["code_sha256"]))|set(map(Path,m.strict_json(ct)["new_code_sha256"]))
  reads=[]
  def read(root,path,sha):
   reads.append(path)
   self.assertTrue(path in memory or path in safe, "unexpected/protected read")
   b=memory[path] if path in memory else (ROOT/path).read_bytes()
   m.need(m.sha_bytes(b)==sha,"PIN_DRIFT");return b
  actual,contract=m.require_auth(ROOT,m.sha_bytes(gb),m.P1_SHA,read=read)
  self.assertEqual(actual,g);self.assertEqual(contract,old);self.assertTrue(safe.issubset(set(reads)))
  memory[m.P2/"A26P2ReadinessReceipt.json"]=rr+b" "
  with self.assertRaises(ValueError):m.require_auth(ROOT,m.sha_bytes(gb),m.P1_SHA,read=read)
 def test_complete_scoring_authorization_chain_synthetic_grants(self):
  ct=(ROOT/m.P2/"A26P2AdmissionContract.json").read_bytes();c=m.sha_bytes(ct)
  rr=m.canon({"status":"PASS_SYNTHETIC_PREPARATION / HOLD_EXPLICIT_D04","admission_contract_sha256":c,"synthetic_tests_passed":True})
  ig=grant();ig["p2_contract_sha256"]=c;ig["p2_readiness_receipt_sha256"]=m.sha_bytes(rr);ib=m.canon(ig);ih=m.sha_bytes(ib)
  mark=m.canon({"grant_sha256":ih,"p1_receipt_sha256":m.P1_SHA,"run_id":m.DEST.name,"scope":"LOCAL_DEVELOPMENT_IMPORT_ONLY","scoring_authorized":False})
  ir={"status":sc.IMPORT_STATUS,"admission_contract_version":m.CONTRACT_VERSION,"independent_documentary_verification":False,"owner_managed_use_attestation":True,"p1_receipt_sha256":m.P1_SHA,"grant_sha256":ih,"private_bundle_sha256":h("synthetic bundle"),"reference_receipt_sha256":m.FINAL,"retrieval_receipt_sha256":m.RET,"cases":32,"rank_groups":384,"original_universe_size":28845,"extension_universe_size":1174,"scope_budgets_verified":128,"denied_read_events":0,"comparison_executed":False,"scoring_authorized":False,"scientific_reference_qualified":False,"mapping_release":0,"authorization_consumed_sha256":m.sha_bytes(mark)}
  rb=m.canon(ir);rh=m.sha_bytes(rb)
  g={"version":sc.SCORE_VERSION,"status":"EXPLICIT_PI_SCORING_AUTHORIZATION","run_id":sc.SCORE_DEST.name,"scope":"LOCAL_DEVELOPMENT_SCORE_ONLY","owner_id":ig["owner_id"],"owner_attestation":"synthetic only","p2_contract_sha256":c,"p2_readiness_receipt_sha256":m.sha_bytes(rr),"import_receipt_sha256":rh,"import_grant_sha256":ih,"private_bundle_sha256":ir["private_bundle_sha256"],"reference_receipt_sha256":m.FINAL,"retrieval_receipt_sha256":m.RET,"scoring_authorized":True,"external_transfer_authorized":False,"publication_authorized":False,"commercial_use_authorized":False,"mapping_release_authorized":False}
  gb=m.canon(g);gh=m.sha_bytes(gb)
  memory={sc.SCORE_GRANT:gb,m.AUTH/"ImportGrant.json":ib,m.DEST/"ImportReceipt.json":rb,m.DEST/"AuthorizationConsumed.json":mark,m.P2/"A26P2ReadinessReceipt.json":rr}
  safe={m.P2/"A26P2AdmissionContract.json",m.P1/"A26P1ImportContract.json"}|set(map(Path,m.strict_json(ct)["new_code_sha256"]))|{Path(x) for x in ("src/u3r2p2a2/score_a2.py","src/u3r2/compare_reference.py","src/u3r2p2a2/a26_p1_semantic_policy.py")}
  def read(root,path,sha):
   self.assertTrue(path in memory or path in safe,"unexpected/protected read")
   b=memory[path] if path in memory else (ROOT/path).read_bytes()
   m.need(m.sha_bytes(b)==sha,"PIN_DRIFT");return b
  actual,receipt=sc.require_scoring_auth(ROOT,gh,rh,read=read)
  self.assertEqual(actual,g);self.assertEqual(receipt,ir)
  g["owner_id"]="different";gb=m.canon(g);memory[sc.SCORE_GRANT]=gb
  with self.assertRaises(ValueError):sc.require_scoring_auth(ROOT,m.sha_bytes(gb),rh,read=read)
 def test_three_reports(self):
  src,packet,u,native,ranks,refs=legacy.fixture()
  # Fabricate exactly the prespecified counts, not any actual data.
  for i,r in enumerate(refs):
   n=2 if i<25 else 1
   if i==0:n=3
   for j in range(n):
    x=copy.deepcopy(r["hard_negatives"][0]);x["target_key"]=u["original"][j+2]
    if i==0 and j==2:x["conflict_type"]="UNRESOLVED_OTHER"
    r["hard_negatives"].append(x)
  self.assertEqual(sum(len(r["hard_negatives"]) for r in refs),90)
  # 32+50+7+1=90; remove one conditional label.
  refs[-1]["hard_negatives"].pop()
  b={"version":"A2.6-P1-SEALED-IMPORT-v0.1","semantic_route":plan.ROUTE,"expected_ids":[s["review_id"] for s in src],"ranks":ranks,"references":refs,**u,"comparison_executed":False,"scoring_authorized":False,"mapping_release":False}
  before=copy.deepcopy(b);a,p=plan.score_three(b)
  self.assertEqual(b,before);self.assertEqual(tuple(a["reports"]),plan.REPORTS);self.assertEqual(a["conservative_demotions"],plan.DEMOTIONS)
  self.assertEqual(a["reports"]["RAW_PRIMARY"]["metrics"],legacy_score(b))
  for x,y in zip(a["reports"]["RAW_NONRELATED"]["metrics"],a["reports"]["CONSERVATIVE_SECONDARY"]["metrics"]):
   for k in ("reference_case_denominator","reference_hit_cases","candidate_edges","unreviewed_edges","reference_edges_hit"):self.assertEqual(x[k],y[k])
   self.assertGreaterEqual(x["negative_overlap"],y["negative_overlap"])
  self.assertEqual(sum(len(x) for x in p.values()),2880)
  bad=copy.deepcopy(b);bad["references"][0]["hard_negatives"].pop()
  with self.assertRaises(ValueError):plan.score_three(bad)
def legacy_score(b):
 from score_a2 import score
 return score(b["ranks"],b["references"],set(map(tuple,b["original"])),set(map(tuple,b["extension"])),b["expected_ids"])[0]["metrics"]
if __name__=="__main__":unittest.main()
