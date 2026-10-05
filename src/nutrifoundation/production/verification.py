from __future__ import annotations

import re

from .models import Check, IndependentReadout, ParsedDocument, PrefillDraft, VerificationReport, digest


REQUIRED = {
    "EvidenceUnit": ("study_id", "population", "exposure", "comparator", "outcome", "time", "estimand", "analysis_population", "model", "effect_measure", "effect_value", "effect_unit", "exposure_increment", "reference_category"),
    "Recommendation": ("population", "recommendation", "applicability", "exceptions"),
    "ScientificClaim": ("statement", "evidence_refs", "population", "outcome"),
}


def verify_draft(draft: PrefillDraft, parsed: ParsedDocument,
                 readout: IndependentReadout | None = None) -> VerificationReport:
    """Mechanical evidence is necessary, never sufficient for semantic support.

    Source-only worker claims are recorded as attestations, not proof of
    cognition, expertise or scientific truth. Canonical/Gold remain gated.
    """
    draft = PrefillDraft.model_validate(draft.model_dump(mode="json"))
    parsed = ParsedDocument.model_validate(parsed.model_dump(mode="json"))
    if readout is not None:
        readout = IndependentReadout.model_validate(readout.model_dump(mode="json"))
    if digest(parsed) != draft.task.parsed_sha256 or parsed.parsed_id != draft.task.parsed_id:
        raise ValueError("Parsed document binding mismatch")
    if parsed.snapshot_id != draft.task.snapshot_id:
        raise ValueError("Snapshot identity mismatch")
    anchors = {a.anchor_id:a for a in parsed.anchors}
    checks = []
    def add(r,f,rule,status,reason):
        checks.append(Check(result_id=r,field=f,rule=rule,status=status,reason=reason))
    independent = bool(readout and readout.task_sha256==draft.task_sha256
        and readout.snapshot_id==draft.task.snapshot_id and readout.parsed_sha256==digest(parsed)
        and readout.worker_id!=draft.task.extractor_id and readout.session_id
        and not readout.candidate_exposed)
    read_results = {r.result_id:r for r in readout.results} if independent else {}
    if independent:
        draft_ids={r.result_id for r in draft.results}
        for rr in read_results.values():
            if rr.result_id not in draft_ids:
                add(rr.result_id,"*","readout_coverage","UNRESOLVED","Independent readout contains an additional result")
            for issue in rr.issues:
                add(rr.result_id,"*","independent_source_issue","UNRESOLVED",issue)
    for result in draft.results:
        for field in REQUIRED[result.object_type]:
            if field not in result.fields:
                add(result.result_id,field,"required_scope","UNRESOLVED","No field assertion supplied")
        for field,assertion in result.fields.items():
            if assertion.state != "PRESENT":
                # Missingness is a fact to verify, not a waiver of required scope.
                add(result.result_id,field,"field_availability","UNRESOLVED",assertion.reason or assertion.state)
            else:
                bound = [anchors.get(ref) for ref in assertion.anchor_refs]
                valid = bool(bound) and all(a is not None and a.snapshot_id==draft.task.snapshot_id
                    and a.source_sha256==draft.task.snapshot_sha256 for a in bound)
                add(result.result_id,field,"anchor_binding","PASS" if valid else "FAIL","Bound exact parser/snapshot anchors" if valid else "Unknown or wrong-version anchor")
                # Exact source value must occur locally, not anywhere in the document.
                support = valid and any(assertion.source_value in a.exact_text for a in bound)
                add(result.result_id,field,"local_source_value","PASS" if support else "FAIL","Source value located in bound span" if support else "Source value absent in its bound span")
                if assertion.normalized_value is not None and assertion.normalized_value != assertion.source_value:
                    add(result.result_id,field,"normalization","UNRESOLVED","Transformation needs explicit qualified deterministic adapter")
                if field in {"effect","effect_value","statement","recommendation"}:
                    text = (assertion.normalized_value or assertion.source_value or "")
                    if re.search(r"\bcaus(?:e[sd]?|al)\b|因果|导致",text,re.I):
                        add(result.result_id,field,"causal_scope","UNRESOLVED","Causal assertion requires scientific identification and explicit review")
            rr = read_results.get(result.result_id)
            compared = rr.fields.get(field) if rr else None
            if not independent:
                add(result.result_id,field,"independent_semantic_support","UNRESOLVED","No eligible locked source-only readout")
            elif compared != assertion:
                add(result.result_id,field,"independent_semantic_support","FAIL","Independent readout differs or omitted field; compare model/outcome/units/anchors")
            else:
                add(result.result_id,field,"independent_semantic_support","PASS","Locked readout agrees; execution independence attested only")
        for issue in result.issues:
            add(result.result_id,"*","source_issue","UNRESOLVED",issue)
    if not draft.results:
        add("*","*","results","UNRESOLVED","No extracted result")
    for omission in draft.coverage_omissions:
        add("*","*","coverage","UNRESOLVED",omission)
    if readout and not independent:
        add("*","*","readout_binding","FAIL","Readout is exposed or has wrong identity/version/task/session binding")
    payload = dict(draft_sha256=digest(draft),parsed_sha256=digest(parsed),checks=tuple(checks),
        independent_readout_id=readout.readout_id if readout else None,
        independent_readout_sha256=digest(readout) if readout else None,
        independent_evidence_status="ATTESTED_EXECUTION_ONLY" if independent else "NOT_PROVEN")
    return VerificationReport(report_id="VER-"+digest(payload),**payload)
