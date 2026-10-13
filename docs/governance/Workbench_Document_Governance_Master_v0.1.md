# NutriFoundation Workbench｜科学规范与开发文档治理总纲 v0.1

> 编制日期：2026-10-13  
> 范围：NutriFoundation / Workbench、选定的 SIS/SIS-MED 及关联科学仓库  
> 记录性质：**DOCUMENTATION_AUDIT / PROPOSED_GOVERNANCE**，非新科学规范、非对已有规范的修订、非真实资料资格放行  
> 起点：`gitzhangcd/NutriFoundation@workbench-p2-1-b-source-centric-ux` (`e7955ef62967c2b1e1de391be90c190138b2fb1f`)  
> 持久来源：`Workbench_Document_Register_v0.1.json`（已核对的 Git 路径与 Git blob SHA）

## 0. 冻结前置原则

本治理文档是**定位、分类、证据追踪与冲突登记工具**；不能以本文件“新近”覆盖任何 frozen SIS/NDF/NDS 科学规范。不适用于授予专家、来源版权、Gold、对外服务或科研伦理许可。

规范权威以**科学对象 / 工作流 / 数据所有权**划分；不得仅靠时间戳、PR 序号或文件标题决定谁覆盖谁。

```
L0 基础科学规范：SIS / SIS-MED / Nutrition Foundation
  ↓ science ownership + normative review（不允许 UI 静默降级）
L1 项目科学执行：NDF D0/D1/D2 / NDS R1，Source / Evidence / Workpack / Freeze
  ↓ version-bound and exposure-safe adapter
L2 Workbench 工程：System Master + 4 companions + P2 / P2.1 / TPA/EA addenda
  ↓ implementation and negative tests
L3 资料与工件：Source originals / approved excerpts / structured IR / demo / fixtures
  ↔ provenance, rights, manifest, original SHA256
L4 证据与交付：PR / exact commit / CI / browser artifact / security / human UX / deploy
```

### 五个层级的放行责任

| 层级 | 主要问题 | 权威签署方 | GitHub 样例 | 特别禁止 |
|---|---|---|---|---|
| L0 | 科学概念和方法是否被定义 | 科学负责人 | `SIS-Main/specs/System_Intelligence_Science_v0.3.1.md` | 以 Workbench 页面修改 SIS 含义 |
| L1 | 哪些事实和专家动作科学上允许 | NDF/NDS scientific owner | `runs/NDF/**`, `runs/NDS/R1/**` | 自动从 parser/QA 变出 Gold |
| L2 | 页面、Reader、权限、状态机如何实现 | 工程负责人 + 上游兼容审核 | `docs/workbench/Workbench_System_Master_v0.2.md` | 以可操作性为由改变曝光锁 |
| L3 | 源文件是什么、是否可用、能否回放 | Source Curator / independent Auditor / Data Steward | SourceArtifact registry + private raw store | 将 DOI 记录等同全文原件/许可 |
| L4 | 交付是否确有证据 | QA、Security、Scientific Owner、Release Owner 分签 | PR #41 + CI + audit receipts | CI success == production / qualified expert |

## 1. 已核实的参考路径（不是全部“正式权威完成”）

### L0｜跨项目科学顶层

- `gitzhangcd/SIS-Main@main:specs/System_Intelligence_Science_v0.3.1.md`：文件存在，Git blob `2c99d87f2c3d5458dca254b1ece3eb9bb7097ce4`；本文已读到 R4 阶段历史。**用户后续讨论的 R5 Master 未在此文件内获得版本证实**，不宣称 R5 已正式归档。
- `gitzhangcd/SIS-Med@main`：仅见 AMIE companion 教学 Markdown；完整 SIS-MED R6 Master **未在该分支发现**。教学文件不能替代科学 Master。
- `Nutrition Foundation v0.1`：被 Workbench 系统 Master 引用为上游权威，但本轮无法指明其**已核验** canonical repo/path/blob。记为 `UNRESOLVED`。
- ARSO/MOSA-ARSO/NutriMAIC：各有 GitHub 仓库；除明确绑定外作为**关联研究程序/参考**，不应默认进入 Workbench 科学权威链。

### L1｜NDF / NDS 当前研究材料

- 当前 NutriFoundation 开发分支 `README.md` 明确科学路由 `SIS R5 → Nutrition Foundation → NDF D0 → NDF D1 || D2 → NDS R1`，以及历史 `E0.4.x` 不是当前 NDS-R1 方案唯一的科学依据。这是该分支**宣称的路由**，不是 R5 原文件已核验的证明。
- `runs/NDF/D1/A0R/Repository_Program_Routing_Freeze_v0.1.json`：路由冻结。
- `runs/NDF/D1/A3R.3/ScientificReferenceState_Bundle_v0.4.json`：本分支 R1-ready 科学参考状态候选权威；必须绑定原始引用和完整科学审计。
- `runs/NDF/D2/Case_0001/NutritionDecisionCaseBundle_v0.2.json`：case bundle 的 `revision=r3`。
- `runs/NDS/R1/P0/Role_Input_Surface_Contract_v0.1.json`：科学上允许输入的表面与 arm allowlist。
- `runs/NDS/R1/P0.1/Exposure_Lock_Registry_v0.1.json`、`Judgment_Freeze_Contract_v0.1.json`：科学曝光与冻结语义，不随 UI 改动。
- `runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json`、`R0_Human_DeNovo_Workpack_v0.2.json`、`R2_PreAI_Workpack_v0.2.json`：当前被科学运行回执识别的 R0/R2 可见输入。
- `R1_AgentFirst_Verification_HoldPack_v0.1.json`：R1 不含独立 preAI，候选未冻结不得开启 Expert verify。
- `P0.1_Conformance_Report_v0.1.json`：`PASS_OPERATIONAL_READINESS_EMPIRICAL_CAPTURE_PENDING_REAL_EXPERTS`。不能称已有真实专家判断或 QualifiedReference。
- 遗留 `E0.4.2` 文件、Batch001 等属于**历史冻结参考/复现输入**；另标 Scientific Legacy，不自动接管当前 NDS-R1 真值。

### L2｜Workbench 工程主规范

`Workbench_System_Master_v0.2.md` 是**已找到的工程设计 Master**，原文件自身状态 `DESIGN_FROZEN / IMPLEMENTATION_GATES_OPEN`，其四份同版附件必须成套引用：

1. `Workbench_Page_IA_and_UX_Contract_v0.2.md`：页面、阅读器、任务问答和可见性设计。
2. `Workbench_Scientific_Adapter_Matrix_v0.2.md`：R0/R1/R2、输入字段、科研科学契约映射。
3. `Workbench_Data_API_State_Contract_v0.2.md`：对象、状态机、事务、后端错误和审计。
4. `Workbench_Acceptance_and_Roadmap_v0.2.md`：负向测试、工程验收分级及发布门禁。
5. `runs/workbench/WB-P0.2/M0/WB-M0_Conformance_Manifest_v0.2.json`：版本和科学文件绑定的机器回执。

在其下方，`WB-P2_Source_Studio_HTML_Fidelity_and_Scientific_Workflow_Master_v0.3.md` 与 P2.1-A/B 等属于**功能增量和已实施记录**，不能自动重写 System Master 的整体科学约束。PR #37/#38/#40/#41 目前是堆叠的 Draft 工作分支；PR #39 属平行 UI-only 方案；勿无差别叠加。

`NutriFoundation Workbench Development Master Plan v1.1`：之前讨论过的设计来源**尚未在已核对两棵 NutriFoundation 树中找到同名原文件**。已找到的 System Master v0.2 是后续科学和工程规范，不应在无实际 diff 证据时声称与 v1.1 逐条相同。

### L3｜资料原件与派生数据边界

- `01_Scientific_World/registry/**` 和 `fixtures/Batch001_Blind_SourceText_v0.1.json`：GitHub 保存了结构化来源索引与 bounded/text fixtures，**不等于保存全部许可完整 PDF**。
- Workbench 分支的 `5_2_diet.AnnotationSourcePackage.v0.1.zip` 是工程 fixture；**不可加入 NDS-R1 R0/R2 的 hidden/strict-blind source allowlist**。
- 原始 `nutrifoundation_p2_scientific_source_portal_demo(1).html`、`Archive.zip` 与 v1.1 Master 原件未在已核查分支中确认存在。要保留原件、截图和独立 hash；不能以二次分析摘要替代。
- 对真实资料只准在具备适当访问控制和使用许可的位置保留原件。公开 GitHub 可保存**非敏感**标识符、权限裁决引用、哈希/版本/匿名 provenance；源全文/患者数据/受限授权文本/秘钥不应默认公开。
- 科研 Source Artifact / Source Package 的原始 SHA-256、DocumentUnit SHA 与 GitHub **Git blob SHA** 必须分开；本目录记录的是后者，不能充当原始字节的 SHA-256。

### L4｜验收文档

- `WB-P1.1-B4_Synthetic_Engineering_Freeze_and_Acceptance_Receipt_v0.1.md`：对**历史精确代码 SHA**证明 synthetic-engineering PASS，仍 `REAL_RESEARCH_NO_GO`。
- `WB-P0.2-C2.2_Real_Expert_Readiness_and_Security_Report_v0.1.md`：真实专家、安全、科学来源等独立闸门待解决。
- PR #41：最新 Workbench UX exact SHA `e7955ef62967c2b1e1de391be90c190138b2fb1f`，9/9 GitHub CI success；用户反馈窄屏验收已通过；仍 Draft、未合并 main。**不能由此推导生产部署已完成**。

## 2. 未裁决的科学版本冲突（必须显式标红且保留历史）

### GATE-01｜SIS R5 / SIS-MED R6 / Nutrition Foundation 的实际 Master 所在位置

Workbench Master 宣称其上游版本是 SIS R5 与 Nutrition Foundation v0.1；GitHub 本次已见 SIS v0.3.1 Master 的 R4 版本史，SIS-Med main 只有教学文件，Nutrition Foundation canonical 路径未定位。**不可无凭据标记“已完整对齐”。**

### GATE-02｜NDF-D2 版本绑定

- `NutritionDecisionCaseBundle_v0.2.json` 声明 case `revision=r3`；
- `NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json` 和 R0 v0.2 Workpack 绑定 `D2-NHANES-L-0001:r3`；
- `NDF/D2/Case_0001/Materialized_Projection_Views_v0.2.json` 仍声明 `D2-NHANES-L-0001:r2`；
- `NDF/D1/A3R.3/A3R3_Rebind_Delta_Manifest_v0.1.json` 也保留 `target_case_ref=r2`，需要解释其历史 delta 与当前 r3 的绑定关系。

要求 NDF/NDS scientific owner 签署：当前 authoritative projection 是哪个版本；如果需新建 r3 projection，则提供不污染隐藏字段的受控重放和新 SHA；如果 r2 可以视为历史兼容则提供**正式兼容裁决**。**禁止直接覆盖冻结 v0.2 文件。**

### GATE-03｜Judgment Freeze 契约与实际 Workpack 版本

`Judgment_Freeze_Contract_v0.1.json` 内的 `source_workpack` 指向 R0/R2 v0.1，但当前使用的是 v0.2。需冻结 exact adapter compatibility / field losslessness / negative fixtures，而非自动升级旧 receipt 的含义。

### GATE-04｜真实来源与部署边界

P2 合成来源登记、用途决议、QA 和 package freeze 没有真实 PDF/MinerU、版权和真实专家资格授权。真实源文件、原始 SHA、许可细分、结构化 lineage 与云端 deployed code revision 尚未获得统一完整的审核回执。

## 3. 文档生命周期、版本规则与所有权

文档必须具备以下头信息（GitHub Markdown front matter 或 sidecar manifest 均可）：

```yaml
document_id: "WB-..."
title: "..."
layer: L0|L1|L2|L3|L4
program: SIS|SIS-MED|NDF|NDS|Workbench
kind: SCIENTIFIC_MASTER|NORMATIVE_CONTRACT|ENGINEERING_SPEC|SOURCE_MATERIAL|ACCEPTANCE_RECEIPT|DESIGN_REFERENCE
authority_owner: "role, not personal name"
repo: "owner/repo"
ref: "immutable SHA/tag or reviewed branch"
path: "..."
git_blob_sha: "40 hex or explicit UNVERIFIED"
content_sha256: null # only when raw bytes independently checked
status: PROPOSED|REVIEWED|FROZEN|SUPERSEDED|HISTORICAL|BLOCKED|MISSING
supersedes: []
depends_on: []
security: PUBLIC|PRIVATE|RESTRICTED
rights_status: NOT_REVIEWED|APPROVED_FOR_PURPOSE|DENIED|UNKNOWN
evidence_refs: []
review_receipt: null
```

**补充约束**：`FROZEN` 只能由文件所属科学/工程批准方记录；`GitHub present` 仅是文件存在性。完整性验收区分路径存在、可读取、内容 hash、科学身份、访问/版权、发布/部署六项。

变更程序：
1. 新版本在独立分支提出 `Normative Delta`，列出对 SIS/NDF/NDS/Workbench 的影响范围和兼容性；
2. 由原权威 owner 和需要的独立 Auditor 核对，再更新权威版本指针；
3. 工程 Adapter 另行演示 exact-lossless mapping + negative tests；
4. 保存不可变旧版本与 supersession 关系，严禁覆盖历史冻结记录；
5. GitHub PR / exact SHA / 浏览器和科研验收分级更新 Issue #42；
6. 公网正式发布只能通过独立 Security / Science / Release 三重 GO。

## 4. 当前建议的目录方案（仅新增治理索引，不搬迁旧目录）

```
docs/
  governance/
    README.md
    Workbench_Document_Governance_Master_v0.1.md
    Workbench_Document_Register_v0.1.json
    Workbench_Normative_Conflict_Register_v0.1.md

docs/workbench/   # 原有 Workbench System Master + companions、P2 / A / B
runs/NDF/         # 科学实验和证据权威；本阶段不动
runs/NDS/         # 严格盲法、专家 workpack、冻结契约；本阶段不动
01_Scientific_World/ # 历史/基础来源元数据目录；本阶段不动
```

### 此轮工作验收条件

- `[x]` 至少 40 份已核验文档记录实际 repo/ref/path/Git blob SHA。
- `[x]` 独立列出缺失的 Master / HTML Demo / QA Archive / 真实原件。
- `[x]` R5、SIS-MED R6、r2/r3、workpack v0.1→v0.2 形成可审计的差异/待裁决记录。
- `[x]` 新增的是治理文档，冻结的 `runs/**` 和 `src/**` 维持原样。
- `[ ]` 上游 scientific owner 对缺失和兼容性问题出具正式回执（**本 PR 不伪造**）。
- `[ ]` 真实原件和版权逐一核查（**不在 public GitHub 执行**）。
- `[ ]` PR 合并和云端服务本次部署（**不在本轮声明完成**）。

## 5. 与 25 里程碑进度总账的关系

此项为 **横向治理审计**，不改变 `A 5/5 + B 2/5 + C 0/5 + D 0/5 + E 0/5 = 7/25` 的工程里程碑计数。登记的风险作为 Issue #42 并行 blocker，随来源准入/科研负责人裁决更新。

本文件建议为 `REVIEW_PENDING`，由科学/工程负责人审核后才能作为正式治理标准发布。
