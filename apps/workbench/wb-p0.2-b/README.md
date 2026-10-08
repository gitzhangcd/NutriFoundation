# Workbench WB-P0.2-B｜PDF.js, Verified PDF_PAGE_BBOX & Bidirectional Replay

**Engineering-only**, derived from the pinned scientific base `gitzhangcd/NutriFoundation@2259fdac9502541909a70d5d79c3460cecb6f657`. This slice does not qualify scientific evidence, Gold, expert judgments or NDS-R1 experimental readiness. The original 5:2 diet PDF is a genuine 16-page paper; extracted Markdown is not independently scientifically verified.

## Running locally

```bash
cd apps/workbench/wb-p0.2-b
python -m pip install -r requirements.txt
# Requires npm registry access during build; pins pdfjs-dist to v4.10.38
bash scripts/install_pdfjs.sh
python wb_a.py serve --root ./local-runtime --host 127.0.0.1 --port 8777
# Open http://127.0.0.1:8777 and import fixtures/5_2_diet.AnnotationSourcePackage.v0.1.zip
```

If the exact PDF.js browser/worker assets are not installed, the viewer labels itself as **离线降级（未加载 PDF.js）**, and renders original PDF pages via PyMuPDF raster images, not via PDF.js. The *same backend-verified PDF_PAGE_BBOX rectangles* are used in either renderer. There is no remote CDN dependency at runtime.

## Exact locator contract

- Create `SourceAnchor` using the unmodified WB-P0.2-A UTF-16/quote/revision contract.
- `POST /api/locators/{anchor_id}/resolve` accepts `{expected_revision, expected_source_pdf_sha256}`. It reads immutable original PDF bytes, verifies SHA-256, searches actual PDF text words, and requires **one unique normalized token-sequence match**; only then is a `PDF_PAGE_BBOX/0.1` sidecar appended to SQLite. The original anchor remains unchanged.
- `GET /api/locators/{anchor_id}` reads the verified sidecar and rechecks source integrity. `GET /api/pdf/page/{n}/png` supplies offline fallback pages. `/api/original.pdf` supplies PDF.js bytes and also rechecks original SHA-256.
- Geometry is in PyMuPDF top-left PDF page points with normalized rectangles used by both viewers. Rotated PDF page hints and PDF.js/PyMuPDF page-size disagreement are not treated as exact. Multiple-line quotes yield multiple boxes, not a giant ambiguous rectangle.
- Nonunique match, unmatched quote, short quote, stale revision, tampered PDF, absent unit, invalid UTF-16, or wrong SHA: **no exact bbox** (409), no best guess. Markdown page hints remain *page hints only*.
- Exact PDF text match is a **technical location guarantee**, not scientific correctness or semantic equivalence.

## Browser behavior

The main work area supports **structured-only**, **PDF-only**, and **split comparison**. Click `定位 PDF` on a SourceAnchor to resolve and display a verified yellow PDF text highlight. Click the highlight to return to the corresponding Markdown unit and exact quote via DOM `Range`/CSS Highlights API, falling back to unit focus only when the visual representation differs.

## Verification

```bash
python -m pytest tests/test_wb_a.py tests/test_pdf_locator.py -q
PYTHONPATH=. python tests/browser_e2e.py
# With locally installed PDF.js + Playwright browser + localhost access:
PYTHONPATH=. python tests/browser_native_pdfjs.py
```

`browser_e2e.py` runs real Chromium and actual FastAPI/TestClient with an offline request bridge, testing the *raster fallback* and bidirectional UI, not PDF.js rendering. `browser_native_pdfjs.py` rejects any fallback and directly asserts `PDF.js` canvas rendering. It was not executable in the original constrained chat environment because npm/CDN and localhost access were blocked. Treat native PDF.js E2E as a separate deployment/CI gate, **not PASS until run**.

## Scope boundary

No role-specific input projection, expert login/auth, R0/R1/R2 cross-arm lock enforcement, qualified Gold, or pre-AI judgment capture is implemented here. Scientific NDF/NDS run artifacts are read-only, and candidate endpoints are deliberately absent.