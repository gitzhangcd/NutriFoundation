# WB-P0.2-C2｜Scientific Contract Adapter, Qualification & Freeze Controller

**Baseline:** `ndf-d1-scientific-core-thin-slice@2259fdac9502541909a70d5d79c3460cecb6f657`  
**Scope:** `SYNTHETIC_ENGINEERING_ONLY` / real expert enrollment disabled  
**Scientific status:** `NDS-R1-P0.1` remains `EMPIRICAL_CAPTURE_PENDING_REAL_EXPERTS`.

## 1. Scientific authority binding

The scientific adapter references 10 existing upstream files using pinned **Git blob** SHA identities from the M0 Scientific Adapter Matrix. Startup with a real repository refuses missing files, mutated bytes, unfrozen semantics, arm/surface changes, invalid case refs, mismatched R0/R2 input substrate or workpack supersession conflicts. The specific v0.1 → v0.2 freeze/workpack compatibility is explicit and fail-closed: `R0_Human_DeNovo_Workpack_v0.2.json` and `R2_PreAI_Workpack_v0.2.json` each must explicitly supersede the v0.1 paths named by the immutable freeze contract. No scientific source file is rewritten.

## 2. Isolated controller policy

| Arm | Before expert freeze | After freeze / candidate | Forbidden action |
|---|---|---|---|
| R0 | Eligible synthetic binding → bounded Human Baseline packet → independent draft | `J_human_de_novo` read-only; **still no Agent** | Any candidate endpoint; R2-like unlock |
| R1 | Qualification/binding; `WAIT_AGENT_FREEZE` without candidate metadata | Frozen Agent set **with source spans** → verification → immutable R1 result | `J_preAI` capture or early candidate exposure |
| R2 | Qualified/bound → baseline packet → versioned draft → signed all-false exposure assertions → atomic `J_preAI` | Frozen set → exposure recorded before payload response → reconciliation → `J_postAI` | Any candidate exposure before freeze; overwrite preAI |

A principal is identified by a backend-generated synthetic token; no browser-stored authority or CSS/hide trick controls the data. Every response is composed from the allowed arm/phase, and the API does **not** contain any C1 `/reader` or `/source/original.pdf` raw route to bypass scientific source allowlists.

## 3. Persistent model / invariants

SQLite local engineering tables `bindings`, `drafts`, `snapshots`, `candidates`, `exposed`, `audit`. Snapshot, frozen candidate, exposure, identity binding and audit tables have `BEFORE UPDATE/DELETE RAISE(ABORT)` triggers. Writes use `BEGIN IMMEDIATE` for serializable-by-writer operations. Draft save uses expected revision. Freeze binds `content_sha = SHA256(canonical JSON payload)`, actor, case-bound slot, input packet digest, timestamp and idempotency key. First exposure records the candidate SHA and a chain-linked audit event **before the response is released**.

`J_postAI` is a distinct row and refers to immutable preAI content SHA. Candidate validation requires source spans and valid disposition taxonomy. Historical process deviations cannot be retroactively repaired; disqualification must be adjudicated by the scientific program, not rewritten in UI. This C2 demo does not support real compromised-exposure rehabilitation.

## 4. Acceptance tests

- Contract-bounded startup and real upstream tamper rejection (full Git checkout).
- Unauthenticated, forged token, cross-arm, role escalation and raw-reader bypass negatives.
- Expert screening failures, cross-arm reuse, R0 Agent denial before/after freeze.
- R1 hold, candidate freeze, verification and immutable result; R1 lacks preAI.
- R2 preAI invalid assertions, atomic freeze/idempotency, candidate exposure after freeze, chronological audit, separate postAI record.
- Source digest mismatch and concurrent optimistic draft writes.
- Direct SQLite UPDATE against locked tables fails.
- SQLite restart persistence and audit digest verification.
- Browser R0/R1/R2 synthetic read-model gate checks, zero console page errors.

**Gate distinction**: `PASS_ENGINEERING_POLICY_SIMULATION` only after both local and full GitHub checks pass. It must not be interpreted as `PASS_REAL_EXPERT_SECURITY` or as `NDS-R1-P0.2` scientific work.

## 5. Next necessary integration

C2.1 (or C3 controlled integration) must wrap **all** C1 Reader, PDF, figure, SourceAnchor, search, thumbnail, export and cached routes in server-side task/phase authorization. Do not make C1 public alongside C2 in any deployment. Add real identity/credential verification + human independent screening before any empirical use. Independent security review and end-user/clinician usability testing remain mandatory.