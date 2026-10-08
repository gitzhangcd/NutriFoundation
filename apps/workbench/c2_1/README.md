# Workbench WB-P0.2-C2.1｜Secure Reader Integration

> **SYNTHETIC ENGINEERING ONLY.** No real expert credential, no clinical data, no NDS-R1 empirical capture, no scientific QualifiedReference/Gold.

C2.1 combines C2's version-bound scientific workflow controller with the C1/B1 real-paper technical reader. The integration uses **new authenticated task-scoped endpoints only** and does **not** mount C1's globally readable `/reader` API.

## Implementation scope

- Signed-back-to-repo authoritative adapter: 10 NDS-R1 frozen Git blobs, R0/R2 v0.2 payload compatibility, role/exposure lock semantics unchanged.
- Synthetic fixture: a public 16-page 5:2 diet study ZIP; 154 CanonicalDocument units. Fixture is **not** a source in the actual NDS-R1 Human Baseline Source Packet; the synthetic demo source grant exists solely to run integration and leakage tests.
- R0/R2: task-owner-only structured text, SHA-pinned original PDF, page PNG, document-scoped search, manifest-allowlisted figure asset, task-owned SourceAnchor and PDF_PAGE_BBOX replay, limited synthetic export.
- R1: full document, original PDF, unrestricted search, exported source and figures are **never allowed**; before frozen candidate set: even reference excerpts are denied; after candidate set: only candidate-attached, source-ref-matched **verified quote snippets** returned after durable candidate exposure log.
- Source anchors scoped by task identity and source version; wrong task/cross arm IDs fail closed. Field bindings remain pre-freeze-only; source-binding SHA is audited **before** `J_preAI` snapshot freeze. This engineering digest is not the frozen scientific judgment content hash.
- No public import endpoint, no global PDF/anchor route, no unrestricted static source files. All authenticated responses and denials set `Cache-Control: no-store`, `Vary: X-Workbench-Token`, `nosniff`, `no-referrer`, and CSP.
- Denial gates include missing token, task cross-access, R1 wait phase, unknown source, direct raw download, wrong revision, bad quote offsets, PDF bytes or Markdown tamper, wrong anchor owner, locator tamper and attempted SQL update/delete of provenance.

## Run

```bash
cd apps/workbench/c2_1
python -m pip install -r requirements.txt
python -m pytest tests -q -rs
# Native PDF.js assets are pinned; installation requires npm network:
bash install_pdfjs.sh
python tests/browser_secure.py       # Chromium + local HTTP server, native PDF.js CI route
```

Run the synthetic demo (requires a full repo checkout and explicit flag):

```bash
python app.py --repo-root ../../../ --root .synthetic-data --allow-synthetic-execution
```

Tokens generated on startup are printed to the **local developer terminal** for synthetic actors only. Paste the appropriate test token in the browser. No token is included in static JS. Opening the page without a token does not expose task source content.

## Major security boundaries / unfinished deployment requirements

This program is **not production authorization**. Synthetic bearer tokens aren't an identity provider, and task roles are hardcoded synthetic exercises. The public paper is not legally/scientifically approved for pre-AI NDS-R1 human experiment. C2.1 only verifies project-scoped technical access and remote Chromium integration. Before real users: credential verification and authorization independent penetration tests, end-to-end permitted NDS source packet materialization, backup/DB administration hardening, CSRF/session strategy, PII/privacy compliance and controlled expert qualification. Existing WB-C1 proof and C0.1 pages aren't mounted in the C2.1 security boundary.

## Test evidence

- `tests/test_controller.py`: C2 regression.
- `tests/test_secure_reader.py`: task / URL / cross-arm / source digest / exposure / BBox / cache / export / DB immutability kill tests.
- `tests/test_official_adapter.py`: two real Git blob checks, skipped only in isolated local artifact, **must run in CI**.
- `tests/browser_bridge.py`: local Chromium with real FastAPI TestClient bridge; raster fallback, not a native PDF.js acceptance claim.
- `tests/browser_secure.py`: real HTTP Chrome E2E; CI requires `C21_REQUIRE_NATIVE_PDFJS=1`, rejecting raster fallback.
