# NutriFoundation Workbench v0.3 · WB-v0.3-P1.1

## Repository-bound integration, Synthetic Pilot Preflight & Non-Regression

**Status:** IMPLEMENTED_ON_REVIEW_BRANCH / CI_PENDING / REAL_EXPERT_NO_GO  
**Date:** 2026-10-09  
**Authority:** `gitzhangcd/NutriFoundation`  
**Base:** `workbench-wb-p0.2-d0-private-staging@d2fd1643a9eb48b5a6582fbc490d4f7f88fec8f4`  
**Implementation branch:** `workbench-v0.3-p1.1-bilingual-integration`

### 1. Unchanged scientific / operational boundaries

- This change is **synthetic-only UX integration**, not independent Gold adjudication, human enrollment, real medical data collection, or NDS-R1 scientific capture.
- The original `C2.1` task-scoped FastAPI controller, source hash checks, evidence anchor, PDF BBox, Pre-AI freeze, Agent exposure gates, R0/R1/R2 projections, 19-field canonical judgment schema, and audit/SQLite constraints remain authoritative.
- The official NDS-R1 r2/r3 source-view conflict, source licensing, credentialing, ethics/consent, production TLS and CentOS 7 EOL acceptance remain independently unresolved; therefore real expert pilot / formal NDS-R1 remain **NO-GO**.
- No Aliyun deployment or live production migration was performed in this stage. The user can review the branch before any deployment.
- Existing workbench D0 is accessed only through the private SSH tunnel; **do not switch on public HTTPS or use real participant credentials** as a side effect of this UI work.

### 2. Exactly what was integrated

| Component | Code | Contract |
|---|---|---|
| Source-bound translation projector | `apps/workbench/c2_1/bilingual.py` | Exact original excerpt + unit raw SHA + UTF-16 offsets + source revision and document hashes; 3 illustrative bilingual excerpt pairs only |
| Scoped bilingual API | `apps/workbench/c2_1/secure_reader.py` | New `GET /v1/tasks/{task}/sources/{source_id}/translations`; same full-source projection `allowed(..., full=True)`, source and PDF integrity checks |
| Bilingual client | `apps/workbench/d0/web/reader.js` | Fetch gated API only after authorized document, validate source IDs/revisions/hashes/exact quote slice before showing translation |
| Modes / context evidence menu | `apps/workbench/d0/web/index.html` / `style.css` | Immersive, side-by-side, English-only, Chinese-assisted modes; translated excerpt mouse selection binds **original English excerpt**, not Chinese text |
| Expert-native judgment | `apps/workbench/d0/web/workbench.js` | Progressive grouped Chinese labels while preserving all 19 `data-key` names, original types, required shape, draft/save/freeze endpoints |
| Opt-in focus mode | D0 HTML/CSS/JS | Two-pane layout; legacy three-pane layout still available for backwards compatibility |
| R1 leakage kill tests | `apps/workbench/c2_1/tests/test_bilingual_v03.py` | Anonymous, other role, cross-arm, source-tamper and R1 full-document translation denial |
| Chromium acceptance | `apps/workbench/d0/tests/browser_d0.py` | Mode switching, Chinese→original evidence binding, focus-mode toggles, R1 denied route; preserves original D0 roundtrip |

The new translation layer is strictly an **illustrative unverified subset**, not a translation model, not paragraph-complete translation, and not a new SourceArtifact. All nontranslated units retain their English original.

### 3. Contract adaptations

**No canonical 19-field model mutation.** UI group titles and field labels are merely presentation adapters. Input values continue through `payload()` and the original `PUT /v1/tasks/{task}/draft` endpoint. Freeze remains `POST /v1/tasks/{task}/freeze` with revision, source packet, idempotency, and exposure assertions.

```text
Task-authorized English SourceDocument
   -> /translations [same task+arm projection, content integrity]
   -> source-bound illustrative TranslationSidecar (non-authoritative)
   -> Chinese selection -> exact English excerpt and UTF-16 offsets
   -> existing /anchors -> /bind-anchor
   -> canonical 19-field expert judgment draft / immutable Pre-AI freeze
```

**Alignment honesty:** the UX marks Chinese→English pairing as **L1 source-excerpt alignment**, not as verified sentence/precise translation span. The English anchor itself is verified by the existing server, and PDF BBox is only shown after actual resolver validation.

**No transcript/gold exposure:** unlike a generic webpage translator, this data is returned only by the backend with task and arm authorization. In particular R1 remains excerpt-only; no full-document translations are available to R1 through the new endpoint. No translation is bundled in public static JavaScript.

### 4. Synthetic UX pilot script (S1–S6)

*Population:* 2–3 UX participants **only after an independent site determination** that the planned synthetic-only exercise is approved; do not ask for formal NDS-R1 participant data or treat their annotations as scientific Gold. Until that determination, use project-team synthetic QA.

| ID | Participant operation | Pass criterion |
|---|---|---|
| S1 | Open synthetic R2, switch all four reading modes | Correct source and translated excerpt display; translation coverage labeled |
| S2 | Select Chinese illustrative excerpt and bind evidence | Original English source quote is saved; exact source revision and PDF hash are preserved |
| S3 | Click bound source and verify original PDF | Service-side verified locator, no invented BBox; fallback errors understood |
| S4 | Use expert-focus progressive form and enter decision | Existing 19 canonical fields preserved, no AI candidate shown in Pre-AI |
| S5 | Save/reload while editing, then correct an unsaved change | No unintended loss, stale revision cannot silently overwrite |
| S6 | Run pre-freeze check, freeze synthetic R2; attempt edit after freeze | Only server permits transition; snapshot read-only and idempotency intact |

**Measure:** per-scenario success/failure, elapsed seconds, mistaken bindings, number of confusing clicks, translation misunderstanding/semantic ambiguity, recovery from errors, NASA-TLX short burden score (optional), top-three qualitative improvement suggestions. Record no patient data.

### 5. Negative checks before any pilot

1. R1 / wrong-role requests for `/translations` denied, including guessed source path.
2. Source Markdown tampering blocks translation with 409; original PDF/source hashes remain matched.
3. R2 Pre-AI cannot read CandidateSet or hidden Gold; no hidden state leaked by translations or static assets.
4. Do not let translated text be submitted directly as a canonical English SourceAnchor.
5. Freeze requires a saved canonical draft; unsaved edits must not be frozen or replaced.
6. External production site security and scientific source qualification cannot be bypassed by a front-end checkbox.

### 6. Acceptance verdict

| Dimension | State |
|---|---|
| Source code located and baseline pinned | VERIFIED |
| Additive cross-language integration | IMPLEMENTED_ON_BRANCH |
| JavaScript syntax parsing | LOCAL_V8_PARSE_PASS |
| Browser and backend regression | PENDING_GITHUB_CI |
| UX translation completeness/accuracy | NOT_QUALIFIED (demo excerpt only) |
| Real-world user usability | NOT_EXECUTED |
| Production deploy/security acceptance | NOT_EXECUTED |
| Real expert pilot / formal NDS-R1 | NO-GO |

**P1.1 scientific freeze:** **PENDING**. Do not confuse engineering green tests with scientific permission.

### 7. Next transition: WB-v0.3-P1.2

After branch CI passes, an independent operator may roll out to a **separate synthetic staging instance** through the existing SSH tunnel, not the user's data workspace. Next design stages:

- Replace illustrative excerpts with qualified versioned paragraph-level translations, reviewed for numeric fidelity, causal qualifiers and clinical terminology.
- Add standalone field-level adapter/sidecars for native expert entries, without changing frozen NDS schema.
- Introduce safe debounced autosave with optimistic concurrency and explicit submitted revision; preserve edit-during-save regression tests.
- Carry translation version / language exposure through the draft, final freeze receipt and audit subject to an approved additive backend contract.
- Reconcile official case `r2/r3` scientific view before real enrollment; obtain all independent readiness receipts and supported-OS deployment for any approved human test.
