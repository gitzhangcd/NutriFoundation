from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from .models import EvidenceUnit, FrozenModel, Provenance


class EvidenceExtractionCandidate(FrozenModel):
    candidate_id: str
    evidence: EvidenceUnit
    extractor_id: str
    extraction_method: str
    extraction_confidence: float = Field(ge=0, le=1)
    source_text_sha256: str
    created_at: datetime
    provenance: Provenance

    @model_validator(mode="after")
    def candidate_must_not_be_frozen(self) -> "EvidenceExtractionCandidate":
        if self.evidence.verification_status != "candidate":
            raise ValueError("Extraction candidate must have verification_status=candidate")
        if self.evidence.status not in {None, "candidate"}:
            raise ValueError("Extraction candidate cannot already be frozen")
        return self


class VerificationChecks(FrozenModel):
    source_linkage: bool
    required_fields: bool
    source_anchor_present: bool
    numeric_support: bool
    applicability_boundary_present: bool
    observational_causality_guard: bool
    guideline_authority_guard: bool


class EvidenceVerificationRecord(FrozenModel):
    verification_id: str
    candidate_id: str
    evidence_id: str
    source_id: str
    verifier_id: str
    extractor_id: str
    independent_from_extractor: bool
    source_text_sha256: str
    checks: VerificationChecks
    status: Literal["verified", "rejected", "escalate"]
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    verified_at: datetime
    provenance: Provenance

    @model_validator(mode="after")
    def verified_record_must_be_independent_and_clean(self) -> "EvidenceVerificationRecord":
        if self.status == "verified":
            if self.verifier_id == self.extractor_id:
                raise ValueError("Verified EvidenceUnit requires a different verifier identity")
            if not self.independent_from_extractor:
                raise ValueError("Verified EvidenceUnit requires independent verification")
            if self.errors:
                raise ValueError("Verified EvidenceUnit cannot contain verification errors")
            if not all(self.checks.model_dump().values()):
                raise ValueError("Verified EvidenceUnit requires all F0 checks to pass")
        return self


class F0FreezeRecord(FrozenModel):
    freeze_id: str
    evidence_id: str
    source_id: str
    candidate_ref: str
    verification_ref: str
    freeze_level: Literal["F0"] = "F0"
    source_text_sha256: str
    frozen_at: datetime
    provenance: Provenance
