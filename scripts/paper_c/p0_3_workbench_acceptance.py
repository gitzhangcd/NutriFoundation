#!/usr/bin/env python3
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from nutrifoundation.workbench.p0_3 import BUILD_ID, TOKENIZER_ID

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"runs/E0.4.3/P0.3"
CAL_SHA=(OUT/"Calibration24_Source_Set_SHA256_v1.0.txt").read_text().strip()
GOLD=json.loads((ROOT/"runs/E0.4.3/P0.2.4/Gold100_Source_Set_FROZEN_v1.0.json").read_text())
CAL=json.loads((OUT/"Calibration24_Source_Set_FROZEN_v1.0.json").read_text())

cal_ids={x["candidate_id"] for x in CAL["assignments"]}
gold_ids={x["candidate_id"] for x in GOLD["assignments"]}
cal_clusters={x.get("study_identity_cluster_id") or x["candidate_id"] for x in CAL["assignments"]}
gold_clusters={x.get("study_identity_cluster_id") or x["candidate_id"] for x in GOLD["assignments"]}

checks={
  "workbench_module_present":(ROOT/"src/nutrifoundation/workbench/p0_3.py").exists(),
  "browser_UI_present":(ROOT/"paper_c/P0.3/workbench/index.html").exists(),
  "automated_test_file_present":(ROOT/"tests/test_p0_3_workbench.py").exists(),
  "calibration_n_24":len(cal_ids)==24,
  "gold100_n_100":len(gold_ids)==100,
  "zero_source_overlap":not bool(cal_ids & gold_ids),
  "zero_StudyIdentity_overlap":not bool(cal_clusters & gold_clusters),
  "calibration_hash_expected":CAL_SHA=="ec793d52a130b98aaefebdb40b85356ed88543aea2b8eff63a7fcd9f8212af33",
}
status="PASS_AUTOMATED_IMPLEMENTATION_TESTS" if all(checks.values()) else "FAIL_AUTOMATED_IMPLEMENTATION_TESTS"
report={
  "stage_id":"E0.4.3-P0.3-H0",
  "artifact":"Annotation_Workbench_Automated_Implementation_Test_Report",
  "version":"v1.0",
  "status":status,
  "build_id":BUILD_ID,
  "tokenizer_id":TOKENIZER_ID,
  "git_sha":os.environ.get("GITHUB_SHA"),
  "test_command":"pytest -q tests/test_p0_3_workbench.py",
  "pytest_reached_report_generation":True,
  "checks":checks,
  "calibration24_sha256":CAL_SHA,
  "gold100_sha256":GOLD["gold100_source_set_sha256"],
  "human_smoke_test":"NOT_RUN",
  "generated_at":datetime.now(timezone.utc).isoformat(),
  "important_boundary":"Automated implementation tests do not substitute for WB-H01..WB-H15 human browser smoke test."
}
canon=json.dumps(report,sort_keys=True,ensure_ascii=False,separators=(",",":"))
report["report_sha256"]=hashlib.sha256(canon.encode()).hexdigest()
(OUT/"P0.3_Workbench_Automated_Implementation_Test_Report_v1.0.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(report,indent=2,ensure_ascii=False))
if status!="PASS_AUTOMATED_IMPLEMENTATION_TESTS":
    raise SystemExit(1)
