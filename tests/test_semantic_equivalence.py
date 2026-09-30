from datetime import datetime, timezone
from pathlib import Path

import pytest

from nutrifoundation.adapters.chat_window import ChatWindowFileBridge
from nutrifoundation.domain.models import Provenance
from nutrifoundation.domain.semantic_equivalence import CalibrationReferenceClass
from nutrifoundation.domain.semantic_worker import ResponseEnvelope, WorkerDescriptor
from nutrifoundation.services.canonical_batch_scoring import score_canonical_batch
from nutrifoundation.services.canonicalization import canonicalize
from nutrifoundation.services.equivalence_calibration import calibrate_fixture
from nutrifoundation.services.semantic_equivalence import compare_field
from nutrifoundation.services.strict_blind import (
    require_strict_blind,
    validate_strict_blind_responses,
)
from nutrifoundation.services.verifier_calibration import calibrate_verifier_fixture


ROOT = Path(__file__).resolve().parents[1]


def test_canonical_aliases_reduce_surface_form_differences():
    left = canonicalize("outcome", "Incident type 2 diabetes")
    right = canonicalize("outcome", "Incident T2D")
    assert "incident_t2d" in left.concepts
    assert "incident_t2d" in right.concepts


def test_effect_semantics_normalize_hr_ci_and_range_syntax():
    result = compare_field(
        "effect",
        "HR 1.15 (95% CI 1.06-1.25)",
        "Hazard ratio 1.15, 95 percent confidence interval 1.06 to 1.25",
    )
    assert result.equivalent is True
    assert result.numeric_recall == 1.0


def test_intervention_conflict_is_not_equivalent():
    result = compare_field(
        "intervention",
        "Low-fat diet",
        "Low-carbohydrate diet",
    )
    assert result.equivalent is False
    assert result.conflict_tags


def test_population_causal_scope_conflict_is_not_equivalent():
    result = compare_field(
        "population",
        "Adults with type 2 diabetes",
        "Adults without diabetes",
    )
    assert result.equivalent is False


def test_anchor_same_pmid_is_equivalent_despite_wording():
    result = compare_field(
        "anchor",
        "PubMed abstract PMID 31841598",
        "PMID: 31841598 PubMed abstract",
    )
    assert result.equivalent is True


def test_equivalence_development_fixture_is_not_publication_grade():
    summary, _ = calibrate_fixture(
        ROOT / "fixtures/E0.4.1_Semantic_Equivalence_Development_Calibration_v0.1.yaml"
    )
    assert summary.case_count == 43
    assert summary.reference_class == CalibrationReferenceClass.MODEL_ASSISTED_DEVELOPMENT.value
    assert summary.publication_grade is False
    assert summary.overall.precision == 1.0
    assert summary.overall.recall == 1.0
    assert summary.overall.specificity == 1.0


def test_verifier_contract_calibration_is_not_publication_grade():
    summary, _ = calibrate_verifier_fixture(
        ROOT / "fixtures/E0.4.1_Verifier_Development_Calibration_v0.1.yaml"
    )
    assert summary.case_count == 20
    assert summary.reference_class == CalibrationReferenceClass.CONTRACT_GENERATED.value
    assert summary.publication_grade is False


def test_current_e04_responses_fail_strict_blind_attestation():
    attestation = validate_strict_blind_responses(
        ROOT / "runs/E0.4/Batch001/responses"
    )
    assert attestation.qualifies is False
    assert attestation.prior_batch_exposure is True


def test_strict_blind_requires_fresh_independent_unexposed_worker(tmp_path):
    response = ResponseEnvelope(
        response_id="RESP-STRICT-001",
        task_id="TASK-STRICT-001",
        task_sha256="a" * 64,
        contract_version="E0.4-v0.1",
        response_schema_version="ResponseEnvelope-v0.1",
        source_text_sha256="b" * 64,
        worker=WorkerDescriptor(
            worker_id="fresh-worker",
            adapter_type="chat_window_file_bridge",
            metadata={
                "fresh_context_attestation": True,
                "prior_batch_exposure": False,
                "hidden_reference_available_to_worker": False,
                "independent_worker_session": True,
            },
        ),
        status="defer",
        output={},
        uncertainties=("synthetic strict-blind attestation test",),
        created_at=datetime.now(timezone.utc),
        provenance=Provenance(source="test"),
    )
    path = tmp_path / "RESP.response.json"
    path.write_text(response.model_dump_json(indent=2), encoding="utf-8")

    attestation = require_strict_blind(tmp_path)
    assert attestation.qualifies is True


def test_canonical_batch_scoring_is_post_response_sidecar():
    report = score_canonical_batch(
        response_dir=ROOT / "runs/E0.4/Batch001/responses",
        hidden_reference_path=ROOT / "fixtures/Batch001_EvidenceUnit_Frozen_v0.1.yaml",
        batch_id="B001",
    )
    assert report.case_count == 20
    assert report.completed_response_count == 19
    assert report.deferred_count == 1
    assert report.comparable_field_count > 0


def test_e041_contract_separates_development_from_publication_validation():
    from nutrifoundation.contract import E041_INVARIANTS

    statements = {item.statement for item in E041_INVARIANTS}
    assert "DevelopmentCalibration != PublicationValidation" in statements
    assert "StrictBlind -> FreshContextRequired" in statements
    assert "VerifierCalibration != EquivalenceCalibration" in statements


def test_current_context_is_rejected_by_strict_blind_scoring(tmp_path):
    from nutrifoundation.services.strict_blind_runner import score_strict_blind_batch

    with pytest.raises(ValueError, match="does not qualify"):
        score_strict_blind_batch(
            source_fixture_path=ROOT / "fixtures/Batch001_Blind_SourceText_v0.1.json",
            response_dir=ROOT / "runs/E0.4/Batch001/responses",
            hidden_reference_path=ROOT / "fixtures/Batch001_EvidenceUnit_Frozen_v0.1.yaml",
            db_path=tmp_path / "strict.db",
            batch_id="B001",
        )
