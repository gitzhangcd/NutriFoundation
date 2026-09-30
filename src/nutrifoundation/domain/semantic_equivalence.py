from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class EquivalenceRelation(StrEnum):
    EQUIVALENT = "equivalent"
    COMPATIBLE_SUPERSET = "compatible_superset"
    PARTIAL = "partial"
    MISMATCH = "mismatch"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"


class CalibrationReferenceClass(StrEnum):
    CONTRACT_GENERATED = "contract_generated"
    MODEL_ASSISTED_DEVELOPMENT = "model_assisted_development"
    HUMAN_INDEPENDENT = "human_independent"


@dataclass(frozen=True)
class CanonicalSemanticForm:
    field: str
    concepts: tuple[str, ...] = ()
    numbers: tuple[str, ...] = ()
    semantic_tags: tuple[str, ...] = ()
    identifiers: tuple[str, ...] = ()
    normalized_text: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EquivalenceResult:
    field: str
    relation: str
    equivalent: bool
    concept_overlap: float
    numeric_recall: float | None
    conflict_tags: tuple[str, ...]
    reference: CanonicalSemanticForm
    candidate: CanonicalSemanticForm
    rationale: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["reference"] = self.reference.as_dict()
        data["candidate"] = self.candidate.as_dict()
        return data


@dataclass(frozen=True)
class CalibrationConfusionMatrix:
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int

    @property
    def precision(self) -> float:
        d = self.true_positive + self.false_positive
        return self.true_positive / d if d else 0.0

    @property
    def recall(self) -> float:
        d = self.true_positive + self.false_negative
        return self.true_positive / d if d else 0.0

    @property
    def specificity(self) -> float:
        d = self.true_negative + self.false_positive
        return self.true_negative / d if d else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "precision": self.precision,
            "recall": self.recall,
            "specificity": self.specificity,
            "f1": self.f1,
        }


@dataclass(frozen=True)
class EquivalenceCalibrationSummary:
    reference_class: str
    case_count: int
    overall: CalibrationConfusionMatrix
    by_field: dict[str, CalibrationConfusionMatrix]
    false_positive_ids: tuple[str, ...]
    false_negative_ids: tuple[str, ...]
    publication_grade: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "reference_class": self.reference_class,
            "case_count": self.case_count,
            "overall": self.overall.as_dict(),
            "by_field": {k: v.as_dict() for k, v in self.by_field.items()},
            "false_positive_ids": list(self.false_positive_ids),
            "false_negative_ids": list(self.false_negative_ids),
            "publication_grade": self.publication_grade,
        }


@dataclass(frozen=True)
class StrictBlindAttestation:
    fresh_context: bool
    prior_batch_exposure: bool
    hidden_reference_available_to_worker: bool
    independent_worker_session: bool

    @property
    def qualifies(self) -> bool:
        return (
            self.fresh_context
            and not self.prior_batch_exposure
            and not self.hidden_reference_available_to_worker
            and self.independent_worker_session
        )

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "qualifies": self.qualifies}


@dataclass(frozen=True)
class CanonicalCaseResult:
    evidence_id: str
    source_id: str
    response_status: str
    comparable_field_count: int
    equivalent_field_count: int
    partial_field_count: int
    mismatch_field_count: int
    missing_field_count: int
    all_critical_fields_equivalent: bool
    field_results: tuple[EquivalenceResult, ...]

    @property
    def field_equivalence_rate(self) -> float:
        return (
            self.equivalent_field_count / self.comparable_field_count
            if self.comparable_field_count
            else 0.0
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "response_status": self.response_status,
            "comparable_field_count": self.comparable_field_count,
            "equivalent_field_count": self.equivalent_field_count,
            "partial_field_count": self.partial_field_count,
            "mismatch_field_count": self.mismatch_field_count,
            "missing_field_count": self.missing_field_count,
            "all_critical_fields_equivalent": self.all_critical_fields_equivalent,
            "field_equivalence_rate": self.field_equivalence_rate,
            "field_results": [item.as_dict() for item in self.field_results],
        }


@dataclass(frozen=True)
class CanonicalBatchSummary:
    batch_id: str
    reference_authority: str
    publication_grade: bool
    case_count: int
    completed_response_count: int
    deferred_count: int
    comparable_field_count: int
    equivalent_field_count: int
    partial_field_count: int
    mismatch_field_count: int
    missing_field_count: int
    all_critical_equivalent_case_count: int
    cases: tuple[CanonicalCaseResult, ...]

    @property
    def field_equivalence_rate(self) -> float:
        return (
            self.equivalent_field_count / self.comparable_field_count
            if self.comparable_field_count
            else 0.0
        )

    @property
    def complete_case_equivalence_rate(self) -> float:
        return (
            self.all_critical_equivalent_case_count / self.case_count
            if self.case_count
            else 0.0
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "reference_authority": self.reference_authority,
            "publication_grade": self.publication_grade,
            "case_count": self.case_count,
            "completed_response_count": self.completed_response_count,
            "deferred_count": self.deferred_count,
            "comparable_field_count": self.comparable_field_count,
            "equivalent_field_count": self.equivalent_field_count,
            "partial_field_count": self.partial_field_count,
            "mismatch_field_count": self.mismatch_field_count,
            "missing_field_count": self.missing_field_count,
            "all_critical_equivalent_case_count": self.all_critical_equivalent_case_count,
            "field_equivalence_rate": self.field_equivalence_rate,
            "complete_case_equivalence_rate": self.complete_case_equivalence_rate,
            "cases": [case.as_dict() for case in self.cases],
        }


@dataclass(frozen=True)
class SemanticBatchCase:
    evidence_id: str
    source_id: str
    response_status: str
    comparable_field_count: int
    equivalent_field_count: int
    all_critical_fields_equivalent: bool
    non_equivalent_fields: tuple[str, ...]
    field_results: tuple[EquivalenceResult, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "response_status": self.response_status,
            "comparable_field_count": self.comparable_field_count,
            "equivalent_field_count": self.equivalent_field_count,
            "all_critical_fields_equivalent": self.all_critical_fields_equivalent,
            "non_equivalent_fields": list(self.non_equivalent_fields),
            "field_results": [item.as_dict() for item in self.field_results],
        }


@dataclass(frozen=True)
class SemanticBatchSummary:
    batch_id: str
    reference_authority: str
    publication_grade: bool
    case_count: int
    completed_response_count: int
    deferred_count: int
    comparable_field_count: int
    equivalent_field_count: int
    critical_field_equivalence_rate: float
    all_critical_fields_equivalent_count: int
    all_critical_fields_equivalent_rate: float
    benchmark_adjudication_count: int
    benchmark_adjudication_rate: float
    cases: tuple[SemanticBatchCase, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "reference_authority": self.reference_authority,
            "publication_grade": self.publication_grade,
            "case_count": self.case_count,
            "completed_response_count": self.completed_response_count,
            "deferred_count": self.deferred_count,
            "comparable_field_count": self.comparable_field_count,
            "equivalent_field_count": self.equivalent_field_count,
            "critical_field_equivalence_rate": self.critical_field_equivalence_rate,
            "all_critical_fields_equivalent_count": self.all_critical_fields_equivalent_count,
            "all_critical_fields_equivalent_rate": self.all_critical_fields_equivalent_rate,
            "benchmark_adjudication_count": self.benchmark_adjudication_count,
            "benchmark_adjudication_rate": self.benchmark_adjudication_rate,
            "cases": [case.as_dict() for case in self.cases],
        }
