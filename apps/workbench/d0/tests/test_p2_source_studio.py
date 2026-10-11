"""P2 source-studio contract tests: complete synthetic workflow, not real qualification."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from d0_app import make_app
from test_d0 import login,accounts
from test_tpa_integrated import REPO
from p2_source_registry import sha

@pytest.fixture
def app(tmp_path):
    identities=accounts()
    identities["p2curator"]={"actor":"SYN-P2-CURATOR-A","role":"curator",
                             "password_hash":identities["producer"]["password_hash"]}
    identities["p2curator2"]={"actor":"SYN-P2-CURATOR-B","role":"curator",
                              "password_hash":identities["producer"]["password_hash"]}
    identities["ea1"]={"actor":"SYN-EA-EXPERT-A","role":"expert",
                       "password_hash":identities["producer"]["password_hash"]}
    return make_app(tmp_path/"data",REPO,accounts=identities,auth_path=tmp_path/"auth.sqlite",
                    origin="http://testserver",allow_synthetic=True)

def record(sid="P2-SYN-TEST-001",fmt="MARKDOWN",raw="# Study\n\nA synthetic trial measured alpha and beta.\n\n| Group | Value |\n|---|---|\n| Mock | 12.4 |"):
    return {"source_id":sid,"revision_id":"r1","title":"Synthetic nutritional study artifact for QA",
     "source_type":"RANDOMIZED_TRIAL","identifier_kind":"SYNTHETIC_ID",
     "identifier":"DEMO-STUDY-001","available_at":"2026-01-01T00:00:00Z",
     "fetched_at":"2026-01-02T00:00:00Z","raw_format":fmt,"raw_content":raw,
     "rights_assertion":"SYNTHETIC_FIXTURE","source_family_refs":[]}

def rights_body():
    return {"decision":"APPROVE_SYNTHETIC",
            "uses":["INTERNAL_SOURCE_REVIEW","MACHINE_PROCESSING","RETAIN_ORIGINAL"],
            "evidence_ref":"SYN-DEMO-RIGHTS-EVIDENCE-001"}

def prepare(app,sid="P2-SYN-TEST-001",fmt="MARKDOWN",raw=None):
    producer,ph=login(app,"producer")
    data=record(sid,fmt,raw) if raw is not None else record(sid,fmt)
    response=producer.post("/v1/p2/sources",headers=ph,json=data)
    assert response.status_code==200,response.text
    auditor,ah=login(app,"auditor")
    rights=auditor.post(f"/v1/p2/sources/{sid}/r1/rights",headers=ah,json=rights_body())
    assert rights.status_code==200,rights.text
    return producer,ph,auditor,ah

def converted(app,sid="P2-SYN-TEST-001",fmt="MARKDOWN",raw=None,payload=None):
    producer,ph,auditor,ah=prepare(app,sid,fmt,raw)
    response=producer.post(f"/v1/p2/sources/{sid}/r1/convert",headers=ph,
                           json={"external_payload":payload})
    assert response.status_code==200,response.text
    curator,ch=login(app,"p2curator")
    doc=curator.get(f"/v1/p2/sources/{sid}/r1/document")
    assert doc.status_code==200,doc.text
    return producer,ph,auditor,ah,curator,ch,doc.json()

def review_all(curator,ch,sid,doc):
    output=[]
    for unit in doc["document"]["units"]:
        quote=unit["text"];request={"unit_id":unit["unit_id"],"decision":"ACCEPT",
            "start_utf16":0,"end_utf16":len(quote.encode("utf-16-le"))//2,
            "source_quote":quote,"source_quote_sha256":hashlib.sha256(quote.encode()).hexdigest(),
            "pdf_locator_status":unit["pdf_locator_status"],"findings":{"conversion_accuracy":"SYNTHETIC_QA_ONLY"}}
        r=curator.post(f"/v1/p2/sources/{sid}/r1/qa",headers=ch,json=request)
        assert r.status_code==200,r.text
        output.append(r.json())
    return output

def test_p2_full_lineage_rights_qa_freeze_scope_restart_without_ea_mutation(app,tmp_path):
    sid="P2-SYN-INTEGRATED-001"
    before=app.state.evidence_engine.list_sources(actor="SYN-PRODUCER-1",role="producer",task_id="EA-P1-SYN-01")
    producer,ph,auditor,ah,curator,ch,document=converted(app,sid)
    assert document["document_sha256"]==sha(document["document"])
    assert document["document"]["parser"]=="MARKDOWN_DETERMINISTIC_V0.1"
    assert len(document["document"]["units"])>=4
    assert "12.4" in json.dumps(document["document"])
    assert producer.get(f"/v1/p2/sources/{sid}/r1/document").status_code==403
    manager,_=login(app,"manager")
    assert manager.get(f"/v1/p2/sources/{sid}/r1/document").status_code==403
    assert manager.get("/v1/p2/sources").json()["total"]==1
    assert "A synthetic trial measured" not in manager.get("/v1/p2/sources").text
    freeze_path=f"/v1/p2/sources/{sid}/r1/freeze"
    before_qa=producer.post(freeze_path,headers=ph,json={"expected_document_sha256":document["document_sha256"]})
    assert before_qa.status_code==409
    assert len(review_all(curator,ch,sid,document))==len(document["document"]["units"])
    frozen=producer.post(freeze_path,headers=ph,json={"expected_document_sha256":document["document_sha256"]})
    assert frozen.status_code==200,frozen.text
    assert frozen.json()["package"]["real_source_qualified"] is False
    assert frozen.json()["package"]["expert_exposure_authorized"] is False
    assert producer.post(freeze_path,headers=ph,json={"expected_document_sha256":document["document_sha256"]}).status_code==409
    assert app.state.p2_source_studio.audit("auditor")["valid"] is True

    proj={"project_id":"PRJ-SYN-P2-TEST","name":"P2 synthetic evidence program",
          "description":"synthetic QA test only","idempotency_key":"p2-prj-001"}
    assert producer.post("/v1/tpa/projects",headers=ph,json=proj).status_code==200
    batch={"batch_id":"BATCH-SYN-P2-TEST","label":"P2 QA Batch",
           "purpose":"synthetic testing","idempotency_key":"p2-batch-001"}
    assert producer.post("/v1/tpa/projects/PRJ-SYN-P2-TEST/batches",headers=ph,json=batch).status_code==200
    scope={"project_id":proj["project_id"],"batch_id":batch["batch_id"]}
    linked=producer.post(f"/v1/p2/sources/{sid}/r1/scope",headers=ph,json=scope)
    assert linked.status_code==200,linked.text
    assert linked.json()["expert_exposure_authorized"] is False
    assert producer.post(f"/v1/p2/sources/{sid}/r1/scope",headers=ph,json=scope).json()["replayed"] is True
    assert manager.get("/v1/p2/sources?project_id=PRJ-SYN-P2-TEST&batch_id=BATCH-SYN-P2-TEST").json()["total"]==1
    assert app.state.evidence_engine.list_sources(actor="SYN-PRODUCER-1",role="producer",task_id="EA-P1-SYN-01")==before
    with app.state.task_production.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM tpa_tasks").fetchone()[0]==0

    restarted=make_app(tmp_path/"data",REPO,accounts=app.state.auth.accounts,
                       auth_path=tmp_path/"auth.sqlite",origin="http://testserver",allow_synthetic=True)
    m,_=login(restarted,"manager")
    detail=m.get(f"/v1/p2/sources/{sid}/r1").json()
    assert detail["status"]=="PACKAGE_FROZEN"
    assert detail["package_sha256"]==frozen.json()["package_sha256"]
    assert m.get("/v1/p2/sources").json()["total"]==1
    assert restarted.state.p2_source_studio.audit("auditor")["valid"] is True

def test_p2_rights_role_and_real_source_intake_kill(app):
    producer,ph=login(app,"producer");auditor,ah=login(app,"auditor")
    manager,mh=login(app,"manager");curator,ch=login(app,"p2curator")
    body=record()
    bad={**body,"rights_assertion":"PUBLIC_WEB", "source_id":"P2-SYN-REAL-DENY"}
    assert producer.post("/v1/p2/sources",headers=ph,json=bad).status_code==403
    assert manager.post("/v1/p2/sources",headers=mh,json=body).status_code==403
    assert curator.post("/v1/p2/sources",headers=ch,json=body).status_code==403
    unauth=TestClient(app)
    assert unauth.get("/v1/p2/sources").status_code==401
    assert unauth.post("/v1/p2/sources",json=body).status_code==403
    assert producer.post("/v1/p2/sources",headers=ph,json=body).status_code==200
    assert producer.post("/v1/p2/sources",headers=ph,json=body).status_code==409
    assert producer.post("/v1/p2/sources/P2-SYN-TEST-001/r1/convert",headers=ph,json={}).status_code==409
    assert producer.post("/v1/p2/sources/P2-SYN-TEST-001/r1/rights",headers=ph,json=rights_body()).status_code==403
    assert auditor.post("/v1/p2/sources/P2-SYN-TEST-001/r1/rights",headers=ah,json={
        **rights_body(),"evidence_ref":"WEB-UNVERIFIED"}).status_code==422
    assert auditor.post("/v1/p2/sources/P2-SYN-TEST-001/r1/rights",headers=ah,json=rights_body()).status_code==200
    assert manager.get("/v1/p2/audit").status_code==403
    assert curator.get("/v1/p2/audit").status_code==403
    assert auditor.get("/v1/p2/audit").json()["valid"] is True

def test_p2_quote_utf16_exact_match_review_immutability(app):
    sid="P2-SYN-UNICODE-TEST";producer,ph,auditor,ah,curator,ch,document=converted(
        app,sid,raw="# Title\n\nA 🙂 unicode text.")
    unit=next(x for x in document["document"]["units"] if "🙂" in x["text"])
    text=unit["text"];quote=text[0:5]
    body={"unit_id":unit["unit_id"],"decision":"ACCEPT","start_utf16":0,
          "end_utf16":len(quote.encode("utf-16-le"))//2,"source_quote":quote,
          "source_quote_sha256":hashlib.sha256(quote.encode()).hexdigest(),
          "pdf_locator_status":"UNRESOLVED"}
    url=f"/v1/p2/sources/{sid}/r1/qa"
    assert curator.post(url,headers=ch,json={**body,"end_utf16":3}).status_code==422
    assert curator.post(url,headers=ch,json={**body,"source_quote":"WRONG"}).status_code==409
    assert curator.post(url,headers=ch,json={**body,"pdf_locator_status":"VERIFIED_UNIQUE_PDF_TEXT"}).status_code==409
    assert curator.post(url,headers=ch,json=body).status_code==200
    assert curator.post(url,headers=ch,json=body).status_code==409
    with app.state.p2_source_studio.connect() as db:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("DELETE FROM p2_reviews WHERE source_id=?",(sid,))

def test_p2_safe_jats_html_and_pdf_external_handoff(app):
    x="<article><front><title>Safe trial</title></front><body><p>A<bold> safe</bold> paragraph.</p><table><tr><td>12.4</td></tr></table></body></article>"
    for sid,fmt,raw in [("P2-SYN-XML-TEST","JATS_XML",x),
                        ("P2-SYN-HTML-TEST","HTML","<h1>Safe</h1><script>BAD-EXEC</script><p>12.4</p>")]:
        producer,ph,auditor,ah,curator,ch,doc=converted(app,sid,fmt,raw)
        assert doc["document"]["units"]
        assert "BAD-EXEC" not in json.dumps(doc)
    producer,ph=login(app,"producer")
    for sid,fmt,raw in [("P2-SYN-XML-BAD","JATS_XML","<!DOCTYPE x [<!ENTITY e SYSTEM 'file:///secret'>]><x>&e;</x>"),
                        ("P2-SYN-HTML-BAD","HTML","<!DOCTYPE html><div>x</div>")]:
        prepare(app,sid,fmt,raw)
        r=producer.post(f"/v1/p2/sources/{sid}/r1/convert",headers=ph,json={})
        assert r.status_code==422
    sid="P2-SYN-PDF-HANDOFF";prepare(app,sid,"PDF_HANDOFF","%PDF-demo-only-not-real")
    assert producer.post(f"/v1/p2/sources/{sid}/r1/convert",headers=ph,json={}).status_code==422
    payload={"adapter":"EXTERNAL_MINERU","units":[
        {"kind":"PARAGRAPH","text":"An external mock paragraph","page_hint":2},
        {"kind":"TABLE_CELL","text":"12.4","page_hint":3}
    ]}
    accepted=producer.post(f"/v1/p2/sources/{sid}/r1/convert",headers=ph,
                           json={"external_payload":payload})
    assert accepted.status_code==200,accepted.text
    curator,ch=login(app,"p2curator");doc=curator.get(f"/v1/p2/sources/{sid}/r1/document").json()
    assert doc["document"]["units"][0]["pdf_locator_status"]=="PAGE_HINT_ONLY"
    assert doc["document"]["parser"]=="EXTERNAL_MINERU_UNVERIFIED"
    assert doc["document"]["units"][1]["page_hint"]==3
    assert accepted.json()["status"]=="QA_PENDING"

def test_p2_rejected_qa_cannot_auto_freeze(app):
    sid="P2-SYN-REJECTED-001";producer,ph,auditor,ah,curator,ch,doc=converted(app,sid)
    u=doc["document"]["units"][0];q=u["text"]
    body={"unit_id":u["unit_id"],"decision":"REJECT","start_utf16":0,
          "end_utf16":len(q.encode("utf-16-le"))//2,"source_quote":q,
          "source_quote_sha256":hashlib.sha256(q.encode()).hexdigest(),
          "pdf_locator_status":"UNRESOLVED"}
    assert curator.post(f"/v1/p2/sources/{sid}/r1/qa",headers=ch,json=body).status_code==200
    response=producer.post(f"/v1/p2/sources/{sid}/r1/freeze",headers=ph,
       json={"expected_document_sha256":doc["document_sha256"]})
    assert response.status_code==409
    assert producer.get(f"/v1/p2/sources/{sid}/r1").json()["status"]=="QA_HOLD"
    assert producer.post(f"/v1/p2/sources/{sid}/r1/scope",headers=ph,json={
        "project_id":"PRJ-SYN-P2-TEST","batch_id":"BATCH-SYN-P2-TEST"}).status_code==409

def test_p2_audit_chain_corruption_rejected_and_manager_readonly(app):
    sid="P2-SYN-SECURE-001";producer,ph,auditor,ah=prepare(app,sid)
    manager,mh=login(app,"manager")
    assert manager.get("/v1/p2/overview").status_code==200
    assert manager.post(f"/v1/p2/sources/{sid}/r1/convert",headers=mh,json={}).status_code==403
    assert manager.get(f"/v1/p2/sources/{sid}/r1/document").status_code==403
    assert app.state.p2_source_studio.audit("auditor")["valid"] is True
    with app.state.p2_source_studio.connect() as db:
        with pytest.raises(sqlite3.IntegrityError):db.execute("DELETE FROM p2_events WHERE source_key=?",(sid+":r1",))
        db.execute("INSERT INTO p2_events(source_key,event,actor,detail,prev_hash,entry_hash,at) VALUES(?,?,?,?,?,?,?)",
                   (sid+":r1","FORGED","SYN-ATTACKER","{}","fake","fake","2026-10-11T00:00:00Z"))
    assert auditor.get("/v1/p2/audit").json()["valid"] is False
