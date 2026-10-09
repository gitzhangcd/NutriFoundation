#!/usr/bin/env python3
"""WB-EA-P0 OFFLINE proposed-contract linter.

No Workbench runtime endpoints or real scientific/Gold evidence are exercised.
Run: python apps/workbench/ea_p0/check_contract.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "specs" / "annotation_contract.v0.1.json"
VECTORS = ROOT / "fixtures" / "conformance_cases.v0.1.json"

FLAG_TO_EXPECTED = {
    "SOURCE_NOT_ALLOWLISTED": "DENY_SOURCE_NOT_ALLOWED",
    "SOURCE_REVISION_MISMATCH": "DENY_SOURCE_REVISION_MISMATCH",
    "CANDIDATE_MISSING_ANCHOR": "BLOCK_UNVERIFIED_CANDIDATE",
    "CANDIDATE_NOT_FROZEN": "BLOCK_UNVERIFIED_CANDIDATE",
    "TRANSLATION_AS_ORIGINAL": "BLOCK_TRANSLATION_AS_SOURCE",
    "PDF_PAGE_HINT_AS_VERIFIED": "BLOCK_UNVERIFIED_PDF_LOCATOR",
    "INDEPENDENT_VIEWED_AGENT": "DENY_EXPOSURE",
    "AUTO_GOLD_PROMOTION": "BLOCK_UNAUTHORIZED_PROMOTION",
    "FUTURE_EVIDENCE": "DENY_FUTURE_EVIDENCE",
    "R0_AGENT_VIEW": "DENY_EXPOSURE",
    "R2_PREAI_AGENT_VIEW": "DENY_EXPOSURE",
}

def check_manifest(spec: dict) -> None:
    assert spec["authority"]["status"] == "PROPOSED_DESIGN_ONLY"
    assert spec["authority"]["runtime_implemented"] is False
    assert spec["authority"]["scientific_owner_signoff"] == "PENDING"
    assert spec["authority"]["source_commit"] == "54b4c2eba844f39c07575573a3e834e0bc00c261"

    kinds = spec["task_kinds"]
    assert set(kinds) == {"DECISION_CASE", "EVIDENCE_ECOSYSTEM_CASE"}
    d = kinds["DECISION_CASE"]
    assert d["profile_id"] == "NDS_R1_DECISION_CAPTURE"
    assert d["field_count"] == 19
    assert d["policy"] == "PASS_THROUGH_UNMODIFIED"
    assert d["reference_set"] == [
        "preferred", "acceptable", "conditional", "not_currently_indicated",
        "prohibited", "unsafe", "unresolved",
    ]
    e = kinds["EVIDENCE_ECOSYSTEM_CASE"]
    assert e["gold_owner"] == "INDEPENDENT_SCIENTIFIC_REFERENCE_AUTHORITY"
    assert "NDS_R1_EXISTING" not in e["allowed_workflows"]

    types = spec["source_types"]
    profiles = spec["profiles"]
    assert len(types) == len(set(types)) == 7
    assert len(profiles) == len(types)
    ids = [p["profile_id"] for p in profiles]
    mapped = [p["source_type"] for p in profiles]
    assert len(set(ids)) == len(ids) and set(mapped) == set(types)
    allowed = set(spec["science_object_candidate_types"])
    for p in profiles:
        assert p["profile_id"].startswith("WB_EA_")
        assert p["required_groups"] and len(set(p["required_groups"])) == len(p["required_groups"])
        assert p["canonical_object_candidates"]
        assert set(p["canonical_object_candidates"]).issubset(allowed)
        assert p["kill_tests"]

    assert spec["field_rules"]["unknown_source_type"] == "TYPE_UNRESOLVED_HOLD"
    assert spec["field_rules"]["auto_gold_promotion"] == "DENY"
    assert spec["fixture_policy"]["paper_5_2"]["scientific_capture"] is False
    assert spec["fixture_policy"]["paper_5_2"]["is_qualified_evidence"] is False
    assert spec["phase_boundaries"]["P0"] == "DESIGN_AND_MACHINE_READABLE_CONTRACT_ONLY"


def proposed_route(spec: dict, vector: dict) -> str:
    """Contract proposal for fixture consistency; NOT service enforcement."""
    kind = vector["task_kind"]
    stype = vector["source_type"]
    profile_id = vector["profile_id"]
    if kind not in spec["task_kinds"]:
        return "HOLD"
    if kind == "DECISION_CASE":
        if profile_id != spec["task_kinds"][kind]["profile_id"]:
            return "BLOCK_PROFILE_TASK_MISMATCH"
    else:
        if stype not in spec["source_types"]:
            return "TYPE_UNRESOLVED_HOLD"
        profiles = {x["source_type"]: x["profile_id"] for x in spec["profiles"]}
        if profile_id != profiles[stype]:
            return "BLOCK_PROFILE_TASK_MISMATCH"
    flags = vector.get("flags", [])
    assert len(flags) <= 1, "A vector must isolate one denial cause"
    if flags:
        return FLAG_TO_EXPECTED[flags[0]]
    return "DELEGATE_EXISTING_NDS_R1" if kind == "DECISION_CASE" else "ROUTE_PROPOSED"


def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    cases = json.loads(VECTORS.read_text(encoding="utf-8"))
    check_manifest(spec)
    ids = set()
    for case in cases["cases"]:
        assert case["id"] not in ids
        ids.add(case["id"])
        actual = proposed_route(spec, case)
        assert actual == case["expected"], (case["id"], actual, case["expected"])
    assert len(cases["scientific_kill_tests"]) >= 5
    for t in cases["scientific_kill_tests"]:
        assert t["expected"] == "SCIENTIFIC_REVIEW_FLAG"
        assert t["type"] in spec["source_types"]
    print(f"WB-EA-P0 proposed contract lint PASS: {len(spec['profiles'])} profiles, "
          f"{len(cases['cases'])} routing/denial vectors, "
          f"{len(cases['scientific_kill_tests'])} scientific-review flags.")
    print("SCOPE: STATIC PROPOSED CONTRACT ONLY; RUNTIME / SCIENCE / GOLD / REAL EXPERT NOT TESTED")


if __name__ == "__main__":
    main()
