"""Local-only authorized source-ingestion and cell-preserving table parser.

Rejects network fetching, keeps originals private, never declares full scientific fidelity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

import fitz

ID_RE = re.compile(r"^CAND-G100-\d{3}$")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")


class TableReader(HTMLParser):
    """Recover table cell boundaries from native HTML/JATS-derived HTML, not flat PMC text."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._table = None
        self._row = None
        self._cell = None
        self._nested = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if self._table is not None:
                raise ValueError("NESTED_TABLE_NOT_SUPPORTED")
            self._table = {"rows": [], "caption": "", "cell_spans": []}
        elif self._table is not None and tag == "tr":
            self._row = []
        elif self._table is not None and tag in ("td", "th") and self._row is not None:
            self._cell = {"tag": tag, "text": [], "attributes": dict(attrs)}

    def handle_data(self, data):
        if self._cell is not None:
            self._cell["text"].append(data)
        elif self._table is not None and self._row is None:
            self._table["caption"] += data

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            txt = " ".join("".join(self._cell["text"]).split())
            att = self._cell["attributes"]
            self._row.append({"text": txt, "rowspan": att.get("rowspan", "1"),
                              "colspan": att.get("colspan", "1"), "is_header": tag == "th"})
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self._table["rows"].append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._cell is not None or self._row is not None:
                raise ValueError("UNBALANCED_NATIVE_TABLE")
            self.tables.append(self._table)
            self._table = None


def parse_native_tables(html_text: str):
    parser = TableReader()
    parser.feed(html_text)
    parser.close()
    if parser._table is not None:
        raise ValueError("TABLE_NOT_CLOSED")
    return parser.tables


def check_reference_cells(tables: list, expected: list[dict]):
    """Compare specific row/cell exact text and preserve table/row/column address.
    A passing sampled value check is NOT comprehensive figure/PDF parity.
    """
    results = []
    for cell in expected:
        tid, rid, cid = cell["table"], cell["row"], cell["col"]
        if any(not isinstance(n, int) or n < 0 for n in (tid, rid, cid)):
            raise ValueError("INVALID_CELL_LOCATOR")
        try:
            actual = tables[tid]["rows"][rid][cid]["text"]
        except (IndexError, KeyError):
            actual = None
        results.append({"locator": {"table": tid, "row": rid, "col": cid},
                        "expected": cell["expected"], "observed": actual,
                        "exact_match": actual == cell["expected"]})
    return {"checked_cells": len(results), "matched": sum(x["exact_match"] for x in results),
            "status": "SAMPLED_NATIVE_HTML_CELL_MATCH" if results and all(x["exact_match"] for x in results)
                      else "FAILED_OR_NO_CHECK", "full_table_parity": "NOT_VERIFIED",
            "results": results}


def inspect_local_pdf(source_id: str, original: Path, private_dir: Path,
                      source_uri: str, rights_attestation: str):
    """Hash and inspect a *user-provided lawful local* PDF. Never download or publish it."""
    if not ID_RE.fullmatch(source_id):
        raise ValueError("INVALID_SOURCE_ID")
    if rights_attestation != "AUTHORIZED_LOCAL_RESEARCH_USE":
        raise ValueError("SOURCE_RIGHTS_ATTESTATION_REQUIRED")
    original_input = Path(original)
    if original_input.is_symlink():
        raise ValueError("SYMLINK_NOT_ALLOWED")
    original = original_input.resolve(strict=True)
    private_dir = Path(private_dir).resolve(strict=True)
    if not original.is_file() or original.suffix.lower() != ".pdf":
        raise ValueError("SOURCE_NOT_A_LOCAL_PDF")
    if not source_uri.startswith("https://") or not any(
        source_uri.startswith(p) for p in (
            "https://pmc.ncbi.nlm.nih.gov/articles/",
            "https://www.nature.com/articles/",
            "https://www.bmj.com/",
            "https://www.andeal.org/",
            "https://academic.oup.com/",
        )
    ):
        raise ValueError("AUTHORITY_URL_NOT_ALLOWLISTED")
    binary = original.read_bytes()
    if not binary.startswith(b"%PDF-"):
        raise ValueError("PDF_SIGNATURE_INVALID")
    doc = fitz.open(stream=binary, filetype="pdf")
    if doc.is_encrypted:
        raise ValueError("ENCRYPTED_SOURCE_NOT_ACCEPTED")
    pages = len(doc)
    images = sum(len(doc[p].get_images(full=True)) for p in range(pages))
    text_pages = [len(doc[p].get_text()) for p in range(pages)]
    return {
        "candidate_id": source_id,
        "source_uri": source_uri,
        "original_sha256": hashlib.sha256(binary).hexdigest(),
        "original_bytes": len(binary),
        "original_pdf_pages": pages,
        "pdf_image_occurrences": images,
        "pdf_page_text_characters": text_pages,
        "original_storage": "PRIVATE_LOCAL_FILE_NOT_UPLOADED_TO_PUBLIC_GITHUB",
        "visual_pages_manual_check": "NOT_VERIFIED",
        "table_cell_parity": "NOT_VERIFIED",
        "supplemental_files": "NOT_VERIFIED",
        "source_rights": rights_attestation,
        "scientific_qualification_L4": "HOLD_EXPERT_ADJUDICATION",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--original-pdf", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--rights-attestation", required=True)
    parser.add_argument("--output-name", default="pdf_receipt.json")
    args = parser.parse_args()
    private = args.private_dir.resolve(strict=True)
    if private.stat().st_mode & 0o077:
        raise SystemExit("PRIVATE_DIRECTORY_MUST_EXCLUDE_GROUP_AND_OTHER")
    filename = Path(args.output_name)
    if filename.name != args.output_name or not filename.name.endswith(".json"):
        raise SystemExit("INVALID_OUTPUT_NAME")
    report = inspect_local_pdf(args.candidate_id, args.original_pdf, private,
                               args.source_url, args.rights_attestation)
    target = private / args.output_name
    with target.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"SOURCE_PDF_RECEIPT_ONLY {target}  sha256={report['original_sha256']}")


if __name__ == "__main__":
    main()
