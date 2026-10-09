"""WB-v0.3-P1.2 scientific translation projection contract (sidecar only).

This module NEVER certifies medical translation quality, never calls third-party
translation services, and cannot widen source/arm authorization. A caller must
first validate its task-scoped source projection.
"""
from __future__ import annotations
import hashlib
import json
import re
from typing import Any

SCHEMA = "WB_BILINGUAL_SOURCE_PROJECTION_V1"
SOURCE_STATUS = {"UNVERIFIED_SYNTHETIC", "REVIEW_PENDING"}
ALIGNMENTS = {"SOURCE_EXCERPT_ONLY", "FULL_UNIT"}
MAX_TRANSLATED_CHARS = 20000
NUMBER = re.compile(r"(?<![\w])(?:\d+(?:[.,]\d+)*)(?:%|％)?")

def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def utf16_slice(text: str, start: int, end: int) -> str:
    if type(start) is not int or type(end) is not int or not 0 <= start < end:
        raise ValueError("INVALID_UTF16_SPAN")
    blob = text.encode("utf-16-le")
    if end * 2 > len(blob):
        raise ValueError("INVALID_UTF16_SPAN")
    try:
        return blob[start*2:end*2].decode("utf-16-le")
    except UnicodeDecodeError as exc:
        raise ValueError("INVALID_UTF16_BOUNDARY") from exc

def numerical_warnings(source: str, translated: str) -> list[str]:
    """Heuristic only; scientific QA must independently check statistics."""
    a = sorted(NUMBER.findall(source))
    b = sorted(NUMBER.findall(translated))
    return [] if a == b else ["NUMERIC_TOKEN_REVIEW_REQUIRED"]

def validate(doc: dict, pack: dict) -> dict:
    required = {"schema_version", "source_document_id", "source_revision",
                "source_markdown_sha256", "source_pdf_sha256", "translation_version",
                "target_language", "policy", "items"}
    if set(pack) != required or pack["schema_version"] != SCHEMA:
        raise ValueError("TRANSLATION_CONTRACT_MISMATCH")
    expected = {"source_document_id": doc["document_id"], "source_revision": doc["revision"],
                "source_markdown_sha256": doc["source_markdown_sha256"],
                "source_pdf_sha256": doc["source_pdf_sha256"]}
    if any(pack[k] != v for k, v in expected.items()):
        raise ValueError("TRANSLATION_SOURCE_VERSION_MISMATCH")
    if pack["target_language"] != "zh-CN" or pack["policy"] != "SYNTHETIC_REVIEW_ONLY":
        raise ValueError("TRANSLATION_NOT_AUTHORIZED")
    if not isinstance(pack["translation_version"], str) or not 1 <= len(pack["translation_version"]) <= 120:
        raise ValueError("INVALID_TRANSLATION_VERSION")
    units = {u["unit_id"]: u for u in doc["units"]}
    if not isinstance(pack["items"], list) or len(pack["items"]) > len(units) * 8:
        raise ValueError("INVALID_TRANSLATION_ITEMS")
    items, seen = [], set()
    expected_keys = {"unit_id", "source_unit_raw_sha256", "source_quote", "source_start_utf16",
                     "source_end_utf16", "translated_excerpt", "alignment_level",
                     "translation_status", "review_receipt_ref"}
    for entry in pack["items"]:
        if not isinstance(entry, dict) or set(entry) != expected_keys:
            raise ValueError("TRANSLATION_ITEM_SCHEMA_MISMATCH")
        unit = units.get(entry["unit_id"])
        if unit is None or entry["source_unit_raw_sha256"] != unit["raw_sha256"]:
            raise ValueError("TRANSLATION_UNIT_IDENTITY_MISMATCH")
        quote = utf16_slice(unit["raw"], entry["source_start_utf16"], entry["source_end_utf16"])
        if not quote or quote != entry["source_quote"]:
            raise ValueError("TRANSLATION_ORIGINAL_SPAN_MISMATCH")
        if entry["alignment_level"] not in ALIGNMENTS:
            raise ValueError("TRANSLATION_ALIGNMENT_INVALID")
        if entry["alignment_level"] == "FULL_UNIT" and quote != unit["raw"]:
            raise ValueError("TRANSLATION_FALSE_FULL_UNIT")
        if entry["translation_status"] not in SOURCE_STATUS or entry["review_receipt_ref"] is not None:
            # A string claiming review/approval is NOT independent verification.
            raise ValueError("TRANSLATION_REVIEW_CLAIM_NOT_VERIFIED")
        tr = entry["translated_excerpt"]
        if not isinstance(tr, str) or not tr.strip() or len(tr) > MAX_TRANSLATED_CHARS:
            raise ValueError("TRANSLATION_TEXT_INVALID")
        identity = (entry["unit_id"], entry["source_start_utf16"], entry["source_end_utf16"])
        if identity in seen: raise ValueError("TRANSLATION_DUPLICATE_SPAN")
        seen.add(identity)
        items.append({**entry, "quality_warnings": numerical_warnings(quote, tr)})
    full = len({x["unit_id"] for x in items if x["alignment_level"] == "FULL_UNIT"})
    counts = {"all_units": len(units), "fully_translated_units": full,
              "translated_excerpts": len(items),
              "untranslated_units": len(units) - full}
    result = dict(pack)
    result.update({"translation_fixture_sha256": digest(pack), "coverage_counts": counts,
                   "coverage": "FULL_SOURCE_UNVERIFIED" if full == len(units) and full else
                   "PARTIAL_UNVERIFIED", "items": items, "scientific_capture": False})
    return result
