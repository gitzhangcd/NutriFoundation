"""WB-P1.1-B4 cross-B1/B2/B3 integration and synthetic-only kill tests.

Covers one shared original EA/TPA authority and independently authenticated
clients; does not implement new science, permissions, Agent or source ingestion.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_tpa_integrated import app,setup_ready,REPO  # noqa: F401
from test_tpa_b1 import manifest
from test_tpa_b2 import attestation_body
from test_tpa_b3 import assign,publish,request
from test_d0 import login,accounts
from d0_app import make_app

B1="/v1/tpa/source-packages"
B2="/v1/tpa/agent-preparations"
B3="/v1/tpa/expert-handoffs"


def source_package(producer,headers):
    source=next(x for x in producer.get("/v1/tpa/sources").json()["sources"]
                if x["source_type"]=="RANDOMIZED_TRIAL")
    data={**manifest(source),"package_id":"SPKG-SYN-B4-RCT-001",
          "idempotency_key":"b4-register-source-001"}
    r=producer.post(B1,headers=headers,json=data)
    assert r.status_code==200,r.text
    return source,data,r.json()


def fresh_app(app):
    """Reconstruct FastAPI / sessions / EA / TPA / B1/B2/B3 from same persisted DB."""
    accts=accounts()
    from test_d0 import PASSWORD
    for name,actor in (("ea1","SYN-EA-EXPERT-A"),("ea2","SYN-EA-EXPERT-B")):
        accts[name]={"actor":actor,"role":"expert","password_hash":accts["r0"]["password_hash"]}
    return make_app(Path(app.state.task_production.path).parent,REPO,accounts=accts,
                    auth_path=Path(app.state.auth.path),origin="http://testserver",
                    allow_synthetic=True)


def test_b4_integrated_source_fixture_expert_handoff_restart_revoke(app):
    producer,ph=login(app,"producer")
    source,manifest_body,source_response=source_package(producer,ph)
    agent="TPA-SYN-B4-INTEGRATED-001"
    independent="TPA-SYN-B4-INDEP-001"
    setup_ready(app,agent,extra=True)
    setup_ready(app,independent,"HUMAN_INDEPENDENT")

    inspected=producer.get(B2+"/"+agent+"/inspect")
    assert inspected.status_code==200,inspected.text
    assert inspected.json()["source_package_at_attestation"]["manifest_sha256"]==source_response["package"]["manifest_sha256"]
    a_body=attestation_body(inspected.json(),"b4-agent-proof-001")
    a_proof=producer.post(B2+"/"+agent+"/attest",headers=ph,json=a_body)
    assert a_proof.status_code==200,a_proof.text
    assert a_proof.json()["attestation"]["candidate_payload_exposed"] is False

    manager,mh=login(app,"manager")
    assert manager.get(B2+"/"+independent).status_code==403
    assert independent not in manager.get(B2).text
    assert "candidate_set_digest" not in manager.get(B2+"/"+agent).text
    assert "candidate_count" not in manager.get(B2+"/"+agent).text
    assert len(manager.get(B3).json()["tasks"])==2

    for task,actor,label in (
        (agent,"SYN-EA-EXPERT-A","b4-agent"),
        (independent,"SYN-EA-EXPERT-B","b4-independent")
    ):
        before=manager.get(B3+"/"+task).json()
        assert before["can_assign"] and not before["can_handoff"]
        assert before["recorded_exposure_events"]==0
        assert assign(manager,mh,task,actor,label+"-assign-001").status_code==200
        assert publish(manager,mh,task,label+"-publish-001").status_code==200
        p=manager.get(B3+"/"+task).json()
        assert p["can_handoff"] and p["recorded_exposure_events"]==0
        assert p["source_ref"]["canonical_document_sha256"]==source["canonical_document_sha256"]
        receipt=manager.post(B3+"/"+task+"/attest",headers=mh,
                             json=request(p,label+"-handoff-001"))
        assert receipt.status_code==200,receipt.text
        assert receipt.json()["handoff"]["expert_read_or_completed_inferred"] is False
        assert "original_anchors" not in receipt.text
    agent_proof_sha=a_proof.json()["attestation"]["attestation_sha256"]
    h_agent_sha=manager.get(B3+"/"+agent).json()["handoff"]["handoff_sha256"]
    h_indep_sha=manager.get(B3+"/"+independent).json()["handoff"]["handoff_sha256"]

    # Restart is a new authenticated app instance referencing precisely the
    # same persisted original EA/TPA DB and immutable B1/B2/B3 receipts.
    recovered=fresh_app(app)
    p2,ph2=login(recovered,"producer")
    m2,mh2=login(recovered,"manager")
    assert p2.get(B1+"/"+manifest_body["package_id"]).json()["package"]["manifest_sha256"]==source_response["package"]["manifest_sha256"]
    assert p2.get(B2+"/"+agent).json()["attestation"]["attestation_sha256"]==agent_proof_sha
    assert m2.get(B3+"/"+agent).json()["handoff"]["handoff_sha256"]==h_agent_sha
    assert m2.get(B3+"/"+independent).json()["handoff"]["handoff_sha256"]==h_indep_sha
    assert p2.post(B1,headers=ph2,json=manifest_body).json()==source_response
    assert p2.post(B2+"/"+agent+"/attest",headers=ph2,json=a_body).json()==a_proof.json()
    assert "candidate_set_digest" not in m2.get(B2+"/"+agent).text

    ea1,_=login(recovered,"ea1")
    ea2,_=login(recovered,"ea2")
    assert ea1.get(f"/v1/ea/tasks/{agent}/workpack").status_code==200
    assert ea2.get(f"/v1/ea/tasks/{independent}/workpack").status_code==200
    assert ea2.get(f"/v1/ea/tasks/{independent}/candidates").status_code==403
    assert ea1.get(f"/v1/ea/tasks/{independent}/workpack").status_code==403
    assert ea2.get(f"/v1/ea/tasks/{agent}/workpack").status_code==403
    assert m2.get(B3+"/"+agent).json()["recorded_exposure_events"]>0
    assert m2.get(B3+"/"+independent).json()["recorded_exposure_events"]>0
    assert m2.get(B3+"/"+agent).json()["expert_read_or_completed_inferred"] is False

    for task in (agent,independent):
        before=m2.get(B3+"/"+task).json()["recorded_exposure_events"]
        revoked=m2.post(f"/v1/tpa/tasks/{task}/revoke",headers=mh2)
        assert revoked.status_code==200,revoked.text
        after=m2.get(B3+"/"+task).json()
        assert after["expert_gate_state"]=="CLOSED"
        assert after["recorded_exposure_events"]==before
        assert after["historical_exposure_remains"] is True
    assert ea1.get(f"/v1/ea/tasks/{agent}/workpack").status_code==403
    assert ea2.get(f"/v1/ea/tasks/{independent}/workpack").status_code==403
    assert m2.get(B3+"/"+agent).json()["handoff"]["handoff_sha256"]==h_agent_sha
    auditor,_=login(recovered,"auditor")
    assert auditor.get("/v1/tpa/audit").json()["valid"] is True


def test_b4_independent_injected_candidate_kill_precedes_manager_handoff(app):
    independent="TPA-SYN-B4-R0-POISON-001"
    producer,ph,_=setup_ready(app,independent,"HUMAN_INDEPENDENT")
    # Isolated malicious DB write: original EA immutable triggers block updates,
    # but insert of a brand-new candidate_set for an independent arm is possible
    # for fault-injection purposes. B3 must explicitly refuse the poisoned arm.
    with app.state.evidence_engine.connect() as db:
        db.execute("INSERT INTO candidate_sets(task_id,record,content_sha) VALUES(?,?,?)",
                   (independent,'{"items":[]}',"f"*64))
    manager,mh=login(app,"manager")
    rejected=manager.get(B3+"/"+independent)
    assert rejected.status_code==403 and rejected.json()["detail"]["code"]=="DENY_INDEPENDENT_AGENT_EXPOSURE"
    assert manager.get(B3).status_code==403
    assert manager.get(B2).json()["total"]==0
    assert producer.get(B2+"/"+independent).status_code==403
    assert producer.get(B2+"/"+independent+"/inspect").status_code==403
    assert manager.post(B3+"/"+independent+"/attest",headers=mh,json={
        "contract":"WB-SYNTHETIC-EXPERT-HANDOFF-v0.1",
        "idempotency_key":"b4-unsafe-independent-001",
        "expected_assignment_event_hash":"0"*64,
        "expected_grant_event_hash":"1"*64}).status_code==403
    assert producer.get("/v1/tpa/sources").status_code==200


def test_b4_original_ea_source_drift_invalidates_b1_b2_b3_without_repair(app):
    producer,ph=login(app,"producer")
    source,data,registered=source_package(producer,ph)
    agent="TPA-SYN-B4-SOURCE-DRIFT-001"
    setup_ready(app,agent)
    state=producer.get(B2+"/"+agent+"/inspect").json()
    assert producer.post(B2+"/"+agent+"/attest",headers=ph,
       json=attestation_body(state,"b4-drift-agent-proof-001")).status_code==200
    manager,mh=login(app,"manager")
    assert assign(manager,mh,agent,"SYN-EA-EXPERT-A","b4-drift-assign-001").status_code==200
    assert publish(manager,mh,agent,"b4-drift-publish-001").status_code==200
    published=manager.get(B3+"/"+agent).json()
    assert manager.post(B3+"/"+agent+"/attest",headers=mh,
       json=request(published,"b4-drift-handoff-001")).status_code==200

    # Fault injection against sealed original EA: bypassing an immutable SQL
    # trigger simulates offline DB tampering, not a supported write path.
    with app.state.evidence_engine.connect() as db:
        db.execute("DROP TRIGGER lock_sources_update")
        row=db.execute("SELECT record FROM sources WHERE source_id=? AND revision_id=?",
                       (source["source_id"],source["revision_id"])).fetchone()
        item=json.loads(row["record"])
        item["canonical_document_sha256"]="0"*64
        db.execute("UPDATE sources SET record=? WHERE source_id=? AND revision_id=?",
                   (json.dumps(item),source["source_id"],source["revision_id"]))
    assert producer.get(B1+"/"+data["package_id"]).status_code==409
    assert producer.get(B2+"/"+agent).status_code==409
    assert manager.get(B3+"/"+agent).status_code==409
    assert manager.get(B3).status_code==409
    assert manager.get(B2+"/"+agent).status_code==409
    # Never issue a different claim, rewrite old SHA or silently re-import.
    with app.state.task_production.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM tpa_expert_handoffs").fetchone()[0]==1
        assert db.execute("SELECT COUNT(*) FROM tpa_agent_preparation_attestations").fetchone()[0]==1


def test_b4_immutable_replay_ledger_direct_sql_modification_rejected(app):
    producer,ph=login(app,"producer")
    source,body,_=source_package(producer,ph)
    task="TPA-SYN-B4-IMMUT-001"
    setup_ready(app,task)
    info=producer.get(B2+"/"+task+"/inspect").json()
    assert producer.post(B2+"/"+task+"/attest",headers=ph,
                         json=attestation_body(info,"b4-immut-agent-001")).status_code==200
    manager,mh=login(app,"manager")
    assert assign(manager,mh,task,"SYN-EA-EXPERT-A","b4-immut-assign-001").status_code==200
    assert publish(manager,mh,task,"b4-immut-publish-001").status_code==200
    details=manager.get(B3+"/"+task).json()
    assert manager.post(B3+"/"+task+"/attest",headers=mh,
                        json=request(details,"b4-immut-handoff-001")).status_code==200
    audit,_=login(app,"auditor")
    baseline=audit.get("/v1/tpa/audit").json()
    assert baseline["valid"] is True
    tables=[
        ("tpa_source_packages","package_id",body["package_id"]),
        ("tpa_source_package_replays","request_key",body["idempotency_key"]),
        ("tpa_agent_preparation_attestations","task_id",task),
        ("tpa_agent_preparation_replays","idempotency_key","b4-immut-agent-001"),
        ("tpa_expert_handoffs","task_id",task),
        ("tpa_expert_handoff_replays","request_key","b4-immut-handoff-001")
    ]
    with app.state.task_production.connect() as db:
        for table,key,value in tables:
            for op in ("UPDATE","DELETE"):
                sql=(f"UPDATE {table} SET "+("record='{}'" if table in
                    ("tpa_source_packages","tpa_agent_preparation_attestations","tpa_expert_handoffs")
                    else ("receipt='{}'" if table!="tpa_agent_preparation_replays" else "receipt='{}'"))+
                    f" WHERE {key}=?" if op=="UPDATE" else
                    f"DELETE FROM {table} WHERE {key}=?")
                try:
                    db.execute(sql,(value,))
                    assert False,(table,op)
                except sqlite3.IntegrityError:
                    pass
    assert audit.get("/v1/tpa/audit").json()["valid"] is True


def test_b4_fake_tpa_audit_event_detected_even_when_sql_insert_permitted(app):
    agent="TPA-SYN-B4-AUDIT-001"
    setup_ready(app,agent)
    auditor,_=login(app,"auditor")
    assert auditor.get("/v1/tpa/audit").json()["valid"] is True
    with app.state.task_production.connect() as db:
        db.execute("INSERT INTO tpa_events(task_id,actor,event,detail,at,prev_hash,entry_hash) "
                   "VALUES(?,?,?,?,?,?,?)",(agent,"SYN-ADMIN","FAULT_INJECTED", "{}",
                                           "2026-10-11T00:00:00+00:00","BOGUS","BOGUS"))
    assert auditor.get("/v1/tpa/audit").json()["valid"] is False


def test_b4_explicit_synthetic_mode_off_real_source_and_credentials_denied(app,tmp_path):
    from test_d0 import accounts as base_accounts
    from d0_app import make_app
    import pytest
    with pytest.raises(RuntimeError,match="SYNTHETIC_ONLY"):
        make_app(tmp_path/"formal",REPO,accounts=base_accounts(),
                 auth_path=tmp_path/"formal_auth.sqlite",origin="http://testserver",
                 allow_synthetic=False)
    producer,h=login(app,"producer")
    s=producer.get("/v1/tpa/sources").json()["sources"][0]
    bad=producer.post("/v1/tpa/source-imports/validate",headers=h,json={
        "import_kind":"REAL_PDF","source_id":s["source_id"],"revision_id":s["revision_id"],
        "canonical_document_sha256":s["canonical_document_sha256"]})
    assert bad.status_code==403
    assert producer.post(B1,headers=h,json={
        **manifest(s),"import_kind":"REAL_PDF","parser_adapter":"MINERU_REAL",
        "package_id":"SPKG-SYN-B4-DENIED-001",
        "idempotency_key":"b4-deny-real-001"
    }).status_code in (403,409)
    manager,mh=login(app,"manager")
    assert manager.get("/v1/tpa/expert-roster").json()["real_qualification"] is False
    expert,_=login(app,"ea1")
    for path in (B1,B2,B3,"/v1/tpa/expert-roster"):
        assert expert.get(path).status_code==403
    assert manager.get("/v1/tpa/status").json()["true_agent"] is False
    assert TestClient(app).get("/health").json()["scientific_capture"]=="DISABLED"
