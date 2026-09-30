import json
from pathlib import Path

from nutrifoundation.services.strict_blind_response_set import (
    validate_strict_blind_response_set,
)


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "runs" / "E0.4.2" / "C" / "StrictBlind_ResponseSet_FROZEN_v1.0.json"
TASKPACK = ROOT / "runs" / "E0.4.2" / "A0" / "StrictBlind_TaskPack_Manifest_v1.0.json"
EXPECTED_CANONICAL_SHA = "513e9d3c09326b7ae715d6cc5b834d7f31decdc1162298190e3708bb31b7beca"


def test_frozen_strict_blind_response_set_passes_pre_scoring_validation():
    result = validate_strict_blind_response_set(
        bundle_path=BUNDLE,
        taskpack_manifest_path=TASKPACK,
        expected_canonical_sha256=EXPECTED_CANONICAL_SHA,
    )
    assert result.status == "PASS"
    assert result.canonical_bundle_sha256 == EXPECTED_CANONICAL_SHA
    assert result.response_count == 20
    assert result.unique_response_ids == 20
    assert result.unique_task_ids == 20
    assert result.completed_count == 19
    assert result.defer_count == 1
    assert result.task_id_set_match is True
    assert result.task_hash_match_count == 20
    assert result.source_hash_match_count == 20
    assert result.contract_match_count == 20
    assert result.schema_match_count == 20
    assert result.metadata_match_count == 20
    assert result.lineage_match_count == 20
    assert result.violations == ()


def test_response_set_task_hash_tamper_fails(tmp_path):
    payload = json.loads(BUNDLE.read_text(encoding="utf-8"))
    payload[0]["task_sha256"] = "0" * 64
    mutated = tmp_path / "mutated.json"
    mutated.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    result = validate_strict_blind_response_set(
        bundle_path=mutated,
        taskpack_manifest_path=TASKPACK,
    )
    assert result.status == "FAIL"
    assert result.task_hash_match_count == 19


def test_response_set_attestation_tamper_fails(tmp_path):
    payload = json.loads(BUNDLE.read_text(encoding="utf-8"))
    payload[0]["worker"]["metadata"]["prior_batch_exposure"] = True
    mutated = tmp_path / "mutated.json"
    mutated.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    result = validate_strict_blind_response_set(
        bundle_path=mutated,
        taskpack_manifest_path=TASKPACK,
    )
    assert result.status == "FAIL"
    assert result.metadata_match_count == 19


def test_response_set_missing_task_fails(tmp_path):
    payload = json.loads(BUNDLE.read_text(encoding="utf-8"))[:-1]
    mutated = tmp_path / "mutated.json"
    mutated.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    result = validate_strict_blind_response_set(
        bundle_path=mutated,
        taskpack_manifest_path=TASKPACK,
    )
    assert result.status == "FAIL"
    assert result.response_count == 19
    assert result.task_id_set_match is False


def test_response_set_wrong_bundle_sha_fails():
    result = validate_strict_blind_response_set(
        bundle_path=BUNDLE,
        taskpack_manifest_path=TASKPACK,
        expected_canonical_sha256="0" * 64,
    )
    assert result.status == "FAIL"
    assert any("canonical_bundle_sha256 mismatch" in item for item in result.violations)
