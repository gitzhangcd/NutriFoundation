from __future__ import annotations

import json
import subprocess

from .models import ExtractionTask, ParsedDocument, PrefillDraft, RawSnapshot, digest
from .store import ProductionStore
from .verification import verify_draft


class PrefillService:
    def __init__(self, store: ProductionStore):
        self.store = store

    def prepare(self, snapshot: RawSnapshot, parsed: ParsedDocument, *, authority_sha256: str,
                extractor_id: str, model_version: str, prompt_version: str,
                coverage_request: str, budget_tokens: int = 16000) -> ExtractionTask:
        if snapshot.lane != "scientific" or snapshot.content_scope not in {"fulltext","abstract"}:
            raise ValueError("Scientific extraction requires a scientific source; observation/grounding/experiment are separate")
        if snapshot.snapshot_id != parsed.snapshot_id:
            raise ValueError("Parser snapshot mismatch")
        # Validate against records owned by the store, never trust caller copies.
        if self.store.get("snapshot",snapshot.snapshot_id) != snapshot.model_dump(mode="json"):
            raise ValueError("Snapshot differs from persisted record")
        if self.store.get("parsed",parsed.parsed_id) != parsed.model_dump(mode="json"):
            raise ValueError("Parsed document differs from persisted record")
        body = dict(snapshot_id=snapshot.snapshot_id,snapshot_sha256=snapshot.content_sha256,
            parsed_id=parsed.parsed_id,parsed_sha256=digest(parsed),authority_sha256=authority_sha256,
            extractor_id=extractor_id,model_version=model_version,prompt_version=prompt_version,
            coverage_request=coverage_request,budget_tokens=budget_tokens)
        task = ExtractionTask(task_id="TASK-"+digest(body),**body)
        with self.store.transaction() as con:
            self.store.put("task",task.task_id,task,con=con)
            self.store.depend(task.task_id,(snapshot.snapshot_id,parsed.parsed_id),con=con)
        return task

    def ingest(self, draft: PrefillDraft):
        task = ExtractionTask.model_validate(self.store.get("task",draft.task.task_id))
        if task != draft.task:
            raise ValueError("Task differs from persisted contract")
        if not self.store.active(task.task_id):
            raise ValueError("Task invalidated")
        parsed = ParsedDocument.model_validate(self.store.get("parsed",task.parsed_id))
        from pathlib import Path
        import hashlib
        snapshot = RawSnapshot.model_validate(self.store.get("snapshot",task.snapshot_id))
        if snapshot.content_sha256 != task.snapshot_sha256:
            raise ValueError("Snapshot task binding mismatch")
        data = Path(snapshot.blob_path).read_bytes()
        if hashlib.sha256(data).hexdigest()!=snapshot.content_sha256 or len(data)!=snapshot.byte_count:
            raise ValueError("Raw snapshot integrity failure")
        report = verify_draft(draft,parsed)
        with self.store.transaction() as con:
            self.store.put("draft",draft.draft_id,draft,con=con)
            self.store.put("verification",report.report_id,report,con=con)
            self.store.depend(draft.draft_id,(task.task_id,),con=con)
            self.store.depend(report.report_id,(draft.draft_id,),con=con)
            # First accepted response is a replay cache, never a scientific truth.
            row = con.execute("SELECT 1 FROM d0_record WHERE kind='task_result' AND id=?",(task.task_id,)).fetchone()
            if not row:
                self.store.put("task_result",task.task_id,{"draft_id":draft.draft_id,"draft_sha256":digest(draft)},con=con)
        return report

    def run_command(self, task_id: str, command: list[str], *, timeout: int = 120) -> PrefillDraft:
        if not command:
            raise ValueError("Worker command required")
        task = ExtractionTask.model_validate(self.store.get("task",task_id))
        parsed = self.store.get("parsed",task.parsed_id)
        if not self.store.active(task_id):
            raise ValueError("Task invalidated")
        with self.store.transaction() as con:
            cached = con.execute("SELECT payload FROM d0_record WHERE kind='task_result' AND id=?",(task_id,)).fetchone()
        if cached:
            ref = json.loads(cached[0])
            draft = PrefillDraft.model_validate(self.store.get("draft",ref["draft_id"]))
            if digest(draft)!=ref["draft_sha256"]:
                raise ValueError("Cached draft hash mismatch")
            self.ingest(draft)
            return draft
        request = {"task":task.model_dump(mode="json"),"task_sha256":digest(task),
            "parsed_document":parsed,"response_schema":PrefillDraft.model_json_schema(),
            "rules":["Return multiple result candidates; do not promote or create Gold.",
                     "Preserve conflicts and unknown fields; bind model/outcome/unit/footnotes.",
                     "budget_tokens is an adapter request; enforce vendor limits in the worker."]}
        result = subprocess.run(command,input=json.dumps(request,ensure_ascii=False),
            capture_output=True,text=True,check=True,timeout=timeout)
        if len(result.stdout.encode()) > 8*1024*1024:
            raise ValueError("Worker response exceeds byte limit")
        draft = PrefillDraft.model_validate_json(result.stdout)
        if draft.task.task_id != task_id:
            raise ValueError("Worker returned another task")
        self.ingest(draft)
        return draft
