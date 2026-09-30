from pathlib import Path

import pytest

from nutrifoundation.services.strict_blind import validate_strict_blind_responses
from nutrifoundation.services.strict_blind_response_bundle import (
    materialize_bundle,
    validate_response_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "runs" / "E0.4.2" / "C" / "StrictBlind_ResponseSet_FROZEN_v1.0.json"
TASKPACK = ROOT / "runs" / "E0.4.2" / "A0" / "StrictBlind_TaskPack_Manifest_v1.0.json"
CANONICAL_SHA256 = "513e9d3c09326b7ae715d6cc5b834d7f31decdc1162298190e3708bb31b7beca"


def test_frozen_strict_blind_bundle_matches_a0_taskpack():
    receipt = validate_response_bundle(
        bundle_path=BUNDLE,
        taskpack_manifest_path=TASKPACK,
        expected_canonical_sha256=CANONICAL_SHA256,
    )
    assert receipt.status == "PASS"
    assert receipt.canonical_bundle_sha256 == CANONICAL_SHA256
    assert receipt.response_count == 20
    assert receipt.completed_count == 19
    assert receipt.defer_count == 1
    assert receipt.failed_count == 0
    assert receipt.unique_response_ids == 20
    assert receipt.unique_task_ids == 20
    assert receipt.task_binding_match_count == 20
    assert receipt.source_hash_match_count == 20
    assert receipt.contract_version_match_count == 20
    assert receipt.response_schema_match_count == 20
    assert receipt.strict_metadata_match_count == 20
    assert receipt.protocol_version_match_count == 20
    assert receipt.blindness_class_match_count == 20


def test_materialized_frozen_bundle_passes_strict_blind_gate(tmp_path):
    receipt = materialize_bundle(
        bundle_path=BUNDLE,
        taskpack_manifest_path=TASKPACK,
        out_dir=tmp_path,
        expected_canonical_sha256=CANONICAL_SHA256,
    )
    assert receipt.status == "PASS"
    assert len(list(tmp_path.glob("*.response.json"))) == 20

    attestation = validate_strict_blind_responses(tmp_path)
    assert attestation.qualifies is True
    assert attestation.fresh_context is True
    assert attestation.prior_batch_exposure is False
    assert attestation.hidden_reference_available_to_worker is False
    assert attestation.independent_worker_session is True


def test_wrong_canonical_hash_is_rejected():
    with pytest.raises(ValueError, match="canonical SHA-256 mismatch"):
        validate_response_bundle(
            bundle_path=BUNDLE,
            taskpack_manifest_path=TASKPACK,
            expected_canonical_sha256="0" * 64,
        )
