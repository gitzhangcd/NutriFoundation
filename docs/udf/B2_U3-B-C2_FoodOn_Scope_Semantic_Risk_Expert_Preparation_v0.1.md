---
title: "B2 / U3-B-C2 | FoodOn Scope Qualification, Semantic Risk Remediation & Expert Adjudication Preparation"
version: "0.1"
date: 2026-11-27
authority: "AI Nutri Unified Data Foundation v2.1"
baseline: "PR61 / d95d9dea810efc1dd80576669f195f765a8e77ff"
status: "BOUNDED_DEVELOPMENT_REMEDIATION / EXPERT_AND_SCIENTIFIC_RELEASE_HOLD"
---

# U3-B-C2｜本体范围、语义风险与专家仲裁准备

## 0. 范围与裁定

依据 UDF v2.1 §§15–17、PR61 的真实 C1 分歧与风险记录，执行版本化开发加固。历史 U2-C、U3-A、U3-B、C0/C1 结果不原地修改；新阶段保持 CURATION_DEV，不批准等价、物理实例、营养值迁移、训练、正式独立参考或 MappingRelease。实际执行为 real_001，额外专家任务准备 expert_packet_001，受限工程审计切片 audit_slice_001。最终验收证据以独立路径中的 C2ValidationReport 和 C2AdmissionReceipt 为准。

## 1. 本体范围：不是把所有FoodOn类当成食品

实际重新解析 FoodOn 2026-09-20 OWL 40,107个命名类，其中39,707有标签。精确恢复旧显式根闭包12,375（按活跃、FoodOn IRI及标签过滤后12,362）。引入命名等价关系和顶层命名交集必要条件，5,290条补充图边；根闭包12,376、活跃12,363。没有把union成员、存在限制的filler当作父类，没有执行完整OWL reasoner。所有准入候选带可复算的子类路径证据；非本体推理完整性声明。

| 新状态 | 类数 |
|---|---:|
| CORE_RETAINED_DEV | 12,252 |
| EXTENSION_TYPED_RETRIEVAL_ONLY | 1,174 |
| HOLD_EXCLUSION_BRANCH_OVERLAP | 110 |
| HOLD_NONFOOD_OR_NONIDENTITY_ROLE | 3,086 |
| HOLD_SCOPE_UNRESOLVED | 12,062 |
| HOLD_NON_FOODON_OR_UNLABELED_OR_DEPRECATED | 11,423 |
| 合计 | 40,107 |

110个旧核心类重叠于保守排除分支（按分支非互斥计数：organism 103，food additive 6，chemical food component 6，animal feed 1）；并非断言这些类不能作为食品概念，仅不在新直接核心准入。保留原12,362类历史成员身份。七类候选通道为加工食品、餐食、脂质成分、零售肉切块、禽蛋、蛋类物质、FoodEx2复合菜分类；不可混同。C1原6个遗漏类全部被分角色覆盖，9个真实负例根/类均HOLD。不得全量纳入food material的8,566个额外分支或将跨角色候选提升为等价。新增1174类仅是候选检索范围。

## 2. 多维风险决定及真实重评估

源/目标语义特征保留原生grain、基础食品词项、明确状态、加工、组成/限定词、部件/整体等。词项是有限规则提取的mention，不是物种或配方真值。明确相斥状态与单边缺少条件分开；不把未知当作冲突。优先开发审核要求可观察的身份锚点、无现存显式冲突、角色和条件没有未解决标记。对不满足条件的候选保留CURATION_DEV导航/证据池，拒绝进入优先审核名单。该严格门槛是本阶段的保守开发设计选择，不是最终科学阈值。不存在正式等价判定。

实际重新执行U2-C全量只读回放253,249对象，实际准入视图6,718。复筛原C1 44案的355条旧边、U3-B 284查询的29,081条边。新增1174类使用相同固定量化E5本地模型、原名及上下文查询两种形式、每形式Top12并集；原284和C1已暴露44案独立分组，不修改两份原生成器队列，不混排历史和本次量化分数。额外产生6,274条候选，C1的7个词表外来源—目标边中有5个出现在新通道Top-K池；这是已暴露开发检索结果，不是独立召回率。原44中未找到候选的查询仍以原始分母保留；所有新通道候选仍角色/范围HOLD或显式阻断。

| 队列 | 查询 | 池边 | 满足开发候选条件 | 优先边 | 有优先候选查询 | 暂不映射查询 |
|---|---:|---:|---:|---:|---:|---:|
| U3A_EXPOSED_44 | 44 | 355 | 11 | 11 | 8 | 36 |
| U3B_FROZEN_284 | 284 | 29,081 | 153 | 67 | 34 | 250 |
| C2_EXTENSION_C1_44 | 44 | 589 | 0 | 0 | 0 | 44 |
| C2_EXTENSION_U3B_284 | 284 | 5,685 | 0 | 0 | 0 | 284 |

U3-B旧池29,081条：明确冲突阻断568，角色/范围HOLD22,743，缺条件HOLD3,131，无可观察锚点HOLD2,486，开发审核候选153。角色/范围HOLD中22,671条涉及不同原生grain；153条可审核边全部FoodOn，FDC/FNDDS无直接优先边。这一明显保守性可能错失有价值的条件/层级关联，下一步需按任务定义grain兼容矩阵、专家证据及独立评价，不能用拒绝比例作为精度。新通道全部不具直接优先审核资格是设计限制，不是失败的食品本体覆盖。查询ABSTAIN仅指所检索池中未发现符合当前门槛的候选，不证明标准不存在目标。

C1的23条Critic困难负例重合边中，4 RED继续明确阻断，19 AMBER转HOLD角色或范围；18/19还有配方、状态、物种或部件等具体附加风险标记，1条只被grain门拦截（菜肴形态区分仍不充分）。Critic意见不是专家确认错误；不把全部19条直接标RED。新增候选均保留原来风险、版本、来源与依赖，无任何正式科学迁移。

## 3. 专家审核准备

36个优先案例全部建立源优先任务，逐一绑定源原生定位、11份源文件hash和4份外部标准。先独立重建来源概念及目标，冻结初始答复后才可经授权看模型分歧。重点证据每案最多4张，共130张；另外186项证据按需访问（31案有额外）。专业角色按食品本体/食品科学、营养成分测量、地域菜谱等分配，不默认PI或模型具备全部资格。

新增严格 INITIAL_SOURCE_FIRST 与 POST_INITIAL_COMPARISON 答复JSON Schema，8/8合成结构例通过（非真实专家）。任务身份、原始证据、目标ID、资格证明、初始冻结hash、显式解盲需由控制端运行时核验，Schema不能自动核实这些科学资格。未部署Workbench或OS级行访问控制；源优先和比较包物理分离只是治理机制。实际专家分配0、答复0、专家参考0。

## 4. 运行合同、验收与审计

主运行输出76,509个真实来源驱动的类型化开发对象：40,107 ScopeAssessment、35,710 SemanticRiskAssessment、656 QueryAdmissionDecision、36 ExpertTaskDraft。19许可域物理分区、标准 Draft 2020-12 Schema、70个输入文件hash前后一致。新合同是统一Envelope的版本化扩展，不原地修改历史42类和U3-B三类。完整私有数据保留Mac（约220 MB），GitHub只归档规范、代码、配置和聚合报告。

最终完整重放、真实用途门禁及反例测试以 validation_001/C2ValidationReport.json 为准。此为同实现重放及真实准入测试，不是独立科学有效性。C2ScopeAssessment的witness与有限规则均需独立工程Critic检验；未获得专业科学裁定。

为Gemini的后续工程审计准备355条已解盲C1边与125个FoodOn范围探针切片，含原23负例、110旧核心交叉分支、6遗漏类、9负例探针。不给新44独立语义审核的源/候选或任何新Critic结果；此次审计仅工程符合性，Gemini将不再被视为本实现完全未暴露的确认性评审。全量新池由控制端验收，独立审计覆盖范围需诚实限定。

## 5. 复现与阶段边界

Mac NutriOne根目录，使用固定模型/原始文件及Conda环境，新的不可变运行目录：
```sh
/Users/zhangcd/miniconda3/bin/python -B src/u3c2/run_c2.py --root . --profile configs/udf/u3c2/C2_ExecutionProfile_v0.1.json --out runs/B2/U3-B/C2/real_002
/Users/zhangcd/miniconda3/bin/python -B tests/u3c2/verify_c2.py --root . --profile configs/udf/u3c2/C2_ExecutionProfile_v0.1.json --run runs/B2/U3-B/C2/real_002 --out runs/B2/U3-B/C2/validation_002
```
专家任务及审计切片脚本仅写新目录，不触碰历史冻结。当前不进入C3正式科学映射、B3营养计算；需工程审计、独立专业裁定、预注册的确认性目标及阈值。开发队列不构成Gold。完整OWL推理、角色兼容与条件性关系、许可和任务级科学资格仍HOLD。

## 6. 交付物

- [执行报告](../../runs/B2/U3-B/C2/real_001/C2ExecutionReport.json)
- [合同](../../runs/B2/U3-B/C2/real_001/C2_Contract.schema.json)
- [专家准备](../../runs/B2/U3-B/C2/expert_packet_001/ExpertPacketPreparationReport.json)
- [专家执行协议](U3B_C2_Expert_Adjudication_Protocol_v0.1.md)
- [专家答复合同](../../schemas/udf/u3c2/ExpertAdjudicationResponse_v0.1.schema.json)
- [独立审计切片报告](../../runs/B2/U3-B/C2/audit_slice_001/AuditSlicePreparationReport.json)
- [验收报告](../../runs/B2/U3-B/C2/validation_001/C2ValidationReport.json)
- [准入记录](../../runs/B2/U3-B/C2/C2AdmissionReceipt.json)
