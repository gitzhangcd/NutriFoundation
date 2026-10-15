# NutriFoundation 文档门户 · DOC-GOV v1.0

> 当前版本：**candidate / REVIEW_PENDING**；索引引用的旧文件不会因本页更新而自动升级。  
> 更新时间：2026-10-15；本页是可读导航，机器权威状态以 [Canonical Authority Registry](governance/DOC-GOV_v1.0_Canonical_Authority_Registry.json) 为准。

## 按角色阅读（最少文件路径）

| 角色 | 依次阅读 |
|---|---|
| 项目负责人 | [当前基线](CURRENT_BASELINE.md) → [科研流程](RESEARCH_WORKFLOW.md) → [Issue #42](https://github.com/gitzhangcd/NutriFoundation/issues/42) → [未闭合事项](governance/Workbench_Normative_Conflict_Register_v0.1.md) |
| 研究生/科研团队 | [研究工作流](RESEARCH_WORKFLOW.md) → [NDF D1 当前研究问题](NDF-D1-A0R_Latest-Paper-Plan-Conformance-Rebaseline_v0.1.md) → [NDF D1 科学薄片](NDF-D1-A3R_First-ScientificReferenceState_v0.1.md) → [NDS-R1 权限和工作包](CURRENT_BASELINE.md#nds-r1-专家任务与严格盲法) |
| Workbench / Cursor 开发 | [Workbench 工程入口](workbench/README.md) → [System Master](workbench/Workbench_System_Master_v0.2.md) → [Companions](workbench/README.md#当前工程基线) → 最新 PR #48 的跨分支增量 |
| 医学/营养专家 | [Workbench 角色职责](workbench/README.md#专家与审核人) → **经过授权的任务来源和最新工作包**；不要求专家直接阅读 SIS schema |
| QA / 安全 / 审稿 | [版本登记](governance/DOC-GOV_v1.0_Canonical_Authority_Registry.json) → [历史冲突](governance/Workbench_Normative_Conflict_Register_v0.1.md) → [交付边界](governance/DOC-GOV_v1.0_Documentation_Convergence_Master.md) |

## 按问题导航

- **科学定义**：[当前科学基线与原件校验](CURRENT_BASELINE.md)。SIS R5 / SIS-MED R6 / Nutrition Foundation 的完整权威原文应保留在各自科学 owner 批准的存储位置；此公共仓库只保存非敏感版本指纹和链接。
- **科学资料从哪里来、如何形成判断**：[研究数据与专家工作流](RESEARCH_WORKFLOW.md)；[NDF/D1](NDF-D1-A2R_First-Thin-Slice-Source-Acquisition-and-Qualification_v0.1.md)；[NDF/D2](NDF-D2_First-Case-Readiness-and-Observation-Completion_v0.1.md)。
- **界面、API、权限和测试**：[Workbench 工程入口](workbench/README.md)。
- **文档治理、缺失/冲突、审计和自动检查**：[治理目录](governance/README.md)；[DOC-GOV v1.0](governance/DOC-GOV_v1.0_Documentation_Convergence_Master.md)。
- **早期 E0.4、Paper C、旧 Demo**：[历史索引](archive/INDEX.md)。

## 版本事实与导航原则

1. 文件“存在”不等于获得科学 authority，PR #46 和 PR #48 的文档是**不同分支**；不要用最新版文件名覆盖源科学合同。
2. 凡引用外部分支，请使用**不可变完整提交 SHA 的文件链接**；分支昵称只作说明。
3. `runs/NDF/**` 与 `runs/NDS/**` 保持原路径，特别是严格盲法输入隔离和冻结对象。
4. 未签署的原件版权、真实专家数据、真实 Gold 和生产部署状态始终是独立门禁。
5. [文件快照清单](governance/DOC-GOV_v1.0_Cross_Branch_Inventory.json) 用于审计文件是否出现，并非全量科学证据/许可数据库。

> 每次新工作包：先核对 [Current Baseline](CURRENT_BASELINE.md) 和 [Issue #42](https://github.com/gitzhangcd/NutriFoundation/issues/42)，必要时更新 machine registry 和本索引；不要为了新功能复制整个 Master。
