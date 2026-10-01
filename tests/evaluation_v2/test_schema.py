from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nutrifoundation.evaluation.v2 import (
    AbstentionResult,
    EvaluationMetadata,
    EvaluationResultV2,
    NumericFidelityResult,
    OntologyAlignmentResult,
    ProvenanceResult,
    ScientificCoreResult,
)


def _metadata() -> EvaluationMetadata:
    return EvaluationMetadata(
        evaluator_version="EvaluatorV2-v0.1",
        created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        worker_visible_information=("source_text", "task_contract"),
        reference_visible_information=("frozen_evidence_unit",),
    )


def test_scientific_core_score_is_mean_of_five_fields():
    result = ScientificCoreResult(
        population=1.0,
        intervention_exposure=1.0,
        comparator=0.5,
        outcome=1.0,
        effect=0.5,
    )
    assert result.score == pytest.approx(0.8)


def test_ontology_score_keeps_three_axes_separate():
    result = OntologyAlignmentResult(
        study_design=1.0,
        claim_type=0.5,
        evidence_role=0.0,
    )
    assert result.score == pytest.approx(0.5)


def test_numeric_fidelity_treats_no_numeric_fields_as_fully_satisfied():
    result = NumericFidelityResult(
        normalized_numeric_fields=0,
        matched_numeric_fields=0,
    )
    assert result.score == 1.0


def test_numeric_fidelity_rejects_impossible_counts():
    with pytest.raises(ValidationError, match="cannot exceed"):
        NumericFidelityResult(
            normalized_numeric_fields=1,
            matched_numeric_fields=2,
        )


def test_unobservable_external_identifier_is_not_provenance_failure():
    result = ProvenanceResult(
        visible_anchor_score=1.0,
        external_identifier_score=None,
    )
    assert result.score == 1.0


def test_all_unobservable_provenance_is_not_applicable():
    assert ProvenanceResult().score is None


def test_abstention_requires_explicit_applicability():
    task_015 = AbstentionResult(applicable=True, correct_abstention=True)
    assert task_015.score == 1.0

    with pytest.raises(ValidationError, match="required"):
        AbstentionResult(applicable=True)

    with pytest.raises(ValidationError, match="must be null"):
        AbstentionResult(applicable=False, correct_abstention=False)


def test_evaluation_result_v2_round_trips_and_binds_v1_identities():
    result = EvaluationResultV2(
        task_id="TASK-BLIND-B001-015",
        response_id="RESP-STRICT-B001-015",
        evidence_id="EU-B001-015",
        source_id="SA-B001-015",
        scientific_core=ScientificCoreResult(
            population=1.0,
            intervention_exposure=1.0,
            comparator=1.0,
            outcome=1.0,
            effect=1.0,
        ),
        ontology=OntologyAlignmentResult(
            study_design=1.0,
            claim_type=1.0,
            evidence_role=1.0,
        ),
        numeric=NumericFidelityResult(
            normalized_numeric_fields=0,
            matched_numeric_fields=0,
        ),
        provenance=ProvenanceResult(
            visible_anchor_score=None,
            external_identifier_score=None,
        ),
        abstention=AbstentionResult(
            applicable=True,
            correct_abstention=True,
        ),
        metadata=_metadata(),
    )

    restored = EvaluationResultV2.model_validate_json(result.model_dump_json())
    assert restored == result
    assert restored.task_id == "TASK-BLIND-B001-015"
    assert restored.response_id == "RESP-STRICT-B001-015"
    assert restored.evidence_id == "EU-B001-015"
    assert restored.source_id == "SA-B001-015"


def test_schema_is_frozen_and_rejects_unknown_fields():
    core = ScientificCoreResult(
        population=1.0,
        intervention_exposure=1.0,
        comparator=1.0,
        outcome=1.0,
        effect=1.0,
    )
    with pytest.raises(ValidationError):
        ScientificCoreResult(
            population=1.0,
            intervention_exposure=1.0,
            comparator=1.0,
            outcome=1.0,
            effect=1.0,
            hidden_gold_label="forbidden",
        )
    with pytest.raises(ValidationError):
        core.population = 0.0
