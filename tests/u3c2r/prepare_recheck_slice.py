#!/usr/bin/env python3
"""Bounded R1 recheck packet: only previously unblinded C1 edges and public ontology."""
import argparse,pathlib as P,json,hashlib
def require(v,c):
 if not v:raise ValueError(c)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding="utf8"))
def lines(p):
 with p.open(encoding="utf8") as f:
  for l in f:
   if l.strip():yield json.loads(l)
def ref(o):return o["object_id"]+"@"+o["revision_id"]
def put(p,o):
 with p.open("x",encoding="utf8") as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write("\n")
def main(root,run,receipt_sha,out):
 root=root.resolve();run=run.resolve();out=out.resolve()
 require(not out.exists() and out.is_relative_to(root/"runs/B2/U3-B/C2/R1") and not out.is_relative_to(run),"NEW_R1_AUDIT_SLICE")
 receipt=run/"R1ExecutionFreezeReceipt.json";require(sha(receipt)==receipt_sha,"EXECUTION_RECEIPT")
 r=read(receipt);rp=run/"R1ExecutionReport.json";require(sha(rp)==r["report_sha256"],"REPORT_HASH")
 report=read(rp);mp=run/"controller_private/partition_manifest.json";require(sha(mp)==r["partition_manifest_sha256"],"PARTITION_MANIFEST")
 old=root/"runs/B2/U3-B/C2/audit_slice_001/private"
 old_edges=read(old/"Exposed44RiskAuditSlice.json");old_scope=read(old/"FoodOnScopeAuditSlice.json")
 edge={ref(x["c2_assessment"]):x for x in old_edges};require(len(edge)==355,"OLD_EDGE_COUNT")
 ids={x["payload"]["iri"] for x in old_scope};ids.update(x["iri"] for x in report["scope_and_risk"]["scope"]["foodon_prefix_exclusion_probes"])
 result=[];s=[];seen=set()
 for rel,v in sorted(read(mp).items()):
  if not rel.endswith(("/VerifiedRiskOverlay.jsonl","/VerifiedScopeOverlay.jsonl")):continue
  f=run/"controller_private/typed_partitions"/rel;require(sha(f)==v["sha256"],"PARTITION_HASH")
  for o in lines(f):
   p=o["payload"]
   if o["kind"]=="VerifiedScopeOverlay":
    if p["iri"] in ids:s.append(o)
   elif p["cohort"]=="U3A_EXPOSED_44":
    k=p["prior_risk_ref"];require(k in edge and k not in seen,"EXPOSED_SCOPE")
    seen.add(k);result.append({"old":edge[k],"r1":o})
 require(seen==set(edge) and {x["payload"]["iri"] for x in s}==ids,"R1_SLICE_CLOSURE")
 out.mkdir(parents=True);p=out/"private";p.mkdir()
 put(p/"Exposed44R1RegressionSlice.json",result);put(p/"R1ScopeRegressionSlice.json",s)
 report={"status":"PASS_R1_BOUNDED_RECHECK_PREPARATION","prior_exposed_edges":len(result),"public_scope_probes":len(s),"new_independent_queue_records_disclosed":0,"new_hidden_candidates_disclosed":0,"slice_hashes":{x.name:sha(x) for x in p.iterdir()},"purpose":"targeted implementation recheck, not a new semantic quality estimate"}
 put(out/"R1AuditSliceReport.json",report);print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=P.Path,default=P.Path("."));p.add_argument("--run",type=P.Path,required=True);p.add_argument("--receipt-sha",required=True);p.add_argument("--out",type=P.Path,required=True);x=p.parse_args();main(x.root,x.run,x.receipt_sha,x.out)
