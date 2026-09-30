from datetime import datetime, timezone
from pathlib import Path
import json

from nutrifoundation.domain.blind_replay import BlindnessClass
from nutrifoundation.domain.semantic_worker import (
    ResponseEnvelope,
    WorkerDescriptor,
)
from nutrifoundation.domain.models import Provenance
from nutrifoundation.services.blind_batch import fixed_e04_time, prepare_blind_tasks
from nutrifoundation.services.blind_runner import score_blind_artifact_run


def mini_source_fixture(tmp_path: Path):
    records = [
        {
            "source_id": "SA-X-001",
            "evidence_id": "EU-X-001",
            "source_url": "https://example.org/1",
            "source_snapshot": {
                "source_id": "SA-X-001",
                "source_type": "RCT",
                "title": "Trial",
                "identifiers": {"doi": None, "pmid": "1", "pmcid": None},
                "publication_types": ["Randomized Controlled Trial"],
            },
            "source_text": (
                "100 adults were randomized to Diet A or Diet B. "
                "Weight change was -5.0 kg versus -2.0 kg."
            ),
        },
        {
            "source_id": "SA-X-002",
            "evidence_id": "EU-X-002",
            "source_url": "https://example.org/2",
            "source_snapshot": {
                "source_id": "SA-X-002",
                "source_type": "Guideline",
                "title": "Guideline",
                "identifiers": {"doi": None, "pmid": "2", "pmcid": None},
                "publication_types": ["Practice Guideline"],
            },
            "source_text": "TITLE ONLY. PUBMED ABSTRACT: unavailable",
        },
    ]
    path = tmp_path / "source.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return path, records


def mini_gold(tmp_path: Path):
    gold = {
        "batch_id": "X",
        "EvidenceUnits": [
            {
                "evidence_id": "EU-X-001",
                "source_id": "SA-X-001",
                "population": "100 adults",
                "intervention": "Diet A",
                "comparator": "Diet B",
                "outcome": "weight",
                "effect": "-5.0 kg versus -2.0 kg",
                "applicability_boundary": "Adults represented in the trial",
                "anchor": "Abstract",
            },
            {
                "evidence_id": "EU-X-002",
                "source_id": "SA-X-002",
                "kind": "guideline_recommendation",
                "population": "Adults",
                "recommendation": "Recommendation text",
                "applicability_boundary": "Adults",
                "anchor": "Guideline",
            },
        ],
    }
    import yaml
    path = tmp_path / "gold.yaml"
    path.write_text(yaml.safe_dump(gold), encoding="utf-8")
    return path


def write_tasks(tmp_path, records):
    tasks = prepare_blind_tasks(
        records,
        batch_id="X",
        run_id="RUN-BLIND-X-E04-v01",
        created_at=fixed_e04_time(),
    )
    out = tmp_path / "tasks"
    out.mkdir()
    for task in tasks:
        (out / f"{task.task_id}.request.json").write_text(
            task.model_dump_json(indent=2),
            encoding="utf-8",
        )
    return out, tasks


def test_blind_task_factory_has_no_gold_parameter_and_no_gold_content(tmp_path):
    _, records = mini_source_fixture(tmp_path)
    _, tasks = write_tasks(tmp_path, records)
    payload = tasks[0].model_dump(mode="json")
    assert "gold" not in json.dumps(payload).lower()
    assert "expected_answer" not in json.dumps(payload).lower()


def test_hidden_gold_is_loaded_only_by_scoring_stage(tmp_path):
    source_path, records = mini_source_fixture(tmp_path)
    gold_path = mini_gold(tmp_path)
    task_dir, tasks = write_tasks(tmp_path, records)
    responses = tmp_path / "responses"
    responses.mkdir()

    first = tasks[0]
    response1 = ResponseEnvelope(
        response_id="RESP-1",
        task_id=first.task_id,
        task_sha256=first.task_sha256,
        contract_version=first.contract_version,
        response_schema_version=first.response_schema_version,
        source_text_sha256=first.source_text_sha256,
        worker=WorkerDescriptor(
            worker_id="chat",
            adapter_type="chat_window_file_bridge",
        ),
        status="completed",
        output={
            "population": "100 adults",
            "intervention": "Diet A",
            "comparator": "Diet B",
            "outcome": "weight",
            "effect": "-5.0 kg versus -2.0 kg",
            "applicability_boundary": "Adults represented in the trial",
            "anchor": "Abstract",
        },
        confidence=0.99,
        created_at=datetime.now(timezone.utc),
        provenance=Provenance(source="test"),
    )
    (responses / f"{first.task_id}.response.json").write_text(
        response1.model_dump_json(indent=2),
        encoding="utf-8",
    )

    second = tasks[1]
    response2 = ResponseEnvelope(
        response_id="RESP-2",
        task_id=second.task_id,
        task_sha256=second.task_sha256,
        contract_version=second.contract_version,
        response_schema_version=second.response_schema_version,
        source_text_sha256=second.source_text_sha256,
        worker=WorkerDescriptor(
            worker_id="chat",
            adapter_type="chat_window_file_bridge",
        ),
        status="defer",
        output={},
        uncertainties=("No abstract available.",),
        created_at=datetime.now(timezone.utc),
        provenance=Provenance(source="test"),
    )
    (responses / f"{second.task_id}.response.json").write_text(
        response2.model_dump_json(indent=2),
        encoding="utf-8",
    )

    report = score_blind_artifact_run(
        source_fixture_path=source_path,
        response_dir=responses,
        hidden_gold_path=gold_path,
        db_path=tmp_path / "blind.db",
        batch_id="X",
        blindness_class=BlindnessClass.STRICT,
    )
    assert report.case_count == 2
    assert report.f0_freeze_count == 1
    assert report.deferred_count == 1
    assert report.operational_escalation_count == 1
    assert report.benchmark_adjudication_count >= 1


def test_source_only_task_generation_does_not_accept_hidden_gold(tmp_path):
    _, records = mini_source_fixture(tmp_path)
    tasks = prepare_blind_tasks(
        records,
        batch_id="X",
        run_id="RUN-BLIND-X-E04-v01",
        created_at=fixed_e04_time(),
    )
    assert len(tasks) == 2
    assert all(task.contract_version == "E0.4-v0.1" for task in tasks)


def test_hidden_gold_numeric_scoring_allows_source_supported_superset():
    from nutrifoundation.services.blind_scoring import score_field

    score = score_field(
        "effect",
        "44% vs 70%; HR 0.63",
        "After 4 years, 44% vs 70%; HR 0.63 and adjusted HR 0.70",
    )
    assert "numeric_effect_mismatch" not in score.errors


def test_hidden_gold_range_endpoints_match_hyphenated_source_style():
    from nutrifoundation.services.blind_scoring import score_field

    score = score_field(
        "effect",
        "OR 19.7 (95% CI 7.8-49.8)",
        "OR 19.7 (95% CI 7.8 to 49.8)",
    )
    assert "numeric_effect_mismatch" not in score.errors


def test_hidden_reference_mismatch_never_triggers_operational_escalation():
    from nutrifoundation.services.blind_scoring import score_case

    gold = {
        "evidence_id": "EU-X-003",
        "source_id": "SA-X-003",
        "population": "Adults with condition X",
        "intervention": "Diet A",
        "outcome": "Outcome Y",
        "effect": "HR 0.80",
        "applicability_boundary": "Narrow trial population",
        "anchor": "Abstract",
    }
    observed = {
        "population": "Adults with condition X",
        "intervention": "Diet A",
        "outcome": "Outcome Y",
        "effect": "HR 0.80",
        "applicability_boundary": "Broader wording that differs from reference",
        "anchor": "Abstract",
    }

    case = score_case(
        gold,
        observed,
        response_status="completed",
        verifier_status="verified",
        f0_frozen=True,
    )

    assert case.operational_escalation_required is False
    assert case.benchmark_adjudication_required is True
