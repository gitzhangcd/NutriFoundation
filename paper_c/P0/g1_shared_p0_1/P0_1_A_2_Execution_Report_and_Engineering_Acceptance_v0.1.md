# G1-Shared P0.1-A.2｜Original Source Recovery, Structural Parity & Workbench Expert Pilot Integration

**Date:** 2026-10-10
**Branch:** research/gold100-bibliography-candidates-20261009
**Base scientific source corpus:** first five G1-Shared exploratory sources, not Paper C Gold100
**Execution decision:** Engineering implementation CI PASS; original primary PDF/attachment parity NO-GO; actual real-expert L4 NOT STARTED.

## 1. Implemented, test-backed code

- apps/workbench/d0/g1_source_pilot.py: five-source role-restricted engineering endpoints, rights gate, own-only independent A/B drafts, optimistic revision, required-field freeze, no team-side Agent answers.
- apps/workbench/d0/web/g1-source-pilot.html: Chinese original-first reading with five task types and blank review fields.
- apps/workbench/d0/g1_source_fidelity.py: no-network private licensed PDF receipt (SHA256 and PDF structure statistics, never falsely declaring source parity) and HTML table cell-preserving parser.
- apps/workbench/d0/d0_app.py: default-off explicit --enable-g1-pilot-engineering hook, preserving NDS-R1 controller and synthetic-only contract.
- apps/workbench/d0/tests/test_g1_source_pilot.py and test_g1_source_fidelity.py: 8 tests.
- .github/workflows/g1-shared-source-pilot.yml: engineering CI with confirmatory Gold100 no-mutation check.

GitHub Actions run: https://github.com/gitzhangcd/NutriFoundation/actions/runs/37973382216

**Actual CI: 8 PASSED; job SUCCESS on Python 3.11.** Covered opt-in, role restrictions, unauthenticated access rejection, CSRF, actual RCT original projection integrity, rights-restricted link-only delivery, independent A/B drafts, stale revisions, immutable engineering freeze, no expert Gold, synthetic native HTML table parsing, synthetic PDF SHA receipt, and Gold100 source slot isolation.

## 2. Actual source access and original document fidelity

| ID | Source type | PMC article body retrieved | Body in current Workbench pilot | Original PDF visual fidelity | Supplement parity |
|---|---|---|---|---|---|
| 004 | RCT | complete | CC BY projection inline | NO-GO | NO-GO |
| 029 | Prospective cohort | complete | external source link only, rights-scoped | NO-GO | NO-GO |
| 048 | Network meta | complete | external source link only, rights-scoped | NO-GO | NO-GO |
| 071 | Dietitian EBPG guideline | complete | external source link only; official EAL authority | NO-GO | NO-GO |
| 096 | PN expert consensus | complete | external source link only, CC BY-NC-ND | NO-GO | NO-GO |

PMC/Nature PDF attempt for RCT returned 403 and PMC supplementary source link could not be fetched. Original PDF/annex binaries not archived locally; zero valid PDF original SHA256 hashes may be claimed. Reading an entire PMC body is not structural fidelity.

### Real source structural-parity failure

The published PMC HTML Table 1 of the time-restricted-eating RCT shows an analysis row of eTRF 28, mTRF 26 and control 28. The prior OAI PMC plain-text body flattens original column boundaries into the contiguous run:

    CharacteristicseTRFmTRFcontrolp valueNo.282628Age...

The values agree at sample level, but HTML table row/column locator fidelity is lost by the plain-body representation. The new HTML table parser supports native cells; its automated tests use **synthetic HTML** only. The original native HTML/JATS bytes are not yet stored in the controlled source vault, so no real-source full table parity is approved. See P0_1_A_2_Source_Recovery_and_Structural_Parity_Audit_v0.1.json.

Separate source-native numeric anomaly in cohort 029 remains DEFER: the original sensitivity analysis displays HR 1.44 with CI upper 1.25 in two intervals. Do not guess a corrected number.

## 3. Engineering pilot deployment/runbook

**This has NOT been deployed to the user's server.** Existing D0 has synthetic engineering credentials and SSH-tunnel configuration; no current OS/security readiness for real clinical review.

From a checkout on an authorized host with D0 locked Python 3.11 requirements and separately provisioned private synthetic credentials:

    python apps/workbench/d0/d0_app.py       --repo-root /PATH/TO/NutriFoundation       --root /PRIVATE/ENGINEERING_DATA       --accounts /PRIVATE/accounts.json       --auth-db /PRIVATE/auth/sessions.sqlite       --origin http://127.0.0.1:18793       --port 8793       --allow-synthetic-execution       --enable-g1-pilot-engineering

Using the documented loopback SSH tunnel, log in at the D0 home page and open /static/g1-source-pilot.html. This opt-in feature remains OFF by default. Both reviewers have separate persistent engineering drafts, but manager cannot read draft contents or scientific source. Freeze is explicitly ENGINEERING_REVIEW_FROZEN_NOT_GOLD.

### Authorized original PDF ingestion

The local-only command accepts **already lawful, privately obtained** PDF files; it computes SHA256, page count and image/page-text statistics. It does not fetch PDF or assert full fidelity.

    python apps/workbench/d0/g1_source_fidelity.py       --candidate-id CAND-G100-004       --original-pdf /PRIVATE/authorized-rct.pdf       --private-dir /PRIVATE/source-vault       --source-url https://pmc.ncbi.nlm.nih.gov/articles/PMC8864028/       --rights-attestation AUTHORIZED_LOCAL_RESEARCH_USE       --output-name CAND-G100-004-pdf-receipt.json

The output directory must be mode 0700. No restricted PDF is uploaded to public GitHub. Separately validate original table cells, figures, supplemental documents and version timestamps using an authenticated reviewer and a source-native loader.

## 4. Final stage gates

| Gate | Result |
|---|---|
| Five typed source tasks with original authority links | PASS |
| Role-isolated A/B engineering drafts and immutable engineering freeze | CI PASS |
| Body-text integrity in RCT source projection | CI PASS |
| Permission-aware link-only handling of other four source bodies | CI PASS |
| Native HTML parser on synthetic test table | CI PASS |
| Native table parity on actual original source | NO-GO |
| Authorized original PDF files hashed in a private vault | NO-GO (0/5) |
| Original PDF pages/figure/table/supplement parity | NO-GO (0/5) |
| Independent expert verification and L4 scientific Gold | NOT STARTED (0/5) |
| Production Workbench OS/identity/deployment acceptance | NO-GO |
| Official confirmatory Paper C Gold100 slot changes | NONE; 0/100 bound |

**Decision:** G1-Shared P0.1-A.2 engineering implementation and CI verification complete, with scientifically correct explicit NO-GO for original-document parity and independent real-expert L4.

## 5. Next exact gates

A.2.1 — Native JATS/HTML/PDF Document Vault, Table/Supplement Recovery and Structural Cell-Parity Confirmation.

A.2.2 — Real-Expert Security Acceptance, Qualified Expert Enrollment, 2-Reviewer Independent L4 Adjudication and SourcePackage Freeze.

Until these gates pass, do not promote a source to Gold, claim production expert pilot acceptance, or use any exposed five-source G1 pilot item in the independent Paper C confirmatory sample.
