# Workbench｜跨项目规范缺口与冲突登记簿 v0.1

> 截止：2026-10-13；**STATUS: AUDIT_OPEN / DECISIONS_NOT_SIGNED**  
> 绑定：`Workbench_Document_Register_v0.1.json`，GitHub `docs/governance/Workbench_Document_Governance_Master_v0.1.md`。  
> 科学文件本阶段只读，不会自动修改 `runs/**`、`src/nutrifoundation/**`。

## 1. 按阻塞程度排列

| ID | 优先级 | 精确问题与已有证据 | 当前结论 | 解除条件 | 负责角色 |
|---|---|---|---|---|---|
| NC-01 | **P0** | `SIS-Main@main/specs/System_Intelligence_Science_v0.3.1.md` 存在，文件首尾与版本记录指向 R4；但 `Workbench_System_Master_v0.2.md` 上游写的是 SIS v0.3.1 R5 | R5 Master **尚未定位**，不得声称科学对齐完成 | 查明 R5 的权威仓库/文件/tag/版本及冻结 SHA，执行影响和 Non-Regression 审计 | SIS scientific owner |
| NC-02 | **P0** | `SIS-Med@main` 本轮仅发现两份 AMIE 教学 Markdown；Workbench 上游依赖 SIS-MED R6 | R6 Master **尚未找到** | 将正式 R6 Master 置于审定的私有权威仓库/固定 ref，记录科学适配裁决 | SIS-MED scientific owner |
| NC-03 | **P0** | Nutrition Foundation v0.1 被列为科学层级，但本轮未确认其唯一权威路径与 blob | 无法证明 Workbench 绑定的是正确版本 | 明确 canonical document、owner、sha、与当前 NDF/NDS 的依赖边界 | Nutrition Foundation owner |
| NC-04 | **P0（正式 R1 前必须阻断）** | `NutritionDecisionCaseBundle_v0.2.json` case revision=r3；NDS R0 workpack / packet case_ref=r3；`Materialized_Projection_Views_v0.2.json` case_ref=r2；`A3R3_Rebind_Delta_Manifest_v0.1.json` target_case_ref=r2 | **确切版本差异已确认**，不能推断语义相同 | owner 签署 r2 历史 / r3 当前投影关系；必要时新建 r3 projection 并重跑严格盲法、证据和 schema 测试 | NDF-D2 + NDS-R1 scientific owners |
| NC-05 | **P0（正式 Expert Freeze 前）** | `Judgment_Freeze_Contract_v0.1.json` 中 R0/R2 `source_workpack` 仍指向 v0.1，当前 `R0_Human_DeNovo_Workpack_v0.2.json` 与 `R2_PreAI_Workpack_v0.2.json`；Workbench Adapter Matrix 记录此问题 | 需要独立版本兼容证明，不能隐式替代冻结契约 | 严格字段映射与 Lossless Mapping Test + negative fixtures + signed adapter compatibility | NDS-R1 owner / adapter owner |
| NC-06 | P1 | 原始 `NutriFoundation Workbench Development Master Plan v1.1` 未在核查的 `main` 和 PR #41 开发树发现同名文件；现有 Workbench System Master v0.2 存在 | 需求溯源尚不完整 | 归档原件，并对比 v1.1 与 v0.2/P2.1 功能 Delta；不把二者误认为同一文件 | Product owner |
| NC-07 | P1 | 原始 `nutrifoundation_p2_scientific_source_portal_demo(1).html`、`Archive.zip` 未在两棵被检查树发现；PR #38 有二次审计报告 | 视觉验收原始证据链未闭合 | 保存经脱敏的原件 hash / fixture ref、截图工件及验收日期；受限原件改用私有存储 | UX / QA owner |
| NC-08 | **P0（真实来源前）** | GitHub public 仓库有 Batch001 registry、bounded text 和 5:2 ZIP 工程 fixture，但没有逐一核实合法完整原件、原件 SHA256、许可用途及来源适用范围 | 真实资料入库 NO-GO | 来源、版权、存储、Machine Processing 与 Expert Exposure 分用途签署 + 原件/解析器/Unit QA lineage | Source steward + independent Auditor |
| NC-09 | **P0（正式部署前）** | Draft PR #36→#37→#38→#40→#41 均未合并 `main`；`main` 没有 Workbench 代码目录；阿里云部署 SHA 未获取 | `Git pushed` ≠ `merged` ≠ `deployed` | 按依赖顺序独立 Review / exact SHA CI / 合并评估，云端软件版本与运行时数据独立核对 | Engineering / DevOps |
| NC-10 | P1 | `runs/NDF/D1/A2R/A2R_Source_Snapshot_Gap_Register_v0.1.json` 是早期打开的来源差异；A3R.1、A3R.3 后续报告分别记录通过和再绑定 | 不应把历史 gap 不加判别认定为当前尚未闭合 | 逐项验证后续 closure receipt 与 source revision/hash，区分历史修复和残留新缺口 | NDF-D1 source owner |

## 2. 文档与科学状态必须分开

| 可核验事实 | 不能由此推断 |
|---|---|
| SIS v0.3.1 文件存在于 `SIS-Main@main` | R5 已完成正式权威整合 |
| NDF-D1-A3R3 conformance PASS | 任何 R0/R1/R2 当前输入的所有版本差异均自动消失 |
| NDS-R1 P0.1 Operational Readiness PASS | 有真实合格专家 / 已冻结 J_preAI / 有 Gold |
| P2 Source Package synthetic-freeze 成功 | 真实文献版权及科学适用性资格已签署 |
| PR #41 九项 CI PASS + 用户窄屏 UX 验收 | 当前 main 已合并、阿里云部署了最新版本、整套真实科研数据可用 |
| 文件的 Git blob SHA 可核查 | 原始 PDF 的 SHA-256/版权/证据原文可核查 |

## 3. 每条冲突的正式处理回执

```yaml
conflict_id: NC-XX
scope_and_owner: "..."
current_exact_refs:
  - {repo: "...", path: "...", commit_or_tag: "...", git_blob_sha: "..."}
symptom: "..."
scientific_or_engineering_impact: "..."
decision: PENDING|APPROVE_COMPATIBILITY|REQUIRE_NEW_VERSION|SUPERSEDE|REJECT
normative_delta: null
old_version_retained: true
independent_reviewer: PENDING
ci_negative_test_receipt: PENDING
exposure_leakage_gate: PENDING
status: OPEN
```

**处置原则：** 对历史冻结文档使用新 revision、兼容证明或 supersession 记录，不通过“改旧 JSON 字段”制造表面一致。每条问题解开后在 GitHub Issue #42 和本文件记录 SHA / 审核角色 / 验收；没有证据不得标记 CLOSED。

## 4. 不阻塞当前哪些工作？

NC-01～NC-05 **必须在正式科学采集、真实专家试点与 Gold 声明前消除**；在此期间可以继续隔离合成 UX 改进、资料目录梳理及测试验证，前提是不改变受保护的科学输入权限和 R0/R1/R2 时序。

NC-06/07 是产品可复现性与设计追踪问题，应在 P2.1-E 设计和 UX 最终验收前完成。NC-08/09 是真实资料/正式部署的硬闸门。

## 5. 当前结论

```text
DOCUMENT_INVENTORY: BUILT_ON_VERIFIED_GIT_BLOB_SHAS
NORMATIVE_HIERARCHY: PROPOSED / REVIEW_PENDING
SCIENTIFIC_R5/R6_LOCATION: NOT_VERIFIED
CASE_R2_R3_BINDING: OPEN_SCIENTIFIC_CONFLICT
WORKPACK_FREEZE_V0_1_V0_2_COMPATIBILITY: REQUIRES_SIGNOFF
REAL_SOURCE / EXPERT / GOLD / PRODUCTION: NO_GO
UPSTREAM_MUTATION_IN_THIS_BRANCH: NONE
```
