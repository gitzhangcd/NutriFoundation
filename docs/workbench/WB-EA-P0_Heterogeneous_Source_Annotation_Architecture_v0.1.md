# WB-EA-P0｜Heterogeneous Scientific Source Annotation Architecture v0.1

> **文档状态：DESIGN_DELIVERED / SCIENTIFIC_OWNER_APPROVAL_PENDING / RUNTIME_NOT_IMPLEMENTED**  
> **基线：** `gitzhangcd/NutriFoundation@54b4c2eba844f39c07575573a3e834e0bc00c261`（2026-10-09）  
> **研发分支：** `workbench-ea-p0-heterogeneous-source-annotation`  
> **性质：** Workbench 下游适配设计，不是对 SIS R5、SIS-MED R6、Nutrition Foundation 或 NDF/NDS 冻结科学语义的修改。

## 0. Executive decision

现有 D0 三栏工作台可以复用为阅读/引文/专家判断的**交互组件**，但不是通用异质文献标注的现成实现：

- `apps/workbench/d0/web/reader.js` 写死 `SOURCE='SYN-5-2-PAPER'`；
- `apps/workbench/c2_1/secure_reader.py` 的 `exact_source()` 仅接受同一固定 ID；
- `apps/workbench/c1/specs/decision_profile.json` 仅定义 `NDS_R1_DECISION_CAPTURE`、19 个决策字段；
- `apps/workbench/d0/d0_app.py` 的 producer 路由提交固定的 synthetic candidate，不是文献 Agent 提取；
- 现有环境 `SYNTHETIC_ENGINEERING_ONLY`，正式专家注册、真实标注、Gold 晋级均未获许可。

**P0 决策：** 增设 `EVIDENCE_ECOSYSTEM_CASE` 任务类型，使用 `SourceRegistry + SourceTypeRouter + AnnotationProfile + CandidateSet + EvidenceReviewRecord + PromotionReceipt` 的适配层；与现有 `DECISION_CASE` 严格隔离，禁止替换 NDS-R1 19 字段模板。

## 1. 科学所有权（Authority / Ownership）

| 领域 | 现有/拟定权威对象 | Workbench 可承担 | Workbench 不得承担 |
|---|---|---|---|
| 上层理论 | SIS R5 / SIS-MED R6 | 保留专家原生判断、可追溯性与决定性不确定性 | 改写临床真值 / Gold |
| 科学知识 | AI Nutri E0–E8 + Nutrition Foundation / NDF D1 | 展示 SourceArtifact、StudyIdentity、EvidenceUnit、ScientificClaim、ScientificRelation、EvidenceSynthesis、Recommendation、ConsensusJudgment 的**带版本投影** | 将 UI 的判断文本直接提升为权威科学对象 |
| 观测与病例 | NDF D2 | 只读 authorized CaseBundle / 观察截止 | 重新分类、补全隐藏值、推断临床结论 |
| 决策参考 | NDS-R1 R0/R1/R2 | 承载原生专家输入、盲法与服务端冻结 | 改变 ExposureLock、J_preAI、QualifiedReference |
| Evidence Annotation（新增） | 由 Evidence Corpus 负责人审批版本的独立协议 | 候选、来源锚点、专家复核、分歧/裁决意见、导出 | 证明临床疗效、自动赋予 Gold 身份 |

核心规则：`SourceArtifact != EvidenceUnit != ScientificClaim != Recommendation != Decision != Gold`。`StudyIdentity` 不等于论文 DOI；单一研究可以有多个伴随出版物，Meta 纳入的原研究不得当新独立受试者证据重复计数。

## 2. 两条分离流水线

```text
A / EVIDENCE_ECOSYSTEM_CASE
Discovery → Acquisition → Type Classification → Source Snapshot & Rights
→ Structured CanonicalDocument + Original Source
→ StudyIdentity / SourceFamily Resolution
→ Type-Specific Agent Candidate Extraction [optional; provenance required]
→ Expert Evidence Review / correction / abstention
→ Independent verification + adjudication for Gold subset
→ Scientific Object Qualification → Versioned Promotion → Audit

B / DECISION_CASE [existing NDS-R1]
Qualified bounded source substrate + D2 authorized Case
→ R0 Human De Novo | R1 Frozen Agent First→Expert Verify |
  R2 Human Focus→immutable J_preAI→Agent Expand→Expert Reconcile
→ Arm-blind independent meta-audit→QualifiedDecisionReference candidate
```

A 的专家审核**不等于** B 的独立决策 Gold。A 的 Agent First 可以是一般语料生产策略，但若构造独立 Gold，须按预注册采样分离 Agent 结果、盲法人工参考与裁决。B 的 R0/R2 pre-AI 不可见 A 的任务标签、Agent candidates、复核记录或 SRS case-specific claim labels，除非它们作为事前冻结的人类允许输入显式授权并已证明无泄漏。

## 3. 类型分派矩阵：统一 Core，异质 Profile

| `source_type` | 必须保留的科学结构 | 重点失效测试 | 可提出的下游对象候选（非自动晋级） |
|---|---|---|---|
| `RANDOMIZED_TRIAL` | 干预臂、PICO、随机化、终点、效应/置信区间、ITT/缺失、时点 | 组间 vs 组内、统计不显著≠等效、数字翻转 | StudyIdentity, EvidenceUnit, ScientificClaim |
| `OBSERVATIONAL_STUDY` | 暴露、结局、时间次序、混杂调整、估计量、选择过程 | 相关性因果升级、混杂丢失 | StudyIdentity, EvidenceUnit, ScientificClaim |
| `SYSTEMATIC_REVIEW_META` | 检索/纳入、原研究 lineage、合并效应、异质性、偏倚、证据确定性 | 原研究重复计数、合并效应误读 | EvidenceSynthesis, ScientificRelation |
| `GUIDELINE` | 机构、版本、recommendation 原话、强度、适用人群、例外、EtD / 原有分级 | 虚构正式推荐、删例外、原分级被强转 | Recommendation, EtDAssessment, ScientificClaim |
| `CONSENSUS` | 专家群体、投票/Delphi/讨论过程、共识条款、分歧、证据缺口 | 以投票替代实证确定性 | DeliberationProcess, ConsensusJudgment |
| `NARRATIVE_REVIEW` | 作者主张、引用链、机制推断、被引用原始文献 | 引用洗白、机制推测提升为已证实结论 | ScientificClaim Candidate, ScientificRelation |
| `CORRECTION_RETRACTION` | 受影响 SourceArtifact/StudyIdentity、事件/公布时间、修订内容、依赖范围 | 未来撤稿泄漏、删除历史 snapshot | Provenance/Version/Dependency Impact |

类型不明则 `TYPE_UNRESOLVED / HOLD`，不得默认为 RCT。可多标签，但必须有主要处理 Profile 和明确的 companion lineage；指南附带系统综述须用 `source_family_refs` 链接，不把一种材料冒充另一种证据。

## 4. 跨来源通用对象与生命周期

```text
Raw Artifact (PDF/HTML) [rights + byte digest]
    ↕ source-faithful, reversible projection
CanonicalDocument [unit ids, source offsets, tables, media, source map]
    ↓
SourceRegistryEntry [artifact/version/retrieved/available/corrected/retracted]
    ↓
AnnotationTask [task_kind, profile, source allowlist, scientific cutoff]
    ↓
AgentCandidateSet [source spans + role/exposure audit; never Gold]
    ↓
ExpertReviewRecord [correction, status, anchor, rationale, uncertainty]
    ↓
IndependentGoldReview/Adjudication [optional qualified reference]
    ↓
Qualification + PromotionReceipt [owned by scientific data pipeline]
    ↓
Versioned NDF/AI Nutri Evidence Ecosystem objects
```

### 4.1 SourceArtifact / SourceIdentity

必须记录 `source_id`、`artifact_identity`、`revision_id`、`source_type`、`source_family_refs`、`original_bytes_sha256`、`canonical_sha256`、`retrieved_at`、`available_at`、`locator`、`rights_status`。校正与撤稿是增加历史版本和影响记录，不允许静默覆写或删除既有有效快照。

### 4.2 SourceSpan / Translation

证据授权基于 `task_id + source_id + revision + raw unit_id + offsets + quote SHA`；必须支持表格单元格与文章正文，不得用页码提示替代精确 PDF BBox。译文 sidecar 仅辅助，引用仍绑定原文 source offsets；翻译模型、版本、覆盖/质量状态可审计且须按 task allowlist 限制，禁止在 pre-AI 阶段透出未许可观点。

### 4.3 Source Type ≠ Task Type

`task_kind=EVIDENCE_ECOSYSTEM_CASE` 是科学来源审核；`task_kind=DECISION_CASE` 是个体决策参考。`source_type` 用于异质抽取和证据评价；同一指南可成为决策案例中的授权阅读材料，但**不能**因此将该决策案例改用 Guideline 专家审查表单。

## 5. 专家—Agent 流程：不混淆独立参考

- **生产流水线** `AGENT_PROPOSE → EXPERT_VERIFY`：候选必须被冻结且附上原文引用、版本和来源；专家可 `ACCEPT/MODIFY/REJECT/NEEDS_MORE_EVIDENCE/IRRELEVANT/UNCERTAIN` 并提交证据锚点；支持 `ABSTAIN`，所有修订保存原始候选。
- **Gold 流水线**：针对预注册高风险抽样设置 blind `HUMAN_INDEPENDENT`（不见 Agent 候选）、双标注、分歧裁决以及元审计；GoldAnnotationUnit 按现有上游规范治理，生产流水线的审核不能自动成为独立 Gold。
- **角色独立**：`extractor != verifier != adversarial_auditor`（逻辑隔离；相同基础模型可以用于不同独立执行实例，但输入和产出不能相互污染）。
- **多来源**：一个任务可引用 N 个来源版本，但每一个 SourceSpan 必须来自 server-issued `AllowedSourceSet`，禁止通过 source_id 猜测或跨任务 URL 获取。

## 6. 科学安全与非回归

1. 不得修改 `runs/NDF/**`、`runs/NDS/**`、`src/nutrifoundation/**`、`apps/workbench/c1/specs/decision_profile.json`、`apps/workbench/c2_1/**` 的已有冻结语义。
2. 现有 R0 永不暴露 Agent；R1 仅能看已冻结候选的批准引文；R2 在 `J_preAI` 服务器冻结前不能看到候选；服务端而不是 CSS 控制访问。
3. `D2-NHANES-L-0001:r2` 与 `:r3` 的 view binding 仍阻塞正式 NDS-R1；本 P0 不得宣称已解决。
4. 真人 IdP/MFA、资格审核、伦理、来源原件及权限、生产 OS/TLS/隐私安全未完成前，不可投入真实患者/专家科研数据。
5. 5:2 RCT 仅作为公开论文阅读工程样例，不属于签署合格的 NDS-R1 Human Baseline Packet；不得因新 Profile 自动晋级其数据。
6. 面向科研的可验证效益必须包含关键科学错误率 CSER、provenance fidelity、source-family dedup、版本忠实度、人工时间与独立 Gold 一致性；界面通过率不是科学有效性。

## 7. P0 交付清单、尚未完成的事项

P0 交付：本架构、[Exact Adapter](WB-EA-P0_Exact_Adapter_Contract_v0.1.md)、[Conformance/Execution Gate](WB-EA-P0_Conformance_and_Execution_Gate_v0.1.md)、机器可读提议性 contracts/profile/fixtures。

仍需 P1：通用权限化多来源 runtime、转换 ingestion、自动 Agent 实际抽取、类型化渲染与保存、双专家裁决、已签科研规范对象晋级、正式专家资格与安全上线。

**P0 自评：** 结构设计完成，权威负责人签署、工程运行落地及真人科学试验 **PENDING**。
