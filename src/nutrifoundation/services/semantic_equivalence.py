from __future__ import annotations

from typing import Any

from nutrifoundation.domain.semantic_equivalence import (
    EquivalenceRelation,
    EquivalenceResult,
)
from nutrifoundation.services.canonicalization import canonicalize, conflict_tags


FIELD_GENERIC_CONCEPTS = {
    "population": {"adults", "people", "participants", "patients", "cohort"},
    "intervention": {"diet", "dietary", "pattern", "intake", "higher"},
    "exposure": {"diet", "dietary", "pattern", "intake", "higher", "share"},
    "intervention_or_exposure": {
        "diet", "dietary", "pattern", "intake", "higher", "share"
    },
    "comparator": {"diet", "dietary", "pattern"},
    "outcome": {"outcome", "risk", "change"},
    "applicability_boundary": {"evidence", "population", "adults"},
}


FIELD_THRESHOLDS = {
    "kind": 0.80,
    "population": 0.45,
    "intervention": 0.45,
    "exposure": 0.45,
    "intervention_or_exposure": 0.45,
    "comparator": 0.45,
    "outcome": 0.45,
    "effect": 0.35,
    "recommendation": 0.35,
    "applicability_boundary": 0.30,
    "anchor": 0.50,
}


def overlap_coefficient(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def _informative_concepts(field: str, concepts: set[str]) -> set[str]:
    generic = FIELD_GENERIC_CONCEPTS.get(field, set())
    filtered = concepts - generic
    return filtered or concepts


def _numeric_recall(reference_numbers: set[str], candidate_numbers: set[str]) -> float | None:
    if not reference_numbers:
        return None
    return len(reference_numbers & candidate_numbers) / len(reference_numbers)


def compare_field(field: str, reference_value: Any, candidate_value: Any) -> EquivalenceResult:
    reference = canonicalize(field, reference_value)
    candidate = canonicalize(field, candidate_value)

    if reference_value is None:
        relation = EquivalenceRelation.NOT_APPLICABLE
        return EquivalenceResult(
            field=field,
            relation=relation.value,
            equivalent=True,
            concept_overlap=1.0,
            numeric_recall=None,
            conflict_tags=(),
            reference=reference,
            candidate=candidate,
            rationale=("reference_not_applicable",),
        )

    if candidate_value is None or not candidate.normalized_text:
        relation = EquivalenceRelation.MISSING
        return EquivalenceResult(
            field=field,
            relation=relation.value,
            equivalent=False,
            concept_overlap=0.0,
            numeric_recall=0.0 if reference.numbers else None,
            conflict_tags=(),
            reference=reference,
            candidate=candidate,
            rationale=("candidate_missing",),
        )

    ref_concepts = _informative_concepts(field, set(reference.concepts))
    cand_concepts = _informative_concepts(field, set(candidate.concepts))
    overlap = overlap_coefficient(ref_concepts, cand_concepts)
    num_recall = _numeric_recall(set(reference.numbers), set(candidate.numbers))
    conflicts = conflict_tags(reference, candidate)
    reasons: list[str] = []

    if field == "anchor":
        ref_ids, cand_ids = set(reference.identifiers), set(candidate.identifiers)
        same_identifier = bool(ref_ids & cand_ids) if ref_ids else False
        if ref_ids and cand_ids and not same_identifier:
            return EquivalenceResult(
                field=field,
                relation=EquivalenceRelation.MISMATCH.value,
                equivalent=False,
                concept_overlap=overlap,
                numeric_recall=num_recall,
                conflict_tags=conflicts,
                reference=reference,
                candidate=candidate,
                rationale=("different_source_identifier",),
            )
        if same_identifier:
            return EquivalenceResult(
                field=field,
                relation=EquivalenceRelation.EQUIVALENT.value,
                equivalent=True,
                concept_overlap=max(overlap, 1.0),
                numeric_recall=num_recall,
                conflict_tags=conflicts,
                reference=reference,
                candidate=candidate,
                rationale=("shared_source_identifier",),
            )

    if conflicts:
        reasons.append("semantic_conflict")

    threshold = FIELD_THRESHOLDS.get(field, 0.45)
    numeric_required = field == "effect" and bool(reference.numbers)
    numeric_ok = (num_recall is None) or num_recall >= 0.80

    if field == "kind":
        shared = set(reference.semantic_tags) & set(candidate.semantic_tags)
        equivalent = bool(shared) and not conflicts
        relation = (
            EquivalenceRelation.EQUIVALENT
            if equivalent
            else EquivalenceRelation.MISMATCH
        )
        reasons.append("shared_kind_family" if equivalent else "different_kind_family")
    elif not conflicts and overlap >= threshold and (not numeric_required or numeric_ok):
        ref_subset = ref_concepts.issubset(cand_concepts)
        cand_subset = cand_concepts.issubset(ref_concepts)
        if ref_subset or cand_subset or overlap >= 0.80:
            relation = EquivalenceRelation.EQUIVALENT
            reasons.append("canonical_concepts_equivalent")
        else:
            relation = EquivalenceRelation.COMPATIBLE_SUPERSET
            reasons.append("canonical_concepts_compatible")
        equivalent = True
    elif not conflicts and overlap >= max(0.20, threshold * 0.60):
        relation = EquivalenceRelation.PARTIAL
        equivalent = False
        reasons.append("partial_canonical_overlap")
        if numeric_required and not numeric_ok:
            reasons.append("insufficient_numeric_coverage")
    else:
        relation = EquivalenceRelation.MISMATCH
        equivalent = False
        reasons.append("insufficient_canonical_overlap")
        if numeric_required and not numeric_ok:
            reasons.append("insufficient_numeric_coverage")

    return EquivalenceResult(
        field=field,
        relation=relation.value,
        equivalent=equivalent,
        concept_overlap=overlap,
        numeric_recall=num_recall,
        conflict_tags=conflicts,
        reference=reference,
        candidate=candidate,
        rationale=tuple(reasons),
    )
