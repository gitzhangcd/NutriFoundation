"""WB-EA-P1: synthetic-only, task-scoped, versioned scientific-annotation engine.

Never creates Gold, imports patient records, or modifies NDF/NDS decision contracts.
The upstream P0 manifest is a PROPOSED adapter, not canonical science schema.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class EAError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def deny(code: str):
    raise EAError(code)


def encoded(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def digest(value) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else encoded(value)).hexdigest()


def when(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("timezone required")
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, AttributeError):
        deny("INVALID_TIME_WITH_OFFSET_REQUIRED")


def utf16_slice(raw: str, start: int, end: int) -> str:
    b = raw.encode("utf-16-le")
    if type(start) is not int or type(end) is not int or not (0 <= start < end <= len(b) // 2):
        deny("INVALID_UTF16_RANGE")
    try:
        return b[start * 2:end * 2].decode("utf-16-le")
    except UnicodeDecodeError:
        deny("INVALID_UTF16_BOUNDARY")


class EvidenceEngine:
    def __init__(self, db_path: Path, contract_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.contract = json.loads(Path(contract_path).read_text(encoding="utf-8"))
        self.profiles = {p["source_type"]: p for p in self.contract["profiles"]}
        self.types = set(self.contract["source_types"])
        self._initialize()

    def connect(self):
        db = sqlite3.connect(str(self.db_path), timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def _initialize(self):
        with self.connect() as db:
            db.executescript("""
              CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT NOT NULL, revision_id TEXT NOT NULL,
                record TEXT NOT NULL, PRIMARY KEY(source_id,revision_id)
              );
              CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY, record TEXT NOT NULL, state TEXT NOT NULL
              );
              CREATE TABLE IF NOT EXISTS candidate_sets (
                task_id TEXT PRIMARY KEY REFERENCES tasks(task_id),
                record TEXT NOT NULL, content_sha TEXT NOT NULL
              );
              CREATE TABLE IF NOT EXISTS reviews (
                task_id TEXT PRIMARY KEY REFERENCES tasks(task_id),
                record TEXT NOT NULL, content_sha TEXT NOT NULL
              );
              CREATE TABLE IF NOT EXISTS audit (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                event TEXT NOT NULL, actor TEXT NOT NULL, detail TEXT NOT NULL,
                prev_sha TEXT NOT NULL, entry_sha TEXT NOT NULL, at TEXT NOT NULL
              );
            """)
            for tbl in ("sources", "candidate_sets", "reviews", "audit"):
                for operation in ("UPDATE", "DELETE"):
                    db.execute(f"""CREATE TRIGGER IF NOT EXISTS lock_{tbl}_{operation.lower()}
                        BEFORE {operation} ON {tbl}
                        BEGIN SELECT RAISE(ABORT,'IMMUTABLE_RECORD'); END""")

    @staticmethod
    def _role(actual: str, allowed: tuple[str, ...]):
        if actual not in allowed:
            deny("ROLE_FORBIDDEN")

    def _event(self, db, task_id: str, event: str, actor: str, detail):
        last = db.execute("SELECT entry_sha FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        prev = last["entry_sha"] if last else "GENESIS"
        now = datetime.now(timezone.utc).isoformat()
        record = {"task_id": task_id, "event": event, "actor": actor,
                  "detail": detail, "prev_sha": prev, "at": now}
        entry = digest(record)
        db.execute("""INSERT INTO audit(task_id,event,actor,detail,prev_sha,entry_sha,at)
                      VALUES(?,?,?,?,?,?,?)""",
                   (task_id, event, actor, encoded(detail).decode(), prev, entry, now))
        return entry

    def register_source(self, *, actor: str, role: str, source):
        self._role(role, ("producer",))
        fields = ("source_id", "revision_id", "source_type", "title",
                  "available_at", "fetched_at", "rights_status", "units")
        if any(k not in source for k in fields):
            deny("SOURCE_REQUIRED_FIELD_MISSING")
        if source["source_type"] not in self.types:
            deny("TYPE_UNRESOLVED_HOLD")
        if source["rights_status"] != "SYNTHETIC_FIXTURE":
            deny("SYNTHETIC_ONLY_SOURCE_RIGHTS")
        if when(source["available_at"]) > when(source["fetched_at"]):
            deny("SOURCE_TEMPORAL_CONFLICT")
        units = source["units"]
        if not isinstance(units, list) or not units:
            deny("UNITS_REQUIRED")
        unit_ids = [x.get("unit_id") for x in units if isinstance(x, dict)]
        if len(unit_ids) != len(units) or len(set(unit_ids)) != len(units):
            deny("DUPLICATE_UNIT_ID")
        for u in units:
            if not isinstance(u.get("text"), str) or not u["text"].strip():
                deny("EMPTY_SOURCE_UNIT")
        original_bytes = "\n\n".join(u["text"] for u in units).encode("utf-8")
        base = {k: source[k] for k in fields}
        base["source_family_refs"] = list(source.get("source_family_refs", []))
        base["original_sha256"] = digest(original_bytes)
        base["canonical_document_sha256"] = digest(units)
        base["artifact_kind"] = "STRUCTURED_TEXT_SYNTHETIC"
        base["scientific_capture"] = False
        base["qualified_evidence"] = False
        base["source_type_profile_id"] = self.profiles[source["source_type"]]["profile_id"]
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT record FROM sources WHERE source_id=? AND revision_id=?",
                             (base["source_id"], base["revision_id"])).fetchone()
            if old:
                if json.loads(old["record"]) != base:
                    deny("IMMUTABLE_SOURCE_VERSION_CONFLICT")
                return base
            db.execute("INSERT INTO sources VALUES(?,?,?)",
                       (base["source_id"], base["revision_id"], encoded(base).decode()))
            self._event(db, "SOURCE_REGISTRY", "SOURCE_REGISTERED", actor,
                        {"source_id": base["source_id"], "revision_id": base["revision_id"],
                         "canonical_sha256": base["canonical_document_sha256"]})
        return base

    @staticmethod
    def _source(db, sid, rev):
        row = db.execute("SELECT record FROM sources WHERE source_id=? AND revision_id=?",
                         (sid, rev)).fetchone()
        if not row:
            deny("SOURCE_VERSION_NOT_FOUND")
        return json.loads(row["record"])

    @staticmethod
    def _task(db, task_id):
        row = db.execute("SELECT record,state FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if not row:
            deny("TASK_NOT_FOUND")
        return json.loads(row["record"]), row["state"]

    @staticmethod
    def _access(task, actor: str, role: str):
        if role == "expert" and task["expert_actor"] != actor:
            deny("TASK_NOT_ASSIGNED")
        if role == "producer" and task["producer_actor"] != actor:
            deny("TASK_NOT_ASSIGNED")

    def create_task(self, *, actor: str, role: str, task):
        self._role(role, ("producer",))
        required = ("task_id", "task_kind", "profile_id", "primary_source",
                    "allowed_source_versions", "knowledge_cutoff", "workflow_strategy",
                    "expert_actor")
        if any(k not in task for k in required):
            deny("TASK_REQUIRED_FIELD_MISSING")
        if task["task_kind"] != "EVIDENCE_ECOSYSTEM_CASE":
            deny("DECISION_CASE_DELEGATE_EXISTING_NDS_ONLY")
        if task["workflow_strategy"] not in ("AGENT_PROPOSE_EXPERT_VERIFY", "HUMAN_INDEPENDENT"):
            deny("WORKFLOW_NOT_IMPLEMENTED")
        if not isinstance(task["allowed_source_versions"], list) or not task["allowed_source_versions"]:
            deny("EMPTY_TASK_SOURCE_ALLOWLIST")
        if not isinstance(task["expert_actor"], str) or not task["expert_actor"].startswith("SYN-EXPERT-"):
            deny("UNQUALIFIED_SYNTHETIC_ACTOR")
        cutoff = when(task["knowledge_cutoff"])
        primary = task["primary_source"]
        granted = set()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for grant in task["allowed_source_versions"]:
                for k in ("source_id", "revision_id", "canonical_document_sha256"):
                    if k not in grant:
                        deny("INVALID_SOURCE_GRANT")
                key = (grant["source_id"], grant["revision_id"])
                if key in granted:
                    deny("DUPLICATE_SOURCE_GRANT")
                granted.add(key)
                source = self._source(db, *key)
                if source["canonical_document_sha256"] != grant["canonical_document_sha256"]:
                    deny("SOURCE_REVISION_MISMATCH")
                if when(source["available_at"]) > cutoff:
                    deny("FUTURE_SOURCE_AT_CUTOFF")
            if not isinstance(primary, dict):
                deny("INVALID_PRIMARY_SOURCE")
            pkey = (primary.get("source_id"), primary.get("revision_id"))
            if pkey not in granted:
                deny("PRIMARY_SOURCE_NOT_ALLOWLISTED")
            doc = self._source(db, *pkey)
            if task["profile_id"] != self.profiles[doc["source_type"]]["profile_id"]:
                deny("BLOCK_PROFILE_TASK_MISMATCH")
            record = {k: task[k] for k in required}
            record["producer_actor"] = actor
            record["profile_version"] = self.contract["version"]
            record["source_type"] = doc["source_type"]
            record["scientific_capture"] = False
            record["gold_qualification"] = "NOT_ELIGIBLE"
            if db.execute("SELECT 1 FROM tasks WHERE task_id=?", (record["task_id"],)).fetchone():
                deny("TASK_ALREADY_EXISTS")
            db.execute("INSERT INTO tasks VALUES(?,?,?)",
                       (record["task_id"], encoded(record).decode(), "REGISTERED"))
            self._event(db, record["task_id"], "TASK_REGISTERED", actor,
                        {"profile_id": record["profile_id"], "allowlist": sorted(list(granted))})
        return record

    def list_sources(self, *, actor: str, role: str, task_id: str):
        self._role(role, ("expert", "producer", "auditor"))
        with self.connect() as db:
            task, state = self._task(db, task_id)
            self._access(task, actor, role)
            result = []
            for grant in task["allowed_source_versions"]:
                source = self._source(db, grant["source_id"], grant["revision_id"])
                result.append({k: v for k, v in source.items() if k != "units"})
            return {"task": task_id, "state": state, "sources": result,
                    "source_count": len(result)}

    def read_source(self, *, actor: str, role: str, task_id: str, source_id: str, revision_id: str):
        self._role(role, ("expert", "producer", "auditor"))
        with self.connect() as db:
            task, _ = self._task(db, task_id)
            self._access(task, actor, role)
            key = (source_id, revision_id)
            if key not in {(x["source_id"], x["revision_id"]) for x in task["allowed_source_versions"]}:
                deny("DENY_SOURCE_NOT_ALLOWED")
            return self._source(db, *key)

    def workpack(self, *, actor: str, role: str, task_id: str):
        self._role(role, ("expert", "producer", "auditor"))
        with self.connect() as db:
            task, state = self._task(db, task_id)
            self._access(task, actor, role)
            profile = self.profiles[task["source_type"]]
            info = {"task_id": task_id, "task_kind": task["task_kind"],
                    "source_type": task["source_type"], "profile_id": task["profile_id"],
                    "profile_version": task["profile_version"],
                    "required_groups": profile["required_groups"], "state": state,
                    "workflow": task["workflow_strategy"], "scientific_capture": False,
                    "gold_qualification": "NOT_ELIGIBLE"}
            if role == "expert" and task["workflow_strategy"] == "AGENT_PROPOSE_EXPERT_VERIFY":
                info["candidate_status"] = "AVAILABLE" if state in ("CANDIDATE_FROZEN", "EXPERT_REVIEW_FROZEN") else "NOT_VISIBLE"
            return info

    def _verify_anchor(self, db, task, anchor):
        keys = ("source_id", "revision_id", "canonical_document_sha256",
                "unit_id", "start_utf16", "end_utf16", "source_quote", "source_quote_sha256")
        if any(k not in anchor for k in keys):
            deny("ANCHOR_REQUIRED_FIELD_MISSING")
        grant = {(x["source_id"], x["revision_id"]): x for x in task["allowed_source_versions"]}
        source_key = (anchor["source_id"], anchor["revision_id"])
        if source_key not in grant:
            deny("DENY_SOURCE_NOT_ALLOWED")
        source = self._source(db, *source_key)
        if (source["canonical_document_sha256"] != anchor["canonical_document_sha256"] or
                grant[source_key]["canonical_document_sha256"] != source["canonical_document_sha256"]):
            deny("SOURCE_REVISION_MISMATCH")
        units = {u["unit_id"]: u["text"] for u in source["units"]}
        if anchor["unit_id"] not in units:
            deny("SOURCE_UNIT_NOT_FOUND")
        text = utf16_slice(units[anchor["unit_id"]], anchor["start_utf16"], anchor["end_utf16"])
        if text != anchor["source_quote"] or digest(text.encode("utf-8")) != anchor["source_quote_sha256"]:
            deny("SOURCE_SPAN_MISMATCH")
        if anchor.get("pdf_locator", {}).get("status") == "VERIFIED_UNIQUE_PDF_TEXT":
            deny("PDF_BBOX_NOT_VERIFIED_BY_THIS_RUNTIME")
        return source_key

    def freeze_candidates(self, *, actor: str, role: str, task_id: str, items):
        self._role(role, ("producer",))
        if not isinstance(items, list) or not items:
            deny("CANDIDATE_SET_EMPTY")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            task, state = self._task(db, task_id)
            self._access(task, actor, role)
            if task["workflow_strategy"] != "AGENT_PROPOSE_EXPERT_VERIFY":
                deny("INDEPENDENT_MODE_NO_AGENT")
            if state != "REGISTERED":
                deny("CANDIDATES_ALREADY_FROZEN")
            seen = set()
            permitted = set(self.profiles[task["source_type"]]["canonical_object_candidates"])
            groups = set(self.profiles[task["source_type"]]["required_groups"])
            for item in items:
                keys = ("candidate_id", "source_ref", "field_group", "candidate_payload",
                        "target_canonical_object_type", "original_anchors", "extraction_run_ref")
                if any(k not in item for k in keys):
                    deny("CANDIDATE_REQUIRED_FIELD_MISSING")
                if item["candidate_id"] in seen:
                    deny("DUPLICATE_CANDIDATE")
                seen.add(item["candidate_id"])
                if item["target_canonical_object_type"] not in permitted:
                    deny("OBJECT_TYPE_NOT_ALLOWED")
                if item["field_group"] not in groups:
                    deny("FIELD_GROUP_NOT_ALLOWED")
                if not isinstance(item["original_anchors"], list) or not item["original_anchors"]:
                    deny("BLOCK_UNVERIFIED_CANDIDATE")
                if not isinstance(item["candidate_payload"], dict) or not item["candidate_payload"]:
                    deny("CANDIDATE_PAYLOAD_EMPTY")
                if not item["extraction_run_ref"] or not isinstance(item["extraction_run_ref"], str):
                    deny("AGENT_RUN_REF_REQUIRED")
                anchored = [self._verify_anchor(db, task, anchor) for anchor in item["original_anchors"]]
                ref = item["source_ref"]
                if (ref.get("source_id"), ref.get("revision_id")) not in anchored:
                    deny("CANDIDATE_SOURCE_UNANCHORED")
            record = {"task_id": task_id, "items": items,
                      "candidate_set_frozen": True, "scientific_capture": False,
                      "gold_qualification": "NOT_ELIGIBLE",
                      "at": datetime.now(timezone.utc).isoformat()}
            record["content_sha256"] = digest(record)
            db.execute("INSERT INTO candidate_sets VALUES(?,?,?)",
                       (task_id, encoded(record).decode(), record["content_sha256"]))
            db.execute("UPDATE tasks SET state=? WHERE task_id=?", ("CANDIDATE_FROZEN", task_id))
            self._event(db, task_id, "AGENT_CANDIDATES_FROZEN", actor,
                        {"digest": record["content_sha256"], "count": len(items)})
            return record

    def read_candidates(self, *, actor: str, role: str, task_id: str):
        self._role(role, ("expert", "producer", "auditor"))
        with self.connect() as db:
            task, state = self._task(db, task_id)
            self._access(task, actor, role)
            if task["workflow_strategy"] == "HUMAN_INDEPENDENT":
                deny("DENY_INDEPENDENT_AGENT_EXPOSURE")
            if state not in ("CANDIDATE_FROZEN", "EXPERT_REVIEW_FROZEN"):
                deny("AGENT_CANDIDATES_NOT_FROZEN")
            row = db.execute("SELECT record FROM candidate_sets WHERE task_id=?", (task_id,)).fetchone()
            if not row:
                deny("AGENT_CANDIDATES_NOT_FROZEN")
            return json.loads(row["record"])

    def freeze_review(self, *, actor: str, role: str, task_id: str, items, candidate_set_digest=None):
        self._role(role, ("expert",))
        if not isinstance(items, list) or not items:
            deny("REVIEW_ITEMS_EMPTY")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            task, state = self._task(db, task_id)
            self._access(task, actor, role)
            if state not in ("REGISTERED", "CANDIDATE_FROZEN"):
                deny("REVIEW_ALREADY_FROZEN")
            workflow = task["workflow_strategy"]
            if workflow == "AGENT_PROPOSE_EXPERT_VERIFY":
                if state != "CANDIDATE_FROZEN":
                    deny("AGENT_CANDIDATES_NOT_FROZEN")
                row = db.execute("SELECT record,content_sha FROM candidate_sets WHERE task_id=?",
                                 (task_id,)).fetchone()
                if not row or row["content_sha"] != candidate_set_digest:
                    deny("CANDIDATE_DIGEST_MISMATCH")
                candidates = json.loads(row["record"])["items"]
                refs = {c["candidate_id"] for c in candidates}
                if len(items) != len(refs) or {x.get("candidate_id") for x in items} != refs:
                    deny("INCOMPLETE_EXPERT_REVIEW")
                allowed = set(self.contract["review_dispositions"])
                candidate_by_id = {c["candidate_id"]: c for c in candidates}
                source_states = set(self.contract["source_support_status"])
                for item in items:
                    if item.get("disposition") not in allowed:
                        deny("INVALID_REVIEW_DISPOSITION")
                    if item.get("source_support_status") not in source_states:
                        deny("SOURCE_SUPPORT_REVIEW_REQUIRED")
                    if item.get("field_group") != candidate_by_id[item["candidate_id"]]["field_group"]:
                        deny("REVIEW_FIELD_GROUP_MISMATCH")
                    if item["disposition"] == "ACCEPT" and item["source_support_status"] not in ("SUPPORTED", "PARTIAL"):
                        deny("UNSUPPORTED_CANDIDATE_CANNOT_BE_ACCEPTED")
                    if item["disposition"] in ("REJECT", "MODIFY") and not item.get("reason"):
                        deny("REVIEW_REASON_REQUIRED")
                    if item["disposition"] == "MODIFY" and not item.get("corrected_candidate_payload"):
                        deny("CORRECTION_REQUIRED")
                    if not isinstance(item.get("expert_anchors", []), list):
                        deny("INVALID_EXPERT_ANCHORS")
                    for anchor in item.get("expert_anchors", []):
                        self._verify_anchor(db, task, anchor)
            else:
                if candidate_set_digest is not None or state != "REGISTERED":
                    deny("DENY_INDEPENDENT_AGENT_EXPOSURE")
                for item in items:
                    if "candidate_id" in item or not item.get("statement"):
                        deny("INVALID_INDEPENDENT_JUDGMENT")
                    for anchor in item.get("original_anchors", []):
                        self._verify_anchor(db, task, anchor)
            now = datetime.now(timezone.utc).isoformat()
            record = {"task_id": task_id, "reviewer": actor,
                      "workflow": workflow, "items": items,
                      "candidate_set_digest": candidate_set_digest if workflow == "AGENT_PROPOSE_EXPERT_VERIFY" else None,
                      "scientific_capture": False, "gold_qualification": "NOT_ELIGIBLE",
                      "immutable": True, "at": now}
            record["content_sha256"] = digest(record)
            db.execute("INSERT INTO reviews VALUES(?,?,?)",
                       (task_id, encoded(record).decode(), record["content_sha256"]))
            db.execute("UPDATE tasks SET state=? WHERE task_id=?", ("EXPERT_REVIEW_FROZEN", task_id))
            self._event(db, task_id, "EXPERT_REVIEW_FROZEN", actor,
                        {"review_digest": record["content_sha256"],
                         "candidate_digest": record["candidate_set_digest"]})
            return record

    def export_record(self, *, actor: str, role: str, task_id: str):
        self._role(role, ("expert", "auditor"))
        with self.connect() as db:
            task, state = self._task(db, task_id)
            self._access(task, actor, role)
            row = db.execute("SELECT record FROM reviews WHERE task_id=?", (task_id,)).fetchone()
            if not row:
                deny("REVIEW_NOT_FROZEN")
            return {"task": task, "state": state, "review": json.loads(row["record"]),
                    "scientific_capture": False, "promotion_authorized": False,
                    "gold_qualification": "NOT_ELIGIBLE", "export_kind": "UNQUALIFIED_EXPERT_REVIEW"}

    def audit(self, *, actor: str, role: str):
        self._role(role, ("auditor",))
        with self.connect() as db:
            rows = [dict(x) for x in db.execute("SELECT * FROM audit ORDER BY seq")]
            prev = "GENESIS"
            for row in rows:
                record = {"task_id": row["task_id"], "event": row["event"],
                          "actor": row["actor"], "detail": json.loads(row["detail"]),
                          "prev_sha": row["prev_sha"], "at": row["at"]}
                if row["prev_sha"] != prev or digest(record) != row["entry_sha"]:
                    deny("AUDIT_CHAIN_BROKEN")
                prev = row["entry_sha"]
            return {"events": rows, "chain_valid": True, "audit_root_digest": prev}
