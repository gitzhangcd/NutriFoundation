# G1-Shared P0.1-A.1｜专家独立 L4 审核手册（真人填写版）

**状态：等待专家指派；已生成10份空白 A/B 任务；当前没有任何已签名专家结论。**

## 一、专家应看到的资料

使用 `P0_1_A_1_Blind_Expert_L4_Independent_Review_Packets_v0.1.json` 各自领取且只显示来源页面、问题、空白字段和必要的原始证据。专家 **不应先看到** Agent 预抽取、研究团队的 source-native anomaly / 数值怀疑、预评分结果、其他专家答案或基于这批来源调试过的判定。

原文为判定权威层，中文对照翻译仅辅助阅读。禁止凭译文直接确认数值及临床规范强度；必须可回指原文、表格及版本。

五份原始来源：
- RCT: https://pmc.ncbi.nlm.nih.gov/articles/PMC8864028/
- Cohort: https://pmc.ncbi.nlm.nih.gov/articles/PMC6538975/
- Network meta: https://pmc.ncbi.nlm.nih.gov/articles/PMC12175170/
- EBPG journal: https://pmc.ncbi.nlm.nih.gov/articles/PMC12646719/ ; EAL official: https://www.andeal.org/template.cfm?key=4888&template=guide_summary
- Expert consensus: https://pmc.ncbi.nlm.nih.gov/articles/PMC11170495/

## 二、专家一屏填写建议

1. 选择当前文献类型及当前科学问题（各类型题干已在 JSON 中）。
2. 完全独立阅读原始材料，不预览 Agent 层。
3. 标记原文 **SourceSpan**（段落位置、表格行列、图号/附件、版本及原件访问时间）。
4. 完成五项类型专属字段，保留不确定性和缺失材料。
5. 对当前科学问题选择 `QUALIFY / CONDITIONAL / DEFER / REJECT`。这不是“论文质量打分”，而是**是否可用于当前 EvidenceQuestion**。
6. 说明原始文件完整性，并明确是否已亲自核对原件、附件、表格及更正。
7. 签名并冻结 `Expert A` 原始答卷；`Expert B` 必须独立完成。
8. 仅当两人都冻结后，研究团队解锁裁决队列；重大不一致交领域 adjudicator。研究团队负责编码到 SIS / NDF / AI Nutri 结构，医生/营养专家不填写复杂 SIS schema。

### 每个问题必须输出

```yaml
source_id: CAND-G100-___
expert_role: A # or B
reviewer_id: ""          # a real verified expert
source_version: ""
source_access_date: ""
scientific_question: ""
candidate_scientific_decision: QUALIFY | CONDITIONAL | DEFER | REJECT
pico_t_and_normativity: ""
original_support_spans:
  - source_uri: ""
    document_sha256: ""  # if an actual original source snapshot exists
    locator_kind: paragraph | pdf_page | table_cell | figure | supplement | recommendation
    locator: ""
    quoted_original_short: ""
limitations: ""
unresolved_source_fidelity: []
study_family_or_version_dependency: []
expert_signed_at: ""
immutable_envelope_hash: ""
```

**缺少可复核原文的数值或推荐不能默许：应选择 DEFER 或限定条件。**

## 三、双专家与最终裁决门禁

- A、B 所见资料必须在版本上等价，且看不到模型推荐值、质控风险队列或另一位专家答案。
- A、B 签署时间和授权审核身份必须由系统真实记录；不能由 Agent 代填。
- 裁决记录需保留两份原答案和对每项关键冲突的具体证据，不能只有合并答案。
- 原始文件缺失时 `SourceArtifact` 可以进入 `HOLD_SOURCE_FIDELITY`，并不阻止专家就有限段落给出 **CONDITIONAL** 判断，但不能自动获得 `FullDocumentScientificQualification`。
- 特定疾病或高风险推荐，优先由具资质临床人员确认医疗规范适用；一般营养证据由合格营养研究专家确认。研究团队维护 schema，Agent 做低风险抽取和差错提示。
- 正式 Paper C Gold100 独立性不可从本批 exposed pilot 推断。

## 四、Workbench 接入要求

`54b4c2e` 的 reader.js 硬编码 `SYN-5-2-PAPER`；所以这里交付的是研究任务 JSON 与操作手册，并非已部署且授权的多来源专家系统。接入时需要：
- Task-scoped Source Registry，文献类型路由和原文版本/hash；
- Bilingual original/translation paragraph alignment with translation as auxiliary only；
- PDF figure/table cell anchor parity, supplement linkage；
- pre-AI immutable freeze，Agent overlay only in permitted later arms；
- two independent review envelopes, adjudicator release gate, export provenance；
- stop-on-missing-source / stale-version / authorization failures.

**当前验收：Review Protocol READY；Real Expert Assignment NOT STARTED；Adjudicated L4 = 0/5。**
