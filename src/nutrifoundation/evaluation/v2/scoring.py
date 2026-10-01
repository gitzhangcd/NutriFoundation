from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import Field

from nutrifoundation.domain.models import FrozenModel
from nutrifoundation.domain.semantic_equivalence import EquivalenceRelation
from nutrifoundation.evaluation.v2.compatibility import (
    CanonicalArtifactV2,
    CompatibilityCaseV2,
)
from nutrifoundation.evaluation.v2.schema import (
    AbstentionResult,
    EvaluationMetadata,
    EvaluationResultV2,
    NumericFidelityResult,
    OntologyAlignmentResult,
    ProvenanceResult,
    ScientificCoreResult,
)
from nutrifoundation.services.semantic_equivalence import (
    FIELD_THRESHOLDS,
    compare_field,
)


EVALUATOR_VERSION = "EvaluatorV2-v0.1"

DimensionName = Literal[
    "scientific_core",
    "ontology",
    "numeric",
    "provenance",
    "abstention",
]


class FieldComparisonV2(FrozenModel):
    dimension: DimensionName
    field: str
    applicable: bool
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    relation: str
    reference_value: Any | None = None
    candidate_value: Any | None = None
    rationale: tuple[str, ...] = ()


class ScoredCaseV2(FrozenModel):
    evaluation: EvaluationResultV2
    field_comparisons: tuple[FieldComparisonV2, ...]

    @property
    def score_vector(self) -> dict[str, float | None]:
        return {
            "scientific_semantic_recovery": self.evaluation.scientific_core.score,
            "ontology_alignment": self.evaluation.ontology.score,
            "provenance_recovery": self.evaluation.provenance.score,
            "numeric_fidelity": self.evaluation.numeric.score,
            "safe_abstention_quality": self.evaluation.abstention.score,
        }


def _effect_axis(artifact: CanonicalArtifactV2) -> tuple[Any | None, bool]:
    scientific = artifact.scientific
    if scientific.effect is not None:
        return scientific.effect, False
    if scientific.recommendation is not None:
        return scientific.recommendation, True
    return None, False


def _semantic_score(field: str, result) -> float:
    if result.relation == EquivalenceRelation.NOT_APPLICABLE.value:
        return 1.0
    if result.equivalent:
        return 1.0

    # Numeric fidelity is a separate V2 dimension. If legacy semantic
    # equivalence failed only because numeric coverage was insufficient,
    # recover the semantic score from concept overlap without importing the
    # numeric penalty into Scientific Core.
    numeric_only = (
        "insufficient_numeric_coverage" in result.rationale
        and not result.conflict_tags
    )
    if numeric_only:
        threshold = FIELD_THRESHOLDS.get(field, 0.45)
        if result.concept_overlap >= threshold:
            return 1.0
        if result.concept_overlap >= max(0.20, threshold * 0.60):
            return 0.5

    if result.relation == EquivalenceRelation.PARTIAL.value:
        return 0.5
    return 0.0


def _scientific_comparisons(
    case: CompatibilityCaseV2,
) -> tuple[ScientificCoreResult, list[FieldComparisonV2]]:
    ref = case.reference.scientific
    cand = case.candidate.scientific

    values: list[tuple[str, str, Any | None, Any | None, tuple[str, ...]]] = [
        ("population", "population", ref.population, cand.population, ()),
        (
            "intervention_exposure",
            "intervention",
            ref.intervention_exposure,
            cand.intervention_exposure,
            (),
        ),
        ("comparator", "comparator", ref.comparator, cand.comparator, ()),
        ("outcome", "outcome", ref.outcome, cand.outcome, ()),
    ]

    ref_effect, ref_is_recommendation = _effect_axis(case.reference)
    cand_effect, cand_is_recommendation = _effect_axis(case.candidate)
    effect_notes: tuple[str, ...] = ()
    if ref_is_recommendation:
        effect_notes += ("reference_recommendation_mapped_to_effect_axis",)
    if cand_is_recommendation:
        effect_notes += ("candidate_recommendation_mapped_to_effect_axis",)
    values.append(("effect", "effect", ref_effect, cand_effect, effect_notes))

    scores: dict[str, float] = {}
    comparisons: list[FieldComparisonV2] = []
    for output_field, comparison_field, reference_value, candidate_value, notes in values:
        result = compare_field(
            comparison_field,
            reference_value,
            candidate_value,
        )
        score = _semantic_score(comparison_field, result)
        applicable = result.relation != EquivalenceRelation.NOT_APPLICABLE.value
        scores[output_field] = score
        comparisons.append(
            FieldComparisonV2(
                dimension="scientific_core",
                field=output_field,
                applicable=applicable,
                score=score,
                relation=result.relation,
                reference_value=reference_value,
                candidate_value=candidate_value,
                rationale=tuple(result.rationale) + notes,
            )
        )

    return ScientificCoreResult(**scores), comparisons


def _ontology_axis(
    *,
    field: str,
    reference_value: str | None,
    candidate_value: str | None,
    response_status: str,
) -> tuple[float, FieldComparisonV2]:
    if reference_value is None:
        return 1.0, FieldComparisonV2(
            dimension="ontology",
            field=field,
            applicable=False,
            score=1.0,
            relation="not_applicable",
            reference_value=None,
            candidate_value=candidate_value,
            rationale=("reference_not_applicable",),
        )

    if response_status != "completed":
        return 0.0, FieldComparisonV2(
            dimension="ontology",
            field=field,
            applicable=True,
            score=0.0,
            relation="no_completed_semantic_output",
            reference_value=reference_value,
            candidate_value=candidate_value,
            rationale=("response_not_completed",),
        )

    matched = candidate_value == reference_value
    score = 1.0 if matched else 0.0
    return score, FieldComparisonV2(
        dimension="ontology",
        field=field,
        applicable=True,
        score=score,
        relation="equivalent" if matched else "mismatch",
        reference_value=reference_value,
        candidate_value=candidate_value,
        rationale=("exact_canonical_ontology_match",) if matched else (
            "canonical_ontology_mismatch",
        ),
    )


def _ontology_comparisons(
    case: CompatibilityCaseV2,
) -> tuple[OntologyAlignmentResult, list[FieldComparisonV2]]:
    ref = case.reference.ontology
    cand = case.candidate.ontology
    scores: dict[str, float] = {}
    comparisons: list[FieldComparisonV2] = []

    for field in ("study_design", "claim_type", "evidence_role"):
        score, comparison = _ontology_axis(
            field=field,
            reference_value=getattr(ref, field),
            candidate_value=getattr(cand, field),
            response_status=case.response_status,
        )
        scores[field] = score
        comparisons.append(comparison)

    return OntologyAlignmentResult(**scores), comparisons


def _numeric_comparisons(
    case: CompatibilityCaseV2,
) -> tuple[NumericFidelityResult, list[FieldComparisonV2]]:
    reference = case.reference.numeric.by_field
    candidate = case.candidate.numeric.by_field
    comparisons: list[FieldComparisonV2] = []
    matched = 0

    for field in sorted(reference):
        ref_tokens = set(reference[field])
        cand_tokens = set(candidate.get(field, ()))
        intersection = ref_tokens & cand_tokens
        fully_matched = ref_tokens.issubset(cand_tokens)
        if fully_matched:
            matched += 1
        recall = len(intersection) / len(ref_tokens) if ref_tokens else 1.0
        comparisons.append(
            FieldComparisonV2(
                dimension="numeric",
                field=field,
                applicable=True,
                score=recall,
                relation=(
                    "matched"
                    if fully_matched
                    else "partial"
                    if intersection
                    else "missing"
                ),
                reference_value=tuple(sorted(ref_tokens)),
                candidate_value=tuple(sorted(cand_tokens)),
                rationale=(
                    "all_reference_numeric_tokens_recovered",
                ) if fully_matched else (
                    "partial_reference_numeric_token_recovery",
                ) if intersection else (
                    "reference_numeric_tokens_not_recovered",
                ),
            )
        )

    result = NumericFidelityResult(
        normalized_numeric_fields=len(reference),
        matched_numeric_fields=matched,
    )
    return result, comparisons


def _provenance_comparisons(
    case: CompatibilityCaseV2,
) -> tuple[ProvenanceResult, list[FieldComparisonV2]]:
    reference = case.reference.provenance
    candidate = case.candidate.provenance
    context_ids = set(candidate.context_visible_identifiers)
    ref_ids = set(reference.provided_identifiers)
    cand_ids = set(candidate.provided_identifiers)
    visible_ref_ids = ref_ids & context_ids

    comparisons: list[FieldComparisonV2] = []

    visible_anchor_score: float | None
    if (
        candidate.semantic_anchor is not None
        and candidate.semantic_anchor_supported is not None
    ):
        visible_anchor_score = 1.0 if candidate.semantic_anchor_supported else 0.0
        relation = (
            "source_span_supported"
            if candidate.semantic_anchor_supported
            else "source_span_unsupported"
        )
        rationale = (
            "candidate_source_span_supported_by_worker_visible_source",
        ) if candidate.semantic_anchor_supported else (
            "candidate_source_span_not_supported_by_worker_visible_source",
        )
    elif reference.semantic_anchor is not None:
        if candidate.semantic_anchor is None:
            visible_anchor_score = 0.0
            relation = "missing"
            rationale = ("reference_semantic_anchor_not_recovered",)
        else:
            result = compare_field(
                "anchor",
                reference.semantic_anchor,
                candidate.semantic_anchor,
            )
            visible_anchor_score = 1.0 if result.equivalent else 0.0
            relation = result.relation
            rationale = tuple(result.rationale)
    elif visible_ref_ids:
        matched_visible_id = bool(visible_ref_ids & cand_ids)
        visible_anchor_score = 1.0 if matched_visible_id else 0.0
        relation = "shared_visible_identifier" if matched_visible_id else "missing"
        rationale = (
            "worker_visible_reference_identifier_recovered",
        ) if matched_visible_id else (
            "worker_visible_reference_identifier_not_recovered",
        )
    elif reference.legacy_anchor is not None and candidate.legacy_anchor is not None:
        result = compare_field(
            "anchor",
            reference.legacy_anchor,
            candidate.legacy_anchor,
        )
        visible_anchor_score = 1.0 if result.equivalent else 0.0
        relation = result.relation
        rationale = tuple(result.rationale)
    else:
        visible_anchor_score = None
        relation = "not_applicable"
        rationale = ("reference_anchor_not_observable_for_scoring",)

    comparisons.append(
        FieldComparisonV2(
            dimension="provenance",
            field="visible_anchor",
            applicable=visible_anchor_score is not None,
            score=visible_anchor_score,
            relation=relation,
            reference_value=reference.legacy_anchor or reference.semantic_anchor,
            candidate_value=candidate.legacy_anchor or candidate.semantic_anchor,
            rationale=rationale,
        )
    )

    external_identifier_score: float | None
    if not cand_ids:
        external_identifier_score = None
        ext_relation = "not_asserted"
        ext_rationale = ("candidate_did_not_assert_external_identifier",)
    elif not context_ids:
        external_identifier_score = None
        ext_relation = "not_verifiable"
        ext_rationale = ("no_worker_visible_identifier_context",)
    else:
        identifiers_valid = cand_ids.issubset(context_ids)
        external_identifier_score = 1.0 if identifiers_valid else 0.0
        ext_relation = "valid" if identifiers_valid else "invalid"
        ext_rationale = (
            "all_asserted_identifiers_worker_visible",
        ) if identifiers_valid else (
            "asserted_identifier_not_present_in_worker_visible_context",
        )

    comparisons.append(
        FieldComparisonV2(
            dimension="provenance",
            field="external_identifier",
            applicable=external_identifier_score is not None,
            score=external_identifier_score,
            relation=ext_relation,
            reference_value=tuple(sorted(context_ids)),
            candidate_value=tuple(sorted(cand_ids)),
            rationale=ext_rationale,
        )
    )

    return ProvenanceResult(
        visible_anchor_score=visible_anchor_score,
        external_identifier_score=external_identifier_score,
    ), comparisons


def _abstention_comparison(
    case: CompatibilityCaseV2,
) -> tuple[AbstentionResult, FieldComparisonV2]:
    insufficient = case.abstention.source_information_insufficient is True
    abstained = case.abstention.abstained

    # The dimension becomes applicable in either direction:
    # source insufficiency creates an obligation to abstain, while any actual
    # abstention must be checked for whether it was warranted.
    applicable = insufficient or abstained
    correct = (insufficient and abstained) if applicable else None

    result = AbstentionResult(
        applicable=applicable,
        correct_abstention=correct,
    )

    if not applicable:
        relation = "not_applicable"
        rationale = ("source_sufficient_and_worker_completed",)
    elif correct:
        relation = "correct_safe_abstention"
        rationale = ("source_insufficient_and_worker_deferred",)
    elif insufficient:
        relation = "unsafe_non_abstention"
        rationale = ("source_insufficient_but_worker_did_not_defer",)
    else:
        relation = "unwarranted_abstention"
        rationale = ("worker_deferred_despite_sufficient_source",)

    comparison = FieldComparisonV2(
        dimension="abstention",
        field="safe_abstention",
        applicable=applicable,
        score=result.score,
        relation=relation,
        reference_value={
            "source_information_insufficient": insufficient,
        },
        candidate_value={
            "abstained": abstained,
            "uncertainties": case.abstention.uncertainties,
        },
        rationale=rationale,
    )
    return result, comparison


def score_case_v2(
    case: CompatibilityCaseV2,
    *,
    evaluated_at: datetime | None = None,
) -> ScoredCaseV2:
    scientific, scientific_comparisons = _scientific_comparisons(case)
    ontology, ontology_comparisons = _ontology_comparisons(case)
    numeric, numeric_comparisons = _numeric_comparisons(case)
    provenance, provenance_comparisons = _provenance_comparisons(case)
    abstention, abstention_comparison = _abstention_comparison(case)

    evaluation = EvaluationResultV2(
        task_id=case.task_id,
        response_id=case.response_id,
        evidence_id=case.evidence_id,
        source_id=case.source_id,
        scientific_core=scientific,
        ontology=ontology,
        numeric=numeric,
        provenance=provenance,
        abstention=abstention,
        metadata=EvaluationMetadata(
            evaluator_version=EVALUATOR_VERSION,
            created_at=evaluated_at or datetime.now(timezone.utc),
            worker_visible_information=case.metadata.worker_visible_information,
            reference_visible_information=case.metadata.reference_visible_information,
        ),
    )

    return ScoredCaseV2(
        evaluation=evaluation,
        field_comparisons=tuple(
            scientific_comparisons
            + ontology_comparisons
            + numeric_comparisons
            + provenance_comparisons
            + [abstention_comparison]
        ),
    )


def score_batch_v2(
    cases: tuple[CompatibilityCaseV2, ...],
    *,
    evaluated_at: datetime | None = None,
) -> tuple[ScoredCaseV2, ...]:
    timestamp = evaluated_at or datetime.now(timezone.utc)
    return tuple(
        score_case_v2(case, evaluated_at=timestamp)
        for case in cases
    )
