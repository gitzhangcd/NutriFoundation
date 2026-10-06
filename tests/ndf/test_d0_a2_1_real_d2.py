import json
from pathlib import Path

from nutrifoundation.ndf.d0 import ValidationContext, validate_objects

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures/ndf/d0/real_objects/NHANES_L_SEQN130378_First_D2_v0.1.json"


def _load():
    return json.loads(FIXTURE.read_text())


def test_first_real_d2_nhanes_object_passes_d0_physical_conformance():
    fixture = _load()
    report = validate_objects(
        fixture["objects"],
        ValidationContext(**fixture["context"]),
        run_id=fixture["case_id"],
    )
    assert report.qualification == "PASS", report.to_dict()
    assert report.failed_checks == 0
    assert fixture["status"] == "D0_PHYSICAL_CONFORMANCE_ONLY"


def test_seqn_is_role_restricted_and_not_in_system_projection():
    fixture = _load()
    mapping = next(x for x in fixture["objects"] if x["kind"] == "SubjectSourceMapping")
    boundary = next(x for x in fixture["objects"] if x["kind"] == "NutritionInformationBoundary")

    assert mapping["visibility"] == "ROLE_RESTRICTED"
    assert mapping["internal_source_mapping"]["SEQN"] == 130378

    projected = json.dumps(boundary["projected_payload"], sort_keys=True)
    assert "130378" not in projected
    assert boundary["restricted_object_refs"] == ["SUBJMAP-NHANES-L-0001"]


def test_observed_and_derived_axes_are_not_collapsed():
    fixture = _load()
    raw = next(x for x in fixture["objects"] if x["object_id"] == "OBS-NHANES-L-0001-RAW")
    drv = next(x for x in fixture["objects"] if x["object_id"] == "OBS-NHANES-L-0001-DRV")

    assert all(
        item["construction_origin"] in {"OBS", "UNK"}
        for item in raw["observations"]
    )
    assert all(
        item["construction_origin"] == "DRV"
        and item["semantic_origin"] == "DERIVED"
        for item in drv["observations"]
    )
    assert "OBS-NHANES-L-0001-RAW" in drv["dependency_refs"]


def test_missing_diet_component_is_not_fabricated_as_normal_or_zero():
    fixture = _load()
    raw = next(x for x in fixture["objects"] if x["object_id"] == "OBS-NHANES-L-0001-RAW")
    energy = next(x for x in raw["observations"] if x["concept"] == "day1_total_energy")

    assert energy["epistemic_expression"] == "UNKNOWN"
    assert energy["construction_origin"] == "UNK"
    assert energy["visibility"] == "NOT_YET_AVAILABLE"
    assert energy["value"] is None
    assert energy["missingness_reason"] == "SOURCE_COMPONENT_NOT_INGESTED_IN_A2_1"


def test_decision_episode_is_cross_sectional_constructed_and_reference_pending():
    fixture = _load()
    episode = next(x for x in fixture["objects"] if x["kind"] == "NutritionDecisionEpisode")

    assert episode["time_mode"] == "EXPERIMENTALLY_DEFINED_CROSS_SECTIONAL"
    assert episode["reference_status"] == "REFERENCE_PENDING"
    assert episode["evaluator_status"] == "PENDING"
    assert episode["clinical_case_claim"] == "NOT_A_REAL_CLINICAL_CASE"
    assert episode["task_type"] == "INFORMATION_SUFFICIENCY_TRIAGE"
