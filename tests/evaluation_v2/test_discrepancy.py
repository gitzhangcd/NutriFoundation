from pathlib import Path

from nutrifoundation.evaluation.v2.discrepancy import (
    CONFIRMED_ARTIFACT,
    NON_ISOMORPHIC,
    ONTOLOGY_AMBIGUITY,
    PRESERVED_RESIDUAL,
    build_discrepancy_attribution_report,
)


ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "runs/E0.4.2/A0/PostFreeze_Controller_Report_v1.0.json"
V2 = ROOT / "runs/E0.4.2/E3/A2.6/Evaluator_V2_Batch_Report_v1.0.json"


def _report():
    return build_discrepancy_attribution_report(
        v1_controller_report_path=V1,
        v2_batch_report_path=V2,
    )


def test_primary_attribution_uses_44_v1_canonical_non_equivalent_events():
    report = _report()
    assert report.canonical_attribution.v1_canonical_non_equivalent_event_count == 44
    assert report.canonical_attribution.category_counts == {
        CONFIRMED_ARTIFACT: 21,
        NON_ISOMORPHIC: 9,
        ONTOLOGY_AMBIGUITY: 6,
        PRESERVED_RESIDUAL: 8,
    }


def test_mechanism_counts_are_frozen():
    report = _report()
    assert report.canonical_attribution.mechanism_counts == {
        "kind_conflates_study_design_and_claim_type": 6,
        "numeric_residual_reclassified": 2,
        "provenance_representation_mismatch": 20,
        "safe_abstention_misclassification": 1,
        "semantic_boundary_not_scored_in_v2_core": 9,
        "semantic_residual": 6,
    }


def test_all_v1_anchor_mismatches_are_confirmed_provenance_artifacts():
    report = _report()
    anchors = [event for event in report.canonical_events if event.v1_field == "anchor"]
    assert len(anchors) == 20
    assert all(event.category == CONFIRMED_ARTIFACT for event in anchors)
    assert all(event.v2_score == 1.0 for event in anchors)
    assert all(
        event.mechanism == "provenance_representation_mismatch"
        for event in anchors
    )


def test_task015_missing_recommendation_is_safe_abstention_artifact():
    report = _report()
    event = next(
        event
        for event in report.canonical_events
        if event.evidence_id == "EU-B001-015"
        and event.v1_field == "recommendation"
    )
    assert event.category == CONFIRMED_ARTIFACT
    assert event.mechanism == "safe_abstention_misclassification"
    assert event.v2_score == 1.0


def test_kind_mismatches_are_frozen_as_contract_ambiguity_not_model_error():
    report = _report()
    kinds = [event for event in report.canonical_events if event.v1_field == "kind"]
    assert len(kinds) == 6
    assert all(event.category == ONTOLOGY_AMBIGUITY for event in kinds)


def test_applicability_boundary_events_remain_unresolved():
    report = _report()
    boundaries = [
        event
        for event in report.canonical_events
        if event.v1_field == "applicability_boundary"
    ]
    assert len(boundaries) == 9
    assert all(event.category == NON_ISOMORPHIC for event in boundaries)


def test_effect_partials_are_reclassified_as_numeric_residuals():
    report = _report()
    events = [
        event
        for event in report.canonical_events
        if event.v1_field == "effect"
    ]
    assert {(event.evidence_id, event.mechanism) for event in events} == {
        ("EU-B001-009", "numeric_residual_reclassified"),
        ("EU-B001-018", "numeric_residual_reclassified"),
    }


def test_v2_exposes_six_newly_localized_orthogonal_residuals():
    report = _report()
    observed = {
        (item.evidence_id, item.dimension, item.field)
        for item in report.v2_newly_localized_residuals
    }
    assert observed == {
        ("EU-B001-003", "numeric", "effect"),
        ("EU-B001-009", "ontology", "claim_type"),
        ("EU-B001-009", "numeric", "applicability_boundary"),
        ("EU-B001-014", "ontology", "claim_type"),
        ("EU-B001-014", "numeric", "effect"),
        ("EU-B001-019", "numeric", "population"),
    }


def test_operational_flags_are_explicitly_non_additive():
    report = _report()
    assert report.operational_audit.critical_error_count == 97
    assert report.operational_audit.error_flag_incidence_count == 123
    assert report.operational_audit.operational_escalation_count == 17
    assert report.operational_audit.benchmark_adjudication_count == 20
    assert "high_risk_hidden_reference_mismatch" in (
        report.operational_audit.non_additive_flags
    )


def test_scalar_accuracy_subtraction_is_explicitly_prohibited():
    report = _report()
    prohibited = " ".join(report.interpretation_freeze["prohibited"])
    assert "Do not subtract V1 field-equivalence rate" in prohibited
    assert "publication-grade model accuracy" in prohibited
