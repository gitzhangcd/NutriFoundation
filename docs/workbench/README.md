# Workbench 文档入口

> Workbench 是科学证据与专家判断的**工程系统**，没有通过 UI 自动授予 Scientific Gold 的权限。  
> GOV-0.4 仅静态符合性评估；本目录的 v0.2 为原设计基线，而不是最新所有 PR 的合并结果。

## 当前工程基线

以下 **五份同版文档**应配套阅读；不要只读其中一份：

| 文档 | 最适用的问题 |
|---|---|
| [Workbench System Master v0.2](Workbench_System_Master_v0.2.md) | 系统边界、模块、科学输入与角色 |
| [Page IA and UX Contract](Workbench_Page_IA_and_UX_Contract_v0.2.md) | 导航、阅读器、专家原生判断交互 |
| [Scientific Adapter Matrix](Workbench_Scientific_Adapter_Matrix_v0.2.md) | R0/R1/R2 与 NDF/NDS 数据投影、字段映射 |
| [Data/API State Contract](Workbench_Data_API_State_Contract_v0.2.md) | 服务端模型、状态机、错误与不可变写入 |
| [Acceptance and Roadmap](Workbench_Acceptance_and_Roadmap_v0.2.md) | Kill tests、测试资格、工程阶段 |

**这是设计规范的 current reference，不是已经完成所有 C/D/E 闸门的证据。**

## P1.1 / P2 文档演进（区分权威和回执）

| 路线 | 阅读入口 | 当前限定 |
|---|---|---|
| 任务生产和专家分配 | [TPA v0.1 P0](WB-TPA-v0.1_P0_Task_Production_Assignment_Normative_Design_Freeze.md) · [P1.1-B4](WB-P1.1-B4_Integrated_Acceptance_Failure_Recovery_and_NonRegression_Freeze_Contract_v0.1.md) | 历史合成工程/运行合同，不能升为真实专家科学准入 |
| 科学资料工作台 P2 | [P2 Source Studio Master v0.3](WB-P2_Source_Studio_HTML_Fidelity_and_Scientific_Workflow_Master_v0.3.md) | 合成来源操作、权限/QA；不是 PDF/MinerU 真实生产管道 |
| P2.1 导航优化 | [A](WB-P2_P21A_Navigation_Convergence_Responsive_Fix_v0.1.md) · [B](WB-P2_P21B_Source_Centric_Workflow_UX_v0.1.md) | 历史 UX 收敛的阶段文档 |
| PR #47 / #48 最新 V2 | [PR #48](https://github.com/gitzhangcd/NutriFoundation/pull/48) · [B4 具体文档](https://github.com/gitzhangcd/NutriFoundation/blob/b3a9ca0f810ca0f5d517fc907c1800d13c24dac0/docs/workbench/WB-P2_V2.2_B4_Continuous_Scientific_Reader_Exact_Anchor_Rework_Contract_v0.1.md) | **尚未进入当前治理分支或 main**；只能作为准确 SHA 候选增量 |
| 实际工程进度 | [Issue #42](https://github.com/gitzhangcd/NutriFoundation/issues/42) | 唯一 25 里程碑 DONE_ENG 总账 |

### PR #48 各新增文档的准确不可变引用

1. [HiFi Demo v1 Alignment](https://github.com/gitzhangcd/NutriFoundation/blob/b3a9ca0f810ca0f5d517fc907c1800d13c24dac0/docs/workbench/WB-P2_HiFi_Demo_v1_4K_Package_Alignment_v0.1.md)；
2. [P2.1 C/D Source Workspace Alignment](https://github.com/gitzhangcd/NutriFoundation/blob/b3a9ca0f810ca0f5d517fc907c1800d13c24dac0/docs/workbench/WB-P2_P21CD_High_Fidelity_Demo_v1_Source_Workspace_Alignment_v0.1.md)；
3. [P2 Source Studio V2 Design](https://github.com/gitzhangcd/NutriFoundation/blob/b3a9ca0f810ca0f5d517fc907c1800d13c24dac0/docs/workbench/WB-P2_Scientific_Source_Studio_V2_Design_v0.1.md)；
4. [V2.0 P0 Engineering and Truth Gate Audit](https://github.com/gitzhangcd/NutriFoundation/blob/b3a9ca0f810ca0f5d517fc907c1800d13c24dac0/docs/workbench/WB-P2_V2.0_P0_Engineering_Data_Truth_Workflow_Gate_Audit_v0.1.md)；
5. [V2.1 P1 Synthetic Lifecycle](https://github.com/gitzhangcd/NutriFoundation/blob/b3a9ca0f810ca0f5d517fc907c1800d13c24dac0/docs/workbench/WB-P2_V2.1_P1_Role_Preserved_Synthetic_Lifecycle_Integration_v0.1.md)；
6. [V2.2 B4 Continuous Reader & Rework](https://github.com/gitzhangcd/NutriFoundation/blob/b3a9ca0f810ca0f5d517fc907c1800d13c24dac0/docs/workbench/WB-P2_V2.2_B4_Continuous_Scientific_Reader_Exact_Anchor_Rework_Contract_v0.1.md)。

这些文件未来随 PR 合并可转为本地链接，但**不得在审查前拷贝成第二个工程 Master**。

## 专家与审核人

- **Expert**：受控读取当前 Task 的证据，依据 Profile-native 工作包提交意见，不必学习 SIS schema。
- **Curator**：校验 DocumentUnit、原件与辅助译文，签署不可变 QA，不能给自身授予 Gold。
- **Auditor**：独立核查权限与原始 provenance，不能代签专家判断。
- **Producer**：可进行受控预处理、合法脱敏返工，不能越权查看 Curator 私有原文。
- **Reviewer / Adjudicator**：依照已批准的科学研究流程复核和仲裁，不能回写冻结独立判断。

## 工程规范不要改变的科学边界

R0 Never Agent；R1 Frozen AgentFirst；R2 `J_preAI` Atomically Frozen Before Agent；原文权威、翻译辅助、严格盲法；有 `D2 r2/r3` 和 `Workpack v0.1/v0.2` 冲突时 fail-closed；`Source QA != Gold`。
