from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nutrifoundation.adapters.chat_window import ChatWindowFileBridge
from nutrifoundation.domain.blind_replay import BlindnessClass
from nutrifoundation.domain.enums import SourceType
from nutrifoundation.domain.models import Provenance, SourceArtifact, SourceIdentifiers
from nutrifoundation.domain.semantic_worker import SemanticTaskState, TaskBundle
from nutrifoundation.io.loaders import load_structured
from nutrifoundation.persistence.sqlite import SQLiteStore
from nutrifoundation.services.blind_batch import (
    fixed_e04_time,
    prepare_blind_tasks,
)
from nutrifoundation.services.blind_scoring import score_case, summarize_cases
from nutrifoundation.services.semantic_bridge import SemanticResponseIngestionService


def _source_from_fixture(record: dict[str, Any]) -> SourceArtifact:
    snapshot = record["source_snapshot"]
    identifiers = snapshot.get("identifiers", {})
    return SourceArtifact(
        source_id=record["source_id"],
        source_type=SourceType(snapshot["source_type"]),
        title=snapshot["title"],
        identifiers=SourceIdentifiers(
            doi=identifiers.get("doi"),
            pmid=identifiers.get("pmid"),
            pmcid=identifiers.get("pmcid"),
        ),
        provenance=Provenance(
            source=record.get("source_url"),
            provider="Batch001BlindSourceFixture-v0.1",
            metadata={
                "blind_input": True,
                "gold_visible": False,
            },
        ),
    )


def seed_blind_store(
    source_fixture_path: str | Path,
    store: SQLiteStore,
    *,
    batch_id: str,
    run_id: str = "RUN-BLIND-B001-E04-v01",
) -> dict[str, dict[str, Any]]:
    source_records = json.loads(Path(source_fixture_path).read_text(encoding="utf-8"))
    source_by_id = {record["source_id"]: record for record in source_records}

    store.initialize()
    for record in source_records:
        source = _source_from_fixture(record)
        store.upsert_source(source)
        store.save_source_text(
            source.source_id,
            "blind_source_text",
            record["source_text"],
            "Batch001BlindSourceFixture-v0.1",
        )

    tasks = prepare_blind_tasks(
        source_records,
        batch_id=batch_id,
        run_id=run_id,
        created_at=fixed_e04_time(),
    )
    for task in tasks:
        store.save_semantic_task(task, SemanticTaskState.PENDING)
        store.transition_semantic_task(task.task_id, SemanticTaskState.EXPORTED)

    return source_by_id


def score_blind_artifact_run(
    *,
    source_fixture_path: str | Path,
    response_dir: str | Path,
    hidden_gold_path: str | Path,
    db_path: str | Path,
    batch_id: str,
    blindness_class: BlindnessClass,
):
    store = SQLiteStore(db_path)
    seed_blind_store(
        source_fixture_path,
        store,
        batch_id=batch_id,
    )

    gold_registry = load_structured(hidden_gold_path)
    gold_by_id = {
        item["evidence_id"]: item
        for item in gold_registry["EvidenceUnits"]
    }

    bridge = ChatWindowFileBridge()
    ingestion = SemanticResponseIngestionService(store)

    cases = []
    response_paths = sorted(Path(response_dir).glob("*.response.json"))

    response_by_task = {}
    for path in response_paths:
        response = bridge.load_response(path)
        response_by_task[response.task_id] = response

    for task, state in store.list_semantic_tasks():
        response = response_by_task.get(task.task_id)
        if response is None:
            observed = {}
            response_status = "missing"
            verifier_status = "not_run"
            f0_frozen = False
        else:
            result = ingestion.ingest(response)
            response_status = response.status
            f0_frozen = result.f0_frozen
            verifier_status = (
                "verified"
                if result.f0_frozen
                else (
                    "not_run"
                    if response.status in {"defer", "failed"}
                    else "rejected"
                )
            )
            frozen = store.get_f0_evidence(task.evidence_id)
            observed = (
                frozen.model_dump(mode="json")
                if frozen is not None
                else dict(response.output)
            )

        gold = gold_by_id[task.evidence_id]
        cases.append(
            score_case(
                gold,
                observed,
                response_status=response_status,
                verifier_status=verifier_status,
                f0_frozen=f0_frozen,
            )
        )

    return summarize_cases(
        batch_id=batch_id,
        blindness_class=blindness_class.value,
        cases=cases,
    )


def write_blind_report(report, path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(report.as_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
