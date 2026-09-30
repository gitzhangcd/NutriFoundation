from __future__ import annotations

from typing import Protocol

from nutrifoundation.domain.semantic_worker import ResponseEnvelope, TaskBundle


class SemanticWorkerAdapter(Protocol):
    """Portable synchronous worker contract for future provider adapters."""

    adapter_type: str

    def execute(self, task: TaskBundle) -> ResponseEnvelope: ...


def assert_response_binding(
    task: TaskBundle,
    response: ResponseEnvelope,
) -> None:
    mismatches = []
    if response.task_id != task.task_id:
        mismatches.append("task_id")
    if response.task_sha256 != task.task_sha256:
        mismatches.append("task_sha256")
    if response.contract_version != task.contract_version:
        mismatches.append("contract_version")
    if response.response_schema_version != task.response_schema_version:
        mismatches.append("response_schema_version")
    if response.source_text_sha256 != task.source_text_sha256:
        mismatches.append("source_text_sha256")
    if mismatches:
        raise ValueError(
            "ResponseEnvelope does not bind to TaskBundle: "
            + ", ".join(mismatches)
        )


def run_adapter_conformance(
    adapter: SemanticWorkerAdapter,
    task: TaskBundle,
) -> ResponseEnvelope:
    """Execute one portable adapter and enforce the provider-neutral contract."""
    response = adapter.execute(task)
    if response.worker.adapter_type != adapter.adapter_type:
        raise ValueError(
            "Adapter type mismatch between adapter and ResponseEnvelope worker descriptor"
        )
    assert_response_binding(task, response)
    return response
