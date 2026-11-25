---
title: "B1 / U2-B — Measurement Semantics, Namespace Qualification & D0 Bridge Conformance"
version: "0.1"
date: 2026-11-25
authority: "AI Nutri Unified Data Foundation v2.1"
status: "PASS_BOUNDED_U2B / GLOBAL_B1_FREEZE_HOLD"
contract_version: "UDF-B1-SEMANTICS-DRAFT-0.1"
run_id: "B1-U2B-real_003"
---

# B1 / U2-B｜营养测量语义、命名空间资格化与 D0 桥接符合性

## 0. 执行结论与验收边界

依据 [UDF v2.1](../AI_Nutri_Unified_Data_Foundation_v2.1.md) §§11,15–22,34–37,41、Nutrition Foundation v0.1 Part III §§2.2–3.2、NDF-D0 §§5–10，以及 [U2-A](B1_U2-A_Source_Native_Contract_and_Real_Roundtrip_v0.1.md)，在真实 U2-A real_003（PR #55）不可变输入上执行。最终基线为 U2-B real_003，UTC 2026-11-25T15:10:55.699574+00:00。**限定语义解释、来源命名空间及共享科学对象桥接验收通过；全局 B1 物理冻结、科学测量资格、生产 D0 迁移及正式 release 仍 HOLD。** 本次不修改 UDF master、U2-A、原始文件或既有 D0。

| 验收项 | 实际结果 |
|---|---:|
| U2-A输入对象 | 5,699 |
| 原始文件hash fence前后验证 | 23/23 |
| 上游/来源依据记录 | 11（9本地字节验证、2云端原文hash登记） |
| ComponentConcept候选 | 19 |
| MeasurementDefinition | 43（37有真实选样值，6仅字典定义） |
| 测量解释 | 2,851 |
| 配方/膳食数量解释 | 266 |
| 同源数值表示转换 | 520 |
| 原生命名空间/记录绑定 | 19 / 747 |
| 原生键绑定/关系检查 | 611 / 578 |
| 新对象独立集合 | 10类，5,665个，读回5,665/5,665 |
| D0共享对象精确往返 | 770/770（23 SourceArtifact + 747 SourceAnchor） |
| 原D0固定版本历史回归 | 12/12 |
| 本次合同检查 | 49/49（10接受、39拒绝） |
| 科学测量正式资格/研究release | 0 / 0 |

## 1. 最小语义合同

MeasurementDefinition 使用 NDSF 的 concept_key、value_type、unit、method、reference_window、aggregation、error_model、reliability、validity、cost_definition、leakage_risk，增补原生分母 Slot、component_ref、依据与待解决问题。定义中的 component_ref 是本地概念逻辑ID，真实对象依赖绑定精确的 ComponentConcept immutable revision；未与FDC、FoodOn等外部本体确证等价。19种概念候选包括能量、食品质量、声明蛋白/脂肪、总脂肪、未定义碳水、可利用碳水、总碳水、钠、膳食纤维、RE/RAE、总叶酸/叶酸/食物叶酸/DFE、GI、NRV%、未知配方数量。食品质量不是营养素；GI/NRV不是成分质量；盐不等于钠；同名碳水不等于相同方法。六个仅字典定义不伪造观察值。所有 error_model、reliability、validity 保持待估计。新合同对象 DRAFT，CURATION_DEV，依据快照与研究者构造定义/派生解释保持来源和 instance_class 分离。

原生测量、解释、单位表示转换分别存储；不改写原字段，不把算术结果升级为独立测量。对概念、定义、来源域、记录、键、候选关系使用独立集合与精确revision依赖。全量源表的内部一致性检查另存，不把方便选样当作代表性评价。

| 来源 | 测量草案数 | 字段级裁定 | 计算/参考边界 |
|---|---:|---|---|
| NutriData 01/02 | 840 | 原生单位，分母/来源方法未知 | 226配方note均HOLD，不填克数；不估计油盐先验 |
| Nutrition5k原版 | 1,715 | 原版每克成分、餐盘和食材行质量/能量定义 | 480每克→每100克仅同源表示，留存食品状态/来源依赖；冲突总量HOLD |
| SNAPMe | 200 | ASA24-2020 Record Items字段定义 | 40个SODI mg→g仅同源数值转换；40个FoodAmt数量解释保留重复列，不合计 |
| OFF | 55 | 官方schema标准numerator规则，100g/100mL分母未定 | 55行录入值和API值相符，但无区分不同录入/标准单位的实例；文档冲突仍记录 |
| Menu-Match | 41 | 菜单热量单位 | 份量分母未知，不视为摄入或称重真值 |

状态计数：1,915 SOURCE_FIELD_CONTRACT_SUPPORTED；55 SOURCE_NUMERATOR_CONTRACT_SUPPORTED_BASIS_HOLD；881 HOLD_SOURCE_SEMANTICS。三个状态均不具有科学计算/评价资格。外部来源标准是本轮解释依据，不是直接原始成分测量。

缺失值审计（2,851条）：2,543非零数字、284数字零、6破折号、7省略号、7 Tr、4斜线。非数值24条全HOLD未核实语义；数字零只表示源记录报告零，不证明实测零。不得用默认常数填补。所有真实输入未出现负值；未来负数由源限定阻断，不默认为零。OFF官方详细schema与开发说明对 _100g 单位表述有差异；源 schema 支持标准numerator，但记录分母不可仅依据字段后缀认定，未完成跨来源可比性。

## 2. 权威依据及精确定位

保留本地来源快照、sha256、版本、定位和所支持的最窄主张，见 [AuthorityEvidenceSummary.json](../../runs/B1/U2-B/real_003/AuthorityEvidenceSummary.json)。来源包括 [Nutrition5k作者README](https://github.com/google-research-datasets/Nutrition5k)、[SNAPMe研究](https://pmc.ncbi.nlm.nih.gov/articles/PMC10708545/)、[ASA24-2020版本说明](https://epi.grants.cancer.gov/asa24/respondent/2020.html)、[NCI官方2020数据字典ZIP](https://epi.grants.cancer.gov/asa24/researcher/ASA24_2020.zip)、[OFF产品营养schema](https://openfoodfacts.github.io/documentation/docs/Product-Opener/schemas/schemas/product_nutrition/)、[OFF开发解释](https://openfoodfacts.github.io/documentation/docs/Product-Opener/dev/explain-nutrition-data/)、[NutriData官网](https://www.nutridata.cn/)及Menu-Match原生说明。实际解析 ASA24 的 `2020Record/DataDictionary_ITEMS_2020Record.xls` DATADICTIONARY：12个测量字段的具体行及单位、另外6个代码/序列字段；原字典zip及XLS成员hash均验证。XLS解析使用专门放在run inputs中的xlrd==2.0.2，未修改系统Python。没有取得NutriData本地版本匹配字段字典，网站说明不能替代分母及note单位。NDSF及NDF-D0原文由云端核对并登记hash。

## 3. 关键真实数据发现：Nutrition5k 总量冲突

全量读取两份原版餐盘元数据（5,006餐盘、28,455食材明细、555食材参考），验证实际6固定字段+每食材7字段。对每个食材行按原成分表每克值×源质量复算能量、脂肪、碳水、蛋白，28,455×4=113,820个数值比较全部Decimal精确相等。该结果支持**同源计算依赖**，不证明独立化学实测准确。

按总量字段与食材行求和进行独立探索性诊断：

| 子源 | 餐盘 | 5项均在0.01内 | 至少1项差异大于0.01 |
|---|---:|---:|---:|
| Cafe1 | 4,768 | 4,325 | 443（质量） |
| Cafe2 | 238 | 0 | 238（能量、碳水、蛋白均有差异；235条脂肪差异） |
| 合计 | 5,006 | 4,325 | 681 |

0.01为本轮探索诊断阈值（各自原生单位kcal/g），另报告1e-6、0.1与最大绝对差；不是预注册的科学准确度或删除标准。Cafe1质量冲突443条（413个总量低于和、30个高于和，最大绝对差7935 g）；Cafe2能量、碳水、蛋白总量全部低于明细和。原因尚未核实，不能直接认定总量或明细哪一方错误，不能以另一方覆盖。U2-A选中165个餐盘总量属性，65个冲突标记；100个在探索阈值内也不自动取得参考资格。私有逐条flag保存来源行与原始值，后续量化任务须应用HOLD_SOURCE_TOTAL_CONFLICT并验证来源与扫描依赖组。N5k360仍未完成场景/绝对尺度资格。

## 4. SNAPMe 版本与记录粒度

原研究使用ASA24-2020；NCI版本说明明确FNDDS 2015-16与FPED 2015-16。Items字典FoodAmt是报告份量转换得到的克数，不是称重。SODI mg可做同源g转换；不得与FoodAmt.1重复求和。4,761条全部原始FoodAmt与FoodAmt.1相等，全部原始全行不同。

| 候选键 | 唯一组合数 | 重复组合组数 |
|---|---:|---:|
| subject/day/Occ_No/FoodNum1 | 3,493 | 298 |
| 上述 + FoodCode | 4,754 | 5 |
| 上述 + CodeNum/ModCode | 4,761 | 0 |

七字段复合键仅在当前文件结构唯一，FoodNum1与原Items FoodNum的派生关系尚未证实；不等于独立摄入事件或可聚合观察。FoodCode 4,640条具有8位数字形式，仍仅是FNDDS 2015-16候选；121条非8位（62条5位、59条4位，36种不同值），不补零、不假设属于补充剂或其他代码域。40条选样中39条候选、1条隔离。实际FNDDS目标版本文件尚未入库并验证外键。禁止与NHANES不同cycle直接join。原始个人键及code行值保留本地，公开报告只有统计和字段名。

## 5. NativeNamespace 与独立候选关系

19个来源快照命名空间、747个原生记录定位绑定、611个原生键绑定。13组同一键域内跨命名空间相同原值，表明单值等同不成立。578条候选原生关系按精确原生键及白名单域关系验证：NutriData业务ID+code 220（另6HOLD），原版Nutrition5k补零的食材ID 214，Menu-Match 48，EPIC动作词表/名词/视频ID各32。类别、菜单、扫描、产品、视频、动作、膳食记录不同键域；镜像与原版、Nutrition5k与N5k360分开。接受跨来源实体等价数0，接受跨来源物理实例等价数0。此处仅结构性候选，名称差异与未解决来源不进入真实Gold。真实记录定位采用artifact/locator，不以同名、图片相似度、FoodCode、条码或不同库的内部id建立物理实例同一性。

## 6. D0共享身份的实际桥接

上游D0保持权威。读取并验证commit 09e854dced620645c49b72f5c4040610f162ef59中的12个D0运行时/fixture Git blob，原runtime四类validator实际执行。新实现仅允许 U2-A 的23 SourceArtifact、747 SourceAnchor经显式映射进入临时D0 CURATION_DEV envelope；以桥接域ID对应唯一immutable B1 ref。D0历史bare object_id依赖通过双射转换，SourceAnchor content维持WITHHELD，版本hash/locator/provenance保持。侧车保存上游版本、审计时钟、未授权release Slot和首次修订Slot。实际执行正向、legacy runtime validate_objects、逆向、完整源对象内容与revision一致性检查，770/770通过；落盘后再次回读770/770。其余9种SCI对象继续独立声明并委托既有D0，不构造伪StudyIdentity/EvidenceUnit/Claim。不是生产互操作、外部系统输入、专家参考或全量历史对象迁移通过。原8负例、2正例、真实D1与D2共12项历史回归全部符合预期；两个真实fixture共13个对象旧schema均未显式instance_class，保持迁移HOLD，不默认REAL。D0 runtime code没有修改。拒绝桥接中伪造release、类型错配、源hash及locator篡改、私有内容泄漏和非双射侧车。

## 7. 实际测试、修订与验收

real_001语义与共享桥接成功，但全量源审计遇到非8位FoodCode后停止；修订为显式HOLD原值并重新执行。real_002全量审计通过，合同测试48/49：错误类型确实被拒绝，但验证器返回的错误码顺序与预期不一致；调整桥接全部envelope先验证再遍历引用。保留历史运行，不覆盖。real_003完整成功。

49项合同测试（10正、39负）全部符合预期，独立回读验证2,851测量解释、520转换、266数量解释、747定位绑定、611键绑定、578候选链接、5,665新对象以及770桥接对象；包括真实对象变异和合成边界测试，不等于全量科学验证。未进行E2H人体试验、NDS独立参考、跨来源Gold、生产Parquet/SQL、完整D0迁移或所有22源适配。Gate：G0研究授权HOLD；G1限定输入通过；G2字段解释/缺失/命名空间及共享桥接通过但全局语义冻结HOLD；G3原生结构与内部数值核查部分通过且冲突保持HOLD；G4参考HOLD；G5仅开发用途；G6/G7/G-PROBE未激活。当前实现Python+JSONL；机器可读定义见注册表。科学计算资格0，正式发布0。

## 8. 交付物、复现和下一步

- [ComponentConcept Registry](../../runs/B1/U2-B/real_003/ComponentConceptRegistry.json)
- [MeasurementDefinition Registry](../../runs/B1/U2-B/real_003/MeasurementDefinitionRegistry.json)
- [SemanticQualificationReport](../../runs/B1/U2-B/real_003/SemanticQualificationReport.json)
- [SourceConsistencyAudit](../../runs/B1/U2-B/real_003/SourceConsistencyAudit.json)
- [D0SharedBridgeReport](../../runs/B1/U2-B/real_003/D0SharedBridgeReport.json)
- [ContractValidationReport](../../runs/B1/U2-B/real_003/ContractValidationReport.json)
- [B1BAdmissionReceipt](../../runs/B1/U2-B/real_003/B1BAdmissionReceipt.json)

代码 GitHub scripts/udf/b1b/；本地 src/b1b/。真实输入 U2-A real_003 及冻结依据 inputs/（原始web/XLS快照、官方zip、已校验D0 snapshot manifest）须可用。Mac根目录命令如下；使用新输出目录保留历史：

```sh
python3 -B src/b1b/run_b1b.py --root . --out runs/B1/U2-B/real_004
python3 -B src/b1b/audit_b1b.py --root . --run runs/B1/U2-B/real_004
python3 -B src/b1b/test_b1b.py --root . --run runs/B1/U2-B/real_004
```

原始源、个人记录、逐行冲突值、原生键、D0共享私有对象与侧车均仅在本地 real_003/private/（约13MB），不进入仓库；本次只归档文档、代码、字段/概念注册表与聚合证据。

总体Milestone：U0已归档；U1限定样本画像完成、原档待核验；U2-A限定原生回放通过；U2-B限定语义和共享桥接通过、全局B1仍未冻结；U3–U9尚未执行。**建议下一工作包 B2 / U3-A｜Canonical Food & Component Vocabulary, Source-Family Registry & Candidate Alignment。** 可以并行推进已审计词表/候选对齐，按用途继续核对NutriData分母/份量单位、Nutrition5k冲突、FNDDS真实代码表、外部概念及同源性；不要求PI现在搬运全量文件。关键测量/临床/人体研究资格需适格独立审核。
