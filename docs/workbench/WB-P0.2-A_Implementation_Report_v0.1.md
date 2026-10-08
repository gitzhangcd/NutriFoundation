# Workbench WB-P0.2-A | Implementation & Acceptance Report v0.1

- **Scope**: `Real-Paper AnnotationSourcePackage → CanonicalDocument → Reader Vertical Slice` with source-anchored page-level PDF replay.
- **Scientific baseline**: `gitzhangcd/NutriFoundation:ndf-d1-scientific-core-thin-slice@2259fdac9502541909a70d5d79c3460cecb6f657`
- **Engineering baseline**: `workbench-wb-p0.2-real-paper-roundtrip` following WB-P0.2-P0 gate.
- **Verification status**: `LOCAL_API_PASS_BROWSER_BRIDGED_PASS / EXACT_PDF_BBOX_NOT_IMPLEMENTED`
- **No empirical status promotion**: NDS-R1-P0.1 still requires real experts; no ExpertJudgment, J_preAI, AI candidates or qualified Gold generated.

## Real source

The previously produced 5:2 diet Markdown ZIP was bundled together with the actual 16-page original PDF into a new `AnnotationSourcePackage v0.1`.

```
5_2_diet.AnnotationSourcePackage.v0.1.zip
├── conversion_manifest.json
├── document.md
├── source/original.pdf
└── assets/fig1_consorte_diagram.jpg
```

The image is an existing source asset, not a newly rendered figure. The PDF p.7 figure location is verified via the PDF text layer; other range-only markers remain explicitly uncertain. `document.md` is an existing conversion and is not a new scientific verification.

## Implementation

- `wb_a.py` – legacy-ZIP upgrade CLI; strict ZIP importer; SHA-256/pdf page validation; Markdown token→CanonicalDocument/DocumentUnit; persistent UTF-16 exact `SourceAnchor`; FastAPI endpoints; PDF and local asset serving.
- `web/index.html` – self-contained modern 3-column reader: document outline, text/table/figure viewer, search, create anchored source quote, original PDF page mode, anchor export, status/boundary notices.
- `tests/test_wb_a.py` – nine backend tests: real 16-page import, 154 units incl. 7 tables and 1 local figure, anchor save/replay/restart, corrupt hash reject, missing PDF reject, traversal reject, UTF-16 surrogate strictness, candidate route absence, idempotent reimport.
- `tests/browser_e2e.py` – real Chromium DOM selection, ZIP upload, real FastAPI TestClient bridged HTTP, anchor creation, PDF page locator UI, persistence and no JS page errors. Chromium direct loopback HTTP is blocked by this environment, so the browser test uses a TestClient bridge and **does not verify the native PDF plugin's pixels**.

## Acceptance evidence

| Criterion | Result |
|---|---|
| Real PDF present and byte-identified | PASS – source SHA-256 `ef50d59998b5af7b8aacedd176b5c8bafb497cd231a837f83f8b5c764e8f3e63`; 16 pages |
| Markdown and assets manifest verified | PASS |
| Canonical units | PASS – 154 (SECTION 36, PARAGRAPH 100, TABLE 7, FIGURE 1, LIST 9, BLOCKQUOTE 1) |
| Exact text Quote/UTF-16/Revision round-trip | PASS |
| Anchor persisted across server restart | PASS |
| Page-level source PDF link | PASS – page hint, not PDF bbox |
| Real browser DOM selection and upload | PASS via bridge |
| Negative cases | PASS – 9/9 Python test functions total |
| Exact PDF bounding box and in-PDF highlighted sentence | **NOT IMPLEMENTED** |
| Multiuser authentication, RBAC, lock, AI exposure guard | **OUT OF SCOPE** |
| Empirical capture or scientific Gold | **NOT CREATED** |

## Remaining issues / subsequent gate

WB-P0.2-B should implement PDF_PAGE_BBOX and a true bidirectional PDF text selection/hit test under PDF.js, additional malformed PDF and package hardening, and adapters for future parser output. The present prototype is a controlled single-paper demonstration; it is not an eligible human/agent experiment surface and must not be used to simulate actual NDS-R1-P0.2 progression.