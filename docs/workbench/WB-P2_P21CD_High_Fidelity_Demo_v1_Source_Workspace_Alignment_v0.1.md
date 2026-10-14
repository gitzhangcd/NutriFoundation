# WB-P2.1-C/D｜Scientific Source Workbench · High-Fidelity Demo v1.0 Alignment v0.1

> Status: **IMPLEMENTED_UI / AWAITING_CI_AND_HUMAN_VISUAL_ACCEPTANCE / REAL_SOURCE_NO_GO**
>
> Implementation branch: `workbench-p2-1-cd-source-workspace-v1-alignment`; parent: `workbench-p2-1-b-source-centric-ux` (PR #41). Scoped strictly to the original D0 `/manage#/studio` and shared independent P2 QA surface.

## 1. UI reference, baseline, and scope

- UX north star: user-confirmed **NutriFoundation 科学资料工作台｜高保真 HTML Demo v1.0**, including its predecessor P2 scientific source portal HTML reference and the P2.1-A/B convergence decisions.
- The deployed Workbench visual language (PR #36 / #37, white + muted emerald, typography, cards, navigation) remains the visual authority. The reference Demo **does not authorize** replacing global application navigation or inventing server capabilities.
- Retain exactly **one** primary `科学资料` entry and **six** in-content P2 tabs: 资料总览 / 来源登记 / 结构化处理 / 人工质量核验 / 科学来源资料库 / 审计与版本记录.
- Project/Batch controls remain collapsed by default and mean **source-version usage-reference filtering**, not provenance, qualification, ownership or expert grants. Audit is globally scoped and has no Project/Batch UI.

## 2. User-first source workflow

```text
列表查找版本
  → 查看单篇来源工作区（当前阶段 / 各环节证据）
  → 获取该角色许可的下一步
  → 来源登记 / 合成用途审核 / 结构化转换 / 独立 Human QA
  → 冻结合成资料包（服务器逐项验证）
  → 仅使用引用绑定；不提升真实来源、Gold 或专家权限
```

### Delivered changes

| Area | Interaction improvement | Scientific/permission constraint |
|---|---|---|
| Source list | Explicit origin switch: all, registered synthetic only, and fictional Demo only; persistent list-first position | Demo never counts as registered or qualified evidence |
| Row & empty state | Distinct row styling and truthful empty-state messaging | Search/status/type/reference filters still apply, without synthetic rows leaking into scoped results |
| Per-source workspace | Drawer is now a stage-guided document workspace with four checkpoints, next-step explanation, fast navigation, and provenance/SHA detail | Checkpoints summarize existing server state; no frontend eligibility or approvals |
| QA reader | Selected source identity, revision, stage and raw-document verification context above Unit progress | Only Curator can load server originals or submit independent Unit decisions |
| Responsive | Dense 2x2 checkpoint cards on desktop, 1 column on narrow screens; constrained source navigation controls and drawer | Horizontal table scrolling is local; global UI retains previous layout |
| Keyboard | Escape closes Studio drawer/wizard and returns keyboard focus to the active tab | Underlying server-side auth and CSRF gates remain unchanged |

### What is **not** delivered by this UI change

- Real PDF binary ingestion, DOI/PMID resolution, JATS/MinerU external service, rights qualification or live repository indexing.
- True continuous bilingual QA over a real lengthy scientific manuscript, verified unique PDF bounding boxes, automatic re-parse/revision repair, or complete human production signoff.
- Modification of existing Expert Workbench, NDS, EA, TPA B1–B4 or authoritative frozen scientific records.
- Production deployment, main merge, real human exposure, Gold or formal scientific acceptance.

## 3. Acceptance gates / no false PASS

1. `apps/workbench/d0/tests/browser_d0.py`: run native Chromium end-to-end at 390 / 680 / 740 / 768 / 1024 / 1440; verify no global horizontal overflow, six tabs, collapsed scope, Demo isolation, drawer checkpoints, QA context, existing B1 entry and role-safe P2 lifecycle.
2. Run D0 P2 Python tests and existing A5, B1–B4, EA, TPA and D0 engine regressions **at the exact PR head SHA**.
3. Manual visual comparison against the actual high-fidelity Demo at overview/list, source drawer, QA, and narrow viewport. No pixel-fidelity or usability signoff is assumed by static inspection.
4. Independently verify that Manager/Producer cannot read raw source; Auditor cannot read Curator original; no forbidden Expert/Gold routes appear after clicking new controls.
5. Re-run on any substantive change before marking Ready for Review. Keep PR Draft while exact-SHA CI or visual/security acceptance is unverified.

## 4. Whole-program delivery ledger

| Phase | Current position | Next gate |
|---|---|---|
| P2.1-A navigation / responsive | Coded in upstream PR #40 | Preserve in end-to-end regression |
| P2.1-B list-first operations | Coded in upstream PR #41 | Preserve live role-guard tests |
| P2.1-C Demo/origin isolation | **Coded here** | Browser + separate-origin review |
| P2.1-D document workspace & QA navigation | **Partially coded here** | Long-form bilingual/full-source & rework workflow remain outstanding |
| P2.1-E cross-device / security acceptance | **Not yet accepted** | Exact-head CI, visual review and independent security/UX signoff |
| Real science / independent expert gate | **NO-GO** | Independent sources, license receipts, QA, immutable freezes and owner approval |

> Do not report "P2.1-D complete", "CI passed", "deployed", or "scientific sources qualified" until those checks are independently evidenced.
