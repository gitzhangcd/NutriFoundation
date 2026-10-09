# WB-EA-P1｜D0 Native Integration Acceptance Receipt v0.1

> **Status:** SYNTHETIC ENGINEERING ACCEPTANCE PASSED / SCIENTIFIC SOURCE & REAL EXPERT NO-GO  
> **Exact baseline:** \`54b4c2eba844f39c07575573a3e834e0bc00c261\`  
> **PR:** [#26](https://github.com/gitzhangcd/NutriFoundation/pull/26) (Draft)  
> **Previous P1:** PR #25 CLOSED / SUPERSEDED / NEVER MERGED  
> **Acceptance date:** 2026-10-10 project-local

## 1. Verified results

**Original D0 in-place integration:**  
GitHub Actions [run 37965935534](https://github.com/gitzhangcd/NutriFoundation/actions/runs/37965935534) = \`success\`. Original D0 Python regression + EA integration: **14 passed**. Node syntax checks for \`reader.js\`, \`workbench.js\` and \`ea_mode.js\` PASS; protected scientific source paths unchanged.

**Existing D0 production-like synthetic browser acceptance:**  
GitHub Actions [run 37965935533](https://github.com/gitzhangcd/NutriFoundation/actions/runs/37965935533) = \`success\`. Both \`Full engine regression\` and \`engineering-acceptance\` jobs PASS. Browser suite output:

- \`status=PASS\`, \`page_errors=[]\`;
- native Chromium with PDF.js (not raster fallback acceptance);
- desktop 1440 × 1000 and mobile 390 × 844 existing regression coverage;
- \`ea_same_d0_login_layout_and_seven_profiles\`;
- \`ea_switch_2_source_versions_in_original_reader\`;
- \`ea_original_quote_binding_to_frozen_review\`;
- \`ea_expert_credential_isolation_and_original_nds_r0_pdf_unchanged\`;
- all original R0/R1/R2 security, pre-AI exposure, 19-field capture, source/anchor/PDF, search and UX regressions in the same browser run.

### Important interpretation

This constitutes **synthetic D0 UI+API+role exposure engineering acceptance**. It is not verification of multi-document real scientific source correctness, statistical validity, licensed PDF conversion, genuine Agent/LLM extraction, translator performance, independent expert qualification, Gold reference reliability or clinical/production security.

## 2. Regression/incident history

- First browser attempt failed because the new test checked candidate elements synchronously before async render. Fixed by Playwright condition waits.
- Dedicated evidence-only expert accounts were added to prevent NDS R0/R2 experts from viewing extra research-source candidates. First CI after role split failed a strict actor-prefix check in \`ea_runtime.py\`, corrected to \`SYN-EA-EXPERT-*\`.
- A later integrated test incorrectly expected the evidence-only actor to have R0 access; fixed to assert \`404\` for EA actor and \`200\` for independent R0 account.
- Subsequent GitHub CI runs \`37965935534\` and \`37965935533\` both passed with code scope and access boundaries confirmed.

## 3. Release / scientific boundary

Do not merge the PR or deploy to public service without science owner and security review. The app continues to run only in \`SYNTHETIC_ENGINEERING_ONLY\`. Data written into \`ea_synthetic.sqlite\` by \`ea_seed.py\` is fabricated structured-text source material. The real Hajek 5:2 paper remains available only as an existing D0 technical reader fixture, not an EA-qualified original source. No formal GoldAnnotationUnit or QualifiedDecisionReference is produced.

For real heterogeneous scientific source annotation, the next work package must explicitly cover the **real original PDF/HTML → verified CanonicalDocument → versioned source grant → bilingual sidecar → independent scientific reference** chain rather than treating these engineering fixtures as qualification.
