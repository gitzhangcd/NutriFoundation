# WB-P0.2-C2 · Scientific Contract Adapter & Exposure-Safe Synthetic Controller

**Status:** engineering conformance only · `SYNTHETIC_ENGINEERING_ONLY` · `REAL_SCIENTIFIC_CAPTURE_DISABLED`.

## Objective

This is a standalone **server-side** scientific workflow controller built after the C1 reader/draft slice. It intentionally **does not mount C1's unprotected reader or raw source endpoints**. The next integration must use its phase-specific `TaskReadModel` to authorize PDF/Markdown/SourceAnchor retrieval, not mix unguarded C1 APIs into R0/R2.

Git baseline: `ndf-d1-scientific-core-thin-slice@2259fdac9502541909a70d5d79c3460cecb6f657`.

## What is implemented

- Git-blob SHA-pinned loader for 10 frozen upstream NDS-R1 files; schema/semantics guards and explicit `Judgment_Freeze_Contract_v0.1` → current R0/R2 v0.2 workpack compatibility binding. **No frozen upstream edits**.
- Synthetic qualification-screen + same-case cross-arm binding exclusion. Not credential verification.
- Three **independent server-side arm/phase** projections: R0 permanent no Agent; R1 hold until frozen candidate set + source spans; R2 only after valid immutable `J_preAI` freeze.
- Complete field-preserving v0.2 scientific response schema, seven reference categories, revision-bound SQLite drafts, `content_sha` freeze receipts and idempotency.
- Immutable candidate vault, controlled first-exposure logging before response, separate R1 verification and R2 `J_postAI` record, append-only hash-chain audit and SQLite update/delete triggers.
- Client access via randomly generated **synthetic dev tokens**. Tokens are printed on local terminal and are **not** production identity, qualifications or authorization to create experimental data.
- Test-only browser controller visualization. It displays safe read-model responses but does not collect real judgments or store credentials in a frontend bundle.

## Start locally (repository checkout with frozen science files)

```bash
cd apps/workbench/c2
pip install -r requirements.txt
python app.py --repo-root ../../../ --allow-synthetic-execution --host 127.0.0.1 --port 8790
```

Copy a synthetic token from the local terminal into the dev UI at `http://127.0.0.1:8790`. No public hosting or real experts. Without `--allow-synthetic-execution`, the CLI exits. The `/health` endpoint always says `scientific_capture=DISABLED`.

## Tests

```bash
python -m pytest tests -q
python -m playwright install chromium
python tests/browser_flow.py
```

The isolated local environment uses a synthetic **replica** of the 10 contract shapes; this has no scientific authority. In a full checkout, two extra tests run: exact Git-blob SHA of the ten real files and fail-closed tamper check. The `make_app(..., test_authority=...)` injection exists solely for test fixtures; normal `make_app` refuses startup if official files are missing/changed.

## Critical negative cases

`R0 → candidate` forbidden forever; `R1 → preAI judgment` forbidden; `R1 → candidates before set freeze` forbidden; `R2 → candidates before J_preAI freeze` forbidden; invalid exposure assertions refused; cross-arm identity reuse forbidden; candidate source spans required; post-AI response cannot overwrite pre-AI; snapshot and audit cannot be updated/deleted; idempotency cannot change payload; unknown or unauthenticated actor refused; no raw reader/source bypass; source packet SHA mismatch refuses draft/freeze.

## Explicit exclusions / risk notices

- **No real credential validation / personal health data handling.** Synthetic qualification is not evidence that a real expert meets NDS eligibility; cannot enroll or bind a real individual.
- **No production-grade multi-tenant authorization, TLS, secret manager, OIDC, audit key management, tamper-proof external write-once store or DLP.** SQLite triggers alone do not defend against administrators who can alter the database file.
- No C1 PDF reader inside C2: it is intentionally omitted until its routes can be made read-model-scoped. The C1 experiment remains its own engineering-only app.
- No science `Gold`, `QualifiedDecisionReference`, real R0/R2 judgments, or formal NDS-R1-P0.2 stage promotion.
- Candidate sources in synthetic tests are test strings, not scientifically verified citations.