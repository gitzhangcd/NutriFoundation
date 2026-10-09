"""WB-EA-P1 integration tests against ORIGINAL D0 app/session, not a second app."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from d0_app import make_app
from test_d0 import PASSWORD, accounts, login


REPO = Path(__file__).resolve().parents[4]


@pytest.fixture
def app(tmp_path):
    return make_app(
        tmp_path / "data", REPO,
        accounts=accounts(),
        auth_path=tmp_path / "auth.sqlite",
        origin="http://testserver",
        allow_synthetic=True,
    )


def test_original_three_pane_ui_and_evidence_mode_share_same_login(app):
    client, head = login(app, "r0")
    html = client.get("/").text
    for required in ('id="expertPanel"', 'id="judgmentPane"', 'id="units"',
                     'id="pdfDetails"', 'id="bilingualToolbar"',
                     'id="eaModeBtn"', 'id="eaTask"', 'id="eaReview"',
                     '/static/reader.js', '/static/workbench.js', '/static/ea_mode.js'):
        assert required in html
    assert client.get("/v1/ea/status").json()["status"] == "D0_INTEGRATED_SYNTHETIC_ONLY"
    assert client.get("/v1/profile").json()["profile_id"] == "NDS_R1_DECISION_CAPTURE"
    assert client.get("/v1/tasks/SYN-R0/read-model").status_code == 200
    assert client.get("/v1/tasks/SYN-R0/sources/SYN-5-2-PAPER/document").status_code == 200


def test_evidence_multi_source_profile_and_frozen_review(app):
    client, head = login(app, "r0")
    tasks = client.get("/v1/ea/tasks").json()["tasks"]
    assert len(tasks) == 7
    task = "EA-P1-SYN-01"
    pack = client.get(f"/v1/ea/tasks/{task}/workpack").json()
    assert pack["source_type"] == "RANDOMIZED_TRIAL"
    assert pack["profile_id"] == "WB_EA_RCT_V0_1"
    result = client.get(f"/v1/ea/tasks/{task}/sources").json()
    assert result["source_count"] == 2
    assert {x["source_id"] for x in result["sources"]} == {"RCT-001", "GUIDE-001"}
    assert client.get(f"/v1/ea/tasks/{task}/sources/GUIDE-001/r1").json()["source_type"] == "GUIDELINE"
    assert client.get(f"/v1/ea/tasks/{task}/sources/META-001/r1").status_code == 403
    frozen = client.get(f"/v1/ea/tasks/{task}/candidates").json()
    cand = frozen["items"][0]
    body = {
        "candidate_set_digest": frozen["content_sha256"],
        "items": [{
            "candidate_id": cand["candidate_id"],
            "field_group": cand["field_group"],
            "source_support_status": "PARTIAL",
            "disposition": "MODIFY",
            "reason": "This fixture is not a genuine research finding",
            "corrected_candidate_payload": {"training_note": "Fictional text only"},
            "expert_anchors": cand["original_anchors"],
        }]
    }
    out = client.post(f"/v1/ea/tasks/{task}/review/freeze", json=body, headers=head)
    assert out.status_code == 200, out.text
    assert out.json()["gold_qualification"] == "NOT_ELIGIBLE"
    assert out.json()["immutable"] is True
    assert client.post(f"/v1/ea/tasks/{task}/review/freeze", json=body, headers=head).status_code == 409
    exported = client.get(f"/v1/ea/tasks/{task}/export").json()
    assert exported["export_kind"] == "UNQUALIFIED_EXPERT_REVIEW"
    assert exported["promotion_authorized"] is False
    # The unchanged NDS R0 authorizations must continue to operate after EA freeze.
    assert client.get("/v1/tasks/SYN-R0/read-model").status_code == 200


def test_login_roles_no_cross_task_or_auditor_source(app):
    a, _ = login(app, "r0")
    b, h = login(app, "r1")
    auditor, _ = login(app, "auditor")
    manager, _ = login(app, "manager")
    assert b.get("/v1/ea/tasks/EA-P1-SYN-01/workpack").status_code == 403
    assert b.get("/v1/ea/tasks/EA-P1-SYN-01/sources/RCT-001/r1").status_code == 403
    assert auditor.get("/v1/ea/tasks").status_code == 403
    assert auditor.get("/v1/ea/tasks/EA-P1-SYN-01/sources/RCT-001/r1").status_code == 403
    assert auditor.get("/v1/ea/audit").json()["chain_valid"] is True
    assert manager.get("/v1/ea/tasks").status_code == 403
    independent = "EA-P1-SYN-INDEPENDENT"
    assert b.get(f"/v1/ea/tasks/{independent}/candidates").status_code == 403
    recorded = b.post(
        f"/v1/ea/tasks/{independent}/review/freeze",
        json={"items": [{"statement": "Uncertain: an association is not causation."}]},
        headers=h,
    )
    assert recorded.status_code == 200, recorded.text
    assert recorded.json()["candidate_set_digest"] is None
    # Original R1 never receives another D0 source via the EA registry.
    assert b.get("/v1/tasks/SYN-R1/sources/SYN-5-2-PAPER/original.pdf").status_code in (403, 404)


def test_cookie_csrf_and_synthetic_only_gates(app):
    unauthenticated = TestClient(app)
    assert unauthenticated.get("/v1/ea/tasks").status_code == 401
    assert unauthenticated.get("/v1/ea/tasks/EA-P1-SYN-01/sources/RCT-001/r1").status_code == 401
    client, head = login(app, "producer")
    assert client.post("/v1/ea/sources", json={}).status_code == 403  # middleware CSRF
    assert client.post("/v1/ea/sources", json={}, headers=head).status_code == 422
    unsafe = {
        "source_id": "UNQUALIFIED-1", "revision_id": "r1",
        "source_type": "GUIDELINE", "title": "unapproved real text",
        "available_at": "2026-01-01T00:00:00Z",
        "fetched_at": "2026-10-10T00:00:00Z",
        "rights_status": "REAL_DOCUMENT", "units": [{"unit_id": "x", "text": "not allowed"}]
    }
    rejected = client.post("/v1/ea/sources", json=unsafe, headers=head)
    assert rejected.status_code == 409
    assert rejected.json()["detail"]["code"] == "SYNTHETIC_ONLY_SOURCE_RIGHTS"
    # Existing NDS roles and exposure remain independent of the additional registry.
    assert app.state.inner.state.controller is not None
