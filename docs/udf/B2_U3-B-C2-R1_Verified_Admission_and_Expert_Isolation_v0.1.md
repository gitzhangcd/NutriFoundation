---
title: "B2 / U3-B-C2-R1 | Verified Admission, Residual-Aware Semantic Routing & Expert Isolation Hardening"
version: "0.1"
date: 2026-11-27
authority: "AI Nutri Unified Data Foundation v2.1"
baseline: "PR62 / f79d29dc200d59c1e40f4d97a834696c3bdc68be"
status: "BOUNDED_DEVELOPMENT_HARDENING / MAPPING_QUALIFICATION_HOLD"
---

# C2-R1｜独立审计核验及版本化整改

## 0. 范围

PI确认 C2-A1 审计冻结并要求继续执行。实际复核 23/23 允许输入、3/3 成果文件和12项发现，冻结收据SHA256 50ab06764a5eb653a2574e55928f14bddb8ee64812b4ae93882c400f71a76b54；5 RED、6 AMBER、1 INFO。审计声称10项REPRODUCED、1项STATIC_ONLY、1项REPORTED_NOT_INDEPENDENTLY_VERIFIED。C2原件、原批次、原代码、Critic冻结与新44独立队列均不改变。仅授权开发整改，不授权科学映射、训练、正式Gold或B3营养计算。审计声明未读禁止项，但没有独立系统日志证明强隔离。

## 1. 审计项裁定与整改

| ID | 发现 | R1处理 |
|---|---|---|
| F-C2-001 | 伪造0步自指witness可通过旧validate | 新入口重新解析固定OWL与策略，40,107原范围对象逐字段重算含真实路径与排除状态；新范围overlay只能通过精确重算 |
| F-C2-002 | 重封RED伪造资格；旧测试门信任调用字典；shortlist依赖不完整 | src/u3c2r/runtime_v2.py的VerifiedGate由控制端预先信任的配置hash与冻结receipt hash启动，加载实际对象全量重算；重封错误对象拒绝，短名单由真实池推导并绑定依赖 |
| F-C2-003 | ExpertTaskDraft角色依赖Critic字段 | 重建36案，均使用统一角色集合，移除所有逐案Critic角色/优先信号；旧36案营养角色实际一致，代码依赖仍需整改；样本成员本身仍为风险富集开发样本 |
| F-C2-004 | 5/11旧准入边存在语义错配或未声明特化 | 5/5退出优先名单；不把剩余者当成真值 |
| F-C2-005 | 中文单字、否定、来源状态、英文特化词 | 完整标签或有限明确登记的完整双语短语才提供开发审核锚点；区别现态/原料来源/否定；未解析剩余条件HOLD；对抗例回归 |
| F-C2-006 | 同名任意跨粒度豁免 | 明确配置角色兼容矩阵，未登记不允许；登记跨角色只进入条件性关系审核，不是直接等价 |
| F-C2-007 | 专家结构和运行时缺口 | v0.2响应schema补条件；独立expert_gate_v2.py检查索引、源/目标版本与locator、任务/实际授权指纹；未获得真实资格及解盲包，实际派发仍HOLD |
| F-C2-008 | organism分支误挡可食对象；负例只验证前缀 | 103个重叠类转DUAL_ROLE_ORGANISM_REVIEW_ONLY，7个其他重叠继续HOLD；6个真实FOODON前缀排除探针，其他候选范围尚待资格化 |
| F-C2-009 | 高拒绝率来自粗粒度门而非完整语义 | R1用保守完整表面证据隔离错误；新实测284/284暂不映射，不能视为可用语义覆盖或精度提升。下一工作要验证条件关系与独立候选质量，不能机械扩充白名单 |
| F-C2-010 | RDF/XML版本变化静默漏公理 | 解析前检查非支持类声明、交集序列化、多标签/语言；205个匿名复杂交集成员明确不推导；未运行完整reasoner |
| F-C2-011 | 同目录隔离和全量独立验证范围 | 新专家A/B分目录0700及文件0600；不是同账号访问隔离，禁止实际分派直到控制端取得独立隔离证据。Gemini仍只审原355边/125探针，不独立验证284新池 |
| F-C2-012 | 暴露/范围治理 | 完整保留，工程审计不构成独立科学Gold |

## 2. R1实际完整重算

本轮不重新运行E5，也不扩大冻结检索池。输入是C2已冻结35,710条边（355原44 + 29,081新284 + 6,274扩展）、65,592个U2-C版本化原生端点、46,160个历史候选（17,079 + 29,081，作为引用解析范围，不称全部重评估），40,107范围对象与656个查询决定。复核128份输入指纹，旧scope payload与固定OWL及策略精确相等，原生source/target refs与原生成器身份一致；FoodOn边必须关联其精确scope assessment。重新生成76,473个类型化overlay（40,107范围+35,710风险+656查询），19许可域。保留旧版本引用、依赖、数据用途及HOLD。另独立生成36个专家任务，不混入76,473分母。

| 队列 | 查询 | 保留候选池 | R1优先审核边 | 有优先审核查询 | 暂不映射 |
|---|---:|---:|---:|---:|---:|
| 原44 | 44 | 355 | 7 | 7 | 37 |
| U3B 284 | 284 | 29,081 | 0 | 0 | 284 |
| 扩展原44 | 44 | 589 | 0 | 0 | 44 |
| 扩展284 | 284 | 5,685 | 0 | 0 | 284 |

原44的11条旧放行中6条仍可审核，5条错配/未声明特化退出；新增一条FNDDS条件审核边。7条优先边仅开发：2条FoodOn完整表面证据、4条FoodOn跨角色条件审核、1条FNDDS条件审核。23条旧Critic负例重合边全部未进入优先名单；4条明确状态阻断，19条未解/不兼容HOLD（17/2）。不宣称Critic负例已经专家证实。原先历史RED仍保守隔离；新版分开记录直接显式矛盾和上游RED未复核，因此显式阻断数不可与旧RED机械比较。

**重要负结果：U3B的34个原开发审核查询降为0。** 全标签规则有意 fail-closed、不是生产级中文/英文语义匹配。没有科学准确率或召回率证明；当前候选仍可导航审查，但不能把拒绝比例当科学进步。待以独立开发队列的实际目标和关系审核区分“目标不存在、候选缺失、条件不明、规则过保守”；之后冻结独立确认集、预先规定任务资格及precision-coverage目标。不要继续仅在已暴露44案上调规则，也不要用Gemini的工程自审作为科学Gold。

## 3. 运行时可信边界

新运行时构造只接受控制端可信的配置及冻结receipt SHA256，重新解析实际冻结manifest、对象哈希、原端点、角色和scope、风险决定及查询短名单。通过完整重放才开放CURATION_INSPECT和DEVELOPMENT_CONCEPT_REVIEW；任一科学用途默认HOLD。禁止以任意调用者提供的“verified records”字典作为资格来源。可信hash必须由独立受控渠道提供，不能由未经授权调用者自行生成当作信任根；本地Python不是OS安全沙箱，未来B3/U5等实际消费者仍需在入口接入，历史C2脚本仅限历史回放，不再作为当前资格入口。

## 4. 专家任务与授权

36源优先任务、11实际源文件和4标准原件均核验，统一角色集合，不使用Critic判断生成角色；130证据卡及186附加项移入控制端专用比较包。新任务编号打散固定顺序，与原风险ID的链接只保存在控制端。源优先和比较包分别为reviewer_source_only、controller_restricted，目录0700、文件0600，只减少误读，不能阻止同系统账号访问。实际隔离未证实、审查者资格注册0、分派0、实际答复0、独立参考0。禁止使用共享WebCodex工作区直接派给真实盲态评审者；须独立账号/最小源投影导出/Workbench访问控制及真实资格证据后授权。旧样本是风险富集开发样本，不能声称独立确认。

专家v0.2 schema和expert_gate_v2.py支持源明确/未知条件、候选非空、条件关系条件非空、证据索引、原生目标ID/版本/标签/定位校验、控制端预先批准的可信授权bundle。Phase B绑定初始真实冻结、task、reviewer、comparison hash及明确解盲授权后才读取比较包。控制端需真实核验资格及访问隔离；不提供伪造授权示例作为实际资格。证据指纹/原生定位核验不能代替专家对证据解释的科学裁定。旧C2 schema保留历史用途。

## 5. 验收及后续

真实主运行 `real_001` 及专家包 `expert_packet_001` 已完成。最终只读验证、实际gate请求和新增回归以 `validation_001/R1ValidationReport.json` 为准；独立审计复核仅限其实际授权切片。未完成ACL、独立科学参考、正式MappingRelease，均HOLD。下一步应先验证两处准入漏洞修复和实际反例，工程审计可限时复查；不要把工程迭代变成无限循环。另由未接触新候选结果的评审者开展新44分层开发审核（原风险25/新模型19分开），优先建立可支持条件关系的结构及任务级判断；本轮Gemini已有实现暴露，不再充当确认性未暴露评审者。独立专家初始及比较任务需实际隔离与资格授权。

## 6. 工件

- `configs/udf/u3c2r/R1_ExecutionProfile_v0.1.json`
- `configs/udf/u3c2r/R1_Policy_v0.1.json`
- `src/u3c2r/runtime_v2.py` / `risk_v2.py` / `scope_v2.py`
- `src/u3c2r/prepare_expert_v2.py` / `expert_gate_v2.py`
- [R1执行报告](../../runs/B2/U3-B/C2/R1/real_001/R1ExecutionReport.json)
- [R1执行冻结](../../runs/B2/U3-B/C2/R1/real_001/R1ExecutionFreezeReceipt.json)
- [R1验收](../../runs/B2/U3-B/C2/R1/validation_001/R1ValidationReport.json)
- [专家准备](../../runs/B2/U3-B/C2/R1/expert_packet_001/ExpertPacketR1Report.json)
- [专家响应v0.2合同](../../schemas/udf/u3c2r/ExpertAdjudicationResponse_v0.2.schema.json)

原始Critic文件、逐行数据、源优先/比较包及私有语义overlay仅留Mac。
