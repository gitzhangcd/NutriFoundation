# WB-EA-P1｜54b4c2e D0-Native Integration Remediation v0.1

> **Status:** SYNTHETIC ENGINEERING / ORIGINAL-D0 INTEGRATION; FULL BROWSER & SCIENCE ACCEPTANCE OPEN  
> **Exact authority baseline:** \`54b4c2eba844f39c07575573a3e834e0bc00c261\`  
> **Branch:** \`workbench-ea-p1-d0-54b4c2e-integration\`  
> **Supersedes for P1 runtime implementation:** old isolated \`apps/workbench/ea_p1/**\` proposal (Draft PR #25).  
> **Retains:** scientific rationale of WB-EA-P0 (Draft PR #24), with proposed source types and profile maps.  
> **Do not merge either runtime PR without independent approval.**

## 1. Why the previous P1 was not acceptable

Git ancestry from the frozen \`54b4c2e\` did not make the older \`apps/workbench/ea_p1/app.py\` app usable as D0 Workbench. It created a separate FastAPI server \`:8795\`, role tokens, HTML/CSS/UI, and a simple structured-text reader. It skipped the already accepted D0 \`:8793\` cookie session, integrated NDS R0/R1/R2 workflow, paragraph-level original/translation viewer, PDF.js, source anchor highlight and 3-column expert judgment layout. Its CI validated a separate app only. **It should not be treated as the implementation of the D0 P1 feature.**

## 2. Corrected implementation: extend real D0 in place

The corrected branch is forked **directly** from \`54b4c2eba844f39c07575573a3e834e0bc00c261\`. It reuses the actual existing Workbench:

| Existing D0 path | Additive change | Preserved boundary |
|---|---|---|
| \`apps/workbench/d0/d0_app.py\` | Instantiate scientific EvidenceEngine and add \`/v1/ea/**\` routes before legacy mount | Reuse existing cookie/Auth/CSRF/Origin/CSP, no second server |
| \`apps/workbench/d0/web/index.html\` | Add "科学证据标注" switch and right-hand typed review subpanel inside original \`#expertPanel\` | Same three columns, old nodes retained, no independent UI |
| \`apps/workbench/d0/web/workbench.js\` | Emit login lifecycle and clear EA on logout | Original \`NDS_R1_DECISION_CAPTURE\` 19-field handling unchanged |
| \`apps/workbench/d0/web/reader.js\` | Add \`loadEvidenceSource()\` using original D0 paragraph/table/outline/selection/local search | Existing R0/R2 original PDF and bilingual read-model path remains; R1 excerpt-only prohibition remains |
| \`apps/workbench/d0/web/ea_mode.js\` | Route task and source selection to D0 read-model, bind source-original selected spans and expert review | Evidence mode separate from NDS tasks; no NDS source/Gold write |
| \`apps/workbench/d0/web/style.css\` | Add mode-specific visibility, share original responsive design | Original CSS preserved |
| \`apps/workbench/d0/ea_adapter.py\` | Role and task-scoped API using original \`request.state.principal\` | Auditor still audit-only; manager cannot read EA sources |
| \`apps/workbench/d0/ea_runtime.py\` | Add source-version registry/candidate/provenance/immutable review engine | Synthetic-only, no qualification/promotion |
| \`apps/workbench/d0/ea_seed.py\` | Seed 7 fictional source types, 7 Agent-review fixture tasks + 1 independent task | No copyrighted real document ingestion, not real LLM |
| \`apps/workbench/d0/ea_contract.v0.1.json\` | Local copy of proposed P0 profiles | Strictly versioned proposal; not upstream canonical science |

## 3. What the user actually sees

1. Log into **the existing D0 page** using a dedicated evidence-only test expert account `ea1` or `ea2`. Do not use the existing `r0/r1/r2` clinical-decision experiment accounts.
2. The existing Workbench automatically opens its science-evidence mode for the evidence-only test account. The UI mode remains distinct from NDS R0/R1/R2.
3. Select a typed scientific annotation task (RCT, observational, Meta, guideline, consensus, narrative, correction).
4. Select one of the task's **explicitly authorized source versions**. A multi-source RCT-plus-guideline fixture tests versioned selection.
5. Read original synthetic text in the **unchanged original D0 reader panel** with D0 paragraph selection, original span highlight and in-document search. Source version and SHA appear in the old provenance area.
6. Evaluate frozen producer candidate in the **existing right-hand expert panel**, choose disposition and support level, add expert rationale and optional corrected JSON. Select original text and bind it to a particular candidate.
7. Freeze through D0's existing cookie+CSRF-protected session. Export is \`UNQUALIFIED_EXPERT_REVIEW\`, not Gold.
8. Switch back via **← 返回 NDS-R1 独立决策工作台**. The original R0/R1/R2 case task and separate original PDF/bilingual reader are restored via the preexisting \`#load\` flow.

## 4. Data and scientific prohibitions

- The seven EA test documents are **fabricated examples**, not peer-reviewed studies or recognized guidelines. Even where a type resembles RCT, it is not the real Hajek 5:2 paper. All outputs \`scientific_capture=false\`, \`gold_qualification=NOT_ELIGIBLE\`.
- Existing D0 5:2 PDF.js + limited bilingual original exercise remains available under **NDS test mode**, not yet authorized as a new EA source. No false equivalence between synthetic structured-text source and real PDF. P1.1 should generalize the C2.1 original PDF+translation source grant with the same security and versioning.
- No real LLM extraction is wired. Producer candidates in \`ea_seed.py\` have \`extraction_run_ref=SYN-FIXTURE-NOT-AN-LLM\`.
- No clinician identity/qualification, external ethics approval, real case intake, or Gold adjudication. Source available dates are synthetic and cannot validate the real knowledge cutoff.
- No changes to \`runs/NDF/**\`, \`runs/NDS/**\`, \`src/nutrifoundation/**\`, \`apps/workbench/c2_1/**\` or the original frozen decision profile. The D2 r2/r3 case mismatch remains unaddressed.

## 5. Execution and acceptance

This is an **in-place additive D0 deployment source change**, not a live production deployment.

**IMPORTANT ROLE SEPARATION:** Dedicated engineering identities `SYN-EA-EXPERT-A` / `SYN-EA-EXPERT-B` are provisioned as `ea1` / `ea2`. Original NDS `r0`/`r1`/`r2` accounts cannot list or open evidence-annotation tasks; EA accounts cannot open NDS DecisionCase source/read-model. The original D0 authentication/cookie/CSRF infrastructure is shared, **not the experimental expert account or exposure state**. Evidence reviewer sessions open EA mode automatically; no UI toggle back to a blinded DecisionCase is permitted within the same account. Logout and authenticate with a distinct test account to inspect NDS. Run the original D0 command in \`apps/workbench/d0/README.md\`. The synthetic evidence fixture initializes once into \`<root>/ea_synthetic.sqlite\`.

Automated checks:

\`\`\`bash
python -m pip install --require-hashes -r apps/workbench/d0/requirements.lock
python -m pip install 'pytest==8.4.2' 'httpx==0.28.1'
python -m pytest apps/workbench/d0/tests/test_d0.py apps/workbench/d0/tests/test_ea_integrated.py -q
node --input-type=module --check < apps/workbench/d0/web/reader.js
node --input-type=module --check < apps/workbench/d0/web/workbench.js
node --input-type=module --check < apps/workbench/d0/web/ea_mode.js
\`\`\`

Do not claim UI E2E or full D0 browser regression solely from HTTP tests. Scientific acceptance and actual interactive usability must be separately assessed against the original D0 browser suite on a private loopback staging instance.

## 6. Release gates

- **G0**: Source history exact \`54b4c2e\`, compare shows additive D0 changes only, no science authority mutations.
- **G1**: Original D0 login/read-model/R0/R1/R2 tests PASS.
- **G2**: EA multi-source/read ACL/typed tasks/candidate review tests PASS.
- **G3**: Original D0 Chromium E2E of evidence-only login, source selection, per-candidate evidence binding, logout, independent NDS login and original PDF/bilingual rendering; keyboard/mobile acceptance remains separate.
- **G4**: Domain-specific scientific source qualification, translation fidelity, statistical interpretation, consensus/guideline relationships, independent expert adjudication—**NOT DONE**.
- **G5**: Deployment, security, ethics, real expert/real evidence Gold—**NO GO**.

P1 implementation is an engineering thin-slice; P1.1 science-ready PDF/document ingestion is the next distinct piece of work.

## 7. Remediation audit trail

The first Chromium run after integration failed an asynchronous assertion which checked candidate count before rendering completed. The suite was corrected to wait for the real UI state. A subsequent semantic audit required separate evidence-only accounts: without them, the same R0/R2 user could acquire additional source exposure while participating in a strict-blind decision experiment. The final state forbids that cross-program access through the server actor grants, not merely by hiding UI elements. CI and live browser results must be attached separately and must not be extrapolated to real expert/Gold validation.
