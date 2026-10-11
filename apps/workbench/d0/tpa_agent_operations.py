"""WB-P1.1-B2 synthetic FIXTURE preparation attestation, never an Agent executor.

Only observes existing P1 TPA PREPARATION_FROZEN and original EA candidate
freeze. No LLM calls, candidate mutation, expert exposure or science promotion.
"""
from __future__ import annotations

import json
import re

from ea_runtime import digest, encoded
from tpa_runtime import block, utcnow
from tpa_source_packages import SourcePackages

CONTRACT="WB-SYNTHETIC-AGENT-PROVENANCE-v0.1"
KEY=re.compile(r"[A-Za-z0-9_.:-]{8,100}\Z")
TASK=re.compile(r"TPA-SYN-[A-Z0-9-]{3,50}\Z")
HEX=re.compile(r"[0-9a-f]{64}\Z")
AGENT="AGENT_PROPOSE_EXPERT_VERIFY"
READY={"READY_FOR_ASSIGNMENT","ASSIGNED","PUBLISHED","REVOKED"}
FIXTURE="SYN-FIXTURE-NOT-AN-LLM"
PREPARATION="SYNTHETIC_FIXTURE_NOT_AN_LLM"
ATTESTED="SYNTHETIC_FIXTURE_ATTESTED"


class AgentPreparationLedger:
    """Immutable operational evidence of an *already frozen* fake candidate."""

    def __init__(self,tpa):
        self.tpa=tpa
        with self.tpa.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tpa_agent_preparation_attestations (
                    task_id TEXT PRIMARY KEY,
                    record TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tpa_agent_preparation_replays (
                    idempotency_key TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    request_digest TEXT NOT NULL,
                    receipt TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS tpa_b2_attestation_immutable_update
                    BEFORE UPDATE ON tpa_agent_preparation_attestations
                    BEGIN SELECT RAISE(ABORT,'IMMUTABLE_AGENT_ATTESTATION'); END;
                CREATE TRIGGER IF NOT EXISTS tpa_b2_attestation_immutable_delete
                    BEFORE DELETE ON tpa_agent_preparation_attestations
                    BEGIN SELECT RAISE(ABORT,'IMMUTABLE_AGENT_ATTESTATION'); END;
                CREATE TRIGGER IF NOT EXISTS tpa_b2_replay_immutable_update
                    BEFORE UPDATE ON tpa_agent_preparation_replays
                    BEGIN SELECT RAISE(ABORT,'IMMUTABLE_AGENT_REPLAY'); END;
                CREATE TRIGGER IF NOT EXISTS tpa_b2_replay_immutable_delete
                    BEFORE DELETE ON tpa_agent_preparation_replays
                    BEGIN SELECT RAISE(ABORT,'IMMUTABLE_AGENT_REPLAY'); END;
            """)

    def _task(self,role,task_id):
        self.tpa.role(role,("producer","manager"))
        if not isinstance(task_id,str) or not TASK.fullmatch(task_id):
            block("INVALID_AGENT_TASK_ID")
        task=self.tpa.get(task_id)
        # Strong prohibition: no candidate status, digest, count or run ref for R0.
        if task["workflow_strategy"]!=AGENT:
            block("DENY_INDEPENDENT_AGENT_EXPOSURE")
        return task

    def _package(self,role,source):
        # Registered B1 packages are optional; do not backdate a new package
        # into the frozen candidate's scientific/provenance history.
        with self.tpa.connect() as db:
            row=db.execute("SELECT record FROM tpa_source_packages WHERE source_id=? AND revision_id=?",
                           (source["source_id"],source["revision_id"])).fetchone()
        if row is None:return None
        package=SourcePackages(self.tpa)._load(role,row)
        if package["canonical_document_sha256"]!=source["canonical_document_sha256"]:
            block("SOURCE_PACKAGE_AUTHORITY_MISMATCH")
        return {"package_id":package["package_id"],"manifest_sha256":package["manifest_sha256"],
                "structure_sha256":package["structure_sha256"],
                "registration_kind":"B1_SYNTHETIC_REFERENCE"}

    def _inspect(self,role,task_id):
        task=self._task(role,task_id)
        if task["state"] not in READY:
            block("AGENT_FIXTURE_NOT_PREPARED")
        if not isinstance(task.get("definition_sha256"),str) or not HEX.fullmatch(task["definition_sha256"]):
            block("TASK_DEFINITION_NOT_FROZEN")
        with self.tpa.connect() as db:
            event=db.execute(
                "SELECT entry_hash,detail,actor,at FROM tpa_events WHERE task_id=? AND event='PREPARATION_FROZEN' ORDER BY seq DESC LIMIT 1",
                (task_id,)).fetchone()
        if not event: block("PREPARATION_EVENT_MISSING")
        recorded=json.loads(event["detail"])
        if recorded.get("preparation_kind")!=PREPARATION or recorded.get("strategy")!=AGENT:
            block("PREPARATION_KIND_MISMATCH")
        candidate=self.tpa.evidence.read_candidates(actor=task["created_by"],role="producer",task_id=task_id)
        if not candidate.get("candidate_set_frozen") or not candidate.get("items"):
            block("CANDIDATES_NOT_FROZEN")
        if candidate.get("content_sha256")!=recorded.get("candidate_set_digest"):
            block("CANDIDATE_PROVENANCE_DRIFT")
        source=self.tpa.registered_source(task["primary_source"]["source_id"],task["primary_source"]["revision_id"])
        if not any(x["source_id"]==source["source_id"] and x["revision_id"]==source["revision_id"] and
                   x["canonical_document_sha256"]==source["canonical_document_sha256"]
                   for x in task["allowed_source_versions"]):
            block("SOURCE_REVISION_MISMATCH")
        for item in candidate["items"]:
            if (item.get("candidate_id")!="FIXTURE-"+task_id or
                item.get("extraction_run_ref")!=FIXTURE or
                item.get("source_ref")!={"source_id":source["source_id"],"revision_id":source["revision_id"]} or
                not item.get("original_anchors") or
                any(a.get("canonical_document_sha256")!=source["canonical_document_sha256"] for a in item["original_anchors"])):
                block("NON_FIXTURE_CANDIDATE_PROHIBITED")
        package=self._package(role,source)
        manifest={
            "contract":CONTRACT,
            "task_id":task_id,"task_definition_sha256":task["definition_sha256"],
            "source_ref":{"source_id":source["source_id"],"revision_id":source["revision_id"],
                          "canonical_document_sha256":source["canonical_document_sha256"]},
            "profile_id":task["profile_id"],"knowledge_cutoff":task["knowledge_cutoff"],
            "preparation_event_hash":event["entry_hash"],
            "preparation_event_at":event["at"],
            "fixture_origin":FIXTURE,"execution_kind":PREPARATION,
            "candidate_set_digest":candidate["content_sha256"],
            "candidate_count":len(candidate["items"]),
            "source_package_at_attestation":package,
            "scientific_capture":False,"gold_qualification":"NOT_ELIGIBLE",
            "real_agent_executed":False,"new_candidates_created":False
        }
        return manifest

    @staticmethod
    def _project(record,role):
        # A manager may coordinate handoff, not inspect candidate hashes or item counts.
        safe={k:v for k,v in record.items() if k not in ("candidate_set_digest","candidate_count")}
        if role!="producer":
            safe.pop("fixture_origin",None)
        safe["candidate_payload_exposed"]=False
        safe["original_units_exposed"]=False
        return safe

    def inspect(self,role,task_id):
        self.tpa.role(role,("producer",))
        manifest=self._inspect(role,task_id)
        return {"status":"FROZEN_FIXTURE_READY_FOR_ATTESTATION",**manifest,
                "read_only_inspection":True,"attestation_written":False}

    def attest(self,role,actor,task_id,body):
        self.tpa.role(role,("producer",))
        key=body["idempotency_key"]
        if not KEY.fullmatch(key):block("INVALID_IDEMPOTENCY_KEY")
        if body["contract"]!=CONTRACT:block("INVALID_PREPARATION_CONTRACT")
        expected_event=body["expected_preparation_event_hash"]
        expected_set=body["expected_candidate_set_digest"]
        if not HEX.fullmatch(expected_event) or not HEX.fullmatch(expected_set):
            block("INVALID_PROVENANCE_DIGEST")
        inspected=self._inspect(role,task_id)
        if (inspected["preparation_event_hash"]!=expected_event or
            inspected["candidate_set_digest"]!=expected_set):
            block("AGENT_PROVENANCE_STALE")
        request_digest=digest(body|{"task_id":task_id})
        with self.tpa.lock,self.tpa.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous=db.execute("SELECT * FROM tpa_agent_preparation_replays WHERE idempotency_key=?",(key,)).fetchone()
            if previous:
                if (previous["task_id"]!=task_id or previous["actor"]!=actor or
                    previous["request_digest"]!=request_digest):
                    block("IDEMPOTENCY_CONFLICT")
                return json.loads(previous["receipt"])
            if db.execute("SELECT 1 FROM tpa_agent_preparation_attestations WHERE task_id=?",(task_id,)).fetchone():
                block("AGENT_ATTESTATION_ALREADY_FROZEN")
            record={**inspected,"attested_by":actor,"attested_at":utcnow(),"status":ATTESTED}
            record["attestation_sha256"]=digest(record)
            receipt={"attestation":self._project(record,role),"idempotent_replay":False,
                     "synthetic_only":True,"real_agent_executed":False}
            db.execute("INSERT INTO tpa_agent_preparation_attestations VALUES(?,?)",
                       (task_id,encoded(record).decode()))
            db.execute("INSERT INTO tpa_agent_preparation_replays VALUES(?,?,?,?,?)",
                       (key,task_id,actor,request_digest,encoded(receipt).decode()))
            self.tpa.event(db,task_id,actor,"SYNTHETIC_AGENT_PREPARATION_ATTESTED",{
                "attestation_sha256":record["attestation_sha256"],
                "preparation_event_hash":record["preparation_event_hash"],
                "source_document_sha256":record["source_ref"]["canonical_document_sha256"],
                "kind":PREPARATION,"scientific_capture":False})
            return receipt

    def detail(self,role,task_id):
        task=self._task(role,task_id)
        with self.tpa.connect() as db:
            row=db.execute("SELECT record FROM tpa_agent_preparation_attestations WHERE task_id=?",
                           (task_id,)).fetchone()
        if not row:
            return {"task_id":task_id,"task_state":task["state"],"status":
                    "FIXTURE_NOT_ATTESTED" if task["state"] in READY else "TASK_NOT_PREPARED",
                    "synthetic_only":True,"real_agent_executed":False,
                    "scientific_capture":False,"gold_qualification":"NOT_ELIGIBLE"}
        record=json.loads(row["record"])
        if digest({k:v for k,v in record.items() if k!="attestation_sha256"})!=record["attestation_sha256"]:
            block("AGENT_ATTESTATION_DRIFT")
        # Re-verify the exact frozen candidate and source/event truth on every read.
        current=self._inspect(role,task_id)
        if any(record.get(k)!=v for k,v in current.items()):
            block("AGENT_PROVENANCE_DRIFT")
        return {"task_id":task_id,"task_state":task["state"],"status":ATTESTED,
                "attestation":self._project(record,role),"synthetic_only":True}

    def listing(self,role,limit=25,offset=0):
        self.tpa.role(role,("producer","manager"))
        if type(limit) is not int or type(offset) is not int or not (1<=limit<=100 and 0<=offset<=100000):
            block("INVALID_PAGINATION")
        with self.tpa.connect() as db:
            total=db.execute(
                "SELECT COUNT(*) FROM tpa_tasks WHERE json_extract(record,'$.workflow_strategy')=?",(AGENT,)).fetchone()[0]
            rows=db.execute(
                "SELECT t.task_id,t.state,t.record,a.record AS attestation FROM tpa_tasks t "
                "LEFT JOIN tpa_agent_preparation_attestations a ON a.task_id=t.task_id "
                "WHERE json_extract(t.record,'$.workflow_strategy')=? "
                "ORDER BY t.task_id DESC LIMIT ? OFFSET ?",(AGENT,limit,offset)).fetchall()
        tasks=[]
        for row in rows:
            task=json.loads(row["record"])
            value={"task_id":row["task_id"],"task_state":row["state"],
                   "primary_source":task["primary_source"],
                   "preparation_status":"ATTESTED" if row["attestation"] else
                     ("FIXTURE_READY_FOR_ATTESTATION" if row["state"] in READY else "TASK_NOT_PREPARED"),
                   "execution_kind":PREPARATION,"real_agent_executed":False,
                   "scientific_capture":False,"gold_qualification":"NOT_ELIGIBLE"}
            if row["attestation"]:
                record=json.loads(row["attestation"])
                value["attestation_sha256"]=record["attestation_sha256"]
            tasks.append(value)
        return {"tasks":tasks,"total":total,"limit":limit,"offset":offset,
                "strategy":AGENT,"synthetic_only":True,
                "independent_arm_included":False,"original_units_exposed":False,
                "candidate_payload_exposed":False}
