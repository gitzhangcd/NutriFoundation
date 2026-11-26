---
title: "B2 / U3-B-C2-R2 | Independent Semantic Calibration, Conditional Alignment & Coverage Recovery"
version: "0.1"
date: 2026-11-27
authority: "AI Nutri Unified Data Foundation v2.1 §§15–21"
baseline: "PR63 / 5e43df1fe57ff934a0452fc3c0de4f19e44973b0"
status: "PASS_R2_P0_DEVELOPMENT_COMPARATORS_AND_REVIEW_PREPARATION / INDEPENDENT_REFERENCE_AND_SCIENTIFIC_QUALIFICATION_HOLD"
---

# R2｜独立语义校准与条件关联开发

## 0. 裁定

R1-A2冻结核验：32/32输入及3/3成果指纹一致，原5个RED核心反例被阻断；本轮独立复核发现3 AMBER（2 REPRODUCED、1 REPORTED_NOT_INDEPENDENTLY_VERIFIED），新增RED 0。冻结收据SHA256 2adced36623b690b1ba60b125da8bb4f494123049f650aa3be3937dc6025a67d。访问边界为评审声明，不能证明ACL。Gemini仅独立复核355条已暴露边和129本体探针，不独立背书R1全量回放。

本轮完成R2-P0冻结开发对照和独立审核准备，未获得新独立参考。R1的正式应用入口保持不变；不以候选问题绕过R1开发概念准入。科学映射、B3计算、训练和正式release均HOLD。R2完整科学校准尚未完成。

## 1. 残余审计问题处理

- R1-F-001：米饭/cooked rice及炒饭/fried rice作为完整双语短语的**待验证隐含熟制状态问题**，不把推断写成原文明确状态。实际本轮34,766条池中未命中这两对，合成回归探针通过。恢复去皮/带皮显式相斥检查，区分原料来源与当前状态。实测67条相关边：61条在旧原始池中已为上游RED，6条在扩展池新触发去皮状态冲突。不是67条新错误。保留所有历史RED与R1明确冲突。
- R1-F-002：专家v0.3草案拒绝HOLD_INSUFFICIENT_EVIDENCE+EXACT与REJECT_AS_EQUIVALENCE+EXACT。结构反例测试通过，未激活专家运行时；Phase B逐边证据绑定、真实资格授权、Workbench权限隔离继续HOLD，移交EA-P0验收。36专家任务不分派。
- R1-F-003：284/284 R1 abstention仍为科学覆盖HOLD。下一步改用独立参考对照，不能以安全拒绝当科学准确率；不继续在原44案上调规则。

## 2. 真实开发比较及冻结范围

固定原284个中文查询，原三个目标域的28,845记录及29,081持久化边，加FoodOn 1,174类扩展域对应5,685边。原C1已暴露44案的355边和589扩展边不进入R2比较池。101份输入指纹锁定，包含原始生成器、R1与审计收据，实际U2-C 65,592个native端点用于恢复身份。未执行新Embedding推理或训练。

生成34,766条R2CandidateQuestion开发记录，保留实际R1风险ref、原生source/target、目标版本、粒度、完整标签证据、未解决条件、去皮状态、原RED、原始rank及rights domains。R2候选关系全部UNRESOLVED，permitted_purpose=CURATION_INSPECT_ONLY，development_concept_review_authorized=false、accepted_equivalence=false、measurement_transfer和mapping_release均HOLD；非科学对象正式释放。对照组为284×4目标域×4方法=4,544组：LABEL（原名）、CONTEXT（上下文）、FUSION（原排序；扩展域RRF固定规则）、TYPED_QUESTION（隔离明确冲突、原RED、范围HOLD和未登记粒度对，完整标签/双语短语证据优先，其余只提出条件问题）。k=1,3,5,12，按域独立排序，不直接混排原模型分数和扩展推理分数。

| Top-3 | 原3域边数 | 明确或原RED边 | 扩展域边数 | 明确或原RED边 |
|---|---:|---:|---:|---:|
| LABEL | 2556 | 30 | 852 | 3 |
| CONTEXT | 2556 | 80 | 852 | 5 |
| FUSION | 2556 | 62 | 852 | 6 |
| TYPED_QUESTION | 2556 | 0 | 852 | 0 |

原池28,496条、扩展5,665条为QUESTION_ONLY（34,161条）；588条明确/原RED、17条范围HOLD，共605条不进入问题优先排序。保留全部开发证据。四方法原域852组和扩展284组均有Top-3候选。这是规则筛查和候选问题覆盖，不是相关性、正确率或语义召回。R1仍0/284开发概念审核资格；不授予任何新的准入。没有独立数据支持条件关系的正确性，禁止把问询候选当关系断言。

## 3. 两个分离的参考批次

先冻结源选择规则和四种排序方法，再发出独立评审。保留U3-B原新44案队列不变，源优先投影核对原生身份与锚点、真实原生别名及已有参考配方名称。44案中19有现行模型候选，25只对应旧U2-C风险候选，分开比较。与C0已暴露44案零重叠。

为避免仅19案的新方法参考不足，另外从284中排除原两个队列，按cohort×source_scope、固定salt和稳定对象ID哈希顺序选择32个未被旧审核抽中的开发样本，选取在读取候选分数前完成，不使用风险分数或标签选样。四层分别抽8案（候选分母41新菜肴、41新食材、59配对菜肴、124配对食材，共265）。32案单独冻结、第一轮不提供。先审核44，完成开发比较和方法调整冻结后再打开32，用于开发泛化检验，不作为确认性Gold。报告分层分母，不假设总体代表性或食品频率权重。样本两批合计76唯一源。

R2第一批审核配置 B2_U3R2_REF44_Gemini_001.json 限定7份输入：源优先44、精确答复Schema、总规范、4份固定公开标准；第二批、所有候选和生成器实现/结果禁止访问。此前Gemini已阅读方法代码，因此本轮即便新会话也仅为开发独立参考，不能声称确认性盲态。实际是否隔离由访问声明与后续治理区分。评审者不得读取控制端比较数据或上传私有源数据至未授权服务。

## 4. 校准测量合同

R2ReferenceReview v0.1要求8维来源语义、证据状态和索引、三标准检索过程、最多3个正向候选和3个困难负例/标准、固定ID版本和真实locator、关系方向、条件、未解决原因及实际耗时。保留未找到目标或证据不足；可以提出本地概念扩展需求，不自动建立正式概念。

控制端 compare_reference.py 在新的PI解盲授权后，核对任务/冻结文件/允许输入、44唯一来源身份及真实标准原件的目标ID、版本、主标签、原生locator、证据索引及source/target证据绑定。源优先判断仅为Critic草稿，不能替代专家。比较按当前模型19与旧25、原域/扩展域分开，统计reference-hit@k（在冻结目标宇宙中有独立评审提出的可支持目标之查询，至少一个目标在相应Top-k中）和困难负例重合，不把未列出边当作错误。

分开处理：目标在冻结宇宙之外、宇宙内但未检索到、检索到但未进特定方法Top-k、无当前模型查询、评审未找到/源证据不足。参考候选可能不完整，reference-hit并非真实召回率。真正Precision–Coverage需要独立的逐边关系与用途裁定，并冻结独立确认样本、阈值、误配容忍度及置信界；此阶段没有参考，禁止计算科学精度/召回。开发结果仅用于后续策略选择，独立专家和EA-P0门禁仍未通过。

## 5. 复现及实际验收

真实本地R2 real_001完成，约71.92 MB私有结果留Mac。实际只读重算validation_001：34,766/34,766候选、4,544/4,544排序组、76/76源优先任务、101输入指纹一致，33/33测试。首次验证对Python tuple与JSON list直接比较失败，修复成规范JSON比较后重跑通过；冻结原件未改动。测试含实际原生目标定位检查、非法证据索引、虚构ID、未知分母、候选升级/释放拦截、专家结构反例；测试为合成/真实端点结合，不产生任何专家结论。所有真实独立R2审核、专业专家答复和释放数0。

复现（新目录，原输入保持固定hash）：
```sh
P=configs/udf/u3r2/R2_DevelopmentProtocol_v0.1.json
/Users/zhangcd/miniconda3/bin/python -B src/u3r2/run_r2.py --root . --profile "$P" --profile-sha 79a7630684afbde2695301e50bd5018cbb41812c944f3e6c41e84eee2b25aaad --out runs/B2/U3-B/C2/R2/real_002
```
使用新运行freeze receipt的SHA256及实际新输出路径运行tests/u3r2/verify_r2.py。禁止原地覆盖。源优先审核44与保留32、私有候选、比较索引、完整文件fence和目标ID集合不上传GitHub，仅归档代码、Schema、配置、聚合报告和指纹。

## 6. 下一步

- R2-P1：独立44源优先审查、冻结收据核验、明确授权后进行真实比较；只用19个当前模型查询比较四方法，另25用于原风险复查。
- R2-P2：基于开发参考进行任务条件/关系候选优化，冻结方法后再启用32保留样本。仍需独立专业逐边验证，不允许把两批当确认性Gold。
- EA-P0：按PI已沟通的现有Workbench集成方案，先设计页面及权限/源资料操作路径给PI确认，再完成专业资格、真实源投影、Phase A冻结、Phase B逐边证据及访问隔离测试。
- C3/B3：仍HOLD。

工件：[R2执行报告](../../runs/B2/U3-B/C2/R2/real_001/R2ExecutionReport.json)、[回放报告](../../runs/B2/U3-B/C2/R2/validation_001/R2ValidationReport.json)、[生成器冻结](../../runs/B2/U3-B/C2/R2/real_001/R2GeneratorFreezeReceipt.json)、[阶段准入](../../runs/B2/U3-B/C2/R2/R2AdmissionReceipt.json)、[独立审核配置](../../configs/audit/tasks/B2_U3R2_REF44_Gemini_001.json)。
