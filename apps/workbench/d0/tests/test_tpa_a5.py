"""WB-P1.1-A5: server-page truth, synthetic role gates and original D0 compatibility."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_tpa_integrated import app, prepare_draft  # noqa: F401
from test_d0 import login


def source_body(src, i):
    return {
        "task_id": f"TPA-SYN-A5-LIST-{i:03d}",
        "task_kind": "EVIDENCE_ECOSYSTEM_CASE",
        "primary_source": {"source_id": src["source_id"], "revision_id": src["revision_id"]},
        "allowed_source_versions": [
            {k: src[k] for k in ("source_id", "revision_id", "canonical_document_sha256")}
        ],
        "profile_id": src["profile_id"],
        "knowledge_cutoff": "2026-10-10T00:00:00Z",
        "workflow_strategy": "HUMAN_INDEPENDENT",
    }


def test_a5_103_tasks_server_pagination_search_and_original_shape(app):
    producer, headers = login(app, "producer")
    src = next(s for s in producer.get("/v1/tpa/sources").json()["sources"]
               if s["source_type"] == "RANDOMIZED_TRIAL")
    for n in range(103):
        response = producer.post("/v1/tpa/tasks/drafts", headers=headers, json=source_body(src, n))
        assert response.status_code == 200, response.text

    # Existing no-query P1 response shape is preserved.
    old = producer.get("/v1/tpa/tasks").json()
    assert len(old["tasks"]) == 103 and "total" not in old
    page_one = producer.get("/v1/tpa/tasks?q=A5-LIST&limit=25&offset=0")
    page_two = producer.get("/v1/tpa/tasks?q=A5-LIST&limit=25&offset=25")
    tail = producer.get("/v1/tpa/tasks?q=A5-LIST&limit=25&offset=100")
    assert page_one.status_code == page_two.status_code == tail.status_code == 200
    assert all(p.json()["total"] == 103 for p in (page_one, page_two, tail))
    first_ids = {x["task_id"] for x in page_one.json()["tasks"]}
    second_ids = {x["task_id"] for x in page_two.json()["tasks"]}
    assert len(first_ids) == len(second_ids) == 25 and first_ids.isdisjoint(second_ids)
    assert len(tail.json()["tasks"]) == 3
    assert producer.get("/v1/tpa/tasks?q=A5-LIST-089&limit=25").json()["total"] == 1
    assert producer.get("/v1/tpa/tasks?state=LEGACY&limit=25").json()["total"] == 103
    assert producer.get("/v1/tpa/overview").json()["counts"]["preparing"] == 103


def test_a5_preparing_filter_truth_and_malformed_search_denied(app):
    p, headers, _ = prepare_draft(app, "TPA-SYN-A5-DRAFT-001", strategy="HUMAN_INDEPENDENT")
    prepare_draft(app, "TPA-SYN-A5-VALID-002", strategy="HUMAN_INDEPENDENT")
    prepare_draft(app, "TPA-SYN-A5-FROZEN-003", strategy="HUMAN_INDEPENDENT")
    prepare_draft(app, "TPA-SYN-A5-READY-004", strategy="HUMAN_INDEPENDENT")
    for tid, actions in [
        ("TPA-SYN-A5-VALID-002", ("validate",)),
        ("TPA-SYN-A5-FROZEN-003", ("validate", "freeze")),
        ("TPA-SYN-A5-READY-004", ("validate", "freeze", "prepare")),
    ]:
        for action in actions:
            res = p.post(f"/v1/tpa/tasks/{tid}/{action}", headers=headers)
            assert res.status_code == 200, res.text

    preparing = p.get("/v1/tpa/tasks?state=PREPARING&limit=25")
    assert preparing.status_code == 200 and preparing.json()["total"] == 3
    assert {t["state"] for t in preparing.json()["tasks"]} == {
        "DRAFT", "VALIDATED", "DEFINITION_FROZEN"
    }
    assert p.get("/v1/tpa/tasks?state=READY_FOR_ASSIGNMENT").json()["total"] == 1
    assert p.get("/v1/tpa/tasks?q=%%%%%%%%").status_code == 422
    assert p.get("/v1/tpa/tasks?q=bad%20markup").status_code == 422
    assert p.get("/v1/tpa/tasks?limit=10000").status_code == 422
    assert p.get("/v1/tpa/overview").json()["counts"]["ready"] == 1


def test_a5_read_model_and_expert_denial_never_grant_source_from_management(app):
    p, headers, _ = prepare_draft(app, "TPA-SYN-A5-BLIND-001", "HUMAN_INDEPENDENT")
    m, _ = login(app, "manager")
    source = m.get("/v1/tpa/tasks?q=A5-BLIND&limit=10")
    assert source.status_code == 200
    item = source.json()["tasks"][0]
    assert item["workflow_strategy"] == "HUMAN_INDEPENDENT"
    assert "candidate" not in str(item).lower() and "units" not in str(item).lower()
    detail = m.get("/v1/tpa/tasks/TPA-SYN-A5-BLIND-001/management")
    assert detail.status_code == 200
    assert detail.json()["scientific_capture"] is False
    assert detail.json()["gold_qualification"] == "NOT_ELIGIBLE"
    assert "canonical_document_sha256" in str(detail.json())
    assert m.get("/v1/ea/tasks/TPA-SYN-A5-BLIND-001/sources").status_code == 403
    ea, _ = login(app, "ea2")
    assert ea.get("/v1/tpa/tasks?q=A5-BLIND").status_code == 403
    assert ea.get("/v1/ea/tasks/TPA-SYN-A5-BLIND-001/workpack").status_code == 403
    assert p.get("/v1/tpa/tasks?q=A5-BLIND").status_code == 200
