from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nutrifoundation.domain.models import Provenance
from nutrifoundation.domain.semantic_worker import TaskBundle


BLIND_RULES = (
    "Extract only what is supported by the supplied source text.",
    "Do not use external knowledge or prior batch answers.",
    "Association must not be upgraded to causation.",
    "Guideline or consensus statements must remain source-stated recommendations.",
    "Every numeric effect must be copied faithfully from source text.",
    "Applicability boundary and source anchor are required.",
    "If the source does not support a field, return null or defer.",
)

REQUESTED_FIELDS = (
    "kind",
    "population",
    "intervention",
    "exposure",
    "intervention_or_exposure",
    "comparator",
    "outcome",
    "effect",
    "recommendation",
    "applicability_boundary",
    "anchor",
    "source_span",
)


def prepare_blind_tasks(
    source_records: list[dict[str, Any]],
    *,
    batch_id: str,
    run_id: str,
    created_at: datetime,
) -> list[TaskBundle]:
    tasks: list[TaskBundle] = []
    for index, record in enumerate(source_records, start=1):
        source_id = record["source_id"]
        evidence_id = record.get("evidence_id") or f"EU-{batch_id}-{index:03d}"
        task_id = f"TASK-BLIND-{batch_id}-{index:03d}"
        source_text = record["source_text"]

        task = TaskBundle.build(
            task_id=task_id,
            task_type="extract_evidence_unit",
            contract_version="E0.4-v0.1",
            run_id=run_id,
            source_id=source_id,
            evidence_id=evidence_id,
            source_snapshot=record["source_snapshot"],
            source_text=source_text,
            source_text_sha256=__import__("hashlib").sha256(
                source_text.encode("utf-8")
            ).hexdigest(),
            requested_fields=REQUESTED_FIELDS,
            rules=BLIND_RULES,
            response_schema_version="ResponseEnvelope-v0.1",
            created_at=created_at,
            provenance=Provenance(
                source=record.get("source_url"),
                provider="BlindTaskFactory-v0.1",
                retrieved_at=created_at,
                lineage_refs=(source_id,),
                metadata={
                    "batch_id": batch_id,
                    "gold_visible_to_task_factory": False,
                    "blind_contract": "source_only",
                },
            ),
        )
        tasks.append(task)
    return tasks


def write_blind_tasks(tasks: list[TaskBundle], out_dir: str | Path) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for task in tasks:
        path = out / f"{task.task_id}.request.json"
        path.write_text(task.model_dump_json(indent=2), encoding="utf-8")


def load_source_fixture(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fixed_e04_time() -> datetime:
    return datetime(2026, 9, 30, 2, 45, tzinfo=timezone.utc)
