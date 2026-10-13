# GOV-0.2｜Scientific Authority Version Adjudication v0.1

> Date: 2026-10-13  
> Project: NutriFoundation Workbench, downstream of SIS / SIS-MED / Nutrition Foundation  
> **Decision type: TECHNICAL EVIDENCE ADJUDICATION; NOT SCIENTIFIC OWNER'S APPROVAL**  
> Parent: GOV-0.1 Draft PR #43, built on PR #41 exact code head `e7955ef62967c2b1e1de391be90c190138b2fb1f`  
> Machine register: [GOV-0.2_Scientific_Authority_Version_Decision_v0.1.json](GOV-0.2_Scientific_Authority_Version_Decision_v0.1.json)  
> Original upstream SIS/NDF/NDS/Gold, source authorization and infrastructure files remain **unchanged**.

## 0. Overall disposition

```text
GOV-0.2_EVIDENCE_DISCOVERY_AND_BYTE_AUDIT: COMPLETED
NUTRITION_FOUNDATION_V0.1_INTEGRATED_MASTER: EXACT_BYTES_VERIFIED
NUTRITION_FOUNDATION_NF_P0..P4: 5/5 SHA256 MATCH INTEGRATED_MASTER
SIS_R5_TARGET: IDENTITY_LOCK_RECORDED / TARGET_RAW_NOT_VERIFIED
SIS_MED_R6_P0.4_TARGET: IDENTITY_LOCK_RECORDED / TARGET_RAW_NOT_VERIFIED
NDF_D1_CURRENT_SRS_R4: EXACT_BRANCH_BLOB_VERIFIED
NDF_D2_CASE_R3_TO_VIEW_R2: BLOCKED
NDS_R1_CURRENT_R0_R2_V02_TEMPLATE_SHAPE: STRUCTURAL_COMPATIBILITY_CONFIRMED
NDS_R1_SOURCE_PACKET_V01_TO_V02: MATERIAL_SOURCE_CONTENT_CHANGE
SCIENTIFIC_OWNER_RATIFICATION: PENDING
REAL_SOURCE / REAL_HUMAN / GOLD / PRODUCTION: NO_GO
```

**完成“裁决调查与证据锁定”不等于全部科学版本已经获得签署发布。** 其余条件需要持有原文件和资质的科学负责人执行。暂可按记录的版本身份开展不触及真实科研输入的合成工程，不可暗示从 R4 到 R5 的自动继承或从 r2 到 r3 的有效性。

## 1. 适用的科学权威顺序

- **SIS v0.3.1 R5**：母科学理论/系统原语、因果 estimand、能力与参考分离的通用语义。
- **SIS-MED v0.3.1 R6 P0.4**：针对**临床营养**再增加医疗决策、安全、参考和时序要求；对一般营养研究不应无根据地强制整套临床 contract。
- **Nutrition Foundation (NDSF) v0.1**：营养领域的 observation/state/information sufficiency/action/reference/trajectory 最小逻辑规范，不能推翻 SIS 或临床场景适用的 SIS-MED。
- **NDF-D0 → (NDF-D1 || NDF-D2) → NDS-R1**：分别负责科学数据/知识参考、个体 case、受盲法约束的专家参考构造；老 E0.4.x / Gold100 的 historical fixture 不会自动成为当前 NDS R1 authority。
- **Workbench System Master v0.2 + adapter、P2/UI/TPA/EA 实现**：软件工程权威，不能创造 source rights、专家资格、Gold 或新的 scientific primitives。

判定规则：`a later document title/date/PR != automatically overriding an independently frozen scientific owner`。按 claim、domain、experimental arm、source/version/exposure contract 的**适用范围**确定优先顺序。

## 2. G02-01｜SIS R5：只确认目标版本身份，原件仍需闭环

两份与 NutriFoundation 上游相关的归档文献（Nutrition Foundation Integrated Master Part VIII、AI Nutri v2.1 Appendix A）均记录：

```yaml
target: SIS v0.3.1 R5 Regenerated Master
source_filename: 05-SIS-v0.3.1-R5-Regenerated-Master-Specification.md
original_bytes_recorded: 181565
original_sha256_recorded: 3e1da79a14111d2ead7bc49d47665bc05c1879969b9233fdaa060c2f95436a82
fingerprint_basis: DOWNSTREAM_DOCUMENTARY_RECORD
source_bytes_located_with_same_digest: false
```

额外核验：
- `gitzhangcd/SIS-Main@main/specs/System_Intelligence_Science_v0.3.1.md`（Git blob `2c99d87f2c3d5458dca254b1ece3eb9bb7097ce4`）仍记录 R4-era Master；**不是经确认的 R5 原件**。
- Google Drive 中另有两份同名 `System-Intelligence-Science-v0.3.1-R5-Regenerated-Master-Specification.md`；逐一读取原始字节后均为 **149590 bytes**、`SHA-256=f7dff71e2c5973f75a7f83c77f189b6d605c5f1ea50f738506e0d115a857c44d`。它们彼此完全一致，但**不是**下游冻结指纹 181565 bytes / `3e1da...` 的文件。
- 另无已核验的 R5 owner 审查回执/ Git tag。不能将这两份较短的同名文件直接替换为后续 v2.1 已使用的目标快照。

**Decision:** 目标定义为 **181565 bytes / `3e1da...`** 所标识的版本；状态 `PIN_DESCRIPTOR_ONLY / BLOCK_R5_CANONICAL_PROMOTION`。任何影响科学原语、模型能力/Reference 或系统论断的 R5 新增内容，在获取精确字节和 owner ratification 前不能声称已被母规范有效批准。

## 3. G02-02｜SIS-MED R6：临床域的附加规范，原件未锁实

下游两份独立文档相同地记录：

```yaml
target: SIS-MED v0.3.1 R6 P0.4
source_filename: 04-SIS-MED-v0.3.1-R6-P0.4-Regenerated-Master-Spec-1-.md
original_bytes_recorded: 61116
original_sha256_recorded: f8513b600ea7a2266d56159df7f3cb1a71dd9b6b11d40721d49430da95e4b335
fingerprint_basis: DOWNSTREAM_DOCUMENTARY_RECORD
source_bytes_located_with_same_digest: false
```

- `gitzhangcd/SIS-Med@main` 仅找到 AMIE 教学资料，不能替代该文件。
- Google Drive 上找到 `SIS-Med-v0.3.1-R5-L1-Regenerated-Master-Specification.md`，**117927 bytes**，SHA-256 `d3de50276e481311cb9f86ab5e68f94b141bf294c4ce67d90efe2ffddd868955`，属于不同版本/命名，不可直接冒充 R6 P0.4。
- Nutrition Foundation v0.1 文本明确：临床营养 Profile 必须同时满足 SIS R5、SIS-MED R6 和 NDSF；这是交叉约束，不是 SIS-MED 取代通用 SIS。

**Decision:** 仅按已记录的文件名/sha 指明 R6 候选目标；`PIN_DESCRIPTOR_ONLY / REAL_CLINICAL_CONFORMANCE_BLOCKED`。真实医疗专家和病例不得因为 Workbench 的 synthetic PASS 被允许。

## 4. G02-03｜Nutrition Foundation v0.1：最强已验证结论（字节级）

已从用户受控文件库取得完整原始 Markdown，并在隔离环境中计算 SHA-256。**没有**把原文件内容复制到 public GitHub。

| 文档 | 实际字节 | SHA-256 | 与 Integrated Master 自述 |
|---|---:|---|---|
| `Nutrition_Foundation_v0.1_Integrated_Master_Specification.md` | 145696 | `81426a9423f825681a155b748643ebd9f3b6d992b67304d35e94abd9f9ca90ce` | 自身可读取、header 与 2026-10-06 edition 一致 |
| NF-P0 Scientific Identity & SIS R5 Alignment | 71965 | `d5342e70e6f524693a437c2b54535a0bae4f02d7c77da390d74e14ce060ca7c4` | **MATCH** |
| NF-P1 Exact Logical Contracts | 123940 | `6695fb0d5399022614432d5c1b22124a2ec3e2e5793b4fe302bf879a4173fc61` | **MATCH** |
| NF-P2 Reference, Safety & Qualification | 21093 | `a3068e4d6e31a87a7fc4fa884ed430e1ab681de589af6e09d0e884aecf1a8686` | **MATCH** |
| NF-P3 Trajectory, Monitoring & ReDecision | 14080 | `a03975dc15aeb1a22e9977317e63d3fd78ea5195f12f1467c776e4a8066f3ae5` | **MATCH** |
| NF-P4 Adapter, Program Routing & Conformance | 21576 | `e45ed8385000498dff4356b3039fd53b01964eaee71331880a84d5d5842cf6fd` | **MATCH** |

- Integrated Master header 为 `NDSF-MASTER-0.1`、2026-10-06，声明 `INTEGRATED LOGICAL BASELINE FROZEN / FINITE SYNTHETIC CHECKS COMPLETED / EMPIRICAL AND PRODUCTION GATES OPEN`。
- 这一结果确认 **P0–P4 阶段档案与当前 Integrated Master 的字节引用链可靠**，可恢复和核查，不等于语义/实验全体证明。
- 原 Master 在用户 private Library 中，可验证 SHA；**未发现在 NutriFoundation 公开主仓库中的 canonical immutable Git 路径**。发布权威 repo/tag/审阅记录须再补，不能给它虚构 Git blob。

**Decision:** `NDSF v0.1 LOGICAL_SOURCE_BYTES_VERIFIED`；内部合成阶段可按该完整 Master 精确版本开展适配审计；正式科学规范发布、GitHub 归档位置、真实专家/临床验证独立待审批。

## 5. G02-04｜NDF-D1/D2：明确当前声明并隔离 r2/r3 不一致

分支 `gitzhangcd/NutriFoundation@workbench-p2-1-b-source-centric-ux`：

- `runs/NDF/D1/A3R.3/ScientificReferenceState_Bundle_v0.4.json`，Git blob `90d7f59c941be3c20d26aba3e1a9be57076fba49`，标记 SRS `SRS-D1-A3R-001:r4`。A3R.3 conformance 报告状态 `PASS_D1_D2_REBIND_READY_FOR_NDS_R1`。
- `runs/NDF/D2/Case_0001/NutritionDecisionCaseBundle_v0.2.json` Git blob `6e07a3fe6c2137976da54df02b7cb540c408e032`，case revision `r3`。
- `runs/NDF/D2/Case_0001/Materialized_Projection_Views_v0.2.json` Git blob `426be595f178408cab11191a3720cf12aea7703b`，**case_ref=`D2-NHANES-L-0001:r2`**，虽声明 `SRS:r4` rebind PASS。
- `runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json` 绑定 `D2-NHANES-L-0001:r3`，却把 `case_view_ref` 指向上述仍为 r2 的文件 `#EXPERT_PRE_AI_VIEW`。
- `A3R3_Rebind_Delta_Manifest_v0.1.json` 中 `target_case_ref=r2`，需独立说明该 delta 是历史对象还是当前生效投影。

**Decision:** `SRS r4 + D2 case r3` 是本开发分支的**当前声明版本**；但 exact projection 的 r2/r3 不一致属于真实先验输入硬阻断。可能的两种正规裁决为：

A. 经 scientific owner 证实 r2 投影为有边界的历史兼容，并用 exact allowlist/投影 hashes + 未暴露字段证明其合法；或  
B. 创建**新的** r3 materialized projection / manifest + version binding / rollback，全部 Strict-Blind regression 通过；旧版 r2 frozen 不改写。

没有正式 receipt 就不能判定 A 或 B 已完成。**真实专家 R0/R2 入组继续 NO-GO**。

## 6. G02-05｜NDS-R1：模板同构，但来源包发生了实质变更

使用精确原文 JSON 对 R0/R2 v0.1 和 v0.2 做字段及叶子值比较：

| 检查项 | R0 v0.1→v0.2 | R2 v0.1→v0.2 |
|---|---|---|
| 回复主体（`response` / `J_preAI`） | **逐字段相同** | **逐字段相同** |
| `pre_open_gate` | 相同 | 相同 |
| `freeze_receipt` | 相同 | 相同 |
| `exposure_assertions_to_sign` | 不适用 | 相同 |
| 改动字段 | `version`、`status`、`human_baseline_source_packet_ref` | 同左 |
| 新增记录 | `supersedes`、`packet_rebind_reason` | 同左 |

R0 v0.2 Git blob `4cbf9830e1f6b02c0414374fd4c964141ea59974`，R2 v0.2 Git blob `3f0a06daa90562b79660d8423e5832caf20ff289`；历史 `Judgment_Freeze_Contract_v0.1.json` Git blob `adcf4f3c1a67354bf26438f53b6ab585d941f9d5`，`source_workpack` 字段仍锁 v0.1。其 freeze receipt 不可因字段同构自动改成另一个科学 artifact ID。

**重要差异：** `Human_Baseline_Source_Packet_v0.1 → v0.2` 虽仍都是 6 个 bounded 来源、同一个 case_ref，**但不是字节和科学内容相等**：
- 更新了矫正后血压指南的 Stage 1 表述；
- 增加 Stage 2 分级及 OR 条件的 source-level support；
- 强化“不得暴露系统对该 case 的特定分类结论”这一硬边界；
- 增加版本 supersession 和刷新原因。

这意味着能够作出的裁决仅是 **`WORKPACK_TEMPLATE_SHAPE_COMPATIBLE`**，不是 `SCIENTIFIC_SUBSTRATE_EQUIVALENT`。R0 与 R2 当前应使用同一个 v0.2 来源基线；R1 仍只能看到被冻结的候选及其授权 source spans，不得从 R2 的 preAI 工作包绕道。

**Decision:** 选定 `R0/R2 Workpack v0.2 + Human Baseline v0.2` 作为分支当前适配目标；`FreezeContract v0.1` 的“原子锁定、J_preAI 不可变和 receipt 语义”按原科学规范保留。新建/批准显式 adapter 兼容回执后才能作为正式执行依据；在此之前不修改原冻结引用，也不放行真实专家输入。

## 7. 本轮需继续处理的正式科学签署

| Owner / gate | 需核定的准确对象 | 允许结果 | 未决时约束 |
|---|---|---|---|
| SIS owner | R5 `181565 / 3e1da...` 原文 + 版本/提议状态 | VERIFIED_SOURCE + ADOPTED or PROPOSED claim split | 不发布 R5 完整合规声明 |
| SIS-MED owner | R6 `61116 / f851...` 原文 + Domain applicability | VERIFIED_SOURCE + signed clinical applicability | 不放行临床营养科研参考 |
| Nutrition Foundation owner | `NDSF-MASTER-0.1` 原始 hash、5 个 phase，与权威私库位置 | CANONICAL_REPO/TAG/OWNER_RATIFICATION | 可做合成适配、不可声明生产 conformance |
| NDF-D2 + NDS owner | r3 case → r2 view delta + source allowlist | SIGNED_COMPATIBILITY or NEW_R3_IMMUTABLE_PROJECTION | R0/R2 真实专家任务阻断 |
| NDS-R1 owner | `FreezeContract v0.1` + `R0/R2 v0.2` + changed source packet | Exact version adapter / negative tests / signed science interpretation | 不提升为正式 human J_preAI |

## 8. 科学非回归与源治理要求

1. 既有 `SIS-Main@main` R4 不因为数字较小而被自动覆盖；R5 target 字节一致、合法来源和签署前维持 proposal status。
2. `SIS-MED R5-L1` 不是 `SIS-MED R6 P0.4` 的可替代内容。
3. 发现 Nutrion Foundation P0–P4 的闭合 hash ≠ 允许将其完整 Markdown 自动复制到 `NutriFoundation` **public** 仓库；须单独确定可见性、许可和不可变发布渠道。
4. NDF D1 SRS status PASS 不消除 D2 view r2/r3 mismatch；Case version、view、source packet、masked fields 必须一致。
5. NDS R0 永不看到 Agent，R1 Frozen AgentFirst，R2 先 freeze J_preAI 后才允许 Agent；合成演示、私有数据和真实科研产生三种不可混淆的 evidence class。
6. GitHub `git_blob_sha`、原始 byte `sha256`、Scientific SourcePackage `source_sha` 是三种不同主张。不能混用。
7. 执行中所有科学版本与原始资料必须纳入独立 Materials Manifest；经批准才允许下游 Workbench 通过投影访问。PR 合并 / 云端部署独立验收。

## 9. 验收结果与阶段进度

- 已完成：SIS/NDSF/SIS-MED **候选身份和上下游关系**追踪；NF P0–P4 SHA256 5/5 精确一致；两份 SIS R5 Drive 同名文件与记录的冻结版本**不一致**得到实际字节证据；NDF r2/r3 重定向点、NDS v0.1/v0.2 逐字段差异与 source support 差异确认；机器裁决清单已建立。
- 未完成：两份指定 SIS R5 / SIS-MED R6 原件与相同 SHA 的 raw bytes；上游 scientific owner 审批；NF 的 immutable Git canonical publication；NDF/NDS r2/r3 数据层验证与新版本；正式适配测试/人体科研。
- 本轮只修改 `docs/governance/**`，**不改变** `runs/NDF/**`、`runs/NDS/**`、Workbench 原 EA/TPA/P2 逻辑、Gold 或部署权限。
- 里程碑总账保持 **7/25 synthetic engineering milestones**。`GOV-0.2 TECHNICAL_ADJUDICATION_COMPLETE / SCIENTIFIC_RATIFICATION_PENDING` 作为横向治理状态记录于 Issue #42。
