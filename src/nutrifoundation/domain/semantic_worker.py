from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, model_validator

from .models import FrozenModel, Provenance


def canonical_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class SemanticTaskState(StrEnum):
    PENDING = "pending"
    EXPORTED = "exported"
    RESPONDED = "responded"
    INGESTED = "ingested"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    F0_FROZEN = "f0_frozen"


class WorkerDescriptor(FrozenModel):
    worker_id: str
    adapter_type: str
    provider: str | None = None
    model: str | None = None
    model_version: str | None = None
    prompt_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskBundle(FrozenModel):
    task_id: str
    task_type: Literal["extract_evidence_unit"]
    contract_version: str
    run_id: str
    source_id: str
    evidence_id: str
    source_snapshot: dict[str, Any]
    source_text: str
    source_text_sha256: str
    requested_fields: tuple[str, ...]
    rules: tuple[str, ...]
    response_schema_version: str
    created_at: datetime
    task_sha256: str
    provenance: Provenance

    @staticmethod
    def digest_payload(data: dict[str, Any]) -> str:
        payload = dict(data)
        payload.pop("task_sha256", None)
        return canonical_sha256(payload)

    @classmethod
    def build(cls, **data: Any) -> "TaskBundle":
        payload = dict(data)
        payload["task_sha256"] = cls.digest_payload(payload)
        return cls(**payload)

    @model_validator(mode="after")
    def validate_hashes(self) -> "TaskBundle":
        source_hash = hashlib.sha256(self.source_text.encode("utf-8")).hexdigest()
        if source_hash != self.source_text_sha256:
            raise ValueError("TaskBundle source_text_sha256 mismatch")
        if self.task_sha256 != self.digest_payload(self.model_dump(mode="json")):
            raise ValueError("TaskBundle task_sha256 mismatch")
        return self


class ResponseEnvelope(FrozenModel):
    response_id: str
    task_id: str
    task_sha256: str
    contract_version: str
    response_schema_version: str
    source_text_sha256: str
    worker: WorkerDescriptor
    status: Literal["completed", "defer", "failed"]
    output: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0, le=1)
    uncertainties: tuple[str, ...] = ()
    error: str | None = None
    created_at: datetime
    provenance: Provenance

    @model_validator(mode="after")
    def validate_status_payload(self) -> "ResponseEnvelope":
        if self.status == "completed" and not self.output:
            raise ValueError("Completed ResponseEnvelope requires output")
        if self.status == "failed" and not self.error:
            raise ValueError("Failed ResponseEnvelope requires error")
        return self


class SemanticSubmissionReceipt(FrozenModel):
    task_id: str
    task_sha256: str
    adapter_type: str
    location: str
    submitted_at: datetime


TASK_STATE_TRANSITIONS: dict[SemanticTaskState, set[SemanticTaskState]] = {
    SemanticTaskState.PENDING: {
        SemanticTaskState.EXPORTED,
        SemanticTaskState.RESPONDED,
        SemanticTaskState.REJECTED,
    },
    SemanticTaskState.EXPORTED: {
        SemanticTaskState.RESPONDED,
        SemanticTaskState.REJECTED,
    },
    SemanticTaskState.RESPONDED: {
        SemanticTaskState.INGESTED,
        SemanticTaskState.DEFERRED,
        SemanticTaskState.REJECTED,
    },
    SemanticTaskState.INGESTED: {
        SemanticTaskState.F0_FROZEN,
        SemanticTaskState.REJECTED,
    },
    SemanticTaskState.DEFERRED: set(),
    SemanticTaskState.REJECTED: set(),
    SemanticTaskState.F0_FROZEN: set(),
}


def assert_task_state_transition(
    current: SemanticTaskState,
    target: SemanticTaskState,
) -> None:
    if target not in TASK_STATE_TRANSITIONS[current]:
        raise ValueError(f"Illegal semantic task transition: {current} -> {target}")
