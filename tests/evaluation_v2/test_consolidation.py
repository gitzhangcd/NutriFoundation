import hashlib
from pathlib import Path

from nutrifoundation.evaluation.v2.consolidation import (
    build_e3_paper_evidence_package,
)


ROOT = Path(__file__).resolve().parents[2]
FROZEN_A28 = ROOT / "runs/E0.4.2/E3/A2.8/E3_Paper_Evidence_Package_v1.0.json"
FROZEN_A28_SHA = FROZEN_A28.with_suffix(FROZEN_A28.suffix + ".sha256")
A28_DOC = ROOT / "docs/E0.4.2-E3-A2.8_Paper_Level_Evidence_Freeze_v1.0.md"


def _package():
    return build_e3_paper_evidence_package(root=ROOT)


def test_a28_non_regression_audit_passes():
    package = _package()
    assert package.status == "PASS"
    assert all(
        item.status.startswith("PASS")
        for item in package.non_regression_audit
    )


def test_a26_digest_difference_is_reconciled_as_packaging_only():
    package = _package()
    check = next(
        item
        for item in package.non_regression_audit
        if item.check_id == "NR-003-a26-lineage-reconciliation"
    )
    assert check.status == "PASS_RECONCILED"
    assert check.details["semantic_object_equal_to_deterministic_rerun"] is True
    assert check.details["packaging_only_digest_difference"] is True
    assert (
        check.details["repository_artifact_sha256"]
        == "f90f0e612afedba64fe76e31c344699290246a8b5f0875cc9574abb5abcb13ad"
    )
    assert (
        check.details["original_ci_serialization_sha256"]
        == "3c4f133135ed0160a9e2f5ce65eb83cc655c1ec3f829e5fcc21ea6d0f83b0296"
    )


def test_a27_report_is_byte_and_semantically_frozen():
    package = _package()
    check = next(
        item
        for item in package.non_regression_audit
        if item.check_id == "NR-004-a27-deterministic-freeze"
    )
    assert check.status == "PASS"
    assert check.details["semantic_object_equal_to_deterministic_rerun"] is True
    assert (
        check.details["repository_sha256"]
        == "1452d2f5fc9c227ca9e9a3bb25e1fd1c285cb77ba39f0743ae3afffb6210de2c"
    )


def test_attribution_counts_and_new_residuals_are_conserved():
    package = _package()
    attr = package.discrepancy_attribution
    assert attr["primary_denominator"] == 44
    assert attr["category_counts"] == {
        "confirmed_evaluator_artifact": 21,
        "non_isomorphic_unresolved": 9,
        "ontology_contract_ambiguity": 6,
        "preserved_scientific_residual": 8,
    }
    assert attr["newly_localized_residual_count"] == 6


def test_v2_five_dimension_results_are_frozen_without_overall_scalar():
    package = _package()
    dims = package.descriptive_results["v2_dimensions"]
    assert dims["scientific_semantic_recovery"]["mean_score"] == 0.9473684210526315
    assert dims["ontology_alignment"]["mean_score"] == 0.8596491228070173
    assert dims["provenance_recovery"]["mean_score"] == 1.0
    assert dims["numeric_fidelity"]["mean_score"] == 0.8088235294117647
    assert dims["safe_abstention_quality"]["mean_score"] == 1.0
    assert package.descriptive_results["overall_scalar_score"] is None
    assert package.descriptive_results["overall_scalar_score_policy"] == "forbidden"


def test_claim_registry_has_no_publication_ready_claims_yet():
    package = _package()
    assert len(package.claims) == 8
    assert all(claim.publication_ready is False for claim in package.claims)
    assert package.publication_grade is False
    assert (
        package.manuscript_use_status
        == "METHODS_RESULTS_DRAFT_READY_NOT_PUBLICATION_GRADE"
    )


def test_claims_preserve_batch_scope_and_limitations():
    package = _package()
    c02 = next(claim for claim in package.claims if claim.claim_id == "E3-C02")
    assert "21 of 44" in c02.statement
    assert "44 V1 canonical discrepancy events only" == c02.scope
    assert any(
        "must not be generalized" in item
        for item in package.limitations
    )


def test_committed_a28_package_is_exact_deterministic_output():
    expected = _package().model_dump_json(indent=2) + "\n"
    assert FROZEN_A28.read_text(encoding="utf-8") == expected


def test_committed_a28_checksum_matches_package_bytes():
    digest = hashlib.sha256(FROZEN_A28.read_bytes()).hexdigest()
    assert digest == "04e4c3b5bbbc2a289383bcab4f2da94eb02f98d06d567b855343a0abe3e53ea8"
    assert FROZEN_A28_SHA.read_text(encoding="utf-8").strip() == (
        f"{digest}  {FROZEN_A28.name}"
    )


def test_a28_paper_doc_has_clean_markdown_math_controls():
    text = A28_DOC.read_text(encoding="utf-8")
    assert "\x08" not in text
    assert "\\boxed" in text
    assert "\\rightarrow" in text
    assert "PASS / FROZEN" in text
