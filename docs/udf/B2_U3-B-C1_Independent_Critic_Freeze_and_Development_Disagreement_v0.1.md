---
title: "B2 / U3-B-C1 | Independent Critic Freeze Verification & Development Disagreement Adjudication"
version: "0.1"
date: 2026-11-27
authority: "AI Nutri Unified Data Foundation v2.1"
status: "PASS_C1_DEVELOPMENT_COMPARISON_AND_RISK_ROUTING / EXPERT_AND_SCIENTIFIC_QUALIFICATION_HOLD"
baseline: "PR60 / 354267b1a15c879038c1ba8d2d2eae59eba2d94d"
---

# B2 / U3-B-C1｜独立审计冻结核验及开发语义分歧裁定

## 0. 裁定

PI在会话中确认Gemini已冻结并授权C1。本轮先检查C0冻结、全部输入指纹及原始目标证据，再读取U3-A原44条隐藏候选执行比较。实际运行 real_001 和只读 validation_001 均exit 0。**通过开发级冻结核验、候选分歧比较及风险归因；专家独立参考、MappingRelease、全局科学资格和B3正式计算仍HOLD。** 本轮仅评价原U3-A的40基础+4补充审核案例，不混入U3-B新284查询或新44条队列。未改变原始文件、历史模型结果、Critic冻结或总纲。

## 1. C0真实冻结和目标核验

- 8/8允许输入、5/5冻结成果文件、44/44唯一review_id及source_ref、195/195逐条目标ID、主标签trim比较、原件locator均通过，两个注册表与逐案记录严格一致。原始FoodOn 39,707个命名有标签类、SR Legacy 7,793食品、FNDDS 8,690食品码、ARS同周期8,690记录独立解析；FNDDS按同周期FoodCode计一次。
- 195条中37条提供与FoodOn原文一致的定义，34条提供FNDDS ARS附加描述（非正式概念定义），124条未提供定义。目标确实存在不等于对应语义正确。
- Critic声明禁止访问0，既有文件改写0；已有U3-A代码/汇总报告历史暴露，具体Gemini模型build不可取得。访问声明无法凭输出文件证明操作系统级隔离，不宣称确认性严格盲审。
- C0的当前任务配置要求字段存在而未冻结全部嵌套类型；较早提示要求composition_constraints、regional_constraints、field_evidence为数组，实际分别为字符串、字符串、字典（各44）。本次按当前配置做身份和字段验证，保留该物理类型差异，未来应明确版本化ReviewRecord Schema，不原地改写原Critic记录。
- Critic报告88候选，107困难负例（44案均有），40案有候选、4案无可靠候选；GREEN 0、AMBER 16、RED 11、HOLD 17；27案建议专业审核。关系：CONDITIONAL 27、CLOSE 23、BROADER_TARGET 22、NARROWER_TARGET 6、RELATED 8、AMBIGUOUS 2、EXACT 0。所有均为CRITIC_DRAFT。

## 2. 比较对象和分母

冻结U3-A对象和隐藏队列经31份输入指纹及对象revision、source_ref、原生key、CandidateQueryRoutes一一闭包核验；U2-C的旧边新投影对应精确legacy_ref。共同可比较范围为FoodOn IRI、FDC SR fdc_id、FNDDS 2015–16 food_code（FDC/ARS不重复）。NutriData等其他目标范围单列。比较同一来源与同一目标原生ID，不用名称等价代替ID，不将proposed_relation当作批准关系。

| 统计 | 实际 |
|---|---:|
| 原生成器候选总边数 | 355 |
| 共同外部标准域候选 | 325 |
| 其他目标域 | 30 |
| 双方共有候选ID | 32 |
| 原生成器命中Critic困难负例 | 23 |
| Critic未判断的外部候选 | 270 |
| Critic独有候选 | 56 |
| 其中在原生成器目标词表 | 49 |
| 其中不在原生成器词表 | 7 |
| 共有32条中的提议关系同型 | 9 |

325=32+23+270；88=32+56；355=325+30。39案有原生成器候选、40案有Critic候选；36案两方均有候选（包含非共同目标域），3案仅原生成器、4案仅Critic、1案两方皆未找到。共同外部标准候选两方均有34案，其中17案有共同ID、17案无共同ID。共同ID不等于正确，Critic未判断不等于错误，关系同型不是准确率。Critic困难负例为其判断而非专家Gold；不由其数量估计总体误配率。

原40基础队列：319原边、77 Critic候选、91困难负例、31共有、17负例重合；4规则RED补充：36原边、11 Critic候选、16困难负例、1共有、6负例重合。选择风险富集，不是总体代表性或确认性样本。

## 3. 开发级根因归因

23条命中Critic困难负例的边中，原U3-A及U2-C均为4 RED/19 AMBER。U2-C明确生熟冲突4条继续fail-closed（含两个词法score=1.0的raw候选），不意味着其所有科学风险识别已完成。根据实际来源和目标名称、Critic理由，控制端进行以下开发级风险分类：

| 风险族 | 边数 | 当前U2-C |
|---|---:|---|
| 明确状态矛盾（原标签明示） | 4 | RED |
| 未明确配方、加工或具体亚型 | 7 | AMBER |
| 物种或组成改变 | 5 | AMBER |
| 食品组件/整体或菜肴形态 | 4 | AMBER |
| 熟制/即食状态依赖推断 | 3 | AMBER |

必须区分**明确冲突、未知限定、粒度差异、条件性近似**；不是19条AMBER全部应该直接判为RED，更不能把所有未声明属性默认互斥。为每条生成RiskAttributionRecord，明确HOLD及专业复核，不升级科学等价。优先专家队列36案=Critic建议27案与17个困难负例重合来源的并集（交集8）；其余8案仍开发审核。36不是已完成专家仲裁数。科学参考0。

## 4. FoodOn目标范围问题

56条Critic独有候选中49条在原28,845条固定外部词表，属于检索候选差异；7条外部范围外候选来自6个活动FoodOn类（有一个类在不同来源中重复）。重新解析每个类的显式命名subClassOf祖先闭包，6/6不能抵达U3-A所使用的food product根FOODON_00001002，且原件确有定义/命名类及相关父类。原先仅取显式命名闭包的保守选择导致范围缺口，不能把七条计为同一词表内的检索失败；也不能直接全量放入40,107个类。未执行OWL推理；应审计食品产品类的复杂定义、相关分支及推理后范围，再建立新版本候选准入规则和非食品负例。

## 5. 反向核查Critic结论

对七个声明标准缺少目标的相关案例执行有限字面/别名检索；4个无字面hit，3个存在合计19个相关或附加描述hit（4+1+14）。实际发现包括冷冻未制或馄饨变体、含特定配料的相关菜肴及主描述为boiled而附加描述包含steamed的FNDDS条目。这些不能证明存在精确等价目标，但足以说明不能把有限检索的“未发现”提升为全标准“绝对不存在”。原判定保留、潜在相关项转开发复核。无hit亦不能证明不存在。未核验Critic报告里所有具体定量营养误差假设，不作为本轮证据。

## 6. 验收

实际只读重放：44来源、195目标、44比较记录、31输入文件及9冻结结果文件均一致。另做行列表独立汇总、同周期载体键一致性、风险分类、FoodOn真实祖先闭包和错误hash/重复键/错周期/虚构ID/越界目录等检查，16/16通过。此为同一实现重放及独立计数校验，并非独立科学验证。全部历史对象、源及Critic冻结未修改。

正式映射等价、独立专家真值、科学计算与MappingRelease均0。没有U3-B多语言生成器的独立质量估计，本次不产生精度/召回或置信区间。

## 7. 交付及下一阶段

- [C1配置](../../configs/udf/u3c1/C1_ComparisonProfile_v0.1.json)
- [冻结核验](../../runs/B2/U3-B/C1/real_001/CriticFreezeVerificationReport.json)
- [分歧比较](../../runs/B2/U3-B/C1/real_001/DevelopmentComparisonReport.json)
- [冻结记录](../../runs/B2/U3-B/C1/real_001/C1FreezeReceipt.json)
- [只读回放与风险归因](../../runs/B2/U3-B/C1/validation_001/C1ValidationReport.json)
- [准入记录](../../runs/B2/U3-B/C1/C1AdmissionReceipt.json)

在Mac NutriOne根目录（原始输入保持相同hash）复现至新目录：

```sh
/Users/zhangcd/miniconda3/bin/python -B src/u3c1/run_c1.py --root . --profile configs/udf/u3c1/C1_ComparisonProfile_v0.1.json --out runs/B2/U3-B/C1/real_002
/Users/zhangcd/miniconda3/bin/python -B tests/u3c1/verify_c1.py --root . --profile configs/udf/u3c1/C1_ComparisonProfile_v0.1.json --run runs/B2/U3-B/C1/real_002 --out runs/B2/U3-B/C1/validation_002
```

逐案分歧、目标原件定位、风险归因、范围诊断和专家队列位于C1运行private目录，原始Critic结果和新审核词条不上传。GitHub仅代码/配置/聚合报告和hash冻结收据。下一工作包建议U3-B-C2：先修正目标宇宙、显式冲突/条件不明/粒度的分离、允许拒绝无合格目标，再组织36优先案例的专业裁定。原44开发审核不可重用作确认性Gold。新44增量审核可独立进行，但按原方案它仅19案拥有新生成器候选，必须与25案旧风险审核分层，不当成统一配对评价。下一轮独立审计由控制端发出精确配置和可复制指令。
