# Research Workflow · 数据来源到科学实验

> 面向研究生/科学资料处理人员。本页梳理**科研动作的依赖关系**，不声称 Workbench 已把真实数据和专家 Gold 打通。

## 0. 科学问题与实验位置

```text
NDS 科学问题/DecisionEpisodeNeed
  → NDF-D1 精确证据薄片（SourceArtifact → EvidenceUnit → ScientificClaim）
  ─┐
  └→ NDF-D2 观察数据/CaseBundle（Observation != Evidence）
          ↓
       applicability、decision tension、information gap
          ↓
       NDS-R1 独立专家判断 R0/R1/R2
          ↓
       冻结的 J / 审核、仲裁 / 合格 Reference
          ↓
       AI Nutri Paper 1 或其他预先注册的系统/模型对比实验
```

### 真实科学来源必须经历的步骤

1. **来源登记与用途审查**：记录 DOI/PMID/PMCID/版本/勘误撤稿，逐用途确认存储、机器处理、专家阅读许可；无原文或许可时 fail-closed。
2. **外部结构化预处理**：PDF/JATS/HTML/Markdown 经受控 parser（可用 MinerU 等）形成带 provenance 的 Document IR；转换完成不是科学接受。
3. **源文核验**：Source Curator 审查 DocumentUnit、表图、页码/必要时 BBox、原文 Span、哈希与译文辅助层；失败创建不可变修订和返工。
4. **Source Package 冻结**：确保来源、权利、QA、版本引用可回放；`freeze != QualifiedReference`，不自动授权专家。
5. **任务准入与角色**：Manager 配置 Project/Batch/Task；Scientist/Independent Auditor 根据 Role Input Surface 分配允许的来源。
6. **专家科学判断**：R0 完全 de novo；R1 仅核验冻结 Agent 候选；R2 先冻结独立 preAI 再受控展开 Agent。
7. **独立复核与 Gold Gate**：分歧仲裁、Reference-set、安全/不确定性、版本溯源、泄露审计、资格和伦理证明完整之后才能作正式科学声明。
8. **Paper 1 实验**：系统对比须先完成独立 Gold 和实验冻结；不要用 synthetic QA 成绩替代临床/科学结果。

## 分清工作台状态

| 工程或科学对象 | 可以证明 | 不可直接证明 |
|---|---|---|
| ParseRun 完成 | 输入转为候选结构化文档 | 原论文所有表图/文本均正确 |
| 源文本 SHA / 精确 Anchor | 可回放到固定来源片段 | 结论科学有效、证据适用于特定人群 |
| Curator QA ACCEPT | 此 Unit 的核对程序按约完成 | 独立科学 Gold 或真实来源许可 |
| Synthetic SourcePackage freeze | 合成系统流程和不可变数据可运作 | 正式来源入库、专家可读或部署 |
| Expert Judgment freeze | 个体判断在规定时序内被锁定 | 独立 Reference 已科学合格 |
| Qualified Reference / Gold | 经所属科学规范和独立审核才可声明 | 不代表方案临床有效性已在前瞻性研究验证 |

## 阅读具体合同

- 科学问题与 D1：[D1 Rebaseline](NDF-D1-A0R_Latest-Paper-Plan-Conformance-Rebaseline_v0.1.md) · [首次薄片](NDF-D1-A3R_First-ScientificReferenceState_v0.1.md)。
- D2 案例：[D2 Case Readiness](NDF-D2_First-Case-Readiness-and-Observation-Completion_v0.1.md)。
- 专家任务：[Current Baseline / NDS-R1](CURRENT_BASELINE.md#nds-r1-专家任务与严格盲法)。
- Workbench：[System Master](workbench/Workbench_System_Master_v0.2.md) · [具体工程文档](workbench/README.md)。
- 交付/发布：[Issue #42](https://github.com/gitzhangcd/NutriFoundation/issues/42) 和 [治理冲突登记](governance/Workbench_Normative_Conflict_Register_v0.1.md)。

**NHANES 使用提醒**：NHANES 典型周期的横断面观测不能凭案例重构自动宣称是同一人的临床纵向轨迹；需要清楚区分真实观察、合成案例与任务构造。
