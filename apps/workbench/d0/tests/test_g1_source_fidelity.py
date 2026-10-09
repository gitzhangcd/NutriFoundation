from pathlib import Path
import sys

import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from g1_source_fidelity import parse_native_tables, check_reference_cells, inspect_local_pdf


def test_html_table_preserves_cell_boundaries():
    html = """<table><caption>Baseline Characteristics</caption>
    <thead><tr><th>Characteristic</th><th>eTRF</th><th>mTRF</th><th>control</th></tr></thead>
    <tbody><tr><td>No.</td><td>28</td><td>26</td><td>28</td></tr>
    <tr><td>Age (SD), years</td><td>28.68 (9.707)</td>
    <td>31.08 (8.438)</td><td>33.57 (11.6)</td></tr></tbody></table>"""
    tables = parse_native_tables(html)
    assert len(tables) == 1
    assert tables[0]["rows"][1][2]["text"] == "26"
    values = [{"table": 0, "row": 1, "col": 1, "expected": "28"},
              {"table": 0, "row": 1, "col": 2, "expected": "26"},
              {"table": 0, "row": 1, "col": 3, "expected": "28"}]
    r = check_reference_cells(tables, values)
    assert r["status"] == "SAMPLED_NATIVE_HTML_CELL_MATCH"
    assert r["matched"] == 3
    assert r["full_table_parity"] == "NOT_VERIFIED"


def test_html_table_refuses_bad_or_fake_parity():
    tables = parse_native_tables("<table><tr><td>1.44</td><td>1.05-1.25</td></tr></table>")
    report = check_reference_cells(tables, [{"table": 0, "row": 0, "col": 0, "expected": "1.12"}])
    assert report["status"] == "FAILED_OR_NO_CHECK"
    assert report["results"][0]["exact_match"] is False
    with pytest.raises(ValueError, match="TABLE_NOT_CLOSED"):
        parse_native_tables("<table><tr><td>1</td></tr>")


def test_local_pdf_receipt_does_not_forge_scientific_fidelity(tmp_path):
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    pdf = tmp_path / "small-synthetic.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((30, 50), "Synthetic research test document - not a scientific source.")
    doc.save(str(pdf))
    report = inspect_local_pdf(
        "CAND-G100-004", pdf, private,
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC8864028/",
        "AUTHORIZED_LOCAL_RESEARCH_USE",
    )
    assert report["original_pdf_pages"] == 1
    assert len(report["original_sha256"]) == 64
    assert report["table_cell_parity"] == "NOT_VERIFIED"
    assert report["scientific_qualification_L4"] == "HOLD_EXPERT_ADJUDICATION"
    with pytest.raises(ValueError, match="SOURCE_RIGHTS_ATTESTATION_REQUIRED"):
        inspect_local_pdf("CAND-G100-004", pdf, private,
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC8864028/", "UNKNOWN")
    with pytest.raises(ValueError, match="INVALID_SOURCE_ID"):
        inspect_local_pdf("../../etc/passwd", pdf, private,
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC8864028/", "AUTHORIZED_LOCAL_RESEARCH_USE")
