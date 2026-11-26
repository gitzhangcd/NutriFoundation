---
title: "B2 / U3-B-C2-R2-P1 | Independent Semantic Reference Verification, Comparative Evaluation & Failure Attribution"
version: "0.1"
date: 2026-11-27
authority: "AI Nutri Unified Data Foundation v2.1 §§15–21"
baseline: "PR64 / d28987009665aa8f9dff0e093959ee1f3ec2d7e4"
status: "PASS_BOUNDED_P1_DEVELOPMENT_REFERENCE_COMPARISON / RETRIEVAL_COVERAGE_AND_SCIENTIFIC_QUALIFICATION_HOLD"
---

# R2-P1｜独立语义参考比较及失败归因

## 0. 裁定与执行

PI已明确授权第一批44案解盲。上一轮WebCodex离线，本轮恢复后实际执行。原R2-P0固定4方法、k=1/3/5/12、三个原目标域与单独FoodOn扩展域，保留32案不用于比较、调参或选择。本轮**开发比较通过，不通过科学映射资格及覆盖能力**。不增加科学等价、营养迁移、训练、B3或MappingRelease，不将独立AI意见当适格专家Gold。原规范、原模型候选、Critic冻结与保留队列不修改。

## 1. 冻结核验及真实原件定位

任务 B2-U3R2-REF44-GEMINI-001，原冻结收据SHA256 f085072ab0905edba3f9903b75d0554c38b53b0c5da897310703b81a28278ddf，7/7允许输入、3/3冻结成果、44/44源身份及JSON Schema、243条候选/困难负例原生ID、版本、标签和所引用原件定位核验。Gemini明确声明已暴露于C0/C2-A1/R1审计；未获确切模型build。实际访问边界为评审声明，非独立ACL证明。报告的66.0 reviewer_minutes为模型自报，冻结时间戳间隔538.159492秒；均不可当真人工作量。

**真实合同偏差：** 原P0 compare_reference.py 直接执行返回REFERENCE_TARGET_LOCATOR，43案不符合原规定的FNDDS双载体组合定位格式，仅1案原严格通过。83条FNDDS目标引用（41正向、42负例）均为正确CSV行号，但未附同周期ARS工作簿行号。逐条独立重新解析7,793 FDC条目、8,690 FNDDS码及8,690 ARS同周期工作簿行、39,707 FoodOn命名有标签类。FNDDS两个载体按原生FoodCode、同周期、唯一键和trim标签相等恢复交叉对应，83/83引用CSV hash、原行号和原标签均精确成立。控制端单独生成83条 CarrierLocatorAddenda（不修改Critic原答复，不伪称评审者曾引用ARS），限定用于此次开发比较。原格式合同不宣布通过；未来明确允许精确单载体引用并由控制端补充同周期定位，若实际ID/版本/标签/行号/证据hash不同仍阻断。原来的严验收程序保留。两个统计实现缺陷（浮点累加65.99999999999997 vs 66.0及计数器类型）本轮执行失败后修正并重跑；没有修改冻结输入。

## 2. 审核规模与分布

112条正向提议（CONDITIONAL 56, BROADER_TARGET 18, RELATED 17, CLOSE 8, EXACT 7, NARROWER_TARGET 5, UNRESOLVED 1），131困难负例（47显式冲突、42组成/物种差异、22粒度/角色差异、20目标特定条件）。36案CONDITIONAL_OR_AMBIGUOUS、7案CANDIDATE_CONCEPT_ONLY、1案NO_SUPPORTED_TARGET_IN_REVIEWED_MATERIAL；19案建议本地概念扩展。原规定supported包含RELATED和其余可支持关系但排除UNRESOLVED/applicability未解，得到111条可比较参考边。词法/词元检索及单评审者覆盖未知，不代表完全参考。实际科学参考0、专家答复0。

## 3. 当前模型19案：真实结果

19案共47条正向提议，其中46条符合预定supported定义（1未解），18案有可比较参考。43条参考边在原固定三库宇宙，3条在两个冻结目标宇宙之外，0条正向参考在1174个扩展域。按原28,845目标记录及保留的前排序候选池，43条宇宙内参考中**只有4条**（4案）进入原检索池，其余39条未检索到（FNDDS 13, FDC 14, FoodOn 12）。3条范围外都为FoodOn真实存在的原生类（japanese spanish mackerel、03250 - rice porridge (efsa foodex2)、pork liver），仅能作为本体范围复核，不直接全量纳入。4条已检索参考仍为R1 HOLD_UNRESOLVED_CONDITIONS，R2均QUESTION_ONLY，说明规则也存在待核条件；但仅重排现有候选无法挽回39条缺失参考边。

**预设主要指标**为Reference-Hit@K：在目标宇宙内有Critic可比较参考目标的18案中，至少命中一个相应目标的案例数，K是每目标域的上限，不是全局K。以下原三域计算（扩展域无参考分母，NA；合并域结果相同，但候选数增加）：

| 方法 | @1 | @3 | @5 | @12 |
|---|---:|---:|---:|---:|
| LABEL | 0/18 | 0/18 | 2/18 | 2/18 |
| CONTEXT | 0/18 | 0/18 | 0/18 | 2/18 |
| FUSION | 0/18 | 1/18 | 1/18 | 3/18 |
| TYPED_QUESTION | 0/18 | 1/18 | 1/18 | 3/18 |

排除RELATED与RELATED_ONLY的敏感性分析：16案/33个原宇宙参考边，各方法命中分子完全不变，FUSION/TYPED@12=3/16。FUSION与TYPED每个K在有参考的18案中逐案命中完全一致，不能声称条件问题排序提高语义命中。LABEL@5高于FUSION@5，不能仅凭@12宣告某方法全局最佳。原三域Top3每方法171边，FUSION和TYPED均1条正向参考重合、1条Critic困难负例重合、169条未评价；LABEL 0正/0负/171未判，CONTEXT 0正/1负/170未判。包含扩展域Top3则228边，新增57边未被Critic判定。TYPED在P0仅过滤已知规则红标，仍有1条独立Critic困难负例进入，规则不能识别全部科学风险。

4条被检索参考：马铃薯(烤)→potato (baked) CLOSE；青豆[青大豆](干)→soybean (dried) BROADER_TARGET（未入各方法Top12）；火鸡肝→turkey liver EXACT提议；小炒肝尖→Pork, fresh, variety meats and by-products, liver, cooked, braised CONDITIONAL。均保留实际语义条件待核；无营养迁移。15/19当前模型案例提出本地概念候选需求，不能外推为总体比例或断言国外库无合适目标。

本轮只是对照独立Critic建议的原生目标重合，不是完整语义真值、真正recall、precision、特异度、校准概率。目标未被Critic列出不等于错误，发现目标不等于关系正确。19案由风险富集队列选出，不代表284全部中文查询；不从该样本估计总体错误率或构造正式置信界。

## 4. 25个旧风险案例

25案均有可比较参考，65正向、75负例。旧226条候选中223条属于共同外部目标域（223个按源去重目标），3条其他域。223=28 Critic支持提议重合+27 Critic负例重合+168未被逐边判断；14案有支持重合、17案有负例重合。27条负例重合中10原U2-C RED、17 AMBER。保留19案里附带旧候选45条作为单独辅助描述（0正向重合、5负例重合，其中3 RED、2 AMBER），不把25与19合并评价本轮E5方法。旧风险负例非专家确认错误。

## 5. 研发决策及止损

主要开发瓶颈是候选生成未命中参考，而非单纯阈值过严。R2-P2建议在已暴露19案上有界改进：先用原生完整标签、别名、分类和源参考配方进行保留限定条件的双语查询重构；新增规范词法/别名/定义检索，与现有密集向量形成混合候选池；把食品身份/组成部件/加工条件分开，增加可审计候选证据；原名、上下文、混合及条件关系候选固定对照，使用相同候选预算比较。不能将Critic提供的目标ID逐项写成词典作为所谓独立泛化。只用于开发诊断；选择规则及排序冻结后才允许发出保留32案独立源优先审核，不能反复在32案上选择超参数。若仍无法有效检索相应目标，按任务收缩范围、建设本地中文概念而非继续盲目全库匹配。正式precision–coverage需专家逐边审查、独立确认参考及预先固定的误配容忍度/阈值/样本量，独立性仍需治理。EA-P0应另行完成Workbench集成、权限隔离与Phase-B逐边证据绑定；36专家任务不分派。U4可按上位规范单独设计原生键及测量资格子路径，不因未达标的跨语言映射扩展正式计算用途。

## 6. 验收、交付及复现

real_001与validation_001实际运行通过；44案、243目标引用、83定位补充、111参考归因逐项重放，127输入fence、8冻结文件未变；23/23检查，包括错误CSV行号、错误版本、错误原生标签、假ID、缺证据、越界索引及伪造科学资格均拒绝。未读取保留32参考结果；控制端仅校验其字节指纹，组合比较索引只投射第一批44。无专家科学资格。GitHub归档代码、配置、聚合报告及指纹；逐案原始标签、Critic原件及补充定位保留本地。

本地复现（需保持PI解盲授权和所有指纹、新输出目录）：
```sh
/Users/zhangcd/miniconda3/bin/python -B src/u3r2p1/run_p1.py --root . --profile configs/udf/u3r2p1/P1_ComparisonProfile_v0.1.json --profile-sha 0906d84e3ba0d0efbb5a1123c3b13a792aff82340017aaa861780d1ca0abfee3 --run runs/B2/U3-B/C2/R2/real_001 --out runs/B2/U3-B/C2/R2/P1/real_002 --pi-authorized-unblind
```
- [参考核验](../../runs/B2/U3-B/C2/R2/P1/real_001/P1ReferenceVerificationReport.json)
- [方法比较](../../runs/B2/U3-B/C2/R2/P1/real_001/P1ComparisonReport.json)
- [冻结收据](../../runs/B2/U3-B/C2/R2/P1/real_001/P1FreezeReceipt.json)
- [验收](../../runs/B2/U3-B/C2/R2/P1/validation_001/P1ValidationReport.json)
- [准入](../../runs/B2/U3-B/C2/R2/P1/P1AdmissionReceipt.json)
