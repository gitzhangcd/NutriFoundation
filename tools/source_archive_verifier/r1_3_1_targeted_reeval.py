#!/usr/bin/env python3
"""Re-evaluate R1.3 CONFIRMED rows and a fixed boundary sample. Does not rewrite R1.3."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tools.source_archive_verifier.identity_evaluator import (
    evaluate_content_completeness,
    evaluate_pdf_identity_canonical,
)

VAULT = Path("/Users/zhangcd/Codes/Ai-Nutri/data/g1_source_library")
R13 = VAULT / "verification_runs" / "G1S-133-R1-3-TRUTHFULNESS-20261010T075311Z"
MANIFEST = VAULT / "Archived_Papers_133_Manifest.json"
BOUNDARY_STATUSES = {
    "VERSION_IDENTITY_UNRESOLVED",
    "TITLE_PREFIX_ONLY_DIVERGENT",
    "COVER_DOI_CONFLICT",
    "CONFLICTING_DOI_DETECTED",
    "TITLE_ONLY_IN_BODY_CITATION",
    "INSUFFICIENT_EVIDENCE",
    "PROBABLE_HIGH_WINDOW_SIMILARITY",
    "DISPERSED_KEYWORDS_REJECTED",
}


def main(run_dir: Path) -> dict:
    prior = [json.loads(line) for line in (R13 / "03_per_source_results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    records = {row["source_id"]: row for row in json.loads(MANIFEST.read_text(encoding="utf-8"))["records"]}
    confirmed = [row for row in prior if row["identity_verdict"] == "CONFIRMED"]
    boundary = [row for row in prior if row["identity_verdict"] != "CONFIRMED" and row["identity_status"] in BOUNDARY_STATUSES]
    probable_sample = [row for row in prior if row["identity_status"] == "PROBABLE_TITLE_DOI_NOT_LOCATED"][:5]
    selected = {row["source_id"]: row for row in confirmed + boundary + probable_sample}
    deltas = []
    for sid, old in selected.items():
        record = records[sid]
        pdf = VAULT / record["archive_asset"]["vault_path"].strip()
        fresh = evaluate_pdf_identity_canonical(
            pdf,
            record["title"],
            record["identifiers"].get("doi") or "",
            record["identifiers"].get("pmid") or "",
            source_id=sid,
            expected_journal=record.get("journal") or "",
            expected_date=record.get("publication_date") or "",
        )
        deltas.append({
            "source_id": sid,
            "cohort": "R13_CONFIRMED" if old["identity_verdict"] == "CONFIRMED" else "BOUNDARY_SAMPLE",
            "r1_3_verdict": old["identity_verdict"],
            "r1_3_status": old["identity_status"],
            "r1_3_1_verdict": fresh["identity_verdict"],
            "r1_3_1_status": fresh["identity_status"],
            "r1_3_1_rule": fresh["match_rule"],
            "changed": old["identity_verdict"] != fresh["identity_verdict"] or old["identity_status"] != fresh["identity_status"],
            "article_identity_block_id": fresh.get("article_identity_block_id"),
            "article_identity_block_page": fresh.get("article_identity_block_page"),
            "article_identity_block_reason": fresh.get("article_identity_block_reason"),
            "has_title_anchor": bool(fresh.get("title_anchor")),
            "has_doi_anchor": bool(fresh.get("doi_anchor")),
            "alternative_credential_count": len(fresh.get("alternative_credential_anchors") or []),
        })
    completeness_rows = []
    for old in prior:
        if old.get("content_completeness") != "COMPLETE":
            continue
        record = records[old["source_id"]]
        pdf = VAULT / record["archive_asset"]["vault_path"].strip()
        fresh = evaluate_content_completeness(pdf)
        completeness_rows.append({
            "source_id": old["source_id"],
            "r1_3_content_completeness": "COMPLETE",
            "r1_3_1_content_completeness": fresh["content_completeness"],
            "r1_3_1_scope": fresh["completeness_scope"],
            "semantic_correction": "REFERENCES_HEADING_IS_LIMITED_COVERAGE_NOT_FULL_TEXT",
        })
    confirmed_deltas = [row for row in deltas if row["cohort"] == "R13_CONFIRMED"]
    summary = {
        "r1_3_run": "G1S-133-R1-3-TRUTHFULNESS-20261010T075311Z",
        "r1_3_confirmed_retested": len(confirmed_deltas),
        "confirmed_verdict_changed": sum(1 for row in confirmed_deltas if row["r1_3_verdict"] != row["r1_3_1_verdict"]),
        "confirmed_status_or_verdict_changed": sum(1 for row in confirmed_deltas if row["changed"]),
        "r1_3_1_verdict_counts_among_former_confirmed": dict(Counter(row["r1_3_1_verdict"] for row in confirmed_deltas)),
        "boundary_sample_retested": sum(1 for row in deltas if row["cohort"] == "BOUNDARY_SAMPLE"),
        "boundary_changed": sum(1 for row in deltas if row["cohort"] == "BOUNDARY_SAMPLE" and row["changed"]),
        "former_complete_rows": len(completeness_rows),
        "former_complete_now": dict(Counter(row["r1_3_1_content_completeness"] for row in completeness_rows)),
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "r131_confirmed86_and_boundary_delta.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in deltas), encoding="utf-8"
    )
    (run_dir / "r131_completeness_semantic_correction.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in completeness_rows), encoding="utf-8"
    )
    (run_dir / "r131_reeval_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    import sys
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/r131-reeval")
    main(destination)
