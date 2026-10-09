# WB-TPA-P1 | Synthetic Management Engineering Acceptance Receipt v0.1

> Status: **SYNTHETIC ENGINEERING PASS / REAL RESEARCH NO-GO**
> Date: 2026-10-10
> Draft PR: https://github.com/gitzhangcd/NutriFoundation/pull/28
> Code acceptance SHA: fbdd71a2569a6c3972d41b0915e7fa1cf54c0c4b
> Parent: PR #27 P0 contract; grandparent: PR #26 D0-native EA; original D0 SHA 54b4c2e

## 1. Implemented and accepted
- Protected same-origin /manage and /v1/tpa/** on the original D0 FastAPI app and existing security middleware, not another app.
- Producer: synthetic source metadata validation, typed task draft, validate, immutable freeze, prepare.
- Producer: all-or-nothing/idempotent seven-source draft batch with immutable receipt.
- Manager: synthetic EA expert assignment, idempotent publication, future-access revocation preserving history.
- EA workpack/source/candidate/list are denied to assigned experts until publish; exposure event written after successful resource read.
- Independent mode candidate-free, original strict-blind EA vs NDS actor separation.
- Original D0 three-pane reader, R0/R1/R2, PDF.js, bilingual and 19-field judgment retained.
- Source import is ONLY validation of previously seeded fictional structured source versions. No real files admitted.
- Synthetic task records and events use separate private tpa_synthetic.sqlite; original scientific controller and runs are unchanged.

## 2. GitHub Actions evidence
- WB-TPA-P1 tests and Chromium: https://github.com/gitzhangcd/NutriFoundation/actions/runs/37975237457: **21 passed**, native Chromium **PASS**, page_errors=[], PDF.js native, both desktop 1440x1000 and mobile 390x844.
- Original D0 private staging: https://github.com/gitzhangcd/NutriFoundation/actions/runs/37975237454: Full engine regression SUCCESS, engineering acceptance SUCCESS.
- Existing EA integration regression (previous milestone): https://github.com/gitzhangcd/NutriFoundation/actions/runs/37974825446: SUCCESS.
- A later README-only commit ceade20e1d6088a64d65fcf9c2790316c4dca363 followed code-acceptance commit; direct commit diff showed **only apps/workbench/d0/README.md** changed.

## 3. Browser checks in the SAME original D0 full suite
- tpa_same_origin_management_login
- tpa_seven_synthetic_source_library
- tpa_real_ui_draft_validation_freeze_prepare
- tpa_agent_fixture_not_llm
- tpa_manager_no_original_source_read
- tpa_expert_assignment_publish_via_UI
- tpa_published_task_delivered_to_original_ea_reader
- tpa_responsive_admin_desktop_mobile

## 4. Failures corrected, no concealed assumptions
- First authorization test failed because Pydantic rejected malformed body before role gate: corrected to role check before schema parse; 403 required for disallowed actor.
- Native browser initial test assumed RCT was default source even though source list is sorted: now explicitly selects RCT.
- Exposures are recorded after successful content fetch; denied reads never count as delivered evidence.

## 5. Honest P0 / science gate
- P0 design defines 24 negative kill cases and 7 positive scenarios. P1 tests cover material synthetic cases, **NOT every 24 cases as exact automated standalone IDs**, especially P2 real-source tests.
- Synthetic actor A/B arm restrictions are engineering fixtures, **not verified clinical credentialing, blinded randomization, genuine prior-exposure qualification or Gold adjudication**.
- Pending P2: external MinerU/parser import, rights, original bytes/hash, canonical unit mapping, evidence locator quality, bilingual sidecar and source qualification.
- Pending P3: real Agent model-run provenance, qualified experts, independent reference adjudication, ethics, security, deployment.
- Never merge draft PR #26/#27/#28 or deploy for real scientists without explicit independent scientific/security signoff.

## 6. Operator walkthrough (isolated disposable engineering instance only)
1. Open /manage with producer account, choose one of the 7 fictional source types; optionally add second allowlisted source, set workflow/cutoff, create a task or a seven-type batch draft.
2. Run validate -> freeze -> prepare actions on each task.
3. Switch to manager account /manage; assign appropriate synthetic EA identity and publish; revoke blocks future reads but does not erase exposure history.
4. Expert ea1 (Agent fixture review) or ea2 (human independent) signs into original / and sees authorized published EA tasks in the unchanged three-pane UI.
5. NDS r0/r1/r2 never receive EA privileges, and original decision case contract remains unmodified.
