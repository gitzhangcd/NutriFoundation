"""Runtime regression tests for G1 task-scoped engineering pilot.

Use D0 authenticated session middleware, never mock production credentials.
"""
from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from d0_app import make_app
from test_d0 import REPO, accounts, login


@pytest.fixture()
def app(tmp_path):
    return make_app(
        tmp_path / "data", REPO, accounts=accounts(),
        auth_path=tmp_path / "auth.sqlite", origin="http://testserver",
        allow_synthetic=True, enable_g1_pilot=True,
    )


def test_pilot_opt_in_default_disabled(tmp_path):
    app = make_app(
        tmp_path / "data", REPO, accounts=accounts(),
        auth_path=tmp_path / "auth.sqlite", origin="http://testserver",
        allow_synthetic=True,
    )
    c, _ = login(app, "r0")
    assert c.get("/v1/g1/pilot/tasks").status_code == 404


def test_anonymous_denied_and_manager_not_expert(app):
    unauth = TestClient(app)
    assert unauth.get("/v1/g1/pilot/tasks").status_code == 401
    assert unauth.get("/v1/g1/pilot/tasks/CAND-G100-004/source").status_code == 401
    manager, _ = login(app, "manager")
    assert manager.get("/v1/g1/pilot/tasks").status_code == 403
    assert manager.get("/v1/g1/pilot/tasks/CAND-G100-004/source").status_code == 403
    assert manager.get("/v1/g1/pilot/audit/status").status_code == 200
    r2, _ = login(app, "r2")
    assert r2.get("/v1/g1/pilot/tasks").status_code == 403


def test_exact_source_scoping_original_and_rights(app):
    a, _ = login(app, "r0")
    r = a.get("/v1/g1/pilot/tasks")
    assert r.status_code == 200
    assert len(r.json()["items"]) == 5
    assert all(t["agent_candidates_visible"] is False for t in r.json()["items"])
    assert not any("candidate_extraction_for_dev_only" in t for t in r.json()["items"])
    data = a.get("/v1/g1/pilot/tasks/CAND-G100-004/source")
    assert data.status_code == 200, data.text
    j = data.json()
    assert j["availability"] == "LICENSED_PMC_TEXT_BODY_ONLY"
    assert len(j["source_body"]) == 40271
    assert j["translation"] is None
    assert j["scientific_gold"] is False
    assert j["original_pdf_parity"] == "NOT_VERIFIED"
    cohort = a.get("/v1/g1/pilot/tasks/CAND-G100-029/source").json()
    assert cohort["source_body"] is None
    assert cohort["availability"] == "EXTERNAL_LINK_ONLY"
    assert a.get("/v1/g1/pilot/tasks/../../etc/passwd/source").status_code != 200
    assert a.get("/v1/g1/pilot/tasks/CAND-G100-081/source").status_code == 404


def test_two_reviewer_immutable_draft_isolation(app):
    a, ah = login(app, "r0")
    b, bh = login(app, "r1")
    item = "CAND-G100-004"
    base = "/v1/g1/pilot/tasks/" + item
    assert a.get(base + "/review").json()["answers"] == {}
    draft = {"expected_revision": 0, "answers": {"source_type": "RCT: direct source review"}}
    assert a.put(base + "/review", json=draft).status_code == 403  # CSRF
    assert a.put(base + "/review", json=draft, headers=ah).status_code == 200
    assert b.get(base + "/review").json()["answers"] == {}
    assert a.get(base + "/review").json()["revision"] == 1
    assert a.put(base + "/review", json=draft, headers=ah).status_code == 409
    bad = {"expected_revision": 1, "answers": {"agent_gold_answer": "pretend"}}
    assert a.put(base + "/review", json=bad, headers=ah).status_code == 422
    assert a.post(base + "/freeze", json={"expected_revision": 1}, headers=ah).status_code == 422
    form = a.get("/v1/g1/pilot/tasks").json()["items"][0]
    assert len(form["fields"]) == 14
    answers = {f["field_id"]: "Unresolved: expert defer and source evidence not yet checked" for f in form["fields"]}
    assert a.put(base + "/review", json={"expected_revision": 1, "answers": answers}, headers=ah).status_code == 200
    frozen = a.post(base + "/freeze", json={"expected_revision": 2}, headers=ah)
    assert frozen.status_code == 200
    assert frozen.json()["state"] == "ENGINEERING_REVIEW_FROZEN_NOT_GOLD"
    assert frozen.json()["scientific_l4_gold"] is False
    assert a.put(base + "/review", json={"expected_revision": 2, "answers": answers}, headers=ah).status_code == 409
    assert b.get(base + "/review").json()["answers"] == {}
    manager, _ = login(app, "manager")
    audit = manager.get("/v1/g1/pilot/audit/status").json()
    assert audit["engineering_frozen_count"] == 1
    assert audit["scientific_l4_gold_count"] == 0
    assert "answers" not in audit and "candidate" not in audit
    assert a.get("/v1/g1/pilot/audit/status").status_code == 403


def test_headless_pilot_shell_and_security(app):
    a, _ = login(app, "r0")
    page = a.get("/static/g1-source-pilot.html")
    assert page.status_code == 200
    assert "科学来源独立审核" in page.text
    assert "Strict-Blind" in page.text
    assert "candidate_extraction_for_dev_only" not in page.text
    assert a.get("/health").json()["live_pilot"] == "NO_GO"
