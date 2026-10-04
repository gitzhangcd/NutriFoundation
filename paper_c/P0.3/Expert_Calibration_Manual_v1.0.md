# Paper C P0.3｜专家校准操作手册 v1.0

## 1. 你在做什么

你不是在回答患者问题，也不是在评价 AI。你的任务是：仅依据当前给定的科学来源，把来源中可以被科学验证的证据对象结构化出来。

校准阶段使用的全部来源都 **不属于 Gold100**，并且与 Gold100 不共享 StudyIdentityCluster。

## 2. 两轮校准

### Round A｜Calibration12A

两位专家先完全独立完成 12 个来源并分别锁定。只有 A/B 都锁定之后，系统才允许显示差异。随后可以讨论差异、发现 codebook 歧义、修改手册或 workbench。Round A 的一致性统计只用于诊断，不是最终过门成绩。

### Round B｜Calibration12B

使用 Round A 后冻结的新版本手册和 workbench。两位专家重新独立完成 12 个从未讨论过的来源。A/B 都锁定以前不得交流答案；两份记录锁定后先计算 reliability，指标冻结后才能讨论。

## 3. 每个来源填写顺序

1. 核对来源身份、版本、worker-visible text hash 与 evidence cutoff。
2. 判断 StudyIdentity / companion / secondary dependency。
3. 列出一个或多个 EvidenceUnit；若来源不足，明确选择 insufficient_source，不要补外部知识。
4. 对每个 EvidenceUnit 填 Population、Intervention/Exposure、Comparator、Outcome。
5. 填 effect direction、effect measure、effect value、unit；数字必须来自原文。
6. 判断 claim type 与 causal level；观察性关联不得因为机制合理就升级成因果。
7. 对 guideline/consensus 填 recommendation status、条件、例外和限制。
8. 完成 source-level applicability boundary。
9. 给关键对象绑定原文 evidence span。
10. 枚举 8 类 critical-error opportunities；是否存在 opportunity 不能参考任何模型表现。
11. 填 uncertainty / protocol ambiguity。
12. 完成独立性、COI 声明并锁定 first-pass。

## 4. Evidence span

不要只复制一句看起来相关的话。span 必须直接支持对应科学对象，并保留会改变意义的限定词、否定词、时间点、亚组和例外。Workbench 会把 span 绑定到固定 token index；不要用自己重新排版的文本。

## 5. 数字

优先复制 source-reported value、measure 和 unit。不要自行计算新的效果量作为 Gold。格式可规范化，但科学数值不能改变。

## 6. 不确定时

如果来源本身没有足够信息，用 `insufficient_source`。如果来源有信息但手册不知道怎样表达，标记 `protocol_ambiguity`。这两者不能混淆。

## 7. Round A 可以讨论什么

只有双方 first-pass 都锁定后才能讨论。讨论目的是识别：scientific disagreement、source ambiguity、codebook ambiguity 或 workbench defect。讨论后只能发布新版本规则，不能改写已经锁定的 first-pass。

## 8. Round B 禁止事项

Round B 指标冻结前，不得：看对方答案、讨论个案、让第三方给答案、查看任何 AB0–AB6 输出、查看 evaluator score、修改 manual/workbench 语义规则。

## 9. Round B 通过标准

- Critical categorical Gwet AC1 ≥ 0.80
- Ordinal weighted agreement ≥ 0.80
- Numeric exact/predeclared-tolerance agreement ≥ 0.95
- Source-span token F1 ≥ 0.85

此外必须没有交叉可见、Gold100 越权访问、未解决的阻断性 workbench 缺陷或影响评分的 protocol ambiguity。

## 10. 如果 Round B 没通过

不会进入 Gold100。Round B 的 12 个来源从此视为已经暴露的 calibration material；修订规则后必须从剩余 non-Gold100 来源重新抽一组新的 blinded validation set，不能在同一 12 篇上反复练到通过。