from __future__ import annotations

from datetime import date, datetime

from .models import PrefillDraft, VerificationReport, digest, now
from .store import ProductionStore


def cutoff_eligibility(start: date | None, end: date | None, cutoff: date) -> str:
    if start is None or end is None:
        return "UNRESOLVED"
    if end < start:
        raise ValueError("Invalid date interval")
    if end <= cutoff:
        return "ELIGIBLE"
    if start > cutoff:
        return "INELIGIBLE"
    return "UNRESOLVED"


class ReleaseService:
    """Staging releases only until authority/schema/H0/expert qualification closes.

    Returning blocked gates is useful now. A user-supplied boolean or worker
    response cannot grant canonical or Gold authority.
    """
    def __init__(self, store: ProductionStore):
        self.store = store

    def promotion_gates(self, draft_id: str, report_id: str, *, use: str) -> dict:
        draft = PrefillDraft.model_validate(self.store.get("draft",draft_id))
        report = VerificationReport.model_validate(self.store.get("verification",report_id))
        blocked = []
        if report.draft_sha256!=digest(draft):
            blocked.append("verification_candidate_version_mismatch")
        if not self.store.active(draft_id) or not self.store.active(report_id):
            blocked.append("dependency_invalidated")
        if any(c.status not in {"PASS","NOT_APPLICABLE"} for c in report.checks):
            blocked.append("field_or_scope_checks_unresolved")
        if report.independent_evidence_status!="ATTESTED_EXECUTION_ONLY":
            blocked.append("independent_readout_missing")
        blocked += ["authority_schema_reconciliation_not_qualified","human_or_h0_release_authority_not_qualified"]
        if use=="gold":
            blocked += ["two_independent_qualified_experts_not_registered","expert_adjudication_not_complete"]
        elif use!="canonical":
            raise ValueError("Unknown promotion use")
        return {"allowed":False,"use":use,"draft_sha256":digest(draft),"blocked_gates":blocked}

    def staging_release(self, draft_ids: tuple[str,...], *, release_id: str, cutoff_mode: str,
                        cutoff: datetime) -> dict:
        if cutoff_mode not in {"SYSTEM_FAITHFUL","CONTENT_FAITHFUL"} or cutoff.tzinfo is None:
            raise ValueError("Explicit cutoff mode and timezone required")
        if cutoff > now():
            raise ValueError("Future cutoff cannot represent an observed system snapshot")
        if len(set(draft_ids))!=len(draft_ids):
            raise ValueError("Duplicate release member")
        members = []
        with self.store.transaction() as con:
            for draft_id in draft_ids:
                row = con.execute("SELECT payload,created_at,sha256 FROM d0_record WHERE kind='draft' AND id=?",(draft_id,)).fetchone()
                if not row:
                    raise ValueError("Missing release member")
                # CONTENT_FAITHFUL needs independently bound public availability;
                # it cannot silently fall back to date of system ingestion.
                if cutoff_mode=="CONTENT_FAITHFUL":
                    raise ValueError("Public availability/date precision not bound; content-faithful release deferred")
                if datetime.fromisoformat(row["created_at"]) > cutoff:
                    raise ValueError("Member was not in system by cutoff")
                invalid = con.execute("SELECT 1 FROM d0_invalidation WHERE dependency_id=?",(draft_id,)).fetchone()
                if invalid:
                    raise ValueError("Invalidated member cannot enter new release")
                import json
                draft = PrefillDraft.model_validate(json.loads(row["payload"]))
                members.append({"draft_id":draft_id,"sha256":row["sha256"],
                    "snapshot_id":draft.task.snapshot_id,"snapshot_sha256":draft.task.snapshot_sha256,
                    "parsed_id":draft.task.parsed_id,"parsed_sha256":draft.task.parsed_sha256,
                    "task_sha256":draft.task_sha256,"authority_sha256":draft.task.authority_sha256})
            release = {"release_id":release_id,"status":"STAGING_ONLY","canonical":False,"gold":False,
                "cutoff_mode":cutoff_mode,"cutoff":cutoff.isoformat(),"members":members,
                "excluded_uses":["canonical_scientific_reference","independent_gold","publication_accuracy_claim"]}
            self.store.put("release",release_id,release,con=con)
            self.store.depend(release_id,draft_ids,con=con)
        return release
