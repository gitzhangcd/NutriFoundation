from __future__ import annotations

from .models import ParsedDocument, PrefillDraft, ReviewDecision, digest
from .store import ProductionStore


class ReviewService:
    def __init__(self, store: ProductionStore):
        self.store = store

    def create(self, draft_id: str, *, reviewer_id: str, mode: str) -> dict:
        if mode not in {"assisted","source_only"}:
            raise ValueError("Unsupported review mode")
        draft = PrefillDraft.model_validate(self.store.get("draft",draft_id))
        snapshot = self.store.get("snapshot",draft.task.snapshot_id)
        payload = dict(draft_id=draft_id,draft_sha256=digest(draft),snapshot_id=draft.task.snapshot_id,
            reviewer_id=reviewer_id,mode=mode,snapshot_sha256=snapshot["content_sha256"])
        task = {"review_task_id":"REVIEW-"+digest(payload),**payload}
        with self.store.transaction() as con:
            self.store.put("review_task",task["review_task_id"],task,con=con)
            self.store.depend(task["review_task_id"],(draft_id,),con=con)
        return task

    def export(self, review_task_id: str) -> dict:
        task = self.store.get("review_task",review_task_id)
        # A server-side projection: source-only clients never receive candidates.
        snapshot = self.store.get("snapshot",task["snapshot_id"])
        out = {"review_task_id":task["review_task_id"],"mode":task["mode"],
            "reviewer_id":task["reviewer_id"],"draft_sha256":task["draft_sha256"],
            "source":{k:v for k,v in snapshot.items() if k!='blob_path'},"blank_fields":["study","population","exposure","comparator",
                "outcome","time","estimand","analysis_population","model","effect","unit","reference","notes"],
            "reviewer_qualification":"NOT_VERIFIED_BY_THIS_EXPORT"}
        if task["mode"]=="assisted":
            draft = PrefillDraft.model_validate(self.store.get("draft",task["draft_id"]))
            parsed = ParsedDocument.model_validate(self.store.get("parsed",draft.task.parsed_id))
            from .verification import verify_draft
            out["prefill"] = draft.model_dump(mode="json")
            out["anchors"] = [a.model_dump(mode="json") for a in parsed.anchors]
            out["checks"] = verify_draft(draft,parsed).model_dump(mode="json")
        return out

    def submit(self, decision: ReviewDecision):
        task = self.store.get("review_task",decision.review_task_id)
        if (task["draft_sha256"]!=decision.draft_sha256 or task["mode"]!=decision.mode
            or task["reviewer_id"]!=decision.reviewer_id):
            raise ValueError("Review decision identity/version/mode mismatch")
        if not self.store.active(decision.review_task_id):
            raise ValueError("Review task invalidated")
        draft = PrefillDraft.model_validate(self.store.get("draft",task["draft_id"]))
        paths = {r.result_id+"/"+f for r in draft.results for f in r.fields}
        if not set(decision.patches).issubset(paths):
            raise ValueError("Patch addresses unknown result field")
        with self.store.transaction() as con:
            # One locked submission per review task. Revisions require a new task.
            self.store.put("review_submission",decision.review_task_id,decision,con=con)
            self.store.put("review_decision",decision.decision_id,decision,con=con)
            self.store.depend(decision.decision_id,(decision.review_task_id,),con=con)
        return digest(decision)

    def revised_draft(self, decision_id: str, new_draft_id: str) -> PrefillDraft:
        decision = ReviewDecision.model_validate(self.store.get("review_decision",decision_id))
        task = self.store.get("review_task",decision.review_task_id)
        original = PrefillDraft.model_validate(self.store.get("draft",task["draft_id"]))
        if decision.mode != "assisted" or decision.decision != "REVISE":
            raise ValueError("Only assisted REVISE creates a new candidate version")
        if not self.store.active(decision_id):
            raise ValueError("Decision invalidated")
        results = []
        for result in original.results:
            fields = dict(result.fields)
            for field in fields:
                if result.result_id+"/"+field in decision.patches:
                    fields[field] = decision.patches[result.result_id+"/"+field]
            results.append(result.model_copy(update={"fields":fields}))
        new = original.model_copy(update={"draft_id":new_draft_id,"results":tuple(results)})
        from .prefill import PrefillService
        PrefillService(self.store).ingest(new)
        self.store.depend(new_draft_id,(original.draft_id,decision_id))
        # Original issues remain until separately adjudicated; patching a number
        # does not silently close a source conflict or reuse old verification.
        return new
