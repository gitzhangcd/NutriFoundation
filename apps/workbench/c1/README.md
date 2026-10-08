# WB-P0.2-C1｜Reader–Judgment Integration, Durable Draft & SourceAnchor Binding

**SYNTHETIC_DEVELOPMENT_ONLY** — not approved for expert identity binding, clinical cases, NDS-R1 empirical work, qualified reference or scientific Gold.

## Actually implemented

- B1 real-paper source package import, 154 canonical document units, original 16-page PDF; validated SourceAnchor and `PDF_PAGE_BBOX/0.2` via mounted B1 reader.
- C0.1 decision profile full fidelity: 19 fields in 5 stages, seven `reference_set` categories, preserved exact scientific field names.
- Unified three-pane workflow: structured reader / pinned PDF.js with raster fallback, editor, anchor rail and explicit field association.
- Drafts **durably saved server-side in SQLite** with immutable source document SHA/revision binding and optimistic concurrency `expected_revision`; competing saves fail `409_REVISION_CONFLICT`.
- SourceAnchor-to-field sidecars validated server-side. Invalid field, forged anchor, stale source SHA and incompatible canonical revision fail closed.
- Synthetic task partition for R0 and R2; no candidate API, no `freeze` endpoint, no actual qualification/protocol exposure controller, no scientific promotion.
- Separate B1 locator implementation reused; no edit to frozen NDF/NDS artifacts.

## Run

```bash
cd apps/workbench/c1
python -m pip install -r requirements.txt
bash install_pdfjs.sh                # Requires npm registry at install time; falls back to raster if absent
python server.py --root ./runtime --demo-source --host 127.0.0.1 --port 8788
# open http://127.0.0.1:8788
```

**Do not enter real patient details or actual qualified expert responses.** In this C1 slice, `/reader/api/import` and draft APIs are *demo-only*, without production auth/least-privilege input surface controls. R0/R2 labels are illustrative. The imported 5:2 diet article is **not** the NDS-R1 `Human_Baseline_Source_Packet_v0.2`.

## Validate

```bash
PYTHONPATH=. python -m pytest tests/test_c1.py -q
PYTHONPATH=. python tests/browser_c1_bridge.py   # offline Chromium, real FastAPI TestClient bridge
PYTHONPATH=. python tests/browser_c1_native.py   # requires installed PDF.js + local HTTP access
```

The local constrained browser does not permit localhost requests; this is why a real FastAPI TestClient bridge is supplied. GitHub CI validates *native* PDF.js browser rendering with a local pinned asset build.

## Known limits

- C1 does not integrate real role qualification, R0/R1/R2 projection, freeze transaction, Agent candidates, clinical data privacy/security, multi-user workflow, review/adjudication or scientific Gold.
- C1 applies only the NDS-R1 expert **decision** form profile in a synthetic setting, not the separate Evidence Annotation Profile form.
- PDF BBox is engineering source positioning, not proof of scientific semantic support.
- This slice assumes one imported paper per demo workspace. Multi-paper assignment allowlists and user identities belong to C2.
- C0.1 UX prototype was previously **locally accepted but not remotely frozen**; the exact `decision_profile.json` here is copied from the local C0.1 release bundle and retained in source control for provenance.