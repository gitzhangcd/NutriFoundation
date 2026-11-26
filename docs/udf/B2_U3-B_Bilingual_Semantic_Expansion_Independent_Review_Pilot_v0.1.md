---
title: "B2 / U3-B | Bilingual Semantic Expansion, Independent Candidate Review & Alignment Qualification Pilot"
version: "0.1"
date: 2026-11-26
authority: "AI Nutri Unified Data Foundation v2.1"
status: "PASS_BOUNDED_GENERATOR_PILOT_AND_FREEZE / INDEPENDENT_REVIEW_AND_MAPPING_QUALIFICATION_HOLD"
baseline: "PR #58, 622c8e472348ec037d82d5d05f5eacf9927f4e14"
run_id: "U3B-real_001"
---

# B2 / U3-B｜双语语义扩展、独立审核与资格化试验

## 0. 实际结论及边界

依据 [UDF v2.1](../AI_Nutri_Unified_Data_Foundation_v2.1.md) §§15–21,41、[U2-C联合加固](B1_U2-C_Scientific_Contract_Consolidation_Runtime_Enforcement_v0.1.md)（PR58）和冻结U3-A数据，执行真实本地跨语言模型检索、来源上下文扩展、重排前冲突候选保留、类型合同、全量落盘验证与独立审核包准备。本轮 generator real_001、validation_001、freeze_001 均 exit 0。**开发生成器及冻结通过；独立语义审核和映射科学资格化仍为HOLD。** Gemini原44条独立审核队列及其冻结输入未改动；指定CriticFreezeReceipt在执行前及最终核验均不存在，未读取独立Critic结果，未解盲。没有新增科学参考、正式等价或MappingRelease。

## 1. 固定基线、模型与数据设计

重新实际执行 U2-C 完整只读回放253,249对象，再经Admission.view验证29,129个词表端点。现有22,180菜肴、3,446食材全词表未转为规范唯一概念；只进行真实开发薄切片。

| 查询范围 | 数量 | 选择 |
|---|---:|---|
| NutriData食材配对 | 128 | U3-A既有135，排除原审核队列7 |
| NutriData菜肴配对 | 60 | U3-A既有64，排除原审核队列4 |
| 新食材 | 48 | 未参与U3-A查询且不在原44队列；固定salt按来源对象ID hash选择 |
| 新菜肴 | 48 | 同上 |
| 合计 | 284 | 配对188、新96；开发集非代表性独立评价 |

固定目标库为FoodOn 2026-09-20选定12,362食物产品类、FDC SR Legacy 2018-04 7,793原生食品、FNDDS 2015–16 FDC载体8,690食品码，合计28,845。ARS同周期载体不重复入检索。目标仅采用原生主标签，保留原生版本/身份/粒度，无外部概念等价推断。

实际下载并验证 [Xenova/multilingual-e5-small](https://huggingface.co/Xenova/multilingual-e5-small) ONNX量化模型固定revision 761b726dd34fb83930e26aab4e9ac3899aa1fa78（基础模型 [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small)）；实际权重118,308,185 bytes，Tokenizer 17,082,730 bytes，config 658 bytes。三个SHA256一致；本地Conda Python 3.9、ONNX Runtime 1.19.2、NumPy 2.0.2；CPU 4线程，batch128，max_tokens64，masked mean pooling与L2归一化，E5 query/passage前缀。仅下载公开模型，没有把NutriData源记录传给外部推理服务。模型和Tokenizer不上传仓库。

## 2. 真实双语与语义扩展执行

每个原生中文查询形成两个实际输入：原名、原名+原生alias+参考配方前5个原生顺序食材名称+显式状态词。原始工作簿行、item_id、detail_json.name及源文件hash重新读取核对；上下文仅表示参考配方，不推断份量、主料重要性、实际餐盘组成、加工真值或营养量。全部284个查询上下文经实际源恢复；不宣称已经生成经过专家批准的中英文规范名。跨语言由真实模型向量完成，非LLM语义裁定。

每个目标域分别进行原名和上下文的精确余弦 Top20，再取并集，保留原始两套rank和score，以RRF（k=60）融合。先保存重排前pool，包括高分且有明确状态冲突的候选；再按U2-C规则筛除RED，选每库最多3个AMBER。所有关系保持UNRESOLVED、review_status=PENDING，禁止自动等价、物理实例、营养计算、训练或评价release。三类新对象（PilotMethod、QueryContextRecord、SemanticCandidateRecord）为U2-C统一Envelope的版本化扩展；使用标准Draft 2020-12和真实端点依赖校验，未改历史42类合同。源、目标、query、方法及锚点引用完整；混合rights域单独存储（4分区）。

| 目标域 | pool | shortlist | 规则冲突候选 |
|---|---:|---:|---:|
| FoodOn | 9,844 | 852 | 188 |
| FDC SR | 9,535 | 852 | 304 |
| FNDDS | 9,702 | 852 | 76 |
| 合计 | 29,081 | 2,556 | 568 |

568条规则冲突候选全部保留在pre-rank证据池、不得进shortlist；涉及72个查询（食材29、菜肴43）。此为有限显式状态规则的筛查，不等于独立专家认定的全部困难负例。其余候选不自动认定正确或无冲突。

## 3. 真实开发比较及重要反证

| 配对组 | 查询 | 旧方法至少一候选 | 新方法至少一shortlist |
|---|---:|---:|---:|
| 食材 | 128 | 85 | 128 |
| 菜肴 | 60 | 14 | 60 |
| 合计 | 188 | 99 | 188 |

此前89个没有候选的配对查询得到新近邻。96新开发查询均得到近邻。**这不是召回率/精度的提高证明**：旧方法含词法阈值、新方法固定Top-K且没有语义拒绝阈值，即使无正确目标也会生成邻居。旧方法在固定三库的891条候选边中，132条在新pool，33条在新shortlist；这只测候选集合重叠，非真阳性。配对组不独立，新样本仅开发用途；不存在准确率、校准概率或正式gold。

原名/上下文检索消融诊断（852个query-target-scope组合）：
| 指标 | 实测 |
|---|---:|
| Top-1目标发生改变 | 729 |
| 原名Top-1显式冲突 | 11 |
| 上下文Top-1显式冲突 | 29 |
| RRF融合Top-1在风险筛前显式冲突 | 21 |
| 筛后RED进入shortlist | 0 |

上下文扩展显著改变排序，并使规则识别的Top-1状态冲突增加；**不能宣称增加配方上下文已经改善语义质量**。后续独立裁定需将原名、上下文、融合三臂分开评估，检查主要食材与菜肴整体粒度混淆、菜系/状态/成分限定及长尾无适用目标。显式状态规则有漏检，不将RED以外视为正确。

## 4. 工程、科学合同与数值复核

| 验收 | 实测 |
|---|---:|
| 持久化类型化对象（1方法+284上下文+29,081候选） | 29,366/29,366 |
| 源上下文重新恢复 | 284/284 |
| 三库每查询两套Top20完整性、融合及非RED shortlist排序组 | 852/852 |
| 模型实际重复推理spot | 36对、72个分数 |
| spot最大绝对差 | 0.0130452（预设0.02数值容差内） |
| 集成测试 | 24/24 |
| 新source-only/hidden配对 | 44/44 |

全量对象、精确依赖、原生源定位、版本、rights分区、rank闭包、RRF与风险准入逐条核验。模型数值spot用相同固定模型但不同batch，动态量化可能产生差异；容差只用于数值复现，不是科学准确度；未独立重跑全部向量检索。24项实际测试覆盖伪造等价/训练/物理实例、伪造概率、缺依赖、错误锚点/粒度、rights去除、额外字段、源标签篡改、真实RED去标/进shortlist、明确中文冲突及U2-C发布拒绝等。执行验证与冻结报告保留，原44队列指纹不变。

## 5. 独立审核准备、冻结及资格门

原44条Gemini开发审核输入不变，新建独立的44条增量队列：
| 分层 | 数量 | 新模型shortlist存在 |
|---|---:|---:|
| U2-C新增规则RED来源（全18） | 18 | 4 |
| 高词法分数AMBER分层 | 12 | 1 |
| 新中文食材 | 7 | 7 |
| 新中文菜肴 | 7 | 7 |
| 合计 | 44 | 19 |

其中25个仅有U2-C旧候选、5个同时有新旧候选、14个只有新检索。不是统一配对评价样本。source-only与candidate-hidden文件分离，44个一一配对和引用闭包真实核验，和原44重叠0。新队列位于 `real_001/private/ReviewSourceOnlyQueue.json`；隐藏候选不得提供给独立Critic。所有生成器输出、代码、配置及队列指纹锁入 `freeze_001/GeneratorFreezeReceipt.json`。文件隔离不证明强访问控制，Gemini过去审计过代码，44+44均非确认性科学评价。旧Critic冻结收据未出现，审核完成0，专家裁定0，正式等价0，正式MappingRelease 0。

[独立审核资格协议](../../configs/udf/u3b/U3B_ReviewQualificationProtocol_v0.1.json) 定义冻结校验、明示解盲、版本化原生目标ID、方向关系、分歧裁定、适格专家参考、指标分母及预注册要求。候选召回=有独立专家认可的目标进入Top-k的查询/在冻结目标宇宙中有合格目标的查询；无合格目标或未解决单列。边精度按指定关系和用途审查，不以双模型一致为真值。正式抽样概率、误配阈值、置信下界、样本量/停止规则须在确认集解盲前由PI和专家确定；开发队列的风险富集比例不可作总体误配率。所有科学用途继续HOLD。未实施独立Critic结果读取或自动合并。

## 6. 交付及复现

- [运行配置](../../configs/udf/u3b/U3B_PilotProfile_v0.1.json)
- [生成器运行报告](../../runs/B2/U3-B/real_001/U3BGeneratorReport.json)
- [三类扩展对象合同](../../runs/B2/U3-B/real_001/U3B_PilotContract.schema.json)
- [验证报告](../../runs/B2/U3-B/validation_001/U3BValidationReport.json)
- [生成器冻结记录](../../runs/B2/U3-B/freeze_001/GeneratorFreezeReceipt.json)
- [阶段准入记录](../../runs/B2/U3-B/U3BAdmissionReceipt.json)

Mac NutriOne根目录使用相同U2-C锁定输入、已下载模型和Conda依赖，创建新目录（不覆盖本轮）：

```sh
/Users/zhangcd/miniconda3/bin/python -B src/u3b/run_u3b.py --root . --profile configs/udf/u3b/U3B_PilotProfile_v0.1.json --out runs/B2/U3-B/real_002
/Users/zhangcd/miniconda3/bin/python -B tests/u3b/verify_u3b.py --root . --profile configs/udf/u3b/U3B_PilotProfile_v0.1.json --run runs/B2/U3-B/real_002 --out runs/B2/U3-B/validation_002
/Users/zhangcd/miniconda3/bin/python -B tests/u3b/freeze_u3b.py --root . --profile configs/udf/u3b/U3B_PilotProfile_v0.1.json --run runs/B2/U3-B/real_002 --validation runs/B2/U3-B/validation_002 --out runs/B2/U3-B/freeze_002
```

现有代码针对Mac本地NutriOne布局（B0适配器在src/b0；仓库历史代码归档于scripts/udf/b0）；无原始私有输入的GitHub CI不能替代真实数据验证。源/目标词条、配方上下文、逐条候选、审查包和111.43 MB私有生成结果保留本地；只同步合同、代码、汇总证据及冻结记录，不上传模型或原始行。全局B0/B1/U3和独立映射冻结仍HOLD。

## 7. 下一步和责任

完成U3-B生成器子包（开发级），进入U3-B-C1独立审核收据验证与开发分歧审查：先由Gemini完成原44条冻结，明确解盲授权后验证目标存在、原生方向、证据及分歧。新44增量由独立Critic另轮审核，不改原队列；营养/测量高风险需适格专家。然后按开发误差和成本预注册独立确认样本及资格门，才可能产生有限任务MappingRelease。当前不进入B3正式计算或U5研究release，不需要PI搬运更多媒体数据。
