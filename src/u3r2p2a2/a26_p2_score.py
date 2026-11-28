#!/usr/bin/env python3
"""A2.6-P2 independent local scoring authorization; one shot, no external IO.
Only an already sealed P2 import may be scored. No direct original-data reads.
Application-level guard, not a defense against a hostile same-account operator.
"""
import argparse,fcntl,json,os,re,sys
from pathlib import Path
import a26_p2_import as m
from a26_p2_score_plan import score_three
SCORE_DEST=m.B/"comparison_score_001"
SCORE_GRANT=m.AUTH/"ScoringGrant.json"
SCORE_VERSION="A2.6-P2-ONE-RUN-SCORING-GRANT-v0.1"
IMPORT_STATUS="PASS_LOCAL_IMPORT_VALIDATED_SEALED / HOLD_SEPARATE_SCORING_AUTHORIZATION"

def validate_scoring_grant(g,expected):
 m.exact_fields(g,("version","status","run_id","scope","owner_id","owner_attestation","p2_contract_sha256","p2_readiness_receipt_sha256","import_receipt_sha256","import_grant_sha256","private_bundle_sha256","reference_receipt_sha256","retrieval_receipt_sha256","scoring_authorized","external_transfer_authorized","publication_authorized","commercial_use_authorized","mapping_release_authorized"),"SCORING_GRANT_FIELDS")
 m.need(g["version"]==SCORE_VERSION and g["status"]=="EXPLICIT_PI_SCORING_AUTHORIZATION" and g["run_id"]==SCORE_DEST.name and g["scope"]=="LOCAL_DEVELOPMENT_SCORE_ONLY","SCORING_GRANT_SCOPE")
 for k,v in expected.items():m.need(m.goodsha(v) and g[k]==v,"SCORING_GRANT_PIN")
 m.need(all(m.goodsha(g[k]) for k in ("p2_contract_sha256","p2_readiness_receipt_sha256","import_grant_sha256","private_bundle_sha256")),"SCORING_GRANT_PIN")
 m.need(all(isinstance(g[k],str) and g[k].strip() for k in ("owner_id","owner_attestation")),"SCORING_OWNER")
 m.need(g["scoring_authorized"] is True and all(g[k] is False for k in ("external_transfer_authorized","publication_authorized","commercial_use_authorized","mapping_release_authorized")),"SCORING_GRANT_BOUNDARY")

def require_scoring_auth(root,grant_sha,receipt_sha,read=m.snapshot):
 m.need(m.goodsha(grant_sha) and m.goodsha(receipt_sha),"TRUSTED_SCORING_DIGEST_REQUIRED")
 def j(path,h):return m.strict_json(read(root,path,h))
 g=j(SCORE_GRANT,grant_sha)
 validate_scoring_grant(g,{"import_receipt_sha256":receipt_sha,"reference_receipt_sha256":m.FINAL,"retrieval_receipt_sha256":m.RET})
 r=j(m.DEST/"ImportReceipt.json",receipt_sha)
 m.need(r["status"]==IMPORT_STATUS and r["admission_contract_version"]==m.CONTRACT_VERSION and r["independent_documentary_verification"] is False and r["owner_managed_use_attestation"] is True and r["p1_receipt_sha256"]==m.P1_SHA and r["grant_sha256"]==g["import_grant_sha256"] and r["private_bundle_sha256"]==g["private_bundle_sha256"] and r["reference_receipt_sha256"]==m.FINAL and r["retrieval_receipt_sha256"]==m.RET,"IMPORT_RECEIPT_BINDING")
 m.need(r["cases"]==32 and r["rank_groups"]==384 and r["original_universe_size"]==28845 and r["extension_universe_size"]==1174 and r["scope_budgets_verified"]==128 and r["denied_read_events"]==0 and r["comparison_executed"] is False and r["scoring_authorized"] is False and r["scientific_reference_qualified"] is False and r["mapping_release"]==0,"IMPORT_RECEIPT_SCOPE")
 ig=j(m.AUTH/"ImportGrant.json",g["import_grant_sha256"])
 m.validate_owner_grant(ig,{"p1_receipt_sha256":m.P1_SHA,"legacy_import_contract_sha256":m.LEGACY_CT_SHA,"owner_direction_sha256":m.GOV_SHA,"owner_selection_sha256":m.SEL_SHA,"reference_receipt_sha256":m.FINAL,"retrieval_receipt_sha256":m.RET,"p2_contract_sha256":g["p2_contract_sha256"],"p2_readiness_receipt_sha256":g["p2_readiness_receipt_sha256"]})
 m.need(ig["owner_id"]==g["owner_id"],"SCORING_OWNER_BINDING")
 marker=j(m.DEST/"AuthorizationConsumed.json",r["authorization_consumed_sha256"])
 m.need(marker=={"grant_sha256":g["import_grant_sha256"],"p1_receipt_sha256":m.P1_SHA,"run_id":m.DEST.name,"scope":"LOCAL_DEVELOPMENT_IMPORT_ONLY","scoring_authorized":False},"IMPORT_CONSUMPTION")
 ct=j(m.P2/"A26P2AdmissionContract.json",g["p2_contract_sha256"])
 rr=j(m.P2/"A26P2ReadinessReceipt.json",g["p2_readiness_receipt_sha256"])
 m.need(ct["version"]==m.CONTRACT_VERSION and rr["status"]=="PASS_SYNTHETIC_PREPARATION / HOLD_EXPLICIT_D04" and rr["admission_contract_sha256"]==g["p2_contract_sha256"] and rr["synthetic_tests_passed"] is True,"SCORING_PREPARATION")
 m.need(set(ct["new_code_sha256"])=={"src/u3r2p2a2/a26_p2_import.py","src/u3r2p2a2/a26_p2_score_plan.py","src/u3r2p2a2/a26_p2_score.py","tests/u3r2p2a2/verify_a26_p2.py"},"SCORING_CODE_SET")
 for path,h in ct["new_code_sha256"].items():read(root,Path(path),h)
 legacy=j(m.P1/"A26P1ImportContract.json",m.LEGACY_CT_SHA)
 for path in ("src/u3r2p2a2/score_a2.py","src/u3r2/compare_reference.py","src/u3r2p2a2/a26_p1_semantic_policy.py"):read(root,Path(path),legacy["code_sha256"][path])
 return g,r

def guarded_score(root,grant_sha,receipt_sha,consume,read=m.snapshot,authorize=require_scoring_auth):
 g,r=authorize(root,grant_sha,receipt_sha,read)
 consume(g,r)
 bundle=m.strict_json(read(root,m.DEST/"PrivateComparisonInputBundle.json",g["private_bundle_sha256"]))
 return score_three(bundle)

def io_gate(root,out):
 state={"active":False,"committing":False,"bundle_reads":0,"denied_reads":0}
 safe={root/x for x in (SCORE_GRANT,m.AUTH/"ImportGrant.json",m.DEST/"ImportReceipt.json",m.DEST/"AuthorizationConsumed.json",m.P2/"A26P2AdmissionContract.json",m.P2/"A26P2ReadinessReceipt.json",m.P1/"A26P1ImportContract.json",m.RUN/".controller.lock")}
 def hook(event,args):
  if event in ("subprocess.Popen","os.system","os.posix_spawn","os.exec","socket.connect","socket.bind","socket.getaddrinfo"):raise PermissionError("SCORING_NO_EXTERNAL_DISPATCH")
  if event!="open" or isinstance(args[0],int):return
  path=Path(os.fsdecode(args[0])).resolve();mode=args[1] or "";flags=args[2] or 0
  writing=any(c in mode for c in "wax+") or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
  if path.is_relative_to(root):
   if writing:
    m.need((state["active"] and path.is_relative_to(out)) or (state["committing"] and path==out/"AuthorizationConsumed.json"),"SCORING_WRITE_DENIED");return
   if path in safe or path.is_relative_to(root/"src") or path.is_relative_to(root/"tests"):return
   if state["active"] and path==root/m.DEST/"PrivateComparisonInputBundle.json":state["bundle_reads"]+=1;return
   state["denied_reads"]+=1;raise PermissionError("SCORING_PROTECTED_READ_DENIED")
  if writing:raise PermissionError("SCORING_EXTERNAL_WRITE_DENIED")
  if path.is_relative_to(Path.home()) and not path.is_relative_to(Path(sys.prefix).resolve()) and not path.is_relative_to(Path(sys.base_prefix).resolve()):raise PermissionError("SCORING_EXTERNAL_HOME_READ_DENIED")
 return state,hook

def main(root,grant_sha,receipt_sha):
 root=root.resolve();out=m.secure_path(root,SCORE_DEST)
 state,hook=io_gate(root,out);sys.addaudithook(hook)
 m.need(not out.exists(),"SCORING_RUN_ALREADY_EXISTS")
 with m.secure_path(root,m.RUN/".controller.lock").open("r") as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  def consume(g,r):
   m.need(not out.exists(),"SCORING_RUN_ALREADY_EXISTS")
   out.mkdir(mode=0o700)
   state["committing"]=True
   try:m.save(out/"AuthorizationConsumed.json",m.canon({"grant_sha256":grant_sha,"import_receipt_sha256":receipt_sha,"run_id":out.name,"scope":"LOCAL_DEVELOPMENT_SCORE_ONLY"}))
   finally:state["committing"]=False
   state["active"]=True
  aggregate,private=guarded_score(root,grant_sha,receipt_sha,consume)
  m.need(state["active"] and state["bundle_reads"]==1 and state["denied_reads"]==0,"SCORING_IO_FENCE")
  files={"AggregateReports.json":m.canon(aggregate),"PrivatePerCaseReports.json":m.canon(private)}
  for name,raw in files.items():m.save(out/name,raw)
  receipt={"status":"PASS_LOCAL_DEVELOPMENT_COMPARISON","grant_sha256":grant_sha,"import_receipt_sha256":receipt_sha,"cases":32,"reports":3,"aggregate_rows":90,"paired_rows":12,"per_case_rows":2880,"output_sha256":{n:m.sha_bytes(b) for n,b in files.items()},"bundle_reads":state["bundle_reads"],"denied_read_events":state["denied_reads"],"scientific_reference_qualified":False,"scientific_precision_recall":"NOT_ESTIMABLE","comparison_executed":True,"mapping_release":0,"publication_authorized":False,"external_transfer_authorized":False}
  m.save(out/"ScoringReceipt.json",m.canon(receipt));print(json.dumps(receipt),flush=True)
if __name__=="__main__":
 sys.dont_write_bytecode=True
 p=argparse.ArgumentParser();p.add_argument("--trusted-scoring-grant-sha256",required=True);p.add_argument("--trusted-import-receipt-sha256",required=True);a=p.parse_args()
 try:main(Path.cwd(),a.trusted_scoring_grant_sha256,a.trusted_import_receipt_sha256)
 except Exception as e:
  msg=str(e);print(json.dumps({"status":"HOLD_SCORING_STOPPED","error":msg if re.fullmatch(r"[A-Z0-9_]{1,90}",msg) else type(e).__name__,"comparison_executed":False}),flush=True);raise SystemExit(2)
