"""Deterministic PDF_PAGE_BBOX locator with adversarial safeguards (WB-P0.2-B1).

PDF text geometry is not an inferential truth source. Never assert exact PDF
coordinates from Markdown page hints alone. A successful location needs ONE
match of the user-approved quote in the actual, immutable PDF text layer.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz

MIN_QUOTE_TOKENS = 5
MAX_QUOTE_TOKENS = 140
TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


class LocatorError(ValueError):
    pass


def norm_tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text).casefold()
    text = text.replace("\u00ad", "").replace("\ufb01", "fi").replace("\ufb02", "fl")
    return TOKEN_RE.findall(text)


@dataclass(frozen=True)
class WordToken:
    text: str
    boxes: tuple[tuple[int, int, float, float, float, float], ...]


def page_tokens(page: fitz.Page) -> list[WordToken]:
    """Use original PDF word order and keep each word's block/line for rect splitting."""
    items: list[WordToken] = []
    previous_raw = ""
    previous_block = previous_line = None
    for word in page.get_text("words", sort=False):
        x0, y0, x1, y1, raw, block, line, _ = word
        tks = norm_tokens(raw)
        if not tks:
            continue
        box = (int(block), int(line), float(x0), float(y0), float(x1), float(y1))
        # A physical end-of-line hyphen may split a word ("fol-" / "lowed").
        # Join only within the same block across immediately successive lines.
        if (items and previous_raw.endswith("-") and previous_block == block and
                previous_line is not None and int(line) == previous_line + 1 and
                len(tks) == 1 and raw[0].isalpha()):
            prior = items[-1]
            if prior.text.isalpha():
                items[-1] = WordToken(prior.text + tks[0], prior.boxes + (box,))
                previous_raw = raw
                previous_block, previous_line = int(block), int(line)
                continue
        items.extend(WordToken(t, (box,)) for t in tks)
        previous_raw = raw
        previous_block, previous_line = int(block), int(line)
    return items


def _check_text_geometry(matched: list[WordToken]) -> None:
    """Refuse lexical matches stitched across unrelated PDF text blocks/lines.

    Reading order from PDF may concatenate the end of one column with the start
    of a second. A flattened text match is *not* sufficient proof of a span.
    """
    prev = None
    for token in matched:
        for box in token.boxes:
            block, line, x0, y0, x1, y1 = box
            if prev is not None:
                pblock, pline, px0, py0, px1, py1 = prev
                if block != pblock:
                    raise LocatorError("CROSS_BLOCK_SEQUENCE_NOT_TRUSTWORTHY")
                if line == pline:
                    # Rotated display is handled later; these are unrotated words.
                    if (x0 + .5 < px0 or x0 - px1 > max(35, 2.5 * (py1-py0)) or
                            y0 > py1 + max(12, 2 * (py1-py0))):
                        raise LocatorError("NON_CONTIGUOUS_PDF_TEXT_GEOMETRY")
                elif line == pline + 1:
                    if y0 < py1 - 2 or y0 - py1 > max(30, 2.5 * (py1 - py0)):
                        raise LocatorError("NON_CONTIGUOUS_PDF_TEXT_GEOMETRY")
                else:
                    raise LocatorError("NON_CONTIGUOUS_PDF_TEXT_GEOMETRY")
            prev = box


def _segments(matched: list[WordToken], page: fitz.Page) -> list[dict[str, Any]]:
    """Geometry in displayed (crop + rotation aware), top-left page pixels/points."""
    width, height = page.rect.width, page.rect.height
    per_line: dict[tuple[int, int], list[tuple[int, int, float, float, float, float]]] = {}
    for token in matched:
        for box in token.boxes:
            per_line.setdefault((box[0], box[1]), []).append(box)
    output = []
    for (block, line), boxes in per_line.items():
        # PyMuPDF extracts words in *unrotated visible crop coordinates*;
        # page.rotation_matrix transforms each word rect into rendered page.rect.
        transformed = [fitz.Rect(b[2], b[3], b[4], b[5]) * page.rotation_matrix for b in boxes]
        x0 = min(r.x0 for r in transformed); y0 = min(r.y0 for r in transformed)
        x1 = max(r.x1 for r in transformed); y1 = max(r.y1 for r in transformed)
        if not (-0.01 <= x0 < x1 <= width + .01 and -0.01 <= y0 < y1 <= height + .01):
            raise LocatorError("BBOX_OUTSIDE_VISIBLE_CROP")
        x0, y0 = max(0.0, x0), max(0.0, y0)
        x1, y1 = min(width, x1), min(height, y1)
        output.append({
            "block": block, "line": line,
            "rect_pdf_top_left": [round(v, 3) for v in (x0, y0, x1, y1)],
            "rect_normalized": [round(v, 7) for v in (x0/width, y0/height, x1/width, y1/height)],
        })
    return output


def locate_pdf_quote(pdf_path: str | Path, quote: str, expected_pdf_sha256: str,
                     claimed_page_hint: int | None = None) -> dict[str, Any]:
    data = Path(pdf_path).read_bytes()
    actual_sha = hashlib.sha256(data).hexdigest()
    if actual_sha != expected_pdf_sha256:
        raise LocatorError("SOURCE_PDF_SHA_MISMATCH")
    q = norm_tokens(quote)
    if not MIN_QUOTE_TOKENS <= len(q) <= MAX_QUOTE_TOKENS or sum(map(len, q)) < 20:
        raise LocatorError("QUOTE_TOO_SHORT_OR_TOO_LONG_FOR_PDF_LOCATION")
    matches: list[tuple[int, fitz.Page, list[WordToken]]] = []
    with fitz.open(stream=data, filetype="pdf") as pdf:
        for idx, page in enumerate(pdf):
            words = page_tokens(page)
            for i in range(len(words) - len(q) + 1):
                if all(words[i+j].text == q[j] for j in range(len(q))):
                    matches.append((idx+1, page, words[i:i+len(q)]))
                    if len(matches) > 1:
                        raise LocatorError("AMBIGUOUS_MULTIPLE_PDF_MATCHES")
        if not matches:
            raise LocatorError("PDF_QUOTE_NOT_FOUND_NO_EXACT_BBOX")
        number, page, matched = matches[0]
        _check_text_geometry(matched)
        segments = _segments(matched, page)
        payload = {
            "schema_version": "PDF_PAGE_BBOX/0.2",
            "match_status": "VERIFIED_UNIQUE_PDF_TEXT",
            "match_procedure": "PDF_WORD_SEQUENCE_NFKC_CASEFOLD_EXACT_V1",
            "page": number,
            "page_width": round(page.rect.width, 3), "page_height": round(page.rect.height, 3),
            "page_rotation": int(page.rotation),
            "page_cropbox": [round(v,3) for v in page.cropbox],
            "geometry_basis": "VISIBLE_CROP_ROTATION_AWARE",
            "coordinate_system": "PDF_PAGE_TOP_LEFT_POINTS_WITH_NORMALIZED_RECTANGLES",
            "rects": segments,
            "pdf_sha256": actual_sha,
            "quote_sha256": hashlib.sha256(quote.encode("utf-8")).hexdigest(),
            "claimed_page_hint": claimed_page_hint,
            "page_hint_agrees": claimed_page_hint is not None and claimed_page_hint == number,
            "bbox_is_semantic_equivalence": False,
        }
        return payload