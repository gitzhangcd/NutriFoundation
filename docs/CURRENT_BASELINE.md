# Current Baseline · 2026-10-15

> **性质：版本导航，不是科学结论或重新冻结。**  
> 这份基线是“我们现在应该参考什么”和“仍缺什么证明”；机器状态见 [Canonical Authority Registry](governance/DOC-GOV_v1.0_Canonical_Authority_Registry.json)。

## 科学权威顺序

```text
SIS v0.3.1 R5                  (一般系统科学，原件 SHA 核验)
    ├── SIS-MED R6 P0.4        (临床/医疗任务附加域规范，原件 SHA 核验)
    ↓
Nutrition Foundation v0.1     (营养科学基础，原件 SHA 核验)
    ↓
NDF D0 → D1 (知识/证据) || D2 (观察/案例)
    ↓
NDS R1  (独立参考构建 + 专家原生标注)
    ↓
NDS P1–P5 / AI Nutri 研究论证及实验
    ↓
Workbench = 科学执行平台，不是临床真值所有者
```

对临床营养任务，SIS-MED R6 是额外适用约束，不可用历史 SIS-MED R5-L1 冒充。

## 上游 Master 精确身份与存储状态

| 目标原件 | 字节数 | SHA-256（全值） | 当前可确认状态 |
|---|---:|---|---|
| SIS v0.3.1 R5 | 181565 | `3e1da79a14111d2ead7bc49d47665bc05c1879969b9233fdaa060c2f95436a82` | 用户上传原件本轮字节级核验匹配；**尚未签署 canonical 私有 Git ref/tag** |
| SIS-MED R6 P0.4 | 61116 | `f8513b600ea7a2266d56159df7f3cb1a71dd9b6b11d40721d49430da95e4b335` | 用户上传原件本轮字节级核验匹配；**尚未签署 canonical 私有 Git ref/tag** |
| Nutrition Foundation v0.1 | 145696 | `81426a9423f825681a155b748643ebd9f3b6d992b67304d35e94abd9f9ca90ce` | 原件本轮核验；GOV-0.3 记录私有个人 Library 副本；科学 owner 发布签署仍缺 |

**校验口径**：SHA-256 为上传文件字节哈希；不是 Git blob SHA；当前对话可访问的附件不是持久权威文档仓库的替代。GOV-0.2、GOV-0.3 历史报告当时声明目标文件缺失，属于当时快照，不应就地篡改；本页记录 2026-10-15 新增的独立证据。

`AI Nutri v2.0` 的上传 Master 可核验；`AI Nutri v2.1` 完整规范与 NDSF 显式 adapter 尚未在现有 Git 审计树中发现**签署过的唯一完整 canonical file**。不据对话中的 v2.1 设计意图宣称已有可执行 adapter 或科学非回归完成。

## NDF/NDS 当前研究执行参考

| 事项 | 路径 / 科学状态 |
|---|---|
| D1 科学研究路由 | [Repository Program Routing](../runs/NDF/D1/A0R/Repository_Program_Routing_Freeze_v0.1.json) |
| D1 科学参考状态候选 | [SRS Bundle v0.4](../runs/NDF/D1/A3R.3/ScientificReferenceState_Bundle_v0.4.json) · R1-ready ≠ qualified Gold |
| D2 Case 当前声明 r3 | [NutritionDecisionCaseBundle v0.2](../runs/NDF/D2/Case_0001/NutritionDecisionCaseBundle_v0.2.json) |
| D2 物化视图仍指向 r2 | [Materialized Projection Views v0.2](../runs/NDF/D2/Case_0001/Materialized_Projection_Views_v0.2.json) · **冲突 OPEN** |

### NDS-R1 专家任务与严格盲法

- [Role Input Surface](../runs/NDS/R1/P0/Role_Input_Surface_Contract_v0.1.json) 与 [Exposure Lock](../runs/NDS/R1/P0.1/Exposure_Lock_Registry_v0.1.json)：专家可见输入和 arm 时序的科学约束。
- [R0 Human DeNovo Workpack v0.2](../runs/NDS/R1/P0.1/R0_Human_DeNovo_Workpack_v0.2.json)：R0 永不接触 Agent 候选。
- [R2 PreAI Workpack v0.2](../runs/NDS/R1/P0.1/R2_PreAI_Workpack_v0.2.json)：R2 必须先冻结独立 `J_preAI`。
- [Judgment Freeze Contract v0.1](../runs/NDS/R1/P0.1/Judgment_Freeze_Contract_v0.1.json)：内部仍引用 v0.1 工作包，**v0.1→v0.2 兼容性裁决 OPEN**。
- R1 AgentFirst 只可核实**已冻结且有原文锚点**的候选，不套用 R2 的 preAI 模式。
- Case r3 / projection r2 的精确不一致与 Workpack 显式兼容问题在正式专家测试前必须解除。

## Workbench 工程（≠ 科学放行）

- 当前治理分支工程设计：[System Master v0.2](workbench/Workbench_System_Master_v0.2.md) + 四份 Companions，属于 **DESIGN_FROZEN / IMPLEMENTATION_GATES_OPEN**。
- 新的 Source Studio 连续 Reader / Unicode anchor / immutable QA 返工：[PR #48 B4 文档（精确 SHA）](https://github.com/gitzhangcd/NutriFoundation/blob/b3a9ca0f810ca0f5d517fc907c1800d13c24dac0/docs/workbench/WB-P2_V2.2_B4_Continuous_Scientific_Reader_Exact_Anchor_Rework_Contract_v0.1.md)，**DRAFT / 尚未纳入 PR #46 治理分支**。
- 25 项工程里程碑的正式进度仍以 [Issue #42](https://github.com/gitzhangcd/NutriFoundation/issues/42) 为准；此文档整理增量 **0/25**。
- 真实文献来源授权、真实 PDF/MinerU 管道、临床科学一致性、独立专家 Gold、正式生产部署均须另外验收。

## 上游冲突处理链接

[历史冲突登记](governance/Workbench_Normative_Conflict_Register_v0.1.md) · [GOV-0.2 版本裁决](governance/GOV-0.2_Scientific_Authority_Adjudication_Report_v0.1.md) · [GOV-0.4 静态对照](governance/GOV-0.4-P0_Nutrition_Foundation_Three_Master_Conformance_Report_v0.1.md)。
