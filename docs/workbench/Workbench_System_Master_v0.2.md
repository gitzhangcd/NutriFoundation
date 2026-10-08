# Workbench System Master Specification v0.2

## WB-P0.2-M0｜End-to-End System Architecture, Scientific Workflow Alignment, Page IA & UX Contract, Engineering Master Freeze

> **规范状态：DESIGN_FROZEN / IMPLEMENTATION_GATES_OPEN**  
> **日期：2026-10-08**  
> **科学基线：** `ndf-d1-scientific-core-thin-slice@2259fdac9502541909a70d5d79c3460cecb6f657`  
> **工程输入：** `workbench-wb-p0.2-real-paper-roundtrip@34386dd9d0b82ba0ad319fa0d46ed0eb9d8c9a00`  
> **规范归属：** Workbench 工程系统；科学真值/Gold 仍归 NDF/NDS 与真实专家审核。  
> **阶段区分：** `WB-P0.2-M0 != NDS-R1-P0.2`。

本文件是可以独立传播的产品、科学适配与工程总规范。四份 companion contracts 细化页面、Adapter、状态/API 和验收。任何附件与本 Master 或上游科学契约冲突，必须暂停实施并形成 normative delta，不允许“按 UI 方便”进行隐式语义替换。

## 0｜系统定义与总体架构

Workbench 是一个 **evidence-grounded、version-bound、exposure-controlled** 的科研证据和专家判断工作台。它不是普通 PDF 阅读器，也不是单纯表单，更不具有自动科学 Gold 授权权。

```text
PDF / DOCX / Markdown / MinerU / GROBID / LLM conversion（独立前处理）
       ↓ 明确 parser provenance 与人工修订历史
AnnotationSourcePackage / SourceArtifact
       ↓ Workbench Importer / SHA / ZIP / schema / permission checks
CanonicalDocument + ParseRun + DocumentUnit
       ↓
Structured Reader ↔ Original PDF / FIGURE / TABLE
       ↕
SourceAnchor / PDF_PAGE_BBOX / version-bound replay
       ↓
┌──────────────────── Unified Workbench Application ─────────────────────┐
│ Task Queue / Qualification / Assignment / Source Library               │
│ Evidence Workspace        | Expert Decision Workspace                  │
│ Expert Draft / Source Bind | Freeze / R1 Verification / R2 Reconciliation│
│ Review / Adjudication     | Audit / Export                              │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↓
Server-side Scientific Workflow Controller (arm × phase × source projection)
       ↓
Immutable Judgment / Exposure Audit / Source Lineage / Versioned Export
       ↓
NDF / NDS independent scientific verification and QualifiedReference authority
```

**三个级别不得混同：** `PARSER_VALID`（格式可导入）、`SOURCE_LOCATOR_VERIFIED`（引文能够回放到确定版本的原文）、`SCIENTIFICALLY_QUALIFIED`（由相应科研规范核查科学含义）。前两个结果不得升级为第三个。

## 1｜权威顺序和非回归

1. SIS v0.3.1 R5、Nutrition Foundation v0.1、当前 NDF-D0/D1/D2、NDS-R1 是上游科学权威。
2. `runs/NDS/R1/P0/Role_Input_Surface_Contract_v0.1.json`、`runs/NDS/R1/P0.1/Exposure_Lock_Registry_v0.1.json`、`Judgment_Freeze_Contract_v0.1.json`、资格与 slot、当前 source packet/workpacks 是实验协议权威。
3. `WB-P0.2-P0` 科学基线、代码与文件保护边界。
4. 本 Master + 同版本 companion specs 属于 **工程设计权威**；不能推翻 1–3。
5. UI、服务端程序、自动化测试不得反向定义科学真值。

当前有效研究路线是 `SIS R5 → Nutrition Foundation → NDF-D0 → (NDF-D1 || NDF-D2) → NDS-R1`；遗留 E0.4.x/Paper C 不可作为当前 NDS-R1 专家表单唯一依据。试点案例 `D2-NHANES-L-0001:r3`，科学参考状态 `SRS-D1-A3R-001:r4`。**本阶段不是 NDS-R1-P0.2**，不能以设计冻结声称真实专家已经提交数据。

**明确的 version-binding issue：** `Judgment_Freeze_Contract_v0.1` 中 R0/R2 的 `source_workpack` 指向 v0.1，而实际 operational workpack 是 v0.2（明确 supersede v0.1）。Workbench 复用旧 freeze semantics、绑定当前 v0.2 payload，建立显式版本化 `ScientificContractAdapter`；如果字段语义冲突必须 `BLOCK_CONTRACT_CONFLICT`，**不改写 frozen upstream**。

## 2｜两类任务配置；一种工作台底座

### 2.1 Evidence Annotation Profile（文献/指南证据标注）

适用研究设计、方法、样本、人群、暴露、效应/结局、表图、限制、source span、证据支持状态的专业核查。**输出为 evidence annotation / review candidate**，不自动成为 `EvidenceUnit_F0`、`ScientificClaim_GOLD` 或 `QualifiedDecisionReference`。论文证据问题可以分为 Evidence、Applicability、Study State、Decision Boundary、Safety 等维度；这些标题是特定任务的 presentation schema，不是所有任务的全球强制问题集。

### 2.2 Expert Decision Capture Profile（案例/专业决策采集）

遵守当前 R0/R2 workpack v0.2：`decision_focus`、`salient_existing_facts`、`decision_changing_missing_information`、`currently_acceptable_actions`、`conditional_actions`、`not_indicated_prohibited_or_unsafe`、`process_action`、`monitoring_needs`、`reference_set` 七类（preferred/acceptable/conditional/not_currently_indicated/prohibited/unsafe/unresolved）、`uncertainty_notes`、`rationale_notes`、`active_expert_minutes`、`clarification_count`。不能强迫专家给出唯一最优方案；必须保留安全未知、未解决问题、替代行动及条件。

**配置约束：** 每项任务必须显式绑定 `task_profile_id/profile_version/case_ref/input_surface_id/source_manifest_sha/arm`。自然问句、分组、页面导航只属于 `ViewModel`；必须可逆映射到科学字段，不允许 UI 修改科学字段语义、因页面简化遗漏有效 reference-set 选项。

## 3｜角色与权限

| 系统角色 | 可负责 | 严格边界 |
|---|---|---|
| Expert | 阅读、创建锚点、填写合法 workpack、提交 | 只看授权的 case/arm/phase/projection |
| Reviewer | 正式授权后复核、批注差异 | 不可覆盖独立判断、不可提前跨臂查看 |
| Adjudicator | 已授权分歧仲裁 | 仲裁结果另存；不可篡改 frozen judgment |
| Manager | 项目、任务、资格审核、来源库 | 管理员不能越过科学输入隔离 |
| Auditor | 查 source/hash/audit/exposure | 只读且按最小必要原则访问 |
| Machine Producer | 输出隔离候选 | 不能直接改变专家判断或 Gold |

**R0/R1/R2 是科学实验 arm，不是任意赋予角色的 RBAC。** 同一真实专家不得在同一 case 跨 arm 重复绑定；必须先做 qualification / prior exposure screen。项目权限、身份、实验臂、阶段、来源集合及版本完整性共同决定是否放行。

## 4｜三条不可合并的科学流程

### R0｜Human De Novo

```text
QUALIFY → BIND(R0) → EXPOSURE_SCREEN_PASS → OPEN_HUMAN_PACKET
→ DRAFT(J_human_de_novo) → SUBMIT → FREEZE → READ_ONLY/HANDOFF
```

R0 **永久不可暴露 Agent**。只允许当前 case-visible observations + `Human_Baseline_Source_Packet_v0.2` 允许的材料。不得在菜单、缓存、下载、前端状态、后端 JSON 中提供 Candidate；不能展示“锁定后查看 AI”的误导提示。

### R1｜AgentFirst Expert Verification

```text
QUALIFY → BIND(R1) → FROZEN_AGENT_CANDIDATE_SET + CANDIDATE_SOURCE_SPANS
→ OPEN_VERIFY → ITEM_DISPOSITIONS → FREEZE_VERIFIED_OUTPUT
```

R1 按规范 **无独立 pre-AI 判断阶段**，不可套用 R2 的 Pre-AI Lock。必须先存在冻结 AgentCandidateSet 和候选绑定原文；专家才可选择 `ACCEPT/REJECT/MODIFY/IRRELEVANT/UNCERTAIN/NEEDS_MORE_EVIDENCE`。其他 arm、最终参考、meta-audit 信息始终不能提前露出。

### R2｜FocusFirst + Agent Expansion

```text
QUALIFY → BIND(R2) → EXPOSURE_SCREEN_PASS → OPEN_HUMAN_PACKET
→ DRAFT(J_preAI) → SUBMIT + ATOMIC_FREEZE(J_preAI)
→ UNLOCK_AGENT_EXPANSION → GENERATE/FREEZE_AGENT_SET
→ AUDITED_EXPOSURE → RECONCILE → FREEZE(J_postAI)
```

R2 只有真实专家合法提交且 receipt 满足 `expert_slot/submitted_at/content_sha/exposure_check=PASS` 才能解锁 Agent 扩展；后续 `J_postAI` 新增而不能覆盖 `J_preAI`。**候选由后台生成不等于被允许向专家展示。** 未授权的存在性计数、自动摘要、差异预览也属于信息泄漏。早期暴露不能靠“删除浏览器历史”恢复科研独立性，必须写 protocol deviation 并禁止当成 clean independent baseline。

## 5｜端到端业务与数据链

```text
Project/Profile registration → Upload/Source conversion → Package qualification
→ Canonical document & hash/revision → Task binding + source allowlist
→ Expert qualification → Role/arm projection → Reading & anchors
→ Draft/autosave → Arm-specific freeze/exposure/reconciliation
→ Authorization-bound review/adjudication → Audit/export
→ External scientific qualification/decision
```

**Import ≠ Authorized to read**：来源库管理员能上传某 PDF，不代表这篇 PDF 自动获准显示给 NDS-R1 的 R0/R2 专家。实际任务可见材料必须等于批准的 input projection，当前 R0/R2 pre-AI 人工材料以 `Human_Baseline_Source_Packet_v0.2` 为权威。之前 5:2 diet PDF 是工程真实论文 fixture，不属于这一 NDS-R1 案例允许信息集合，不能混入 blinded task。

## 6｜资料前处理边界

用户先用独立工具处理 PDF/OCR/图表，再把可读 Markdown/HTML 与原件导入 Workbench。MinerU、GROBID 和 LLM 转换器都只是上游可换的实现；不要求把所有转换控件塞进专家主页面。

建议兼容当前已验收的 `AnnotationSourcePackage/0.1`：

```text
AnnotationSourcePackage/
├── conversion_manifest.json
├── source/original.pdf
├── document.md
└── assets/*.{png,jpg,jpeg,webp}
```

导入检查 ZIP path traversal、成员大小、哈希、页数、资料完整性、Markdown 表图引用、parser provenance。来源包缺失 PDF 原件时不可宣称原件精准追溯；扫描页无文字层，必须显示“待 OCR/人工核验”，不能用页码提示伪造精确 BBox。再次转换或人工编辑都产生新 version，而非静默覆盖已有原件。

## 7｜文档、锚点与判断的对象边界

| 对象 | 工程负责 | 不代表 |
|---|---|---|
| SourceArtifact | 原件、版本、SHA、存储与权限 | 科学证据已合格 |
| AnnotationSourcePackage | 格式化来源包与 manifest | 原论文内容已验证 |
| ParseRun | 解析工具、运行与告警 | 独立 scientific verification |
| CanonicalDocument / DocumentUnit | 章节、段落、表、图、段落 offset | ScientificClaim |
| SourceAnchor | UTF-16 offset、原文引文、source/version 指针 | EvidenceUnit Gold |
| PDF_PAGE_BBOX/0.2 | 原件 PDF text-layer 唯一匹配、旋转/裁剪坐标、多个 rectangles | 语义等价或因果支持 |
| AnnotationTask | profile/case/arm/projection 绑定 | 专家已经合格 |
| ExpertDraft | 可编辑草稿、版本化 | 已冻结专家判断 |
| LockSnapshot/FreezeReceipt | 只读快照、内容 hash、提交/身份/来源版本 | QualifiedDecisionReference |
| CandidateSet/Reconciliation | AI 候选与经允许的差异处理 | 未经审核的 scientific truth |
| AuditEvent | 操作、曝光、来源与版本历史 | 替代医生意见 |

**锚点能力分级：** `EXACT_PDF_BBOX_VERIFIED`、`TEXT_QUOTE_VERIFIED_NO_BBOX`、`PAGE_HINT_ONLY`、`UNRESOLVED_AMBIGUOUS`、`STALE_REVISION`。只能在第一类展示“精确 PDF 高亮”。PDF B1 已在 0/90/180/270、非零 CropBox、双栏、重复引文、跨表格伪拼接、无文字层扫描 PDF 中通过工程测试或正确拒绝。不能推论已支持所有异形 PDF、复杂 OCR 或科学真值。

## 8｜一屏完成、分阶段展开

**统一 App Shell**：左侧项目/任务/材料导航，顶栏输入身份、case、arm、task phase 与保存状态。任务主屏分为结构化证据阅读区（建议 40%）、自然语言判断区（40%）、证据和进度区（20%）；面板可调，原件 PDF 在证据阅读区切换或并排显示，不能要求专家跳到另一个系统复制引用。

**Expert Decision Capture 推荐五个可展开阶段（仅 ViewModel，不改变科学 schema）：**
1. 可见事实与决策焦点；
2. 决策改变型缺失信息；
3. 现阶段可接受/条件性/不适用/不安全行动与 reference_set；
4. 监测、过程动作、理由与不确定性；
5. 复查、资格与暴露声明、按 arm 提交/冻结。

Evidence Annotation 使用**自己的**证据评价阶段模板，而不能把上面五项当作文献评估的唯一问题。R1 验证中心以冻结候选逐条 disposition 为主，不呈现 R2 独立判断页。支持 unknown/abstain、多个证据锚点、条件、备选方案、草稿恢复和字段验证。锁前的潜在 Agent 摘要、提示卡和统计均不显示。

## 9｜逻辑信息架构

1. Projects / Dashboard / My Tasks；
2. Qualification & Task Preflight；
3. Source Library / Import & Validation；
4. Structured Reader & PDF Inspector；
5. Expert Workspace（核心任务主屏）；
6. Submission & Freeze Confirmation（适用 R0/R2）；
7. R1 Agent-first Verification；
8. R2 Candidate Comparison & Reconciliation；
9. Review & Adjudication；
10. Audit, Versions & Exports；
11. Project Settings / Profile Configuration。

以上为逻辑页面，不必每一个都有独立网址。Reader 和 Judgment 应保留在同一任务 workspace 中，其路由和导航行为见 `Workbench_Page_IA_and_UX_Contract_v0.2.md`。

## 10｜后端与部署架构决策

**模块化单体优先**，不在 MVP 阶段引入不必要的微服务。建议 React + TypeScript + Vite 作为统一 Web Shell；复用已验收 PDF.js 固定版本 `pdfjs-dist@4.10.38`（升级另设回归）；FastAPI + Pydantic v2 对接现有 reader/anchor Python；首期开发 SQLite，团队协作前迁 PostgreSQL；原始文档与 assets 使用隔离文件/对象存储。搜索可先使用已规范化 DocumentUnit，不要求先部署 OpenSearch。MinerU/OCR/LLM 由异步 upstream adapter 接入，转换服务的成功不改变科研验证状态。

模块边界：`Ingestion, Canonical, Reader, Anchor, Project, ExpertIdentity, ScientificContractAdapter, RoleProjection, Task, Draft, Freeze, CandidateVault, Reconciliation, Review, Audit, Export`。**服务端实现全部身份、输入投影、冻结、候选开放与审计授权；客户端隐藏按钮不是安全保障。**

未来代码组织：

```text
apps/workbench/
├── wb-p0.2-a/       # existing verified historical slice
├── wb-p0.2-b/
├── wb-p0.2-b1/
└── app/             # new integrated web + API
packages/workbench_contracts/
fixtures/workbench/
tests/workbench/
docs/workbench/
runs/workbench/
```

科学权威 `runs/NDF/**`、`runs/NDS/R1/P0/**`、`runs/NDS/R1/P0.1/**` 与 `src/nutrifoundation/**` 保持只读；新 app 封装现有 B1 reader 和 locator，实现单一持久数据与角色 projection，避免又做一套不兼容 PDF 引擎。

## 11｜授权、隐私、状态与审计

建议服务端判定：

\[
Permit(a,o,action) = RBAC(a) \land Assignment(a,o) \land ArmPhasePolicy(o) \land VersionIntegrity(o) \land SourceAllowlist(a,o)
\]

每个读取、下载、搜索、缩略图、export、audit 查询、cache key、SSR/HTML bootstrap 都必须执行同一投影策略，默认 deny。候选在隔离存储 `CandidateVault` 中，未经许可不得预加载到浏览器。R2 暴露须先核验 freeze/资格并写入 durable exposure event，之后才返回内容；使用事务与幂等键防止“已经暴露但没记录”。

冻结为原子操作：校验资格、arm、input source SHA、draft expected_revision、表单完整性、exposure assertions → canonical JSON 内容 SHA → immutable snapshot + receipt + append-only audit event。错误拒绝并记录，但不得写半成品。冻结之后更正必须创建有 reason 的新对象，不能更新原快照。

敏感医学信息默认去标识化、任务最低必要权限；原件上传要隔离验证，Markdown 必须防 XSS；实际医疗部署另做数据合规、访问授权、加密、密钥管理、备份恢复与数据保留政策。没有特定机构批准，不应把真实患者数据发给第三方 OCR/LLM 服务。

## 12｜本阶段与后续阶段

**已实际完成（工程级）**：WB-P0.2-A 导入+Canonical Reader；B PDF_PAGE_BBOX/双向回放；B1 对抗布局与 native PDF.js 回归。B1 结果：37 项 Python 测试 PASS，GitHub Actions run `37750463593` 本地与独立 Chromium/PDF.js 测试 PASS，截图工件已保存。*这不是对临床科学准确性/任意 PDF 完备性的承诺。*

**尚未实施**：正式任务资格绑定、完整 R0/R1/R2 server policy、统一 Expert UI、J_preAI 原子冻结、候选隔离、多人 review/adjudication、生产权限与部署、真实专家使用与科研 outcome 数据。

后续增量：

```text
M0 = Master design freeze (this stage; documentation only)
→ C0 = screen/component contract + field mapping + state fixtures
→ C1 = integrated Reader + Expert Draft (synthetic engineering-only)
→ C2 = qualification/assignment + R0/R1/R2 server projection + freeze/exposure
→ C3 = candidate reconciliation + reviewer/adjudication + export
→ C4 = formal usability, security, deployment, non-regression and real experts
```

**C0 不应先于 M0；C2 的 engineering test pass 也不意味着科学 NDS-R1-P0.2 实际启动。**

## 13｜Kill tests（任何出现均阻断）

1. 将 parser/import 成功标记为 Verified Evidence/Gold；
2. R0 从任何 API、缓存、导出、页面收到 Agent candidate 或计数；
3. R1 在冻结候选和 source spans 之前开放验证；
4. R2 在合法 J_preAI freeze 之前看见任何 Agent 信息（含摘要、数目、搜索）；
5. R2 postAI 修改 preAI 内容或 hash；
6. 同一专家在同一 case 跨臂重复使用；
7. R0/R2 pre-AI source projection 被随意加入未获批准的 PDF 或科学结论；
8. stale/ambiguous/unmatched quote 被渲染为 exact BBox；
9. 模拟数据被当作真实专家或 QualifiedReference；
10. Workbench PR 修改冻结 NDF/NDS 文件；
11. 权限控制仅依赖前端 visibility；
12. 暴露审计无法还原当时的 source/candidate 版本。

## 14｜M0 冻结内容与待决项

**本次冻结**：双任务 profile、三科学 arm、合法来源投影、不可变独立判断、read-only scientific lineage、精确锚点校验、信息架构、统一交互原则、模块边界、服务端门禁与非回归项目。

**后续 ADR 决定（不是当前实现）**：真实身份提供方、SQLite→PostgreSQL 迁移策略、生产部署云/本地、数据保护协议、具体设计 tokens 与无障碍测量阈值、PDF.js 升级策略、所有 JSON Schema 的机器可执行格式。若上游 scientific contract 改版，先审查语义冲突再创建新的 adapter 版本；绝不隐式替换历史 snapshot。

推荐决议状态：`PASS_DESIGN_BASELINE_FROZEN / RUNTIME_AND_SCIENTIFIC_GATES_PENDING`。它仅说明设计及跨文件 contract 已核对，不说明 Expert Workspace、正式资格审查或真实专家实验已运行。

## 15｜必读附件及规范链接

- `Workbench_Page_IA_and_UX_Contract_v0.2.md`：各页面、布局与不同 arm 可见性、交互状态。
- `Workbench_Scientific_Adapter_Matrix_v0.2.md`：冻结 R0/R1/R2 source/workpack 的字段级映射与兼容裁决。
- `Workbench_Data_API_State_Contract_v0.2.md`：对象、状态机、API、事务、审计错误语义。
- `Workbench_Acceptance_and_Roadmap_v0.2.md`：测试矩阵、kill tests、C0–C4 gates 与验收模板。
- `runs/workbench/WB-P0.2/M0/WB-M0_Conformance_Manifest_v0.2.json`：机器可读依据/承诺/保护路径/门禁状态。

所有附属文件必须注明设计提案与已实施代码的边界。科学研究所需的真正专家身份、专业独立性、原始临床数据和 reference qualification 不得由 Workbench 单方推定。
