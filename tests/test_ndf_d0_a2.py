import json
from pathlib import Path

from nutrifoundation.ndf import run_fixture_suite

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "fixtures/ndf/d0_a2/Fixture_Suite_v0.1.json"


def test_ndf_d0_a2_8_plus_2_fixture_gate():
    report = run_fixture_suite(json.loads(SUITE.read_text()))
    assert report["summary"]["negative_total"] == 8
    assert report["summary"]["negative_correctly_rejected"] == 8
    assert report["summary"]["positive_total"] == 2
    assert report["summary"]["positive_correctly_accepted"] == 2
    assert report["summary"]["expectations_met"] == 10


def test_every_fixture_reports_validator_breakdown():
    report = run_fixture_suite(json.loads(SUITE.read_text()))
    for row in report["results"]:
        assert set(row["validator_results"]) == {"V0.1", "V0.2", "V0.3", "V0.4"}
