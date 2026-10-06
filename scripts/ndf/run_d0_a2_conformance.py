#!/usr/bin/env python3
import json
from pathlib import Path

from nutrifoundation.ndf import run_fixture_suite

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "fixtures/ndf/d0_a2/Fixture_Suite_v0.1.json"
OUT = ROOT / "runs/NDF/D0/A2"
OUT.mkdir(parents=True, exist_ok=True)

suite = json.loads(SUITE.read_text())
report = run_fixture_suite(suite)

gate = (
    report["summary"]["negative_total"] == 8
    and report["summary"]["negative_correctly_rejected"] == 8
    and report["summary"]["positive_total"] == 2
    and report["summary"]["positive_correctly_accepted"] == 2
)
report["fixture_gate"] = "PASS" if gate else "FAIL"
report["important_boundary"] = (
    "This report qualifies the synthetic 8+2 runtime fixture suite only. "
    "Full D0 requires first real D1 and D2 object conformance."
)

path = OUT / "D0_A2_Fixture_Conformance_Report_v0.1.json"
path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(report, indent=2, ensure_ascii=False))
raise SystemExit(0 if gate else 1)
