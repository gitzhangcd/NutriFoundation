# WB-P0.2-C2.2｜Real-Expert Pilot Readiness, Scientific Source Qualification & Security Acceptance

**Date:** 2026-10-09  
**Engineering repository:** `gitzhangcd/NutriFoundation`  
**Development branch:** `workbench-wb-p0.2-real-paper-roundtrip`  
**Source scientific base:** `ndf-d1-scientific-core-thin-slice@2259fdac9502541909a70d5d79c3460cecb6f657`

## 1. Two independent decisions

| Question | Assessment | Authority |
|---|---|---|
| Is C2.2's *synthetic engineering readiness gate* reproducible? | Local: PASS; remote CI must validate all original frozen files | Workbench engineering |
| May we now invite real experts onto the current app with real credentials? | **NO-GO** pending external evidence and secure deployment | Site PI / security / ethics / identity/credential reviewer |
| Does this qualify NDS-R1 scientific human capture? | **NO-GO**; 0/3 real expert slots, 0 real J_preAI; no QualifiedDecisionReference | NDS-R1 scientific program |

**Do not conflate engineering acceptance with human enrollment, production security accreditation or ethics approval.** A simulated person or signed *test* JWT is not a qualified professional.

## 2. Official frozen authority + scientific packet mapping

Authority is the **same ten immutable Git blob SHA bindings** as C2.1. The active case is `D2-NHANES-L-0001:r3`; the R0/R2 active operational payloads are `R0_Human_DeNovo_Workpack_v0.2` and `R2_PreAI_Workpack_v0.2`, while frozen judgment semantics remain from `Judgment_Freeze_Contract_v0.1` through the explicit, tested compatibility map.

**Human Baseline Source Packet:** `HBSP-R1P0-001`, `Human_Baseline_Source_Packet_v0.2`, retrieved/cutoff date in source entries **2026-10-07**. Six frozen source identities:

1. Academy of Nutrition and Dietetics — Nutrition Assessment;
2. 2025 AHA/ACC Multisociety High Blood Pressure Guideline (corrected online version);
3. American Heart Association — Home Blood Pressure Monitoring;
4. USPSTF — Healthy Diet and Physical Activity Counseling in Adults With CVD Risk Factors;
5. Dietary Guidelines for Americans, 2025–2030;
6. USPSTF — Behavioral Weight Loss Interventions in Adults.

These are **source-level bounded excerpts with references and version/status metadata**, **not** signed/captured full-text originals. Do not silently refresh live web pages as if they were the 2026-10-07 snapshot; do not add the 5:2 diet reader demo article. Full-text availability/revision/copyright/lineage and source excerpt verification must be independently ratified before formal expert release. R0 and R2 preAI share an identical canonical packet SHA, not just visually similar cards. R1 independent preAI is not instantiated; R1 may verify only the frozen candidate-linked source spans through C2.1.

### 2.1 Explicit unresolved scientific version conflict

The frozen **`Human_Baseline_Source_Packet_v0.2`** and R0/R2 v0.2 workpacks reference **`D2-NHANES-L-0001:r3`**, but the designated `runs/NDF/D2/Case_0001/Materialized_Projection_Views_v0.2.json` declares **`case_ref = D2-NHANES-L-0001:r2`** (Git blob `426be595f178408cab11191a3720cf12aea7703b`). These values were read from the repository; no data are invented. `view_binding_check()` intentionally yields `BLOCK_REQUIRES_SCIENTIFIC_OWNER_RECONCILIATION`.

**Exact next action for scientific owner:** determine whether the old view is an obsolete pointer requiring a new approved r3 projection/view binding, or whether a formally signed compatibility delta establishes equivalent allowed content. Independently record the decision and verify no leak/future/hidden fields. **Do not edit frozen NDF/NDS files from this engineering stage.** Do not treat visual numerical similarity as proof of scientific revision equality.

## 3. Credentialed real-expert preflight contract

- Identity: an approved institution IdP/SSO verifies RS256 OIDC issuer/audience/kid/signature, `exp`, `iat`, `sub`, nonce and MFA. **This stage implements an offline test verifier primitive, not a connected IdP**.
- Professional qualification: independently verify professional role, nutrition/clinical-nutrition expertise, practice/research history, decision experience, source appraisal experience and conflicts as required by `Expert_Qualification_Instance_Registry_v0.1`.
- Scientific contamination screen: document exposure to the **exact case**, other arm outputs, hidden dietary values, SRS claim labels, final reference and other experts' judgments; refusal or follow-up if exposure cannot be excluded.
- Task binding: same real identity cannot be bound to R0/R1/R2 for the same case, and no task can be opened before status `QUALIFIED + BOUND + EXPOSURE_SCREEN_PASS`.
- Real credentials should **not** be pasted into local C2.2 synthetic inputs; future approved site service stores the minimum necessary proof hashes/registry references under restricted access.
- Research ethics/consent and source licensing require independent authorization appropriate to the planned live usability pilot and scientific study. No approval or legal determination is claimed here.

## 4. Readiness gate matrix (8 independent blockers)

| Gate | Status | Evidence needed |
|---|---|---|
| Identity provider | PENDING | Configured trusted JWKS/issuer/audience, real login + MFA, session revocation tests |
| Expert credentials | PENDING | Independent qualification review/credential proof |
| Prior exposure and arm binding | PENDING | Signed screen and cross-arm exclusion test on real identities |
| Ethics and participant consent | PENDING | Written institutional review/approval determination and consent flow |
| Scientific source snapshots/rights | PENDING | Exact bounded text/source revision and permissions evidence |
| Case version r2/r3 reconciliation | **BLOCK** | Scientific owner signed resolution, re-gated under explicit normative delta |
| Production deployment and privacy | PENDING | Security assessment, TLS, data access, backup/restore, retention, PII/PHI treatment |
| UX vs research separation | PENDING | Dedicated synthetic-case UX plan excluding formal study exact case and prior exposures |

**Guardrail:** this release cannot convert externally supplied checkboxes to `PASS`. Before a future production pilot, create a signed, independently verified `ReadinessReceipt` workflow with named review authorities, verifiable evidence hashes and auditable expiry; any missing receipt fails closed. Production-grade auth/ZTA, replay prevention and external pentest have not been demonstrated by the test verifier.

## 5. Engineering changes and tested controls

- `source_packet.py`: lossless whitelisted six-source bounded projection; stable SHA for R0/R2 equivalence; reject missing/extra source, stale version or unauthorized `R1`/postAI use.
- `authority.py`: unchanged pinned 10 scientific Git blob adapter; no upstream mutation.
- `credentialing.py`: signature-verified OIDC *primitive* under generated test keys. Wrong algorithm, issuer, audience, exp, kid, nonce and missing MFA fail closed. **Identity-only**: no automatic expert qualification.
- `gates.py`: eight external gates and version conflict; **NO-GO** even if attacker supplies `True` for every supposed approval.
- `app.py`: local-only synthetic manager **read-only** readiness dashboard; one-time console test token, restrictive CSP and `no-store`; no real onboarding, manuscript, patient, Agent or Gold APIs.
- CI: full frozen scientific file binding, source projection + token negative tests, Chromium, protected scientific path diff.

## 6. Small real-expert UX pilot design after all gates pass

**Not authorized yet.** Recommended first human UX study: 2–3 independent doctors/nutrition experts on **separate explicitly synthetic clinical/nutrition scenarios**, not the official NDS R1 case, with a written short protocol and consent/privacy approval. Observe: task completion, case/document navigation, source anchoring, unknown/conditional actions, return from PDF, draft recovery, error comprehension and time-on-task. Do not reveal candidate content when task claims to be preAI; do not reuse these participants later for the *same* formal arm/case if prior exposure has contaminated the workflow. Record task-time and burden; treat outcomes as usability results, not Gold/reference data.

## 7. M0 and NDS-R1 non-regression / next gate

- Scientific read-model is a presentation of bounded source support, not additional evidence or case-specific clinical truth.
- R0 permanently no Agent; R1 only after Agent set frozen; R2 independent J_preAI before any Agent output. C2.2 **does not add a new route** to bypass these controls.
- Frozen `runs/NDF/**`, `runs/NDS/R1/P0/**`, `runs/NDS/R1/P0.1/**`, and scientific `src/nutrifoundation/**` must show **zero Git diff** from pinned base.
- **C2.2 design/security engineering PASS is not a live-user GO.** Exit for real-person usability requires all eight independently evidenced gates and production security review; exit for NDS-R1 additionally requires formal scientific qualification and approved protocol.

**Next proposed work:** scientific owner resolves case projection r2/r3 mismatch, source provenance snapshot team verifies six frozen bounded excerpts, institution chooses real IdP and verifies credentials/consent and production security, then run isolated usability pilot with synthetic tasks. Only afterward consider NDS-R1 P0.1 real qualified expert slot binding.
