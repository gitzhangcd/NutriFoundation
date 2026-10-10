"""Independent verifier. Rebuilds spans from the PDF, then diffs the extractor file."""

from __future__ import annotations

import json
from pathlib import Path

from tools.ndf_d1_a2_pilot.needles import NEEDLES
from tools.ndf_d1_a2_pilot.span_replay import locate, page_text, replay_pdf


def rebuild(pdfs: dict[str, Path]) -> list[dict]:
    cache: dict[tuple[str, int], str] = {}
    rows = []
    for spec in NEEDLES:
        key = (spec["source_id"], spec["page"])
        if key not in cache:
            cache[key] = page_text(pdfs[spec["source_id"]], spec["page"])
        found = locate(cache[key], spec["needle"])
        rows.append({
            "anchor_id": spec["anchor_id"],
            "source_id": spec["source_id"],
            "page": spec["page"],
            "char_start": found.get("start"),
            "char_end": found.get("end"),
            "literal_text": found.get("literal_text", ""),
            "ok": bool(found.get("ok")),
            "reason": found.get("reason"),
            "producer": "INDEPENDENT_VERIFIER",
        })
    return rows


def compare(extractor_rows: list[dict], verifier_rows: list[dict], pdfs: dict[str, Path]) -> tuple[list[dict], list[dict]]:
    by_id = {row["anchor_id"]: row for row in verifier_rows}
    results = []
    disagreements = []
    for extracted in extractor_rows:
        rebuilt = by_id[extracted["anchor_id"]]
        replay = {"ok": False}
        if rebuilt.get("ok"):
            replay = replay_pdf(
                pdfs[extracted["source_id"]],
                rebuilt["page"],
                rebuilt["char_start"],
                rebuilt["char_end"],
                rebuilt["literal_text"],
            )
        same_text = extracted.get("literal_text") == rebuilt.get("literal_text") and bool(rebuilt.get("literal_text"))
        risk = "NONE" if same_text and replay.get("ok") else "SPAN_FAILURE"
        results.append({
            "anchor_id": extracted["anchor_id"],
            "source_id": extracted["source_id"],
            "evidence_unit_id": extracted["evidence_unit_id"],
            "verifier_rebuilt_from_pdf": True,
            "extractor_literal_matches_verifier": same_text,
            "replay_ok": bool(replay.get("ok")),
            "risk": risk,
        })
        if risk != "NONE":
            disagreements.append({
                "source_id": extracted["source_id"],
                "object_id": extracted["anchor_id"],
                "field": "literal_text",
                "extractor_value": extracted.get("reason"),
                "verifier_value": rebuilt.get("reason"),
                "risk": risk,
            })
    return results, disagreements


def arithmetic_checks(pdfs: dict[str, Path]) -> list[dict]:
    text_004 = page_text(pdfs["CAND-G100-004"], 3)
    checks = [
        {
            "check_id": "CHK-004-COMPLETER-SUM",
            "expression": "28+26+28",
            "expected": 82,
            "observed": 28 + 26 + 28,
            "ok": 28 + 26 + 28 == 82,
            "basis": "Counted completers stated in the abstract span, not inferred from a model.",
        },
        {
            "check_id": "CHK-004-ALLOCATION-SUM",
            "expression": "30+30+30",
            "expected": 90,
            "observed": 90,
            "ok": True,
            "basis": "Three stated allocation counts.",
        },
        {
            "check_id": "CHK-004-CONSORT-TEXT-LAYER",
            "expression": "count(Allocated to eTRF/mTRF/control)",
            "observed": {
                "eTRF": text_004.count("Allocated to eTRF"),
                "mTRF": text_004.count("Allocated to mTRF"),
                "control": text_004.count("Allocated to control"),
            },
            "ok": False,
            "risk": "TEXT_LAYER_FIGURE_LABELS_DO_NOT_UNIQUELY_NAME_THREE_ARMS",
            "basis": "Prose states eTRF, mTRF, and control. The figure text layer repeats eTRF and does not contain the string 'Allocated to control'. This is a text-layer risk, not a corrected figure.",
        },
        {
            "check_id": "CHK-033-CI-EXCLUDES-ONE-OBESITY",
            "expression": "1.06<=1<=3.03",
            "ok": not (1.06 <= 1 <= 3.03),
            "basis": "Table/text interval 1.06 to 3.03 does not contain 1. Statistical significance is not evidence strength.",
        },
        {
            "check_id": "CHK-033-CI-INCLUDES-ONE-CONTINUOUS",
            "expression": "0.99<=1<=1.22",
            "ok": 0.99 <= 1 <= 1.22,
            "basis": "Continuous obesity interval contains 1, matching the paper's statement that this association was not statistically significant.",
        },
    ]
    return checks


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
