# Workbench Page IA & Expert-Native UX Contract v0.2

> WB-P0.2-M0｜**DESIGN_FROZEN / UI_IMPLEMENTATION_PENDING**；2026-10-08。以 `Workbench_System_Master_v0.2.md` 为上位工程权威。本文件不声明页面已经开发。

## 1. One App Shell, dual profiles

采用一个统一 Shell：项目/任务 Sidebar、任务顶栏、可调的 Evidence Reader、Judgment/Review 面板、Evidence Anchor/Issue rail。**同一 work session 不等于所有材料都可见**：UI 接口只消费服务器生成的 `TaskReadModel`，不在浏览器本地按 arm 过滤完整原始数据。

- 左导航（全站）：我的任务 / 来源库 / 审核中心 / 审计与导出（依 RBAC/projection 决定）；管理员另见项目管理和 Profile 配置。
- 任务顶栏：项目、任务 ID、可见材料版本、流程和剩余工作、可恢复的保存状态。禁用“R2 PreAI 已完成百分比”等会影响实验的跨臂统计。
- Evidence pane：章节树、结构化 Markdown、原始 PDF、表/图、搜索和高亮、证据片段导航；按源版本显示 BBox 状态。
- Center pane：当前 profile 的专家自然专业问句、展开阶段、保存、条件性行动/未知/替代方案。
- Right pane：当前任务已授权证据锚点、未完成问题与非敏感进度；不在 R0/R2 pre-AI 显示 candidate 数量/被隐藏标签的标题。

默认 40/40/20 宽度比例仅为设计建议（可配置）；桌面 ≥ 1280px 为主要正式标注环境，窄视口优先只读/导航，不允许错误覆盖字段导致缺漏的正式锁定。拖拽分栏保持用户本地视图偏好，但不能改变任务的科学对象。

## 2. Route and page contract

| ID | Logical screen / route proposal | Main role | Data surface | Success condition |
|---|---|---|---|---|
| P01 | `/projects` Dashboard/My Tasks | Expert/Manager | own tasks, non-sensitive metadata | 可找到任务，不泄漏其他 arm 的内容 |
| P02 | `/tasks/:id/preflight` Qualification & Assignment | Expert/Manager | eligibility screen, task preview allowlist | QUALIFIED+BOUND 与 prior exposure 明确 |
| P03 | `/sources` Import/Library | Manager | source packages, parser diagnostics | hash/ZIP/package 校验，未授权文件不出现在 expert packet |
| P04 | `/tasks/:id/workspace?mode=reader` | Expert | authorized canonical units + PDF | 原文 ↔ anchor 可回放 |
| P05 | `/tasks/:id/workspace?mode=judgment` | Expert | profile-specific form, allowed source | 草稿可保存、恢复、未知/条件支持 |
| P06 | `/tasks/:id/freeze` | R0/R2 Expert | complete draft + receipt preview | 原子提交后只读；R0 永无 AI |
| P07 | `/tasks/:id/verify` | R1 Expert | frozen AgentCandidateSet + source spans | 逐项验证；禁止前置访问 |
| P08 | `/tasks/:id/reconcile` | R2 Expert | frozen J_preAI + frozen Agent Set | postAI 分歧不覆盖 preAI |
| P09 | `/reviews` and `/reviews/:id` | Reviewer/Adjudicator | authorized frozen outputs | 差异另存，非独立真值 |
| P10 | `/audit` and `/exports` | Auditor/Manager | filtered event/manifest logs | 完整 provenance 与 least privilege |
| P11 | `/settings/profiles` | Manager | versioned task profile configs | profile 改版不重写历史记录 |

路径为**待实现的路由提案**，并不是当前 `wb-p0.2-b1` 已经提供的地址。Reader/Judgment 用同一 workspace route + mode switching，以免任务上下文丢失。

## 3. Main task workspace interaction

```text
┌──────────────────────────── Task ID / Input Surface / Save State ──────────────────────┐
│ Sidebar  │ Reader: structured text / PDF │ Expert native questions │ Anchors / Progress│
│ docs     │ headings / tables / figures   │ one stage expanded       │ quote + source    │
│ tasks    │ highlight selected quote      │ multiple actions/unknown │ unresolved items  │
│ sections │ bidirectional page replay     │ save / next / freeze     │ limited indicators│
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**核心交互 I-01**：选中 Markdown 片段 → 侧边标注条 → `Create anchor` → 后端校验 quote/UTF-16/revision → 保存 → 锚点项显示来源页及定位级别。若 PDF text-layer 多次匹配，显示 `AMBIGUOUS` 且不能画精准高亮。反向点击 PDF 高亮，应返回当时确切 DocumentUnit，不能跳转到新版内容。

**I-02**：切换原件查看。Reader 显示 PDF.js canvas 和 BBox overlay；旋转/CropBox 映射必须与其实际 viewport 一致。无文字层或未经校验的页面，降级页级阅读并明确提示“尚无精确锚点”。

**I-03**：根据 profile 选择输入问题/标签。选中的 source anchor 自动附到所编辑的允许字段；用户确认后保存草稿。锚点可 0/多条取决于题目必要性；不能在无证据情形强迫虚假引用。

**I-04**：草稿自动保存：已保存/保存中/失败/冲突四类明确反馈；页面刷新恢复字段顺序、值和 linked_anchor_ids。`409_REVISION_CONFLICT` 提供重新载入或创建待审核 fork，禁止盲目覆盖。

**I-05**：Unknown/Abstain 分支必须支持“资料不足/超出当前范围/待检查源”等合理理由；允许多种可接受方案、conditional 与 unsafe 并存；禁用“一键自动形成最佳答案”默认值。

**I-06**：Lock 前 overview 应完整列出准备被锁定的所有专家字段、引用、未知项、来源包版本与暴露声明；二次确认不可省略。正式 R2 freeze 之前绝不检索/展示 Agent 输出。

**I-07**：R1 验证仅从候选冻结后入口进入，每条卡片包含候选结论、source spans、`ACCEPT/REJECT/MODIFY/IRRELEVANT/UNCERTAIN/NEEDS_MORE_EVIDENCE`、理由，按最终工作包提交。R1 没有 “J_preAI” 操作。

**I-08**：R2 postAI 页面以“已锁定的专家独立判断（只读） vs 允许暴露的候选”为两列，对应中间 reconciliation 操作；关闭候选不会抹除 exposure history；新增 `J_postAI`。

## 4. Profile-specific stage mapping

### Evidence Annotation Profile（科研论文）

- 文献基本特征、设计和资料来源；
- 效应/结局与证据单元；
- 适用性、偏倚与不确定性；
- 决策边界/潜在影响；
- 证据核查和提交。

### Expert Decision Capture（NDS-R1）

- 可见事实 + `decision_focus`；
- `decision_changing_missing_information`；
- 当前、条件性和不可行/不安全行动 + 七类 `reference_set`；
- `process_action / monitoring_needs / uncertainty_notes / rationale_notes`；
- 信息完整性、暴露声明及 arm-specific submission。

**注意**：这是自然语言展示分组，不新增科学事实类别；详细字段映射在 Scientific Adapter Matrix。R1 始终使用候选验证 Profile，R2 后半段使用 reconciliation Profile。

## 5. Arm/phase dependent presentation (server must authorize)

| Display element | R0 | R1 before Agent freeze | R1 after Agent freeze | R2 preAI | R2 postAI |
|---|---|---|---|---|---|
| Approved case view | yes | only approved preparation view | yes | yes | yes |
| Human Baseline Source Packet | yes | not a substitute for R1 controlled sources | R1 allowlisted spans | yes | freeze-bound provenance |
| Independent judgment editor | R0 | NO | NO | R2 | preAI read-only |
| Frozen Agent candidate | NEVER | NO | yes | NO | yes after valid gates |
| Candidate differences | NEVER | NO | verification-only | NO | yes |
| Other experts' records | NO | NO | NO | NO | NO except authorized later review |
| Meta-audit/final reference/hidden data | NO | NO | NO | NO | NO |

All modes must be backed by separate server projections; rendering a component with `display:none` is **not acceptable**.

## 6. Component taxonomy and UI state

- `TaskShell`, `TaskStatusHeader`, `SourceTree`, `StructuredUnitRenderer`, `PdfCanvasReader`, `EvidenceSelectionToolbar`, `AnchorRail`, `SourceSpanInspector`, `JudgmentStageAccordion`, `FieldEvidenceBinder`, `ReferenceSetEditor`, `UnknownReasonEditor`, `DraftStatus`, `FreezeReviewDialog`, `AgentCandidateCard`, `ReconciliationDiff`, `AuditTimeline`.
- UI states: `LOADING`, `EMPTY`, `READY`, `EDITING`, `SAVING`, `SAVED`, `CONFLICT`, `LOCK_READY`, `LOCKING`, `LOCKED`, `FORBIDDEN`, `SOURCE_STALE`, `BBOX_UNRESOLVED`, `PROTOCOL_DEVIATION`.
- Error content must explain action and recovery; must not leak hidden candidate existence or label.
- Accessibility: keyboard reader selection, visible focus, WCAG 2.2 AA as design target, color-independent status, zoom reflow; RTL/vertical layouts and scanned OCR are not guaranteed in v0.2.

## 7. Designed-not-deployed boundary

B1 already supplies local structured reader, PDF.js locator and bidirectional replay. **None** of P01/P02/P05–P11 are claimed deployed by this M0 design. A UI screenshot alone never satisfies authorization, freeze or scientific usability acceptance. Formal acceptance requires Playwright/Chromium E2E, API isolation tests, reload recovery and real expert pilot after separate permission approval.
