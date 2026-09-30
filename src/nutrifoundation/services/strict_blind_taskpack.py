from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from nutrifoundation.domain.semantic_worker import TaskBundle, canonical_sha256
from nutrifoundation.services.blind_batch import (
    fixed_e04_time,
    load_source_fixture,
    prepare_blind_tasks,
)


STRICT_BLIND_PROTOCOL_VERSION = "E0.4.2-A0-v0.1"
TASK_CONTRACT_VERSION = "E0.4-v0.1"
DEFAULT_RUN_ID = "RUN-BLIND-B001-E04-v01"

FORBIDDEN_ARTIFACT_TOKENS = (
    "Batch001_EvidenceUnit_Frozen",
    "Batch001/Responses",
    "Batch001/responses",
    "Blind_Replay_Report",
    "Canonical_Equivalence_Report",
    "Semantic_Equivalence_Development_Calibration",
    "Verifier_Development_Calibration",
    "ScientificClaim_Gold",
)

FORBIDDEN_PAYLOAD_KEYS = {
    "gold",
    "hidden_gold",
    "hidden_reference",
    "expected_equivalent",
    "benchmark_score",
    "human_adjudication",
}

REQUIRED_WORKER_METADATA = {
    "fresh_context_attestation": True,
    "prior_batch_exposure": False,
    "hidden_reference_available_to_worker": False,
    "independent_worker_session": True,
    "strict_blind_protocol_version": STRICT_BLIND_PROTOCOL_VERSION,
    "blindness_class": "strict_blind_fresh_context",
}


@dataclass(frozen=True)
class BlindWallAudit:
    status: str
    task_count: int
    unique_task_ids: int
    unique_source_ids: int
    unique_evidence_ids: int
    task_hash_match_count: int
    source_hash_match_count: int
    forbidden_token_hits: tuple[str, ...]
    forbidden_key_hits: tuple[str, ...]
    reference_answer_visibility_violations: tuple[str, ...]
    prior_response_artifacts_included: bool
    hidden_reference_artifacts_included: bool
    scoring_artifacts_included: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _walk_keys(value: Any, *, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_PAYLOAD_KEYS:
                hits.append(child_path)
            hits.extend(_walk_keys(child, path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_walk_keys(child, path=f"{path}[{index}]"))
    return hits


def reconstruct_tasks(
    source_fixture_path: str | Path,
    *,
    batch_id: str = "B001",
) -> list[TaskBundle]:
    records = load_source_fixture(source_fixture_path)
    return prepare_blind_tasks(
        records,
        batch_id=batch_id,
        run_id=DEFAULT_RUN_ID,
        created_at=fixed_e04_time(),
    )


def task_manifest_entries(tasks: list[TaskBundle]) -> list[dict[str, Any]]:
    return [
        {
            "task_id": task.task_id,
            "source_id": task.source_id,
            "evidence_id": task.evidence_id,
            "task_sha256": task.task_sha256,
            "source_text_sha256": task.source_text_sha256,
            "contract_version": task.contract_version,
            "response_schema_version": task.response_schema_version,
        }
        for task in tasks
    ]


def taskpack_sha256(entries: list[dict[str, Any]]) -> str:
    return canonical_sha256(
        {
            "protocol_version": STRICT_BLIND_PROTOCOL_VERSION,
            "task_contract_version": TASK_CONTRACT_VERSION,
            "tasks": entries,
        }
    )


def build_taskpack_manifest(
    source_fixture_path: str | Path,
    *,
    batch_id: str = "B001",
) -> dict[str, Any]:
    tasks = reconstruct_tasks(source_fixture_path, batch_id=batch_id)
    entries = task_manifest_entries(tasks)
    return {
        "artifact": "StrictBlindTaskPackManifest",
        "stage": "E0.4.2-A0",
        "version": "v1.0",
        "status": "FROZEN_SOURCE_ONLY",
        "blindness_class": "strict_blind_fresh_context",
        "batch_id": batch_id,
        "task_count": len(entries),
        "task_contract_version": TASK_CONTRACT_VERSION,
        "strict_blind_protocol_version": STRICT_BLIND_PROTOCOL_VERSION,
        "source_fixture": str(source_fixture_path),
        "tasks": entries,
        "taskpack_sha256": taskpack_sha256(entries),
        "required_worker_metadata": dict(REQUIRED_WORKER_METADATA),
        "hidden_reference_in_task_factory": False,
        "scoring_permitted_before_response_freeze": False,
    }


def audit_taskpack(
    *,
    source_fixture_path: str | Path,
    frozen_manifest: dict[str, Any],
    batch_id: str = "B001",
) -> BlindWallAudit:
    tasks = reconstruct_tasks(source_fixture_path, batch_id=batch_id)
    expected_entries = task_manifest_entries(tasks)
    frozen_entries = frozen_manifest.get("tasks", [])

    task_ids = [item["task_id"] for item in expected_entries]
    source_ids = [item["source_id"] for item in expected_entries]
    evidence_ids = [item["evidence_id"] for item in expected_entries]

    frozen_by_id = {
        item.get("task_id"): item
        for item in frozen_entries
        if isinstance(item, dict)
    }
    task_hash_match_count = sum(
        frozen_by_id.get(item["task_id"], {}).get("task_sha256")
        == item["task_sha256"]
        for item in expected_entries
    )
    source_hash_match_count = sum(
        frozen_by_id.get(item["task_id"], {}).get("source_text_sha256")
        == item["source_text_sha256"]
        for item in expected_entries
    )

    serialized = json.dumps(
        frozen_manifest,
        ensure_ascii=False,
        sort_keys=True,
    )
    forbidden_token_hits = tuple(
        token
        for token in FORBIDDEN_ARTIFACT_TOKENS
        if token.lower() in serialized.lower()
    )
    forbidden_key_hits = tuple(sorted(_walk_keys(frozen_manifest)))

    visibility_violations: list[str] = []
    for task in tasks:
        visible = task.provenance.metadata.get("reference_answer_visible")
        if visible is not False:
            visibility_violations.append(task.task_id)

    prior_response = any(
        token.lower() in serialized.lower()
        for token in ("prior_response", "response_artifact", "/responses/")
    )
    hidden_reference = any(
        token.lower() in serialized.lower()
        for token in ("hidden_reference", "evidenceunit_frozen")
    )
    scoring_artifacts = any(
        token.lower() in serialized.lower()
        for token in ("scoring_report", "blind_replay_report", "canonical_equivalence_report")
    )

    expected_pack_hash = taskpack_sha256(expected_entries)
    pack_hash_matches = (
        frozen_manifest.get("taskpack_sha256") == expected_pack_hash
    )
    counts_match = frozen_manifest.get("task_count") == len(expected_entries)
    no_contamination = not (
        forbidden_token_hits
        or forbidden_key_hits
        or visibility_violations
        or prior_response
        or hidden_reference
        or scoring_artifacts
    )
    hashes_match = (
        task_hash_match_count == len(expected_entries)
        and source_hash_match_count == len(expected_entries)
        and pack_hash_matches
    )

    status = (
        "PASS"
        if counts_match and hashes_match and no_contamination
        else "FAIL"
    )
    return BlindWallAudit(
        status=status,
        task_count=len(expected_entries),
        unique_task_ids=len(set(task_ids)),
        unique_source_ids=len(set(source_ids)),
        unique_evidence_ids=len(set(evidence_ids)),
        task_hash_match_count=task_hash_match_count,
        source_hash_match_count=source_hash_match_count,
        forbidden_token_hits=forbidden_token_hits,
        forbidden_key_hits=forbidden_key_hits,
        reference_answer_visibility_violations=tuple(visibility_violations),
        prior_response_artifacts_included=prior_response,
        hidden_reference_artifacts_included=hidden_reference,
        scoring_artifacts_included=scoring_artifacts,
    )


def write_manifest(manifest: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_manifest(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
