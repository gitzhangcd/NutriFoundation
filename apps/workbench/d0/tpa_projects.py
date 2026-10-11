"""P1.1-A2 additive *synthetic-only* Project/Batch operational organization.

Project/Batch membership is not a scientific protocol, data grant, or Gold authority.
All writes share TaskProduction's exact SQLite transaction and immutable audit chain.
"""
from __future__ import annotations

import json
import re

from ea_runtime import digest, encoded
from tpa_runtime import TPAError, block, utcnow

PROJECT_ID = re.compile(r"PRJ-SYN-[A-Z0-9-]{3,40}\Z")
BATCH_ID = re.compile(r"BATCH-SYN-[A-Z0-9-]{3,40}\Z")
KEY = re.compile(r"[A-Za-z0-9_.:-]{8,100}\Z")
DANGEROUS_TEXT = re.compile(r"[<>]|(?:https?://|www\.|@|\bsk-[A-Za-z0-9]|\b(?:\d[ -]?){10,}\b)", re.I)
ALLOWED_STATES = frozenset({"DRAFT", "VALIDATED", "DEFINITION_FROZEN", "READY_FOR_ASSIGNMENT", "ASSIGNED", "PUBLISHED", "REVOKED"})


class TPAProjects:
    def __init__(self, tpa):
        self.tpa = tpa
        with tpa.lock, tpa.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tpa_project_registry(
                  project_id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
                  owner_actor TEXT NOT NULL, created_at TEXT NOT NULL, lifecycle TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tpa_operational_batches(
                  batch_id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
                  label TEXT NOT NULL, purpose TEXT NOT NULL,
                  created_by TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tpa_task_placement(
                  task_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, batch_id TEXT NOT NULL,
                  task_revision_id TEXT NOT NULL, definition_digest TEXT NOT NULL,
                  placed_by TEXT NOT NULL, placed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tpa_ops_idempotency(
                  key TEXT PRIMARY KEY, action TEXT NOT NULL, actor TEXT NOT NULL,
                  request_digest TEXT NOT NULL, receipt TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS tpa_ops_batch_index ON tpa_operational_batches(project_id);
                CREATE INDEX IF NOT EXISTS tpa_ops_placement_index ON tpa_task_placement(batch_id);
            """)
            for table in ("tpa_project_registry", "tpa_operational_batches", "tpa_task_placement", "tpa_ops_idempotency"):
                for operation in ("UPDATE", "DELETE"):
                    db.execute("CREATE TRIGGER IF NOT EXISTS tpa_ops_{}_{}_immutable "
                               "BEFORE {} ON {} BEGIN SELECT RAISE(ABORT, 'IMMUTABLE'); END".format(
                                   table, operation.lower(), operation, table))

    @staticmethod
    def access(role, write=False):
        if role not in (("producer",) if write else ("producer", "manager")):
            block("ROLE_FORBIDDEN")

    @staticmethod
    def ident(value, pattern, code):
        if not isinstance(value, str) or not pattern.fullmatch(value):
            block(code)
        return value

    @staticmethod
    def safe_text(value, lo, hi):
        if not isinstance(value, str) or not lo <= len(value.strip()) <= hi or DANGEROUS_TEXT.search(value):
            block("INVALID_SYNTHETIC_METADATA")
        if any(ord(c) < 32 for c in value):
            block("INVALID_SYNTHETIC_METADATA")
        return value.strip()

    @staticmethod
    def key(value):
        if not isinstance(value, str) or not KEY.fullmatch(value):
            block("INVALID_IDEMPOTENCY_KEY")
        return value

    def replay(self, db, key, actor, action, req):
        row = db.execute("SELECT * FROM tpa_ops_idempotency WHERE key=?", (key,)).fetchone()
        if row is None:
            return None
        if row["actor"] != actor or row["action"] != action or row["request_digest"] != digest(req):
            block("IDEMPOTENCY_CONFLICT")
        return json.loads(row["receipt"])

    @staticmethod
    def save_replay(db, key, actor, action, req, receipt):
        db.execute("INSERT INTO tpa_ops_idempotency VALUES(?,?,?,?,?)",
                   (key, action, actor, digest(req), encoded(receipt).decode()))

    @staticmethod
    def ensure_project(db, project_id):
        row = db.execute("SELECT * FROM tpa_project_registry WHERE project_id=?", (project_id,)).fetchone()
        if row is None:
            block("PROJECT_NOT_FOUND")
        if row["lifecycle"] != "ACTIVE":
            block("PROJECT_NOT_ACTIVE")
        return row

    @classmethod
    def ensure_batch(cls, db, project_id, batch_id):
        cls.ensure_project(db, project_id)
        row = db.execute("SELECT * FROM tpa_operational_batches WHERE batch_id=?", (batch_id,)).fetchone()
        if row is None or row["project_id"] != project_id:
            block("BATCH_NOT_FOUND_OR_SCOPE_MISMATCH")
        return row

    def create_project(self, role, actor, body):
        self.access(role, True)
        ident = self.ident(body.get("project_id"), PROJECT_ID, "INVALID_PROJECT_ID")
        name = self.safe_text(body.get("name"), 2, 100)
        desc = self.safe_text(body.get("description", ""), 0, 500)
        key = self.key(body.get("idempotency_key"))
        req = {"project_id": ident, "name": name, "description": desc}
        with self.tpa.lock, self.tpa.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = self.replay(db, key, actor, "CREATE_PROJECT", req)
            if old is not None:
                return old
            if db.execute("SELECT 1 FROM tpa_project_registry WHERE project_id=?", (ident,)).fetchone():
                block("PROJECT_ALREADY_EXISTS")
            now = utcnow()
            receipt = {**req, "owner_actor": actor, "created_at": now, "lifecycle": "ACTIVE", "synthetic_only": True}
            db.execute("INSERT INTO tpa_project_registry VALUES(?,?,?,?,?,?)",
                       (ident, name, desc, actor, now, "ACTIVE"))
            self.tpa.event(db, ident, actor, "OPERATIONAL_PROJECT_CREATED", {"project_id": ident})
            self.save_replay(db, key, actor, "CREATE_PROJECT", req, receipt)
            return receipt

    def create_batch(self, role, actor, project_id, body):
        self.access(role, True)
        project_id = self.ident(project_id, PROJECT_ID, "INVALID_PROJECT_ID")
        ident = self.ident(body.get("batch_id"), BATCH_ID, "INVALID_BATCH_ID")
        label = self.safe_text(body.get("label"), 2, 100)
        purpose = self.safe_text(body.get("purpose", ""), 0, 500)
        key = self.key(body.get("idempotency_key"))
        req = {"project_id": project_id, "batch_id": ident, "label": label, "purpose": purpose}
        with self.tpa.lock, self.tpa.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = self.replay(db, key, actor, "CREATE_BATCH", req)
            if old is not None:
                return old
            self.ensure_project(db, project_id)
            if db.execute("SELECT 1 FROM tpa_operational_batches WHERE batch_id=?", (ident,)).fetchone():
                block("BATCH_ALREADY_EXISTS")
            now = utcnow()
            receipt = {**req, "created_by": actor, "created_at": now, "synthetic_only": True}
            db.execute("INSERT INTO tpa_operational_batches VALUES(?,?,?,?,?,?)",
                       (ident, project_id, label, purpose, actor, now))
            self.tpa.event(db, ident, actor, "OPERATIONAL_BATCH_CREATED", {"project_id": project_id, "batch_id": ident})
            self.save_replay(db, key, actor, "CREATE_BATCH", req, receipt)
            return receipt

    def create_task_in_batch(self, role, actor, body):
        self.access(role, True)
        project_id = self.ident(body.get("project_id"), PROJECT_ID, "INVALID_PROJECT_ID")
        batch_id = self.ident(body.get("batch_id"), BATCH_ID, "INVALID_BATCH_ID")
        key = self.key(body.get("idempotency_key"))
        draft = {k: v for k, v in body.items() if k not in ("project_id", "batch_id", "idempotency_key")}
        req = {"project_id": project_id, "batch_id": batch_id, "draft": draft}
        with self.tpa.lock, self.tpa.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = self.replay(db, key, actor, "CREATE_TASK_IN_BATCH", req)
            if old is not None:
                return old
            self.ensure_batch(db, project_id, batch_id)
            record = self.tpa.build_draft_record(actor, draft)  # same source/profile/cutoff/Strict-Blind guards
            task_id = record["task_id"]
            if db.execute("SELECT 1 FROM tpa_tasks WHERE task_id=?", (task_id,)).fetchone():
                block("TASK_ALREADY_EXISTS")
            db.execute("INSERT INTO tpa_tasks(task_id,record,state) VALUES(?,?,?)",
                       (task_id, encoded(record).decode(), "DRAFT"))
            stamp = utcnow()
            definition_digest = digest(record)
            db.execute("INSERT INTO tpa_task_placement VALUES(?,?,?,?,?,?,?)",
                       (task_id, project_id, batch_id, record["task_revision_id"], definition_digest, actor, stamp))
            self.tpa.event(db, task_id, actor, "TASK_DRAFT_CREATED", {"definition_digest": definition_digest})
            self.tpa.event(db, task_id, actor, "OPERATIONAL_TASK_PLACED",
                           {"project_id": project_id, "batch_id": batch_id, "task_revision_id": record["task_revision_id"]})
            receipt = {"task": record, "state": "DRAFT", "placement": {"project_id": project_id,
                       "batch_id": batch_id, "task_id": task_id, "task_revision_id": record["task_revision_id"]}}
            self.save_replay(db, key, actor, "CREATE_TASK_IN_BATCH", req, receipt)
            return receipt

    def list_projects(self, role, limit=50, offset=0):
        self.access(role)
        limit, offset = self.page(limit, offset)
        with self.tpa.connect() as db:
            total = db.execute("SELECT COUNT(*) FROM tpa_project_registry").fetchone()[0]
            rows = db.execute("""SELECT p.*, COUNT(DISTINCT b.batch_id) AS batch_count,
                COUNT(DISTINCT x.task_id) AS task_count
                FROM tpa_project_registry p
                LEFT JOIN tpa_operational_batches b ON b.project_id=p.project_id
                LEFT JOIN tpa_task_placement x ON x.batch_id=b.batch_id
                GROUP BY p.project_id ORDER BY p.created_at DESC, p.project_id LIMIT ? OFFSET ?""",
                (limit, offset)).fetchall()
        return {"projects": [dict(x) for x in rows], "total": total, "limit": limit, "offset": offset, "synthetic_only": True}

    @staticmethod
    def page(limit, offset):
        if not isinstance(limit, int) or not 1 <= limit <= 100 or not isinstance(offset, int) or not 0 <= offset <= 100000:
            block("INVALID_PAGINATION")
        return limit, offset

    def project(self, role, project_id):
        self.access(role)
        with self.tpa.connect() as db:
            row = self.ensure_project(db, project_id)
        return {**dict(row), "synthetic_only": True}

    def batches(self, role, project_id):
        self.access(role)
        with self.tpa.connect() as db:
            self.ensure_project(db, project_id)
            rows = db.execute("""SELECT b.*, COUNT(x.task_id) AS task_count
              FROM tpa_operational_batches b
              LEFT JOIN tpa_task_placement x ON x.batch_id=b.batch_id
              WHERE b.project_id=? GROUP BY b.batch_id ORDER BY b.created_at DESC, b.batch_id""",
              (project_id,)).fetchall()
        return {"batches": [dict(x) for x in rows], "synthetic_only": True}

    def batch(self, role, project_id, batch_id):
        self.access(role)
        with self.tpa.connect() as db:
            row = self.ensure_batch(db, project_id, batch_id)
            n = db.execute("SELECT COUNT(*) FROM tpa_task_placement WHERE batch_id=?", (batch_id,)).fetchone()[0]
        return {**dict(row), "task_count": n, "synthetic_only": True}

    @staticmethod
    def scope(db, project_id, batch_id):
        if batch_id and not project_id:
            block("PROJECT_SCOPE_REQUIRED_FOR_BATCH")
        if project_id:
            TPAProjects.ensure_project(db, project_id)
        if batch_id:
            TPAProjects.ensure_batch(db, project_id, batch_id)

    @staticmethod
    def where(project_id, batch_id, state=None, q=None):
        cond, args = [], []
        if project_id:
            cond.append("x.project_id=?")
            args.append(project_id)
        if batch_id:
            cond.append("x.batch_id=?")
            args.append(batch_id)
        if q is not None:
            if not isinstance(q, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,60}", q):
                block("INVALID_TASK_QUERY")
            cond.append("t.task_id LIKE ?")
            args.append("%" + q.upper() + "%")
        if state:
            if state == "LEGACY":
                cond.append("x.task_id IS NULL")
            elif state == "PREPARING":
                cond.append("t.state IN ('DRAFT','VALIDATED','DEFINITION_FROZEN')")
            elif state in ALLOWED_STATES:
                cond.append("t.state=?")
                args.append(state)
            else:
                block("INVALID_STATE_FILTER")
        return (" WHERE " + " AND ".join(cond)) if cond else "", args

    def list_tasks(self, role, project_id=None, batch_id=None, state=None, q=None, limit=50, offset=0):
        self.access(role)
        limit, offset = self.page(limit, offset)
        with self.tpa.connect() as db:
            self.scope(db, project_id, batch_id)
            predicate, args = self.where(project_id, batch_id, state, q)
            base = " FROM tpa_tasks t LEFT JOIN tpa_task_placement x ON x.task_id=t.task_id " + predicate
            total = db.execute("SELECT COUNT(*)" + base, args).fetchone()[0]
            rows = db.execute("SELECT t.*,x.project_id,x.batch_id" + base +
                              " ORDER BY t.task_id DESC LIMIT ? OFFSET ?", [*args, limit, offset]).fetchall()
        data = []
        for row in rows:
            task = json.loads(row["record"])
            data.append({"task_id": task["task_id"], "task_revision_id": task["task_revision_id"],
                         "state": row["state"], "source_type": task["source_type"],
                         "profile_id": task["profile_id"], "primary_source": task["primary_source"],
                         "workflow_strategy": task["workflow_strategy"],
                         "assigned_expert": row["assignment_actor"], "published_at": row["published_at"],
                         "project_id": row["project_id"], "batch_id": row["batch_id"],
                         "legacy": row["project_id"] is None})
        return {"tasks": data, "total": total, "limit": limit, "offset": offset,
                "synthetic_only": True, "real_experts": False}

    def detail(self, role, task_id):
        self.access(role)
        row = self.tpa.get(task_id)
        with self.tpa.connect() as db:
            p = db.execute("SELECT * FROM tpa_task_placement WHERE task_id=?", (task_id,)).fetchone()
        safe = {k: row[k] for k in ("task_id", "task_revision_id", "state", "source_type", "profile_id",
                                     "primary_source", "allowed_source_versions", "knowledge_cutoff",
                                     "workflow_strategy", "assigned_expert", "published_at")}
        safe["placement"] = {"project_id": p["project_id"], "batch_id": p["batch_id"]} if p else None
        safe["legacy"] = p is None
        safe["next_action"] = ({"DRAFT": "validate", "VALIDATED": "freeze",
                                "DEFINITION_FROZEN": "prepare", "READY_FOR_ASSIGNMENT": "assign",
                                "ASSIGNED": "publish"}).get(row["state"])
        safe["scientific_capture"] = False
        safe["gold_qualification"] = "NOT_ELIGIBLE"
        return safe

    def overview(self, role, project_id=None, batch_id=None):
        self.access(role)
        with self.tpa.connect() as db:
            self.scope(db, project_id, batch_id)
            predicate, args = self.where(project_id, batch_id)
            rows = db.execute("""SELECT t.state, COUNT(*) AS count FROM tpa_tasks t
                LEFT JOIN tpa_task_placement x ON x.task_id=t.task_id""" + predicate +
                " GROUP BY t.state", args).fetchall()
            legacy = db.execute("SELECT COUNT(*) FROM tpa_tasks t LEFT JOIN tpa_task_placement x ON x.task_id=t.task_id WHERE x.task_id IS NULL").fetchone()[0]
        by_state = {r["state"]: r["count"] for r in rows}
        counts = {"preparing": sum(by_state.get(s, 0) for s in ("DRAFT", "VALIDATED", "DEFINITION_FROZEN")),
                  "ready": by_state.get("READY_FOR_ASSIGNMENT", 0), "assigned": by_state.get("ASSIGNED", 0),
                  "published": by_state.get("PUBLISHED", 0), "revoked": by_state.get("REVOKED", 0),
                  "total": sum(by_state.values()), "legacy": legacy if not project_id else 0,
                  "blocked": None}
        return {"counts": counts, "states": by_state, "scope": {"project_id": project_id,
                "batch_id": batch_id}, "synthetic_only": True,
                "opened_is_not_read": True, "gold_qualification": "NOT_ELIGIBLE"}