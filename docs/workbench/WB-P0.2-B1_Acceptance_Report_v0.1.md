# WB-P0.2-B1｜Adversarial PDF Layout, Anchor Fidelity & Reader Acceptance

**Date:** 2026-10-08  
**Scientific base:** `ndf-d1-scientific-core-thin-slice@2259fdac9502541909a70d5d79c3460cecb6f657`  
**Engineering branch:** `workbench-wb-p0.2-real-paper-roundtrip`  
**Scientific status:** `NO_SCIENTIFIC_TRUTH_OR_HUMAN_CAPTURE_CREATED`

## Scope

The stage validates whether an actual PDF original can be used as reliable *technical evidence-location substrate* when subjected to rotated media, shifted CropBox, two-column reading order, repeated quotes, synthetic image-only scans, spliced table cells, forged text hints and modified bytes.

## Implemented normative delta

- `PDF_PAGE_BBOX/0.2` replaces the v0.1 assumption that page rotation must equal 0.
- All confirmed display rectangles are transformed by the original PyMuPDF page rotation matrix and normalized against the **visible crop page** (`page.rect`); they are not derived from Markdown hint or screen pixel coordinates.
- A candidate quote requires a unique token match on the original immutable PDF text layer **AND** plausible word geometry within a contiguous text block. This addresses visually discontinuous snippets that may be falsely joined in flattened token order.
- A wrong page hint is only a provenance warning. It cannot override a unique source text match. Ambiguous/unreadable quotes do not receive exact BBox at all.
- The frontend validates sidecar source SHA/canonical revision and normalized rectangle bounds before overlays are shown.
- Raster viewer fallback and genuine native PDF.js are separately identified, tested and reported.

## Adversarial fixture/measurement matrix

| Fixture | Challenge | Expected result |
|---|---|---|
| Original 5:2 diet, 16 pages | Genuine source, preexisting anchored paragraph | Exact highlight + regression |
| Synthetic rotate 0° | Baseline coordinate parity | VERIFIED + ink intersection |
| Synthetic rotate 90° | Portrait → landscape | VERIFIED + ink intersection |
| Synthetic rotate 180° | Flipped text | VERIFIED + ink intersection |
| Synthetic rotate 270° | Landscape flip | VERIFIED + ink intersection |
| CropBox shifted | Nonzero visible origin | VERIFIED + ink intersection |
| CropBox + 90° rotation | Combined coordinate transform | VERIFIED + ink intersection + native browser E2E |
| Two-column valid paragraph | Good text wrapped within a column | VERIFIED |
| False cross-column join | Flat tokens suggest nonexistent sentence | REJECT |
| False cross-table-cell join | Distant row cells incorrectly appear contiguous | REJECT |
| Repeated quote within page | Multiple plausible locations | REJECT |
| Repeated quote across pages | Reuse of phrase | REJECT |
| Synthetic image-only scan | No authoritative text layer | REJECT |
| Wrong Markdown page hint | Misleading page metadata | Accurate unique original page, mismatch warning |
| Source bytes tampered | Identity mismatch | REJECT |

### Local test evidence

- Python backend + adversarial tests: **37 passed** at initial acceptance run.
- Chromium offline fallback/real FastAPI bridge on original 5:2 study: **PASS**, with JavaScript errors `[]`.
- Native PDF.js/Chromium job: **pending remote CI** until corresponding GitHub Actions run completes. Local degraded browser pass does not substitute for this check.

## Acceptance criteria

The B1 acceptance gate requires that the same committed code/fixtures be used for Python tests, native PDF.js 5:2 diet replay and rotated/cropped native PDF.js replay. The last must verify real canvas render, normalized overlay geometry within tolerance, and click-to-structured reverse replay. For rejected fixtures, no guess may be written as a verified sidecar.

## Scope exclusions

- No OCR correctness claim, no proof of scientific statement validity, no high-confidence semantics for all adversarial PDF encodings.
- No UI for expert credential binding, R0/R1/R2 exposure, pre-AI lock or post-AI reconciliation; these are separate future slices.
- All NDF/NDS scientific sources remain read-only.