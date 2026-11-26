---
title: "B1 / U2-C | Scientific Contract Consolidation, Runtime Enforcement & Non-Regression Qualification"
version: "0.1"
date: 2026-11-26
authority: "AI Nutri Unified Data Foundation v2.1"
status: "PASS_BOUNDED_U2C_HARDENING / GLOBAL_FREEZE_AND_RESEARCH_RELEASE_HOLD"
baseline: "PR #57, 7e861fdf35a1f8d5bde0b35d6f98920276798c3d"
---

# U2-C｜联合科学合同整改与真实运行验收

## 0. 结论与边界

本次依据 UDF v2.1、U2-A/B、U3-A 冻结开发记录和两轮 Gemini Critic 审计，执行 C1–C7 联合加固。新 runtime 对三个历史阶段的228,191个对象做版本化统一投影，新增25,030个餐盘质量对象、26个OFF记录级语义对象及2个API快照，共253,249对象；使用 Conda Python 3.9.16 / jsonschema 4.25.1 的 Draft202012Validator 标准校验器，全量通过，并完整只读回放。另独立补样得到12个符合Schema的OFF源/解释对象，不混入首轮分母。真实执行、重新读取、准入和历史回归均 exit 0。本轮新测试56/56，历史重跑141/141（不是读取原报告充当新测试）；五个此前被错误接受的变异均被拒绝。107份输入/代码/合同文件指纹前后一致。

**通过限定开发级加固；并非全局 B1/U3 冻结、正式科学测量、MappingRelease 或营养计算引擎生产验收。** 原始源数据、PR #55–57历史实现/运行、Gemini现有44条独立审核包保持不变。未读取Gemini的独立审核输出。本轮不授权模型训练、临床应用或公开数据发布。

## 1. 版本化统一合同与复现

| 资产 | 原对象 | 投影/验证 |
|---|---:|---:|
| U2-A real_003 | 5,699 / 17类 | 全量 |
| U2-B real_003 | 5,665 / 10类 | 全量 |
| U3-A real_002 | 216,827 / 13类 | 全量 |
| 新质量及语义对象 | 25,058 | 全量 |
| 总计 | 253,249 / 42类 | 253,249/253,249标准Schema及独立只读回放 |
| OFF第二次定向补样 | 12 | 独立Schema验证，不加进上述分母 |

新统一Envelope为 UDF-U2C-ENVELOPE-0.1，共享18字段（含governance、typed payload）。40类历史Payload及2类新增对象采用显式合同；保留原始 raw/metadata 等有意开放的内部来源表示。拒绝额外未注册业务字段、非法boolean rank、超范围number score；运行时进一步校验源字段、依赖闭包及资格。治理属性通过governance收敛。原object_id保留；新revision_id绑定内容和审计时间；supersedes_ref与legacy_ref指向精确历史版本；引用经锁定历史版本resolver解析，不假称历史引用已全部迁移至新的物理主键。两份只在云端登记hash的权威依据与9份本地字节核验依据明确区分。不同审计时钟下的稳定对象ID及不同revision做限定测试，未重新构建全部不同时间快照。

## 2. C1｜科学测量语义

- OFF官方字段定义 carbohydrates（可利用）、carbohydrates-total（总碳水）与具体产品记录的实际语义独立保存。历史11个碳水解释的有效概念为UNSPECIFIED/HOLD，声明语义保留；不按市场标签猜测法规或转换。追加25个真实API商品（第一批20、第二批5）；第一批源声明11个100mL、9个100g，第二批5个100g；第二批确有2个 carbohydrates-total_100g 字段，并实际保存其解释。没有真实非标准录入单位的可判别值对（0），不能以合成mg→g测试替代。两批的失败/空结果保留本地获取清单。记录级定义、原标签、分母及单位资格继续HOLD。
- 维生素A prior按明确单位解析RE/RAE。真实RAE候选仍正确，测试RE误挂RAE和逆向篡改被拒绝。维生素E FDC 1158为Vitamin E MG_ATE，非1109 alpha-tocopherol MG；1158仅字典存在，没有SR Legacy值，标明DICTIONARY_ONLY_NO_SOURCE_VALUES。候选声明的当量类型一致不证明分析方法等价，不切换1109补值。未知单位FREE/PURE/SCORE等均不可判定，未知与未知不匹配。质量单位、测量等价和实际值可用性分别登记。
- 112条成分候选的既有80 AMBER/32 RED保留候选用途；当量/未知单位判断进一步受控，未批准任一等价、换算或计算。未复核全部FDC分析方法定义或所有源字段字典。

## 3. C2｜Nutrition5k测量准入闭环

从两份原版餐盘CSV独立重新计算5,006×5=25,030个质量记录，原native total与对应食材和分别保留。阈值0.01使用各原生kcal/g单位，仅诊断内部冲突。1,392个属性冲突，涉及681个餐盘；与全部旧冲突标记逐项数值一致。165个选定总量与质量记录绑定（65冲突、100在诊断阈值内）。在旧测量对象及解释的新投影中，质量引用和状态均强制绑定。

通过新Admission入口实际请求全部2,851个测量：
| 判定 | 数量 |
|---|---:|
| HOLD_SOURCE_TOTAL_CONFLICT | 65 |
| OFF_RECORD_COMPONENT_DEFINITION_UNRESOLVED | 11 |
| MEASUREMENT_NOT_QUALIFIED | 2,775 |
| ALLOW用于计算 | 0 |

质量引用缺失、未绑定、解释缺失的真实对象反例均HOLD，冲突原因优先于普通未资格化。阈值内100条并不获得科学参考资格；不修改源总量、不替代独立化学或称重真值。

## 4. C3｜运行时约束与边界

新入口 src/u2c/admission.py 先验证实际版本化投影和真实依赖，再作用途裁定；调用者提供对象引用而非自证资格。重算hash的伪造内容也必须与从锁定源重新生成的合法投影一致。来源家族校验从仅有声明与孤立函数推进到载体、原始来源标签和规则一致性检查；独立计权请求在没有任务级独立性资格时HOLD。所有候选保留CURATION_DEV；原生关系只用注册命名空间、端点类型及原生键规则。原14个孤立守卫的职责由新策略/运行时或明确NOT_IMPLEMENTED_DENY接管，并非直接调用全部旧函数。未实现的几何、摄入聚合、独立参考、锁定探针、训练、发布、临床等用途拒绝；仍需在真实B3/U5消费者实现时做接入验收。不是OS层或任意第三方代码不可绕过的权限沙箱。

五项旧审计实际反例：伪造独立性、错误载体家族绑定、RAE prior改RE、未注册Payload字段、缺少必要来源依赖，新实际验证全部拒绝。额外测量/质量、版本、许可域、关系、类型、时间与单位反例见测试报告。19正例、37拒绝或HOLD测试均符合预期。

## 5. C4/C5/C6｜合同收敛、可重复验证与来源治理

源特定原生配方和关联规则抽至 U2C_Policy_v0.1.json；历史计数、文件指纹、原运行路径抽至 HistoricalBaselineProfile_v0.1.json，生成独立manifest。新的execute写入全新目录，verify读回不覆盖执行目录；附加报告必须新路径。新源规则可以注册，无需修改相应核心查找逻辑；合成规则测试验证此性质，不代表XiaChuFang/RecipeNLG新原生适配器已完成。旧适配器和测试保留历史实现，不原地改写。历史报告分开生成；旧U2A报告名称初次恢复有差异，改正后实际重跑通过。

新投影按来源及依赖传递的rights_domains分19个本地物理分区，混合依赖使用单独受限区。每区按kind分别存储。OFF、NutriData、USDA、FoodOn和观察记录分域，混合源的许可判断不以文件拼接自动推论；不宣称已经通过法务审批或全部来源许可兼容。旧私有文件仍保持不变。统一模型、物理分区和发布许可三层区分；所有release HOLD。

## 6. U3-A候选风险复筛（不替代U3-B）

在17,079条已持久化边上，补充明确中文加工、鲜冻、生熟及限定词规则。4条旧RED保留，新增33条RED，总37条，涉及22个来源词条。原44条开发审核包覆盖4个原规则RED来源；新增18个尚未在队列中。高词法分数AMBER来源558个，其中547个不在现有队列；1,950个来源有状态维度未决。仅反映规则筛查，不等于真实冲突总数或映射正确率。新通用只读审核可复跑（实际两次结果一致），没有写入旧队列、没有发布新审核队列或读取Gemini输出。U3-B需独立检索、多维语义、保留排序前困难负例和真正盲态评测；不能以37条RED排除全部错误。

## 7. C7｜真实非回归与复现

| 历史验收 | 本轮实际重跑 |
|---|---:|
| U2-A | 46/46 |
| U2-B | 49/49 |
| U3-A | 34/34 |
| D0 pinned runtime | 12/12；770共享对象精确逆向 |
| 合计 | 141/141 |
| U2-C新增集成 | 56/56 |

历史测试输出到新回归目录，原报告文件不变；无新增独立参考资格。标准Schema/对象回放及额外OFF源解析不混入测试项分母。

Mac根目录复现（使用新的输出名称；旧冻结文件保持不变；本地有相同源快照、Conda及D0固定runtime）：

```sh
/Users/zhangcd/miniconda3/bin/python -B src/u2c/runtime.py --root . freeze --profile configs/udf/u2c/HistoricalBaselineProfile_v0.1.json --manifest runs/B1/U2-C/manifest_002.json
/Users/zhangcd/miniconda3/bin/python -B src/u2c/runtime.py --root . execute --manifest runs/B1/U2-C/manifest_002.json --out runs/B1/U2-C/real_002
/Users/zhangcd/miniconda3/bin/python -B src/u2c/runtime.py --root . verify --manifest runs/B1/U2-C/manifest_002.json --run runs/B1/U2-C/real_002
```

正式复核基线为 manifest_001 + real_001 + regression_001 + validation_001。可用 tests/u2c/regression.py 与 test_u2c_integration.py 按其CLI参数重复执行到新的目录（followup hash、44条旧source-only队列与新回归报告由显式参数给出）。GitHub仅归档代码、合同、策略、公开聚合报告及准入记录；本地私有投影约581MB及原始数据、原始API快照、完整文件manifest、逐行质量/审核对象不上传。Mac空间约49GiB，未额外复制媒体。

## 8. 验收门及后续

C2、C4和C7限定范围通过；C1安全语义已加固，OFF真实异单位判别仍HOLD；C3已实现开发级强制入口，未来生产消费者尚未激活；C5已拆分本轮策略与manifest，新增原生parser仍待实施；C6分区和阻断通过，法律授权未完成。B0/B1全局与U3冻结仍HOLD，独立科学测量/正式MappingRelease/研究release均0。

后续U3-B可在新开发准入合同下开展，保留Gemini44条冻结审核包；18个新增RED来源和高分AMBER分层另设开发审核增量，不影响独立判断。尚不能进入B3正式营养计算/参考或实验发布。上游Master不改动。

## 9. 审计工件

- [真实执行报告](../../runs/B1/U2-C/real_001/U2CExecutionReport.json)
- [只读回放报告](../../runs/B1/U2-C/validation_001/ReadOnlyReplayReport.json)
- [集成验收56项](../../runs/B1/U2-C/validation_001/U2CIntegrationReport.json)
- [OFF真实补样报告](../../runs/B1/U2-C/validation_001/OFFFollowupReport.json)
- [风险复筛报告](../../runs/B1/U2-C/validation_001/ReviewRiskAudit.json)
- [历史非回归](../../runs/B1/U2-C/regression_001/HistoricalRegressionReport.json)
- [统一合同](../../schemas/udf/u2c/UDF_U2C_UnifiedContract_v0.1.schema.json)
- [准入记录](../../runs/B1/U2-C/U2CAdmissionReceipt.json)
