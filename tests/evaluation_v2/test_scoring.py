from datetime import datetime, timezone
from pathlib import Path

import pytest

from nutrifoundation.evaluation.v2 import (
    map_frozen_v1_batch,
    score_batch_v2,
    score_case_v2,
)


ROOT = Path(__file__).resolve().parents[2]
RESPONSES = ROOT / "runs/E0.4/Batch001/responses"
SOURCE_FIXTURE = ROOT / "fixtures/Batch001_Blind_SourceText_v0.1.json"
HIDDEN_REFERENCE = ROOT / "fixtures/Batch001_EvidenceUnit_Frozen_v0.1.yaml"
TASK_MANIFEST = ROOT / "runs/E0.4.2/A0/StrictBlind_TaskPack_Manifest_v1.0.json"
STAMP = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def cases():
    mapped = map_frozen_v1_batch(
        response_dir=RESPONSES,
        source_fixture_path=SOURCE_FIXTURE,
        hidden_reference_path=HIDDEN_REFERENCE,
        task_manifest_path=TASK_MANIFEST,
    )
    return {case.evidence_id: case for case in mapped}


def test_score_vector_is_multidimensional_and_has_no_overall_scalar(cases):
    scored = score_case_v2(cases["EU-B001-001"], evaluated_at=STAMP)
    assert scored.score_vector.keys() == {
        "scientific_semantic_recovery",
        "ontology_alignment",
        "provenance_recovery",
        "numeric_fidelity",
        "safe_abstention_quality",
    }
    assert "overall" not in scored.score_vector


def test_rct_case_scores_canonical_ontology_without_kind_conflation(cases):
    scored = score_case_v2(cases["EU-B001-001"], evaluated_at=STAMP)
    assert scored.evaluation.ontology.study_design == 1.0
    assert scored.evaluation.ontology.claim_type == 1.0
    assert scored.evaluation.ontology.evidence_role == 1.0
    assert scored.evaluation.ontology.score == 1.0


def test_observational_case_keeps_numeric_fidelity_separate_from_semantics(cases):
    scored = score_case_v2(cases["EU-B001-014"], evaluated_at=STAMP)
    assert scored.evaluation.numeric.score == 1.0
    assert scored.evaluation.scientific_core.population == 1.0
    assert scored.evaluation.scientific_core.intervention_exposure == 1.0
    assert scored.evaluation.scientific_core.outcome == 1.0
    assert scored.evaluation.scientific_core.effect == 1.0


def test_guideline_recommendation_is_not_dropped_from_scientific_core(cases):
    scored = score_case_v2(cases["EU-B001-016"], evaluated_at=STAMP)
    effect = next(
        item
        for item in scored.field_comparisons
        if item.dimension == "scientific_core" and item.field == "effect"
    )
    assert effect.reference_value is not None
    assert effect.candidate_value is not None
    assert "reference_recommendation_mapped_to_effect_axis" in effect.rationale
    assert "candidate_recommendation_mapped_to_effect_axis" in effect.rationale


def test_worker_visible_identifier_is_scored_without_requiring_all_context_ids(cases):
    scored = score_case_v2(cases["EU-B001-011"], evaluated_at=STAMP)
    assert scored.evaluation.provenance.visible_anchor_score == 1.0
    assert scored.evaluation.provenance.external_identifier_score == 1.0
    # The response asserted PMID but not DOI. Omission of an optional visible
    # identifier is not treated as provenance failure.
    external = next(
        item
        for item in scored.field_comparisons
        if item.dimension == "provenance" and item.field == "external_identifier"
    )
    assert "pmid:36513271" in external.candidate_value
    assert "doi:10.1016/j.diabres.2022.110207" not in external.candidate_value


def test_supported_semantic_source_span_can_anchor_provenance():
    from nutrifoundation.evaluation.v2.compatibility import (
        CanonicalArtifactV2,
        CanonicalOntology,
        CanonicalNumericPayload,
        CanonicalProvenance,
        CanonicalScientificPayload,
        CanonicalAbstentionInput,
        CompatibilityCaseV2,
        CompatibilityMetadata,
    )

    candidate = CanonicalArtifactV2(
        scientific=CanonicalScientificPayload(),
        ontology=CanonicalOntology(),
        numeric=CanonicalNumericPayload(),
        provenance=CanonicalProvenance(
            semantic_anchor="supported span",
            semantic_anchor_supported=True,
        ),
    )
    reference = CanonicalArtifactV2(
        scientific=CanonicalScientificPayload(),
        ontology=CanonicalOntology(),
        numeric=CanonicalNumericPayload(),
        provenance=CanonicalProvenance(
            legacy_anchor="PubMed abstract PMID 1",
            provided_identifiers=("pmid:1",),
            context_visible_identifiers=("pmid:1",),
        ),
    )
    case = CompatibilityCaseV2(
        task_id="TASK-X",
        response_id="RESP-X",
        task_sha256="a" * 64,
        source_text_sha256="b" * 64,
        contract_version="E0.4-v0.1",
        response_schema_version="ResponseEnvelope-v0.1",
        evidence_id="EU-X",
        source_id="SA-X",
        response_status="completed",
        candidate=candidate,
        reference=reference,
        abstention=CanonicalAbstentionInput(abstained=False),
        metadata=CompatibilityMetadata(
            worker_visible_information=("source_text",),
            reference_visible_information=("frozen_evidence_unit",),
        ),
    )
    scored = score_case_v2(case, evaluated_at=STAMP)
    assert scored.evaluation.provenance.visible_anchor_score == 1.0


def test_task015_safe_defer_is_positive_abstention_evidence(cases):
    scored = score_case_v2(cases["EU-B001-015"], evaluated_at=STAMP)
    assert scored.evaluation.abstention.applicable is True
    assert scored.evaluation.abstention.correct_abstention is True
    assert scored.evaluation.abstention.score == 1.0
    abstention = next(
        item
        for item in scored.field_comparisons
        if item.dimension == "abstention"
    )
    assert abstention.relation == "correct_safe_abstention"


def test_completed_sufficient_case_has_no_abstention_score(cases):
    scored = score_case_v2(cases["EU-B001-014"], evaluated_at=STAMP)
    assert scored.evaluation.abstention.applicable is False
    assert scored.evaluation.abstention.score is None


def test_numeric_fidelity_counts_reference_fields_not_surface_tokens(cases):
    scored = score_case_v2(cases["EU-B001-014"], evaluated_at=STAMP)
    result = scored.evaluation.numeric
    assert result.normalized_numeric_fields >= 1
    assert result.matched_numeric_fields <= result.normalized_numeric_fields
    assert 0.0 <= result.score <= 1.0


def test_batch_scoring_is_deterministic_for_fixed_metadata_time(cases):
    ordered = tuple(cases[key] for key in sorted(cases))
    first = score_batch_v2(ordered, evaluated_at=STAMP)
    second = score_batch_v2(ordered, evaluated_at=STAMP)
    assert [item.model_dump(mode="json") for item in first] == [
        item.model_dump(mode="json") for item in second
    ]


def test_all_batch001_cases_produce_valid_five_dimension_vectors(cases):
    scored = score_batch_v2(
        tuple(cases[key] for key in sorted(cases)),
        evaluated_at=STAMP,
    )
    assert len(scored) == 20
    for item in scored:
        vector = item.score_vector
        assert 0.0 <= vector["scientific_semantic_recovery"] <= 1.0
        assert 0.0 <= vector["ontology_alignment"] <= 1.0
        if vector["provenance_recovery"] is not None:
            assert 0.0 <= vector["provenance_recovery"] <= 1.0
        assert 0.0 <= vector["numeric_fidelity"] <= 1.0
        if vector["safe_abstention_quality"] is not None:
            assert 0.0 <= vector["safe_abstention_quality"] <= 1.0
