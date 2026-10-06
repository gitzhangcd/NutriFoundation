import json
from pathlib import Path

from nutrifoundation.ndf.d0 import ValidationContext, validate_objects

ROOT = Path(__file__).resolve().parents[2]


def _context(payload):
    return ValidationContext(**payload)


def test_eight_negative_fixtures_detect_expected_failure_classes():
    suite = json.loads(
        (ROOT / "fixtures/ndf/d0/runtime_qualification/a2_8_plus_2.json").read_text()
    )
    for fixture in suite["negative"]:
        report = validate_objects(
            fixture["objects"], _context(fixture.get("context", {})),
            run_id=fixture["fixture_id"],
        )
        observed = {c.error_code for c in report.checks if c.error_code}
        assert set(fixture["expected_error_codes"]).issubset(observed), (
            fixture["fixture_id"], fixture["expected_error_codes"], sorted(observed)
        )
        assert report.qualification == "FAIL"


def test_two_positive_fixtures_pass_without_unexpected_errors():
    suite = json.loads(
        (ROOT / "fixtures/ndf/d0/runtime_qualification/a2_8_plus_2.json").read_text()
    )
    for fixture in suite["positive"]:
        report = validate_objects(
            fixture["objects"], _context(fixture.get("context", {})),
            run_id=fixture["fixture_id"],
        )
        assert report.qualification == "PASS", report.to_dict()
        assert report.failed_checks == 0


def test_first_real_object_is_d0_conformant_only():
    fixture = json.loads(
        (ROOT / "fixtures/ndf/d0/real_objects/B002-S1-001_PMid36670395.json").read_text()
    )
    report = validate_objects(
        fixture["objects"], _context(fixture["context"]), run_id=fixture["case_id"]
    )
    assert report.qualification == "PASS", report.to_dict()
    assert fixture["status"] == "D0_PHYSICAL_CONFORMANCE_ONLY"
    assert all(obj.get("qualification_status") != "QUALIFIED" for obj in fixture["objects"])
