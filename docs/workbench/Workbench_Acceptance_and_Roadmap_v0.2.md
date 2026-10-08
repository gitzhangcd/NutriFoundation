# Workbench Acceptance, Non-Regression & Delivery Roadmap v0.2

> WB-P0.2-M0｜**DESIGN_FROZEN / RUNTIME_VALIDATION_PENDING**。本文区分现有 reader 技术证据、规范验收、后续真实专家实验。任何“PASS”仅适用于该项已实际执行的测量。

## 1. Engineering evidence already available

| Stage | Evidence scope | Actual status | Exclusion |
|---|---|---|---|
| WB-P0.2-P0 | scientific base pinned; reuse contract and protected paths | PASS_WITH_EXPLICIT_COMPATIBILITY_BINDING | 不代表人体实验 |
| WB-P0.2-A | 真实 5:2 diet PDF→structured Markdown→canonical reader→anchors | implementation passed local tests / committed | 不代表科学验证 |
| WB-P0.2-B | 原始 PDF 文字层唯一匹配→BBox→PDF.js 双向回放 | native PDF.js CI PASS | 不等于 OCR 全覆盖 |
| WB-P0.2-B1 | 旋转/CropBox、双栏、伪拼接、重复文字、扫描与 hash fail-closed | 37 Python tests PASS；native Chromium CI `37750463593` PASS | 没有专家 UI/冻结/角色实验 |
| WB-P0.2-M0 | 系统 Master + 四份精确 companion specs + manifest | 本阶段**设计审查与冻结** | 未执行新 UI runtime tests |

Repo engineering baseline: `workbench-wb-p0.2-real-paper-roundtrip@34386dd9d0b82ba0ad319fa0d46ed0eb9d8c9a00`; frozen scientific base `ndf-d1-scientific-core-thin-slice@2259fdac9502541909a70d5d79c3460cecb6f657`。

## 2. Gate protocol

M0 合格门禁要求：

1. master exists and is self-contained; four companions resolve its exact roles/profile/object/phase terms;
2. all current NDS-R1 upstream scientific paths and R0/R2 current v0.2 payload versions are cited correctly;
3. R0, R1, R2 workflows are demonstrably **not** merged;
4. reader source/anchor and later judgments never silently promote scientific Gold;
5. no source allowlist widening or engineering fixture contamination of NDS-R1;
6. each logical route specifies roles, data surface and failure status;
7. exact state/API/transaction/immutability and exposure constraints specified;
8. C0–C4 deliverables and negative tests have unambiguous acceptance expectations;
9. Git diff relative to pinned science contains no changed NDF/NDS frozen artifacts;
10. manifest files are versioned and committed with checked SHA and commit ID.

M0 通过仅表示 **design baseline frozen**；C0 起必须提供可运行 UI 与至少完整 mock E2E。任何实证成功结论必须增加人类专家资格、任务隔离、合法独立判断、研究设计与独立核查等科学证据。

## 3. Non-regression matrix (minimum executable fixtures)

| ID | Trigger | Expected server result | Related contract |
|---|---|---|---|
| NR-01 | R0 GET candidate, diff, image thumbnail, export, prefetch | 403/404 no leak + audit | Exposure Lock v0.1 |
| NR-02 | R1 candidate not frozen opens verify | 403; HOLD | R1 HoldPack v0.1 |
| NR-03 | R1 candidate frozen but no source spans | 403; HOLD | Role Input Surface v0.1 |
| NR-04 | R2 Agent output before J_preAI freeze through API, cache or SSR | 403/no bytes | R2 Lock Registry |
| NR-05 | R2 freeze valid, then postAI edits preAI snapshot | forbidden; old hash unchanged | Judgment Freeze v0.1 |
| NR-06 | Same real expert attempts R0 and R2 on same case | reject second bind | Slot Binding v0.1 |
| NR-07 | Hidden diet value, SRS evidential state or final reference in R0/R2 preAI packet | policy rejection | Human Packet v0.2 |
| NR-08 | Unapproved imported 5:2 PDF appears in R0 source list | absent + deny direct URL | Role Input Surface |
| NR-09 | Exact PDF quote repeated/cross block/cross-table/scan no text | no exact BBox | PDF_PAGE_BBOX/0.2 |
| NR-10 | Original PDF changed/revision stale/UTF-16 surrogate split | reject anchor replay | CanonicalDocument/SourceAnchor |
| NR-11 | Two tabs save different draft revisions | 409, no silent overwrite | Draft contract |
| NR-12 | Freeze retried twice with same idempotency key | one immutable receipt | Freeze transaction |
| NR-13 | Exposure-event database commit fails | candidate response withheld | Audit/Exposure transaction |
| NR-14 | Reviewer sees pre-lock other-arm data | forbidden | Role projection |
| NR-15 | Import/parser PASS tries creating Gold/QualifiedReference | forbidden/unsupported | Scientific ownership |
| NR-16 | Frozen NDF/NDS file changed by PR | fail CI / review | P0 scientific base gate |
| NR-17 | Workpack v0.1/0.2 conflicts in field semantics | BLOCK_CONTRACT_CONFLICT | Scientific Adapter matrix |
| NR-18 | Source document re-conversion after active draft | create revision/task migration gate | Version-bound reader |
| NR-19 | Candidate existence leak in sidebar counts, URL, logs, search | 0 sensitive bytes | Unified projection policy |
| NR-20 | Test placeholder qualification counted as real human | reject empirical status | Expert qualification rules |

Security checks must test **server API response and stored data**, not only rendered elements. No automated green result can substitute for the actual submitted expert judgment and scientific verification.

## 4. C0–C4 executable roadmap

### C0｜Design-to-code interface contract and acceptance fixtures

Deliver: shared design tokens, 11 logical page wireframes and flows, two distinct `TaskProfile` field maps, exact R0/R1/R2 visual projection state chart, sample read-models **clearly tagged synthetic**, API OpenAPI draft, backend permission decision table, component props/stories, keyboard UX cases. Required pass: contract mapping roundtrip, no hidden data in mock fixtures, reviewed science compatibility issue v0.1→v0.2. **No real expert onboarding yet**.

### C1｜Unified Reader + Expert-Native Draft vertical slice

Deliver: web app shell, task queue, TaskWorkspace, integrated B1 Reader, FieldAnchorBinder, five expandable *profile-specific* stages, draft persistence and conflict handling, test-only engineering identities. Run refresh/resume, wrong anchor/version, unknown/conditional/reference set preservation, responsive desktop E2E. **All task fixtures synthetic**. Must not implement a permissive candidate list endpoint.

### C2｜Scientific Adapter / qualification / exposure / freeze

Deliver: real identity workflow, NDS-R1 workpack binding, source packet projection, arm machine, immutable snapshots, transactional receipt, isolated candidate vault, enforce R0 never Agent/R1 AgentFirst/R2 lock-first, exposure audit and negative tests. Must fail non-regression NR-01..NR-20 if violated. For a real pilot, require separate scientific/ethics/data approval and real qualified experts.

### C3｜Review/reconciliation/audit/export

Deliver: frozen candidate imports, R1 item verification, R2 differences and J_postAI, Reviewer/Adjudicator with separations, versioned export, audit trail and provenance verifier. Full multi-role integration CI; no postAI override of independent human baseline.

### C4｜Operational and human pilot readiness

Deliver: PostgreSQL / object-storage migration, authentication, 2FA as policy requires, role-restricted storage, restore tests, security audit, accessibility/responsiveness, real expert usability pilot, training and governance playbooks, measured burden/accuracy/error analysis; independent NDS scientific validation gates remain separately owned.

## 5. C0/C1 go/no-go milestones

- **C0 Gate**: Page-to-contract traceability 100% for user-visible science fields; prototype does not preload hidden candidates; adapter reconciling current v0.2 has documented tests; ADRs for chosen architecture.
- **C1 Gate**: real public PDF retains B1 anchor fidelity inside integrated UI; full synthetic expert draft saved/reloaded without loss, source binding exact, React/JS backend tests pass.
- **C2 Gate**: all three arms have distinct tested transitions; all forbidden projections actually deny, freeze durable/atomic, out-of-order attempts create audit record; exact provenance matches scientific source packet.
- **C3 Gate**: R1 and R2 differences are correctly represented and frozen outputs immutable; reviewer receives only authorized frozen data, event replay recovers exposure order.
- **C4 Gate**: clinical/nutrition experts report usability data under approved protocol; privacy, security, reproducibility and investigator sign-off obtained. No “publication-grade” claim from engineering metrics alone.

## 6. Evidence reporting rule

A phase report must state `commit`, `test command`, `runner/local environment`, `fixture list`, `pass/fail counts`, `screenshots/artifacts`, `known gaps`, `science exclusion`, `protected diff`, `next gate`. No report should say "scientifically verified" solely because Markdown parsing/BBox/React E2E succeeds.

For controlled tests distinguish: `SYNTHETIC_ENGINEERING_ONLY`, `REAL_PUBLIC_DOCUMENT_ANNOTATION_DEMO`, `REAL_HUMAN_EMPIRICAL_WORKFLOW`. These flags are mutually distinguishable in manifest and exports.

## 7. M0 status convention

M0 records: `PASS_DESIGN_BASELINE_FROZEN / IMPLEMENTATION_PENDING / NDS_R1_P0_1_EMPIRICAL_CAPTURE_PENDING` after remote commit/file verification. It is not a pass of C0–C4. New feature work should branch as a reviewable PR from the protected M0 code lineage; do not force-push archived A/B/B1 technical evidence.
