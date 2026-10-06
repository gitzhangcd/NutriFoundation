#!/usr/bin/env python3
import json
from pathlib import Path

from nutrifoundation.ndf.d0 import ValidationContext, validate_objects

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures/ndf/d0/real_objects/NHANES_L_SEQN130378_First_D2_v0.1.json"
PREVIOUS = ROOT / "runs/NDF/D0/A2/D0_A2_Runtime_Conformance_Report_v0.1.json"
OUT = ROOT / "runs/NDF/D0/A2.1"
OUT.mkdir(parents=True, exist_ok=True)

fixture = json.loads(FIXTURE.read_text())
previous = json.loads(PREVIOUS.read_text())

report = validate_objects(
    fixture["objects"],
    ValidationContext(**fixture["context"]),
    run_id=fixture["case_id"],
)

observed = sorted({c.error_code for c in report.checks if c.error_code})
real_d2_pass = report.qualification == "PASS" and report.failed_checks == 0
previous_a2_pass = previous.get("D0_A2_gate") == "PASS"
full_gate = previous_a2_pass and real_d2_pass

payload = {
    "stage": "NDF-D0-A2.1",
    "contract_version": fixture["context"]["contract_version"],
    "case_id": fixture["case_id"],
    "subject_alias": "SUBJ-NHANES-L-0001",
    "source_cycle": "NHANES August 2021-August 2023",
    "carrier": {
        "repository": "codingman7778/nhanes",
        "path": "nhanes_23.csv",
        "git_blob_sha": "705865448b96f122a52ee2f738ff9991488a2476",
        "status": "PUBLIC_REPLICA_NOT_BYTE_VERIFIED_AGAINST_OFFICIAL_XPT_IN_CURRENT_RUNTIME",
    },
    "semantic_authority": [
        "CDC DEMO_L codebook",
        "CDC BMX_L codebook",
        "CDC BPXO_L codebook",
    ],
    "real_D2_physical_conformance": {
        "qualification": report.qualification,
        "failed_checks": report.failed_checks,
        "error_codes": observed,
        "expectation_met": real_d2_pass,
    },
    "scientific_boundaries": {
        "reference_status": "REFERENCE_PENDING",
        "evaluator_status": "PENDING",
        "scientific_claim_status": "NOT_EVALUATED",
        "clinical_case_claim": "NOT_A_REAL_CLINICAL_CASE",
        "time_mode": "EXPERIMENTALLY_DEFINED_CROSS_SECTIONAL",
    },
    "previous_D0_A2_gate": "PASS" if previous_a2_pass else "FAIL",
    "full_D0_minimum_runtime_gate": "PASS" if full_gate else "FAIL",
    "important_boundary": (
        "PASS means the first real NHANES-grounded D2 object survives the current "
        "deterministic D0 physical validators. It does not qualify the GitHub replica "
        "as an authoritative CDC byte copy, does not establish DecisionReference validity, "
        "and does not activate NDS-P1."
    ),
}

path = OUT / "D0_A2_1_First_Real_D2_Conformance_Report_v0.1.json"
path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
print(json.dumps(payload, indent=2, ensure_ascii=False))
raise SystemExit(0 if full_gate else 1)
