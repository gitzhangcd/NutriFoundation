#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1.3 content-identity, provenance, completeness, and gate functions.

Identity verdicts come from PDF text regions and locatable spans.
SourceID never selects a verdict. Historical anomalies live in the
quarantine registry and bind to asset hash plus manifest revision.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import fitz

REGISTRY_PATH = Path(__file__).resolve().parent / "fixtures" / "quarantine_registry_r1_3.json"
NO_DOI_POLICY_ID = "NO_DOI_REQUIRES_TWO_SECONDARY_CREDENTIALS_V1"

LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.I)
DOI_FORMAT_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.I)
PMID_FORMAT_RE = re.compile(r"^\d{1,9}$")
REF_LINE = re.compile(
    r"^(?:references|bibliography|literature cited|works cited)\s*:?\s*$"
    r"|^(?:references|bibliography|literature cited|works cited)\s*:\s+\S",
    re.I,
)
BODY_LINE = re.compile(
    r"^(?:abstract|introduction|background|methods|materials and methods|results|discussion)\b",
    re.I,
)
VERSION_UNRESOLVED_RE = re.compile(
    r"author manuscript|accepted manuscript|uncorrected proof|\bpreprint\b",
    re.I,
)
COVER_ONLY_RE = re.compile(r"cover page only|only the cover was captured|contains only the cover", re.I)
TRUNCATION_RE = re.compile(r"article truncated|text is truncated|\[truncated\]|truncated before the bibliography", re.I)
PAGE_OF_RE = re.compile(r"\bpage\s+(\d+)\s+of\s+(\d+)\b", re.I)
ISSUER_PHRASES = (
    "national health commission",
    "world health organization",
    "centers for disease control",
    "american diabetes association",
    "american heart association",
    "ministry of health",
    "academy of nutrition",
)


def calculate_sha256(filepath: Path) -> str:
    digest = hashlib.sha256()
    with open(filepath, "rb") as handle:
        while chunk := handle.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text_canonical(text: str) -> str:
    if not text:
        return ""
    for src, dst in LIGATURES.items():
        text = text.replace(src, dst)
    text = text.replace("\u00ad", "")
    text = re.sub(r"[\r\n\t]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_title_canonical(text: str) -> str:
    text = normalize_text_canonical(text).lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", text).split())


def normalize_with_map(raw: str) -> tuple[str, list[int]]:
    """Normalize like normalize_title_canonical and map each output char to a raw index."""
    pairs: list[tuple[str, int]] = []
    for index, char in enumerate(raw):
        if char in LIGATURES:
            for expanded in LIGATURES[char]:
                pairs.append((expanded, index))
            continue
        if char == "\u00ad":
            continue
        lowered = char.lower()
        pairs.append((lowered if lowered.isalnum() else " ", index))
    output: list[str] = []
    indexes: list[int] = []
    previous_space = True
    for char, index in pairs:
        if char == " ":
            if previous_space:
                continue
            previous_space = True
        else:
            previous_space = False
        output.append(char)
        indexes.append(index)
    if output and output[-1] == " ":
        output.pop()
        indexes.pop()
    return "".join(output), indexes


def extract_dois_from_text(text: str) -> list[str]:
    return [match.group(0).rstrip(".;,") for match in DOI_RE.finditer(text)]


def semantic_verdict(value: str) -> str:
    if value == "PASS":
        return "CONFIRMED"
    return value or "UNKNOWN"


def _inactive_hold(source_id: str | None) -> dict:
    return {
        "active": False,
        "reason": "CONTENT_EVALUATOR_DOES_NOT_APPLY_SOURCE_ID_HOLD",
        "source_id": source_id,
        "expected_asset_sha256": None,
        "manifest_revision": None,
        "legacy_issue_derived": False,
    }


def _anchor(page: int, literal: str, span: list[int] | None, bbox, region: str, method: str) -> dict:
    return {
        "page": page,
        "literal_text": literal,
        "char_span": span if span is not None else [0, 0],
        "bbox": bbox,
        "region": region,
        "extraction_method": method,
    }


def _result(
    verdict: str,
    status: str,
    rule: str,
    anchor: dict,
    *,
    confidence: float,
    conflict_features: list,
    reason: str,
    source_id: str | None,
    policy_id: str | None = None,
    secondary_credentials: list | None = None,
) -> dict:
    return {
        "identity_verdict": verdict,
        "observed_identity_verdict": verdict,
        "administrative_hold": _inactive_hold(source_id),
        "identity_status": status,
        "match_rule": rule,
        "proof_anchor": anchor,
        "confidence": confidence,
        "anchor_page": anchor["page"],
        "literal_text": anchor["literal_text"],
        "conflict_features": conflict_features,
        "reason": reason,
        "policy_id": policy_id,
        "secondary_credentials": secondary_credentials or [],
    }


def _bbox_for(page, literal: str):
    line = next((item.strip() for item in literal.splitlines() if item.strip()), "")
    if not line:
        return None
    rects = page.search_for(line) or ([] if len(line) <= 48 else page.search_for(line[:48]))
    if not rects:
        return None
    rect = rects[0]
    return [round(rect.x0, 2), round(rect.y0, 2), round(rect.x1, 2), round(rect.y1, 2)]


def _locate(raw: str, phrase: str):
    if not phrase:
        return None
    normalized, indexes = normalize_with_map(raw)
    position = normalized.find(phrase)
    if position < 0 or not indexes:
        return None
    start = indexes[position]
    end = indexes[position + len(phrase) - 1] + 1
    return {"char_span": [start, end], "literal_text": raw[start:end]}


def _iter_regions(page_text: str, incoming: str):
    """Split one page into region slices. Returns (segments, outgoing_state)."""
    lines = page_text.splitlines(keepends=True)
    state = incoming
    buffer_start = 0
    buffer_state = state
    segments = []
    offset = 0

    def flush(end: int):
        nonlocal buffer_start
        if end > buffer_start:
            segments.append({
                "region": buffer_state,
                "start": buffer_start,
                "raw": page_text[buffer_start:end],
            })
            buffer_start = end

    for line in lines:
        stripped = line.strip()
        new_state = None
        if REF_LINE.match(stripped):
            new_state = "REFERENCES"
        elif state != "REFERENCES" and BODY_LINE.match(stripped):
            new_state = "BODY"
        if new_state and new_state != state:
            flush(offset)
            state = new_state
            buffer_state = state
            buffer_start = offset
        offset += len(line)
    flush(len(page_text))
    return segments, state


def _page_bundle(doc) -> list[dict]:
    state = "FRONT_MATTER"
    pages = []
    for page_index in range(len(doc)):
        raw = doc[page_index].get_text()
        segments, state = _iter_regions(raw, state)
        pages.append({"page": page_index + 1, "raw": raw, "segments": segments, "page_obj": doc[page_index]})
    return pages


def _hits(pages, phrase: str, region: str) -> list[dict]:
    found = []
    if not phrase:
        return found
    for page in pages:
        for segment in page["segments"]:
            if segment["region"] != region:
                continue
            located = _locate(segment["raw"], phrase)
            if not located:
                continue
            start = segment["start"] + located["char_span"][0]
            end = segment["start"] + located["char_span"][1]
            literal = page["raw"][start:end]
            found.append({
                "page": page["page"],
                "region": region,
                "char_span": [start, end],
                "literal_text": literal,
                "bbox": _bbox_for(page["page_obj"], literal),
                "page_obj": page["page_obj"],
            })
    return found


def _doi_hits(pages) -> list[dict]:
    found = []
    for page in pages:
        for match in DOI_RE.finditer(page["raw"]):
            doi = match.group(0).rstrip(".;,").lower()
            region = "BODY"
            for segment in page["segments"]:
                if segment["start"] <= match.start() < segment["start"] + len(segment["raw"]):
                    region = segment["region"]
                    break
            literal = page["raw"][match.start():match.end()]
            found.append({
                "doi": doi,
                "page": page["page"],
                "region": region,
                "char_span": [match.start(), match.end()],
                "literal_text": literal,
                "bbox": _bbox_for(page["page_obj"], literal),
            })
    return found


def _front_text(pages) -> tuple[str, str]:
    chunks = []
    for page in pages:
        for segment in page["segments"]:
            if segment["region"] == "FRONT_MATTER":
                chunks.append(segment["raw"])
    raw = "\n".join(chunks)
    return raw, normalize_title_canonical(raw)


def _token_conflict(expected: str, observed: str) -> bool:
    if expected == observed:
        return False
    shorter, longer = sorted((expected, observed), key=len)
    if longer.startswith(shorter) and len(longer) - len(shorter) <= 4:
        return False
    return True


def _prefix_divergence(front_norm: str, expected_words: list[str]):
    if len(expected_words) < 7:
        return None
    words = front_norm.split()
    if len(words) < 6:
        return None
    for length in range(len(expected_words) - 1, 5, -1):
        needle = expected_words[:length]
        for index in range(0, len(words) - length + 1):
            if words[index:index + length] != needle:
                continue
            observed_next = words[index + length] if index + length < len(words) else ""
            expected_next = expected_words[length]
            if not observed_next or not _token_conflict(expected_next, observed_next):
                continue
            return {
                "matched_words": length,
                "expected_next": expected_next,
                "observed_next": observed_next,
                "observed_phrase": " ".join(words[index:index + length + 1]),
            }
    return None


def _secondary_credentials(front_raw: str, front_norm: str, expected_pmid: str, expected_journal: str, expected_date: str, expected_publisher: str) -> list[str]:
    found = []
    if expected_pmid and expected_pmid in front_raw:
        found.append("PMID")
    journal = normalize_title_canonical(expected_journal)
    if journal and journal in front_norm:
        found.append("JOURNAL")
    year_match = re.search(r"(?:19|20)\d{2}", expected_date or "")
    if year_match and year_match.group(0) in front_raw:
        found.append("PUBLICATION_YEAR")
    publisher = normalize_title_canonical(expected_publisher)
    if publisher and publisher in front_norm:
        found.append("ISSUING_BODY")
    elif any(phrase in front_norm for phrase in ISSUER_PHRASES):
        found.append("ISSUING_BODY")
    if re.search(r"\b(version|edition)\b|\bv\s*\d+(?:\.\d+)+\b", front_raw, re.I):
        found.append("VERSION")
    return found


def _window_ratio(front_norm: str, expected: str) -> float:
    if len(expected) < 12 or len(front_norm) < 12:
        return 0.0
    import difflib
    width = min(len(front_norm), len(expected) + 30)
    step = max(12, width // 3)
    best = 0.0
    for index in range(0, max(1, len(front_norm) - width + 1), step):
        window = front_norm[index:index + width]
        best = max(best, difflib.SequenceMatcher(None, expected, window[:len(expected)]).ratio())
    return best


def evaluate_pdf_identity_canonical(
    pdf_path: Path,
    expected_title: str,
    expected_doi: str,
    expected_pmid: str,
    source_id: str | None = None,
    expected_journal: str = "",
    expected_date: str = "",
    expected_publisher: str = "",
) -> dict:
    """Content-only identity decision. source_id is ignored for the verdict."""
    pdf_path = Path(pdf_path)
    empty = _anchor(0, "", [0, 0], None, "NONE", "NO_PAGE")
    if not pdf_path.exists() or not pdf_path.is_file():
        return _result(
            "HOLD", "FILE_NOT_FOUND", "FILE_EXISTENCE_CHECK", empty,
            confidence=0.0, conflict_features=["FILE_MISSING_ON_DISK"],
            reason=f"File does not exist: {pdf_path}", source_id=source_id,
        )
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        return _result(
            "HOLD", "CONTAINER_ERROR", "CONTAINER_INTEGRITY_CHECK", empty,
            confidence=0.0, conflict_features=[f"CANNOT_OPEN_PDF: {exc}"],
            reason=f"Corrupt PDF container: {exc}", source_id=source_id,
        )
    try:
        return _evaluate_open_document(
            doc, expected_title, expected_doi, expected_pmid, source_id,
            expected_journal, expected_date, expected_publisher,
        )
    finally:
        doc.close()


def _evaluate_open_document(doc, expected_title, expected_doi, expected_pmid, source_id, expected_journal, expected_date, expected_publisher):
    title_norm = normalize_title_canonical(expected_title)
    title_words = title_norm.split()
    doi_expected = (expected_doi or "").strip().lower().rstrip(".;,")
    pmid = (expected_pmid or "").strip()
    pages = _page_bundle(doc)
    if not pages:
        anchor = _anchor(0, "", [0, 0], None, "NONE", "EMPTY_DOCUMENT")
        return _result("HOLD", "INSUFFICIENT_EVIDENCE", "EMPTY_DOCUMENT", anchor, confidence=0.0, conflict_features=["NO_PAGES"], reason="PDF has no pages.", source_id=source_id)

    front_raw, front_norm = _front_text(pages)
    title_front = _hits(pages, title_norm, "FRONT_MATTER")
    title_refs = _hits(pages, title_norm, "REFERENCES")
    title_body = _hits(pages, title_norm, "BODY")
    dois = _doi_hits(pages)
    front_dois = [item for item in dois if item["region"] == "FRONT_MATTER"]
    ref_dois = [item for item in dois if item["region"] == "REFERENCES"]
    expected_front = [item for item in front_dois if item["doi"] == doi_expected] if doi_expected else []
    expected_refs = [item for item in ref_dois if item["doi"] == doi_expected] if doi_expected else []
    first_front_doi = front_dois[0] if front_dois else None
    cover_conflict = bool(
        doi_expected and first_front_doi and first_front_doi["doi"] != doi_expected and not expected_front
    )

    def pack(hit, region):
        return _anchor(hit["page"], hit["literal_text"], hit["char_span"], hit["bbox"], region, "PYMUPDF_GET_TEXT_CHAR_SPAN_WITH_NORM_MAP")

    if VERSION_UNRESOLVED_RE.search(front_raw) and (expected_front or title_front):
        hit = title_front[0] if title_front else expected_front[0]
        return _result(
            "HOLD", "VERSION_IDENTITY_UNRESOLVED", "VERSION_PHRASE_WITHOUT_VERSION_OF_RECORD",
            pack(hit, "FRONT_MATTER"),
            confidence=0.45, conflict_features=["VERSION_IDENTITY_UNRESOLVED"],
            reason="Front matter identifies an author manuscript, preprint, or uncorrected proof.",
            source_id=source_id,
        )

    if title_front and cover_conflict:
        return _result(
            "HOLD", "COVER_DOI_CONFLICT", "COVER_DOI_CONFLICTS_WITH_EXPECTED_DOI", pack(first_front_doi, "FRONT_MATTER"),
            confidence=0.2,
            conflict_features=[f"COVER_DOI:{first_front_doi['doi']}", f"EXPECTED_DOI:{doi_expected}"],
            reason="Front-matter DOI disagrees with the expected DOI.",
            source_id=source_id,
        )

    if title_front and doi_expected and expected_front and not cover_conflict:
        hit = title_front[0]
        return _result(
            "CONFIRMED", "CONFIRMED_TITLE_AND_DOI_GROUNDED", "FULL_TITLE_AND_DOI_IN_ARTICLE_IDENTITY_REGION",
            pack(hit, "FRONT_MATTER"),
            confidence=1.0, conflict_features=[],
            reason="Full title and expected DOI are both in the article-identity region.",
            source_id=source_id,
        )

    if title_front and not doi_expected:
        if VERSION_UNRESOLVED_RE.search(front_raw):
            return _result(
                "HOLD", "VERSION_IDENTITY_UNRESOLVED", "VERSION_PHRASE_WITHOUT_PINNING_DOI",
                pack(title_front[0], "FRONT_MATTER"),
                confidence=0.4, conflict_features=["VERSION_IDENTITY_UNRESOLVED"],
                reason="Front matter marks an unsettled version and no DOI pins it.",
                source_id=source_id,
            )
        credentials = _secondary_credentials(front_raw, front_norm, pmid, expected_journal, expected_date, expected_publisher)
        if len(credentials) >= 2:
            return _result(
                "CONFIRMED", "CONFIRMED_TITLE_NO_DOI_REQUIRED", "NO_DOI_SECONDARY_CREDENTIAL_POLICY",
                pack(title_front[0], "FRONT_MATTER"),
                confidence=0.95, conflict_features=[],
                reason="No DOI is expected. Full title plus two secondary credentials support confirmation.",
                source_id=source_id, policy_id=NO_DOI_POLICY_ID, secondary_credentials=credentials,
            )
        return _result(
            "PROBABLE", "PROBABLE_TITLE_WITHOUT_SECONDARY_CREDENTIALS", "TITLE_ONLY_IS_NOT_CONFIRMATION",
            pack(title_front[0], "FRONT_MATTER"),
            confidence=0.7, conflict_features=["SECONDARY_CREDENTIALS_BELOW_POLICY"],
            reason="Full title is present, but fewer than two secondary credentials were found.",
            source_id=source_id, policy_id=NO_DOI_POLICY_ID, secondary_credentials=credentials,
        )

    if title_front and doi_expected and not expected_front:
        return _result(
            "PROBABLE", "PROBABLE_TITLE_DOI_NOT_LOCATED", "FULL_TITLE_WITHOUT_FRONT_MATTER_DOI",
            pack(title_front[0], "FRONT_MATTER"),
            confidence=0.75, conflict_features=["DOI_NOT_IN_ARTICLE_IDENTITY_REGION"],
            reason="Full title is in front matter, but the expected DOI was not located there.",
            source_id=source_id,
        )

    if (title_refs or expected_refs) and not title_front:
        hit = title_refs[0] if title_refs else expected_refs[0]
        both = bool(title_refs and expected_refs)
        status = "REFERENCE_REGION_NOT_DOCUMENT_IDENTITY" if both or title_refs else "DOI_IN_REFERENCES_ONLY"
        rule = "TITLE_AND_DOI_IN_REFERENCES_ONLY" if both or (title_refs and expected_refs) else "NEGATIVE_CONTROL_NC01_DOI_IN_REFERENCES"
        features = ["DOI_FOUND_ONLY_IN_BIBLIOGRAPHY"] if status == "DOI_IN_REFERENCES_ONLY" else ["TITLE_OR_DOI_FOUND_IN_REFERENCES"]
        if status == "DOI_IN_REFERENCES_ONLY":
            features = ["DOI_FOUND_ONLY_IN_BIBLIOGRAPHY", "TITLE_SIMILARITY_DEFICIENT"]
        return _result(
            "HOLD", status, rule, pack(hit, hit["region"]),
            confidence=0.1, conflict_features=features,
            reason="A reference-list occurrence is not the document's own title or DOI.",
            source_id=source_id,
        )

    divergence = _prefix_divergence(front_norm, title_words)
    if divergence:
        anchor = None
        for page in pages:
            for segment in page["segments"]:
                if segment["region"] != "FRONT_MATTER":
                    continue
                located = _locate(segment["raw"], divergence["observed_phrase"])
                if not located:
                    continue
                start = segment["start"] + located["char_span"][0]
                end = segment["start"] + located["char_span"][1]
                literal = page["raw"][start:end]
                anchor = _anchor(page["page"], literal, [start, end], _bbox_for(page["page_obj"], literal), "FRONT_MATTER", "PYMUPDF_GET_TEXT_CHAR_SPAN_WITH_NORM_MAP")
                break
            if anchor:
                break
        if anchor is None:
            raw_page = pages[0]["raw"]
            end = min(180, len(raw_page))
            anchor = _anchor(1, raw_page[:end], [0, end], None, "FRONT_MATTER", "PAGE_TEXT_PREFIX_SPAN")
        return _result(
            "HOLD", "TITLE_PREFIX_ONLY_DIVERGENT", "PREFIX_MATCH_DOES_NOT_CONFIRM_FULL_TITLE", anchor,
            confidence=0.3,
            conflict_features=["TITLE_PREFIX_DIVERGENCE", f"OBSERVED_NEXT:{divergence['observed_next']}"],
            reason="Only a title prefix matches; the continuation is a different title.",
            source_id=source_id,
        )

    if cover_conflict:
        return _result(
            "HOLD", "CONFLICTING_DOI_DETECTED", "COVER_DOI_CONFLICTS_WITH_EXPECTED_DOI",
            pack(first_front_doi, "FRONT_MATTER"),
            confidence=0.2,
            conflict_features=[f"COVER_DOI:{first_front_doi['doi']}", f"EXPECTED_DOI:{doi_expected}"],
            reason="The cover DOI belongs to a different work and the expected title was not found.",
            source_id=source_id,
        )

    if title_body and not title_front:
        return _result(
            "HOLD", "TITLE_ONLY_IN_BODY_CITATION", "BODY_CITATION_IS_NOT_DOCUMENT_TITLE",
            pack(title_body[0], "BODY"),
            confidence=0.2, conflict_features=["TITLE_FOUND_ONLY_AS_BODY_CITATION"],
            reason="The expected title occurs in the body, not in the document title region.",
            source_id=source_id,
        )

    ratio = _window_ratio(front_norm, title_norm)
    raw_page = pages[0]["raw"]
    probe_end = min(180, len(raw_page))
    probe = raw_page[:probe_end]
    anchor = _anchor(
        1, probe, [0, probe_end], _bbox_for(pages[0]["page_obj"], probe.splitlines()[0] if probe else "") if probe else None,
        "FRONT_MATTER" if front_raw else "BODY", "PAGE_TEXT_PREFIX_SPAN",
    )
    if ratio < 0.68:
        return _result(
            "HOLD", "DISPERSED_KEYWORDS_REJECTED", "NEGATIVE_CONTROL_NC02_DISPERSED_KEYWORDS", anchor,
            confidence=ratio, conflict_features=["TITLE_PHRASE_NOT_COHERENT", "MAX_SLIDING_WINDOW_SIMILARITY_LOW"],
            reason="No coherent full-title span was found.",
            source_id=source_id,
        )
    if ratio >= 0.92:
        return _result(
            "PROBABLE", "PROBABLE_HIGH_WINDOW_SIMILARITY", "FULL_TITLE_SIMILAR_BUT_NOT_EXACT", anchor,
            confidence=ratio, conflict_features=["TITLE_NOT_EXACT"],
            reason="Front matter is similar to the full title but not an exact span.",
            source_id=source_id,
        )
    return _result(
        "HOLD", "INSUFFICIENT_EVIDENCE", "CANONICAL_FALLTHROUGH_HOLD", anchor,
        confidence=ratio, conflict_features=["EVIDENCE_BELOW_CONFIRMATION_THRESHOLD"],
        reason="Identity evidence does not meet confirmation rules.",
        source_id=source_id,
    )


def replay_proof_anchor(pdf_path: Path, anchor: dict) -> dict:
    pdf_path = Path(pdf_path)
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        return {"ok": False, "reason": f"CANNOT_OPEN:{exc}", "observed_literal_text": ""}
    try:
        page_no = int(anchor.get("page") or 0)
        if page_no < 1 or page_no > len(doc):
            return {"ok": False, "reason": "PAGE_OUT_OF_RANGE", "observed_literal_text": ""}
        raw = doc[page_no - 1].get_text()
        span = anchor.get("char_span") or [0, 0]
        start, end = int(span[0]), int(span[1])
        if start < 0 or end > len(raw) or start >= end:
            return {"ok": False, "reason": "SPAN_OUT_OF_RANGE", "observed_literal_text": ""}
        observed = raw[start:end]
        ok = observed == anchor.get("literal_text")
        return {"ok": ok, "reason": "MATCH" if ok else "LITERAL_MISMATCH", "observed_literal_text": observed}
    finally:
        doc.close()


def resolve_administrative_hold(source_id: str, observed_asset_sha256: str, manifest_revision: str | None = None, registry: dict | None = None) -> dict:
    if registry is None:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    revision = manifest_revision or registry.get("manifest_revision")
    for entry in registry.get("entries", []):
        if entry.get("source_id") != source_id:
            continue
        hash_ok = (entry.get("expected_asset_sha256") or "").lower() == (observed_asset_sha256 or "").lower()
        revision_ok = entry.get("manifest_revision") == revision
        if hash_ok and revision_ok:
            return {
                "active": True,
                "reason": "HASH_AND_MANIFEST_REVISION_MATCH",
                "source_id": source_id,
                "expected_asset_sha256": entry.get("expected_asset_sha256"),
                "manifest_revision": entry.get("manifest_revision"),
                "hold_code": entry.get("hold_code"),
                "legacy_issue_derived": True,
                "legacy_note": entry.get("legacy_note"),
            }
        return {
            "active": False,
            "reason": "ASSET_HASH_DOES_NOT_MATCH_QUARANTINE_ENTRY",
            "source_id": source_id,
            "expected_asset_sha256": entry.get("expected_asset_sha256"),
            "observed_asset_sha256": observed_asset_sha256,
            "manifest_revision": revision,
            "legacy_issue_derived": True,
        }
    return {
        "active": False,
        "reason": "SOURCE_ID_NOT_IN_QUARANTINE_REGISTRY",
        "source_id": source_id,
        "legacy_issue_derived": False,
    }


def evaluate_acquisition_provenance(reported_channel: str | None, download_log: dict | None, observed_asset_sha256: str | None) -> dict:
    required = ["source_url", "retrieved_at", "asset_sha256", "record_signature"]
    if not isinstance(download_log, dict):
        return {
            "acquisition_provenance": "EVIDENCE_PENDING" if reported_channel else "UNVERIFIED",
            "triggered_rules": ["ACQUISITION_CHANNEL_IS_NOT_PROVENANCE"],
            "missing_fields": required,
            "reported_channel": reported_channel,
            "hash_matches_log": False,
            "reason": "A channel string is not a download log.",
        }
    missing = [field for field in required if not download_log.get(field)]
    url = str(download_log.get("source_url") or "")
    url_ok = url.startswith("http://") or url.startswith("https://")
    if url and not url_ok:
        missing.append("source_url_scheme")
    hash_ok = (download_log.get("asset_sha256") or "").lower() == (observed_asset_sha256 or "").lower() and bool(observed_asset_sha256)
    if not hash_ok:
        missing.append("asset_sha256_mismatch")
    if not missing and url_ok and hash_ok:
        return {
            "acquisition_provenance": "VERIFIED",
            "triggered_rules": ["PROVENANCE_URL_TIME_SIGNATURE_HASH_MATCH"],
            "missing_fields": [],
            "reported_channel": reported_channel,
            "hash_matches_log": True,
            "reason": "Log binds source URL, retrieval time, signature, and asset hash.",
        }
    return {
        "acquisition_provenance": "EVIDENCE_PENDING",
        "triggered_rules": ["PROVENANCE_LOG_INCOMPLETE"],
        "missing_fields": missing,
        "reported_channel": reported_channel,
        "hash_matches_log": hash_ok,
        "reason": "Download log is present but does not satisfy VERIFIED requirements.",
    }


def evaluate_content_completeness(pdf_path: Path) -> dict:
    pdf_path = Path(pdf_path)
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        return {
            "content_completeness": "UNRESOLVED",
            "completeness_scope": "UNREADABLE_CONTAINER",
            "evidence": f"Cannot open PDF: {exc}",
            "triggered_rules": ["CONTAINER_UNREADABLE"],
        }
    try:
        page_count = len(doc)
        if page_count == 0:
            return {
                "content_completeness": "UNRESOLVED",
                "completeness_scope": "NO_PAGES",
                "evidence": "PDF opened with zero pages.",
                "triggered_rules": ["NO_PAGES"],
            }
        indexes = sorted({0, page_count // 2, page_count - 1})
        samples = [(index + 1, doc[index].get_text()) for index in indexes]
        blob = "\n".join(text for _, text in samples)
        if COVER_ONLY_RE.search(blob):
            return {
                "content_completeness": "PARTIAL",
                "completeness_scope": "COVER_ONLY",
                "evidence": "Sampled text states the file is cover-only.",
                "triggered_rules": ["COVER_ONLY_SIGNAL"],
                "page_count": page_count,
            }
        if TRUNCATION_RE.search(blob):
            return {
                "content_completeness": "PARTIAL",
                "completeness_scope": "BODY_TEXT",
                "evidence": "Sampled text states the article is truncated.",
                "triggered_rules": ["TRUNCATION_SIGNAL"],
                "page_count": page_count,
            }
        for page_no, text in samples:
            for match in PAGE_OF_RE.finditer(text):
                declared = int(match.group(2))
                if declared > page_count:
                    return {
                        "content_completeness": "PARTIAL",
                        "completeness_scope": "BODY_TEXT",
                        "evidence": f"Page {page_no} declares page count {declared} but the file has {page_count} pages.",
                        "triggered_rules": ["DECLARED_PAGE_COUNT_EXCEEDS_FILE"],
                        "page_count": page_count,
                    }
        has_references = any(REF_LINE.match(line.strip()) for _, text in samples for line in text.splitlines())
        if not has_references and page_count > 2:
            # References often sit on the last pages; scan the final two pages' headings only.
            for index in range(max(0, page_count - 2), page_count):
                if any(REF_LINE.match(line.strip()) for line in doc[index].get_text().splitlines()):
                    has_references = True
                    break
        if has_references:
            return {
                "content_completeness": "COMPLETE",
                "completeness_scope": "BODY_THROUGH_BIBLIOGRAPHY_TABLES_AND_APPENDICES_NOT_ASSESSED",
                "evidence": "A references heading was observed and no truncation or missing-page signal was found. Tables and appendices were not assessed.",
                "triggered_rules": ["REFERENCES_HEADING_OBSERVED", "SUPPLEMENTS_NOT_ASSESSED"],
                "page_count": page_count,
            }
        return {
            "content_completeness": "NOT_ASSESSED",
            "completeness_scope": "FULL_WORK_INCLUDING_TABLES_AND_APPENDICES",
            "evidence": "No positive completeness dossier and no defect signal. Page count is not treated as completeness.",
            "triggered_rules": ["PAGE_COUNT_IS_NOT_COMPLETENESS"],
            "page_count": page_count,
        }
    finally:
        doc.close()


def evaluate_rights_posture() -> dict:
    return {
        "rights_legal_status": "NOT_ASSESSED",
        "redistribution_permission": "NO_PER_WORK_REDISTRIBUTION_GRANT_ON_FILE",
        "project_use_policy": "INTERNAL_LOCAL_RESEARCH_ONLY",
        "project_policy_check": "APPLIED",
        "legal_verification_completed": False,
        "triggered_rules": ["G4_PROJECT_POLICY_IS_NOT_LEGAL_VERIFICATION"],
        "basis": "Internal local research is allowed by project policy. That policy is not a per-work legal opinion and does not grant redistribution.",
    }


def evaluate_manifest_integrity(records: list[dict], research_relationships: list[dict] | None = None) -> dict:
    relationships = research_relationships or []
    relation_by_doi = {}
    for item in relationships:
        relation_by_doi[(item.get("doi") or "").strip().lower()] = item
    source_ids = [record.get("source_id") for record in records]
    duplicate_ids = sorted([sid for sid, count in Counter(source_ids).items() if sid and count > 1])
    doi_members: dict[str, list[str]] = {}
    pmid_members: dict[str, list[str]] = {}
    invalid_dois = []
    invalid_pmids = []
    doi_absent = []
    for record in records:
        sid = record.get("source_id")
        identifiers = record.get("identifiers") or {}
        doi = (identifiers.get("doi") or "").strip()
        pmid = (identifiers.get("pmid") or "").strip()
        if doi:
            if not DOI_FORMAT_RE.match(doi):
                invalid_dois.append({"source_id": sid, "doi": doi})
            doi_members.setdefault(doi.lower(), []).append(sid)
        else:
            doi_absent.append(sid)
        if pmid:
            if not PMID_FORMAT_RE.match(pmid):
                invalid_pmids.append({"source_id": sid, "pmid": pmid})
            pmid_members.setdefault(pmid, []).append(sid)
        elif pmid == "" and "pmid" in identifiers:
            pass
    triggered = []
    if duplicate_ids:
        triggered.append({"rule_id": "G0_SOURCE_ID_DUPLICATE", "source_ids": duplicate_ids})
    if invalid_dois:
        triggered.append({"rule_id": "G0_DOI_FORMAT_INVALID", "items": invalid_dois})
    if invalid_pmids:
        triggered.append({"rule_id": "G0_PMID_FORMAT_INVALID", "items": invalid_pmids})
    stated = []
    unstated = []
    for doi, members in sorted(doi_members.items()):
        if len(members) < 2:
            continue
        relation = relation_by_doi.get(doi)
        if relation and relation.get("relation") in {"correction", "companion", "version", "erratum"}:
            stated.append({"doi": doi, "relation": relation["relation"], "members": members})
        else:
            unstated.append({"doi": doi, "members": members})
            triggered.append({"rule_id": "G0_DUPLICATE_DOI_RELATIONSHIP_UNSTATED", "doi": doi, "members": members})
    for pmid, members in pmid_members.items():
        if len(members) > 1:
            triggered.append({"rule_id": "G0_DUPLICATE_PMID_REVIEW", "pmid": pmid, "members": members})
    verdict = "PASS" if not triggered else "HOLD"
    return {
        "verdict": verdict,
        "triggered_rules": triggered,
        "source_count": len(records),
        "unique_source_ids": len(set(source_ids)),
        "duplicate_source_ids": duplicate_ids,
        "doi_absent_count": len(doi_absent),
        "doi_absent_source_ids": doi_absent,
        "invalid_doi_count": len(invalid_dois),
        "invalid_pmid_count": len(invalid_pmids),
        "research_relationships": stated,
        "duplicate_doi_unconditional_anomalies": unstated,
        "reason": (
            f"Computed over {len(records)} records: unique_source_ids={len(set(source_ids))}, "
            f"invalid_dois={len(invalid_dois)}, invalid_pmids={len(invalid_pmids)}, "
            f"duplicate_doi_with_relationship={len(stated)}, duplicate_doi_unstated={len(unstated)}, "
            f"doi_absent={len(doi_absent)}."
        ),
    }


def aggregate_identity_gate(rows: list[dict]) -> dict:
    counts = Counter(row.get("identity_verdict") for row in rows)
    completeness = Counter(row.get("content_completeness") for row in rows)
    triggered = []
    total = len(rows)
    if counts.get("CONFIRMED", 0) != total:
        triggered.append({
            "rule_id": "G3_NOT_ALL_SOURCES_CONFIRMED",
            "confirmed": counts.get("CONFIRMED", 0),
            "probable": counts.get("PROBABLE", 0),
            "hold": counts.get("HOLD", 0),
            "mismatch": counts.get("MISMATCH", 0),
            "total": total,
        })
    admin = sum(1 for row in rows if (row.get("administrative_hold") or {}).get("active"))
    if admin:
        triggered.append({"rule_id": "G3_HASH_BOUND_ADMINISTRATIVE_HOLD", "count": admin})
    if completeness.get("COMPLETE", 0) != total:
        triggered.append({"rule_id": "G3_CONTENT_COMPLETENESS_NOT_UNIVERSAL", "by_status": dict(completeness)})
    return {
        "verdict": "PASS" if not triggered else "HOLD",
        "triggered_rules": triggered,
        "counts": dict(counts),
        "completeness_counts": dict(completeness),
    }


def aggregate_provenance_gate(rows: list[dict]) -> dict:
    counts = Counter(row.get("acquisition_provenance") for row in rows)
    triggered = []
    if counts.get("VERIFIED", 0) != len(rows):
        triggered.append({
            "rule_id": "G4_VERIFIED_REQUIRES_URL_LOG_TIME_SIGNATURE_AND_HASH",
            "verified": counts.get("VERIFIED", 0),
            "evidence_pending": counts.get("EVIDENCE_PENDING", 0),
            "unverified": counts.get("UNVERIFIED", 0),
            "total": len(rows),
        })
    return {"verdict": "PASS" if not triggered else "HOLD", "triggered_rules": triggered, "counts": dict(counts)}


def aggregate_rights_gate(rows: list[dict]) -> dict:
    unverified_legal = sum(1 for row in rows if not row.get("legal_verification_completed"))
    triggered = []
    if unverified_legal:
        triggered.append({
            "rule_id": "G4_PROJECT_POLICY_IS_NOT_LEGAL_VERIFICATION",
            "legal_status_not_assessed": unverified_legal,
            "project_policy_applied": sum(1 for row in rows if row.get("project_policy_check") == "APPLIED"),
            "total": len(rows),
        })
    return {"verdict": "PASS" if not triggered else "HOLD", "triggered_rules": triggered}


def aggregate_study_type_gate(rows: list[dict], human_completed: int) -> dict:
    legacy = sum(1 for row in rows if row.get("legacy_issue_derived"))
    triggered = [{
        "rule_id": "G5_LEGACY_LIST_IS_NOT_A_NEW_MEASUREMENT",
        "legacy_issue_derived_count": legacy,
        "provisional_count": sum(1 for row in rows if row.get("study_type_qualification") == "PROVISIONAL"),
        "human_review_completed": human_completed,
        "total": len(rows),
    }]
    if human_completed == len(rows) and legacy == 0:
        triggered = []
    return {"verdict": "PASS" if not triggered else "HOLD", "triggered_rules": triggered}
