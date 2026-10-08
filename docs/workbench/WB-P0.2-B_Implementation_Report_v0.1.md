# Workbench WB-P0.2-B｜PDF.js Integration, PDF_PAGE_BBOX & Bidirectional Anchor Replay

**Date:** 2026-10-08  
**Authority:** Workbench engineering branch derived from `ndf-d1-scientific-core-thin-slice@2259fdac9502541909a70d5d79c3460cecb6f657`  
**Overall decision:** `PASS_NATIVE_PDFJS_E2E_AND_LOCATOR_CONFORMANCE`

## 1. Delivered

1. Real-PDF quote locator `pdf_locator.py`, using PDF words and conservative NFKC/casefold normalization. Unique match required, no manufactured positions.
2. `PDF_PAGE_BBOX/0.1` with precise page number, top-left point rects and normalized rects; signed by source identity, revision and locator SHA-256.
3. Append-only `pdf_locators` SQLite table; SourceAnchor immutable and unchanged.
4. Version-locked `POST /api/locators/{id}/resolve`, `GET /api/locators/{id}`, and integrity-controlled PDF/page PNG APIs.
5. Browser split structured/PDF interface, PDF.js dynamic local import and worker; deterministic PDF raster fallback when PDF.js assets unavailable.
6. Click anchor → verified PDF highlight → click PDF bbox → return to Markdown unit and exact quote where representable.
7. `scripts/install_pdfjs.sh` to fetch pinned PDF.js `4.10.38` at build time, including library LICENSE. No runtime CDN.
8. Backend fixture tests and browser interaction E2E, plus a separate **true native PDF.js test script** requiring external installed assets.

## 2. Test evidence

- Baseline WB-P0.2-A backend regression: 9 / 9 PASS.
- New PDF locator cases: 12 / 12 PASS.
- Total backend unit/integration: **21 / 21 PASS**.
- Offline Chromium E2E: **PASS** on actual FastAPI endpoints through browser bridge; page 1 BBox visible, text box clickable, return to structured anchor, zero JS exceptions.
- Native PDF.js E2E: **PASS — GitHub Actions run 37739834099**, completed successfully at commit `4659fbcddfadc6aaf472c4b1840d8d0ccbb963d0`. The runner installed pinned `pdfjs-dist@4.10.38`, executed Python tests and Playwright/Chromium, asserted the real PDF.js canvas and bidirectional bbox replay, and uploaded a screenshot artifact. The constrained chat container itself used the distinct raster fallback mode.
- Scientific expert/evaluator/NDS-R1 experimental gates: **NOT PART OF THIS ENGINEERING SLICE**.

## 3. Negative tests and safety

| Scenario | Expected result |
|---|---|
| Wrong expected revision or source hash | 409, no locator |
| Tampered source before/after locator freeze | 409, no replay of stale BBox |
| Quote too short | 409, no guessed BBox |
| Quote not found in PDF | 409, no BBox |
| Quote occurs in multiple PDF locations | 409, no guess |
| Invalid page/scale | 404/422 |
| Legacy anchor existing without locator | Stored unchanged; explicit resolve needed |
| Rotated page / different viewer page box | Exact geometry not asserted |
| Agent candidates before NDS-R1 freeze | No candidate API present in this slice |

## 4. Limitations

- A PDF with native text is required; scanned-only PDFs require OCR adapter with independent provenance and human verification.
- Exact phrase matching is conservative and may refuse typography-rewritten, substantially edited or OCR-degraded Markdown quotes. This is preferable to false positives.
- The locator is lexical, not a scientific claim or evidence validity verdict.
- PDF.js and server raster are separate renderer modes; the current environment only verified the raster mode.
- Single-document local store, no authentication or multi-expert experiment. The UI is **not eligible for NDS-R1 human pilot**.

## 5. Next gate

`WB-P0.2-B1｜Native PDF.js E2E, BBox Rendering Conformance & Adversarial PDF Layout Validation`, focusing on true PDF.js/browser acceptance, rotations/cropbox, scans and duplicate-text edge cases before any experiment-grade integration.
## 6. Remote native integration acceptance evidence

- Workflow run: https://github.com/gitzhangcd/NutriFoundation/actions/runs/37739834099
- Conclusion: `success` on implementation commit `4659fbcddfadc6aaf472c4b1840d8d0ccbb963d0`.
- Steps `Install pinned PDF.js assets`, `Run backend and locator regressions`, and `Run native PDF.js Chromium E2E`: **SUCCESS**.
- Screenshot artifact: `wb-p0-2-b-pdfjs-e2e`, artifact ID `11533510985`.
- No NDF/NDS scientific contract or frozen run artifact was modified for this gate.
