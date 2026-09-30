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
