# WB-P0.2-C2.1｜Secure Reader Integration, Task-Scoped Source Projection & Exposure Leakage Kill Tests

**Date:** 2026-10-09  
**Engineering-only gate:** `LOCAL_SECURITY_AND_UI_PASS / REMOTE_NATIVE_PDFJS_CI_PENDING` before remote CI.  
**Scientific base:** `ndf-d1-scientific-core-thin-slice@2259fdac9502541909a70d5d79c3460cecb6f657`  
**Source:** frozen 10 scientific Git blobs via `authority.py`; no mutation of `runs/NDF/**`, `runs/NDS/R1/P0/**`, `runs/NDS/R1/P0.1/**`, or `src/nutrifoundation/**`.

## 1. Scope, architecture and scientific source distinction

C2.1 uses C2's frozen-adapter + DB workflow controller and C1's B1 text anchor/PDF locator implementation. C1's public `/reader`, raw PDFs, imports, images and global anchor endpoints are **not mounted**. C2.1 exposes only `/v1/tasks/{task}/sources/...` routes with explicit `X-Workbench-Token` identity, task/arm binding and phase checks **on each API call**; no CSS-only access control.

The 5:2 diet PLOS ONE 16-page PDF and its 154 canonical units are **an independently pinned engineering source fixture only**. The official R0/R2 `Human_Baseline_Source_Packet_v0.2` continues to define real NDS-R1 scientific input; there is no scientific authorization to substitute or supplement that packet with the 5:2 paper. Synthetic task grants are tagged `not_scientific_source_packet` and `SYNTHETIC_TASK_EXERCISE_ONLY`.

## 2. Authorization matrix (all other paths fail closed)

| Task and phase | Full article / raw PDF / page PNG / search / source export | Anchor create / field bind | Candidate quote spans | Candidate data |
|---|---|---|---|---|
| R0 Human De Novo (synthetic) | allowed only to bound synthetic owner | only while editable | denied | NEVER |
| R0 Frozen (synthetic) | read-only | denied | denied | NEVER |
| R1 WAIT_AGENT_FREEZE | denied | denied | denied | denied |
| R1 EXPERT_VERIFY after candidate freeze | **denied** | denied | *only* verified `candidate.source_spans` from this source_ref | allowed through C2 logged reveal |
| R2 PRE_AI (synthetic) | allowed only to bound synthetic owner | only while editable | denied | denied |
| R2 WAIT_AGENT_FREEZE / POST_AI | original previously-authorized synthetic fixture remains readable | no new preAI anchors / bindings | not a full PDF widening for candidate source set | only after frozen `J_preAI` / candidate gate |
| Unbound/cross-arm/manager/anonymous | denied | denied | denied | denied |

**Important:** The R1 candidate source-ref field in C2's test envelope is a string and not itself scientific provenance. Therefore C2.1 additionally verifies candidate quote uniquely against original immutable PDF text and exact `SYN-5-2-PAPER` source ID; ambiguous/unmatched quote **refuses** precise locator. It does not allow R1 to download an unredacted original, which would expose extra context beyond the candidate-linked spans.

## 3. Implemented technical controls

1. Fixed Git-blob source ZIP identity, manifest import, immutable original SHA-256 and markdown SHA-256 checked on every protected source access.
2. Opaque route source ID `SYN-5-2-PAPER` resolves only in the current bound task. Direct old `/reader`, `/api/original.pdf`, import and asset paths are absent.
3. Whole-document response contains **plain text only**, no rich HTML injections. Query results limited to authorized canonical units, bounded query length/results.
4. Original PDF byte response has no shared ETag or 304 reuse; `Range` requests receive a complete authorized response. All public/API responses including refusals use `no-store`, `Vary: X-Workbench-Token`, `nosniff`, `no-referrer` and CSP.
5. Task-owned SourceAnchors: quote and UTF-16 range/revision must match original canonical text. Another arm cannot replay a guessed anchor ID or its verified BBox.
6. `PDF_PAGE_BBOX/0.2` remains unique original text-layer matching and rotation/CropBox-aware; persisted locator SHA validated before replay. Table, source quote, locator and source binding rows are append-only via SQLite triggers.
7. Field-Anchor linking accepts only v0.2 scientific workpack field names, including seven `reference_set` subfields. No post-freeze change permitted. On R0/R2 freeze the sorted source-binding digest is included in a prior append-only audit event *in the same transaction* as immutable judgment freeze; independent expert content SHA remains its own frozen hash.
8. R1 reference snippet GET first revalidates all matching source quotes in immutable original PDF, then writes `CANDIDATE_EXPOSURE` before delivering any authorized content.
9. Reader index/JS does not contain candidate data, demo tokens or user-facing hidden counts. No global source enumeration or public raw byte route.

## 4. Test matrix / local evidence

- Original C2 scientific controller regressions: **16 pass** in local run.
- C2.1 source-scoping/anchor/cache/path/source-tamper/DB immutability negative suite: **12 pass** in local run; combined `28 passed, 2 skipped` (official Git repo-only checks).
- Two official NDS Git blob checks: **intentionally skipped in isolated local directory**; must pass (0 skipped) in GitHub Actions full checkout.
- Local Chromium with actual FastAPI TestClient bridge: **PASS**, original PDF page raster fallback, task-private selection → SourceAnchor → field mapping → PDF bbox → reverse replay; R1 locked, R0 never-Agent; JavaScript errors **0**.
- Remote true native PDF.js E2E using pinned PDF.js v4.10.38 and Chromium: **PENDING CI** until a successful GitHub run is observed. Do not conflate local raster fallback with PDF.js acceptance.

## 5. Remaining limitations and next release gate

- Synthetic opaque tokens are local test-only, not real identity verification, authorization federation or production session management. This app refuses real expert capture by design.
- Clinical/PII storage, production backup controls, multi-tenant isolation, actual user usability, source packet scientific qualification and redaction/secure partial-page R1 PDF clip were not assessed in this slice.
- No real NDS-R1 expert slot is bound; real J_preAI and scientific QualifiedDecisionReference remain **zero**.
- Official current R0/R2 scientific sources are bounded excerpts/URLs, not imported as 5:2 PDF originals. Do not inject an unauthorized original into an arm based on technical import alone.
- C2.1 is a task-scoped reader **security engineering slice**; do not call it a penetration-tested production service.
- Next engineering gate: production-grade identity and scientific source packet materialization/approval, secure deployment/privacy review, simultaneous-user/TOCTOU stress testing, and reviewer/adjudication workflow integration.

## 6. Acceptance decision procedure

`PASS_SYNTHETIC_SECURE_READER_ENGINEERING` only after all of the following: remote Python tests report zero failure/skip; native PDF.js and Chromium browser test passes (raster fallback explicitly rejected); protected upstream scientific paths diff remains empty; report + manifest are committed to Workbench engineering namespace. Regardless of engineering PASS, NDS-R1 stays `EMPIRICAL_CAPTURE_PENDING_REAL_EXPERTS`.
