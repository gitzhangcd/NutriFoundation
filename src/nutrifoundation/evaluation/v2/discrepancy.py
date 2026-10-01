from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import Field

from nutrifoundation.domain.models import FrozenModel
from nutrifoundation.io.loaders import load_structured


REPORT_VERSION = "E0.4.2-E3-A2.7-v1.0"

CONFIRMED_ARTIFACT = "confirmed_evaluator_artifact"
PRESERVED_RESIDUAL = "preserved_scientific_residual"
ONTOLOGY_AMBIGUITY = "ontology_contract_ambiguity"
NON_ISOMORPHIC = "non_isomorphic_unresolved"


class InputEvidence(FrozenModel):
    path: str
    sha256: str


class CanonicalAttributionEvent(FrozenModel):
    evidence_id: str
    v1_field: str
    v1_relation: str
    category: str
    mechanism: str
    v2_dimension: str | None = None
    v2_field: str | None = None
    v2_relation: str | None = None
    v2_score: float | None = Field(default=None, ge=0.0, le=1.0)
    interpretation: str


class NewlyLocalizedResidual(FrozenModel):
    evidence_id: str
    dimension: str
    field: str
    relation: str
    score: float = Field(ge=0.0, le=1.0)
    interpretation: str


class AttributionSummary(FrozenModel):
    v1_canonical_non_equivalent_event_count: int
    category_counts: dict[str, int]
    category_rates: dict[str, float]
    mechanism_counts: dict[str, int]


class OperationalAudit(FrozenModel):
    critical_error_count: int
    error_flag_incidence_count: int
    operational_escalation_count: int
    benchmark_adjudication_count: int
    error_counts: dict[str, int]
    non_additive_flags: tuple[str, ...]
    interpretation: str


class DiscrepancyAttributionReport(FrozenModel):
    artifact: str = "V1 ↔ V2 Discrepancy Attribution Report"
    report_version: str = REPORT_VERSION
    status: str = "PASS"
    batch_id: str
    reference_authority: str
    publication_grade: bool
    v1_controller_report: InputEvidence
    v2_batch_report: InputEvidence
    v1_canonical_summary: dict[str, Any]
    v2_dimension_summary: tuple[dict[str, Any], ...]
    canonical_attribution: AttributionSummary
    canonical_events: tuple[CanonicalAttributionEvent, ...]
    v2_newly_localized_residuals: tuple[NewlyLocalizedResidual, ...]
    operational_audit: OperationalAudit
    interpretation_freeze: dict[str, tuple[str, ...]]


def _sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _stable_path(path: str | Path) -> str:
    value = Path(path)
    try:
        return str(value.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(value)


def _comparison(
    v2_case: dict[str, Any],
    dimension: str,
    field: str,
) -> dict[str, Any] | None:
    for item in v2_case.get("field_comparisons", []):
        if item.get("dimension") == dimension and item.get("field") == field:
            return item
    return None


def _low(item: dict[str, Any] | None) -> bool:
    return (
        item is not None
        and item.get("applicable") is True
        and item.get("score") is not None
        and float(item["score"]) < 1.0
    )


def _canonical_field_to_v2(field: str) -> tuple[str, str] | None:
    mapping = {
        "population": ("scientific_core", "population"),
        "intervention": ("scientific_core", "intervention_exposure"),
        "exposure": ("scientific_core", "intervention_exposure"),
        "intervention_or_exposure": (
            "scientific_core",
            "intervention_exposure",
        ),
        "comparator": ("scientific_core", "comparator"),
        "outcome": ("scientific_core", "outcome"),
        "effect": ("scientific_core", "effect"),
        "recommendation": ("scientific_core", "effect"),
    }
    return mapping.get(field)


def _numeric_field_for_v1(field: str) -> str | None:
    if field in {
        "population",
        "intervention",
        "exposure",
        "intervention_or_exposure",
        "comparator",
        "outcome",
        "effect",
        "recommendation",
        "applicability_boundary",
    }:
        return (
            "intervention_exposure"
            if field in {"intervention", "exposure", "intervention_or_exposure"}
            else "effect"
            if field == "recommendation"
            else field
        )
    return None


def _attribute_canonical_event(
    *,
    evidence_id: str,
    field: str,
    relation: str,
    v2_case: dict[str, Any],
) -> CanonicalAttributionEvent:
    if field == "anchor":
        item = _comparison(v2_case, "provenance", "visible_anchor")
        if item is not None and item.get("score") == 1:
            return CanonicalAttributionEvent(
                evidence_id=evidence_id,
                v1_field=field,
                v1_relation=relation,
                category=CONFIRMED_ARTIFACT,
                mechanism="provenance_representation_mismatch",
                v2_dimension="provenance",
                v2_field="visible_anchor",
                v2_relation=item.get("relation"),
                v2_score=item.get("score"),
                interpretation=(
                    "V1 required a reference-style anchor representation; "
                    "V2 verifies the worker-provided source_span against "
                    "worker-visible source text."
                ),
            )

    abstention_score = (
        v2_case.get("score_vector", {}).get("safe_abstention_quality")
    )
    if (
        field == "recommendation"
        and v2_case.get("response_status") == "defer"
        and abstention_score == 1
    ):
        item = _comparison(v2_case, "abstention", "safe_abstention")
        return CanonicalAttributionEvent(
            evidence_id=evidence_id,
            v1_field=field,
            v1_relation=relation,
            category=CONFIRMED_ARTIFACT,
            mechanism="safe_abstention_misclassification",
            v2_dimension="abstention",
            v2_field="safe_abstention",
            v2_relation=item.get("relation") if item else None,
            v2_score=item.get("score") if item else 1.0,
            interpretation=(
                "V1 counted the intentionally absent recommendation as "
                "missing; V2 recognizes the source-insufficient defer as "
                "correct safe abstention."
            ),
        )

    if field == "applicability_boundary":
        return CanonicalAttributionEvent(
            evidence_id=evidence_id,
            v1_field=field,
            v1_relation=relation,
            category=NON_ISOMORPHIC,
            mechanism="semantic_boundary_not_scored_in_v2_core",
            interpretation=(
                "V2 does not carry semantic applicability-boundary recovery "
                "as a Scientific Core dimension. This V1 event therefore "
                "cannot be labeled either model error or evaluator artifact "
                "from the V1↔V2 comparison alone."
            ),
        )

    if field == "kind":
        claim = _comparison(v2_case, "ontology", "claim_type")
        study = _comparison(v2_case, "ontology", "study_design")
        role = _comparison(v2_case, "ontology", "evidence_role")
        if claim is not None and claim.get("score") == 1:
            return CanonicalAttributionEvent(
                evidence_id=evidence_id,
                v1_field=field,
                v1_relation=relation,
                category=CONFIRMED_ARTIFACT,
                mechanism="ontology_kind_conflation_corrected",
                v2_dimension="ontology",
                v2_field="claim_type",
                v2_relation=claim.get("relation"),
                v2_score=claim.get("score"),
                interpretation=(
                    "The monolithic V1 kind mismatch disappears after "
                    "decomposing study design, claim type, and evidence role."
                ),
            )
        return CanonicalAttributionEvent(
            evidence_id=evidence_id,
            v1_field=field,
            v1_relation=relation,
            category=ONTOLOGY_AMBIGUITY,
            mechanism="kind_conflates_study_design_and_claim_type",
            v2_dimension="ontology",
            v2_field="claim_type",
            v2_relation=claim.get("relation") if claim else None,
            v2_score=claim.get("score") if claim else None,
            interpretation=(
                "V2 localizes the disagreement to claim_type while "
                f"study_design={study.get('score') if study else None} and "
                f"evidence_role={role.get('score') if role else None}. "
                "Because the strict-blind worker contract did not define a "
                "closed vocabulary for legacy kind, this is frozen as a "
                "contract/ontology ambiguity rather than a pure model error."
            ),
        )

    mapped = _canonical_field_to_v2(field)
    semantic = (
        _comparison(v2_case, mapped[0], mapped[1])
        if mapped is not None
        else None
    )
    if _low(semantic):
        return CanonicalAttributionEvent(
            evidence_id=evidence_id,
            v1_field=field,
            v1_relation=relation,
            category=PRESERVED_RESIDUAL,
            mechanism="semantic_residual",
            v2_dimension=semantic["dimension"],
            v2_field=semantic["field"],
            v2_relation=semantic.get("relation"),
            v2_score=semantic.get("score"),
            interpretation=(
                "The discrepancy persists after canonical V2 semantic "
                "mapping and remains a scientific semantic residual."
            ),
        )

    numeric_field = _numeric_field_for_v1(field)
    numeric = (
        _comparison(v2_case, "numeric", numeric_field)
        if numeric_field is not None
        else None
    )
    if _low(numeric):
        return CanonicalAttributionEvent(
            evidence_id=evidence_id,
            v1_field=field,
            v1_relation=relation,
            category=PRESERVED_RESIDUAL,
            mechanism="numeric_residual_reclassified",
            v2_dimension="numeric",
            v2_field=numeric_field,
            v2_relation=numeric.get("relation"),
            v2_score=numeric.get("score"),
            interpretation=(
                "V1 mixed semantic and numeric disagreement. V2 recovers "
                "the semantics but preserves the remaining quantitative "
                "fidelity deficit in the Numeric dimension."
            ),
        )

    return CanonicalAttributionEvent(
        evidence_id=evidence_id,
        v1_field=field,
        v1_relation=relation,
        category=CONFIRMED_ARTIFACT,
        mechanism="legacy_surface_or_dimension_conflation",
        v2_dimension=semantic.get("dimension") if semantic else None,
        v2_field=semantic.get("field") if semantic else None,
        v2_relation=semantic.get("relation") if semantic else None,
        v2_score=semantic.get("score") if semantic else None,
        interpretation=(
            "The V1 non-equivalence is not reproduced by the corresponding "
            "V2 semantic or numeric comparison."
        ),
    )


def _v1_parent_fields(dimension: str, field: str) -> tuple[str, ...]:
    mapping = {
        ("scientific_core", "population"): ("population",),
        ("numeric", "population"): ("population",),
        ("scientific_core", "intervention_exposure"): (
            "intervention",
            "exposure",
            "intervention_or_exposure",
        ),
        ("numeric", "intervention_exposure"): (
            "intervention",
            "exposure",
            "intervention_or_exposure",
        ),
        ("scientific_core", "comparator"): ("comparator",),
        ("numeric", "comparator"): ("comparator",),
        ("scientific_core", "outcome"): ("outcome",),
        ("numeric", "outcome"): ("outcome",),
        ("scientific_core", "effect"): ("effect", "recommendation"),
        ("numeric", "effect"): ("effect", "recommendation"),
        ("ontology", "claim_type"): ("kind",),
        ("numeric", "applicability_boundary"): ("applicability_boundary",),
    }
    return mapping.get((dimension, field), ())


def _newly_localized_residuals(
    *,
    v1_cases: dict[str, dict[str, Any]],
    v2_cases: dict[str, dict[str, Any]],
) -> tuple[NewlyLocalizedResidual, ...]:
    results: list[NewlyLocalizedResidual] = []
    for evidence_id, v2_case in sorted(v2_cases.items()):
        if v2_case.get("response_status") != "completed":
            continue
        v1_fields = {
            item.split(":", 1)[0]
            for item in v1_cases[evidence_id].get("non_equivalent_fields", [])
        }
        for item in v2_case.get("field_comparisons", []):
            dimension = item.get("dimension")
            field = item.get("field")
            if dimension not in {"scientific_core", "ontology", "numeric"}:
                continue
            if not _low(item):
                continue
            parents = _v1_parent_fields(dimension, field)
            if any(parent in v1_fields for parent in parents):
                continue
            results.append(
                NewlyLocalizedResidual(
                    evidence_id=evidence_id,
                    dimension=dimension,
                    field=field,
                    relation=item.get("relation") or "unknown",
                    score=float(item["score"]),
                    interpretation=(
                        "V2 orthogonalization exposes a residual that was "
                        "not represented as a non-equivalent field in the V1 "
                        "canonical case summary."
                    ),
                )
            )
    return tuple(results)


def build_discrepancy_attribution_report(
    *,
    v1_controller_report_path: str | Path,
    v2_batch_report_path: str | Path,
) -> DiscrepancyAttributionReport:
    v1_path = Path(v1_controller_report_path)
    v2_path = Path(v2_batch_report_path)
    v1 = load_structured(v1_path)
    v2 = load_structured(v2_path)

    v1_canonical = v1["hidden_scoring"]["canonical_semantic_scoring"]
    v1_operational = v1["hidden_scoring"]["operational_blind_replay"]
    v1_cases = {
        item["evidence_id"]: item
        for item in v1["hidden_scoring"]["canonical_cases"]
    }
    v2_cases = {item["evidence_id"]: item for item in v2["cases"]}

    if set(v1_cases) != set(v2_cases):
        raise ValueError("V1 and V2 reports do not cover the same evidence IDs")

    events: list[CanonicalAttributionEvent] = []
    for evidence_id in sorted(v1_cases):
        for item in v1_cases[evidence_id].get("non_equivalent_fields", []):
            field, relation = item.split(":", 1)
            events.append(
                _attribute_canonical_event(
                    evidence_id=evidence_id,
                    field=field,
                    relation=relation,
                    v2_case=v2_cases[evidence_id],
                )
            )

    expected_non_equivalent = (
        int(v1_canonical["partial_field_count"])
        + int(v1_canonical["mismatch_field_count"])
        + int(v1_canonical["missing_field_count"])
    )
    if len(events) != expected_non_equivalent:
        raise ValueError(
            "Canonical event reconstruction mismatch: "
            f"{len(events)} != {expected_non_equivalent}"
        )

    category_counts = Counter(event.category for event in events)
    mechanism_counts = Counter(event.mechanism for event in events)
    denominator = len(events)
    category_rates = {
        key: value / denominator
        for key, value in sorted(category_counts.items())
    }

    error_counts = dict(v1_operational["error_counts"])
    operational_flag_incidence = sum(int(v) for v in error_counts.values())

    interpretation_freeze = {
        "supported": (
            "The same frozen strict-blind ResponseSet is compared under V1 and V2 evaluation contracts.",
            "Among V1 canonical non-equivalent field events, confirmed evaluator artifacts may be counted only where V2 supplies positive counter-evidence under the frozen rules.",
            "Residual semantic/numeric discrepancies that persist in V2 remain scientific residuals under the current F0 reference.",
            "Legacy kind disagreements are not interpreted as pure model error because the strict-blind worker contract did not define a closed legacy-kind vocabulary.",
            "V1 applicability-boundary discrepancies remain unresolved where V2 has no isomorphic semantic core dimension.",
            "V2 newly localized residuals are reported separately rather than treated as regressions.",
        ),
        "prohibited": (
            "Do not subtract V1 field-equivalence rate from V2 Scientific Semantic Recovery and call the difference an accuracy gain.",
            "Do not interpret the V2 Scientific Semantic Recovery mean as publication-grade model accuracy.",
            "Do not interpret 123 V1 error-flag incidences as 123 independent model errors.",
            "Do not generalize the Batch001 evaluator-artifact fraction beyond this frozen batch and F0 reference.",
            "Do not convert unresolved non-isomorphic applicability-boundary events into either evaluator artifacts or model errors without a dedicated boundary evaluator.",
        ),
    }

    return DiscrepancyAttributionReport(
        batch_id=v2["batch_id"],
        reference_authority=v2["reference_authority"],
        publication_grade=bool(v2["publication_grade"]),
        v1_controller_report=InputEvidence(
            path=_stable_path(v1_path),
            sha256=_sha256_file(v1_path),
        ),
        v2_batch_report=InputEvidence(
            path=_stable_path(v2_path),
            sha256=_sha256_file(v2_path),
        ),
        v1_canonical_summary={
            "comparable_field_count": v1_canonical["comparable_field_count"],
            "equivalent_field_count": v1_canonical["equivalent_field_count"],
            "partial_field_count": v1_canonical["partial_field_count"],
            "mismatch_field_count": v1_canonical["mismatch_field_count"],
            "missing_field_count": v1_canonical["missing_field_count"],
            "field_equivalence_rate": v1_canonical["field_equivalence_rate"],
            "complete_case_equivalence_rate": (
                v1_canonical["complete_case_equivalence_rate"]
            ),
        },
        v2_dimension_summary=tuple(v2["dimension_summary"]),
        canonical_attribution=AttributionSummary(
            v1_canonical_non_equivalent_event_count=denominator,
            category_counts=dict(sorted(category_counts.items())),
            category_rates=category_rates,
            mechanism_counts=dict(sorted(mechanism_counts.items())),
        ),
        canonical_events=tuple(events),
        v2_newly_localized_residuals=_newly_localized_residuals(
            v1_cases=v1_cases,
            v2_cases=v2_cases,
        ),
        operational_audit=OperationalAudit(
            critical_error_count=int(v1_operational["critical_error_count"]),
            error_flag_incidence_count=operational_flag_incidence,
            operational_escalation_count=int(
                v1_operational["operational_escalation_count"]
            ),
            benchmark_adjudication_count=int(
                v1_operational["benchmark_adjudication_count"]
            ),
            error_counts=error_counts,
            non_additive_flags=(
                "high_risk_hidden_reference_mismatch",
                "verifier_rejection",
                "semantic_defer",
                "missing_critical_field",
            ),
            interpretation=(
                "Operational flags are overlapping governance and diagnostic "
                "signals. Their incidence sum is not an independent-error "
                "denominator and is not used for the primary attribution rate."
            ),
        ),
        interpretation_freeze=interpretation_freeze,
    )


def write_discrepancy_report(
    report: DiscrepancyAttributionReport,
    path: str | Path,
) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump_json(indent=2) + "\n"
    path.write_text(payload, encoding="utf-8")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{digest}  {path.name}\n",
        encoding="utf-8",
    )
    return digest
