#!/usr/bin/env python3
"""R3.6 synthetic exception guards. No real source packet or AGY dispatch."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src/u3r2p2a2"))
import agy_r36_exception as e
v=e.v
class ExceptionGuards(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.run=Path(self.tmp.name);self.d=self.run/"exception";self.d.mkdir()
  self.case=self.run/"case_016";self.case.mkdir();(self.run/"runtime").mkdir()
  self.prompt="Fictional exact review request\n";self.ss="s"*64
  v.obj(self.case/"QueryFreeze.json",{"fixture":True})
  self.binding={"query_freeze_sha256":v.sha(self.case/"QueryFreeze.json"),"source_sha256":self.ss,"prompt_sha256":hashlib.sha256(self.prompt.encode()).hexdigest(),"original_attempts":[{"attempt":1},{"attempt":2}],"original_session_hashes":["old1","old2"],"provider_reported_prior_error":"LOCATION_FAILED_PRECONDITION_400"}
  self.c={"version":e.VERSION,"ordinal":16,"stage":"review","attempt":3,"additional_dispatch_budget":1,"original_attempt_budget":2,"timeout_seconds":210,"scientific_method_sha256":e.METHOD,"requalification_receipt_sha256":e.REQUAL,"binding":self.binding,"owner_authorization":e.OWNER_AUTH,"fourth_attempt_authorized":False,"comparison_authorized":False,"mapping_release_authorized":False,"remote_exactly_once_claimed":False}
  v.obj(self.d/"ExceptionContract.json",self.c)
  self.x={"case":self.case,"binding":self.binding,"prompt":self.prompt,"parse":lambda x:{"record":x,"review_note":"fictional"}}
 def consume(self):return e.consume(self.d,self.c,self.binding,self.case,self.run)
 def reject(self,k,val,code):
  c=copy.deepcopy(self.c);c[k]=val
  with self.assertRaisesRegex(ValueError,code):e.consume(self.d,c,self.binding,self.case,self.run)
  self.assertFalse((self.d/"AuthorizationConsumed.json").exists())
 def test_wrong_case(self):self.reject("ordinal",17,"EXCEPTION_SCOPE")
 def test_query_not_allowed(self):self.reject("stage","query","EXCEPTION_SCOPE")
 def test_fourth_attempt_not_allowed(self):self.reject("attempt",4,"EXCEPTION_SCOPE")
 def test_additional_budget_not_expandable(self):self.reject("additional_dispatch_budget",2,"EXCEPTION_SCOPE")
 def test_original_budget_not_rewritten(self):self.reject("original_attempt_budget",3,"EXCEPTION_METHOD")
 def test_timeout_unchanged(self):self.reject("timeout_seconds",300,"EXCEPTION_METHOD")
 def test_method_unchanged(self):self.reject("scientific_method_sha256","other","EXCEPTION_METHOD")
 def test_requalification_required(self):self.reject("requalification_receipt_sha256","other","EXCEPTION_METHOD")
 def test_no_comparison(self):self.reject("comparison_authorized",True,"EXCEPTION_BOUNDARY")
 def test_no_release(self):self.reject("mapping_release_authorized",True,"EXCEPTION_BOUNDARY")
 def test_no_fourth_authorization(self):self.reject("fourth_attempt_authorized",True,"EXCEPTION_BOUNDARY")
 def test_no_remote_exactly_once(self):self.reject("remote_exactly_once_claimed",True,"EXCEPTION_BOUNDARY")
 def test_owner_binding(self):self.reject("owner_authorization","unapproved","EXCEPTION_BINDING")
 def test_prompt_and_query_binding(self):
  c=copy.deepcopy(self.c);c["binding"]["prompt_sha256"]="changed"
  with self.assertRaisesRegex(ValueError,"EXCEPTION_BINDING"):e.consume(self.d,c,self.binding,self.case,self.run)
  c=copy.deepcopy(self.c);c["binding"]["query_freeze_sha256"]="changed"
  with self.assertRaisesRegex(ValueError,"EXCEPTION_BINDING"):e.consume(self.d,c,self.binding,self.case,self.run)
 def test_consumption_atomic_once(self):
  z=self.consume();h=v.sha(self.d/"AuthorizationConsumed.json")
  self.assertEqual(z,e.consumption(self.d,self.c,self.binding))
  e.check_consumed(self.d,self.c,self.binding)
  with self.assertRaisesRegex(ValueError,"EXCEPTION_ALREADY_CONSUMED"):self.consume()
  self.assertEqual(h,v.sha(self.d/"AuthorizationConsumed.json"))
 def test_existing_attempt_blocks(self):
  (self.case/"review_attempt_03").mkdir()
  with self.assertRaisesRegex(ValueError,"EXCEPTION_ATTEMPT_EXISTS"):self.consume()
 def test_existing_runtime_blocks(self):
  (self.run/"runtime/016_review_03").mkdir()
  with self.assertRaisesRegex(ValueError,"EXCEPTION_ATTEMPT_EXISTS"):self.consume()
 def test_consumption_tamper(self):
  z=self.consume();z["attempt"]=4;(self.d/"AuthorizationConsumed.json").write_text(json.dumps(z))
  with self.assertRaisesRegex(ValueError,"EXCEPTION_CONSUMPTION_BINDING"):e.check_consumed(self.d,self.c,self.binding)
 def create_terminal(self,raw,complete=True,session="new3",prompt=None):
  a=self.case/"review_attempt_03";a.mkdir()
  v.put(a/"Prompt.txt",self.prompt if prompt is None else prompt)
  l={"method_sha256":e.METHOD,"stage":"review","source_sha256":self.ss,"case_ordinal":16,"attempt":3,"prompt_sha256":v.sha(a/"Prompt.txt"),"declared_model_required":v.MODEL,"tool_permission":False}
  v.obj(a/"Launch.json",l)
  v.obj(a/"DispatchIntent.json",{"session_id_sha256":session,"model_id":v.MODEL,"prompt_sha256":v.sha(a/"Prompt.txt")})
  v.put(a/"RawResponse.txt",raw)
  v.obj(a/"Terminal.json",{"launch_sha256":v.sha(a/"Launch.json"),"status":"RESPONSE_COMPLETE" if complete else "FAILED_TERMINAL","sent":True,"rpc_returned":complete,"rpc_error_code":None,"prompt_wall_seconds":5.0 if complete else 210.1,"model_id":v.MODEL,"session_id_sha256":session,"stop_reason":"end_turn" if complete else None,"tool_updates":0,"tool_requests":0,"error":None if complete else "ACP_TIMEOUT","wall_seconds":7.0,"raw_sha256":v.sha(a/"RawResponse.txt"),"dispatch_intent_sha256":v.sha(a/"DispatchIntent.json")})
  return a
 def finish(self):
  with patch.object(e,"verify_contract",return_value=self.c),patch.object(v,"invoke",side_effect=AssertionError("NO MODEL")):
   return e.finish(self.run,self.run,self.d,self.x)
 def test_missing_terminal_never_promoted(self):
  self.consume()
  with self.assertRaisesRegex(ValueError,"EXCEPTION_UNCERTAIN_DISPATCH_STOP"):self.finish()
  self.assertFalse((self.case/"CaseFreeze.json").exists())
 def test_complete_invalid_json_holds(self):
  self.consume();a=self.create_terminal("provider error")
  z=self.finish();self.assertEqual(z["status"],"HOLD_EXCEPTION_FAILED")
  self.assertEqual(v.load(a/"Validation.json")["error"],"JSONDecodeError")
  self.assertFalse((self.case/"CaseFreeze.json").exists())
 def test_timeout_partial_json_holds(self):
  self.consume();a=self.create_terminal('{"record":"not accepted"}',False)
  z=self.finish();self.assertEqual(z["status"],"HOLD_EXCEPTION_FAILED")
  self.assertEqual(v.load(a/"Validation.json")["error"],"ACP_TIMEOUT")
  self.assertFalse((self.case/"CaseFreeze.json").exists())
 def test_session_must_be_new(self):
  self.consume();self.create_terminal('{"x":1}',session="old2")
  with self.assertRaisesRegex(ValueError,"EXCEPTION_SESSION_BINDING"):self.finish()
 def test_prompt_must_be_identical(self):
  self.consume();self.create_terminal('{"x":1}',prompt="different")
  with self.assertRaisesRegex(ValueError,"EXCEPTION_PROMPT_DRIFT"):self.finish()
 def test_valid_terminal_freezes_and_replays(self):
  self.consume();self.create_terminal('{"fictional":true}')
  z=self.finish();h=v.sha(self.case/"CaseFreeze.json")
  self.assertEqual(z["status"],"PASS_EXCEPTION_CASE_FROZEN")
  cf=v.load(self.case/"CaseFreeze.json")
  self.assertEqual(cf["review_attempt"]["attempt"],3)
  self.assertFalse(cf["scientific_reference_qualified"])
  self.assertEqual(cf["execution_exception"]["exception_contract_sha256"],v.sha(self.d/"ExceptionContract.json"))
  self.assertEqual(z,self.finish());self.assertEqual(h,v.sha(self.case/"CaseFreeze.json"))
if __name__=="__main__":unittest.main(verbosity=1)
