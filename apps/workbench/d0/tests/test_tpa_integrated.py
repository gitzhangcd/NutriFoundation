"""TPA-P1 acceptance: original D0 + EA source/Gold separation under synthetic-only management."""
from __future__ import annotations

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from d0_app import make_app
from test_d0 import PASSWORD,accounts,login

REPO=Path(__file__).resolve().parents[4]


@pytest.fixture
def app(tmp_path):
    identities=accounts()
    for name,actor in (("ea1","SYN-EA-EXPERT-A"),("ea2","SYN-EA-EXPERT-B")):
        identities[name]={"actor":actor,"role":"expert","password_hash":identities["r0"]["password_hash"]}
    return make_app(tmp_path/"data",REPO,accounts=identities,
                    auth_path=tmp_path/"auth.sqlite",origin="http://testserver",
                    allow_synthetic=True)


def prepare_draft(app, task_id, strategy="AGENT_PROPOSE_EXPERT_VERIFY", extra=False):
    producer,headers=login(app,"producer")
    sources=producer.get("/v1/tpa/sources").json()["sources"]
    main=next(x for x in sources if x["source_type"]=="RANDOMIZED_TRIAL")
    other=next(x for x in sources if x["source_type"]=="GUIDELINE")
    allow=[main,other] if extra else [main]
    grants=[{k:s[k] for k in ("source_id","revision_id","canonical_document_sha256")} for s in allow]
    body={
        "task_id":task_id,"task_kind":"EVIDENCE_ECOSYSTEM_CASE",
        "primary_source":{"source_id":main["source_id"],"revision_id":main["revision_id"]},
        "allowed_source_versions":grants,"profile_id":main["profile_id"],
        "knowledge_cutoff":"2026-10-10T00:00:00Z","workflow_strategy":strategy
    }
    created=producer.post("/v1/tpa/tasks/drafts",headers=headers,json=body)
    assert created.status_code==200,created.text
    return producer,headers,body


def setup_ready(app, task_id, strategy="AGENT_PROPOSE_EXPERT_VERIFY", extra=False):
    producer,headers,body=prepare_draft(app,task_id,strategy,extra)
    for action,state in (("validate","VALIDATED"),("freeze","DEFINITION_FROZEN"),
                         ("prepare","READY_FOR_ASSIGNMENT")):
        r=producer.post(f"/v1/tpa/tasks/{task_id}/{action}",headers=headers)
        assert r.status_code==200,(action,r.text)
        assert r.json()["state"]==state
    return producer,headers,body


def test_manage_public_shell_and_strict_permissions(app):
    public=TestClient(app)
    assert public.get("/manage").status_code==200
    assert "Task Production & Assignment" in public.get("/manage").text
    assert public.get("/v1/tpa/sources").status_code==401
    assert public.get("/v1/tpa/tasks").status_code==401
    assert public.post("/v1/tpa/tasks/drafts",json={}).status_code==403
    expert,_=login(app,"ea1")
    assert expert.get("/manage").status_code==403
    assert expert.get("/v1/tpa/tasks").status_code==403
    assert expert.get("/v1/tpa/sources").status_code==403
    manager,mh=login(app,"manager")
    sources=manager.get("/v1/tpa/sources")
    assert sources.status_code==200
    assert len(sources.json()["sources"])==7
    assert "units" not in sources.text and "invented trial" not in sources.text
    assert manager.get("/v1/ea/tasks").status_code==403
    assert manager.get("/v1/ea/tasks/EA-P1-SYN-01/sources/RCT-001/r1").status_code==403
    assert manager.post("/v1/tpa/tasks/drafts",headers=mh,json={}).status_code==403
    auditor,_=login(app,"auditor")
    assert auditor.get("/manage").status_code==403


def test_agent_staged_delivery_and_original_nds_nonregression(app):
    tid="TPA-SYN-E2E-001"
    producer,ph,_=prepare_draft(app,tid,extra=True)
    ea1,_=login(app,"ea1")
    assert tid not in [x["task_id"] for x in ea1.get("/v1/ea/tasks").json()["tasks"]]
    assert ea1.get(f"/v1/ea/tasks/{tid}/workpack").status_code==403
    for action in ("validate","freeze","prepare"):
        r=producer.post(f"/v1/tpa/tasks/{tid}/{action}",headers=ph)
        assert r.status_code==200,r.text
    assert ea1.get(f"/v1/ea/tasks/{tid}/workpack").status_code==403
    assert tid not in [x["task_id"] for x in ea1.get("/v1/ea/tasks").json()["tasks"]]
    manager,mh=login(app,"manager")
    assert producer.post(f"/v1/tpa/tasks/{tid}/assign",headers=ph,json={}).status_code==403
    wrong=manager.post(f"/v1/tpa/tasks/{tid}/assign",headers=mh,
        json={"expert_actor":"SYN-EA-EXPERT-B","idempotency_key":"wrong-arm-e2e-001"})
    assert wrong.status_code==403
    assigned=manager.post(f"/v1/tpa/tasks/{tid}/assign",headers=mh,
        json={"expert_actor":"SYN-EA-EXPERT-A","idempotency_key":"agent-assignment-001"})
    assert assigned.status_code==200,assigned.text
    assert ea1.get(f"/v1/ea/tasks/{tid}/sources").status_code==403
    published=manager.post(f"/v1/tpa/tasks/{tid}/publish",headers=mh,
        json={"idempotency_key":"agent-publish-001"})
    assert published.status_code==200,published.text
    assert published.json()["gold_qualification"]=="NOT_ELIGIBLE"
    assert tid in [x["task_id"] for x in ea1.get("/v1/ea/tasks").json()["tasks"]]
    assert ea1.get(f"/v1/ea/tasks/{tid}/workpack").status_code==200
    pack=ea1.get(f"/v1/ea/tasks/{tid}/sources").json()
    assert pack["source_count"]==2
    assert ea1.get(f"/v1/ea/tasks/{tid}/sources/GUIDE-001/r1").status_code==200
    assert ea1.get(f"/v1/ea/tasks/{tid}/sources/META-001/r1").status_code==403
    candidates=ea1.get(f"/v1/ea/tasks/{tid}/candidates").json()
    assert candidates["items"][0]["extraction_run_ref"]=="SYN-FIXTURE-NOT-AN-LLM"
    b=candidates["items"][0]
    _,eh=login(app,"ea1")
    frozen=ea1.post(f"/v1/ea/tasks/{tid}/review/freeze",headers=eh,json={
        "candidate_set_digest":candidates["content_sha256"],"items":[{
            "candidate_id":b["candidate_id"],"field_group":b["field_group"],
            "source_support_status":"PARTIAL","disposition":"REJECT",
            "reason":"Synthetic source has no research validity","expert_anchors":b["original_anchors"]
        }]
    })
    # The independent ea1 session has its own CSRF token: use login's client alongside headers.
    assert frozen.status_code==403
    c,h=login(app,"ea1")
    assert c.post(f"/v1/ea/tasks/{tid}/review/freeze",headers=h,json={
        "candidate_set_digest":candidates["content_sha256"],"items":[{
            "candidate_id":b["candidate_id"],"field_group":b["field_group"],
            "source_support_status":"PARTIAL","disposition":"REJECT",
            "reason":"Synthetic text is not evidence","expert_anchors":b["original_anchors"]
        }]
    }).status_code==200
    assert c.get(f"/v1/ea/tasks/{tid}/export").json()["export_kind"]=="UNQUALIFIED_EXPERT_REVIEW"
    audit,_=login(app,"auditor")
    history=audit.get("/v1/tpa/audit").json()
    assert history["valid"] is True
    assert history["events"]>=8
    assert any(x["event"]=="SOURCE_UNIT_VIEWED" for x in history["recent_events"])
    r0,_=login(app,"r0")
    assert r0.get("/v1/tasks/SYN-R0/read-model").status_code==200
    assert r0.get("/v1/ea/tasks").status_code==403
    assert r0.get(f"/v1/ea/tasks/{tid}/sources/RCT-001/r1").status_code==403


def test_independent_no_agent_metadata_exposure(app):
    tid="TPA-SYN-INDEPENDENT-002"
    producer,ph,_=setup_ready(app,tid,"HUMAN_INDEPENDENT")
    manager,mh=login(app,"manager")
    assert manager.post(f"/v1/tpa/tasks/{tid}/assign",headers=mh,json={
        "expert_actor":"SYN-EA-EXPERT-A","idempotency_key":"indep-bad-arm-002"}).status_code==403
    assert manager.post(f"/v1/tpa/tasks/{tid}/assign",headers=mh,json={
        "expert_actor":"SYN-EA-EXPERT-B","idempotency_key":"indep-assign-002"}).status_code==200
    assert manager.post(f"/v1/tpa/tasks/{tid}/publish",headers=mh,json={
        "idempotency_key":"indep-publish-002"}).status_code==200
    ea2,h=login(app,"ea2")
    work=ea2.get(f"/v1/ea/tasks/{tid}/workpack").json()
    assert work["workflow"]=="HUMAN_INDEPENDENT"
    assert "candidate_status" not in work and "candidate" not in str(work).lower()
    assert ea2.get(f"/v1/ea/tasks/{tid}/candidates").status_code==403
    assert ea2.get(f"/v1/ea/tasks/{tid}/sources/RCT-001/r1").status_code==200
    ea1,_=login(app,"ea1")
    assert ea1.get(f"/v1/ea/tasks/{tid}/workpack").status_code==403
    done=ea2.post(f"/v1/ea/tasks/{tid}/review/freeze",headers=h,
                  json={"items":[{"statement":"Fictional evidence is not qualified."}]})
    assert done.status_code==200,done.text
    assert done.json()["candidate_set_digest"] is None


def test_import_rejection_temporal_profile_csrf_and_conflict(app):
    p,h=login(app,"producer")
    src=p.get("/v1/tpa/sources").json()["sources"][0]
    assert p.post("/v1/tpa/source-imports/validate",json={},headers=h).status_code==422
    assert p.post("/v1/tpa/source-imports/validate",headers=h,json={
        "import_kind":"REAL_PDF","source_id":src["source_id"],"revision_id":src["revision_id"],
        "canonical_document_sha256":src["canonical_document_sha256"]}).status_code==403
    assert p.post("/v1/tpa/source-imports/validate",headers=h,json={
        "import_kind":"EXISTING_SYNTHETIC_SOURCE","source_id":src["source_id"],
        "revision_id":src["revision_id"],"canonical_document_sha256":"0"*64}).status_code==409
    assert p.post("/v1/tpa/tasks/drafts",json={}).status_code==403
    bad={
        "task_id":"TPA-SYN-INVALID-003","task_kind":"DECISION_CASE",
        "primary_source":{"source_id":src["source_id"],"revision_id":src["revision_id"]},
        "allowed_source_versions":[{k:src[k] for k in
           ("source_id","revision_id","canonical_document_sha256")}],
        "profile_id":src["profile_id"],"knowledge_cutoff":"2026-10-10T00:00:00Z",
        "workflow_strategy":"HUMAN_INDEPENDENT"
    }
    assert p.post("/v1/tpa/tasks/drafts",headers=h,json=bad).status_code==403
    bad["task_kind"]="EVIDENCE_ECOSYSTEM_CASE";bad["profile_id"]="WRONG_RCT_PROFILE"
    assert p.post("/v1/tpa/tasks/drafts",headers=h,json=bad).status_code==409
    bad["profile_id"]=src["profile_id"];bad["knowledge_cutoff"]="2025-01-01T00:00:00Z"
    assert p.post("/v1/tpa/tasks/drafts",headers=h,json=bad).status_code==409
    assert p.get("/v1/tpa/tasks").json()["tasks"]==[]


def test_publishing_idempotency_and_role_denial(app):
    tid="TPA-SYN-IDEMPOTENCY-004"
    p,h,_=setup_ready(app,tid)
    m,mh=login(app,"manager")
    a={"expert_actor":"SYN-EA-EXPERT-A","idempotency_key":"idem-assign-004"}
    first=m.post(f"/v1/tpa/tasks/{tid}/assign",headers=mh,json=a)
    assert first.status_code==200
    assert m.post(f"/v1/tpa/tasks/{tid}/assign",headers=mh,json=a).json()==first.json()
    tampered={**a,"expert_actor":"SYN-EA-EXPERT-B"}
    assert m.post(f"/v1/tpa/tasks/{tid}/assign",headers=mh,json=tampered).status_code==409
    key={"idempotency_key":"idem-publish-004"}
    pub=m.post(f"/v1/tpa/tasks/{tid}/publish",headers=mh,json=key)
    assert pub.status_code==200
    assert m.post(f"/v1/tpa/tasks/{tid}/publish",headers=mh,json=key).json()==pub.json()
    assert m.post(f"/v1/tpa/tasks/{tid}/publish",headers=mh,json={"idempotency_key":"different-pub-004"}).status_code==409
    assert p.post(f"/v1/tpa/tasks/{tid}/publish",headers=h,json=key).status_code==403
    auditor,_=login(app,"auditor")
    assert auditor.get("/v1/tpa/audit").json()["valid"] is True


def test_revoke_preserves_read_history_and_blocks_new_access(app):
    tid="TPA-SYN-REVOKE-005"
    setup_ready(app,tid)
    manager,mh=login(app,"manager")
    assert manager.post(f"/v1/tpa/tasks/{tid}/assign",headers=mh,json={
        "expert_actor":"SYN-EA-EXPERT-A","idempotency_key":"revocation-assign-005"}).status_code==200
    assert manager.post(f"/v1/tpa/tasks/{tid}/publish",headers=mh,json={
        "idempotency_key":"revocation-pub-005"}).status_code==200
    expert,_=login(app,"ea1")
    assert expert.get(f"/v1/ea/tasks/{tid}/sources/RCT-001/r1").status_code==200
    revoked=manager.post(f"/v1/tpa/tasks/{tid}/revoke",headers=mh)
    assert revoked.status_code==200,revoked.text
    assert revoked.json()["historical_exposure_remains"] is True
    assert expert.get(f"/v1/ea/tasks/{tid}/sources/RCT-001/r1").status_code==403
    assert expert.get(f"/v1/ea/tasks/{tid}/workpack").status_code==403
    assert tid not in [x["task_id"] for x in expert.get("/v1/ea/tasks").json()["tasks"]]
    assert manager.post(f"/v1/tpa/tasks/{tid}/publish",headers=mh,
                        json={"idempotency_key":"new-epoch-005"}).status_code==409
    auditor,_=login(app,"auditor")
    history=auditor.get("/v1/tpa/audit").json()
    assert history["valid"] is True
    assert any(x["event"]=="SOURCE_UNIT_VIEWED" for x in history["recent_events"])
    assert any(x["event"]=="ACCESS_REVOKED" for x in history["recent_events"])
