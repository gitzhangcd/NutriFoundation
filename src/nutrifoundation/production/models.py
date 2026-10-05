from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import Field, model_validator
from nutrifoundation.domain.models import FrozenModel


CONTRACT = "D0-production-v0.1"
FieldState = Literal["PRESENT", "NOT_REPORTED", "NOT_APPLICABLE", "NOT_ACQUIRED", "EXTRACTION_FAILED", "UNRESOLVED"]
CheckState = Literal["PASS", "FAIL", "UNRESOLVED", "NOT_APPLICABLE"]


def now() -> datetime:
    return datetime.now(timezone.utc)


def digest(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    def encode(item):
        if hasattr(item,"model_dump"):
            return item.model_dump(mode="json")
        if isinstance(item,datetime):
            return item.isoformat()
        raise TypeError(f"Not a canonical JSON value: {type(item).__name__}")
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),default=encode).encode()).hexdigest()


class RawSnapshot(FrozenModel):
    snapshot_id: str
    source_id: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_version: str
    format: Literal["JATS_XML", "TEXT", "PDF", "HTML", "XPT", "OTHER"]
    content_scope: Literal["metadata", "abstract", "fulltext", "supplement", "observation", "grounding", "experiment"]
    lane: Literal["scientific", "observation", "grounding", "experiment"] = "scientific"
    license: str
    byte_count: int = Field(ge=0)
    blob_path: str


class Anchor(FrozenModel):
    anchor_id: str
    snapshot_id: str
    source_sha256: str
    parser_version: str
    locator: str
    exact_text: str
    text_sha256: str
    context: dict[str, Any] = Field(default_factory=dict)


class ParsedDocument(FrozenModel):
    parsed_id: str
    snapshot_id: str
    parser_version: str
    anchors: tuple[Anchor, ...]
    warnings: tuple[str, ...] = ()


class FieldAssertion(FrozenModel):
    state: FieldState
    source_value: str | None = None
    normalized_value: str | None = None
    anchor_refs: tuple[str, ...] = ()
    reason: str | None = None

    @model_validator(mode="after")
    def require_provenance(self):
        if self.state == "PRESENT" and (self.source_value is None or not self.anchor_refs):
            raise ValueError("PRESENT requires a source value and anchors")
        if self.state != "PRESENT" and not self.reason:
            raise ValueError("Missing/unknown fields require a reason")
        return self


class ResultDraft(FrozenModel):
    result_id: str
    object_type: Literal["EvidenceUnit", "Recommendation", "ScientificClaim"]
    fields: dict[str, FieldAssertion]
    issues: tuple[str, ...] = ()


class ExtractionTask(FrozenModel):
    contract_version: Literal["D0-production-v0.1"] = CONTRACT
    task_id: str
    snapshot_id: str
    snapshot_sha256: str
    parsed_id: str
    parsed_sha256: str
    authority_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    extractor_id: str
    model_version: str
    prompt_version: str
    coverage_request: str
    budget_tokens: int = Field(gt=0)


class PrefillDraft(FrozenModel):
    contract_version: Literal["D0-production-v0.1"] = CONTRACT
    draft_id: str
    task: ExtractionTask
    task_sha256: str
    results: tuple[ResultDraft, ...]
    coverage_completed: str
    coverage_omissions: tuple[str, ...]
    status: Literal["STAGING"] = "STAGING"

    @model_validator(mode="after")
    def bind_task(self):
        if self.task_sha256 != digest(self.task):
            raise ValueError("Extraction task hash mismatch")
        ids = [r.result_id for r in self.results]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate result ID")
        return self


class Check(FrozenModel):
    result_id: str
    field: str
    rule: str
    status: CheckState
    reason: str


class VerificationReport(FrozenModel):
    report_id: str
    draft_sha256: str
    parsed_sha256: str
    scope: Literal["mechanical_and_independent_readout_comparison"] = "mechanical_and_independent_readout_comparison"
    checks: tuple[Check, ...]
    independent_readout_id: str | None = None
    independent_readout_sha256: str | None = None
    independent_evidence_status: Literal["NOT_PROVEN", "ATTESTED_EXECUTION_ONLY"] = "NOT_PROVEN"
    scientific_truth_certified: Literal[False] = False


class IndependentReadout(FrozenModel):
    readout_id: str
    task_sha256: str
    snapshot_id: str
    parsed_sha256: str
    worker_id: str
    session_id: str
    input_scope: Literal["source_only"]
    candidate_exposed: bool
    completed_at: datetime
    locked_at: datetime
    results: tuple[ResultDraft, ...]

    @model_validator(mode="after")
    def locking(self):
        if self.completed_at.tzinfo is None or self.locked_at.tzinfo is None:
            raise ValueError("UTC-aware readout times required")
        if self.locked_at < self.completed_at:
            raise ValueError("Readout must complete before lock")
        ids = [r.result_id for r in self.results]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate readout result ID")
        return self


class ReviewDecision(FrozenModel):
    decision_id: str
    review_task_id: str
    draft_sha256: str
    mode: Literal["assisted", "source_only"]
    reviewer_id: str
    submitted_at: datetime
    # Field paths are result_id/field. Original draft is never overwritten.
    patches: dict[str, FieldAssertion] = Field(default_factory=dict)
    reasons: dict[str, str] = Field(default_factory=dict)
    independent_results: tuple[ResultDraft, ...] = ()
    decision: Literal["CONFIRM", "REVISE", "UNRESOLVED", "DEFER"]

    @model_validator(mode="after")
    def require_patch_reason(self):
        if self.submitted_at.tzinfo is None:
            raise ValueError("UTC-aware submission time required")
        if any(not self.reasons.get(path) for path in self.patches):
            raise ValueError("Every patch requires a reason")
        if self.decision == "REVISE" and not self.patches:
            if self.mode != "source_only":
                raise ValueError("REVISE requires patches")
        if self.mode == "source_only":
            if self.patches:
                raise ValueError("Source-only readout cannot patch unseen candidate fields")
            if self.decision in {"CONFIRM","REVISE"} and not self.independent_results:
                raise ValueError("Source-only completion requires independently read results")
        elif self.independent_results:
            raise ValueError("Assisted review cannot claim source-only results")
        return self
