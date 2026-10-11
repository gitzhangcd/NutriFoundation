"""WB-P1.1-B3 safety tests. Original EA/TPA remains sole exposure authority."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_tpa_integrated import app,setup_ready  # noqa: F401
from test_d0 import login

BASE="/v1/tpa/expert-handoffs"
CONTRACT="WB-SYNTHETIC-EXPERT-HANDOFF-v0.1"


def assign(manager,headers,task,actor,key):
    return manager.post(f"/v1/tpa/tasks/{task}/assign",headers=headers,
                        json={"expert_actor":actor,"idempotency_key":key})


def publish(manager,headers,task,key):
    return manager.post(f"/v1/tpa/tasks/{task}/publish",headers=headers,json={"idempotency_key":key})


def request(preview,key):
    return {"contract":CONTRACT,"idempotency_key":key,
            "expected_assignment_event_hash":preview["assignment_event_hash"],
            "expected_grant_event_hash":preview["grant_event_hash"]}


def test_b3_only_fixed_synthetic_roster_and_no_secondary_credential_system(app):
    manager,mh=login(app,"manager")
    data=manager.get("/v1/tpa/expert-roster")
    assert data.status_code==200,data.text
    assert data.json()["new_credentials_created"] is False
    assert data.json()["real_qualification"] is False
    items=data.json()["experts"]
    assert len(items)==2
    assert {r["actor"] for r in items}=={"SYN-EA-EXPERT-A","SYN-EA-EXPERT-B"}
    assert {r["mode"] for r in items}=={
        "AGENT_PROPOSE_EXPERT_VERIFY","HUMAN_INDEPENDENT"}
    assert all(r["qualification"]=="SYNTHETIC_ACCOUNT_ONLY" for r in items)
    assert "password" not in data.text.lower() and "token" not in data.text.lower()
    assert TestClient(app).get("/v1/tpa/expert-roster").status_code==401
    expert,_=login(app,"ea1")
    assert expert.get("/v1/tpa/expert-roster").status_code==403
    assert expert.get(BASE).status_code==403
    auditor,_=login(app,"auditor")
    assert auditor.get(BASE).status_code==403
    producer,_=login(app,"producer")
    assert producer.get("/v1/tpa/expert-roster").status_code==200


def test_b3_preflight_cross_arm_and_no_prepublish_expert_exposure(app):
    task="TPA-SYN-B3-CROSSARM-001"
    producer,_,_=setup_ready(app,task)
    manager,mh=login(app,"manager")
    roster=manager.get("/v1/tpa/expert-roster").json()
    assert roster["experts"][0]["actor"]=="SYN-EA-EXPERT-A"
    preview=manager.get(BASE+"/"+task+"/preview")
    assert preview.status_code==200,preview.text
    info=preview.json()
    assert info["can_assign"] and not info["can_publish"] and not info["can_handoff"]
    assert info["expected_expert_actor"]=="SYN-EA-EXPERT-A"
    assert info["expert_gate_state"]=="CLOSED"
    assert info["recorded_exposure_events"]==0
    assert info["scientific_capture"] is False
    assert manager.get(BASE).json()["total"]==1
    assert manager.post(BASE+"/"+task+"/attest",headers=mh,json={
        "contract":CONTRACT,"idempotency_key":"b3-before-publish-001",
        "expected_assignment_event_hash":"0"*64,"expected_grant_event_hash":"1"*64
    }).status_code==409
    ea1,_=login(app,"ea1")
    assert ea1.get(f"/v1/ea/tasks/{task}/workpack").status_code==403
    assert assign(manager,mh,task,"SYN-EA-EXPERT-B","b3-wrong-arm-001").status_code==403
    assigned=assign(manager,mh,task,"SYN-EA-EXPERT-A","b3-correct-arm-001")
    assert assigned.status_code==200,assigned.text
    assert ea1.get(f"/v1/ea/tasks/{task}/workpack").status_code==403
    still=manager.get(BASE+"/"+task).json()
    assert still["can_publish"] and not still["can_handoff"]
    assert len(still["assignment_event_hash"])==64
    assert still["grant_event_hash"] is None
    assert producer.get(BASE+"/"+task).status_code==200
    assert producer.post(BASE+"/"+task+"/attest",headers=login(app,"producer")[1],
                         json={"contract":CONTRACT,"idempotency_key":"b3-no-producer-write-001",
                               "expected_assignment_event_hash":"0"*64,"expected_grant_event_hash":"1"*64}).status_code==403


def test_b3_original_publish_grant_then_separate_expert_reader_and_revoke(app):
    task="TPA-SYN-B3-EXPOSURE-001"
    producer,_,_=setup_ready(app,task,"AGENT_PROPOSE_EXPERT_VERIFY",extra=True)
    manager,mh=login(app,"manager")
    assert assign(manager,mh,task,"SYN-EA-EXPERT-A","b3-exposure-assign-001").status_code==200
    after_assign=manager.get(BASE+"/"+task).json()
    assert not after_assign["can_handoff"]
    assert publish(manager,mh,task,"b3-exposure-publish-001").status_code==200
    view=manager.get(BASE+"/"+task)
    assert view.status_code==200,view.text
    ready=view.json()
    assert ready["can_handoff"] and ready["expert_gate_state"]=="TASK_AUTHORIZED_ONLY"
    assert ready["recorded_exposure_events"]==0
    assert ready["historical_exposure_remains"] is False
    assert ready["expert_read_or_completed_inferred"] is False
    assert ready["real_expert_qualified"] is False
    assert "candidate_payload" not in view.text or '"candidate_payload_exposed":false' in view.text.replace(" ","")
    assert "source_quote" not in view.text and "original_anchors" not in view.text
    wrong=manager.post(BASE+"/"+task+"/attest",headers=mh,json={
        **request(ready,"b3-wrong-grant-001"),"expected_grant_event_hash":"0"*64})
    assert wrong.status_code==409 and wrong.json()["detail"]["code"]=="EXPERT_HANDOFF_STALE"
    body=request(ready,"b3-correct-handoff-001")
    success=manager.post(BASE+"/"+task+"/attest",headers=mh,json=body)
    assert success.status_code==200,success.text
    assert success.json()["handoff"]["status"]=="SYNTHETIC_HANDOFF_ATTESTED"
    assert success.json()["handoff"]["grant_event_hash"]==ready["grant_event_hash"]
    assert success.json()["handoff"]["expert_read_or_completed_inferred"] is False
    assert manager.post(BASE+"/"+task+"/attest",headers=mh,json=body).json()==success.json()
    assert manager.post(BASE+"/"+task+"/attest",headers=mh,json={
        **body,"idempotency_key":"b3-new-key-conflict-001"}).status_code==409

    # Expert must log into original EA, not manager's session.
    ea1,_=login(app,"ea1")
    assert ea1.get(f"/v1/ea/tasks/{task}/workpack").status_code==200
    assert ea1.get(f"/v1/ea/tasks/{task}/sources/GUIDE-001/r1").status_code==200
    ea2,_=login(app,"ea2")
    assert ea2.get(f"/v1/ea/tasks/{task}/workpack").status_code==403
    after_view=manager.get(BASE+"/"+task)
    assert after_view.status_code==200
    assert after_view.json()["recorded_exposure_events"]>=1
    assert after_view.json()["last_recorded_exposure_at"] is not None
    assert after_view.json()["expert_read_or_completed_inferred"] is False
    assert after_view.json()["handoff"]["handoff_sha256"]==success.json()["handoff"]["handoff_sha256"]
    assert after_view.json()["real_expert_qualified"] is False

    revoke=manager.post(f"/v1/tpa/tasks/{task}/revoke",headers=mh)
    assert revoke.status_code==200
    assert ea1.get(f"/v1/ea/tasks/{task}/workpack").status_code==403
    expired=manager.get(BASE+"/"+task).json()
    assert expired["state"]=="REVOKED" and expired["expert_gate_state"]=="CLOSED"
    assert expired["historical_exposure_remains"] is True
    assert expired["recorded_exposure_events"]>=1
    assert expired["handoff"]["handoff_sha256"]==success.json()["handoff"]["handoff_sha256"]
    # Same nonce is a read of the committed historical receipt, not a new grant.
    assert manager.post(BASE+"/"+task+"/attest",headers=mh,json=body).json()==success.json()
    assert manager.post(BASE+"/"+task+"/attest",headers=mh,json={
        **body,"idempotency_key":"b3-after-revoke-001"}).status_code==409
    auditor,_=login(app,"auditor")
    history=auditor.get("/v1/tpa/audit").json()
    assert history["valid"] is True
    assert any(x["event"]=="SYNTHETIC_HANDOFF_ATTESTED" for x in history["recent_events"])


def test_b3_independent_arm_no_candidates_and_correct_original_ea_account(app):
    task="TPA-SYN-B3-INDEPENDENT-001"
    producer,_,_=setup_ready(app,task,"HUMAN_INDEPENDENT")
    manager,mh=login(app,"manager")
    ready=manager.get(BASE+"/"+task+"/preview").json()
    assert ready["expected_expert_actor"]=="SYN-EA-EXPERT-B"
    assert ready["workflow_strategy"]=="HUMAN_INDEPENDENT"
    assert ready["can_assign"]
    assert "candidate_set_digest" not in str(ready)
    assert "candidate_count" not in str(ready)
    assert assign(manager,mh,task,"SYN-EA-EXPERT-A","b3-indep-wrong-001").status_code==403
    assert assign(manager,mh,task,"SYN-EA-EXPERT-B","b3-indep-correct-001").status_code==200
    assert publish(manager,mh,task,"b3-indep-publish-001").status_code==200
    preview=manager.get(BASE+"/"+task).json()
    assert preview["can_handoff"]
    ea1,_=login(app,"ea1")
    ea2,_=login(app,"ea2")
    assert ea1.get(f"/v1/ea/tasks/{task}/workpack").status_code==403
    assert ea2.get(f"/v1/ea/tasks/{task}/workpack").status_code==200
    assert ea2.get(f"/v1/ea/tasks/{task}/candidates").status_code==403
    before=manager.get(BASE+"/"+task).json()
    assert before["recorded_exposure_events"]>=1
    assert manager.post(BASE+"/"+task+"/attest",headers=mh,json=request(preview,"b3-indep-handoff-001")).status_code==200
    final=manager.get(BASE+"/"+task)
    assert final.status_code==200
    assert "candidate_set_digest" not in final.text
    assert "candidate_payload" not in final.text or '"candidate_payload_exposed":false' in final.text.replace(" ","")


def test_b3_immutable_replay_input_and_role_security(app):
    task="TPA-SYN-B3-IMMUT-001"
    producer,_,_=setup_ready(app,task)
    manager,mh=login(app,"manager")
    assert assign(manager,mh,task,"SYN-EA-EXPERT-A","b3-immut-assign-001").status_code==200
    assert publish(manager,mh,task,"b3-immut-publish-001").status_code==200
    detail=manager.get(BASE+"/"+task).json()
    data=request(detail,"b3-immut-proof-001")
    assert manager.post(BASE+"/"+task+"/attest",headers=mh,json=data).status_code==200
    assert manager.post(BASE+"/"+task+"/attest",headers=mh,json={
        **data,"expected_grant_event_hash":"0"*64}).status_code==409
    assert manager.post(BASE+"/"+task+"/attest",headers=mh,json={
        **data,"unauthorized_field":"real qualification"}).status_code==422
    assert manager.post(BASE+"/"+task+"/attest",headers=mh,json={
        **data,"contract":"REAL_EXPERT-v9"}).status_code==422
    assert manager.post(BASE+"/"+task+"/attest",json=data).status_code==403
    assert TestClient(app).get(BASE).status_code==401
    assert manager.get(BASE+"?limit=500").status_code==422
    assert manager.get(BASE+"?offset=-1").status_code==422
    assert manager.get(BASE+"/TPA-SYN-MISSING-999").status_code==404
    assert manager.get(BASE+"/bad-task").status_code==422
    with app.state.task_production.connect() as db:
        for sql in ("DELETE FROM tpa_expert_handoffs WHERE task_id=?",
                    "UPDATE tpa_expert_handoffs SET record='{}' WHERE task_id=?"):
            try:db.execute(sql,(task,));assert False,"immutable handoff mutated"
            except sqlite3.IntegrityError:pass
    from tpa_expert_handoff import ExpertHandoffLedger
    again=ExpertHandoffLedger(app.state.task_production)
    assert again.detail("manager",task)["handoff"]["handoff_sha256"]==manager.get(BASE+"/"+task).json()["handoff"]["handoff_sha256"]
