# NutriFoundation｜文档与规范治理索引

本目录是 **GitHub 文件现状的审计和待审批治理方案**，不是另一个能覆盖 SIS、NDF、NDS 原科学规范的“新 Master”。

| 文件 | 用途 | 当前状态 |
|---|---|---|
| [Workbench_Document_Governance_Master_v0.1.md](Workbench_Document_Governance_Master_v0.1.md) | 科学规范 / 工程规范 / 原始资料 / 验收证据五层体系；所有权和变更约束 | PROPOSED / REVIEW_PENDING |
| [Workbench_Document_Register_v0.1.json](Workbench_Document_Register_v0.1.json) | 47 项已核验 Git blob 的路径/版本/状态目录及 8 项待补充原件 | VERIFIED_PATHS / NO_SOURCE_RIGHTS_ATTESTED |
| [Workbench_Normative_Conflict_Register_v0.1.md](Workbench_Normative_Conflict_Register_v0.1.md) | SIS R5 / SIS-MED R6、NDF case r2/r3、workpack v0.1→v0.2 等问题跟踪 | OPEN |

**统一总进度：** [Workbench Execution Master Roadmap Issue #42](https://github.com/gitzhangcd/NutriFoundation/issues/42)

**工程基线：** [Workbench System Master v0.2](../workbench/Workbench_System_Master_v0.2.md) + [Page IA / UX](../workbench/Workbench_Page_IA_and_UX_Contract_v0.2.md) + [Scientific Adapter](../workbench/Workbench_Scientific_Adapter_Matrix_v0.2.md) + [Data/API](../workbench/Workbench_Data_API_State_Contract_v0.2.md) + [Acceptance](../workbench/Workbench_Acceptance_and_Roadmap_v0.2.md)。

**现阶段禁止：** 擅自修改冻结科学树；将 Git blob SHA 当成原件 SHA-256；将 synthetic QA 变成科学 Gold；把真实病历/版权受限论文/密钥放进 public GitHub；把 Draft CI 通过当成 main 合并或阿里云部署。

**更新原则：** 每个新规范和材料必须先明确科学 owner、canonical repo/ref/path、审定 status、版本绑定、存储/权限、变更影响及验收回执，再改变本索引的 current 引用。

## GOV-0.2｜科学权威版本证据裁决（2026-10-13）

- [GOV-0.2 Scientific Authority Adjudication Report](GOV-0.2_Scientific_Authority_Adjudication_Report_v0.1.md)：SIS R5 / SIS-MED R6 目标文件指纹、Nutrition Foundation v0.1 P0–P4 的实际字节校验、NDF r2/r3 和 NDS v0.1→v0.2 结构及内容差异。
- [GOV-0.2 Machine Decision Lock](GOV-0.2_Scientific_Authority_Version_Decision_v0.1.json)：6 项 authority/version pin 与明确 release gate。

本阶段 `TECHNICAL_EVIDENCE_ADJUDICATED`，**没有**替代科学负责人签署；已核验的 Nutrition Foundation Master 原文件仍在受控私有文件库中，未作为明文复制到 public GitHub。
