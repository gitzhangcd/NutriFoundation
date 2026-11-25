---
title: "B0 / U1-A — NutriData Real Asset Inventory, Native Schema Profiling & Grounding Feasibility Audit"
version: "0.1"
date: 2026-11-25
status: "PARTIAL_PASS_NUTRIDATA_PROFILE_ONLY / B0_OPEN"
authority: "AI Nutri Unified Data Foundation v2.1"
master_git_blob: "9e3169814f8800e1b6eba6fd94a4097c57a00488"
run_id: "NutriData_real_001"
---

# B0 / U1-A｜NutriData 真实数据画像与关联可行性审计 v0.1

## 0. 实际执行结论

本轮依据 [UDF v2.1](../AI_Nutri_Unified_Data_Foundation_v2.1.md) §13、§18、§34、物理合同规则与 B0 执行合同，真实扫描本地可访问的 NutriData 工作簿；不增加宏观规范。**G023 原生结构画像通过，整体 B0 尚未通过。** 22 个其他公开数据源是用户报告已下载，但未在本次授权项目目录定位，不推定缺失、损坏或已完成审计。

- 25 个 XLSX、25 张工作表、94,667 条非空原生数据行（不含表头）；37,478,213 字节。
- 25/25 ZIP CRC 检查通过，25/25 原始文件扫描前后 SHA-256 一致；无读取异常。表头均为首行，无重复表头、显式空数据行或超出已识别表头的非空单元格。
- 两个原生 ID 列在每张表内均唯一且非空；跨子库 ID 命名空间未证明统一。
- 187,884 个可解析 JSON 对象、1,450 个空 JSON 单元格，0 个解析失败/非对象（总计 189,334 个预期 list/detail 单元格）。不是每个详情都存在。
- 菜肴与食物成分原生键可行性很高：152,324 / 152,531 条唯一连接且食品 code 一致（99.86%）。
- 未建立独立化学/摄入真值、营养计算有效性、正式 B1 物理冻结、研究资产 release 或实验结论。

## 1. 审计对象、分母、方法与边界

运行时点（UTC）：`2026-11-25T10:25:16.104344+00:00`。授权范围为 NutriOne 的 source_data 内既有 excel-Nutridata 工作簿（真实位置在本地私有文件清单中）。实际格式 XLSX，非此前口头描述 CSV。本次不把未扫描的 22 源、公开资料规模或合成 fixture 当成实际扫描结果。

采用 Python 标准库 OOXML ZIP/XML 原生读取；解析 shared strings、inline strings、原生 cell type、原生坐标和公式存在性；完整消费工作表 XML。首个非空行为表头，数据行定义为至少一个原生非空值的显式行；没有重新保存或重新计算工作簿。零与缺失候选 token 保留。键使用原生字符串精确比较，绝不将编号转为整数。JSON 严格拒绝重复对象键及非标准 NaN/Infinity。CRC 仅验证档案结构完整，不证明源下载完备或值正确。未复原 Excel 数值格式渲染、源数据库字典、历史版本及所有嵌套字段的深层 schema；对于数字格式所显示的前导零仍需专项检查。

程序：GitHub `scripts/udf/b0/profile_nutridata.py` 与 `profile_nutridata_core_links.py`；本地对应 `src/b0/`。主扫描脚本 SHA-256 `46f3bba99d8a90e74aaf138b7fe65cff0d97e9cd3745c999e37eb9649acb9eaa`；复核脚本 SHA-256 `80cee2a15e37da39da9328199563c56c198bb622cc66c2896936758ccc7d4512`。8 项基础 smoke assertions 与两个真实扫描进程 exit 0；未开展大规模 synthetic fixture suite。所有原始数据均留本地，不发布原始行或个人路径。

## 2. SourceRegistryDelta：现有资产登记

G023 为顶层 NutriData 来源集合，以下 25 子资产按实际文件序号登记。编号 06、25 未出现在本地文件名清单；不能据此推断原站缺库或下载缺失。供应商 release ID、字段字典、完整性边界和授权状态未确认。25 张表的原生记录并非 94,667 个独立食品、受试者或研究。其余 G001–G022 保留历史注册 ID、用户报告下载状态、实际目录和版本 UNRESOLVED（见 SourceRegistryDelta.json）。

| 子资产ID | 文件 | 原生表 | 行 | 列 | 非空详情对象/行 | 首期 |
|---|---|---|---:|---:|---:|---|
| NDF-G023-01 | 01-食物成分库 | nutridata_ingredient | 3,446 | 59 | 3446 / 3446 | CORE |
| NDF-G023-02 | 02-菜肴库 | nutridata_dish | 22,180 | 10 | 22180 / 22180 | CORE |
| NDF-G023-03 | 03-婴幼儿配方奶粉 | nutridata_baby_formula | 2,455 | 12 | 2455 / 2455 | Deferred |
| NDF-G023-04 | 04-特医食品 | nutridata_special_formula | 365 | 13 | 365 / 365 | Deferred |
| NDF-G023-05 | 05-营养素补充剂 | nutridata_supplement | 22,902 | 12 | 22902 / 22902 | Deferred |
| NDF-G023-07 | 07-GI食品库 | nutridata_gi_food | 6,840 | 17 | 6840 / 6840 | GI conditional |
| NDF-G023-08 | 08-保健食品 | nutridata_health_food | 29,383 | 13 | 29383 / 29383 | Deferred |
| NDF-G023-09 | 09-功能食品原料 | nutridata_functional_food | 533 | 81 | 533 / 533 | Deferred |
| NDF-G023-10 | 10-氨基酸库 | nutridata_amino_acid | 1,002 | 28 | 1002 / 1002 | Deferred |
| NDF-G023-11 | 11-脂肪酸库 | nutridata_fatty_acid | 1,100 | 52 | 1100 / 1100 | Deferred |
| NDF-G023-12 | 12-大豆异黄酮 | nutridata_isoflavone | 273 | 12 | 273 / 273 | Deferred |
| NDF-G023-13 | 13-植物甾醇 | nutridata_phytosterol | 91 | 15 | 91 / 91 | Deferred |
| NDF-G023-14 | 14-胡萝卜素 | nutridata_carotene | 91 | 13 | 91 / 91 | Deferred |
| NDF-G023-15 | 15-USDA胆碱 | nutridata_choline | 271 | 15 | 271 / 271 | Deferred |
| NDF-G023-16 | 16-类黄酮 | nutridata_flavonoid | 275 | 13 | 275 / 275 | Deferred |
| NDF-G023-17 | 17-花青素 | nutridata_anthocyanin | 141 | 11 | 141 / 141 | Deferred |
| NDF-G023-18 | 18-白藜芦醇 | nutridata_resveratrol | 204 | 10 | 204 / 204 | Deferred |
| NDF-G023-19 | 19-叶黄素 | nutridata_lutein | 302 | 9 | 302 / 302 | Deferred |
| NDF-G023-20 | 20-番茄红素 | nutridata_lycopene | 51 | 8 | 51 / 51 | Deferred |
| NDF-G023-21 | 21-代餐食品 | nutridata_meal_replacement | 287 | 38 | 287 / 287 | Deferred |
| NDF-G023-22 | 22-咖啡因 | nutridata_caffeine | 546 | 12 | 540 / 546 | Deferred |
| NDF-G023-23 | 23-碘 | nutridata_iodine | 1,443 | 10 | 0 / 1443 | Deferred |
| NDF-G023-24 | 24-快餐库 | nutridata_fast_food | 162 | 11 | 162 / 162 | Deferred |
| NDF-G023-26 | 26-水产库 | nutridata_aquatic | 204 | 33 | 204 / 204 | Deferred |
| NDF-G023-27 | 27-奶茶库 | nutridata_milk_tea | 120 | 19 | 119 / 120 | Deferred |

所有表的 id 与 item_id 均通过单表非空/唯一检查；这不等于跨表同一业务 ID。实际物理快照的 25 份哈希、时间及文件定位已保存在本地 NativeFileManifest.json。原始来源及使用授权需独立核验；不将数据汇聚平台等同于独立测量来源。

## 3. 原生字段与层级

| 对象 | 原生路径及粒度 | B1 处理 |
|---|---|---|
| Ingredient record | ingredient sheet, 59 columns; row anchor | 保留 id、item_id、name、edible、water_rate、宏量、微量、脂肪酸、氨基酸及 list/detail JSON；不先填缺失或汇总 |
| Dish recipe record | dish sheet, 10 columns; row anchor | 保留 id、item_id、name、calorie、category、major、list/detail JSON 及时间列 |
| Ingredient composition | detail_json.nutritionMap[group][] | 166,691 个原生营养条目；名、desc、unit、value、部分 nrv、description/排序；按 JSON 路径保留 |
| Dish composition | detail_json.nutritionMap[group][] | 959,692 个原生营养条目；派生/测量身份仍待核查 |
| Recipe ingredient line | dish.detail_json.major[] | 152,531 条原生明细；(dish item_id, 数组索引) 为候选来源定位，不以食材名作唯一键 |
| Ingredient portion | detail_json.ingredientUnit[] | 2,338/3,446 行存在非空份量列表 |
| Dish portion | detail_json.unit[] | 21,794/22,180 行存在非空份量列表 |
| Cooking step | detail_json.dishCooksteps[] | 22,136/22,180 行有非空步骤，步骤位置/文字/媒体引用分层；不自动下载媒体 |
| Composition provenance | ingredient.detail_json.source, nutrientHistoryMap | 3,446 行 source 非空，17 个不同原始来源字符串；仅 1 行有非空 history map；不是独立证据数 |
| GI record | gi_food sheet, detail_json | 6,840 行，GI/GL、参考食物及来源/条件字段；暂不启用为基础宏量前置 |

核心三表 list_json.id 和 detail_json.id 均与各自行 item_id 一致；成分表内部 id 仅 1 行与 JSON ID 相等，菜肴及 GI 表内部 id 均不等于 JSON ID。不能将导出内部行 id 作为跨表业务键。

## 4. CandidateKeyLinkAudit：真正的连接路径

分母为 152,531 条 major 明细，22,180 个有非空 major 的菜肴记录。所有 note 是 JSON float 且为正数，未发现 major 明细中 unit、noteUnit、weightUnit、quantityUnit 的非空字段；不能直接认定为克、可食质量或最终摄入。

| 候选链接 | 单匹配 | 零匹配 | 多匹配 | inner join 行 | left join 行 | code 一致 | code 不一致 |
|---|---:|---:|---:|---:|---:|---:|---:|
| major.ingrId -> ingredient.id | 144504 | 8027 | 0 | 144504 | 152531 | 2498 | 142006 |
| major.ingrId -> ingredient.item_id | 152324 | 207 | 0 | 152324 | 152531 | 152324 | 0 |
| major.ingrId -> ingredient.detail_id | 152324 | 207 | 0 | 152324 | 152531 | 152324 | 0 |
| major.code -> ingredient.code | 152324 | 207 | 0 | 152324 | 152531 | 152324 | 0 |

**候选正确路径：** dish.detail_json.major[].ingrId → ingredient.item_id（与 ingredient.detail_json.id 相符），并逐条检查 major.code = ingredient.detail_json.code。三种候选（业务 ID、JSON ID、code）统计结果一致；复核脚本独立重读两个工作簿的原生内容，结果与主扫描一致。未观察到连接扩张。

- 152,324 条唯一匹配且 code 完全一致；21,973/22,180 个菜肴全部明细可连接且 code 一致（99.07%）。
- 207 条未匹配明细涉及 9 个不同 ingrId 与 9 个 code；最大单一 ID 频次 185。不能补造记录或静默丢行；以 source row/array index 定位待查。
- 84,024 条名称精确一致，68,300 条名称不同（占唯一匹配 44.84%）。名称差异不自动认定错配或同义，必须通过候选 alias/粒度核查；当前只是原生代码关联可行性，不是经过专家验证的食物概念匹配。
- 错用内部 id 仍有 144,504 个匹配，但仅 2,498 个 code 一致，142,006 个不一致。这是高风险的伪连接。B1 必须有反例验证：输入 internal id 伪链接被拒绝。
- 匹配和缺失统计均不提供对特定食材配方真值、食品来源质量、营养或临床效应的证据。

## 5. 缺失、单位及营养数值语义

以下表为食物成分库宽表原生值的逐列完整统计。非数字符号计数不是已经确证的 missingness 语义；数字零也不一定代表实测零。

| 列 | 非零数字 | 数字零 | 空白 + 空格 | 可能缺失/微量标记 | 其他/不等式 | 分母 |
|---|---:|---:|---:|---|---:|---:|
| calorie | 3399 | 18 | 0 + 0 | —: 24 | 5 | 3446 |
| protein | 3300 | 37 | 0 + 0 | —: 50; Tr: 42 | 17 | 3446 |
| fat | 3176 | 101 | 0 + 0 | Tr: 34; —: 35; tr: 4; -: 2 | 94 | 3446 |
| carbohydrate | 3076 | 255 | 0 + 0 | —: 23; Tr: 21 | 71 | 3446 |
| na | 3141 | 48 | 0 + 0 | —: 201; Tr: 9; -: 29 | 18 | 3446 |
| dietary_fiber | 1723 | 1026 | 1 + 0 | Tr: 23; —: 536; -: 8; tr: 1 | 128 | 3446 |
| vitamin_a | 1795 | 203 | 134 + 2 | —: 826; Tr: 219; -: 32; tr: 12 | 223 | 3446 |
| folic_acid | 1083 | 67 | 84 + 2 | —: 208; Tr: 44; -: 248 | 1710 | 3446 |

实际检测到 Tr/tr、—、-、未知、空值及其他非数值；尤其叶酸非数值很多。不得用统一 replace(Tr,0) 或 fillna(0) 导入。不确定义 Tr、破折号、0 的生物或测量含义，先保存 raw token + candidate class；具体解释须取得源字典或专业审查。其他字符串待分层解析，不以 Decimal 失败直接认定缺失。

全量宽表与对应嵌套 desc 数值的独立比对：

| 字段 | 可数值比较且相等 | 数值不一致 | 非数字对 | 嵌套缺项 |
|---|---:|---:|---:|---:|
| calorie | 3417 | 0 | 29 | 0 |
| protein | 3337 | 0 | 109 | 0 |
| fat | 3277 | 0 | 169 | 0 |
| carbohydrate | 3331 | 0 | 115 | 0 |
| na | 3189 | 0 | 257 | 0 |
| dietary_fiber | 2749 | 0 | 696 | 1 |
| vitamin_a | 1998 | 0 | 1314 | 134 |
| folic_acid | 1150 | 0 | 2212 | 84 |
| carbs_used | 2706 | 0 | 307 | 433 |

在本次可数值比较范围内未发现差异；所有报告的非数字对原始文本精确一致。菜肴库 calorie 22,180/22,180 与嵌套能量数值相等。这只说明导出内部一致性，不是独立化学验证。

- 原生 nutritionMap 明确给出能量 kcal、蛋白质/脂肪/碳水 g、钠 mg、维生素A μg RAE、维生素E mg α-TE 等；GI 条目可无量纲，不按营养素质量处理。
- 对本轮测试的核心营养素 description 文字，未检出显式每100克基准提示（限测试字符串；不证明数据没有其他来源说明）。原生每份/每100g、生/熟、可食部及成品出品率未资格化。
- 份量 unit/value 表存在但换算语义未充分核对。note 数值并不能证明克重，也不能证明油/盐的实际留存量。B3 参数先验必须先确认单位及配方投入/出品率语义，另用真实称重校准。
- 17 个原始来源字符串需解析成可审查 SourceArtifact/源版本/来源家族；NutriData 转引值与 FDC 同源风险保留。
- detail_json 空白：咖啡因库 6/546，碘库 1,443/1,443，奶茶库 1/120；这三库不可假定有完整嵌套详情。全库 list_json 对象 94,667/94,667，detail_json 对象 93,217/94,667。对非核心数据库只做画像，不进入本轮转换。

## 6. 原生字段分类与待验证科学语义

| 原生字段族 | 对齐合同 | 当前裁定 |
|---|---|---|
| item_id、JSON.id、code | ALIGN-S / F | 指定来源/版本的业务记录 ID；code 交叉验证；不直接跨 FDC/其他子库合并 |
| name、alias、major.name | ALIGN-S | 候选概念及别名；保持原文、方向、粒度、不确定性 |
| edible、water_rate、portion.unit/value、major.note | ALIGN-M | 保存原生数量及标签；实际基准与单位待查，禁止自动换算 |
| desc/name、value、unit、nrv | ALIGN-N | 原始营养属性、显示单位及标签参考；未知分母/定义/缺失单独标记 |
| cooking steps | 过程语义 | 文本/位置原样抽取；不从动作直接推断营养留存 |
| source、history、时间 | provenance | 来源线索与原始版本，需来源独立性审查 |
| GI/GL、reference、volunteer 等 | 条件性测量 | 独立任务；不以 GI 直接替代个体反应或营养治疗证据 |

保留 v2.1 的 FoodConcept ≠ FoodInstance ≠ Recipe、Not Annotated ≠ Absent、Observed ≠ Inferred 等区分。源数据不自动成为训练标签、科学证据、临床参考或 Gold。

## 7. K5RouteDecision

状态：HOLD_NOT_OBSERVED。当前本地授权目录没有 N5k360、原版 Nutrition5k 的实体目录及元数据，无法检查 dish_id、相机、绝对尺度、质量与增量组。不能把未访问写成断链或物理不合格。取得路径后按 §18 有限检查；若原生 ID/质量/分组不能恢复，切换原版 Nutrition5k 必要 metadata/media；若绝对尺度不可验证而真实质量有效，保留图像到重量候选、暂停绝对几何；若仍不满足再切自主称重 Pilot。B0-P 开发/校准/锁定探针采集尚未执行；不阻断 NDS/E2H 合法薄切片。

## 8. CoreSliceSelection 与 B0AdmissionReceipt

| 门 | 状态 | 后续 |
|---|---|---|
| B0-a 路径/版本 | PARTIAL | G023 实际登记完成；22 源路径待绑定，来源版本与许可未核验 |
| B0-b 原生画像 | PASS_PROFILE_G023 | 25 个真实 XLSX 全量行/字段/JSON 画像；CSV 编码与分隔符未执行（没有 CSV） |
| B0-c 缺失/单位 | PARTIAL | 计数、单位标签及原值保留；分母、数量单位、油盐、出品率及缺失语义待确认 |
| B0-d 粒度/键 | PASS_STATISTICAL_CORE_LINK | 单表键 + code 交叉核验；207 孤儿及名称差异需隔离/复核；不能自动获得科学资格 |
| B0-e K5 | HOLD_NOT_OBSERVED | 等待数据访问，按止损规则 |
| B0-f 真实样例 | PARTIAL | 本地保存成分、菜肴各前3行真实开发样例及原始定位；不是锁定评测样本 |

首轮只选 01 食物成分、02 菜肴两个逻辑库，GI 仅任务触发。允许编写/验证 B1 的原生摄取合同草案（typed raw record, stable source anchor, nested payload, namespace-qualified keys, UNKNOWN/PENDING 状态）；**不允许冻结完整 B1 物理合同或发布营养量化资产。** 先通过真实 round-trip、ID 伪链接/未知单位/缺失标记/重复与孤儿隔离的负例测试，以及来源/单位语义审查。上游共同 envelope 需保留 instance_class 与 source_class。

## 9. 交付与复现

| 合同交付物 | 本轮位置/状态 |
|---|---|
| SourceRegistryDelta | [SourceRegistryDelta.json](../../runs/B0/U1-A/NutriData_real_001/SourceRegistryDelta.json) |
| NativeFileManifest | 本地 private/NativeFileManifest.json（25原件哈希、CRC与定位，不公开原始文件） |
| NativeTableProfiles | 本地 private/NativeTableProfiles.json（全部字段、原生类型、JSON状态/顶层键、候选键）；[共享汇总](../../runs/B0/U1-A/NutriData_real_001/summary_shareable.json) |
| CandidateKeyLinkAudit | 本地 private/CoreLinkAudit.json；[独立复核汇总](../../runs/B0/U1-A/NutriData_real_001/core_link_crosscheck.json) |
| K5RouteDecision | 本文 §7、机器可读 receipt |
| CoreSliceSelection | 本文 §8、机器可读 receipt；本地 private/CoreRawSamples.json |
| B0AdmissionReceipt | [B0AdmissionReceipt.json](../../runs/B0/U1-A/NutriData_real_001/B0AdmissionReceipt.json) |

本地复现（必须选择新输出目录，不覆盖冻结运行）：

```sh
python3 src/b0/profile_nutridata.py --self-test
python3 src/b0/profile_nutridata.py --root source_data/excel-Nutridata --out runs/B0/U1-A/NutriData_real_002
python3 -B src/b0/profile_nutridata_core_links.py --root source_data/excel-Nutridata --out runs/B0/U1-A/NutriData_real_002/core_link_crosscheck.json
```

仓库仅同步公开统计、登记/receipt、文档与审计代码，不同步原始工作簿、记录、样例、媒体 URL、完整本地路径或 private 目录。代码版本可从历史提交复现。此运行尚未实施全量媒体去重、数据处理/训练、许可审查、全面源字典验证、完整 B0/B1 资格或独立统计评价。

## 10. 总体 Milestone 与分工

| 阶段 | 实际状态 |
|---|---|
| U0 | v2.1 在 main 已归档（PR #52） |
| U1 / B0 | G023 实地画像及核心连接审计完成；整体 1/23 顶层来源画像，22源待绑定，语义资格未闭合 |
| U2 / B1 | 仅允许原生薄切片合同草案，未冻结 |
| U3–U5 | 尚未执行标准化、量化、任务释放 |
| U6–U9 | 尚未执行独立探针、基线、受控实验及外部验证 |

PI 需确认/提供：22个多模态数据集的实际存储根路径或授权元数据访问方式；若能取得 NutriData 数据字典、营养成分基准、菜肴配方 note 单位说明则提供。Agent 负责后续来源查证、生成 B1 真实薄切片适配器和负例、孤儿列表及名称差异抽检建议；关键科学测量与安全语义需适格专业审查，不以双 Agent 一致替代 Gold。自主餐盘采集准备可并行，不阻塞路径及结构审计。

本轮没有修改 UDF master、历史冻结参考或科研结论。下一任务：B0/U1-A-Remainder + B1-Native-Core-Draft（仅在限定真实数据范围内开展），不以本报告声称 B0 整体完成。
