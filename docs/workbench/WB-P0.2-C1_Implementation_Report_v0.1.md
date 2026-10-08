# WB-P0.2-C1 Implementation & Non-Regression Report v0.1

**Stage:** WB-P0.2-C1 · Reader–Judgment Integration, Durable Draft Persistence & SourceAnchor Binding

**Scientific authority:** `ndf-d1-scientific-core-thin-slice@2259fdac9502541909a70d5d79c3460cecb6f657` — no scientific files modified.

**Status:** `PASS_C1_ENGINEERING_VERTICAL_SLICE / SCIENTIFIC_CAPTURE_DISABLED`.

## Scope and data ownership

This stage integrates an actual publicly available 16-page 5:2 diet paper as reading material with a **synthetic demo judgment**, not with the official NDS-R1 case. In particular, this paper is not silently added to the approved R0/R2 Human Baseline Source Packet. `Observation ≠ Evidence ≠ Claim ≠ Applicability ≠ Decision`; `SourceAnchor != Scientific Gold`.

The original B1 importer, Markdown canonicalizer, SourceAnchor validation and `PDF_PAGE_BBOX/0.2` geometry are imported unchanged as code modules (`reader_core.py`, `pdf_locator.py`). This creates a functional browser workspace and backend without changing NDF/NDS.

## Exact deliverables

- Full 19-field decision profile in five natural-language stages, including all seven `reference_set` classifications.
- Left structured reader / original PDF with independently verified BBox, middle judgment editor, right anchor rail.
- Selection of a real source quote → backend anchor validation → persist anchor → bind to any valid decision field → durable SQLite save → reload → independent export.
- `PUT /api/tasks/{task_id}/draft` uses `expected_revision`, source PDF SHA and canonical revision binding. Concurrent stale submission is rejected with HTTP 409 rather than overwritten.
- `GET /api/tasks/{task_id}/export` emits `SYNTHETIC_ONLY_NOT_SCIENTIFIC_OUTPUT`; saves produce `SYNTHETIC_DRAFT_SAVE` demonstration audit events.

## Local acceptance

- Python API tests: **11 passed**, including persistence after app recreation, repeat source roundtrip, forged anchor rejection, stale doc identity rejection and cross-task isolation.
- Offline Chromium/real FastAPI bridge: **PASS**; source phrase → verified PDF bbox → return canonical unit, linked field and server-side draft restore. JavaScript page exceptions: zero.

## Explicit incomplete capabilities

- No formal R0/R1/R2 server-side permissions, expert identity or participant consent.
- No preAI `J_preAI` freeze or Agent expansion; no scientific adjudication/QualifiedDecisionReference.
- No multi-user production auth, encryption, tenant boundary, backup/retention or regulated-data review.
- True native PDF.js E2E **passed** on GitHub Actions (run `37808073261`, successful). Local Chromium was separately tested with raster fallback and a real FastAPI TestClient bridge.

## Progression criteria

Only a passing remote native PDF.js E2E plus upstream protected-path diff=0 warrants `PASS_C1_ENGINEERING_VERTICAL_SLICE`.
Next work (`C2`) must implement the server-side contract adapter and leakage-safe role/phase projections *before* any real scientific capture.
## Remote conformance receipt (2026-10-09)

- GitHub Actions: https://github.com/gitzhangcd/NutriFoundation/actions/runs/37808073261
- Tested code commit: `2533afd07f258b97d62ecc27030509e59ec44b43`
- `Unit and API regressions (11 contracts)`: SUCCESS.
- `True native PDF.js, real-paper anchor and durable draft E2E`: SUCCESS.
- Native browser artifact: `wb-p0-2-c1-native-pdfjs` (ID `11563089198`).
- Science lineage remains untouched; no qualified human/Gold data or formal J_preAI freeze was generated.

**Final engineering gate:** `PASS_C1_ENGINEERING_VERTICAL_SLICE`. This is not the C2 server-side authorization/exposure freeze and not a research stage promotion.
