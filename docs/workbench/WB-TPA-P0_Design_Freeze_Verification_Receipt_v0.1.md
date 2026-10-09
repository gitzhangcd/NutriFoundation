# WB-TPA-P0｜Design-Freeze Verification Receipt v0.1

> Date: 2026-10-10  
> Result: **P0 DESIGN-FREEZE CHECK PASSED** (document/JSON/lineage-only verification)  
> Runtime acceptance: **NOT RUN / NOT APPLICABLE IN P0**  
> Production, real source, real Agent, real expert, Gold: **NO-GO**

## Verified user decisions
- Same-origin independent management route **/manage** using existing original D0 security perimeter; role privileges remain separate.
- Only **EVIDENCE_ECOSYSTEM_CASE**, no direct creation/modification of NDS DecisionCase/R0/R1/R2.
- External MinerU/other parser; TPA imports/validates structured manifests instead of embedding PDF conversion in expert UI.
- First **synthetic-management implementation**, then qualified real sources, then genuine Agent and gated expert pilot.
- No merge of draft PR #26, no real expert deployment.

## Verification performed
1. Read original integrated D0 EA interfaces: apps/workbench/d0/ea_runtime.py, ea_adapter.py, ea_seed.py, ea_contract.v0.1.json, d0_app.py, auth.py, provision.py, web/ea_mode.js, PR #26 acceptance receipt.
2. Read supplied SIS-MED R6, SIS R5, AI Nutri v2.0, Nutrition Foundation and NDF/NDS material for boundaries. **No assertion of complete scientific conformance; science-owner review remains open.**
3. Created branch **workbench-tpa-p0-contract-freeze** from existing PR #26 integration branch, not from main, and added new documentation only.
4. Fetched back all three written files from the new GitHub branch. Parsed both machine JSON files successfully.
5. Compared branch with **workbench-ea-p1-d0-54b4c2e-integration**: **ahead 3 commits / behind 0**, only added:
   - docs/workbench/WB-TPA-v0.1_P0_Task_Production_Assignment_Normative_Design_Freeze.md
   - docs/workbench/contracts/WB-TPA-P0_v0.1.json
   - docs/workbench/contracts/WB-TPA-P0_Negative_Fixtures_v0.1.json
6. Manifest includes **24 negative kill tests + 7 positive tests**. These are **not executed tests**. Their JSON validity and unique IDs were checked at generation; future P1 runtime/browser validation still required.
7. Pre-existing PR #26 synthetic engineering CI success: GitHub Actions runs 37965935534 (14 D0+EA Python tests) and 37965935533 (native Chromium) are **historical pre-TPA receipts**. They do not demonstrate TPA implementation.

## Normative delta vs PR #26
**Add:** same-origin manager route; task draft and immutable revision; SourceImportJob/Qualification; task projection; preparation provenance; expert eligibility and versioned assignments; durable delivery-exposure ledger; idempotent task publishing; synthetic-first acceptance.  
**Preserve:** all original D0 runtime source/PDF.js/bilingual/19-field decision; existing EA adapter behavior; task-only source allowlist; source and candidate immutability; strict EA/NDS account separation; independent human blind.  
**Do not touch:** runs/NDF/**, runs/NDS/**, src/nutrifoundation/**, apps/workbench/c1/**, apps/workbench/c2_1/**, apps/workbench/c2_2/**.

## Release gate
P0 design freeze is an operational specification only. Start P1 with a new branch from this P0 branch, implement code inside original D0, build synthetic tests and check all K/P fixtures plus full original browser non-regression before claiming engineering acceptance. **No source/Gold qualification, PR merge, public deployment, or human study enrollment in this phase.**
