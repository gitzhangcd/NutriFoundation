from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from nutrifoundation.adapters.chat_window import ChatWindowFileBridge
from nutrifoundation.adapters.portability import (
    assert_response_binding,
    run_adapter_conformance,
)
from nutrifoundation.domain.enums import SourceType
from nutrifoundation.domain.models import Provenance, SourceArtifact
from nutrifoundation.domain.semantic_worker import (
    ResponseEnvelope,
    SemanticTaskState,
    WorkerDescriptor,
)
from nutrifoundation.persistence.sqlite import SQLiteStore
from nutrifoundation.services.semantic_bridge import (
    SemanticResponseIngestionService,
    SemanticTaskOrchestrator,
)


def make_store(tmp_path: Path) -> SQLiteStore:
    store = SQLiteStore(tmp_path / "semantic.db")
    store.initialize()
    source = SourceArtifact(
        source_id="SA-TEST-001",
        source_type=SourceType.RCT,
        title="Test randomized trial",
        provenance=Provenance(source="fixture"),
    )
    store.upsert_source(source)
    store.save_source_text(
        "SA-TEST-001",
        "pubmed_abstract",
        (
            "100 adults were randomized to Diet A or Diet B. "
            "The primary outcome was weight. "
            "Weight change was -5.0 kg versus -2.0 kg."
        ),
        "fixture",
    )
    return store


def make_response(task, **updates):
    data = dict(
        response_id=f"RESP-{task.task_id}",
        task_id=task.task_id,
        task_sha256=task.task_sha256,
        contract_version=task.contract_version,
        response_schema_version=task.response_schema_version,
        source_text_sha256=task.source_text_sha256,
        worker=WorkerDescriptor(
            worker_id="chat-worker-1",
            adapter_type="chat_window_file_bridge",
            provider="ChatGPT",
            model="test-model",
            prompt_version="E0.3.1-v0.1",
        ),
        status="completed",
        output={
            "kind": "intervention_effect",
            "population": "100 adults",
            "intervention": "Diet A",
            "comparator": "Diet B",
            "outcome": "weight",
            "effect": "-5.0 kg versus -2.0 kg",
            "applicability_boundary": "Adults represented in the trial",
            "anchor": "Abstract",
        },
        confidence=0.95,
        uncertainties=(),
        created_at=datetime.now(timezone.utc),
        provenance=Provenance(source="chat-window-test"),
    )
    data.update(updates)
    return ResponseEnvelope(**data)


def test_task_bundle_hash_is_self_verifying(tmp_path):
    store = make_store(tmp_path)
    task = SemanticTaskOrchestrator(store).prepare_evidence_task(
        "SA-TEST-001",
        "EU-TEST-001",
    )
    assert len(task.task_sha256) == 64
    assert len(task.source_text_sha256) == 64

    payload = task.model_dump(mode="json")
    payload["source_text"] = payload["source_text"] + " tampered"
    with pytest.raises(ValidationError):
        type(task).model_validate(payload)


def test_chat_window_file_bridge_roundtrip(tmp_path):
    store = make_store(tmp_path)
    orchestrator = SemanticTaskOrchestrator(store)
    task = orchestrator.prepare_evidence_task(
        "SA-TEST-001",
        "EU-TEST-001",
    )

    bridge = ChatWindowFileBridge()
    receipt = bridge.export_task(task, tmp_path / "outbox")
    orchestrator.mark_exported(task.task_id, receipt.location)

    loaded_task_path = Path(receipt.location)
    assert loaded_task_path.exists()

    response = make_response(task)
    response_path = tmp_path / "response.json"
    response_path.write_text(
        response.model_dump_json(indent=2),
        encoding="utf-8",
    )
    loaded_response = bridge.load_response(response_path)
    assert_response_binding(task, loaded_response)


def test_completed_chat_response_runs_deterministic_verifier_and_freezes_f0(tmp_path):
    store = make_store(tmp_path)
    task = SemanticTaskOrchestrator(store).prepare_evidence_task(
        "SA-TEST-001",
        "EU-TEST-001",
    )
    result = SemanticResponseIngestionService(store, legacy_f0=True).ingest(
        make_response(task)
    )

    assert result.f0_frozen is True
    assert result.task_state == "f0_frozen"
    frozen = store.get_f0_evidence("EU-TEST-001")
    assert frozen is not None
    assert frozen.effect == "-5.0 kg versus -2.0 kg"

    task_record = store.get_semantic_task(task.task_id)
    assert task_record is not None
    assert task_record[1] == SemanticTaskState.F0_FROZEN


def test_wrong_task_hash_is_rejected_before_candidate_creation(tmp_path):
    store = make_store(tmp_path)
    task = SemanticTaskOrchestrator(store).prepare_evidence_task(
        "SA-TEST-001",
        "EU-TEST-001",
    )
    response = make_response(task).model_copy(
        update={"task_sha256": "0" * 64}
    )

    with pytest.raises(ValueError, match="task_sha256"):
        SemanticResponseIngestionService(store).ingest(response)

    assert store.get_f0_evidence("EU-TEST-001") is None


def test_unknown_provider_output_field_is_rejected_by_core_contract(tmp_path):
    store = make_store(tmp_path)
    task = SemanticTaskOrchestrator(store).prepare_evidence_task(
        "SA-TEST-001",
        "EU-TEST-001",
    )
    response = make_response(task)
    response = response.model_copy(
        update={"output": {**response.output, "provider_secret": "x"}}
    )

    result = SemanticResponseIngestionService(store).ingest(response)
    assert result.task_state == "rejected"
    assert "non-contract fields" in result.errors[0]
    assert store.get_f0_evidence("EU-TEST-001") is None


def test_defer_is_preserved_without_forced_guessing(tmp_path):
    store = make_store(tmp_path)
    task = SemanticTaskOrchestrator(store).prepare_evidence_task(
        "SA-TEST-001",
        "EU-TEST-001",
    )
    response = make_response(
        task,
        status="defer",
        output={},
        confidence=None,
        uncertainties=("Source text is insufficient for effect extraction.",),
    )

    result = SemanticResponseIngestionService(store).ingest(response)
    assert result.task_state == "deferred"
    assert result.f0_frozen is False
    assert store.get_f0_evidence("EU-TEST-001") is None


def test_fake_future_api_adapter_passes_same_portability_contract(tmp_path):
    store = make_store(tmp_path)
    task = SemanticTaskOrchestrator(store).prepare_evidence_task(
        "SA-TEST-001",
        "EU-TEST-001",
    )

    class FakeAPIAdapter:
        adapter_type = "future_api_adapter"

        def execute(self, task):
            response = make_response(task)
            return response.model_copy(
                update={
                    "worker": WorkerDescriptor(
                        worker_id="future-api-worker",
                        adapter_type=self.adapter_type,
                        provider="FutureProvider",
                        model="future-model",
                    )
                }
            )

    response = run_adapter_conformance(FakeAPIAdapter(), task)
    assert response.worker.adapter_type == "future_api_adapter"


def test_adapter_type_mismatch_fails_conformance(tmp_path):
    store = make_store(tmp_path)
    task = SemanticTaskOrchestrator(store).prepare_evidence_task(
        "SA-TEST-001",
        "EU-TEST-001",
    )

    class BadAdapter:
        adapter_type = "expected_adapter"

        def execute(self, task):
            return make_response(task)

    with pytest.raises(ValueError, match="Adapter type mismatch"):
        run_adapter_conformance(BadAdapter(), task)
