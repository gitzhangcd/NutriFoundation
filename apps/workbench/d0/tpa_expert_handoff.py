"""WB-P1.1-B3 fixed synthetic expert roster and exposure-safe handoff receipts.

An operational projection only: the original TPA assign/publish and EA
expert_gate remain the SOLE authorization and exposure authorities.
"""
from __future__ import annotations

import json
import re

from ea_runtime import digest, encoded
from tpa_runtime import block, utcnow

CONTRACT="WB-SYNTHETIC-EXPERT-HANDOFF-v0.1"
TASK=re.compile(r"TPA-SYN-[A-Z0-9-]{3,50}\Z")
KEY=re.compile(r"[A-Za-z0-9_.:-]{8,100}\Z")
ROSTER={
    "SYN-EA-EXPERT-A":{"actor":"SYN-EA-EXPERT-A","mode":"AGENT_PROPOSE_EXPERT_VERIFY",
                       "login_hint":"ea1","qualification":"SYNTHETIC_ACCOUNT_ONLY"},
    "SYN-EA-EXPERT-B":{"actor":"SYN-EA-EXPERT-B","mode":"HUMAN_INDEPENDENT",
                       "login_hint":"ea2","qualification":"SYNTHETIC_ACCOUNT_ONLY"}
}
EXPOSURES={"WORKPACK_VIEWED","SOURCE_UNIT_VIEWED","CANDIDATE_SET_VIEWED","CANDIDATES_VIEWED",
           "SOURCE_VIEWED","SOURCE_METADATA_VIEWED","EXPERT_REVIEW_FROZEN"}
# The original TPA/EA events are authoritative: never infer a view from PUBLISHED.

class ExpertHandoffLedger:
    def __init__(self,tpa):
        self.tpa=tpa
        with tpa.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tpa_expert_handoffs (
                  task_id TEXT PRIMARY KEY,
                  record TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tpa_expert_handoff_replays (
                  request_key TEXT PRIMARY KEY, task_id TEXT NOT NULL,
                  actor TEXT NOT NULL, request_digest TEXT NOT NULL, receipt TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS tpa_b3_handoff_no_update
                  BEFORE UPDATE ON tpa_expert_handoffs
                  BEGIN SELECT RAISE(ABORT,'IMMUTABLE_EXPERT_HANDOFF'); END;
                CREATE TRIGGER IF NOT EXISTS tpa_b3_handoff_no_delete
                  BEFORE DELETE ON tpa_expert_handoffs
                  BEGIN SELECT RAISE(ABORT,'IMMUTABLE_EXPERT_HANDOFF'); END;
                CREATE TRIGGER IF NOT EXISTS tpa_b3_replay_no_update
                  BEFORE UPDATE ON tpa_expert_handoff_replays
                  BEGIN SELECT RAISE(ABORT,'IMMUTABLE_EXPERT_HANDOFF_REPLAY'); END;
                CREATE TRIGGER IF NOT EXISTS tpa_b3_replay_no_delete
                  BEFORE DELETE ON tpa_expert_handoff_replays
                  BEGIN SELECT RAISE(ABORT,'IMMUTABLE_EXPERT_HANDOFF_REPLAY'); END;
            """)

    def roster(self,role):
        self.tpa.role(role,("manager","producer"))
        return {"experts":[dict(v) for v in ROSTER.values()],
                "qualification":"SYNTHETIC_ACCOUNT_ONLY",
                "real_qualification":False,"new_credentials_created":False,
                "scientific_capture":False}

    def _get(self,role,task_id):
        self.tpa.role(role,("manager","producer"))
        if not isinstance(task_id,str) or not TASK.fullmatch(task_id):
            block("INVALID_EXPERT_TASK_ID")
        return self.tpa.get(task_id)

    @staticmethod
    def _match(task):
        expected="SYN-EA-EXPERT-A" if task["workflow_strategy"]=="AGENT_PROPOSE_EXPERT_VERIFY" else (
            "SYN-EA-EXPERT-B" if task["workflow_strategy"]=="HUMAN_INDEPENDENT" else None)
        if expected is None:block("UNSUPPORTED_EXPERT_WORKFLOW")
        return ROSTER[expected]

    def _events(self,db,task_id):
        return [dict(x) for x in db.execute(
            "SELECT seq,event,actor,detail,at,entry_hash FROM tpa_events WHERE task_id=? ORDER BY seq",
            (task_id,))]

    def _facts(self,role,task_id):
        task=self._get(role,task_id)
        expected=self._match(task)
        with self.tpa.connect() as db:
            events=self._events(db,task_id)
        assignments=[x for x in events if x["event"]=="EXPERT_ASSIGNED"]
        releases=[x for x in events if x["event"]=="TASK_PUBLISHED"]
        grants=[x for x in events if x["event"]=="GRANT_ISSUED"]
        revocations=[x for x in events if x["event"]=="ACCESS_REVOKED"]
        assigned=task.get("assigned_expert")
        if assigned is not None and assigned!=expected["actor"]:
            block("CROSS_ARM_PRIOR_EXPOSURE")
        if task["state"] in ("ASSIGNED","PUBLISHED","REVOKED"):
            if len(assignments)!=1 or assigned!=expected["actor"]:
                block("ASSIGNMENT_PROVENANCE_MISMATCH")
            if json.loads(assignments[0]["detail"]).get("assigned_expert")!=assigned:
                block("ASSIGNMENT_PROVENANCE_MISMATCH")
        if task["state"] in ("PUBLISHED","REVOKED") and task.get("published_at"):
            if len(releases)!=1 or len(grants)!=1:
                block("PUBLISH_GRANT_PROVENANCE_MISMATCH")
            if json.loads(releases[0]["detail"]).get("expert_actor")!=assigned or (
                json.loads(grants[0]["detail"]).get("expert_actor")!=assigned):
                block("PUBLISH_GRANT_PROVENANCE_MISMATCH")
        if task["state"]=="PUBLISHED" and (not task["published_at"] or revocations):
            block("PUBLISH_GRANT_PROVENANCE_MISMATCH")
        if task["state"]=="REVOKED" and not revocations:
            block("REVOKE_PROVENANCE_MISMATCH")
        if task["workflow_strategy"]=="HUMAN_INDEPENDENT":
            # B3 never reads or exposes candidate payload. Even a tampered EA
            # independent-arm candidate row invalidates downstream handoff.
            with self.tpa.evidence.connect() as e:
                if e.execute("SELECT 1 FROM candidate_sets WHERE task_id=?",(task_id,)).fetchone():
                    block("DENY_INDEPENDENT_AGENT_EXPOSURE")
        primary=task["primary_source"]
        source=self.tpa.registered_source(primary["source_id"],primary["revision_id"])
        permitted=task["allowed_source_versions"]
        if not any(x["source_id"]==primary["source_id"] and x["revision_id"]==primary["revision_id"]
                   and x["canonical_document_sha256"]==source["canonical_document_sha256"] for x in permitted):
            block("SOURCE_REVISION_MISMATCH")
        exposure=[x for x in events if x["event"] in EXPOSURES and x["actor"]==assigned]
        # This is recorded event telemetry ONLY, not proof of comprehension,
        # completed judgment, scientific acceptance or exposure completeness.
        snapshot={
            "task_id":task_id,"state":task["state"],"workflow_strategy":task["workflow_strategy"],
            "expected_expert_actor":expected["actor"],"assigned_expert":assigned,
            "synthetic_roster_qualification":"SYNTHETIC_ACCOUNT_ONLY",
            "source_ref":{"source_id":primary["source_id"],"revision_id":primary["revision_id"],
                          "canonical_document_sha256":source["canonical_document_sha256"]},
            "task_definition_sha256":task.get("definition_sha256"),
            "assignment_event_hash":assignments[0]["entry_hash"] if assignments else None,
            "published_event_hash":releases[0]["entry_hash"] if releases else None,
            "grant_event_hash":grants[0]["entry_hash"] if grants else None,
            "revocation_event_hash":revocations[-1]["entry_hash"] if revocations else None,
            "published_at":task.get("published_at"),
            "can_assign":task["state"]=="READY_FOR_ASSIGNMENT",
            "can_publish":task["state"]=="ASSIGNED" and bool(assignments),
            "can_handoff":task["state"]=="PUBLISHED" and bool(releases) and bool(grants),
            "expert_gate_state":"TASK_AUTHORIZED_ONLY" if task["state"]=="PUBLISHED" else "CLOSED",
            "recorded_exposure_events":len(exposure),
            "last_recorded_exposure_at":exposure[-1]["at"] if exposure else None,
            "historical_exposure_remains":bool(exposure),
            "expert_read_or_completed_inferred":False,
            "candidate_payload_exposed":False,"source_original_text_exposed":False,
            "real_expert_qualified":False,"scientific_capture":False,
            "gold_qualification":"NOT_ELIGIBLE"
        }
        return snapshot

    def preview(self,role,task_id):
        return {"contract":CONTRACT,**self._facts(role,task_id),
                "preview_only":True,"grant_created":False,"model_executed":False}

    def listing(self,role,limit=25,offset=0):
        self.tpa.role(role,("manager","producer"))
        if type(limit)!=int or type(offset)!=int or not (1<=limit<=100 and 0<=offset<=100000):
            block("INVALID_PAGINATION")
        with self.tpa.connect() as db:
            count=db.execute("SELECT COUNT(*) FROM tpa_tasks").fetchone()[0]
            ids=db.execute("SELECT task_id FROM tpa_tasks ORDER BY task_id DESC LIMIT ? OFFSET ?",(limit,offset)).fetchall()
        rows=[self._facts(role,x["task_id"]) for x in ids]
        return {"tasks":rows,"total":count,"limit":limit,"offset":offset,
                "synthetic_only":True,"source_original_text_exposed":False,
                "candidate_payload_exposed":False,"real_expert_qualification":False}

    def attest(self,role,actor,task_id,body):
        self.tpa.role(role,("manager",))
        key=body["idempotency_key"]
        if not KEY.fullmatch(key):block("INVALID_IDEMPOTENCY_KEY")
        if body["contract"]!=CONTRACT:block("INVALID_HANDOFF_CONTRACT")
        facts=self._facts(role,task_id)
        if not facts["can_handoff"]:block("TASK_NOT_PUBLISHED_FOR_HANDOFF")
        if facts["grant_event_hash"]!=body["expected_grant_event_hash"] or (
            facts["assignment_event_hash"]!=body["expected_assignment_event_hash"]):
            block("EXPERT_HANDOFF_STALE")
        request_digest=digest({**body,"task_id":task_id})
        with self.tpa.lock,self.tpa.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous=db.execute("SELECT * FROM tpa_expert_handoff_replays WHERE request_key=?",(key,)).fetchone()
            if previous:
                if previous["task_id"]!=task_id or previous["actor"]!=actor or previous["request_digest"]!=request_digest:
                    block("IDEMPOTENCY_CONFLICT")
                return json.loads(previous["receipt"])
            if db.execute("SELECT 1 FROM tpa_expert_handoffs WHERE task_id=?",(task_id,)).fetchone():
                block("EXPERT_HANDOFF_ALREADY_FROZEN")
            record={k:facts[k] for k in ("task_id","workflow_strategy","expected_expert_actor",
                "assigned_expert","source_ref","task_definition_sha256","assignment_event_hash",
                "published_event_hash","grant_event_hash","published_at",
                "synthetic_roster_qualification")}
            record.update({"contract":CONTRACT,"status":"SYNTHETIC_HANDOFF_ATTESTED",
                           "attested_at":utcnow(),"attested_by":actor,
                           "real_expert_qualified":False,"scientific_capture":False,
                           "gold_qualification":"NOT_ELIGIBLE","expert_read_or_completed_inferred":False})
            record["handoff_sha256"]=digest(record)
            receipt={"handoff":record,"replayed":False,"authorization_source":"ORIGINAL_TPA_EA_GATE",
                     "real_expert_qualified":False}
            db.execute("INSERT INTO tpa_expert_handoffs(task_id,record) VALUES(?,?)",
                       (task_id,encoded(record).decode()))
            db.execute("INSERT INTO tpa_expert_handoff_replays VALUES(?,?,?,?,?)",
                       (key,task_id,actor,request_digest,encoded(receipt).decode()))
            self.tpa.event(db,task_id,actor,"SYNTHETIC_HANDOFF_ATTESTED",{
                "handoff_sha256":record["handoff_sha256"],
                "assignment_event_hash":record["assignment_event_hash"],
                "grant_event_hash":record["grant_event_hash"],"scientific_capture":False})
            return receipt

    def detail(self,role,task_id):
        facts=self._facts(role,task_id)
        with self.tpa.connect() as db:
            row=db.execute("SELECT record FROM tpa_expert_handoffs WHERE task_id=?",(task_id,)).fetchone()
        handoff=json.loads(row["record"]) if row else None
        if handoff:
            valid=digest({k:v for k,v in handoff.items() if k!="handoff_sha256"})==handoff["handoff_sha256"]
            for k in ("task_id","workflow_strategy","expected_expert_actor","assigned_expert",
                      "source_ref","task_definition_sha256","assignment_event_hash",
                      "published_event_hash","grant_event_hash"):
                valid=valid and handoff[k]==facts[k]
            if not valid:block("EXPERT_HANDOFF_DRIFT")
        return {"contract":CONTRACT,**facts,"handoff":handoff,
                "handoff_status":"ATTESTED" if handoff else "NOT_ATTESTED",
                "real_expert_qualified":False}
