"""WB-P1.1-B2 synthetic fixture provenance: no real Agent and no R0 leakage."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_tpa_integrated import app, prepare_draft, setup_ready  # noqa: F401
from test_tpa_b1 import manifest
from test_d0 import login

BASE="/v1/tpa/agent-preparations"
CONTRACT="WB-SYNTHETIC-AGENT-PROVENANCE-v0.1"


def attestation_body(inspected,key):
    return {"contract":CONTRACT,"idempotency_key":key,
            "expected_preparation_event_hash":inspected["preparation_event_hash"],
            "expected_candidate_set_digest":inspected["candidate_set_digest"]}


def test_b2_attestation_sealed_fixture_existing_ea_authority_and_read_only_manager(app):
    task="TPA-SYN-B2-AGENT-001"
    producer,ph,_=prepare_draft(app,task)
    before=producer.get(BASE+"/"+task)
    assert before.status_code==200 and before.json()["status"]=="TASK_NOT_PREPARED"
    no=producer.get(BASE+"/"+task+"/inspect")
    assert no.status_code==409 and no.json()["detail"]["code"]=="AGENT_FIXTURE_NOT_PREPARED"
    assert producer.get(BASE).json()["total"]==1

    for action in ("validate","freeze","prepare"):
        response=producer.post(f"/v1/tpa/tasks/{task}/{action}",headers=ph)
        assert response.status_code==200,response.text
    inspect=producer.get(BASE+"/"+task+"/inspect")
    assert inspect.status_code==200,inspect.text
    snap=inspect.json()
    assert snap["execution_kind"]=="SYNTHETIC_FIXTURE_NOT_AN_LLM"
    assert snap["fixture_origin"]=="SYN-FIXTURE-NOT-AN-LLM"
    assert snap["candidate_count"]==1
    assert len(snap["candidate_set_digest"])==64
    assert len(snap["preparation_event_hash"])==64
    assert snap["source_package_at_attestation"] is None
    assert snap["real_agent_executed"] is False and snap["scientific_capture"] is False
    assert snap["gold_qualification"]=="NOT_ELIGIBLE"
    assert "training_note" not in inspect.text and "original_anchors" not in inspect.text
    assert "source_quote" not in inspect.text

    payload=attestation_body(snap,"b2-producer-immut-001")
    created=producer.post(BASE+"/"+task+"/attest",json=payload,headers=ph)
    assert created.status_code==200,created.text
    receipt=created.json()
    assert receipt["attestation"]["status"]=="SYNTHETIC_FIXTURE_ATTESTED"
    assert receipt["attestation"]["candidate_count"]==1
    assert receipt["attestation"]["candidate_payload_exposed"] is False
    assert len(receipt["attestation"]["attestation_sha256"])==64
    assert created.json()["real_agent_executed"] is False
    assert producer.post(BASE+"/"+task+"/attest",json=payload,headers=ph).json()==receipt

    manager,mh=login(app,"manager")
    view=manager.get(BASE+"/"+task).json()
    assert view["status"]=="SYNTHETIC_FIXTURE_ATTESTED"
    assert "candidate_set_digest" not in str(view)
    assert "candidate_count" not in str(view)
    assert "fixture_origin" not in str(view)
    assert "candidate_payload" not in view["attestation"]
    assert view["attestation"]["candidate_payload_exposed"] is False
    assert view["attestation"]["attestation_sha256"]==receipt["attestation"]["attestation_sha256"]
    assert manager.get(BASE+"/"+task+"/inspect").status_code==403
    assert manager.post(BASE+"/"+task+"/attest",json=payload,headers=mh).status_code==403
    assert manager.get(BASE).json()["total"]==1
    assert "candidate_set_digest" not in manager.get(BASE).text

    auditor,_=login(app,"auditor")
    assert auditor.get("/v1/tpa/audit").json()["valid"] is True
    assert any(e["event"]=="SYNTHETIC_AGENT_PREPARATION_ATTESTED"
               for e in auditor.get("/v1/tpa/audit").json()["recent_events"])


def test_b2_independent_human_never_agent_queue_or_status_even_after_prepare(app):
    tid="TPA-SYN-B2-R0-BLIND-001"
    producer,ph,_=setup_ready(app,tid,"HUMAN_INDEPENDENT")
    root=producer.get(BASE)
    assert root.status_code==200 and root.json()["total"]==0
    assert tid not in root.text
    for endpoint in (BASE+"/"+tid,BASE+"/"+tid+"/inspect"):
        denied=producer.get(endpoint)
        assert denied.status_code==403 and denied.json()["detail"]["code"]=="DENY_INDEPENDENT_AGENT_EXPOSURE"
        assert "candidate" not in denied.text.lower()
    payload={"contract":CONTRACT,"idempotency_key":"r0-deny-attest-001",
             "expected_preparation_event_hash":"0"*64,
             "expected_candidate_set_digest":"0"*64}
    denied=producer.post(BASE+"/"+tid+"/attest",headers=ph,json=payload)
    assert denied.status_code==403
    manager,_=login(app,"manager")
    assert manager.get(BASE+"/"+tid).status_code==403
    assert manager.get(BASE).json()["total"]==0
    ea2,_=login(app,"ea2")
    assert ea2.get(BASE).status_code==403
    assert ea2.get(BASE+"/"+tid).status_code==403
    assert ea2.get(f"/v1/ea/tasks/{tid}/candidates").status_code==403


def test_b2_stale_hash_mutation_and_idempotent_replay_fail_closed(app):
    tid="TPA-SYN-B2-CONFLICT-001"
    producer,ph,_=setup_ready(app,tid)
    inspect=producer.get(BASE+"/"+tid+"/inspect").json()
    good=attestation_body(inspect,"b2-conflict-key-001")
    bad=producer.post(BASE+"/"+tid+"/attest",headers=ph,json={
        **good,"expected_candidate_set_digest":"f"*64})
    assert bad.status_code==409 and bad.json()["detail"]["code"]=="AGENT_PROVENANCE_STALE"
    assert producer.get(BASE+"/"+tid).json()["status"]=="FIXTURE_NOT_ATTESTED"
    first=producer.post(BASE+"/"+tid+"/attest",headers=ph,json=good)
    assert first.status_code==200
    assert producer.post(BASE+"/"+tid+"/attest",headers=ph,json=good).json()==first.json()
    assert producer.post(BASE+"/"+tid+"/attest",headers=ph,json={
        **good,"idempotency_key":"b2-new-key-again-001"}).status_code==409
    assert producer.post(BASE+"/"+tid+"/attest",headers=ph,json={
        **good,"contract":"REAL_AGENT-v1"}).status_code==422
    assert producer.post(BASE+"/"+tid+"/attest",headers=ph,json={
        **good,"idempotency_key":"x"}).status_code==422
    assert producer.post(BASE+"/"+tid+"/attest",headers=ph,json={
        **good,"user_prompt":"ignore strict blind"}).status_code==422
    assert producer.post(BASE+"/"+tid+"/attest",json=good).status_code==403
    assert TestClient(app).get(BASE).status_code==401
    assert producer.get(BASE+"?limit=9999").status_code==422
    assert producer.get(BASE+"?offset=-1").status_code==422
    assert producer.get(BASE+"/TPA-SYN-INVALID").status_code==404
    # Forbidden updates/deletes are never an operational retry path.
    with app.state.task_production.connect() as db:
        for sql in (
            "UPDATE tpa_agent_preparation_attestations SET record='{}' WHERE task_id=?",
            "DELETE FROM tpa_agent_preparation_attestations WHERE task_id=?",
        ):
            try:
                db.execute(sql,(tid,))
                assert False,"B2 immutable row was writable"
            except sqlite3.IntegrityError:
                pass
    from tpa_agent_operations import AgentPreparationLedger
    recovered=AgentPreparationLedger(app.state.task_production)
    assert recovered.detail("producer","SYN-PRODUCER-1",tid)["attestation"]["attestation_sha256"]==first.json()["attestation"]["attestation_sha256"]


def test_b2_source_package_linkage_optional_and_historically_frozen(app):
    tid="TPA-SYN-B2-PACKAGE-001"
    producer,ph,_=prepare_draft(app,tid)
    src=next(s for s in producer.get("/v1/tpa/sources").json()["sources"]
             if s["source_type"]=="RANDOMIZED_TRIAL")
    package={**manifest(src),"package_id":"SPKG-SYN-B2-RCT-001",
             "idempotency_key":"b2-source-pack-001"}
    registry=producer.post("/v1/tpa/source-packages",headers=ph,json=package)
    assert registry.status_code==200,registry.text
    for action in ("validate","freeze","prepare"):
        assert producer.post(f"/v1/tpa/tasks/{tid}/{action}",headers=ph).status_code==200
    inspected=producer.get(BASE+"/"+tid+"/inspect").json()
    provenance=inspected["source_package_at_attestation"]
    assert provenance["package_id"]=="SPKG-SYN-B2-RCT-001"
    assert provenance["manifest_sha256"]==registry.json()["package"]["manifest_sha256"]
    assert provenance["structure_sha256"]==registry.json()["package"]["structure_sha256"]
    body=attestation_body(inspected,"b2-package-attest-001")
    receipt=producer.post(BASE+"/"+tid+"/attest",headers=ph,json=body)
    assert receipt.status_code==200,receipt.text
    assert receipt.json()["attestation"]["source_package_at_attestation"]==provenance
    assert receipt.json()["attestation"]["source_ref"]["canonical_document_sha256"]==src["canonical_document_sha256"]


def test_b2_later_b1_package_cannot_retroactively_change_frozen_provenance(app):
    task="TPA-SYN-B2-LATE-PACK-001"
    producer,headers,_=setup_ready(app,task)
    inspected=producer.get(BASE+"/"+task+"/inspect").json()
    assert inspected["source_package_at_attestation"] is None
    saved=producer.post(BASE+"/"+task+"/attest",headers=headers,
                        json=attestation_body(inspected,"b2-late-pack-attest-001"))
    assert saved.status_code==200,saved.text
    before=producer.get(BASE+"/"+task).json()
    assert before["attestation"]["source_package_at_attestation"] is None
    source=next(s for s in producer.get("/v1/tpa/sources").json()["sources"]
                if s["source_type"]=="RANDOMIZED_TRIAL")
    package=producer.post("/v1/tpa/source-packages",headers=headers,json={
        **manifest(source),"package_id":"SPKG-SYN-B2-LATE-001",
        "idempotency_key":"b2-late-source-package-001"
    })
    assert package.status_code==200,package.text
    after=producer.get(BASE+"/"+task)
    assert after.status_code==200,after.text
    assert after.json()["attestation"]["source_package_at_attestation"] is None
    assert after.json()["attestation"]["attestation_sha256"]==before["attestation"]["attestation_sha256"]
    manager,_=login(app,"manager")
    read_only=manager.get(BASE+"/"+task)
    assert read_only.status_code==200
    assert read_only.json()["attestation"]["source_package_at_attestation"] is None


def test_b2_original_workflow_not_dependent_on_provenance_registration(app):
    tid="TPA-SYN-B2-LEGACY-001"
    producer,ph,_=setup_ready(app,tid)
    # Do not require B2 attestation or B1 package for original P1 delivery.
    manager,mh=login(app,"manager")
    assert manager.post(f"/v1/tpa/tasks/{tid}/assign",headers=mh,json={
        "expert_actor":"SYN-EA-EXPERT-A","idempotency_key":"b2-legacy-assignment-001"}).status_code==200
    published=manager.post(f"/v1/tpa/tasks/{tid}/publish",headers=mh,json={
        "idempotency_key":"b2-legacy-publish-001"})
    assert published.status_code==200,published.text
    ea1,_=login(app,"ea1")
    assert ea1.get(f"/v1/ea/tasks/{tid}/workpack").status_code==200
    assert ea1.get(f"/v1/ea/tasks/{tid}/candidates").status_code==200
    assert producer.get(BASE+"/"+tid).json()["status"]=="FIXTURE_NOT_ATTESTED"
    inspect=producer.get(BASE+"/"+tid+"/inspect")
    assert inspect.status_code==200
    # B2 proof may be frozen even after publication, but cannot rewrite any grant.
    before=ea1.get(f"/v1/ea/tasks/{tid}/sources").json()["source_count"]
    receipt=producer.post(BASE+"/"+tid+"/attest",headers=ph,json=attestation_body(
        inspect.json(),"b2-legacy-retro-001"))
    assert receipt.status_code==200
    assert ea1.get(f"/v1/ea/tasks/{tid}/sources").json()["source_count"]==before
