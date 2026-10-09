"""WB-TPA-P1. Synthetic-only same-origin production and assignment controller.

The existing EA engine remains the scientific annotation execution engine.
No imported real source, genuine Agent, live expert qualification or Gold promotion.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from ea_runtime import EAError, digest, encoded, when
from ea_seed import anchor


class TPAError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def block(code):
    raise TPAError(code)


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class TaskProduction:
    """Operational task state is separate from EA execution state."""
    def __init__(self, path: Path, evidence):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.evidence = evidence
        self.lock = threading.RLock()
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tpa_tasks (
                  task_id TEXT PRIMARY KEY, record TEXT NOT NULL, state TEXT NOT NULL,
                  assignment_actor TEXT, published_at TEXT);
                CREATE TABLE IF NOT EXISTS tpa_events (
                  seq INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                  actor TEXT NOT NULL, event TEXT NOT NULL, detail TEXT NOT NULL,
                  at TEXT NOT NULL, prev_hash TEXT NOT NULL, entry_hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS tpa_idempotency (
                  key TEXT PRIMARY KEY, action TEXT NOT NULL, task_id TEXT NOT NULL,
                  request_hash TEXT NOT NULL, receipt TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS tpa_batches (
                  batch_id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
                  request_hash TEXT NOT NULL, receipt TEXT NOT NULL, actor TEXT NOT NULL);
            """)
            for table in ("tpa_events", "tpa_idempotency", "tpa_batches"):
                for op in ("UPDATE", "DELETE"):
                    db.execute("CREATE TRIGGER IF NOT EXISTS tpa_{}_{}_lock "
                               "BEFORE {} ON {} BEGIN SELECT RAISE(ABORT, 'IMMUTABLE'); END"
                               .format(table, op.lower(), op, table))

    def connect(self):
        db = sqlite3.connect(str(self.path), timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        return db

    @staticmethod
    def role(role, permitted):
        if role not in permitted:
            block("ROLE_FORBIDDEN")

    def event(self, db, task_id, actor, event, detail):
        p = db.execute("SELECT entry_hash FROM tpa_events ORDER BY seq DESC LIMIT 1").fetchone()
        prev = p["entry_hash"] if p else "GENESIS"
        value = {"task_id":task_id, "actor":actor, "event":event,
                 "detail":detail, "at":utcnow(), "prev_hash":prev}
        h = digest(value)
        db.execute("INSERT INTO tpa_events(task_id,actor,event,detail,at,prev_hash,entry_hash) "
                   "VALUES(?,?,?,?,?,?,?)",
                   (task_id,actor,event,encoded(detail).decode(),value["at"],prev,h))
        return h

    @staticmethod
    def record(row):
        if row is None:
            block("TASK_NOT_FOUND")
        return json.loads(row["record"])

    def get(self, task_id):
        with self.connect() as db:
            r = db.execute("SELECT * FROM tpa_tasks WHERE task_id=?", (task_id,)).fetchone()
            if not r:
                block("TASK_NOT_FOUND")
            return {**self.record(r), "state":r["state"],
                    "assigned_expert":r["assignment_actor"],
                    "published_at":r["published_at"]}

    def sources(self, role):
        self.role(role, ("manager","producer"))
        with self.evidence.connect() as db:
            records = [json.loads(x["record"]) for x in
                       db.execute("SELECT record FROM sources ORDER BY source_id")]
        return {"sources":[{
            "source_id":x["source_id"], "revision_id":x["revision_id"],
            "title":x["title"], "source_type":x["source_type"],
            "canonical_document_sha256":x["canonical_document_sha256"],
            "available_at":x["available_at"], "rights_status":x["rights_status"],
            "profile_id":x["source_type_profile_id"], "synthetic":True
        } for x in records if x.get("rights_status")=="SYNTHETIC_FIXTURE"],
        "source_original_text_exposed":False,"real_import_enabled":False}

    def registered_source(self, source_id, revision_id):
        with self.evidence.connect() as db:
            row = db.execute("SELECT record FROM sources WHERE source_id=? AND revision_id=?",
                             (source_id,revision_id)).fetchone()
        if not row:
            block("SOURCE_NOT_REGISTERED")
        source = json.loads(row["record"])
        if source.get("rights_status")!="SYNTHETIC_FIXTURE" or not source.get("title","").startswith("[SYNTHETIC]"):
            block("SYNTHETIC_ONLY_REAL_SOURCE_DENY")
        return source

    def validate_import(self, role, body):
        self.role(role,("producer",))
        if body.get("import_kind")!="EXISTING_SYNTHETIC_SOURCE":
            block("SYNTHETIC_ONLY_REAL_SOURCE_DENY")
        source = self.registered_source(body.get("source_id"),body.get("revision_id"))
        if body.get("canonical_document_sha256") != source["canonical_document_sha256"]:
            block("SOURCE_REVISION_MISMATCH")
        return {"status":"VALID_EXISTING_SYNTHETIC_FIXTURE", "source_id":source["source_id"],
                "revision_id":source["revision_id"],"canonical_document_sha256":source["canonical_document_sha256"],
                "real_parser_imported":False,"scientific_capture":False}

    def listing(self, role, actor):
        self.role(role,("manager","producer"))
        with self.connect() as db:
            rows=db.execute("SELECT * FROM tpa_tasks ORDER BY task_id DESC").fetchall()
        data=[]
        for row in rows:
            record=self.record(row)
            data.append({
                "task_id":record["task_id"],"state":row["state"],
                "source_type":record["source_type"],"profile_id":record["profile_id"],
                "workflow_strategy":record["workflow_strategy"],
                "primary_source":record["primary_source"],
                "assigned_expert":row["assignment_actor"],
                "published_at":row["published_at"],"task_revision_id":record["task_revision_id"]
            })
        return {"tasks":data,"synthetic_only":True,"real_experts":False}

    def build_draft_record(self, actor, body):
        ident = body.get("task_id")
        if not isinstance(ident,str) or not re.fullmatch(r"TPA-SYN-[A-Z0-9-]{3,50}",ident):
            block("INVALID_TPA_SYNTHETIC_TASK_ID")
        if body.get("task_kind")!="EVIDENCE_ECOSYSTEM_CASE":
            block("NDS_SOURCE_OF_TRUTH_ONLY")
        mode=body.get("workflow_strategy")
        if mode not in ("AGENT_PROPOSE_EXPERT_VERIFY","HUMAN_INDEPENDENT"):
            block("WORKFLOW_NOT_SUPPORTED")
        primary=body.get("primary_source")
        grants=body.get("allowed_source_versions")
        if not isinstance(primary,dict) or not isinstance(grants,list) or not grants or len(grants)>7:
            block("INVALID_SOURCE_ALLOWLIST")
        cutoff=when(body.get("knowledge_cutoff"))
        available=set()
        verified=[]
        for ref in grants:
            if not isinstance(ref,dict):block("INVALID_SOURCE_GRANT")
            src=self.registered_source(ref.get("source_id"),ref.get("revision_id"))
            if ref.get("canonical_document_sha256")!=src["canonical_document_sha256"]:
                block("SOURCE_REVISION_MISMATCH")
            key=(src["source_id"],src["revision_id"])
            if key in available:block("DUPLICATE_SOURCE_GRANT")
            available.add(key)
            if when(src["available_at"])>cutoff:block("FUTURE_SOURCE_AT_CUTOFF")
            verified.append({k:src[k] for k in ("source_id","revision_id","canonical_document_sha256")})
        pkey=(primary.get("source_id"),primary.get("revision_id"))
        if pkey not in available:block("PRIMARY_NOT_ALLOWLISTED")
        source=self.registered_source(*pkey)
        pid=self.evidence.profiles[source["source_type"]]["profile_id"]
        if body.get("profile_id")!=pid:block("PROFILE_SOURCE_TYPE_MISMATCH")
        record={
            "task_id":ident,"task_revision_id":"r1","task_kind":"EVIDENCE_ECOSYSTEM_CASE",
            "primary_source":{"source_id":pkey[0],"revision_id":pkey[1]},
            "allowed_source_versions":verified,"profile_id":pid,
            "profile_version":self.evidence.contract["version"],
            "source_type":source["source_type"],"knowledge_cutoff":body["knowledge_cutoff"],
            "workflow_strategy":mode,"exposure_policy_ref":"WB-TPA-P0_v0.1",
            "protocol_version":"WB-TPA-v0.1",
            "scientific_capture":False,"gold_qualification":"NOT_ELIGIBLE",
            "created_by":actor,"created_at":utcnow()
        }
        return record

    def draft(self, role, actor, body):
        self.role(role,("producer",))
        record=self.build_draft_record(actor,body)
        ident=record["task_id"]
        with self.lock, self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM tpa_tasks WHERE task_id=?",(ident,)).fetchone():
                block("TASK_ALREADY_EXISTS")
            db.execute("INSERT INTO tpa_tasks(task_id,record,state) VALUES(?,?,?)",
                       (ident,encoded(record).decode(),"DRAFT"))
            self.event(db,ident,actor,"TASK_DRAFT_CREATED",{"definition_digest":digest(record)})
        return {"task":record,"state":"DRAFT"}

    def batch_drafts(self,role,actor,body):
        """One atomic transaction for a fully validated set of synthetic drafts."""
        self.role(role,("producer",))
        batch_id=body.get("batch_id")
        key=body.get("idempotency_key")
        items=body.get("items")
        if not isinstance(batch_id,str) or not re.fullmatch(r"TPA-BATCH-[A-Z0-9-]{3,40}",batch_id):
            block("INVALID_BATCH_ID")
        if not isinstance(key,str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{8,100}",key):
            block("INVALID_IDEMPOTENCY_KEY")
        if not isinstance(items,list) or not 1<=len(items)<=7:
            block("INVALID_BATCH_SIZE")
        request_hash=digest({"batch_id":batch_id,"items":items})
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT * FROM tpa_batches WHERE request_key=? OR batch_id=?",
                           (key,batch_id)).fetchone()
            if old:
                if old["request_hash"]!=request_hash or old["actor"]!=actor or old["request_key"]!=key:
                    block("IDEMPOTENCY_CONFLICT")
                return json.loads(old["receipt"])
            # Validate *all* records before creating even one task.
            records=[self.build_draft_record(actor,item) for item in items]
            ids=[r["task_id"] for r in records]
            if len(set(ids))!=len(ids):
                block("DUPLICATE_BATCH_TASK_ID")
            placeholders=",".join("?" for _ in ids)
            if db.execute("SELECT 1 FROM tpa_tasks WHERE task_id IN ("+placeholders+") LIMIT 1",
                          ids).fetchone():
                block("TASK_ALREADY_EXISTS")
            for record in records:
                ident=record["task_id"]
                db.execute("INSERT INTO tpa_tasks(task_id,record,state) VALUES(?,?,?)",
                           (ident,encoded(record).decode(),"DRAFT"))
                self.event(db,ident,actor,"TASK_DRAFT_CREATED",
                           {"definition_digest":digest(record),"batch_id":batch_id})
            receipt={"batch_id":batch_id,"task_ids":ids,"created_count":len(ids),
                     "state":"DRAFT","all_or_nothing":True,
                     "scientific_capture":False}
            db.execute("INSERT INTO tpa_batches VALUES(?,?,?,?,?)",
                       (batch_id,key,request_hash,encoded(receipt).decode(),actor))
            self.event(db,batch_id,actor,"BATCH_DRAFTS_FROZEN",
                       {"task_count":len(ids),"request_hash":request_hash})
            return receipt

    def batches(self,role):
        self.role(role,("manager","producer"))
        with self.connect() as db:
            rows=db.execute("SELECT receipt FROM tpa_batches ORDER BY batch_id DESC").fetchall()
        return {"batches":[json.loads(r["receipt"]) for r in rows],
                "synthetic_only":True}

    def transition(self, role, actor, task_id, action):
        self.role(role,("producer",))
        target={"validate":("DRAFT","VALIDATED"),"freeze":("VALIDATED","DEFINITION_FROZEN")}
        if action not in target:block("ACTION_NOT_SUPPORTED")
        prior,next_state=target[action]
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("SELECT * FROM tpa_tasks WHERE task_id=?",(task_id,)).fetchone()
            record=self.record(row)
            if row["state"]!=prior:
                block("INVALID_TASK_TRANSITION")
            # Recheck immutable registered sources and authoritative profile.
            for ref in record["allowed_source_versions"]:
                src=self.registered_source(ref["source_id"],ref["revision_id"])
                if src["canonical_document_sha256"]!=ref["canonical_document_sha256"]:
                    block("SOURCE_REVISION_MISMATCH")
                if when(src["available_at"])>when(record["knowledge_cutoff"]):
                    block("FUTURE_SOURCE_AT_CUTOFF")
            if record["profile_id"]!=self.evidence.profiles[record["source_type"]]["profile_id"]:
                block("PROFILE_SOURCE_TYPE_MISMATCH")
            if action=="freeze":
                record["definition_sha256"]=digest(record)
                record["definition_frozen_at"]=utcnow()
                db.execute("UPDATE tpa_tasks SET state=?, record=? WHERE task_id=?",
                           (next_state,encoded(record).decode(),task_id))
            else:
                db.execute("UPDATE tpa_tasks SET state=? WHERE task_id=?",(next_state,task_id))
            self.event(db,task_id,actor,next_state,{"definition_sha256":record.get("definition_sha256")})
            return {"task_id":task_id,"state":next_state,"definition_sha256":record.get("definition_sha256")}

    def prepare(self,role,actor,task_id):
        self.role(role,("producer",))
        with self.lock:
            row=self.get(task_id)
            if row["state"]!="DEFINITION_FROZEN":block("INVALID_TASK_TRANSITION")
            if row["created_by"]!=actor:block("PRODUCER_OWNER_MISMATCH")
            task={
                "task_id":task_id,"task_kind":"EVIDENCE_ECOSYSTEM_CASE",
                "primary_source":row["primary_source"],
                "allowed_source_versions":row["allowed_source_versions"],
                "profile_id":row["profile_id"],"knowledge_cutoff":row["knowledge_cutoff"],
                "workflow_strategy":row["workflow_strategy"],
                "expert_actor":"SYN-EA-EXPERT-A" if row["workflow_strategy"]=="AGENT_PROPOSE_EXPERT_VERIFY"
                               else "SYN-EA-EXPERT-B"
            }
            # EA registration is private while TPA delivery gate is closed.
            try:
                self.evidence.create_task(actor=actor,role="producer",task=task)
            except EAError as e:
                if e.code!="TASK_ALREADY_EXISTS":raise
                with self.evidence.connect() as db:
                    existing=json.loads(db.execute("SELECT record FROM tasks WHERE task_id=?",
                                                   (task_id,)).fetchone()["record"])
                if any(existing.get(k)!=task[k] for k in task):
                    block("EA_TASK_PREPARATION_CONFLICT")
            candidate_digest=None
            if row["workflow_strategy"]=="AGENT_PROPOSE_EXPERT_VERIFY":
                source=self.registered_source(row["primary_source"]["source_id"],row["primary_source"]["revision_id"])
                profile=self.evidence.profiles[source["source_type"]]
                candidate={
                    "candidate_id":"FIXTURE-"+task_id,
                    "source_ref":{"source_id":source["source_id"],"revision_id":source["revision_id"]},
                    "field_group":next(x for x in profile["required_groups"] if x!="source_spans"),
                    "target_canonical_object_type":profile["canonical_object_candidates"][0],
                    "candidate_payload":{"training_note":"SYNTHETIC fixture; not model output or clinical evidence."},
                    "original_anchors":[anchor(source,"u2")],
                    "extraction_run_ref":"SYN-FIXTURE-NOT-AN-LLM"
                }
                try:
                    result=self.evidence.freeze_candidates(actor=actor,role="producer",
                                                           task_id=task_id,items=[candidate])
                except EAError as e:
                    if e.code!="CANDIDATES_ALREADY_FROZEN":raise
                    result=self.evidence.read_candidates(actor=actor,role="producer",task_id=task_id)
                    if result["items"]!=[candidate]:block("EA_CANDIDATE_PREPARATION_CONFLICT")
                candidate_digest=result["content_sha256"]
            receipt={"preparation_kind":"SYNTHETIC_FIXTURE_NOT_AN_LLM",
                     "candidate_set_digest":candidate_digest,
                     "strategy":row["workflow_strategy"],"prepared_at":utcnow()}
            with self.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                changed=db.execute("UPDATE tpa_tasks SET state=? WHERE task_id=? AND state=?",
                                   ("READY_FOR_ASSIGNMENT",task_id,"DEFINITION_FROZEN"))
                if changed.rowcount!=1:block("INVALID_TASK_TRANSITION")
                self.event(db,task_id,actor,"PREPARATION_FROZEN",receipt)
            return {"task_id":task_id,"state":"READY_FOR_ASSIGNMENT",**receipt}

    def assign(self,role,actor,task_id,body):
        self.role(role,("manager",))
        who=body.get("expert_actor")
        key=body.get("idempotency_key")
        if not isinstance(key,str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{8,100}",key):
            block("INVALID_IDEMPOTENCY_KEY")
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT * FROM tpa_idempotency WHERE key=?",(key,)).fetchone()
            request_hash=digest({"expert_actor":who,"task_id":task_id})
            if old:
                if old["action"]!="ASSIGN" or old["task_id"]!=task_id or old["request_hash"]!=request_hash:
                    block("IDEMPOTENCY_CONFLICT")
                return json.loads(old["receipt"])
            row=db.execute("SELECT * FROM tpa_tasks WHERE task_id=?",(task_id,)).fetchone()
            record=self.record(row)
            if row["state"]!="READY_FOR_ASSIGNMENT":block("INVALID_TASK_TRANSITION")
            allowed="SYN-EA-EXPERT-A" if record["workflow_strategy"]=="AGENT_PROPOSE_EXPERT_VERIFY" else "SYN-EA-EXPERT-B"
            if who!=allowed:block("CROSS_ARM_PRIOR_EXPOSURE")
            # Exactly provisioned, separated engineering actors, NOT real qualification.
            receipt={"task_id":task_id,"state":"ASSIGNED","assigned_expert":who,
                     "assignment_revision_id":"r1","synthetic_identity_only":True}
            db.execute("UPDATE tpa_tasks SET state=?,assignment_actor=? WHERE task_id=?",
                       ("ASSIGNED",who,task_id))
            self.event(db,task_id,actor,"EXPERT_ASSIGNED",receipt)
            db.execute("INSERT INTO tpa_idempotency VALUES(?,?,?,?,?)",
                       (key,"ASSIGN",task_id,request_hash,encoded(receipt).decode()))
            return receipt

    def publish(self,role,actor,task_id,body):
        self.role(role,("manager",))
        key=body.get("idempotency_key")
        if not isinstance(key,str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{8,100}",key):
            block("INVALID_IDEMPOTENCY_KEY")
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT * FROM tpa_idempotency WHERE key=?",(key,)).fetchone()
            request_hash=digest({"task_id":task_id,"action":"PUBLISH"})
            if old:
                if old["action"]!="PUBLISH" or old["task_id"]!=task_id or old["request_hash"]!=request_hash:
                    block("IDEMPOTENCY_CONFLICT")
                return json.loads(old["receipt"])
            row=db.execute("SELECT * FROM tpa_tasks WHERE task_id=?",(task_id,)).fetchone()
            record=self.record(row)
            if row["state"]!="ASSIGNED":block("INVALID_TASK_TRANSITION")
            if record["workflow_strategy"]=="AGENT_PROPOSE_EXPERT_VERIFY":
                candidate=self.evidence.read_candidates(actor=record["created_by"],role="producer",task_id=task_id)
                if not candidate.get("candidate_set_frozen"):block("CANDIDATES_NOT_FROZEN")
            else:
                with self.evidence.connect() as e:
                    if e.execute("SELECT 1 FROM candidate_sets WHERE task_id=?",(task_id,)).fetchone():
                        block("DENY_INDEPENDENT_AGENT_EXPOSURE")
            now=utcnow()
            receipt={"task_id":task_id,"state":"PUBLISHED","expert_actor":row["assignment_actor"],
                     "available_at":now,"scientific_capture":False,"gold_qualification":"NOT_ELIGIBLE"}
            db.execute("UPDATE tpa_tasks SET state=?,published_at=? WHERE task_id=?",
                       ("PUBLISHED",now,task_id))
            self.event(db,task_id,actor,"TASK_PUBLISHED",receipt)
            self.event(db,task_id,actor,"GRANT_ISSUED",{"expert_actor":row["assignment_actor"],"scope":"TASK_AUTHORIZED_ONLY"})
            db.execute("INSERT INTO tpa_idempotency VALUES(?,?,?,?,?)",
                       (key,"PUBLISH",task_id,request_hash,encoded(receipt).decode()))
            return receipt

    def revoke(self,role,actor,task_id):
        """Revocation denies future deliveries, never erases already served material."""
        self.role(role,("manager",))
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("SELECT * FROM tpa_tasks WHERE task_id=?",(task_id,)).fetchone()
            self.record(row)
            if row["state"] not in ("ASSIGNED","PUBLISHED"):
                block("INVALID_TASK_TRANSITION")
            previous=row["state"]
            db.execute("UPDATE tpa_tasks SET state='REVOKED' WHERE task_id=?",(task_id,))
            detail={"task_id":task_id,"state":"REVOKED","prior_state":previous,
                    "assigned_expert":row["assignment_actor"],
                    "historical_exposure_remains":True,
                    "revoked_at":utcnow()}
            self.event(db,task_id,actor,"ACCESS_REVOKED",detail)
            return detail

    def expert_gate(self,task_id, actor, role, exposure_event=None, source_ref=None):
        """Called from EA source/workpack/candidate endpoints before data is returned."""
        if not task_id.startswith("TPA-SYN-"):
            return True
        if role=="producer":
            return True  # original EA producer ownership and source ACL still apply
        if role!="expert":block("ROLE_FORBIDDEN")
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row=db.execute("SELECT state,assignment_actor,record FROM tpa_tasks WHERE task_id=?",
                           (task_id,)).fetchone()
            if not row or row["state"]!="PUBLISHED" or row["assignment_actor"]!=actor:
                block("TASK_NOT_DELIVERED_OR_ASSIGNED")
            if exposure_event:
                detail={"authorized":True,"scope":"TASK_AUTHORIZED_ONLY"}
                if source_ref:
                    with self.evidence.connect() as source_db:
                        src=source_db.execute("SELECT record FROM sources WHERE source_id=? AND revision_id=?",source_ref).fetchone()
                    if not src:
                        block("SOURCE_NOT_REGISTERED")
                    content=json.loads(src["record"])
                    task=self.record(row)
                    if not any(x["source_id"]==source_ref[0] and x["revision_id"]==source_ref[1]
                               for x in task["allowed_source_versions"]):
                        block("SOURCE_NOT_ALLOWLISTED")
                    detail.update({"source_id":source_ref[0],"revision_id":source_ref[1],
                                   "content_digest":content["canonical_document_sha256"]})
                self.event(db,task_id,actor,exposure_event,detail)
        return True

    def audit(self,role):
        self.role(role,("auditor",))
        with self.connect() as db:
            events=[dict(r) for r in db.execute("SELECT * FROM tpa_events ORDER BY seq")]
        prev="GENESIS"
        for x in events:
            if x["prev_hash"]!=prev:
                return {"valid":False,"events":len(events)}
            record={"task_id":x["task_id"],"actor":x["actor"],"event":x["event"],
                    "detail":json.loads(x["detail"]),"at":x["at"],"prev_hash":x["prev_hash"]}
            if digest(record)!=x["entry_hash"]:
                return {"valid":False,"events":len(events)}
            prev=x["entry_hash"]
        return {"valid":True,"events":len(events),"recent_events":[
            {"task_id":x["task_id"],"event":x["event"],"actor":x["actor"],"at":x["at"]}
            for x in events[-20:]]}
