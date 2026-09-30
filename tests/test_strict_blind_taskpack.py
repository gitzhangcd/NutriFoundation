import copy
from pathlib import Path

from nutrifoundation.services.strict_blind_taskpack import (
    REQUIRED_WORKER_METADATA,
    audit_taskpack,
    build_taskpack_manifest,
    load_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fixtures" / "Batch001_Blind_SourceText_v0.1.json"
FROZEN = (
    ROOT
    / "runs"
    / "E0.4.2"
    / "A0"
    / "StrictBlind_TaskPack_Manifest_v1.0.json"
)


def test_frozen_taskpack_matches_deterministic_e04_tasks():
    frozen = load_manifest(FROZEN)
    generated = build_taskpack_manifest(SOURCE, batch_id="B001")

    assert frozen["task_count"] == 20
    assert frozen["taskpack_sha256"] == generated["taskpack_sha256"]
    assert frozen["tasks"] == generated["tasks"]


def test_blind_wall_audit_passes_for_frozen_taskpack():
    frozen = load_manifest(FROZEN)
    audit = audit_taskpack(
        source_fixture_path=SOURCE,
        frozen_manifest=frozen,
        batch_id="B001",
    )

    assert audit.status == "PASS"
    assert audit.task_count == 20
    assert audit.unique_task_ids == 20
    assert audit.unique_source_ids == 20
    assert audit.unique_evidence_ids == 20
    assert audit.task_hash_match_count == 20
    assert audit.source_hash_match_count == 20
    assert audit.forbidden_token_hits == ()
    assert audit.forbidden_key_hits == ()
    assert audit.reference_answer_visibility_violations == ()
    assert audit.prior_response_artifacts_included is False
    assert audit.hidden_reference_artifacts_included is False
    assert audit.scoring_artifacts_included is False


def test_hidden_reference_artifact_breaks_blind_wall():
    frozen = load_manifest(FROZEN)
    contaminated = copy.deepcopy(frozen)
    contaminated["leaked_path"] = "fixtures/Batch001_EvidenceUnit_Frozen_v0.1.yaml"

    audit = audit_taskpack(
        source_fixture_path=SOURCE,
        frozen_manifest=contaminated,
        batch_id="B001",
    )
    assert audit.status == "FAIL"
    assert audit.hidden_reference_artifacts_included is True


def test_prior_response_artifact_breaks_blind_wall():
    frozen = load_manifest(FROZEN)
    contaminated = copy.deepcopy(frozen)
    contaminated["leaked_path"] = "runs/E0.4/Batch001/responses/RESP.json"

    audit = audit_taskpack(
        source_fixture_path=SOURCE,
        frozen_manifest=contaminated,
        batch_id="B001",
    )
    assert audit.status == "FAIL"
    assert audit.prior_response_artifacts_included is True


def test_task_hash_tamper_breaks_blind_wall():
    frozen = load_manifest(FROZEN)
    contaminated = copy.deepcopy(frozen)
    contaminated["tasks"][0]["task_sha256"] = "0" * 64

    audit = audit_taskpack(
        source_fixture_path=SOURCE,
        frozen_manifest=contaminated,
        batch_id="B001",
    )
    assert audit.status == "FAIL"
    assert audit.task_hash_match_count == 19


def test_fresh_context_worker_metadata_is_frozen():
    assert REQUIRED_WORKER_METADATA == {
        "fresh_context_attestation": True,
        "prior_batch_exposure": False,
        "hidden_reference_available_to_worker": False,
        "independent_worker_session": True,
        "strict_blind_protocol_version": "E0.4.2-A0-v0.1",
        "blindness_class": "strict_blind_fresh_context",
    }


def test_taskpack_does_not_accept_hidden_gold_parameter():
    generated = build_taskpack_manifest(SOURCE, batch_id="B001")
    assert generated["hidden_reference_in_task_factory"] is False
    assert generated["scoring_permitted_before_response_freeze"] is False
