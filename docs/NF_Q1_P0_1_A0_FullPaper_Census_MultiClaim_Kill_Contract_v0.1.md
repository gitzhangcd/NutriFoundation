# NF-Q1-P0.1-A0｜Full-Paper Evidence Census, Multi-Claim Extraction Contract & Omission Kill Tests

版本：v0.1｜执行日期：2026-10-17｜状态：CONTRACT AND DETERMINISTIC KILL TESTS EXECUTED; ACTUAL FULL-PAPER CENSUS HOLD｜purpose：CURATION_DEV

## 1. 科学问题

核查已经提取出来的 ScientificClaim 是否得到原文支持，不等于确认原始论文的关键结果都被提取出来。

\[
\mathrm{ExtractionAccuracy}\neq\mathrm{ExtractionCompleteness}
\]

先独立盘点全文、Methods 所声明结局、Results 报告结果、表格、图像和可取得的补充材料，再生成 EvidenceUnit / ScientificClaim。无原始材料、材料目录和独立结果分母，不得报告全文完整提取。

**本轮 A0 的实证边界：**现有 NDF-D1 A2 两篇论文的 16 个 EU、5 个 Claim、35 个 selected anchors 已复用，上游仅为这些候选提供 L1/L2。它们不是全文结果普查。本次 A0 环境未取得 A2 私有 PDF 字节，所以 FULL-PAPER CENSUS、L3、L4 和 Gold 都是 HOLD/NOT_GRANTED。

## 2. 科学对象与执行辅助台账的分离

继续遵守 SIS R5、SIS-MED R6、Nutrition Foundation v0.1、NDF D0/D1 与 NDS-R1。

核心链：
\[
SourceArtifact\rightarrow StudyIdentity\rightarrow EvidenceUnit\rightarrow ScientificClaim\rightarrow ScientificRelation/ScientificReferenceState
\]

A0 新增的仅为执行层辅助记录：
- DocumentSurfaceLedger：BODY、METHODS、RESULTS、TABLES、FIGURES、SUPPLEMENT，各自状态 NOT_ASSESSED / PARTIAL / ASSESSED / NOT_AVAILABLE；
- MethodsOutcomeDeclaration：论文方法部分或注册方案声明的主要、次要、安全、敏感性和亚组结局；
- ResultInventory：按 Study、分析人群、暴露、比较、结局、时间、模型、版本记录每个结果；
- ExtractionCoverageDelta：原始结构清单与 Agent 提取清单差异；
- OmissionAudit：独立遗漏审计和补抽队列。

未取得、未解析、未报告、没有发现必须区分，不能将未知误报为不存在。

## 3. ResultRecord 合同

逐条记录 source_id、StudyIdentity、文件及附件版本、原文段落/表格单元/图面板精确锚点、Methods 声明对应关系、result_role、分析人群、干预/暴露、比较组、结局、时间点、调整模型、各组数值、效应类型、CI/P/单位以及 reporting/extraction/verification 状态；仅原文报告的数值允许进入记录。

粒度：
\[
ResultKey=(StudyID,Outcome,Population/AnalysisSet,Comparator,Time,Model,SourceVersion)
\]

不同研究设计按有意义的字段适配。不允许统计显著性替代证据等级，不允许将观察性关联升级为干预因果效应，不允许同研究的不同发表被视作独立研究。

## 4. Result / EU / Claim 多对多关系

- 一个结果可以映射到多个有出处的证据使用对象，但不能在转换时丢失分母与分析模型。
- 一个 Claim 可以使用多个 EU，一个 EU 可以支持不同范围的 Claim；允许无 Claim 的 EU，不允许无 EU 的 Claim。
- 区分作者原文 Claim、Agent 归纳候选、支持/限定/相反 Evidence 和不允许的越界推论。
- 原始事实核验与具体 UserQuestion 能否回答属于不同审核阶段；即使事实确认也不自动授予 L3、L4、Gold。

## 5. A/B/C 三角色，专家避免锚定

A Full-Paper Extractor：先枚举文档结构和 Methods/Results、图表、附件，再生成 ResultRecord / EU / Claim 候选；
B Independent Source Verifier：基于原始 PDF 独立恢复关键数值、分母、方向、模型、表格锚点，再与 A 比对；
C Omission & Conflict Auditor：不预先阅读 A 的结果，从原始文献独立建立结果清单，寻找非显著结果、安全问题、失访、限制、冲突和遗漏。

同一模型不同提示词不保证独立真值。专家先从中性原文记录少量 J_preAI 关注点，再看 Agent 的候选和差异并记录 J_postAI/暴露，不强制专家手工填写完整 Ontology。R0/R1/R2 实验比较须另行保留独立参照。

## 6. 完整性 Gate

G0 来源身份、版本、hash、权限和附件目录；
G1 正文、Methods、Results、全部表、图、补充材料有确切盘点状态；
G2 Methods 声明的结局分别映射到结果、NOT_REPORTED 或 UNRESOLVED；
G3 每个结果保留人群、比较、时间、分析模型、数值与可回放原文锚点；
G4 B/C 基于原文执行独立重建而不沿用 A 的结论；
G5 授权专家分开判断 L3 语义范围、L4 科学问题资格；
G6 真实 Workbench 支持原文跳转、保存修改、不可变审计、重新打开及暴露记录。

无法审查的 PDF、图像、附件不得记为 ASSESSED；任何材料范围或结果分母未知时，禁止声明 100% coverage。

## 7. 错误注入 Kill Tests

KT01 丢失 HOMA 主要结局；KT02 丢失非显著血压；KT03 丢失连续变量估计；KT04 丢失残余混杂局限；
KT05 改错原文锚点数字；KT06 跨来源锚点；KT07 队列关联改因果；KT08 非肥胖成人外推糖尿病；
KT09 Agent 自授 Gold；KT10 无全量原文却宣称完成；KT11 Methods 结局未映射；KT12 Claim 无 EU；
KT13 图像缺少审计凭证却宣称已审；KT14 必要表格锚点丢失；KT15 EU 数值被改错；KT16 AI 暴露日志丢失。

本轮本地测试：6/6 基础 unittest PASS、16/16 对应 mutation 规则识别 PASS。它们是预设合成机制测试，不是实际 PDF 完整性测量，不能外推为 evidence recall、专家准确率或临床安全。

## 8. 实际状态及下一步

来源 2、EvidenceUnit candidates 16、ScientificClaim candidates 5、selected anchors 35。上游证据 cutoff 为 2026-10-07，来源再取得日期晚于 cutoff，不能伪造历史可用性。本轮 selected-span registry 机械复核通过，但 PDF 字节未在本轮重新取得，文档与结果分母为 UNKNOWN；FULL-PAPER CENSUS = HOLD，独立人审/L3/L4/Gold = NOT_GRANTED。

下一步：在授权的私有资料运行环境内重取对应版本的 PDF，枚举全页/Results/Methods/表格/图/补充资料，独立盘点并将 A/B/C 差异转交专家，最后才集成 Workbench 的事实核验闭环。

本次对话另行交付完整本地 Python 合同校验器、16 项机制错误注入和详细执行记录的 ZIP；本 GitHub PR 不冒充已执行完整全文重建。

## 9. Non-regression

不改写 SIS/SIS-MED、已有 EvidenceQuestion、A2/G1 冻结审计和 133 篇资料的准入状态。两篇不同人群、研究设计与 estimand 的试点禁止人为拼接成一项共同因果效果。
