from __future__ import annotations

from datetime import datetime

from pydantic import Field, model_validator

from nutrifoundation.domain.models import FrozenModel


class ScientificCoreResult(FrozenModel):
    """Five-field scientific semantic recovery scores."""

    population: float = Field(ge=0.0, le=1.0)
    intervention_exposure: float = Field(ge=0.0, le=1.0)
    comparator: float = Field(ge=0.0, le=1.0)
    outcome: float = Field(ge=0.0, le=1.0)
    effect: float = Field(ge=0.0, le=1.0)

    @property
    def score(self) -> float:
        return (
            self.population
            + self.intervention_exposure
            + self.comparator
            + self.outcome
            + self.effect
        ) / 5.0


class OntologyAlignmentResult(FrozenModel):
    """Separates study design from claim meaning and evidence role."""

    study_design: float = Field(ge=0.0, le=1.0)
    claim_type: float = Field(ge=0.0, le=1.0)
    evidence_role: float = Field(ge=0.0, le=1.0)

    @property
    def score(self) -> float:
        return (self.study_design + self.claim_type + self.evidence_role) / 3.0


class NumericFidelityResult(FrozenModel):
    """Tracks normalized numeric facts independently from surface form."""

    normalized_numeric_fields: int = Field(ge=0)
    matched_numeric_fields: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_counts(self) -> "NumericFidelityResult":
        if self.matched_numeric_fields > self.normalized_numeric_fields:
            raise ValueError(
                "matched_numeric_fields cannot exceed normalized_numeric_fields"
            )
        return self

    @property
    def score(self) -> float:
        if self.normalized_numeric_fields == 0:
            return 1.0
        return self.matched_numeric_fields / self.normalized_numeric_fields


class ProvenanceResult(FrozenModel):
    """Scores only provenance information that was observable to the worker."""

    visible_anchor_score: float | None = Field(default=None, ge=0.0, le=1.0)
    external_identifier_score: float | None = Field(default=None, ge=0.0, le=1.0)

    @property
    def score(self) -> float | None:
        applicable = tuple(
            value
            for value in (
                self.visible_anchor_score,
                self.external_identifier_score,
            )
            if value is not None
        )
        if not applicable:
            return None
        return sum(applicable) / len(applicable)


class AbstentionResult(FrozenModel):
    """Represents safe defer behavior only when abstention is applicable."""

    applicable: bool
    correct_abstention: bool | None = None

    @model_validator(mode="after")
    def validate_applicability(self) -> "AbstentionResult":
        if self.applicable and self.correct_abstention is None:
            raise ValueError(
                "correct_abstention is required when abstention is applicable"
            )
        if not self.applicable and self.correct_abstention is not None:
            raise ValueError(
                "correct_abstention must be null when abstention is not applicable"
            )
        return self

    @property
    def score(self) -> float | None:
        if not self.applicable:
            return None
        return 1.0 if self.correct_abstention else 0.0


class EvaluationMetadata(FrozenModel):
    evaluator_version: str
    created_at: datetime
    worker_visible_information: tuple[str, ...] = ()
    reference_visible_information: tuple[str, ...] = ()


class EvaluationResultV2(FrozenModel):
    """Versioned sidecar evaluation result for frozen ResponseEnvelope artifacts."""

    task_id: str
    response_id: str
    evidence_id: str
    source_id: str
    scientific_core: ScientificCoreResult
    ontology: OntologyAlignmentResult
    numeric: NumericFidelityResult
    provenance: ProvenanceResult
    abstention: AbstentionResult
    metadata: EvaluationMetadata
