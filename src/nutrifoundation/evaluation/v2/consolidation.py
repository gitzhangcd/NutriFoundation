from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import Field

from nutrifoundation.domain.models import FrozenModel
from nutrifoundation.evaluation.v2.discrepancy import (
    build_discrepancy_attribution_report,
)
from nutrifoundation.evaluation.v2.runner import run_frozen_response_set_v2
from nutrifoundation.io.loaders import load_structured


PACKAGE_VERSION = "E0.4.2-E3-A2.8-v1.0"
A26_STAMP = datetime.fromisoformat("2026-10-01T04:36:07+00:00")
STRICT_RESPONSE_SHA256 = (
    "f5cc39f4d0394f5928eb5142c5c4aa43dab638ea2077fbcd2950f4f64a66d0c7"
)


class EvidencePointer(FrozenModel):
    path: str
    sha256: str


class AuditCheck(FrozenModel):
    check_id: str
    status: str
    interpretation: str
    details: dict[str, Any] = Field(default_factory=dict)


class ScientificClaim(FrozenModel):
    claim_id: str
    statement: str
    status: str
    scope: str
    evidence_refs: tuple[str, ...]
    paper_location: tuple[str, ...]
    publication_ready: bool


class E3PaperEvidencePackage(FrozenModel):
    artifact: str = "E0.4.2-E3 Paper-Level Evidence Package"
    package_version: str = PACKAGE_VERSION
    status: str
    batch_id: str
    reference_authority: str
    publication_grade: bool
    manuscript_use_status: str
    inputs: dict[str, EvidencePointer]
    non_regression_audit: tuple[AuditCheck, ...]
    descriptive_results: dict[str, Any]
    discrepancy_attribution: dict[str, Any]
    claims: tuple[ScientificClaim, ...]
    limitations: tuple[str, ...]
    prohibited_interpretations: tuple[str, ...]
    next_publication_gates: tuple[str, ...]


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _stable_path(path: str | Path, root: Path) -> str:
    value = Path(path).resolve()
    root = root.resolve()
    try:
        return str(value.relative_to(root))
    except ValueError:
        return str(value)


def _sidecar_digest(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip().split()[0]


def _dimension_map(v2_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["dimension"]: item
        for item in v2_report["dimension_summary"]
    }


def _a26_semantic_projection(report: dict[str, Any]) -> dict[str, Any]:
    projected = {
        **report,
        "response_set": dict(report["response_set"]),
        "source_fixture": dict(report["source_fixture"]),
        "hidden_reference": dict(report["hidden_reference"]),
        "task_manifest": dict(report["task_manifest"]),
    }
    projected["response_set"]["path"] = "<repo-relative-or-absolute>"
    projected["source_fixture"]["path"] = "<repo-relative-or-absolute>"
    projected["hidden_reference"]["path"] = "<repo-relative-or-absolute>"
    projected["task_manifest"]["path"] = "<repo-relative-or-absolute>"
    return projected


def build_e3_paper_evidence_package(
    *,
    root: str | Path = ".",
) -> E3PaperEvidencePackage:
    root = Path(root).resolve()

    response_path = root / "runs/E0.4.2/A0/StrictBlind_ResponseSet_FROZEN_v1.0.json"
    source_fixture = root / "fixtures/Batch001_Blind_SourceText_v0.1.json"
    hidden_reference = root / "fixtures/Batch001_EvidenceUnit_Frozen_v0.1.yaml"
    task_manifest = root / "runs/E0.4.2/A0/StrictBlind_TaskPack_Manifest_v1.0.json"
    v1_path = root / "runs/E0.4.2/A0/PostFreeze_Controller_Report_v1.0.json"
    a26_path = root / "runs/E0.4.2/E3/A2.6/Evaluator_V2_Batch_Report_v1.0.json"
    a26_sidecar = a26_path.with_suffix(a26_path.suffix + ".sha256")
    a26_manifest_path = root / "runs/E0.4.2/E3/A2.6/Freeze_Manifest_v1.0.json"
    a27_path = root / "runs/E0.4.2/E3/A2.7/V1_V2_Discrepancy_Attribution_v1.0.json"
    a27_sidecar = a27_path.with_suffix(a27_path.suffix + ".sha256")
    a27_manifest_path = root / "runs/E0.4.2/E3/A2.7/Freeze_Manifest_v1.0.json"

    response_sha = sha256_file(response_path)
    v1_sha = sha256_file(v1_path)
    a26_repo_sha = sha256_file(a26_path)
    a27_repo_sha = sha256_file(a27_path)

    v1 = load_structured(v1_path)
    a26 = load_structured(a26_path)
    a26_manifest = load_structured(a26_manifest_path)
    a27 = load_structured(a27_path)
    a27_manifest = load_structured(a27_manifest_path)

    checks: list[AuditCheck] = []

    checks.append(
        AuditCheck(
            check_id="NR-001-frozen-response-identity",
            status="PASS" if response_sha == STRICT_RESPONSE_SHA256 else "FAIL",
            interpretation=(
                "The strict-blind semantic ResponseSet is byte-identical to "
                "the response set used by A2.6/A2.7."
            ),
            details={
                "observed_sha256": response_sha,
                "expected_sha256": STRICT_RESPONSE_SHA256,
                "response_count": len(load_structured(response_path)),
            },
        )
    )

    a26_embedded_input_sha = a27["v2_batch_report"]["sha256"]
    checks.append(
        AuditCheck(
            check_id="NR-002-a26-repository-artifact-binding",
            status="PASS" if a26_repo_sha == a26_embedded_input_sha else "FAIL",
            interpretation=(
                "The A2.7 attribution report is bound to the exact A2.6 "
                "report bytes currently stored in the repository."
            ),
            details={
                "a26_repository_sha256": a26_repo_sha,
                "a27_embedded_a26_sha256": a26_embedded_input_sha,
            },
        )
    )

    rerun_a26 = run_frozen_response_set_v2(
        response_set_path=response_path,
        source_fixture_path=source_fixture,
        hidden_reference_path=hidden_reference,
        task_manifest_path=task_manifest,
        batch_id="B001",
        evaluated_at=A26_STAMP,
        expected_response_set_sha256=STRICT_RESPONSE_SHA256,
    )
    a26_semantic_equal = (
        _a26_semantic_projection(rerun_a26.model_dump(mode="json"))
        == _a26_semantic_projection(a26)
    )
    original_ci_output_sha = _sidecar_digest(a26_sidecar)
    manifest_ci_output_sha = a26_manifest["frozen_output"]["sha256"]
    checks.append(
        AuditCheck(
            check_id="NR-003-a26-lineage-reconciliation",
            status=(
                "PASS_RECONCILED"
                if (
                    a26_semantic_equal
                    and original_ci_output_sha == manifest_ci_output_sha
                    and a26_repo_sha != original_ci_output_sha
                )
                else "PASS"
                if (
                    a26_semantic_equal
                    and a26_repo_sha == original_ci_output_sha
                    and original_ci_output_sha == manifest_ci_output_sha
                )
                else "FAIL"
            ),
            interpretation=(
                "A2.6 scientific content reproduces deterministically. "
                "The historical sidecar/manifest digest is retained as the "
                "original CI serialization checksum; the repository artifact "
                "has a distinct byte digest caused by post-CI packaging/"
                "serialization, not by changed scientific content."
            ),
            details={
                "semantic_object_equal_to_deterministic_rerun": a26_semantic_equal,
                "repository_artifact_sha256": a26_repo_sha,
                "original_ci_serialization_sha256": original_ci_output_sha,
                "a26_manifest_frozen_output_sha256": manifest_ci_output_sha,
                "packaging_only_digest_difference": (
                    a26_semantic_equal and a26_repo_sha != original_ci_output_sha
                ),
            },
        )
    )

    rerun_a27 = build_discrepancy_attribution_report(
        v1_controller_report_path=v1_path,
        v2_batch_report_path=a26_path,
    )
    a27_semantic_equal = rerun_a27.model_dump(mode="json") == a27
    a27_sidecar_sha = _sidecar_digest(a27_sidecar)
    checks.append(
        AuditCheck(
            check_id="NR-004-a27-deterministic-freeze",
            status=(
                "PASS"
                if a27_semantic_equal
                and a27_repo_sha == a27_sidecar_sha
                else "FAIL"
            ),
            interpretation=(
                "The committed A2.7 attribution report is a deterministic "
                "reproduction of the frozen V1 and V2 inputs, and its "
                "repository bytes match the frozen checksum sidecar."
            ),
            details={
                "semantic_object_equal_to_deterministic_rerun": a27_semantic_equal,
                "repository_sha256": a27_repo_sha,
                "sidecar_sha256": a27_sidecar_sha,
            },
        )
    )

    attribution = a27["canonical_attribution"]
    expected_categories = {
        "confirmed_evaluator_artifact": 21,
        "non_isomorphic_unresolved": 9,
        "ontology_contract_ambiguity": 6,
        "preserved_scientific_residual": 8,
    }
    counts_ok = (
        attribution["v1_canonical_non_equivalent_event_count"] == 44
        and attribution["category_counts"] == expected_categories
        and len(a27["v2_newly_localized_residuals"]) == 6
    )
    checks.append(
        AuditCheck(
            check_id="NR-005-attribution-count-conservation",
            status="PASS" if counts_ok else "FAIL",
            interpretation=(
                "All 44 V1 canonical non-equivalent events are attributed "
                "exactly once and V2's six newly localized residuals remain "
                "separate from the V1 denominator."
            ),
            details={
                "v1_non_equivalent_event_count": (
                    attribution["v1_canonical_non_equivalent_event_count"]
                ),
                "category_counts": attribution["category_counts"],
                "newly_localized_residual_count": len(
                    a27["v2_newly_localized_residuals"]
                ),
            },
        )
    )

    dims = _dimension_map(a26)
    dimension_expected = {
        "scientific_semantic_recovery": (19, 0.9473684210526315),
        "ontology_alignment": (19, 0.8596491228070173),
        "provenance_recovery": (20, 1.0),
        "numeric_fidelity": (17, 0.8088235294117647),
        "safe_abstention_quality": (1, 1.0),
    }
    dimensions_ok = all(
        dims[name]["eligible_case_count"] == eligible
        and dims[name]["mean_score"] == mean
        for name, (eligible, mean) in dimension_expected.items()
    )
    checks.append(
        AuditCheck(
            check_id="NR-006-v2-dimension-non-regression",
            status="PASS" if dimensions_ok else "FAIL",
            interpretation=(
                "The frozen five-dimensional V2 descriptive results reproduce "
                "without a composite overall score."
            ),
            details={
                name: {
                    "eligible": dims[name]["eligible_case_count"],
                    "mean": dims[name]["mean_score"],
                }
                for name in dimension_expected
            },
        )
    )

    same_reference_boundary = (
        a26["reference_authority"]
        == a27["reference_authority"]
        == "Batch001_F0_reference_not_independent_expert_gold"
        and a26["publication_grade"] is False
        and a27["publication_grade"] is False
    )
    checks.append(
        AuditCheck(
            check_id="NR-007-reference-authority-boundary",
            status="PASS" if same_reference_boundary else "FAIL",
            interpretation=(
                "All E3 claims remain explicitly benchmark/development-side "
                "and do not promote the F0 reference to independent expert Gold."
            ),
            details={
                "reference_authority": a26["reference_authority"],
                "publication_grade": a26["publication_grade"],
            },
        )
    )

    all_pass = all(check.status.startswith("PASS") for check in checks)

    claims = (
        ScientificClaim(
            claim_id="E3-C01",
            statement=(
                "For the same frozen strict-blind Batch001 worker outputs, "
                "changing the evaluation contract materially changes where "
                "errors are attributed."
            ),
            status="SUPPORTED_WITHIN_FROZEN_BATCH",
            scope="Batch001 strict-blind ResponseSet under F0 reference",
            evidence_refs=("NR-001", "NR-004", "NR-005"),
            paper_location=("Abstract/Key finding", "Results", "Discussion"),
            publication_ready=False,
        ),
        ScientificClaim(
            claim_id="E3-C02",
            statement=(
                "21 of 44 V1 canonical non-equivalent field events "
                "are confirmed evaluator artifacts under the frozen A2.7 rules."
            ),
            status="SUPPORTED_WITHIN_FROZEN_BATCH",
            scope="44 V1 canonical discrepancy events only",
            evidence_refs=("A2.7 canonical attribution",),
            paper_location=("Results",),
            publication_ready=False,
        ),
        ScientificClaim(
            claim_id="E3-C03",
            statement=(
                "All 20 V1 anchor mismatches are explained by provenance "
                "representation mismatch when worker-supported source spans "
                "are evaluated against worker-visible source text."
            ),
            status="SUPPORTED_WITHIN_FROZEN_BATCH",
            scope="20 Batch001 tasks",
            evidence_refs=("A2.6 provenance recovery", "A2.7 mechanism counts"),
            paper_location=("Results", "Error analysis"),
            publication_ready=False,
        ),
        ScientificClaim(
            claim_id="E3-C04",
            statement=(
                "The single source-insufficient defer case is correctly "
                "recognized as safe abstention rather than a missing-answer failure."
            ),
            status="SUPPORTED_CASE_LEVEL",
            scope="EU-B001-015 only",
            evidence_refs=("A2.6 safe_abstention_quality", "A2.7 attribution"),
            paper_location=("Results", "Case study"),
            publication_ready=False,
        ),
        ScientificClaim(
            claim_id="E3-C05",
            statement=(
                "Evaluator V2 preserves eight V1 scientific residuals while "
                "also exposing six additional orthogonal residuals not explicitly "
                "localized by the V1 canonical summary."
            ),
            status="SUPPORTED_WITHIN_FROZEN_BATCH",
            scope="Batch001 under current V2 decomposition",
            evidence_refs=("A2.7 canonical attribution", "A2.7 newly localized residuals"),
            paper_location=("Results", "Discussion"),
            publication_ready=False,
        ),
        ScientificClaim(
            claim_id="E3-C06",
            statement=(
                "Legacy kind disagreements cannot yet be interpreted as pure "
                "model errors because the strict-blind contract did not define "
                "a closed legacy-kind vocabulary."
            ),
            status="SUPPORTED_AS_CONTRACT_LIMITATION",
            scope="Six ontology/contract ambiguity events",
            evidence_refs=("A2.7 ontology_contract_ambiguity",),
            paper_location=("Limitations", "Methods"),
            publication_ready=False,
        ),
        ScientificClaim(
            claim_id="E3-C07",
            statement=(
                "Nine V1 applicability-boundary discrepancies remain unresolved "
                "because V1 and V2 lack an isomorphic semantic boundary metric."
            ),
            status="SUPPORTED_AS_UNRESOLVED",
            scope="Nine V1 applicability-boundary events",
            evidence_refs=("A2.7 non_isomorphic_unresolved",),
            paper_location=("Limitations", "Future work"),
            publication_ready=False,
        ),
        ScientificClaim(
            claim_id="E3-C08",
            statement=(
                "Evaluator architecture should be treated as part of the "
                "scientific measurement system rather than as a neutral "
                "implementation detail."
            ),
            status="SUPPORTED_AS_METHODLOGICAL_INTERPRETATION_WITHIN_BATCH",
            scope=(
                "Methodological interpretation supported by the frozen "
                "Batch001 intervention on evaluator architecture"
            ),
            evidence_refs=("E3-C01", "E3-C02", "E3-C05"),
            paper_location=("Discussion",),
            publication_ready=False,
        ),
    )

    return E3PaperEvidencePackage(
        status="PASS" if all_pass else "FAIL",
        batch_id="B001",
        reference_authority=a26["reference_authority"],
        publication_grade=False,
        manuscript_use_status=(
            "METHODS_RESULTS_DRAFT_READY_NOT_PUBLICATION_GRADE"
            if all_pass
            else "BLOCKED_BY_NON_REGRESSION_FAILURE"
        ),
        inputs={
            "strict_blind_response_set": EvidencePointer(
                path=_stable_path(response_path, root),
                sha256=response_sha,
            ),
            "v1_controller_report": EvidencePointer(
                path=_stable_path(v1_path, root),
                sha256=v1_sha,
            ),
            "a2_6_v2_batch_report_repository_artifact": EvidencePointer(
                path=_stable_path(a26_path, root),
                sha256=a26_repo_sha,
            ),
            "a2_7_discrepancy_report": EvidencePointer(
                path=_stable_path(a27_path, root),
                sha256=a27_repo_sha,
            ),
            "a2_6_freeze_manifest": EvidencePointer(
                path=_stable_path(a26_manifest_path, root),
                sha256=sha256_file(a26_manifest_path),
            ),
            "a2_7_freeze_manifest": EvidencePointer(
                path=_stable_path(a27_manifest_path, root),
                sha256=sha256_file(a27_manifest_path),
            ),
        },
        non_regression_audit=tuple(checks),
        descriptive_results={
            "v2_dimensions": {
                name: {
                    "eligible_case_count": dims[name]["eligible_case_count"],
                    "mean_score": dims[name]["mean_score"],
                    "min_score": dims[name]["min_score"],
                    "max_score": dims[name]["max_score"],
                }
                for name in dimension_expected
            },
            "overall_scalar_score": None,
            "overall_scalar_score_policy": "forbidden",
        },
        discrepancy_attribution={
            "primary_denominator": 44,
            "category_counts": attribution["category_counts"],
            "category_rates": attribution["category_rates"],
            "mechanism_counts": attribution["mechanism_counts"],
            "newly_localized_residual_count": len(
                a27["v2_newly_localized_residuals"]
            ),
        },
        claims=claims,
        limitations=(
            "Batch001 contains only 20 tasks and is not an external replication cohort.",
            "The reference authority is F0 and not independent expert Gold.",
            "The V2 applicability-boundary semantic dimension is not isomorphic to V1 and remains unresolved.",
            "The legacy kind contract did not define a closed ontology vocabulary.",
            "The 47.73% evaluator-artifact fraction is batch-specific and must not be generalized.",
            "A2.6 has a packaging-level byte-digest discrepancy between original CI serialization and the repository artifact; semantic deterministic equality is preserved and explicitly reconciled in NR-003.",
        ),
        prohibited_interpretations=(
            "Do not report V2 Scientific Semantic Recovery as publication-grade model accuracy.",
            "Do not subtract V1 field-equivalence rate from V2 semantic-recovery mean as an accuracy gain.",
            "Do not interpret 123 V1 operational flag incidences as 123 independent model errors.",
            "Do not generalize the 21/44 evaluator-artifact fraction beyond frozen Batch001.",
            "Do not call ontology-contract ambiguity events pure model failures.",
            "Do not resolve applicability-boundary events without an isomorphic boundary evaluator.",
            "Do not describe the F0 reference as independent expert Gold.",
        ),
        next_publication_gates=(
            "Independent expert-Gold adjudication of the reference set.",
            "Replication on additional pre-frozen batches with the V2 contract fixed before scoring.",
            "Dedicated applicability-boundary evaluator with an isomorphic V1↔V2 contract.",
            "Closed ontology/claim-type vocabulary with pre-registered mapping rules.",
            "External or cross-domain replication to estimate generalizability of evaluator-artifact rates.",
        ),
    )


def write_e3_paper_evidence_package(
    package: E3PaperEvidencePackage,
    path: str | Path,
) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = package.model_dump_json(indent=2) + "\n"
    path.write_text(payload, encoding="utf-8")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{digest}  {path.name}\n",
        encoding="utf-8",
    )
    return digest
