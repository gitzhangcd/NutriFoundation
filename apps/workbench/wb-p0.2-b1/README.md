# Workbench WB-P0.2-B1 — Adversarial PDF Layout, Anchor Fidelity & Reader Acceptance

This is the **engineering-only** successor of WB-P0.2-B. The scientific baseline remains pinned to `gitzhangcd/NutriFoundation@2259fdac9502541909a70d5d79c3460cecb6f657`. No NDF/NDS scientific state, frozen experiment, independent expert judgment, scientific truth, or Gold is created here.

## What changed

- `PDF_PAGE_BBOX/0.2`: visible-crop + 0/90/180/270 rotation-aware top-left PDF display coordinates; every rectangle carries normalized 0..1 coordinates for reader overlay.
- Actual glyph-overlap tests for rotated and cropped pages, **not just location string checks**.
- PDF text geometry guard: reject unsupported cross-block/column sequences, implausible cross-line jumps and table-cell joins even when flattened PDF token strings match.
- Fail closed for duplicated quotes (same page or different pages), image-only scanned pages, manipulated PDF bytes, absent quote and stale revision. Markdown page hints never create an exact bbox.
- UI additionally checks PDF SHA and canonical revision before drawing a highlight. Native PDF.js remains a pinned, locally installed module, with clearly labeled raster fallback.
- Adversarial fixture factory generates synthetic PDFs and an exact reproducible source ZIP; this fixture is **not a clinical or scientific case**.

## Run

```bash
cd apps/workbench/wb-p0.2-b1
python -m pip install -r requirements.txt playwright
python -m pytest tests/test_wb_a.py tests/test_pdf_locator.py tests/test_adversarial_layout.py -q
python adversarial/fixture_factory.py
# Locally requires npm registry access only at install/build time:
bash scripts/install_pdfjs.sh
python -m playwright install chromium
PYTHONPATH=. python tests/browser_native_pdfjs.py
PYTHONPATH=. python tests/browser_native_b1.py
python wb_a.py serve --root ./local-runtime --host 127.0.0.1 --port 8777
```

Use the authentic paper `fixtures/5_2_diet.AnnotationSourcePackage.v0.1.zip` for paper regression. For rotated/crop acceptance use `fixtures/b1_synthetic_crop_rotate_90.AnnotationSourcePackage.v0.1.zip` (auto-generated).

## Acceptance contract

| Expected behavior | Gate |
|---|---|
| Native PDF.js shows authentic research PDF; anchor opens source page and reverses to Markdown | E2E PASS |
| Rotation 0,90,180,270 and visible CropBox offsets have actual pixel-based ink overlap | PASS |
| Native PDF.js 90° rotated + cropped page overlays computed bbox and reverse click returns exact unit | E2E PASS |
| Two-column valid paragraph supports normal locating | PASS |
| Cross-column same-height or split table cells do not become false continuous quote | FAIL_CLOSED |
| Multi-occurrence, image-only text, short quote, wrong SHA or stale revision cannot show false exact bbox | FAIL_CLOSED |
| Source hint disagrees with verified unique text | preserve actual page and emit `page_hint_agrees=false` |
| Reader has no pre-AI candidate endpoint or expert Gold promotion | PASS |

## Known limitations

1. No OCR service integrated. Image-only pages require a separate OCR/parser run and its own validation/provenance before precise anchoring; nothing is synthesized here.
2. PDF words in one text block can still misrepresent semantically discontinuous text in unusually encoded PDFs; conservative geometry checks reduce risk but do not prove scientific semantics.
3. PDF.js and PyMuPDF can disagree on exotic PDF font/render semantics. Test target is deterministic regular text PDFs plus adversarial basic layouts; extensive publishing-format and assistive-technology coverage remains later work.
4. The v0.2 BBox geometry is a revisioned engineering sidecar. Migration of already persisted v0.1 BBox records is out of scope; an independently versioned new workspace is used for this slice.

## Scientific boundaries

`R0/R1/R2` expert qualification, hidden surfaces, exposure locks and Gold promotion are not implemented as a production human protocol in this engineering reader. The known frozen scientific artifacts under `runs/NDF/**`, `runs/NDS/R1/P0/**` and `runs/NDS/R1/P0.1/**` must remain untouched.