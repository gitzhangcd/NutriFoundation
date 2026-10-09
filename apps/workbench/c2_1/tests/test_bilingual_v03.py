"""WB-v0.3-P1.1: task-scoped bilingual excerpt projection kill tests."""
from pathlib import Path

from conftest import bind, h
from test_secure_reader import setup_r2, scope


def test_bilingual_exact_source_hash_offsets_and_no_scientific_promotion(env):
    c, keys, _ = env
    doc, allowed = setup_r2(env)
    url = scope() + "/translations"
    res = c.get(url, headers=allowed)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["source_document_id"] == doc["document_id"]
    assert data["source_revision"] == doc["revision"]
    assert data["source_markdown_sha256"] == doc["source_markdown_sha256"]
    assert data["source_pdf_sha256"] == doc["source_pdf_sha256"]
    assert data["scientific_capture"] is False
    assert data["coverage"] == "SELECTED_EXCERPTS_NOT_FULL_PARAGRAPH_TRANSLATIONS"
    assert data["items"], "at least the known synthetic RCT excerpt must match"
    for record in data["items"]:
        unit = next(u for u in doc["units"] if u["unit_id"] == record["unit_id"])
        assert unit["raw_sha256"] == record["source_unit_raw_sha256"]
        assert unit["raw"][record["source_start_utf16"]:record["source_end_utf16"]] == record["source_quote"]
        assert record["alignment_level"] == "SOURCE_EXCERPT_ONLY"
        assert "UNVERIFIED" in record["translation_status"]
    for forbidden in ("candidate_set", "QualifiedDecisionReference", "hidden_diet_values", "other_expert_judgment"):
        assert forbidden not in res.text


def test_bilingual_task_authorization_and_r1_negative_gate(env):
    c, keys, _ = env
    doc, r2 = setup_r2(env)
    url = scope() + "/translations"
    assert c.get(url).status_code in (401, 404)
    assert c.get(url, headers=h(keys, "SYN-ADMIN")).status_code in (401, 404)
    assert c.get(url, headers=h(keys, "SYN-EXPERT-A")).status_code in (401, 404)
    assert c.get(scope() + "/../WRONG/translations", headers=r2).status_code in (400, 404)
    bind(env, "SYN-R1", "SYN-EXPERT-B")
    r1_url = scope("SYN-R1") + "/translations"
    assert c.get(r1_url, headers=h(keys, "SYN-EXPERT-B")).status_code == 404
    assert "no-store" in c.get(url, headers=r2).headers.get("Cache-Control", "")


def test_source_integrity_tamper_blocks_translation(env):
    c, keys, app = env
    doc, r2 = setup_r2(env)
    path = app.state.source_store.path("document.md")
    original = path.read_bytes()
    try:
        path.write_bytes(original + b"\nmutated")
        assert c.get(scope() + "/translations", headers=r2).status_code == 409
    finally:
        path.write_bytes(original)
