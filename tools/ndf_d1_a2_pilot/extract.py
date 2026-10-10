"""Extractor. Reads the PDF. Does not assign L3/L4 qualification."""

from __future__ import annotations

from pathlib import Path

from tools.ndf_d1_a2_pilot.needles import NEEDLES
from tools.ndf_d1_a2_pilot.span_replay import locate, page_text


def extract_anchors(pdfs: dict[str, Path]) -> list[dict]:
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
            "evidence_unit_id": spec["evidence_unit_id"],
            "page": spec["page"],
            "role": spec["role"],
            "locator_status": "LOCATED" if found.get("ok") else "HOLD",
            "char_start": found.get("start"),
            "char_end": found.get("end"),
            "literal_text": found.get("literal_text", ""),
            "reason": found.get("reason"),
            "producer": "EXTRACTOR",
        })
    return rows
