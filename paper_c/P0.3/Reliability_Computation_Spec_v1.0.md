# P0.3 Reliability Computation Specification v1.0

## 1. Freeze timing

本规范在任何 Calibration12B 专家标注产生之前冻结。阈值继承 P0.1，不根据观察到的一致性结果调整。

## 2. Primary analysis population

仅使用 Calibration12B 中 Annotator A 与 B 均已 `FIRST_PASS_LOCKED` 的 pre-adjudication paired records。Adjudicated values 不进入 reliability 计算。

## 3. Critical categorical Gwet AC1

对 Reliability Gate Contract 中预先列出的每个 critical categorical field 分别计算 Gwet AC1。

对某字段，设共有 $N$ 个 applicable paired decisions、预定义类别数为 $q\ge2$，观察一致率为：

$$
P_a=\frac{1}{N}\sum_{i=1}^{N}I(A_i=B_i)
$$

令 $p_k$ 为两位 annotator 在类别 $k$ 上的合并边际比例：

$$
p_k=\frac{n_{Ak}+n_{Bk}}{2N}
$$

chance agreement：

$$
P_e=\frac{1}{q-1}\sum_{k=1}^{q}p_k(1-p_k)
$$

则：

$$
AC1=\frac{P_a-P_e}{1-P_e}
$$

Primary corpus-level categorical statistic 为各 estimable field 的 **applicable-decision-count weighted mean AC1**。同时报告每个字段 AC1 与 denominator。若没有任何 estimable field，则 gate 为 `NON_ESTIMABLE_BLOCK`。

通过标准：`weighted mean Gwet AC1 >= 0.80`。

## 4. Ordinal weighted agreement

P0.1 的 `ordinal weighted agreement` 在 P0.3 预先 operationalize 为 **linear weighted agreement**，不是事后选择某个 kappa 版本。

对于有 $K$ 个有序等级的 paired decision：

$$
w(a,b)=1-\frac{|a-b|}{K-1}
$$

primary ordinal statistic 为全部 applicable ordinal paired decisions 的平均 $w(a,b)$。

通过标准：`>=0.80`。

如论文需要，可额外报告 weighted kappa/AC2 作为 secondary sensitivity analysis，但不能替代 primary gate。

## 5. Numeric agreement

只比较 source-reported critical numeric results。先按 frozen normalization rule 标准化数字格式、effect measure 与 unit。

一对值计为 agreement，当且仅当：

- canonical values 完全相同；或
- 在 Round B 前已经在 contract 中为该 measure 明确声明 tolerance，且差异处于 tolerance 内。

Primary numeric agreement：

$$
Agreement_{num}=\frac{N_{agree}}{N_{applicable}}
$$

通过标准：`>=0.95`。

## 6. Source-span token F1

Evidence span 使用 frozen workbench tokenizer 的 stable token indices。对于同一 canonical scientific object / critical opportunity：

$$
Precision=\frac{|T_A\cap T_B|}{|T_A|}
$$

$$
Recall=\frac{|T_A\cap T_B|}{|T_B|}
$$

$$
F1=\frac{2PR}{P+R}
$$

若 A/B 均为空且该对象不 applicable，则不进入 denominator；若一方为空另一方非空，则 F1=0。

Primary span statistic 为 applicable object-level F1 的 macro mean。

通过标准：`>=0.85`。

## 7. Missing / non-estimable

`not_applicable` 不应被人为转成 agreement。每个 metric 必须同时报告 applicable denominator。任何 primary metric 无法估计时，P0.3 不可 PASS，应触发 calibration-design review；不得用其他指标替代。

## 8. Integrity gate

即使所有数值指标通过，只要发生以下任一项，P0.3 仍 FAIL/BLOCK：cross-annotator visibility、Gold100 unauthorized access、first-pass 非法修改、schema invalid、blocking workbench defect、或影响评分的 unresolved protocol ambiguity。

## 9. Freeze

Round B reliability output 必须先计算并 SHA-256 冻结，再开放 Round B discussion/adjudication。