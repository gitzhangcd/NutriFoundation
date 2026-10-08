# Workbench Scientific Contract Adapter & Exposure Matrix v0.2

> WB-P0.2-M0｜**DESIGN_FROZEN / ADAPTER_RUNTIME_NOT_IMPLEMENTED**  
> 科学基线 commit：`2259fdac9502541909a70d5d79c3460cecb6f657`。本文只定义科学协议到 Workbench 的无损映射；不是 NDS-R1 科学协议修订。

## 1. 权威文档绑定（Git blob SHA）

| Upstream path (under `gitzhangcd/NutriFoundation`) | Authority/use | Git blob SHA |
|---|---|---|
| `runs/NDS/R1/P0/Role_Input_Surface_Contract_v0.1.json` | 科学 allowlist、arm 间比较公平性 | `6ff4acdd45ba0d750ad362f41cdf1f817fc1bb47` |
| `runs/NDS/R1/P0.1/Exposure_Lock_Registry_v0.1.json` | 三条科学实验流程的门禁顺序 | `ba43d882ac85bd63c61c008ee8ddddc6f787d36c` |
| `runs/NDS/R1/P0.1/Judgment_Freeze_Contract_v0.1.json` | pre/post immutability、freeze receipt | `adcf4f3c1a67354bf26438f53b6ab585d941f9d5` |
| `runs/NDS/R1/P0.1/Expert_Slot_Binding_Registry_v0.1.json` | 实际 slot/arm 唯一绑定 | `2c4eac75204d0a6f9b3283d6561bb82837f680e2` |
| `runs/NDS/R1/P0.1/Expert_Qualification_Instance_Registry_v0.1.json` | 人类专家资格和 prior exposure 字段 | `0ddcd6f9672fb78109db4f49fa6e3e3683034e63` |
| `runs/NDS/R1/P0/Reconciliation_Exposure_Templates_v0.1.json` | 逐项处置、J_postAI 与暴露日志 | `b69d2987f88b073927f21f82ad6685496473f09a` |
| `runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json` | R0/R2 preAI 唯一当前 bounded source substrate | `a38d000f9962dac35e00d407f1d984721bc031ef` |
| `runs/NDS/R1/P0.1/R0_Human_DeNovo_Workpack_v0.2.json` | R0 当前表单 payload | `4cbf9830e1f6b02c0414374fd4c964141ea59974` |
| `runs/NDS/R1/P0.1/R2_PreAI_Workpack_v0.2.json` | R2 当前表单 payload + assertions | `3f0a06daa90562b79660d8423e5832caf20ff289` |
| `runs/NDS/R1/P0.1/R1_AgentFirst_Verification_HoldPack_v0.1.json` | R1 当前 HOLD/候选验证类别 | `02bffb41358666a02f6eb46aaa79c5ca94eaae23` |

> Git blob SHA 不是文件的 raw SHA-256；应分别记录 source/JSON bytes 的 SHA-256，不得将 Git blob ID 直接当实验内容哈希。本表的 blob SHA 用于识别 Git 权威版本。

## 2. Scientific → engineering allocation

| Scientific property | Source | Workbench engineering projection/field | Guard |
|---|---|---|---|
| `case_ref` | Workpack/role surface | `TaskAssignment.case_ref` | 完全一致、不可偷偷换 case |
| arm `R0/R1/R2` | Slot + ExposureLock | `TaskAssignment.arm` | 同人同 case 不跨臂 |
| expert identity / qualification | Qualification Registry | `ExpertQualificationRecord` | 真实验证后可 BOUND，模板不等于真人 |
| current human packet | Human Baseline v0.2 | `ApprovedInputSurface.signed_manifest` | R0/R2 preAI 仅显式 allowlist；不自动给全部库 |
| R0 response | R0 workpack v0.2 | `J_human_de_novo.payload` | 不改字段，不允许候选 |
| R2 J_preAI | R2 workpack v0.2 | `J_preAI.payload` | exposure assertions + content SHA，atomic freeze |
| R1 verification | R1 holdpack v0.1 | `CandidateDisposition[]` | 只有冻结候选 + source spans 后可创建 |
| candidate set | R1/R2 arm contract | `CandidateVault.candidate_set` | 版本冻结后、arm 允许后才投影 |
| post-AI judgment | Reconciliation templates | `J_postAI` and `ReconciliationRecord` | 新对象，禁止覆盖 J_preAI |
| exposure events | Reconciliation/Exposure templates | append-only `ExposureEvent` | 先持久记录可见性的事实，再投影 |
| scientific Gold/reference | NDF/NDS independently | **NO OWNER IN WORKBENCH** | Workbench 不能提升 Gold |

## 3. R0/R2 v0.2 workpack field mapping（不得丢失列表）

| Scientific field | Expert-native question/UX | Storage form | Lossless requirement |
|---|---|---|---|
| `decision_focus` | “这次最需要解决的专业问题是什么？” | scalar nullable | 保存原句，不自行填默认诊断 |
| `salient_existing_facts` | “哪些已知事实会影响你的判断？” | ordered list | 保留原顺序、各项 source anchors |
| `decision_changing_missing_information` | “缺什么信息可能改变决定？” | ordered list | 不转化为泛泛的越多越好清单 |
| `currently_acceptable_actions` | “现在可以做什么？” | ordered list | 多个方案并存 |
| `conditional_actions` | “哪些方案只在特定条件下可行？” | ordered list | 条件不能丢 |
| `not_indicated_prohibited_or_unsafe` | “哪些做法当前不适用/被禁止/不安全？” | ordered list | 不得自动合并为“拒绝” |
| `process_action` | “首先需采取哪些过程步骤？” | ordered list | 与治疗推荐不同 |
| `monitoring_needs` | “需要观察或随访什么？” | ordered list | 可为空且需保留原意 |
| `reference_set.preferred` | 首选方案集 | array | 不能暗设唯一值 |
| `reference_set.acceptable` | 可接受方案集 | array | 保存并行有效替代 |
| `reference_set.conditional` | 条件成立时可接受 | array | 保存限定条件 |
| `reference_set.not_currently_indicated` | 目前不适用 | array | 不等于永久禁止 |
| `reference_set.prohibited` | 禁止 | array | 保留与 unsafe 差异 |
| `reference_set.unsafe` | 存在不安全性 | array | 保留风险说明 |
| `reference_set.unresolved` | 尚未解决 | array | 不强行定论 |
| `uncertainty_notes` | 不确定性与未知 | ordered list | 不当作“不完整”的统一报错 |
| `rationale_notes` | 专家原始理由 | ordered list | 不被 Agent 生成内容覆盖 |
| `active_expert_minutes` | 用于报告的有效专家工时 | nullable number | 需记录采集口径与出处 |
| `clarification_count` | 需要专家澄清次数 | integer | 不等于点击按钮次数 |

**适配规则：** 页面阶段/标签只是显示映射；保存原始字段类型和列表位置；扩展性证据引用存 sidecar — `FieldAnchorBinding`，不改变 frozen workpack 的科学字段。如果发生输入字段、enum、null/unknown 语义不一致，拒绝提交并发起 Adapter 升级审核。

## 4. R0/R1/R2 input surfaces and state gates

| Arm/phase | Source exposure | Agent exposure | Valid output | Invalid operation |
|---|---|---|---|---|
| R0 before/after freeze | `HUMAN_BASELINE_SOURCE_PACKET` | NEVER | `J_human_de_novo` snapshot | AI candidate/read/search/export |
| R1 qualification/pre candidate | qualification-only bounded info | NO | HOLD | agent verification page open |
| R1 expert verify | `CASE_VIEW` + **frozen** Agent Set + referenced source spans | YES (after freeze) | Expert verification disposition | missing candidate source refs |
| R2 expert preAI | same bounded human substrate as R0 | NO | `J_preAI` | Agent output, SRS claim state labels |
| R2 Agent expansion | Agent-oriented case + SRS | agent system only | frozen candidate set | changing frozen J_preAI |
| R2 expert postAI | `FROZEN_J_PREAI` + frozen CandidateSet + referenced spans | YES after receipt | `J_postAI` + reconciliation | rewriting preAI |

Forbidden at all ex-ante exposure surfaces: hidden diet values, future evidence, other-arm outputs, other experts' judgments, final reference, workflow outcome scores, hidden meta-audit labels. **R0 and R2 preAI must be comparable in source substrate**, including source versions, source excerpt bounds and case projection, otherwise实验不再比较相同的 intervention。

## 5. Adapter binding and version delta resolution

```yaml
adapter_id: NDS_R1_WB_V0_2
scientific_base_commit: 2259fdac9502541909a70d5d79c3460cecb6f657
freeze_semantics: Judgment_Freeze_Contract_v0.1
current_payloads:
  R0: R0_Human_DeNovo_Workpack_v0.2
  R2: R2_PreAI_Workpack_v0.2
  R1: R1_AgentFirst_Verification_HoldPack_v0.1
human_source: Human_Baseline_Source_Packet_v0.2
on_schema_semantic_conflict: BLOCK_CONTRACT_CONFLICT
upstream_frozen_mutation: FORBIDDEN
```

**冲突控制**：必须对照旧 freeze semantics 和新 workpack payload 做 exact comparison，记录旧引用为何仍有效、当前字段是否发生含义变更。如升级为 v0.3，则新建 adapter + fixture + migration，不可复写既有 frozen judgment。当前已识别不一致是**路径版本引用**，不能臆断两版语义完全相同；C0 的自动化 contract audit 必须正式验证。

## 6. Empirical status and lock receipt

仓库当前 R1-P0.1 状态：`PASS_OPERATIONAL_READINESS_EMPIRICAL_CAPTURE_PENDING_REAL_EXPERTS`。当前真实专家 0/3、R0 独立判断 0、R2 J_preAI 0、Agent Candidate Sets 0、Reconciliations 0、QualifiedReference 尚未建立。

R0/R2 实际提交至少包含 `expert_slot`、真实提交时间、canonical-content SHA、`exposure_check=PASS`、source packet identity。客户端不能自己直接提交 hash 声称 frozen；必须由服务端基于最终持久化内容重新计算、原子写入 receipt。R1 的 CandidateSet 需要独立 candidate freeze receipt，不得用专家空模板代替。

任何 Workbench 设计图、模拟表单、Playwright fixture、AI 自动补全都不能改变上述状态。不同环境的 sample/fixture 必须硬标 `SYNTHETIC_ENGINEERING_ONLY`。
