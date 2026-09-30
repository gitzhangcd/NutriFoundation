from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REQUIRED_STRICT_BLIND_METADATA = {
    "fresh_context_attestation": True,
    "prior_batch_exposure": False,
    "hidden_reference_available_to_worker": False,
    "independent_worker_session": True,
    "strict_blind_protocol_version": "E0.4.2-A0-v0.1",
    "blindness_class": "strict_blind_fresh_context",
}


@dataclass(frozen=True)
class StrictBlindResponseSetValidation:
    status: str
    bundle_sha256: str
    response_count: int
    unique_response_ids: int
    unique_task_ids: int
    completed_count: int
    defer_count: int
    task_id_set_match: bool
    task_hash_match_count: int
    source_hash_match_count: int
    contract_match_count: int
    schema_match_count: int
    metadata_match_count: int
    lineage_match_count: int
    violations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_strict_blind_response_set(
    *,
    bundle_path: str | Path,
    taskpack_manifest_path: str | Path,
    expected_bundle_sha256: str | None = None,
) -> StrictBlindResponseSetValidation:
    bundle_path = Path(bundle_path)
    raw = bundle_path.read_bytes()
    bundle_sha256 = _sha256_bytes(raw)
    responses = json.loads(raw.decode("utf-8"))
    manifest = _load_json(taskpack_manifest_path)

    violations: list[str] = []

    if not isinstance(responses, list):
        raise ValueError("Strict-blind response bundle must be a JSON array")

    manifest_tasks = {
        item["task_id"]: item
        for item in manifest.get("tasks", [])
        if isinstance(item, dict) and item.get("task_id")
    }
    expected_task_ids = set(manifest_tasks)
    observed_task_ids = {
        item.get("task_id")
        for item in responses
        if isinstance(item, dict) and item.get("task_id")
    }

    task_hash_match_count = 0
    source_hash_match_count = 0
    contract_match_count = 0
    schema_match_count = 0
    metadata_match_count = 0
    lineage_match_count = 0
    statuses: Counter[str] = Counter()
    response_ids: list[str] = []

    for index, item in enumerate(responses):
        if not isinstance(item, dict):
            violations.append(f"response[{index}] is not an object")
            continue

        task_id = item.get("task_id")
        response_id = item.get("response_id")
        if response_id:
            response_ids.append(response_id)
        statuses[str(item.get("status"))] += 1

        expected = manifest_tasks.get(task_id)
        if expected is None:
            violations.append(f"{task_id or index}: task_id not in frozen TaskPack")
            continue

        if item.get("task_sha256") == expected.get("task_sha256"):
            task_hash_match_count += 1
        else:
            violations.append(f"{task_id}: task_sha256 mismatch")

        if item.get("source_text_sha256") == expected.get("source_text_sha256"):
            source_hash_match_count += 1
        else:
            violations.append(f"{task_id}: source_text_sha256 mismatch")

        if item.get("contract_version") == expected.get("contract_version"):
            contract_match_count += 1
        else:
            violations.append(f"{task_id}: contract_version mismatch")

        if item.get("response_schema_version") == expected.get("response_schema_version"):
            schema_match_count += 1
        else:
            violations.append(f"{task_id}: response_schema_version mismatch")

        worker = item.get("worker") or {}
        metadata = worker.get("metadata") or {}
        if all(
            metadata.get(key) == value
            for key, value in REQUIRED_STRICT_BLIND_METADATA.items()
        ):
            metadata_match_count += 1
        else:
            violations.append(f"{task_id}: strict-blind metadata mismatch")

        lineage = ((item.get("provenance") or {}).get("lineage_refs") or [])
        if lineage == [task_id]:
            lineage_match_count += 1
        else:
            violations.append(f"{task_id}: provenance lineage mismatch")

    if expected_bundle_sha256 and bundle_sha256 != expected_bundle_sha256:
        violations.append(
            "bundle_sha256 mismatch: "
            f"expected={expected_bundle_sha256} observed={bundle_sha256}"
        )

    if len(response_ids) != len(set(response_ids)):
        violations.append("response_id values are not unique")

    task_id_set_match = observed_task_ids == expected_task_ids
    if not task_id_set_match:
        violations.append("observed task_id set does not equal frozen TaskPack task_id set")

    expected_count = len(expected_task_ids)
    if len(responses) != expected_count:
        violations.append(
            f"response_count mismatch: expected={expected_count} observed={len(responses)}"
        )

    status = "PASS" if not violations else "FAIL"

    return StrictBlindResponseSetValidation(
        status=status,
        bundle_sha256=bundle_sha256,
        response_count=len(responses),
        unique_response_ids=len(set(response_ids)),
        unique_task_ids=len(observed_task_ids),
        completed_count=statuses.get("completed", 0),
        defer_count=statuses.get("defer", 0),
        task_id_set_match=task_id_set_match,
        task_hash_match_count=task_hash_match_count,
        source_hash_match_count=source_hash_match_count,
        contract_match_count=contract_match_count,
        schema_match_count=schema_match_count,
        metadata_match_count=metadata_match_count,
        lineage_match_count=lineage_match_count,
        violations=tuple(violations),
    )
