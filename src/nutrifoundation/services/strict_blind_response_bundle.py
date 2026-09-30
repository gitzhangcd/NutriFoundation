from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from nutrifoundation.domain.semantic_worker import ResponseEnvelope
from nutrifoundation.services.strict_blind_taskpack import REQUIRED_WORKER_METADATA


@dataclass(frozen=True)
class ResponseFreezeReceipt:
    status: str
    bundle_sha256: str
    response_count: int
    completed_count: int
    defer_count: int
    failed_count: int
    unique_response_ids: int
    unique_task_ids: int
    task_binding_match_count: int
    source_hash_match_count: int
    contract_version_match_count: int
    response_schema_match_count: int
    strict_metadata_match_count: int
    protocol_version_match_count: int
    blindness_class_match_count: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def bundle_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_bundle(path: str | Path) -> list[ResponseEnvelope]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Strict-blind response bundle must be a JSON array")
    return [ResponseEnvelope.model_validate(item) for item in raw]


def validate_response_bundle(
    *,
    bundle_path: str | Path,
    taskpack_manifest_path: str | Path,
    expected_bundle_sha256: str | None = None,
) -> ResponseFreezeReceipt:
    responses = load_bundle(bundle_path)
    taskpack = json.loads(Path(taskpack_manifest_path).read_text(encoding="utf-8"))
    expected = {item["task_id"]: item for item in taskpack["tasks"]}

    actual_sha = bundle_sha256(bundle_path)
    if expected_bundle_sha256 is not None and actual_sha != expected_bundle_sha256:
        raise ValueError(
            f"Frozen response bundle SHA-256 mismatch: {actual_sha} != "
            f"{expected_bundle_sha256}"
        )

    response_ids = [item.response_id for item in responses]
    task_ids = [item.task_id for item in responses]
    if len(set(response_ids)) != len(response_ids):
        raise ValueError("Duplicate response_id in frozen bundle")
    if len(set(task_ids)) != len(task_ids):
        raise ValueError("Duplicate task_id in frozen bundle")
    if set(task_ids) != set(expected):
        missing = sorted(set(expected) - set(task_ids))
        extra = sorted(set(task_ids) - set(expected))
        raise ValueError(
            f"Task set mismatch. missing={missing} extra={extra}"
        )

    task_binding = 0
    source_hash = 0
    contract_version = 0
    response_schema = 0
    strict_metadata = 0
    protocol_version = 0
    blindness_class = 0

    for response in responses:
        ref = expected[response.task_id]
        task_binding += response.task_sha256 == ref["task_sha256"]
        source_hash += response.source_text_sha256 == ref["source_text_sha256"]
        contract_version += response.contract_version == ref["contract_version"]
        response_schema += (
            response.response_schema_version == ref["response_schema_version"]
        )

        metadata = response.worker.metadata
        strict_metadata += all(
            metadata.get(key) == value
            for key, value in REQUIRED_WORKER_METADATA.items()
        )
        protocol_version += (
            metadata.get("strict_blind_protocol_version")
            == taskpack["strict_blind_protocol_version"]
        )
        blindness_class += (
            metadata.get("blindness_class")
            == taskpack["blindness_class"]
        )

    n = len(responses)
    counts = Counter(item.status for item in responses)
    all_bound = all(
        value == n
        for value in (
            task_binding,
            source_hash,
            contract_version,
            response_schema,
            strict_metadata,
            protocol_version,
            blindness_class,
        )
    )
    status = "PASS" if n == taskpack["task_count"] and all_bound else "FAIL"

    return ResponseFreezeReceipt(
        status=status,
        bundle_sha256=actual_sha,
        response_count=n,
        completed_count=counts.get("completed", 0),
        defer_count=counts.get("defer", 0),
        failed_count=counts.get("failed", 0),
        unique_response_ids=len(set(response_ids)),
        unique_task_ids=len(set(task_ids)),
        task_binding_match_count=task_binding,
        source_hash_match_count=source_hash,
        contract_version_match_count=contract_version,
        response_schema_match_count=response_schema,
        strict_metadata_match_count=strict_metadata,
        protocol_version_match_count=protocol_version,
        blindness_class_match_count=blindness_class,
    )


def materialize_bundle(
    *,
    bundle_path: str | Path,
    taskpack_manifest_path: str | Path,
    out_dir: str | Path,
    expected_bundle_sha256: str | None = None,
) -> ResponseFreezeReceipt:
    receipt = validate_response_bundle(
        bundle_path=bundle_path,
        taskpack_manifest_path=taskpack_manifest_path,
        expected_bundle_sha256=expected_bundle_sha256,
    )
    if receipt.status != "PASS":
        raise ValueError(f"Frozen response bundle validation failed: {receipt}")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if list(out.glob("*.response.json")):
        raise ValueError("Response materialization directory must be empty")

    for response in load_bundle(bundle_path):
        path = out / f"{response.task_id}.response.json"
        path.write_text(response.model_dump_json(indent=2), encoding="utf-8")

    return receipt
