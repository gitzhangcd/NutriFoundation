# WB-P1.1-B0｜Existing Workbench Integration & Gap Audit v0.1

> Date: 2026-10-11. Repository: `gitzhangcd/NutriFoundation`. Audited branch: `workbench-tpa-p1.1-a-management-ux-spec` @ `04accfe50839247992dd0a439361a9646bd4f567` (Draft PR #29). Last acceptance-tested code: `849ebd4f1edd958b3c0ef9784a1dcab58e32f39f`; one subsequent documentation-only commit.  
> **Disposition:** B0 source/lineage/contract audit completed. **Integration = CONDITIONAL SYNTHETIC BASELINE; operational UX = PARTIAL; scientific, real-expert, production, Gold = NO-GO.**  
> Evidence scope: read-only GitHub code/commit/PR/CI metadata audit. No local Git checkout or fresh end-to-end test run was possible in this audit session; do not relabel historical CI as newly executed tests.

## 1. Authority and fixed decisions

Maintain the *existing* original D0 single-origin application, three-pane bilingual/PDF.js reader and NDS 19-field R0/R1/R2 paths. Integrate evidence work within D0's `/v1/ea/**` and expert `/` entry point; operations stay on `/manage`, `/v1/tpa/**`. No second app/server, no fabricated real expert/Gold status, no automatic scientific source rights or model output qualification. Structured conversion/MinerU is upstream and outside Workbench; only validated, versioned, rights-qualified import packages may enter the future real-source admission gate (not implemented).

Audit compares: WB-TPA P0 freeze, WB-TPA P1 receipt, P1.1-A page specification, A1 minimal operational contract, A4 engineering receipt and D0/EA/TPA code. The previously discussed **Development Master Plan v1.1** determines the intended B0→A5→subsequent B-module order; its complete master file was *not present in the audited Git tree*, therefore full clause-by-clause conformity with that document remains **unverified**, not assumed.

## 2. Verified ancestry, release baseline and CI

| Ref | State / evidence |
|---|---|
| PR #23 | D0 v0.3 expert-UX remediation; head `54b4c2e...`; Draft, open |
| PR #26 | D0-native EA integration; head `7c954331...`; Draft, open |
| PR #27 | TPA P0 design-only freeze, ancestor of current branch; Draft |
| PR #28 | TPA P1 synthetic /manage production and assignment, ancestor of current branch; Draft |
| PR #29 | A1–A4 additive Project→Batch→Task UI/runtime; `04accfe5...`; Draft, open, not merged |
| main | GitHub compare `main...PR29`: 329 commits ahead, zero behind at audit time. **Workbench development is not yet merged into main**. Do not infer production delivery. |
| PR #26→#29 | GitHub comparison returns 65 commits ahead, zero behind: exact inherited D0/EA lineage, not a parallel app. |
| P1 base→#29 | 34 commits ahead; 14 changed files, including two new operations Python modules and management UX files. |

CI: for code SHA `849ebd4f...`, [P1.1-A](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38119182596), [original TPA](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38119182591), [EA](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38119182611), and [D0/full engine](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38119182563) each report SUCCESS in GitHub Actions. P1.1-A has independently inspected two successful jobs (`p11-python`, `p11-chromium`); A4 receipt reports 30 Python tests and 86 Chromium checks, but this B0 audit did **not** rerun those tests. `849ebd4f → 04accfe5` changed only A4 documentation.

## 3. System and interface inventory

```text
External PDF/MinerU/structured parser [P2 admission NOT ACTIVE]
    -> qualified versioned source package [future B1/P2 boundary]
    -> same-origin /manage: producer / manager (P1.1-A synthetic operations)
       -> /v1/tpa/{sources,projects,batches,overview,tasks,...}
       -> tpa_synthetic.sqlite (Project/OperationalBatch/Placement + state + events)
       -> original TPA publish/assign/revoke controller
    -> same-origin /: separate authorized EA expert login
       -> /v1/ea/tasks -> /workpack -> task-allowlisted source/version
       -> bilingual/PDF.js/quote anchoring + independent/review freeze
       -> ea_synthetic.sqlite, non-Gold only
    || strict separation from D0 NDS R0/R1/R2, 19-field contract.
```

Confirmed code anchors:
- [D0 unified app, route installation, middleware and same-origin security](https://github.com/gitzhangcd/NutriFoundation/blob/workbench-tpa-p1.1-a-management-ux-spec/apps/workbench/d0/d0_app.py)
- [Operations API](https://github.com/gitzhangcd/NutriFoundation/blob/workbench-tpa-p1.1-a-management-ux-spec/apps/workbench/d0/tpa_projects_adapter.py)
- [Immutable Project/Batch/Placement persistence](https://github.com/gitzhangcd/NutriFoundation/blob/workbench-tpa-p1.1-a-management-ux-spec/apps/workbench/d0/tpa_projects.py)
- [Legacy TPA controller and routes](https://github.com/gitzhangcd/NutriFoundation/blob/workbench-tpa-p1.1-a-management-ux-spec/apps/workbench/d0/tpa_adapter.py)
- [Management shell and navigation](https://github.com/gitzhangcd/NutriFoundation/blob/workbench-tpa-p1.1-a-management-ux-spec/apps/workbench/d0/web/manage.html)
- [P1.1 client-side flows](https://github.com/gitzhangcd/NutriFoundation/blob/workbench-tpa-p1.1-a-management-ux-spec/apps/workbench/d0/web/tpa_p11.js)
- [P1 original task actions](https://github.com/gitzhangcd/NutriFoundation/blob/workbench-tpa-p1.1-a-management-ux-spec/apps/workbench/d0/web/tpa_manage.js)
- [Existing expert mode and source anchors](https://github.com/gitzhangcd/NutriFoundation/blob/workbench-tpa-p1.1-a-management-ux-spec/apps/workbench/d0/web/ea_mode.js)

Contract evidence:
- Project / batch / task creation uses original D0 session, strict producer role and CSRF/Origin guard.
- Operations data uses the existing private TPA SQLite, immutable UPDATE/DELETE triggers, same transaction for new task+placement, idempotency records and append-only TPA event calls.
- Existing `POST /v1/tpa/batches/drafts` (legacy 1–7 atomic receipt) remains distinct from persistent OperationalBatch; historical tasks stay in explicit Legacy bucket.
- Manager and producer receive operational metadata; dedicated auditor authority stays separate. EA and NDS actors cannot read the management APIs; manager cannot access EA original source units or independent candidates.
- A4 acceptance documents exact non-regression over original D0, PDF.js/bilingual/SourceAnchor, NDS 19 fields and EA strict-blind. **This confirms synthetic engineering testing only.**

## 4. B0 gap matrix

Legend: **P0** required before promoting an operational UX baseline; **P1** planned next module; **GATE** intentional real-science/production prohibition. Evidence classes: CODE (source reviewed), CI (historical GitHub success), SPEC (design intention not code).

| ID | Area | Verified observation | Priority / owner-stage | Test/acceptance exit |
|---|---|---|---|---|
| B0-01 | D0 expert reuse | Single D0 `/`, EA opt-in in-page, three-pane reader and original 19 fields inherited; no second app in PR29 | PASS · retain A5 | Original D0/EA/NDS PDF.js/anchor/browser suite unchanged |
| B0-02 | Manager security | Same-origin cookie/CSRF/Origin, producer/manager write separation, synthetic test identities; server controls authoritative | PASS within synthetic · retain | Unauthorized EA/NDS/manager source/candidate requests denied |
| B0-03 | Project→Batch→Task | Persistent immutable operational tables, task creation+placement atomic; legacy behavior preserved | PASS within synthetic · retain | Idempotency/rollback/restart/legacy tests |
| **B0-04** | **Task Center ergonomics** | `renderTasks` still generates legacy task **cards**, not a real columnar table with integrated filtering, progress and bulk-oriented browsing | **P0 · A5** | True table, filters, paging, keyboard and actionable states on desktop/tablet/mobile |
| **B0-05** | **Five-step wizard** | `renderWizard()` switches two original form fieldsets; stages 3/4/5 mainly instruct users to act in a **separate task list**, rather than a cohesive state-driven wizard | **P0 · A5** | Guided S1–S5, state/role gates, preserved receipts, no bypass of backend transition |
| **B0-06** | **Task detail/recovery** | `opsTaskDetail` renders an inline section, not the planned right-side detail drawer; shows basic profile/status/source but no complete contextual lifecycle/receipts; retry keys generated anew by client for publish/task create | **P0 · A5** | Accessible drawer, safe full source SHA/version, permitted actions and receipt; same-intent retry key survives uncertain network result |
| **B0-07** | **Management→expert handoff** | Backend published TPA tasks are listed through EA only after expert authorization; manager UI supplies an `/` link but not a clear task-specific handoff/revocation outcome view | **P0 · A5** | Synthetic publish→separate EA login→correct task/versions→quote/review/freeze→revoke, with no impersonation or cross-arm leak |
| **B0-08** | **List scale/read-model** | `fetchViews` downloads all scoped tasks in pages up to 10k, `loadProjects` does per-project batch fetches, but `renderTasks` uses separately fetched unfiltered original list and client filtering | **P1 · A5/B4** | Consistent server-backed pagination, filtered counts, no incomplete-list illusion, 100+ synthetic tasks stress test |
| B0-09 | Scientific source library | '科学资料库' is an explicit placeholder; existing API only exposes metadata for seven fictional source types; MinerU/PDF admission absent by design | P1 · B1, P2 science gate | Source registry UX/identity/lineage and preview for synthetic first; rights-qualified source admission remains separately gated |
| B0-10 | Agent preparation | 'Agent 准备' placeholder; current candidates are fixed `SYN-FIXTURE-NOT-AN-LLM`, not a real Agent execution/provenance chain | P1 · B2, P3 science gate | Synthetic lifecycle/status and freeze receipts first; real Agent only after provenance/security review |
| B0-11 | Expert and assignment | Existing P1 supports fixed mode-specific synthetic accounts, assign/publish/revoke; no real expert credential, conflict check or eligibility record | P1 · B3, P3 science gate | Synthetic roster/assignment view and projection; formal human onboarding remains NO-GO |
| B0-12 | Quality/exports | '进度与质控', '审计与导出' are placeholders; `/v1/tpa/audit` remains auditor-only; `PUBLISHED` says nothing about actual read/review completion | P1 · B4/C | Only server-verified aggregate states; scientific quality/Gold prohibited absent independent gold-owner process |
| B0-13 | Versioned master traceability | P1.1-A page spec and A1/A4 present; complete discussed Master Plan v1.1 itself absent from audited PR29 Git tree | P1 · A5 documentation | Link exact canonical Master and trace all relevant requirements or mark not evidenced |
| B0-14 | Release and real research | PRs #23/#26/#27/#28/#29 all Draft/unmerged; real PDF/MinerU, expert rights and science validation absent | **GATE** | Independent science+security owner signoff; no main merge, real-world publishing or Gold now |

**Additional code-review note (not a demonstrated CI failure):** The frontend passes a new `crypto.randomUUID()` for each create/assign/publish attempt. Backend supports idempotent replay of the *same* key, but a client-side timeout followed by a fresh click does not necessarily replay the same intent key. Add an operation-intent pending/reconciliation mechanism in A5, and test ambiguous network outcomes; historical A-UI-11 API-level idempotency tests do not alone prove UI retry resilience.

## 5. A5 implementation backlog (do before new full B-module screens)

**A5-01 — Task table and state-safe navigation:** Replace card-only Task Center with responsive task table; keyed rows: ID, Project/Batch/Legacy, source type+version, strategy, exact TPA state, assignee, allowed next action. Backend pagination, state/scope filters, clear unknown metrics. Never show source units or candidate metadata.

**A5-02 — Transactional wizard UX:** Keep *existing* producer `/v1/tpa/**` endpoints; bind S1 selection, S2 draft, S3 validate+freeze, S4 prepare and S5 separate-manager assign+publish to one resumable state-aware interaction. Disabled future steps cannot effect hidden server writes.

**A5-03 — Detail drawer and receipts:** Accessible task-detail drawer with deep-link/history/back semantics; exact allowed source versions and SHA; immutable placement; safe receipts and retry/reconcile. No implicit expert comprehension status. Preserve audit append-only semantics.

**A5-04 — Safe expert handoff:** Show task ID and mode-specific expert login instructions without sharing credentials or changing roles; verify published/revoked access in a distinct EA browser session. Expert original bilingual/PDF.js/anchors remain original D0. Route from manager to expert cannot grant entitlement.

**A5-05 — Regression and compatibility:** Re-run original P1, EA, D0/engine and P1.1 suites; add Playwright synthetic E2E for S1→S5, task table 100+, mid-operation retry, stale session/revocation, source SHA, keyboard/mobile, legacy, strict-blind denial. Record actual new run IDs. A5 must not mutate `runs/**`, `src/nutrifoundation/**`, `apps/workbench/c1/**`, `c2_1/**`, `c2_2/**`.

## 6. Sequential post-A5 roadmap

1. **P1.1-A5**: management UX convergence + safe handoff + independent acceptance.
2. **P1.1-B demo/integration**: join existing A5 management and unchanged D0 expert pages in one *synthetic* end-to-end walkthrough, not a new duplicate app. Distinguish this demo substage from **this B0 audit** to avoid identifier ambiguity.
3. **P1.1-B1**: scientific source-library operations UI / synthetic qualified-source packet inspection, rights/state interfaces (real source P2 gate).
4. **P1.1-B2**: Agent preparation UX and provenance-shaped synthetic status, without invoking real models or leaking blinded candidates.
5. **P1.1-B3**: expert roster, qualification placeholders, assignments, access/revocation and role-safe cross-page state; real experts P3 gate.
6. **P1.1-B4**: multi-step synthetic E2E acceptance, failure recovery, performance and non-regression receipts.
7. **P1.1-C**: QA/progress/read-only audit exports scoped to their own authorized principals, metrics validated; then independent P2/P3/P4 scientific/security gates.

## 7. Decision and mandatory NO-GO

**B0 decision:** The PR29 branch *does* extend the original D0 Workbench correctly at the architecture and synthetic-runtime level. It is a suitable code base for **A5 incremental UX repair and subsequent B1–B4 work**, not a production or scientific release. Do not fork a new standalone app. Do not merge any draft Workbench PR to main; do not deploy public services, ingest real sources, enroll real experts or produce Gold on the strength of this audit.

**Not certified in B0:** fresh local executable tests, full real-source bilingual fidelity/rights, actual LLM candidate provenance, clinician qualification, human UX acceptance, security pen test, cloud production deployment, or scientific Gold validity. Carry those as explicit separate future acceptance gates.
