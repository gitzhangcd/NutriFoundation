from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from nutrifoundation.domain.models import FrozenModel
from nutrifoundation.evaluation.v2.scoring import FieldComparisonV2
from nutrifoundation.evaluation.v2.schema import EvaluationResultV2


class InputArtifactV2(FrozenModel):
    path: str
    sha256: str


class StrictBlindEvidenceV2(FrozenModel):
    fresh_context: bool
    prior_batch_exposure: bool
    hidden_reference_available_to_worker: bool
    independent_worker_session: bool
    blindness_class: str
    qualifies: bool


class ResponseSetEvidenceV2(FrozenModel):
    path: str
    sha256: str
    response_count: int = Field(ge=0)
    completed_count: int = Field(ge=0)
    deferred_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    attestation: StrictBlindEvidenceV2


class DimensionAggregateV2(FrozenModel):
    dimension: str
    eligible_case_count: int = Field(ge=0)
    scored_case_count: int = Field(ge=0)
    mean_score: float | None = Field(default=None, ge=0.0, le=1.0)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    max_score: float | None = Field(default=None, ge=0.0, le=1.0)


class FieldAggregateV2(FrozenModel):
    dimension: str
    field: str
    eligible_case_count: int = Field(ge=0)
    scored_case_count: int = Field(ge=0)
    mean_score: float | None = Field(default=None, ge=0.0, le=1.0)
    relation_counts: dict[str, int] = Field(default_factory=dict)


class BatchCaseReportV2(FrozenModel):
    task_id: str
    response_id: str
    evidence_id: str
    source_id: str
    response_status: str
    score_vector: dict[str, float | None]
    evaluation: EvaluationResultV2
    field_comparisons: tuple[FieldComparisonV2, ...]


class BatchEvaluationReportV2(FrozenModel):
    artifact: str = "Evaluator V2 Batch Re-Scoring Report"
    report_version: str
    evaluator_version: str
    mapping_version: str
    batch_id: str
    evaluated_at: datetime
    reference_authority: str
    publication_grade: bool
    response_set: ResponseSetEvidenceV2
    source_fixture: InputArtifactV2
    hidden_reference: InputArtifactV2
    task_manifest: InputArtifactV2
    aggregation_policy: dict[str, str]
    dimension_summary: tuple[DimensionAggregateV2, ...]
    field_summary: tuple[FieldAggregateV2, ...]
    cases: tuple[BatchCaseReportV2, ...]

    def compact_summary(self) -> dict[str, Any]:
        return {
            "artifact": self.artifact,
            "report_version": self.report_version,
            "evaluator_version": self.evaluator_version,
            "mapping_version": self.mapping_version,
            "batch_id": self.batch_id,
            "evaluated_at": self.evaluated_at.isoformat(),
            "reference_authority": self.reference_authority,
            "publication_grade": self.publication_grade,
            "response_set": self.response_set.model_dump(mode="json"),
            "dimension_summary": [
                item.model_dump(mode="json")
                for item in self.dimension_summary
            ],
        }
