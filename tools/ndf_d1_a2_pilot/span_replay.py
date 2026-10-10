"""Locate a pre-registered string in one PDF page and replay it."""

from __future__ import annotations

from pathlib import Path

import fitz


def page_text(pdf: Path, page_number: int) -> str:
    document = fitz.open(pdf)
    try:
        return document[page_number - 1].get_text()
    finally:
        document.close()


def locate(text: str, needle: str) -> dict:
    start = text.find(needle)
    if start < 0:
        return {"ok": False, "reason": "NEEDLE_NOT_IN_PAGE_TEXT"}
    second = text.find(needle, start + 1)
    if second >= 0:
        return {"ok": False, "reason": "NEEDLE_NOT_UNIQUE", "start": start}
    end = start + len(needle)
    literal = text[start:end]
    return {
        "ok": literal == needle,
        "start": start,
        "end": end,
        "literal_text": literal,
        "reason": "REPLAYED" if literal == needle else "SLICE_MISMATCH",
    }


def replay_pdf(pdf: Path, page_number: int, start: int, end: int, literal_text: str) -> dict:
    text = page_text(pdf, page_number)
    observed = text[start:end] if 0 <= start < end <= len(text) else ""
    return {"ok": observed == literal_text, "observed_length": len(observed)}
