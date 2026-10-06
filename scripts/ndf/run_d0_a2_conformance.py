#!/usr/bin/env python3
import json
from pathlib import Path

from nutrifoundation.ndf.d0 import ValidationContext, validate_objects

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "fixtures/ndf/d0/runtime_qualification/a2_8_plus_2.json"
REAL_D1 = ROOT / "fixtures/ndf/d0/real_objects/B002-S1-001_PMid36670395.json"
OUT = ROOT / "runs/NDF/D0/A2"
OUT.mkdir(parents=True, exist_ok=True)


def context(payload):
    return ValidationContext(**payload)


suite = json.loads(SUITE.read_text())
rows = []

for fixture in suite["negative"]:
    report = validate_objects(
        fixture["objects"],
        context(fixture.get("context", {})),
        run_id=fixture["fixture_id"],
    )
    observed = sorted({c.error_code for c in report.checks if c.error_code})
    expected = sorted(fixture["expected_error_codes"])
    ok = report.qualification == "FAIL" and set(expected).issubset(observed)
    rows.append({
        "fixture_id": fixture["fixture_id"],
        "class": "negative",
        "qualification": report.qualification,
        "expected_error_codes": expected,
        "observed_error_codes": observed,
        "expectation_met": ok,
    })

for fixture in suite["positive"]:
    report = validate_objects(
        fixture["objects"],
        context(fixture.get("context", {})),
        run_id=fixture["fixture_id"],
    )
    ok = report.qualification == "PASS" and report.failed_checks == 0
    rows.append({
        "fixture_id": fixture["fixture_id"],
        "class": "positive",
        "qualification": report.qualification,
        "observed_error_codes": sorted(
            {c.error_code for c in report.checks if c.error_code}
        ),
        "expectation_met": ok,
    })

real = json.loads(REAL_D1.read_text())
real_report = validate_objects(
    real["objects"],
    context(real["context"]),
    run_id=real["case_id"],
)
real_d1_ok = (
    real_report.qualification == "PASS"
    and real["status"] == "D0_PHYSICAL_CONFORMANCE_ONLY"
)

negative_rows = [x for x in rows if x["class"] == "negative"]
positive_rows = [x for x in rows if x["class"] == "positive"]

fixture_gate = (
    len(negative_rows) == 8
    and all(x["expectation_met"] for x in negative_rows)
    and len(positive_rows) == 2
    and all(x["expectation_met"] for x in positive_rows)
)

output = {
    "stage": "NDF-D0-A2",
    "contract_version": suite["contract_version"],
    "fixture_gate": "PASS" if fixture_gate else "FAIL",
    "fixture_summary": {
        "negative_total": len(negative_rows),
        "negative_correctly_rejected": sum(x["expectation_met"] for x in negative_rows),
        "positive_total": len(positive_rows),
        "positive_correctly_accepted": sum(x["expectation_met"] for x in positive_rows),
    },
    "fixtures": rows,
    "first_real_D1_object": {
        "case_id": real["case_id"],
        "source_identity": "PMID:36670395",
        "qualification": real_report.qualification,
        "status_boundary": real["status"],
        "expectation_met": real_d1_ok,
    },
    "D0_A2_gate": "PASS" if (fixture_gate and real_d1_ok) else "FAIL",
    "full_D0_runtime_gate": "PENDING_FIRST_REAL_D2_OBJECT",
    "important_boundary": (
        "D0-A2 PASS establishes deterministic fixture qualification and first real "
        "D1 physical conformance only. It does not establish scientific qualification, "
        "reference validity, or full D0 completion; a first real D2 observation/case "
        "object remains required."
    ),
}

path = OUT / "D0_A2_Runtime_Conformance_Report_v0.1.json"
path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(output, indent=2, ensure_ascii=False))

raise SystemExit(0 if output["D0_A2_gate"] == "PASS" else 1)
