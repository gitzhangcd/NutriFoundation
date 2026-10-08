# Workbench WB-P0.2-A | Real-Paper Reader Vertical Slice

Engineering-only local proof of `AnnotationSourcePackage → CanonicalDocument → Structured Reader → SourceAnchor → Original PDF (page hint)`. Does **not** qualify scientific evidence, expert workpacks, or Gold. Pinned upstream base: `gitzhangcd/NutriFoundation@2259fdac9502541909a70d5d79c3460cecb6f657`.

## Start

```bash
python -m pip install -r requirements.txt
python wb_a.py package --legacy /path/to/old_annotation_source.zip --pdf /path/to/original.pdf --out fixtures/5_2_diet.AnnotationSourcePackage.v0.1.zip
python wb_a.py serve --root ./local-runtime --host 127.0.0.1 --port 8777
# open http://127.0.0.1:8777 and upload source ZIP
python -m pytest tests -q
```

The new ZIP includes `conversion_manifest.json`, `document.md`, `source/original.pdf`, and images under `assets/`. The importer checks SHA-256 values, PDF page count, asset integrity, ZIP path traversal and size limits. It refuses legacy ZIPs without the original PDF.

`CanonicalDocument` units are derived from Markdown sections, paragraphs, tables and figures. SourceAnchor is **strictly exact on the Markdown unit's UTF-16 text range**, with a cryptographic quote hash and pinned PDF identity. HTML is rendered with raw HTML disabled. Page hints (from `<!-- pdf-page: N -->`) drive the **page-level original PDF** viewer; PDF text bbox / precise in-PDF sentence highlighting is **not implemented** and must not be claimed.

Persistence is single-paper SQLite + filesystem, appropriate for this controlled local slice only. Authentication, multi-user permission guards, cross-arm exposure and candidate reveal are **out of scope** (not implemented, not simulated).

## Next gate

WB-P0.2-B: PDF_PAGE_BBOX and parser provenance/reconciliation, plus hardening source-package identity, with adversarial PDFs. Before any human/agent experiment, implement the full role-specific server-side projection and NDS-R1 pre-AI exposure gate; this UI is not an eligible experimental capture workflow.