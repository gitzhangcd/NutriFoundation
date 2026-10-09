"""Seed clearly fabricated evidence-annotation tasks. NEVER real published evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from core import EvidenceEngine, digest

HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent / "ea_p0" / "specs" / "annotation_contract.v0.1.json"

SOURCES = [
    ("RCT-001", "RANDOMIZED_TRIAL", "[SYNTHETIC] 5:2 diet study training narrative",
     "A synthetic randomized trial compares two dietary advice methods.",
     "The invented trial reports a fictional 6-month comparison. It must never be cited as a real 5:2 trial result."),
    ("COHORT-001", "OBSERVATIONAL_STUDY", "[SYNTHETIC] cohort study",
     "A fabricated observational cohort links a diet pattern with an outcome.",
     "The association is observational and cannot by itself prove causation."),
    ("META-001", "SYSTEMATIC_REVIEW_META", "[SYNTHETIC] systematic review",
     "A synthetic systematic review describes studies and a pooled effect.",
     "Individual studies may overlap with other reviews and must not be counted twice."),
    ("GUIDE-001", "GUIDELINE", "[SYNTHETIC] nutrition guidance",
     "A fabricated guideline includes a conditional recommendation for an example population.",
     "The recommendation has an exception and uses an organization-specific grading scale."),
    ("CONS-001", "CONSENSUS", "[SYNTHETIC] consensus statement",
     "A fictional Delphi panel considered an example nutrition practice.",
     "Expert agreement is not the same as high-certainty empirical effect evidence."),
    ("NARR-001", "NARRATIVE_REVIEW", "[SYNTHETIC] narrative review",
     "A fictional narrative review proposes a mechanistic hypothesis.",
     "The hypothesis remains unproven and the citations would require validation."),
    ("CORR-001", "CORRECTION_RETRACTION", "[SYNTHETIC] correction notice",
     "A fictional correction updates an earlier study interpretation.",
     "Historical snapshots before the correction date must not include the new information."),
]


def anchor(source, unit_id="u2", text=None):
    raw = next(x["text"] for x in source["units"] if x["unit_id"] == unit_id)
    quote = raw if text is None else text
    start = raw.index(quote)
    prefix = raw[:start]
    start16 = len(prefix.encode("utf-16-le")) // 2
    return {
        "source_id": source["source_id"], "revision_id": source["revision_id"],
        "canonical_document_sha256": source["canonical_document_sha256"],
        "unit_id": unit_id, "start_utf16": start16,
        "end_utf16": start16 + len(quote.encode("utf-16-le")) // 2,
        "source_quote": quote, "source_quote_sha256": digest(quote.encode("utf-8")),
        "pdf_locator": {"status": "UNRESOLVED"}
    }


def populate(engine: EvidenceEngine):
    now = datetime.now(timezone.utc).isoformat()
    result = []
    for i, (sid, kind, title, p1, p2) in enumerate(SOURCES):
        source = engine.register_source(actor="SYN-PRODUCER-1", role="producer",
            source={"source_id": sid, "revision_id": "r1",
                    "source_type": kind, "title": title, "available_at": "2026-01-01T00:00:00+00:00",
                    "fetched_at": now, "rights_status": "SYNTHETIC_FIXTURE",
                    "units": [{"unit_id": "u1", "text": p1}, {"unit_id": "u2", "text": p2}],
                    "source_family_refs": []})
        result.append(source)
    tasks = []
    for i, source in enumerate(result):
        profile = engine.profiles[source["source_type"]]
        # The first case intentionally uses TWO authorized source versions.
        allow = [source, result[3]] if i == 0 else [source]
        task = engine.create_task(actor="SYN-PRODUCER-1", role="producer",
            task={"task_id": "EA-P1-SYN-" + str(i + 1).zfill(2),
                  "task_kind": "EVIDENCE_ECOSYSTEM_CASE",
                  "primary_source": {"source_id": source["source_id"], "revision_id": "r1"},
                  "allowed_source_versions": [
                      {"source_id": s["source_id"], "revision_id": s["revision_id"],
                       "canonical_document_sha256": s["canonical_document_sha256"]}
                      for s in allow],
                  "profile_id": profile["profile_id"], "knowledge_cutoff": now,
                  "workflow_strategy": "AGENT_PROPOSE_EXPERT_VERIFY",
                  "expert_actor": "SYN-EXPERT-A"})
        candidate = {"candidate_id": "CAND-" + task["task_id"], "source_ref":
                {"source_id": source["source_id"], "revision_id": "r1"},
            "field_group": next(x for x in profile["required_groups"] if x != "source_spans"),
            "target_canonical_object_type": profile["canonical_object_candidates"][0],
            "candidate_payload": {"training_note": "FABRICATED source content; verify against the simulated original unit."},
            "original_anchors": [anchor(source)], "extraction_run_ref": "SYN-FIXTURE-NOT-AN-LLM"}
        engine.freeze_candidates(actor="SYN-PRODUCER-1", role="producer",
                                 task_id=task["task_id"], items=[candidate])
        tasks.append(task["task_id"])
    independent = result[1]
    engine.create_task(actor="SYN-PRODUCER-1", role="producer",
        task={"task_id": "EA-P1-SYN-INDEPENDENT", "task_kind": "EVIDENCE_ECOSYSTEM_CASE",
              "primary_source": {"source_id": independent["source_id"], "revision_id": "r1"},
              "allowed_source_versions": [{"source_id": independent["source_id"],
                   "revision_id": "r1",
                   "canonical_document_sha256": independent["canonical_document_sha256"]}],
              "profile_id": engine.profiles["OBSERVATIONAL_STUDY"]["profile_id"],
              "knowledge_cutoff": now, "workflow_strategy": "HUMAN_INDEPENDENT",
              "expert_actor": "SYN-EXPERT-B"})
    return {"sources": len(result), "agent_verify_tasks": tasks,
            "independent_task": "EA-P1-SYN-INDEPENDENT",
            "note": "ALL SOURCE TEXT FABRICATED, NOT REAL EVIDENCE OR MODEL OUTPUT"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    args = parser.parse_args()
    import json
    print(json.dumps(populate(EvidenceEngine(args.db, CONTRACT)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
