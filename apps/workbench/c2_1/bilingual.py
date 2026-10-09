"""WB-v0.3-P1.1 bilingual UX *sample*, not a scientific translation authority.

Only display translations derived from the already task-authorized document.
The security boundary is the secure_reader controller endpoint, NOT this module.
Do not place source-text translations in publicly accessible /static files.
"""
from __future__ import annotations

from hashlib import sha256
from translation_contract import SCHEMA, validate

VERSION = "WB-v0.3-P1.1-UX-EXCERPTS-v0.1"
STATUS = "ILLUSTRATIVE_UNVERIFIED_NOT_FOR_SCIENTIFIC_CAPTURE"

# Deliberately small reviewer-visible UX fixture, not a machine-translated
# full-text archive. Exact source excerpts must exist in the qualified,
# task-authorized SourceDocument to be projected.
PAIRS = (
    (
        "Three hundred adults with obesity were randomised",
        "共三百名肥胖成年人被随机分配（此处仅供阅读交互演练）。",
    ),
    (
        "Simple 5:2 advice and multicomponent weight management advice generated similar modest results.",
        "简明的 5:2 饮食建议与多组分体重管理建议产生了相近且幅度有限的结果。",
    ),
    (
        "Adding initial group support enhanced 5:2 adherence and effects, but the impact diminished over time.",
        "增加初期小组支持改善了对 5:2 饮食的依从性和干预效果，但这种影响随时间推移而减弱。",
    ),
)


def projection(doc: dict) -> dict:
    """V1.2 manifest: exact-source excerpts, versioned but NOT certified translations."""
    entries = []
    for unit in doc["units"]:
        raw = unit["raw"]
        for original, zh in PAIRS:
            if raw.count(original) != 1:
                continue
            i = raw.index(original)
            start = len(raw[:i].encode("utf-16-le")) // 2
            end = start + len(original.encode("utf-16-le")) // 2
            entries.append({
                "unit_id": unit["unit_id"],
                "source_unit_raw_sha256": unit["raw_sha256"],
                "source_quote": original,
                "source_start_utf16": start,
                "source_end_utf16": end,
                "translated_excerpt": zh,
                "alignment_level": "SOURCE_EXCERPT_ONLY",
                "translation_status": "UNVERIFIED_SYNTHETIC",
                "review_receipt_ref": None,
            })
    pack = {
        "schema_version": SCHEMA,
        "source_document_id": doc["document_id"],
        "source_revision": doc["revision"],
        "source_markdown_sha256": doc["source_markdown_sha256"],
        "source_pdf_sha256": doc["source_pdf_sha256"],
        "translation_version": VERSION,
        "target_language": "zh-CN",
        "policy": "SYNTHETIC_REVIEW_ONLY",
        "items": entries,
    }
    result = validate(doc, pack)
    # Keep P1.1 API fields for backwards-compatible synthetic Chromium tests.
    result["translation_policy"] = STATUS
    result["coverage"] = "SELECTED_EXCERPTS_NOT_FULL_PARAGRAPH_TRANSLATIONS"
    return result
