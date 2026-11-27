#!/usr/bin/env python3
"""Synthetic R2 reconciliation guards: no real source or model dispatch."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src/u3r2p2a2"))
import agy_r2_recovery as r
v=r.v

class R2Guards(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)
  self.case=self.root/"case_008";self.case.mkdir()
  self.a=self.case/"review_attempt_01";self.a.mkdir()
  self.d=self.root/"recovery";self.d.mkdir()
  self.mh="m"*64;self.ss="s"*64;self.prompt="synthetic exact request\n"
  v.obj(self.case/"QueryFreeze.json",{"synthetic":True})
  self.qsha=v.sha(self.case/"QueryFreeze.json")
  v.put(self.a/"Prompt.txt",self.prompt);v.put(self.a/"RawResponse.txt","")
  v.obj(self.a/"Launch.json",{"method_sha256":self.mh,"source_sha256":self.ss,"case_ordinal":8,"stage":"review","attempt":1,"tool_permission":False,"declared_model_required":v.MODEL,"prompt_sha256":v.sha(self.a/"Prompt.txt")})
  v.obj(self.a/"DispatchIntent.json",{"model_id":v.MODEL,"session_id_sha256":"old-session","prompt_sha256":v.sha(self.a/"Prompt.txt")})
  self.original=r.original_attempt(self.case,self.mh,self.ss,self.prompt,self.qsha)
  self.c={"version":r.VERSION,"method_sha256":self.mh,"ordinal":8,"stage":"review","attempt":2,"additional_dispatch_budget":1,"original":self.original,"owner_authorization":r.OWNER_AUTH,"remote_exactly_once_claimed":False,"comparison_authorized":False,"scientific_release_authorized":False}
  v.obj(self.d/"RecoveryContract.json",self.c);v.obj(self.d/"Reconciliation.json",{"status":"UNKNOWN"})
 def check(self):
  return r.original_attempt(self.case,self.mh,self.ss,self.prompt,self.qsha)
 def test_unknown_is_not_timeout(self):
  self.assertEqual(self.original["native_ACP_terminal_outcome"],"UNKNOWN");self.assertFalse((self.a/"Terminal.json").exists())
 def test_exact_prompt(self):
  with self.assertRaisesRegex(ValueError,"ORIGINAL_PROMPT_DRIFT"):r.original_attempt(self.case,self.mh,self.ss,self.prompt+"x",self.qsha)
 def test_query_pin(self):
  with self.assertRaisesRegex(ValueError,"QUERY_PIN"):r.original_attempt(self.case,self.mh,self.ss,self.prompt,"wrong")
 def test_terminal_not_fabricated_or_reconciled_if_present(self):
  v.obj(self.a/"Terminal.json",{"status":"SYNTHETIC"})
  with self.assertRaisesRegex(ValueError,"FIRST_ATTEMPT_FILE_SET"):self.check()
 def test_nonempty_original_response_holds(self):
  (self.a/"RawResponse.txt").write_text("partial")
  with self.assertRaisesRegex(ValueError,"ORIGINAL_RESPONSE_NOT_EMPTY"):self.check()
 def test_extra_original_file_holds(self):
  v.put(self.a/"unexpected.txt","x")
  with self.assertRaisesRegex(ValueError,"FIRST_ATTEMPT_FILE_SET"):self.check()
 def test_source_binding(self):
  with self.assertRaisesRegex(ValueError,"ORIGINAL_LAUNCH_SCOPE"):r.original_attempt(self.case,self.mh,"other",self.prompt,self.qsha)
 def test_wrong_case(self):
  c=copy.deepcopy(self.c);c["ordinal"]=9
  with self.assertRaisesRegex(ValueError,"AUTH_SCOPE"):r.consume(self.d,c,self.original,self.mh)
  self.assertFalse((self.d/"AuthorizationConsumed.json").exists())
 def test_wrong_stage(self):
  c=copy.deepcopy(self.c);c["stage"]="query"
  with self.assertRaisesRegex(ValueError,"AUTH_SCOPE"):r.consume(self.d,c,self.original,self.mh)
 def test_extra_budget_rejected(self):
  c=copy.deepcopy(self.c);c["additional_dispatch_budget"]=2
  with self.assertRaisesRegex(ValueError,"AUTH_SCOPE"):r.consume(self.d,c,self.original,self.mh)
 def test_changed_model_authorization_rejected(self):
  c=copy.deepcopy(self.c);c["original"]["old_session_sha256"]="different"
  with self.assertRaisesRegex(ValueError,"AUTH_BINDING"):r.consume(self.d,c,self.original,self.mh)
 def test_no_remote_exactly_once_claim(self):
  c=copy.deepcopy(self.c);c["remote_exactly_once_claimed"]=True
  with self.assertRaisesRegex(ValueError,"AUTH_BOUNDARY"):r.consume(self.d,c,self.original,self.mh)
 def test_no_scientific_release(self):
  c=copy.deepcopy(self.c);c["scientific_release_authorized"]=True
  with self.assertRaisesRegex(ValueError,"AUTH_BOUNDARY"):r.consume(self.d,c,self.original,self.mh)
 def test_consumption_once(self):
  z=r.consume(self.d,self.c,self.original,self.mh)
  h=v.sha(self.d/"AuthorizationConsumed.json")
  self.assertEqual(z,r.check_consumed(self.d,self.c,self.original,self.mh))
  with self.assertRaisesRegex(ValueError,"AUTH_ALREADY_CONSUMED"):r.consume(self.d,self.c,self.original,self.mh)
  self.assertEqual(h,v.sha(self.d/"AuthorizationConsumed.json"))
  self.assertFalse((self.a/"Terminal.json").exists())
 def test_consumed_before_dispatch_crash_not_reissued(self):
  r.consume(self.d,self.c,self.original,self.mh)
  self.assertFalse((self.case/"review_attempt_02").exists())
  with self.assertRaisesRegex(ValueError,"AUTH_ALREADY_CONSUMED"):r.consume(self.d,self.c,self.original,self.mh)
 def test_consumption_tamper_holds(self):
  z=r.consume(self.d,self.c,self.original,self.mh);z["attempt"]=3
  (self.d/"AuthorizationConsumed.json").write_text(json.dumps(z))
  with self.assertRaisesRegex(ValueError,"CONSUMPTION_BINDING"):r.check_consumed(self.d,self.c,self.original,self.mh)
 def test_pin_subset_append_only(self):
  pins=r.tree_pins(self.case);v.put(self.case/"new_receipt.json","synthetic")
  r.pin_subset(self.case,pins)
  self.assertEqual(len(r.tree_pins(self.case)),len(pins)+1)
  (self.a/"RawResponse.txt").write_text("tampered")
  with self.assertRaisesRegex(ValueError,"PIN_DRIFT"):r.pin_subset(self.case,pins)
 def test_no_symlink(self):
  (self.case/"link").symlink_to(self.a/"Prompt.txt")
  with self.assertRaisesRegex(ValueError,"PIN_SYMLINK"):r.tree_pins(self.case)
 def test_path_traversal_rejected(self):
  with self.assertRaisesRegex(ValueError,"PIN_PATH"):r.pin_subset(self.case,{"../outside":"x"})
 def test_exact_or_append_refuses_overwrite(self):
  p=self.d/"Append.json";r.exact_or_append(p,{"x":1});h=v.sha(p)
  r.exact_or_append(p,{"x":1})
  with self.assertRaisesRegex(ValueError,"APPEND_ONLY_DRIFT"):r.exact_or_append(p,{"x":2})
  self.assertEqual(v.sha(p),h)
if __name__=="__main__":unittest.main(verbosity=1)
