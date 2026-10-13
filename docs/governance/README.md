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


## GOV-0.3｜原始材料受控归档与追溯（2026-10-13）

- [GOV-0.3 原件归档、缺口恢复与权限边界报告](GOV-0.3_Original_Materials_Archive_and_Recovery_Report_v0.1.md) — 9 份实际可恢复的原件已保存到**个人私有 Library**，9/9 全量回读 SHA-256 匹配；7 类所需原件/证据仍未恢复。
- [GOV-0.3 原始材料清单（机器可读）](GOV-0.3_Controlled_Original_Materials_Manifest_v0.1.json) — 所有已归档文件的准确字节数、SHA-256、私有相对路径、角色与不可替代版本声明。
- [科学来源原件资格回执模板](GOV-0.3_Scientific_Source_Original_Qualification_Receipt_Template_v0.1.json) — 真实 PDF/JATS/HTML 存储、处理、专家阅读和传播权限独立审批；默认 NO-GO。

**私有存储位置：** `/NutriFoundation/GOV-0.3/Source-Snapshots/`（personal Library；不是 GitHub 路径）。本仓库**仅提交可审阅的元数据和空模板，不包含这些完整原始文档**。已核验 SIS R5 `149590/f7dff...` 及 SIS-MED R5-L1 `117927/d3de...` 是历史替代原件，不能冒充 GOV-0.2 的 `181565/3e1da...`、`61116/f851...` 两个目标文件。

状态：`PRIVATE_ARCHIVE_9_OF_9_BYTE_VERIFIED / MISSING_CATEGORIES_7 / SCIENTIFIC_OWNER_SIGNOFF_PENDING`。这不是 Source Rights qualification、医学专家试验或 Gold GO。


## GOV-0.4-P0｜Nutrition Foundation × 三份 Master 的静态符合性审计（2026-10-13）

- [逐条科学语义对照报告](GOV-0.4-P0_Nutrition_Foundation_Three_Master_Conformance_Report_v0.1.md) — NDSF v0.1 对 archived SIS R5、archived SIS-Med R5-L1、AI Nutri v2.1 的逻辑符合性、精确版本错配与最小 Delta。
- [15 轴结构化矩阵](GOV-0.4-P0_NDSF_Three_Master_Static_Conformance_Matrix_v0.1.json) — 各项来源章节/行号、适用域、判定性质、版本锁与 release gate。

**本阶段只完成 GOV-0.4 的 P0 文本审计，不等于 GOV-0.4 Non-Regression 全部完成。** 三项需补的版本绑定：SIS R5 exact bytes、SIS-MED R6 P0.4 exact bytes、AI Nutri v2.1 对 NDSF v0.1 的显式 downstream adapter。真实专家、Gold、临床与生产门禁不变。


### GOV-0.4-P0 权威版本修订 0.1.1｜2026-10-13

**重要裁决：SIS-MED 的当前临床营养权威只能使用 `SIS-MED v0.3.1 R6 P0.4`。** `SIS-Med R5-L1` 只能用于历史对比，不再计入当前临床科学规范符合性。R6 P0.4 的精确原始文件尚未恢复，因此临床 R6 条款级验证标记 `NOT_ASSESSED`，不得以 R5-L1 对照结果声称 R6 PASS。详情见 [修订后的审计报告](GOV-0.4-P0_Nutrition_Foundation_Three_Master_Conformance_Report_v0.1.md) 及 [15 轴矩阵](GOV-0.4-P0_NDSF_Three_Master_Static_Conformance_Matrix_v0.1.json)。
