from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import StrEnum
from typing import Any


class BlindnessClass(StrEnum):
    STRICT = "strict_blind_fresh_context"
    ENGINEERING_ONLY = "engineering_blind_current_context_prior_exposure"


class FieldMatch(StrEnum):
    EXACT = "exact"
    NEAR = "near"
    PARTIAL = "partial"
    MISMATCH = "mismatch"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"


class SemanticErrorType(StrEnum):
    EVIDENCE_KIND_MISMATCH = "evidence_kind_mismatch"
    POPULATION_SCOPE_MISMATCH = "population_scope_mismatch"
    INTERVENTION_EXPOSURE_MISMATCH = "intervention_exposure_mismatch"
    COMPARATOR_MISMATCH = "comparator_mismatch"
    OUTCOME_MISMATCH = "outcome_mismatch"
    NUMERIC_EFFECT_MISMATCH = "numeric_effect_mismatch"
    EFFECT_SEMANTIC_MISMATCH = "effect_semantic_mismatch"
    RECOMMENDATION_MISMATCH = "recommendation_mismatch"
    APPLICABILITY_BOUNDARY_MISMATCH = "applicability_boundary_mismatch"
    SOURCE_ANCHOR_MISMATCH = "source_anchor_mismatch"
    CAUSALITY_LEVEL_MISMATCH = "causality_level_mismatch"
    MISSING_CRITICAL_FIELD = "missing_critical_field"
    VERIFIER_REJECTION = "verifier_rejection"
    SEMANTIC_DEFER = "semantic_defer"


@dataclass(frozen=True)
class FieldScore:
    field: str
    match: str
    lexical_similarity: float | None
    gold_value: Any
    observed_value: Any
    errors: tuple[str, ...] = ()

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class CaseScore:
    evidence_id: str
    source_id: str
    response_status: str
    verifier_status: str
    f0_frozen: bool
    field_scores: tuple[FieldScore, ...]
    critical_error_count: int
    exact_field_count: int
    comparable_field_count: int
    operational_escalation_required: bool
    operational_escalation_reasons: tuple[str, ...]
    benchmark_adjudication_required: bool
    benchmark_adjudication_reasons: tuple[str, ...]
    verifier_errors: tuple[str, ...] = ()
    response_uncertainties: tuple[str, ...] = ()

    def as_dict(self):
        data = asdict(self)
        data["field_scores"] = [x.as_dict() for x in self.field_scores]
        return data


@dataclass(frozen=True)
class BlindReplaySummary:
    batch_id: str
    blindness_class: str
    case_count: int
    completed_response_count: int
    deferred_count: int
    verifier_pass_count: int
    f0_freeze_count: int
    operational_escalation_count: int
    benchmark_adjudication_count: int
    critical_error_count: int
    exact_field_count: int
    near_or_exact_field_count: int
    comparable_field_count: int
    exact_field_rate: float
    near_or_exact_field_rate: float
    verifier_yield: float
    f0_yield: float
    operational_escalation_rate: float
    benchmark_adjudication_rate: float
    error_counts: dict[str, int]
    cases: tuple[CaseScore, ...]

    def as_dict(self):
        data = asdict(self)
        data["cases"] = [x.as_dict() for x in self.cases]
        return data
