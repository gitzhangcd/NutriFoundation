from pathlib import Path

import pytest

from nutrifoundation.evaluation.v2 import map_frozen_v1_batch


ROOT = Path(__file__).resolve().parents[2]
RESPONSES = ROOT / "runs/E0.4/Batch001/responses"
SOURCE_FIXTURE = ROOT / "fixtures/Batch001_Blind_SourceText_v0.1.json"
HIDDEN_REFERENCE = ROOT / "fixtures/Batch001_EvidenceUnit_Frozen_v0.1.yaml"
TASK_MANIFEST = ROOT / "runs/E0.4.2/A0/StrictBlind_TaskPack_Manifest_v1.0.json"


@pytest.fixture(scope="module")
def cases():
    mapped = map_frozen_v1_batch(
        response_dir=RESPONSES,
        source_fixture_path=SOURCE_FIXTURE,
        hidden_reference_path=HIDDEN_REFERENCE,
        task_manifest_path=TASK_MANIFEST,
    )
    return {case.evidence_id: case for case in mapped}


def test_maps_all_frozen_batch001_v1_responses():
    mapped = map_frozen_v1_batch(
        response_dir=RESPONSES,
        source_fixture_path=SOURCE_FIXTURE,
        hidden_reference_path=HIDDEN_REFERENCE,
        task_manifest_path=TASK_MANIFEST,
    )
    assert len(mapped) == 20
    assert len({case.task_id for case in mapped}) == 20
    assert len({case.evidence_id for case in mapped}) == 20


def test_intervention_and_exposure_collapse_to_one_scientific_axis(cases):
    intervention_case = cases["EU-B001-001"]
    assert (
        intervention_case.candidate.scientific.intervention_exposure
        == "Low-carbohydrate Mediterranean-style diet"
    )

    exposure_case = cases["EU-B001-014"]
    assert (
        exposure_case.candidate.scientific.intervention_exposure
        == "Higher ultraprocessed-food share of the diet"
    )


def test_study_design_claim_type_and_evidence_role_are_separated(cases):
    rct = cases["EU-B001-001"].candidate.ontology
    assert rct.study_design == "randomized_controlled_trial"
    assert rct.claim_type == "interventional_effect"
    assert rct.evidence_role == "primary_study"

    cohort = cases["EU-B001-014"].candidate.ontology
    assert cohort.study_design == "cohort"
    assert cohort.claim_type == "observational_association"
    assert cohort.evidence_role == "primary_study"

    synthesis = cases["EU-B001-011"].candidate.ontology
    assert synthesis.study_design == "meta_analysis"
    assert synthesis.claim_type == "evidence_synthesis"
    assert synthesis.evidence_role == "evidence_synthesis"

    guideline = cases["EU-B001-016"].candidate.ontology
    assert guideline.study_design == "guideline"
    assert guideline.claim_type == "recommendation"
    assert guideline.evidence_role == "guideline"


def test_reference_without_legacy_kind_is_compatible_with_source_design(cases):
    reference = cases["EU-B001-001"].reference.ontology
    assert reference.study_design == "randomized_controlled_trial"
    assert reference.claim_type == "interventional_effect"
    assert reference.evidence_role == "primary_study"


def test_legacy_anchor_is_split_from_semantic_and_provenance_components(cases):
    provenance = cases["EU-B001-001"].candidate.provenance
    assert provenance.semantic_anchor is None
    assert provenance.legacy_anchor == "PubMed abstract PMID 19721018"
    assert "pmid:19721018" in provenance.provided_identifiers
    assert "pmid:19721018" in provenance.context_visible_identifiers
    assert "doi:10.7326/0003-4819-151-5-200909010-00004" in (
        provenance.context_visible_identifiers
    )
    assert provenance.context_retrieval_identifier.endswith("/19721018/")


def test_source_span_support_is_verified_against_worker_visible_source():
    from nutrifoundation.evaluation.v2.compatibility import map_provenance

    source = {
        "source_text": (
            "RESULTS: After 4 years, 44% of patients required treatment "
            "compared with 70% in the control group."
        ),
        "source_snapshot": {"identifiers": {}},
        "source_url": None,
    }
    supported = map_provenance(
        {
            "source_span": "After 4 years, 44% of patients required treatment",
            "anchor": "RESULTS",
        },
        source,
    )
    unsupported = map_provenance(
        {
            "source_span": "After 8 years, 99% of patients required treatment",
            "anchor": "RESULTS",
        },
        source,
    )
    assert supported.semantic_anchor_supported is True
    assert unsupported.semantic_anchor_supported is False


def test_unprovided_identifier_is_not_invented_as_candidate_output(cases):
    provenance = cases["EU-B001-011"].candidate.provenance
    assert "doi:10.1016/j.diabres.2022.110207" not in provenance.provided_identifiers
    assert "doi:10.1016/j.diabres.2022.110207" in provenance.context_visible_identifiers


def test_numeric_mapping_uses_existing_canonical_number_normalization(cases):
    numeric = cases["EU-B001-014"].candidate.numeric
    assert "effect" in numeric.by_field
    assert "1.15" in numeric.by_field["effect"]
    assert "1.06" in numeric.by_field["effect"]
    assert "1.25" in numeric.by_field["effect"]
    assert "2" not in numeric.by_field["effect"]


def test_safe_defer_is_mapped_without_turning_it_into_a_score(cases):
    deferred = cases["EU-B001-015"]
    assert deferred.response_status == "defer"
    assert deferred.abstention.abstained is True
    assert deferred.abstention.source_information_insufficient is True
    assert deferred.candidate.scientific.population is None
    assert deferred.reference.scientific.recommendation is not None


def test_mapping_preserves_frozen_hash_bindings(cases):
    case = cases["EU-B001-001"]
    assert case.task_sha256 == (
        "d44cb4f3baa4908bb9b42c234cd84ba0207874b86d6b18e2a3022eecf0320541"
    )
    assert case.source_text_sha256 == (
        "475eeb6c60ae0842e5427723703168f147f3d75b2021adda33edf5bc54725786"
    )
    assert case.contract_version == "E0.4-v0.1"
    assert case.response_schema_version == "ResponseEnvelope-v0.1"


def test_mapping_is_deterministic(cases):
    first = cases["EU-B001-014"].model_dump(mode="json")
    second = map_frozen_v1_batch(
        response_dir=RESPONSES,
        source_fixture_path=SOURCE_FIXTURE,
        hidden_reference_path=HIDDEN_REFERENCE,
        task_manifest_path=TASK_MANIFEST,
    )
    by_id = {case.evidence_id: case for case in second}
    assert by_id["EU-B001-014"].model_dump(mode="json") == first
