from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .enums import ClaimType, HumanDecision, IntegrityStatus, ReliabilityState, SourceType


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Provenance(FrozenModel):
    source: str | None = None
    provider: str | None = None
    retrieved_at: datetime | None = None
    version: str | None = None
    lineage_refs: tuple[str, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceIdentifiers(FrozenModel):
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None


class SourceArtifact(FrozenModel):
    source_id: str
    source_type: SourceType
    title: str
    authors: tuple[str, ...] = ()
    publication_date: date | None = None
    identifiers: SourceIdentifiers = Field(default_factory=SourceIdentifiers)
    evidence_domain: str | None = None
    provenance: Provenance
    version: str = "v0.1"


class EvidenceUnit(FrozenModel):
    evidence_id: str
    source_id: str
    kind: str | None = None
    population: dict[str, Any] | str
    intervention: dict[str, Any] | str | None = None
    exposure: dict[str, Any] | str | None = None
    intervention_or_exposure: dict[str, Any] | str | None = None
    comparator: dict[str, Any] | str | None = None
    outcome: dict[str, Any] | str
    follow_up: str | None = None
    estimand: str | None = None
    effect_measure: str | None = None
    effect_value: str | None = None
    effect: str | None = None
    recommendation: str | None = None
    certainty: str | None = None
    source_span: str | None = None
    anchor: str | None = None
    applicability_boundary: dict[str, Any] | str | None = None
    verification_status: str
    status: str | None = None
    verification: tuple[str, ...] = ()
    provenance: Provenance

    @model_validator(mode="after")
    def validate_scientific_payload(self) -> "EvidenceUnit":
        has_exposure = any(
            value is not None
            for value in (
                self.intervention,
                self.exposure,
                self.intervention_or_exposure,
            )
        )
        is_source_statement = self.recommendation is not None
        if not has_exposure and not is_source_statement:
            raise ValueError(
                "EvidenceUnit requires intervention/exposure or a source-stated recommendation"
            )
        if self.effect is None and self.effect_value is None and self.recommendation is None:
            raise ValueError("EvidenceUnit requires effect/effect_value or recommendation")
        if not (self.source_span or self.anchor):
            raise ValueError("EvidenceUnit requires source_span or anchor")
        return self


class ScientificClaim(FrozenModel):
    claim_id: str
    statement: str
    claim_type: ClaimType
    evidence_refs: tuple[str, ...]
    population_scope: dict[str, Any]
    outcome_scope: dict[str, Any]
    applicability_boundary: dict[str, Any] = Field(default_factory=dict)
    limitations: tuple[str, ...] = ()
    provenance: Provenance

    @model_validator(mode="after")
    def causal_claim_requires_evidence(self) -> "ScientificClaim":
        if self.claim_type == ClaimType.CAUSAL and not self.evidence_refs:
            raise ValueError("Causal ScientificClaim cannot exist without EvidenceUnit references")
        return self


class CitationContext(FrozenModel):
    citing_source_id: str
    claim_alignment: Literal["exact_claim", "partial_claim", "background_only", "unclear"]
    reception_role: Literal[
        "supports",
        "contrasts",
        "contradicts",
        "independent_replication",
        "failed_replication",
        "methodological_use",
        "background_mention",
        "extends_generalizes",
        "critique",
    ]
    evidence_type: str | None = None
    independence_group_id: str | None = None
    citation_span: str | None = None
    extraction_confidence: float = Field(ge=0, le=1)
    human_review_required: bool = False


class CitationReceptionRecord(FrozenModel):
    reception_id: str
    target_type: Literal["SourceArtifact", "ScientificClaim"]
    target_id: str
    retrieval_date: date
    providers: tuple[str, ...]
    citation_contexts: tuple[CitationContext, ...] = ()
    independent_citation_families: int | None = Field(default=None, ge=0)
    derivative_citation_families: int | None = Field(default=None, ge=0)
    provenance: Provenance

    @property
    def claim_aligned_support_count(self) -> int:
        return sum(
            1
            for c in self.citation_contexts
            if c.claim_alignment in {"exact_claim", "partial_claim"}
            and c.reception_role in {"supports", "independent_replication", "extends_generalizes"}
        )


class ScientificInfluenceSignal(FrozenModel):
    influence_id: str
    target_type: Literal["SourceArtifact", "ScientificClaim"]
    target_id: str
    snapshot_date: date
    raw_citation_count: int | None = Field(default=None, ge=0)
    field_year_normalized_percentile: float | None = Field(default=None, ge=0, le=100)
    journal_metric_name: str | None = None
    journal_metric_value: float | None = Field(default=None, ge=0)
    provenance: Provenance


class ReliabilityVector(FrozenModel):
    intrinsic_evidence_validity: Literal["low", "moderate", "high", "mixed", "insufficient"]
    evidence_independence: Literal["low", "moderate", "high", "mixed", "unresolved"]
    direct_replication: Literal["none", "limited", "convergent", "mixed", "failed", "not_applicable"]
    citation_reception: Literal["insufficient", "supportive", "mixed", "contested", "adverse", "not_applicable"]
    integrity_status: IntegrityStatus
    temporal_maturity: Literal["early", "developing", "mature", "legacy"]
    applicability_stability: Literal["narrow", "moderate", "broad", "heterogeneous", "unresolved"]


class ClaimReliabilitySignal(FrozenModel):
    reliability_id: str
    claim_id: str
    evidence_refs: tuple[str, ...]
    citation_reception_refs: tuple[str, ...] = ()
    scientific_influence_refs: tuple[str, ...] = ()
    reliability_vector: ReliabilityVector
    reliability_state: ReliabilityState
    eligible_for_expert_gold_review: bool
    blockers: tuple[str, ...] = ()
    escalation_reasons: tuple[str, ...] = ()
    rationale: tuple[str, ...] = ()
    provenance: Provenance

    @model_validator(mode="after")
    def influence_cannot_be_only_basis_for_upgrade(self) -> "ClaimReliabilitySignal":
        if self.reliability_state in {ReliabilityState.CONVERGENT, ReliabilityState.ROBUST}:
            if not self.evidence_refs:
                raise ValueError("Reliability cannot be upgraded from influence alone")
        if self.reliability_vector.integrity_status == IntegrityStatus.RETRACTED:
            if self.reliability_state not in {ReliabilityState.DEGRADED, ReliabilityState.INVALIDATED}:
                raise ValueError("Retracted evidence cannot have convergent/robust reliability state")
        return self


class HumanAdjudicationRecord(FrozenModel):
    adjudication_id: str
    claim_id: str
    reviewer_id: str
    reviewer_role: str
    independent_from_agent_extraction: bool
    conflict_of_interest: str | None = None
    decision: HumanDecision
    approved_wording: str | None = None
    adjudicated_at: datetime
    provenance: Provenance

    @model_validator(mode="after")
    def validate_approval(self) -> "HumanAdjudicationRecord":
        if self.decision in {
            HumanDecision.APPROVE_GOLD_AS_WRITTEN,
            HumanDecision.APPROVE_GOLD_WITH_REVISION,
        }:
            if not self.independent_from_agent_extraction:
                raise ValueError("Gold approval requires independent human/expert adjudication")
            if not self.approved_wording:
                raise ValueError("Approved Gold claim requires explicit approved wording")
        return self


class GoldScientificClaim(FrozenModel):
    gold_claim_id: str
    claim_id: str
    approved_wording: str
    evidence_refs: tuple[str, ...]
    f1_record_refs: tuple[str, ...]
    citation_reception_refs: tuple[str, ...]
    scientific_influence_refs: tuple[str, ...]
    reliability_ref: str
    adjudication_ref: str
    frozen_at: datetime
    version: str
    provenance: Provenance
