#!/usr/bin/env python3
"""Join four independently frozen A2.8 scopes; no new inference or reference reads."""
import json,sys,collections
from pathlib import Path
from a28_prepare import B,OUT,snap,j,sha,canon,save,need,PINS,SCOPES
from a28_generate import CONTRACT,DEST,ARMS
SEGROOT=B/"candidate_recovery_segmented_001"
RECOVERY=Path("configs/udf/u3r2p2a2/A28SegmentedExecution_v0.1.json")

def merge_scope_rows(scope_rows,ids,budgets,universe):
 need(set(scope_rows)==set(SCOPES),"SEGMENT_SCOPE_CLOSURE")
 ids=set(ids);result=[];counts=collections.Counter()
 for s in SCOPES:
  seen=set()
  for r in scope_rows[s]:
   need(set(r)=={"review_id","scope","arm","pool_budget","targets"} and r["scope"]==s and r["review_id"] in ids and r["arm"] in ARMS,"SEGMENT_ROW")
   k=(r["review_id"],s,r["arm"])
   need(k not in seen,"SEGMENT_DUPLICATE");seen.add(k)
   t=[tuple(x) for x in r["targets"]];cap=budgets[r["review_id"],s]
   need(r["pool_budget"]==cap and len(t)==len(set(t))<=cap and set(t)<=universe[s],"SEGMENT_CAP_OR_TARGET")
   counts[r["arm"]]+=len(t);result.append(r)
  need(seen=={(i,s,a) for i in ids for a in ARMS},"SEGMENT_GROUP_CLOSURE")
 return result,dict(counts)

def main(contract_sha,recovery_sha,receipt_hashes):
 need(not DEST.exists(),"OUTPUT_EXISTS")
 need(set(receipt_hashes)==set(SCOPES),"FOUR_RECEIPTS_REQUIRED")
 ct=j(CONTRACT,contract_sha);rec=j(RECOVERY,recovery_sha)
 need(rec["original_contract_sha256"]==contract_sha and rec["scope_execution_only"] is True and rec["expected_total_groups"]==816,"RECOVERY")
 snap("src/u3r2p2a2/a28_generate_segment.py",rec["runner_sha256"])
 for p,h in ct["code_sha256"].items():snap(p,h)
 qrec=j(OUT/"QueryFreezeReceipt.json",ct["query_receipt_sha256"])
 q=j(OUT/"PrivateQueryViews51.json",qrec["private_query_views_sha256"])
 ids=[x["review_id"] for x in q["queries"]];need(len(ids)==len(set(ids))==51,"CASE_CLOSURE")
 budgets={(x["review_id"],x["scope"]):x["pool_budget"] for x in q["budgets"]}
 need(set(budgets)=={(i,s) for i in ids for s in SCOPES},"BUDGET_CLOSURE")
 u=j("runs/B2/U3-B/C2/R2/real_001/controller_private/FrozenTargetUniverse.json","311ce55e814aae9ea473609811b9be621f42d52bf2eedf68fcca610adb6f8163")
 o=set(map(tuple,u["original"]));e=set(map(tuple,u["extension"]))
 need(len(o)==28845 and len(e)==1174 and not o&e,"UNIVERSE")
 by={s:{t for t in o if t[0]==s} for s in SCOPES[:3]};by[SCOPES[3]]=e
 rows={};stats={};segment_receipts={};qt=None;runtime=0
 for s in SCOPES:
  folder=SEGROOT/s
  r=j(folder/"ScopeFreezeReceipt.json",receipt_hashes[s])
  need(r["status"]=="PASS_SINGLE_SCOPE_RANK_FREEZE" and r["scope"]==s and r["contract_sha256"]==contract_sha and r["recovery_contract_sha256"]==recovery_sha and r["query_receipt_sha256"]==ct["query_receipt_sha256"] and r["rank_groups"]==204 and r["cases"]==51,"SEGMENT_RECEIPT")
  need(r["reference_outputs_read"]==r["historical_rank_outputs_read"]==r["application_io_denials"]==r["mapping_release"]==0,"SEGMENT_SCOPE")
  for p,h in r["input_sha256"].items():snap(p,h)
  rows[s]=[json.loads(x) for x in snap(folder/"PrivateRanks.jsonl",r["rank_sha256"]).splitlines()]
  need(len(rows[s])==204 and set(r["target_stats"])=={s},"SEGMENT_ROWS")
  stats[s]=r["target_stats"][s];runtime+=r["runtime_seconds"]
  if qt is None:qt=r["query_truncation"]
  else:need(qt==r["query_truncation"],"QUERY_TRUNCATION_DRIFT")
  segment_receipts[s]=receipt_hashes[s]
 ranks,counts=merge_scope_rows(rows,ids,budgets,by);need(len(ranks)==816,"GLOBAL_GROUP_CLOSURE")
 for p,h in PINS.items():need(sha(Path(p).read_bytes())==h,"POST_INPUT_DRIFT")
 DEST.mkdir(mode=0o700)
 rh=save(DEST/"PrivateRanks.jsonl",b"".join(canon(x) for x in ranks))
 receipt={"version":"A2.8-CANDIDATE-RECOVERY-RECEIPT-v0.1","status":"PASS_SOURCE_ONLY_FACTORIAL_RANK_FREEZE","contract_sha256":contract_sha,"query_receipt_sha256":ct["query_receipt_sha256"],"rank_sha256":rh,"rank_groups":816,"cases":51,"scope_budgets":204,"candidate_counts":counts,"target_stats":stats,"query_truncation":qt,"runtime_seconds":round(runtime,3),"model_revision":ct["model_revision"],"input_sha256":PINS,"reference_outputs_read":0,"historical_rank_outputs_read":0,"mapping_release":0,"scientific_reference_qualified":False,"segmented_recovery_contract_sha256":recovery_sha,"segment_receipts":segment_receipts,"join_inference_calls":0,"application_io_denials":0}
 print(json.dumps({"receipt_sha256":save(DEST/"CandidateFreezeReceipt.json",receipt),"rank_groups":816,"counts":counts},ensure_ascii=False))
if __name__=="__main__":
 need(len(sys.argv)==7,"USAGE: original_contract recovery_contract FoodOn_receipt FDC_receipt FNDDS_receipt extension_receipt")
 main(sys.argv[1],sys.argv[2],dict(zip(SCOPES,sys.argv[3:])))
