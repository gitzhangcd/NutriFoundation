# WB-P0.2-C0｜Page-to-Contract UI Specification & UX Acceptance

**Status:** C0_PROTOTYPE_IMPLEMENTED / DESIGN_FREEZE_PENDING_BROWSER_CHECK  
**Authority:** Workbench System Master v0.2 @ `e2a3151b43f0599a8056b95dbf62152b400c62ae`  
**Scope:** interactive, synthetic, no real expert data or runtime authorization claim.

## 页面与合同映射

| UI | Scientific input | Contract / guard | C0 prototype |
|---|---|---|---|
| P01 Task queue | own assignment metadata | task assignment scoped server read model | active synthetic examples |
| P02 Qualification | identity, conflict, exposure screen | Expert Qualification Registry; same-case arm exclusion | contract-only |
| P03 Source library | source package | Input Surface Contract, source hashes | navigation mock |
| P04 Evidence Reader | allowlisted CanonicalDocument | B1 PDF locator v0.2; anchored source | synthetic evidence example only |
| P05 Decision Workspace | R0 response / R2 J_preAI v0.2 | adapter field mapping, source allowlist | 5-step interactive form |
| P06 Freeze | immutable expert snapshot | Judgment Freeze Contract v0.1 + v0.2 payload | design-only, disabled formally |
| P07 AgentFirst Verify | frozen candidate + spans | Exposure Lock Registry R1 | hold and authorized synthetic modes |
| P08 Reconcile | frozen J_preAI + candidate | Exposure Lock Registry R2 | read-only synthetic state |
| P09 Review | authorized frozen records | reviewer phase policy | contract-only |
| P10 Audit/Export | redacted events | append-only server audit | navigation mock |
| P11 Profiles | versioned view mapping | administrative review | navigation mock |

## Expert-native stage-to-field mapping

1. Facts/focus → `salient_existing_facts`, `decision_focus`.
2. Decision-changing missing info → `decision_changing_missing_information`.
3. Actions and boundaries → `currently_acceptable_actions`, `conditional_actions`, `not_indicated_prohibited_or_unsafe`, `reference_set` (all seven categories).
4. Process/monitoring/uncertainty → `process_action`, `monitoring_needs`, `uncertainty_notes`, `rationale_notes`.
5. Review → content completeness, source anchors, exposure declaration, snapshot preview; it **does not** redefine clinical truth.

The C0 prototype intentionally shows only a short representative input field per stage; it does **not** pretend all production mappings are implemented. Full field coverage is mandatory in C1 before contract-based draft acceptance.

## Interaction rules

- One shell with three complementary panes; real Reader/Judgment integration is scheduled for C1.
- R0: candidate access permanently prohibited; no candidate payload.
- R1 HOLD: no verification form until qualified, bound, and a frozen candidate with source spans exists; simulated HOLD illustrates UI state.
- R1 VERIFY: candidate visible only in synthetic already-frozen fixture; no pre-AI independent judgment.
- R2 PRE: no candidate bytes in task object, UI, counts or hidden DOM; displayed negative-access control returns explicit simulated denial.
- R2 POST: immutable preAI summary and separate reconciliation disposition. UI cannot update original preAI content.
- No real persistence: browser in-memory demo state only. Formal save/lock/exposure permissions remain future server-side implementation; do not interpret UI assertions as evidence of the backend gates.

## UX acceptance gates

| ID | Expected verification |
|---|---|
| U01 | Can navigate tasks and return without navigation dead end |
| U02 | R0 view has no AI reveal path |
| U03 | R1 hold has no candidate bytes, and no inappropriate preAI editor |
| U04 | R1 verify offers six scientifically contracted dispositions |
| U05 | R2 PRE has zero candidate bytes and refused-access feedback |
| U06 | R2 POST has read-only locked judgment vs candidate view |
| U07 | Decision profile visibly staged with expert-native wording |
| U08 | Evidence selection creates synthetic anchor with honest `PAGE_HINT_ONLY` label |
| U09 | Web prototype works at desktop viewport; keyboard-focusable buttons and textarea |
| U10 | No source, test account, or synthetic action is written into NDS/R1 authoritative outputs |

All acceptances are **prototype-level**, except scientific role restrictions which must be independently enforced at API/projection layer during C2.