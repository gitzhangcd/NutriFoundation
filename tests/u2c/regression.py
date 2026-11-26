#!/usr/bin/env python3
"""Historical regression on the immutable PR55/56/57 fixtures.
Legacy tests that create reports are directed into new, isolated verification dirs.
Only explicitly permitted old files are linked for readback; no CriticPilot paths.
"""
import argparse,copy,json,os,pathlib as P,sys,subprocess,hashlib
ROOT=P.Path(".").resolve()
sys.path.insert(0,str(P.Path(__file__).resolve().parents[2]/"src/u2c"))
from core import require,sha,blob,load,put
def main(root,out,profile):
 root=root.resolve();out=out.resolve()
 require(out.is_relative_to(root/"runs/B1/U2-C") and not out.exists(),"NEW_REGRESSION_DIRECTORY_REQUIRED")
 profile=load(profile);runs={x["stage"]:root/x["run"] for x in profile["stages"]}
 oldtests={"U2-A":("tests/b1/test_b1_contract.py","efe85bd48903cdc17faa46275d0e0fc1a427f043"),
 "U2-B":("src/b1b/test_b1b.py","e36a1e94eccd5f71d454353309cf6f1a02e0a631"),
 "U3-A":("src/b2/test_b2.py","c97e19ecce69c2de8aac18fcc26533b174bd1682")}
 for path,expected in oldtests.values():require(blob(root/path)==expected,"HISTORICAL_TEST_CODE_DRIFT")
 require(blob(root/"src/b1b/bridge.py")=="da8d6a3056cac6a13a996dcd43031ec110ced709","HISTORICAL_BRIDGE_DRIFT")
 # No legacy writes: use separate top-level run directory with a symlink only to the frozen private input tree.
 # The audited old scripts read private inputs; report outputs are siblings of private/, not written into it.
 fence={}
 def report_name(stage):return "ContractNegativeTestReport.json" if stage=="U2-A" else "ContractValidationReport.json"
 for stage,p in runs.items():
  for q in (p/"private/collection_manifest.json",p/report_name(stage)):
   fence[str(q)]=sha(q)
  if stage=="U2-B":
   for q in (p/"private/D0SharedProjection.json",p/"private/D0SharedBridgeSidecar.json",p/"SourceConsistencyAudit.json"):fence[str(q)]=sha(q)
  if stage=="U3-A":
   for q in (p/"B2RunReport.json",p/"private/ReviewSourceOnlyQueue.json",p/"private/ReviewCandidatesHidden.json",p/"private/CandidateQueryRoutes.jsonl"):fence[str(q)]=sha(q)
 out.mkdir(parents=True);stats={}
 py=sys.executable
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1")
 for stage,(path,h) in oldtests.items():
  src=runs[stage];shadow=out/stage;shadow.mkdir()
  if stage=="U2-A":
   report=shadow/"ContractValidationReport.json";cmd=[py,"-B",str(root/path),"--run",str(src),"--out",str(report)]
  else:
   (shadow/"private").symlink_to(src/"private",target_is_directory=True)
   for name in (["SourceConsistencyAudit.json"] if stage=="U2-B" else ["B2RunReport.json"]):
    with (shadow/name).open("xb") as f:f.write((src/name).read_bytes())
   report=shadow/"ContractValidationReport.json";cmd=[py,"-B",str(root/path),"--root",str(root),"--run",str(shadow)]
  r=subprocess.run(cmd,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=240)
  if r.returncode!=0:print(stage,"FAILED",r.stderr[-2000:],r.stdout[-1000:],flush=True);raise RuntimeError("HISTORICAL_TEST_FAILED:"+stage)
  a=load(report);require(a["failed"]==0,"HISTORICAL_TEST_FAILED")
  old=load(src/report_name(stage))
  require(a["total"]==old["total"] and a["passed"]==old["passed"] and a["failed"]==old["failed"],"HISTORICAL_TEST_RESULT_DRIFT")
  stats[stage]={"total":a["total"],"passed":a["passed"],"failed":a["failed"],"test_code_git_blob":h,"exit_code":r.returncode}
  print("HISTORICAL",stage,stats[stage],flush=True)
 # Original pinned D0 validator; also confirm exact bridge inverse through historical implementation.
 sys.path[:0]=[str(root/"src/b1b"),str(root/"src/b1")]
 from bridge import run_d0,reverse
 from contract import canon,ref
 p=runs["U2-B"]/"private";legacy=load(p/"D0SharedProjection.json");side=load(p/"D0SharedBridgeSidecar.json")
 back=reverse(legacy,side);expected={}
 for k in ("SourceArtifact","SourceAnchor"):
  with (runs["U2-A"]/"private/typed_collections"/(k+".jsonl")).open() as h:
   for l in h:
    o=json.loads(l);expected[ref(o)]=o
 require({ref(o):canon(o) for o in back}=={r:canon(o) for r,o in expected.items()},"HISTORICAL_BRIDGE_REVERSE_DRIFT")
 d=run_d0(root/"runs/B1/U2-B/inputs/d0_snapshot",legacy)
 stats["D0"]={"passed":d["historical_test_passed"],"total":d["historical_test_count"],"exact_bridge_roundtrip":len(back),"pinned_commit":d["pinned_commit"]}
 require(all(sha(P.Path(k))==v for k,v in fence.items()),"HISTORICAL_FILE_CHANGED")
 # Keep no symlink to a private tree in exported results. Remove only newly created links, not targets.
 for stage in ("U2-B","U3-A"):
  q=out/stage/"private";require(q.is_symlink(),"SHADOW_INPUT_LINK");q.unlink()
 report={"status":"PASS_HISTORICAL_NON_REGRESSION","historical_tests":stats,"total":sum(x["total"] for x in stats.values()),"passed":sum(x["passed"] for x in stats.values()),
         "old_report_files_unchanged":True,"scope":"historical fixture reruns; separate reports, no new scientific reference or independent Critic data"}
 put(out/"HistoricalRegressionReport.json",report);print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--root",type=P.Path,default=P.Path("."));p.add_argument("--out",type=P.Path,required=True);p.add_argument("--profile",type=P.Path,required=True);a=p.parse_args();main(a.root,a.out,a.profile)
