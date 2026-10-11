"""B1 synthetic structure/lineage/rights checks; original EA stays the text owner."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_tpa_integrated import app, prepare_draft  # noqa: F401
from test_d0 import login


def manifest(source):
    return {
        "schema_version":"WB-SOURCE-PACKAGE-v0.1",
        "import_kind":"EXISTING_SYNTHETIC_SOURCE",
        "parser_adapter":"SYNTHETIC_FIXTURE_ADAPTER",
        "source_id":source["source_id"],
        "revision_id":source["revision_id"],
        "source_type":source["source_type"],
        "profile_id":source["profile_id"],
        "canonical_document_sha256":source["canonical_document_sha256"],
        "rights_status":"SYNTHETIC_FIXTURE",
        "parent_package_id":None
    }


def test_b1_validate_zero_side_effect_and_original_text_hidden(app):
    producer, headers=login(app,"producer")
    source=producer.get("/v1/tpa/sources").json()["sources"][0]
    data=manifest(source)
    response=producer.post("/v1/tpa/source-packages/validate",headers=headers,json=data)
    assert response.status_code==200,response.text
    result=response.json()
    assert result["status"]=="VALIDATED_SYNTHETIC_REFERENCE"
    assert result["content_imported"] is False
    assert result["real_source_qualified"] is False
    assert result["gold_qualification"]=="NOT_ELIGIBLE"
    assert result["source_lineage"]["upstream"]=="EA_SEEDED_FIXTURE"
    assert len(result["structure_index"])==2
    assert result["structure_index"][0]["unit_id"]=="u1"
    assert result["structure_index"][0]["element_kind"]=="PARAGRAPH"
    assert len(result["structure_sha256"])==64
    assert "text" not in str(result).lower() or "unit_text_sha256" in str(result)
    assert "A synthetic randomized trial compares" not in response.text
    assert producer.get("/v1/tpa/source-packages").json()["total"]==0
    # Manager read-only cannot validate or register; EA experts cannot even list.
    manager,mh=login(app,"manager")
    assert manager.get("/v1/tpa/source-packages").status_code==200
    assert manager.post("/v1/tpa/source-packages/validate",headers=mh,json=data).status_code==403
    assert manager.post("/v1/tpa/source-packages",headers=mh,json={
        **data,"package_id":"SPKG-SYN-TEST-001","idempotency_key":"manager-no-001"
    }).status_code==403
    ea,_=login(app,"ea1")
    assert ea.get("/v1/tpa/source-packages").status_code==403
    assert ea.get("/v1/tpa/source-packages/SPKG-SYN-TEST-001").status_code==403
    assert TestClient(app).get("/v1/tpa/source-packages").status_code==401


def test_b1_registration_immutability_idempotency_and_audit_chain(app):
    producer,headers=login(app,"producer")
    source=producer.get("/v1/tpa/sources").json()["sources"][0]
    body={**manifest(source),"package_id":"SPKG-SYN-IMMUTABLE-001","idempotency_key":"b1-save-immutable-001"}
    first=producer.post("/v1/tpa/source-packages",headers=headers,json=body)
    assert first.status_code==200,first.text
    assert first.json()["idempotent_replay"] is False
    item=first.json()["package"]
    assert item["manifest_sha256"] and item["structure_sha256"]
    assert item["lineage"]["source_id"]==source["source_id"]
    assert item["canonical_document_sha256"]==source["canonical_document_sha256"]
    assert item["gold_qualification"]=="NOT_ELIGIBLE"
    again=producer.post("/v1/tpa/source-packages",headers=headers,json=body)
    assert again.status_code==200 and again.json()==first.json()
    assert producer.get("/v1/tpa/source-packages").json()["total"]==1
    assert producer.post("/v1/tpa/source-packages",headers=headers,json={
        **body,"idempotency_key":"b1-save-another-001"
    }).status_code==409
    assert producer.post("/v1/tpa/source-packages",headers=headers,json={
        **body,"package_id":"SPKG-SYN-CONFLICT-002"
    }).status_code==409
    manager,_=login(app,"manager")
    listed=manager.get("/v1/tpa/source-packages?limit=5&offset=0")
    assert listed.status_code==200
    assert listed.json()["packages"][0]["package_id"]==body["package_id"]
    detail=manager.get("/v1/tpa/source-packages/"+body["package_id"])
    assert detail.status_code==200
    assert detail.json()["package"]["manifest_sha256"]==item["manifest_sha256"]
    assert "invented trial" not in detail.text
    assert "candidate_payload" not in detail.text
    auditor,_=login(app,"auditor")
    assert auditor.get("/v1/tpa/audit").json()["valid"] is True
    with app.state.task_production.connect() as db:
        with sqlite3.Connection(":memory:") as scratch:
            assert scratch is not None
        try:
            db.execute("UPDATE tpa_source_packages SET source_id='EVIL' WHERE package_id=?",
                       (body["package_id"],))
            assert False,"immutable trigger not enforced"
        except sqlite3.IntegrityError:
            pass
    # Restart registry against same DB: exact package and idempotent receipt survive.
    from tpa_source_packages import SourcePackages
    restored=SourcePackages(app.state.task_production)
    assert restored.detail("producer",body["package_id"])["package"]["manifest_sha256"]==item["manifest_sha256"]
    assert restored.register("producer","SYN-PRODUCER-1",body)==first.json()


def test_b1_invalid_rights_source_digest_parser_lineage_and_schema_fail_closed(app):
    producer,headers=login(app,"producer")
    source=producer.get("/v1/tpa/sources").json()["sources"][0]
    item=manifest(source)
    for delta,expected in [
        ({"import_kind":"REAL_PDF"},403),
        ({"parser_adapter":"MINERU"},403),
        ({"rights_status":"LICENSED"},422),
        ({"canonical_document_sha256":"0"*64},409),
        ({"profile_id":"FAKE_PROFILE"},409),
        ({"source_type":"GUIDELINE"},409),
        ({"schema_version":"WB-SOURCE-PACKAGE-v999"},422),
        ({"parent_package_id":"SPKG-SYN-MISSING-PARENT"},404),
        ({"parent_package_id":"<img src=x>"},422),
        ({"source_id":"IMAGINARY-001"},404),
        ({"unreviewed_html":"<script>alert(1)</script>"},422)
    ]:
        response=producer.post("/v1/tpa/source-packages/validate",headers=headers,json={**item,**delta})
        assert response.status_code==expected,(delta,response.status_code,response.text)
    assert producer.get("/v1/tpa/source-packages").json()["total"]==0
    assert producer.get("/v1/tpa/source-packages?limit=101").status_code==422
    assert producer.get("/v1/tpa/source-packages?offset=-1").status_code==422
    assert producer.get("/v1/tpa/source-packages/SPKG-SYN-MISSING-PARENT").status_code==404
    assert producer.post("/v1/tpa/source-packages",headers=headers,json={
        **item,"package_id":"REAL-PKG","idempotency_key":"invalid-pkg-001"
    }).status_code==422
    assert producer.get("/v1/tpa/source-packages").json()["total"]==0


def test_b1_source_package_not_prerequisite_to_existing_synthetic_tasks(app):
    producer,headers,_=prepare_draft(app,"TPA-SYN-B1-NONREG-001",
                                    strategy="HUMAN_INDEPENDENT")
    assert producer.get("/v1/tpa/source-packages").json()["total"]==0
    for action in ("validate","freeze","prepare"):
        response=producer.post("/v1/tpa/tasks/TPA-SYN-B1-NONREG-001/"+action,headers=headers)
        assert response.status_code==200,response.text
    # B1 registration is purely operational metadata. Does not create EA grants.
    ea,_=login(app,"ea2")
    assert ea.get("/v1/ea/tasks/TPA-SYN-B1-NONREG-001/workpack").status_code==403
    manager,_=login(app,"manager")
    assert manager.get("/v1/tpa/source-packages").json()["total"]==0
