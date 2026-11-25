---
title: "B2 / U3-A — Canonical Food & Component Vocabulary, Source-Family Registry & Candidate Alignment"
version: "0.1"
execution_date: 2026-11-25
archive_date: 2026-11-26
authority: "AI Nutri Unified Data Foundation v2.1"
status: "PASS_BOUNDED_U3A / MAPPING_RELEASE_HOLD"
run_id: "B2-U3A-real_002"
---

# B2 / U3-A｜统一词表、来源家族与候选语义对齐

## 0. 实际执行结论

依据 [UDF v2.1](../AI_Nutri_Unified_Data_Foundation_v2.1.md) §§15–21,35,41 与 [U2-B](B1_U2-B_Measurement_Semantics_Namespace_D0_Bridge_v0.1.md) / PR #56，实际从 NutriData、已审计公开样本及官方标准快照提取原生词表，生成来源家族及候选对齐。第二轮 real_002 退出码0，恢复执行记录后完成额外审核队列审计。**本次通过的是限定开发级词表/候选生成与工程验证，不是等价映射发布或 U3 全局冻结。** 原始数据不改写，既有 UDF/D0/B0/B1资产不改写。

| 对象/验收 | 实际 |
|---|---:|
| 来源快照域 / 词表域 | 22 / 21 |
| 原生词表及锚点 | 65,592 / 65,592 |
| 候选检索查询 / 有候选 | 2,066 / 1,972 |
| 食物候选映射 / 来源锚定概念候选 | 17,079 / 2,876 |
| 原生属性字段 / NutriData字段候选 / FDC候选边 | 572 / 98 / 112 |
| 来源家族声明 / 潜在家族 / 词表记录绑定 | 26 / 11 / 51,406 |
| FNDDS同周期双载体编码关联 | 8,690 |
| SNAPMe原生食品码候选关联 / 短码隔离 | 4,640 / 121 |
| 类型化对象及回放 | 216,827 / 216,827（13类） |
| 合同测试 | 34/34（10接受、24拒绝） |
| 审核队列 / 已审核 | 44 / 0（原40+红标补充4） |
| 已接受跨源等价 / 正式MappingRelease / 科学测量资格 | 0 / 0 / 0 |

## 1. 标准数据实物、版本与来源登记

| 标准 | 实际下载与解析 |
|---|---|
| FoodOn | [官方稳定入口](https://purl.obolibrary.org/obo/foodon.owl)，RDF/XML 40,779,019 bytes，内部versionIRI为2026-09-20。指定日期路径第一次404，稳定入口实物核验后使用，保留版本字段与sha256；原文件含另一versionInfo日期，不擅自归一。 |
| FDC SR Legacy | [USDA 2018-04 CSV release](https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip)，7,793个食品和NDB crosswalk，474个营养素字典记录，644,125个food_nutrient记录，149个实际出现营养属性ID；检查food及nutrient外键无孤儿。保留55个derivation_id计数组，不能据此证明独立实验。 |
| FNDDS 2015–16 FDC carrier | [USDA历史FDC调查食品CSV](https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_survey_food_csv_2020-03-31.zip)，实际内部start/end date均为2015-01-01至2016-12-31；8,690个唯一FoodCode及fdc_id。 |
| FNDDS 2015–16 ARS carrier | [USDA ARS Foods and Beverages XLSX](https://www.ars.usda.gov/ARSUserFiles/80400530/apps/2015-2016%20FNDDS%20At%20A%20Glance%20-%20Foods%20and%20Beverages.xlsx)，8,690个唯一8位食品码。 |

四份实物与取得记录、SHA256等均在 [SourceSnapshotRegistry](../../runs/B2/U3-A/real_002/SourceSnapshotRegistry.json) 登记，原始文件/获取清单留本地 inputs/。本轮未下载或接入FDC全系列数据库、FNDDS所有周期，未验证后续NHANES周期crosswalk。

FoodOn：40,107命名类、39,707有标签类。只取从FOODON_00001002 food product根沿显式命名subClassOf可达、FOODON命名空间、非deprecated且有标签的12,362类；13,858条保留子图命名父类边，无环验证通过。保留原标签、原始IRI、原生同义词及类型；不使用OWL推理器，不声称覆盖所有可食物质，不将导入的动植物、化学物或过程类一律当食品。官方层级边与本轮候选映射分开。

## 2. 原生词表及候选注册表

| 词表域 | 记录 |
|---|---:|
| NutriData食材成分库 | 3,446 |
| NutriData菜肴参考配方 | 22,180 |
| FoodOn选定食物产品类 | 12,362 |
| FDC SR Legacy食品 | 7,793 |
| FNDDS FDC载体 | 8,690 |
| FNDDS ARS载体 | 8,690 |
| Food-101类别 | 101 |
| UEC-Food100 / 256镜像类别 | 100 / 256 |
| ISIA Food-500类别 | 500 |
| Food-11纠正镜像粗类 / Food-5K存在性类 | 11 / 2 |
| Fruits-360当前目录 | 279 |
| 原版Nutrition5k食材 | 555 |
| Menu-Match菜单项 | 41 |
| XiaChuFang / RecipeNLG镜像样例菜谱 | 12 / 12 |
| OFF单商品 / 搜索API快照 | 1 / 10 |
| EPIC名词（混合动作物体词表） | 300 |
| FoodX-251镜像数字类别ID（无可靠名称） | 251 |

65,592是来源词表记录而非去重食品数，包含同周期FNDDS两载体、存在性分类、动作物体词表及未命名数字ID。Snapshot 22另含不产生词表的SNAPMe linkfile。原生词表键均按域校验；原名、alias、source locator和hash保留，不将casefold名称作主键。每个记录具有VocabularyAnchorDraft及不可变版本依赖。2,876个CanonicalFoodConceptCandidate只是被选定/引用的NutriData或FoodOn来源锚点候选，尚未赋等价类，不是2,876个独立规范真值概念。

## 3. 食物语义候选与限制

实际使用NFKC/casefold及保留原名的token/字符bigram、IDF加权Jaccard检索（候选池160，单查询路径每目标域Top3，阈值0.12；多路径合并最多15候选/词条）。双语种子由本轮研究者/Agent编写，仅作为开发候选；保留带括号限定的原始名称，译词仅辅助检索。不使用跨语言embedding、LLM reranking、校准概率或独立Critic完成的判断。所有AlignmentRecord的relation_type与source_relation_to_target均为UNRESOLVED，proposed_relation单独存储且方向source→target。绝不将词法精确surface升为EXACT；BROADER_TARGET只是待核实提议。风险路由：17,075 AMBER、4 RED；RED规则数量不是全部真实冲突数。

| 查询范围 | 词条 | 至少一候选 | surface exact候选 |
|---|---:|---:|---:|
| Food101 | 101 | 101 | 41 |
| UEC100/256 | 356 | 356 | 74 |
| ISIA | 500 | 499 | 107 |
| Food11 | 11 | 11 | 2 |
| Fruits360 | 279 | 279 | 0 |
| Nutrition5k | 555 | 555 | 246 |
| Menu-Match | 41 | 41 | 7 |
| XiaChuFang | 12 | 12 | 1 |
| RecipeNLG | 12 | 12 | 0 |
| NutriData食材 | 135 | 90 | 64 |
| NutriData菜肴 | 64 | 16 | 4 |
| 合计 | 2,066 | 1,972 | 546 |

95.5%仅表示存在至少一个词法候选，不是精度/召回或独立概念覆盖。提议分布：12,294 AMBIGUOUS，4,080 RELATED，611 CLOSE，94 BROADER_TARGET；按查询路径统计RAW_NON_ZH_LEXICAL 15,861，AUTHORED_BILINGUAL_REVERSE_SURFACE 229，RAW_ZH_LEXICAL 35，带限定head翻译729，整词双语225。中文NutriData为候选hub本身，查询时禁止同域映射且按类型排除另一NutriData域，因此当前英文外部检索依赖有限双语种子，未开展中文同域别名归并；16/64菜肴结果不能作为全部22,180菜谱可映射比例。后续以中文地方菜、烹饪方式、主料和保留状态为核心补跨语言语义检索及候选重排。FoodX数字标签251、Food5K二类、EPIC混合物体300及OFF商品11均不进入当前菜品概念匹配，保留各自身份域。

## 4. 真实 FNDDS 版本连接

FDC与ARS的8,690个食品码全部一致；8,626个主描述原文精确一致，64个仅首尾空白不同，trim后8,690个一致。real_001因错误地要求原文字符串完全相等而在落盘前失败，real_002改用明确限定的trim比较并保留原始字符串及差异状态，未修改任何源。双载体为同周期数据的两份载体，不是独立测量。

SNAPMe全4,761原生行中4,640条8位码全部在两载体找到，且source Food_Description与ARS主描述trim后全相等，外键孤儿0。121条非8位码继续隔离，不补零、不推断补充剂、不跨周期join。对全部4,761行建立来源快照、原生行定位、目标ref或HOLD状态的NativeCodeLinkCandidate；8,690个FNDDSCarrierCrosswalk为同周期原生代码关联。所有关系禁止自动升级为同一实际食物、聚合摄入、营养测量或科学参考；ASA24原观测粒度、CodeNum/ModCode语义及来源独立性仍需资格化。

## 5. 组件词表及来源家族

FDC 474个字典字段与NutriData两库98个(name,unit,scope)原生字段分别保留，共572个ComponentNativeField；98个本地来源字段候选链接到U2-B已有概念或本地扩展（非已审核的独立营养素）。90/98字段有至少一个实际FDC字典候选；8个保留未匹配。112条候选边中80 AMBER、32 RED，98条目标ID在实际SR Legacy food_nutrient记录出现。数值存在不代表可比较。区分Energy不同算法、不同碳水定义、RE/RAE、叶酸/DFE、GI、NRV与源单位。所有分母、源方法、转换及等价仍HOLD；不将候选字典映射直接写进营养计算。

来源家族：26个原始来源/载体声明，归为11个潜在家族，51,406条词表记录绑定（不是全词表完整独立样本谱系）。NutriData食物成分库17种声明，35条USDA来源，2,493条声明来自《中国食物成分表》各版，487条内部数据；22,180菜肴记录源标签空，保留配方来源不明。USDA_COMPOSITION的25,763个词表绑定含SR Legacy、两个FNDDS载体、Nutrition5k成分及NutriData USDA转引；SNAPMe来源家族另由code-link依赖表达。不得将这些绑定计数当作独立测量数。家族共享是可能相关依赖，不宣称同一原始样品/实验；不明来源不能默认独立。

## 6. 工程验收与补充审核

B2 real_002实际216,827对象、13个类型集合的写入、读回、revision及引用闭包全部通过；65,592原生词表从实际源重新提取并核对逻辑内容；60个候选边分层重新执行相同检索器核对排序/分数/匹配形式；8,690个FNDDS跨载体、4,761个SNAPMe候选重新验证；34/34合同测试（10正、24负）通过，包括方向错误、自动EXACT、错误单位/分母、跨周期、短码补零、同源独立性、实例提升、泄漏与错误版本。此为同一实现回放/工程约束，不是独立科学方法、外部gold或全局D0迁移。源文件扫描前后hash一致；此前U2-A、U2-B准入指纹检查通过。

原40个source-only开发审核词条（5个无候选）全部尚未人工/独立Critic审阅。恢复后检查发现原队列未覆盖4个规则RED来源；新建独立review_queue_audit_001补充4个，原运行不改写。共44个来源、全部4个当前规则RED均覆盖、已审阅0；候选refs与source-only文件分离，未证明真正blind访问控制，不属于确认性独立评价。后续需独立复核规则未捕获的状态/粒度冲突，设计独立分层精度/召回样本；不使用这44条开发样本作为独立准确率证明。

## 7. 交付物、执行与下一阶段

- [B2RunReport](../../runs/B2/U3-A/real_002/B2RunReport.json)
- [ExternalStandardAudit](../../runs/B2/U3-A/real_002/ExternalStandardAudit.json)
- [SourceSnapshotRegistry](../../runs/B2/U3-A/real_002/SourceSnapshotRegistry.json)
- [SourceFamilyRegistrySummary](../../runs/B2/U3-A/real_002/SourceFamilyRegistrySummary.json)
- [CandidateAlignmentReport](../../runs/B2/U3-A/real_002/CandidateAlignmentReport.json)
- [ComponentAlignmentReport](../../runs/B2/U3-A/real_002/ComponentAlignmentReport.json)
- [ContractValidationReport](../../runs/B2/U3-A/real_002/ContractValidationReport.json)
- [ReviewQueueAudit](../../runs/B2/U3-A/review_queue_audit_001/ReviewQueueAudit.json)
- [B2AdmissionReceipt](../../runs/B2/U3-A/real_002/B2AdmissionReceipt.json)

代码GitHub scripts/udf/b2/；Mac src/b2/。保留真实输入、B0/B1输入清单、external acquisition manifest与hash固定的标准实物，Mac根目录以新目录复现：

```sh
python3 -B src/b2/run_b2.py --root . --out runs/B2/U3-A/real_003
python3 -B src/b2/test_b2.py --root . --run runs/B2/U3-A/real_003
python3 -B src/b2/audit_review_queue.py --run runs/B2/U3-A/real_002 --out runs/B2/U3-A/review_queue_audit_002
```

原始词条/代码/候选边、参与者相关行、review source/hidden文件及私有锚点约390 MB保存在Mac real_002/private/；标准输入约50 MB。仅同步代码、报告、汇总、快照指纹与准入记录，不上传原始行。Mac剩余空间约58 GiB，不扩大媒体复制。

总体Milestone：U0 v2.1归档；U1限定原生画像；U2-A/B限定通过，B1全局冻结HOLD；U3-A限定词表/候选生成通过，U3整体仍HOLD；U4–U9未执行。**建议B2 / U3-B｜Bilingual Semantic Expansion, Independent Candidate Review & Alignment Qualification Pilot**，从中文食材和菜肴的语义扩展、44条开发队列开始，形成独立复核与受控映射释放门；并行补NutriData官方分母/配方note字典、FDC定义/单位、来源家族、冲突量化及真实数据版本。Food2K原生类表与VIREO原生类别/353食材标签仍未取得，若激活相关任务，仅请求这类最小文件，不要求搬运全量媒体。所有未知继续HOLD，正式MappingRelease及科学用途资格仍0。
