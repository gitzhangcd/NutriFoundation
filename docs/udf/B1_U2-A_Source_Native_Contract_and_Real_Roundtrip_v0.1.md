---
title: "B1 / U2-A — Source-Native Data Contract, Canonical Object Draft & Real-Sample Round-Trip Validation"
version: "0.1"
date: 2026-11-25
authority: "AI Nutri Unified Data Foundation v2.1"
status: "PASS_U2_A_BOUNDED_REAL_DRAFT / B1_GLOBAL_FREEZE_HOLD"
contract_version: "UDF-B1-NATIVE-DRAFT-0.1"
run_id: "B1-U2A-real_003"
---

# B1 / U2-A｜原生数据合同、统一对象草案及真实样本回放验证

## 0. 执行结论与范围

依据 [UDF v2.1](../AI_Nutri_Unified_Data_Foundation_v2.1.md) §11、§20、§34、§35、§37、§41，以及前序 [NutriData B0](B0_U1-A_NutriData_Real_Asset_Audit_v0.1.md)、[公开样本 B0](B0_U1-A_Public_Sample_Exploration_v0.1.md) 的实际准入结果，完成原生适配器和 source-scoped canonical draft 的限定范围真实执行。原始数据不改写，不需要下载完整媒体。

**U2-A 真实薄切片的工程验收通过；不是全局 B1 schema freeze。** B0 整体仍开放。首轮与第二轮真实运行留本地；本报告以最终加固后 `real_003` 为权威，未覆盖历史运行。时间：2026-11-25T14:37:46.230478+00:00。

| 指标 | 最终实测 |
|---|---:|
| 通过 B0 文件 hash fence、扫描前后一致的源文件 | 23 |
| 来源适配范围 | 14（11个目标公开源、1个原版Nutrition5k替代源、2个NutriData子库） |
| 原生记录与源锚点回放 | 747 / 747 |
| 类型化对象 | 5,699 |
| 已声明并实际落盘的对象类型 | 17 |
| 字段级来源回放 | 10,975 / 10,975 |
| JSONL序列化读回和同一时钟独立重新执行适配器 | 5,699 / 5,699 |
| 不同审计时钟下稳定object_id | 5,699 / 5,699；revision不同 |
| 合同测试 | 46/46（7个正例、39个拒绝测试，包含真实对象变异） |
| JSON Schema草案结构检查 | 5,699 / 5,699；5/5结构负例拒绝 |
| 正式发布/科学资格化资产 | 0 |

所有记录、镜像、已暴露validation数据只允许 CURATION_DEV；并不代表原始下载版本、真实化学营养误差、长期个体状态、科学参考或模型评测已获资格。

## 1. 实际实现：三层数据与独立关联

```text
L0 Source artifact (bytes + hash + scope)
      │
      ├─ SourceAnchor (sheet/row, CSV record, JSON pointer, text line)
      ▼
L1 NativeRecord (ordered/raw logical record + raw digest)
      │  typed field bindings (original path + exact raw value + field axes)
      ▼
L2 Source-scoped canonical draft (typed collection)
      ├─ Candidate native link (typed endpoint + namespace + source key)
      ├─ Measurement draft (raw lexical value, unit/basis/qualification Slot)
      └─ Development structural allowlist view
```

共享层不是跨源统一真值表。源文件hash与 B0 清单绑定，SourceAnchor 的 locator 指向可重新读取的源文件记录，canonical 字段以原生路径（JSON pointer）与原值绑定。XLSX记录包含原生字段、显式单元格值/类型/公式存在性、表头、原始JSON字符串及解析后JSON；CSV保留表头与顺序token；文本保留原始行；JSON保留完整选中源节点。原始数据的 byte-level 真实性依靠源文件hash与定位器，不声称 canonical 单独能复原整份源文件或原字节编码。

对象ID采用文件快照身份、原生定位、对象类型和子记录索引的确定性散列，不依赖运行时钟；revision覆盖完整内容（含实际创建时间），引用为 immutable object_id@revision_id。不同审计时钟验证同源同定位的ID稳定而revision不同。新输入快照版本变化不默认视为同一个实物或同一个业务实体。

### 1.1 CommonEnvelope 与 Slot

继承 NDF-D0 §6 和 NDSF Part III §2.2–2.4，实际字段有 object_id、revision_id、kind、schema_version、contract_version、lifecycle、producer_role、created_time、clock_axis、provenance_refs、dependency_refs、source_class、instance_class、purpose_release_ref、purpose、supersedes_ref。当前全为 DRAFT / REAL_SOURCE_GROUNDED / CURATION_DEV；这里真实镜像记录只是“该镜像实际包含此字段”，不是证明原版或自然世界真值。禁止 synthetic/mixed/simulated 混入此 real-only profile，不改变上游对合法构造及模拟实验的支持。

四种 Slot：VALUE、UNAVAILABLE、PENDING、NOT_APPLICABLE。原生空值/零/Tr/非数字字符串可保留在受限原始表示，但未知规范量不直接赋0。字段绑定的 KNOWN 指原生表达存在，不代表其测量语义已知。字段级 origin_mode、knowledge_state、construction_class、visibility_overlay 保持正交；仅当前源表达的OBSERVED/OBS被实际实例化。未知单位、分母、制备状态和资格使用 tagged PENDING。

### 1.2 稳定身份、科学对象及测量

FoodLabelDraft 是来源内类别，不是规范化 FoodConcept；FoodEntityDraft 是来源内食材/菜单项候选；RecipeDraft 是参考配方或原生菜谱而非实物；FoodInstanceDraft 是 Nutrition5k 原生扫描身份，不是已验证独立餐盘；MediaObservationDraft 是区域或菜单标签观察，不声称已取得全部实际图像；DietaryObservationDraft 是报告链路行而非长期状态；ProcessVocabularyDraft、VideoMetadataDraft 与食品类别分开。ProductVersionDraft 保留条码及API快照，不声称历史商品版本完全相同。NutrientMeasurementDraft 是来源属性/数量草案（含质量、能量、营养值），没有完成完整 MeasurementDefinition、ComponentConcept、测量效度或误差模型实例化。NativeLinkDraft 保留结构匹配与科学资格 PENDING，不支持名称或视觉相似度自动升级为同一物理实例。

## 2. 实际选样与源级回放

选择方式：确定性分布式下标薄切片、故意包含NutriData孤儿/名称差异、SNAPMe重复候选键，以及被引用父记录的闭包。不是随机样本、代表性样本或独立benchmark。源记录检查范围为解析器实际读入的相关文件，不是整个22个原始数据集。父键闭包导致两个成分表的选样超过100；不表示已全量转换。

| 输入适配器 | 来源 | 实际解析记录 | 选中 | 回放 |
|---|---|---:|---:|---:|
| nutridata_ingredient | NDF-G023-01 | 3,446 | 134 | 134 |
| nutridata_dish | NDF-G023-02 | 22,180 | 34 | 34 |
| n5k_ingredient | NDF-G013 | 555 | 120 | 120 |
| n5k_dish1 | NDF-G013 | 4,768 | 17 | 17 |
| n5k_dish2 | NDF-G013 | 238 | 16 | 16 |
| snapme | NDF-G004 | 4,761 | 40 | 40 |
| food101_train | NDF-G001 | 75,750 | 32 | 32 |
| NDF-G002_category | NDF-G002 | 100 | 24 | 24 |
| NDF-G002_bbox | NDF-G002 | 114 | 24 | 24 |
| NDF-G003_category | NDF-G003 | 256 | 24 | 24 |
| NDF-G003_bbox | NDF-G003 | 100 | 24 | 24 |
| isia_class | NDF-G005 | 500 | 32 | 32 |
| NDF-G012_recipe | NDF-G012 | 12 | 12 | 12 |
| NDF-G018_recipe | NDF-G018 | 12 | 12 | 12 |
| off_single | NDF-G016 | 1 | 1 | 1 |
| off_search | NDF-G016 | 10 | 10 | 10 |
| menu_items | NDF-G017 | 41 | 41 | 41 |
| menu_labels | NDF-G017 | 646 | 24 | 24 |
| recipeqa | NDF-G020 | 3,562 | 24 | 24 |
| epic_train | NDF-G022 | 67,217 | 32 | 32 |
| epic_verb_class | NDF-G022 | 97 | 10 | 10 |
| epic_noun_class | NDF-G022 | 300 | 28 | 28 |
| epic_video_id | NDF-G022 | 700 | 32 | 32 |

本次未实现 G006、G007、G008、G009、G010、G011、G014、G015、G019、G021 的完整原生适配；G013 仅 Nutrition5k 原版替代。尤其 VIREO 的作者处理后矩阵不能代替原生图片和353维食材标注。G023仅处理01/02两个核心子库。所有公开数据与用户下载档案的版本等价仍未验证。来源/许可按B0记录保留，未授权的研究release一律HOLD。

## 3. 17类实际独立集合

| 类型 | 对象数 |
|---|---:|
| SourceArtifact | 23 |
| SourceAnchor | 747 |
| NativeRecord | 747 |
| FoodEntityDraft | 295 |
| NutrientMeasurementDraft | 2,851 |
| RecipeDraft | 58 |
| RecipeIngredientDraft | 226 |
| FoodInstanceDraft | 33 |
| NativeLinkDraft | 358 |
| DietaryObservationDraft | 40 |
| FoodLabelDraft | 112 |
| MediaObservationDraft | 72 |
| ProductVersionDraft | 11 |
| QARecordDraft | 24 |
| ProcessVocabularyDraft | 38 |
| VideoMetadataDraft | 32 |
| ProcessObservationDraft | 32 |

本地按kind分别保存 JSONL 文件，不采用单个无约束科学多态事实表。本轮没有安装PyArrow、DuckDB、Pydantic或jsonschema；使用Python 3.9+标准库和版本化JSON/JSONL草案，避免依赖环境成为阻断。未做生产Parquet/SQL FK部署，也未声称大规模吞吐验证完成。

## 4. 来源关联、测量和阻断结果

| 检查 | 实际结果 | 边界 |
|---|---:|---|
| NutriData菜肴参考配方明细 | 226 | 结构化配方行，非真实摄入 |
| 其中业务ID+code候选连接 | 220 | 100条名称差异仍保留，不判为同义 |
| 无可核验父记录或code不符 | 6 | 明示HOLD，原始行不丢弃 |
| Nutrition5k食材明细父链接 | 214 | 采用已验证的来源原生整数ID到ingr_十位补零规则；与N5k360场景隔离 |
| Menu-Match菜单标签关联 | 48 | 菜单热量是来源参考，不是实测摄入 |
| EPIC动作—词表/视频元数据关联 | 96 | verb、noun、video 分别命名空间和类型校验；不从动作直接推断进食 |
| SNAPMe全主表重复候选键组 | 298 | 40条选样包含17条重复候选组成员；禁止按该键自动去重或聚合 |

358条NativeLinkDraft加220条NutriData配方候选父链接仅为结构证据；科学语义资格未通过。NutriData连接必须用 item_id + code，不得使用内部行id。Nutrition5k保留同一dish的固定前6字段和重复7字段原生布局，量化依据按来源声明区分；不赋予N5k360绝对尺度或独立扫描组。OFF的 _100g 后缀与展示单位分别保留，未将展示单位直接附到API归一后缀值。SNAPMe原生两数量列保留，未重复计算，也未发布参与者标识。

本次2,851个来源属性/测量草案分组如下。这些是本地草案候选标签，不是新增科学参考层，也不意味着相应Q-profile已获得资格。

| 本地候选标签 | 对象数 |
|---|---:|
| Q-COMPOSITION_SOURCE_UNQUALIFIED | 840 |
| Q-COMMON-CALC_CANDIDATE | 1468 |
| Q-MASS_CANDIDATE | 247 |
| Q-RECALL_CANDIDATE | 200 |
| Q-LABEL_CANDIDATE | 55 |
| Q-MENU_CANDIDATE | 41 |

未知成分分母、源方法、配方note单位、食物状态、调味品及出品率继续PENDING。所有 normalized_value / qualification 为 PENDING。无营养标准化计算、无油盐先验估计、无独立化学实测或参考独立性主张。

## 5. 真正执行的验证，而非数据复制

运行 `run_b1.py` 时：首先核验每份实际文件与前序B0 hash清单一致；从原件构造17类对象并运行类型、依赖、原生绑定、测量和用途校验；落盘独立 JSONL；重新读回全部对象并重算revision digest；重新打开真实源文件按locator恢复747个原生逻辑记录及锚点、检查10,975个字段；在同一时钟下重新运行适配器并比较完整对象；另以不同审计时钟重新执行并核对稳定对象ID和新revision；最后保留本地源resolver、collection manifest及聚合报告。适配器再执行仍使用同一代码，不是独立实现或人工语义复核。

`test_b1_contract.py` 的46项测试包括7项接受测试及39项拒绝测试，其中多项在真实私有对象的内存副本上修改字段并重算合法revision，确认能被对应科学/结构守卫拒绝，而不仅仅是hash变化。以下测试表来自实际报告，不等于UDF §35所有实验、时间及E2H端到端测试均通过。

| # | 检查 | 预期 | 实测 |
|---:|---|---|---|
| 1 | real private typed collections validate | `ACCEPT` | PASS |
| 2 | lexical zero remains value; unknown Tr is not zero | `ACCEPT` | PASS |
| 3 | source-native pending orphan retained | `ACCEPT` | PASS |
| 4 | structural allowlist projection | `ACCEPT` | PASS |
| 5 | all current real records restricted to curation | `ACCEPT` | PASS |
| 6 | valid explicit unit/state comparison guard | `ACCEPT` | PASS |
| 7 | native link evidence can be structural candidate | `ACCEPT` | PASS |
| 8 | same-name recipe and image promoted to instance | `INSTANCE_IDENTITY_NOT_PROVED` | PASS |
| 9 | perceptual hash similarity promoted to instance | `INSTANCE_IDENTITY_NOT_PROVED` | PASS |
| 10 | unknown or missing numeric slot with hidden value | `SLOT_UNAVAILABLE_INVALID` | PASS |
| 11 | Tr silently changed to measured zero | `MEASUREMENT_VALUE_DRIFT` | PASS |
| 12 | unmarked oil given arbitrary default amount | `RECIPE_QUANTITY_DRIFT` | PASS |
| 13 | unqualified recipe note converted to grams | `RECIPE_NOTE_UNIT_BASIS_HOLD` | PASS |
| 14 | raw and cooked values compared as equal | `FOOD_STATE_INCOMPARABLE` | PASS |
| 15 | mL to g without density | `DENSITY_REQUIRED` | PASS |
| 16 | serving to g without portion mass | `PORTION_MASS_REQUIRED` | PASS |
| 17 | same source family double counting | `SOURCE_DEPENDENCE` | PASS |
| 18 | N5k360 unknown absolute scale | `GEOMETRY_OR_GROUP_HOLD` | PASS |
| 19 | incremental scans treated independent | `GEOMETRY_OR_GROUP_HOLD` | PASS |
| 20 | SNAPMe aggregation before grain qualified | `AGGREGATION_NOT_QUALIFIED` | PASS |
| 21 | replicated whole meal contribution even if grain declared | `DUPLICATE_AGGREGATION` | PASS |
| 22 | daily record relabeled habitual | `DIETARY_STATE_INFLATION` | PASS |
| 23 | system or evaluator view requested outside scope | `PROJECTION_NOT_AUTHORIZED` | PASS |
| 24 | hidden gold added to allowlist projection | `PROJECTION_CLOSURE` | PASS |
| 25 | source hash nested in field list | `PROJECTION_CLOSURE` | PASS |
| 26 | agent-only reference promoted to Gold | `REFERENCE_NOT_QUALIFIED` | PASS |
| 27 | mutated immutable revision | `REVISION_INTEGRITY` | PASS |
| 28 | missing instance_class | `ENVELOPE_FIELDS` | PASS |
| 29 | mixed instance in real-source only ingest | `REAL_ONLY_PROFILE` | PASS |
| 30 | synthetic source promoted to real | `REAL_WITH_SYNTHETIC_SOURCE` | PASS |
| 31 | source document referenced as study identity | `REF_KIND_MISMATCH` | PASS |
| 32 | evidence/claim type conflation cannot pass grounding validator | `REF_KIND_MISMATCH` | PASS |
| 33 | same database calculation claimed chemical assay | `REFERENCE_PROFILE_MISMATCH` | PASS |
| 34 | unknown denominator passed to calculation | `MEASUREMENT_NOT_QUALIFIED` | PASS |
| 35 | canonical normalized value invented | `UNQUALIFIED_NORMALIZATION` | PASS |
| 36 | unqualified source basis fabricated | `SOURCE_BASIS_HOLD` | PASS |
| 37 | public exposed data promoted to locked probe | `PROBE_NOT_INDEPENDENT` | PASS |
| 38 | development data requested for locked release | `RELEASE_BLOCKED` | PASS |
| 39 | unqualified development reference requested for training | `RELEASE_BLOCKED` | PASS |
| 40 | evidence-backed field changed despite valid revision digest | `CANONICAL_SOURCE_DRIFT` | PASS |
| 41 | source anchor raw record hash mismatch | `NATIVE_RAW_DIGEST` | PASS |
| 42 | source record has invalid anchor locator | `ANCHOR_MISMATCH` | PASS |
| 43 | duplicated native record locator | `DUPLICATE_NATIVE_LOCATOR` | PASS |
| 44 | wrong NutriData parent ID despite plausible name | `BUSINESS_KEY_CODE_MISMATCH` | PASS |
| 45 | unqualified link promoted to same physical instance | `LINK_PROMOTION` | PASS |
| 46 | future release flag or frozen record inserted into draft | `DEV_ONLY` | PASS |

另用 `check_schema.py` 独立检查实际 JSON Schema 使用的关键词子集（非通用JSON Schema标准符合性实现），全部5,699个对象结构通过、5项结构负例拒绝，17类schema和运行时字段一致。系统/评估者视图不予授权，当前仅允许schema inspection的结构白名单输出（无原值、标识、路径、hash或参考答案）；没有构造真实任务的模型输入、Gold或锁定评测release。

## 6. D0 科学侧桥接：11类独立对象，不重复建设母层

已检查仓库现行 `src/nutrifoundation/ndf/d0` 运行时、structural validator 以及首个真实D1 fixture；既有 D0-A2/A2.1 的历史物理通过记录保留、不重写。B1的两个共享科学类型SourceArtifact、SourceAnchor已实际分集合实例化，另外9个科学类型按 NDF-D0 §5.1 独立声明并委托既有D0，未伪造SCI记录。

[桥接登记](../../schemas/udf/b1/B1_D0_ScientificCollectionBridge_v0.1.json) 保留11个逻辑集合：source_artifacts、source_anchors、study_identities、evidence_units、scientific_claims、scientific_relations、evidence_conflicts、evidence_gaps、verification_records、knowledge_snapshots、scientific_reference_states。**这不是11类均已实际落盘或D0↔B1生产互操作通过。** 现有 D0 历史的 source_class（如 PRIMARY_STUDY）、purpose_release_ref枚举、flat payload、null supersedes_ref 与B1新Slot、source_role、nested payload及instance_class不同。桥接必须显式映射并保留版本；旧实例缺instance_class保持迁移未决，不能默认REAL。本轮未执行生产桥接适配器、既有D0全量回归或真实SCI/决策/认识实验。B1不替代现有规范、系统或已冻结实验。

## 7. Gate与Milestone

| 门 | 本轮结果 |
|---|---|
| G0 | HOLD：来源与用途授权/资格未完全确认 |
| G1 | PASS_SELECTED：23份实际源输入及747锚点一致 |
| G2 | PASS_DRAFT：原生表示及17类对象、46项合同与5项结构负例；尚未科学语义定型 |
| G3 | PARTIAL：选样结构关联有效；孤儿、别名、真实身份、测量基准仍需资格 |
| G4 | HOLD：无独立科学参考或化学真值资格 |
| G5 | PASS_DEV_PROJECTION_ONLY；正式发布HOLD |
| G6/G7/G-PROBE | 未激活 |

U0 v2.1 已归档；U1的NutriData与网络样本画像完成限定范围，用户原始22档案仍未全量验收；U2-A 当前限定真实薄切片通过；U2全局物理合同尚未冻结，U3–U9尚未执行。本轮工作不要求PI提供全量数据或确认；后续针对无法从网络取得的原生标签、N5k360场景尺度、NutriData官方字段基准以及专业语义，按实际需要请求最小材料。下一任务候选：**B1 / U2-B｜Measurement Semantics, Namespace Qualification & D0 Bridge Conformance**。可以并行开展已画像的词表抽取，但不在语义资格门前发布B2映射。

## 8. 交付物与复现

- [B1结构Schema草案](../../schemas/udf/b1/B1_Native_ObjectContract_v0.1.schema.json)
- [D0科学侧独立集合桥接登记](../../schemas/udf/b1/B1_D0_ScientificCollectionBridge_v0.1.json)
- [最终真实回放报告](../../runs/B1/U2-A/real_003/RealSampleRoundTripReport.json)
- [合同负例报告](../../runs/B1/U2-A/real_003/ContractNegativeTestReport.json)
- [Schema检查报告](../../runs/B1/U2-A/real_003/SchemaCheckReport.json)
- [B1准入receipt](../../runs/B1/U2-A/real_003/B1AdmissionReceipt.json)
- 程序：`scripts/udf/b1/contract.py`、`run_b1.py`、`check_schema.py`、`test_b1_contract.py`。本地对应 `src/b1/` 及 `tests/b1/`。

从 NutriOne 根目录执行（必须使用新的输出目录，保留原运行）：

```sh
python3 -B src/b1/run_b1.py --root . --out runs/B1/U2-A/real_004
python3 -B tests/b1/test_b1_contract.py --run runs/B1/U2-A/real_004 --out runs/B1/U2-A/real_004/ContractNegativeTestReport.json
python3 -B src/b1/check_schema.py --schema schemas/udf/b1/B1_Native_ObjectContract_v0.1.schema.json --bridge schemas/udf/b1/B1_D0_ScientificCollectionBridge_v0.1.json --run runs/B1/U2-A/real_004 --out runs/B1/U2-A/real_004/SchemaCheckReport.json
```

原始记录、患者/参与者标识、源映射、本地真实对象及媒体保留在Mac本地，`real_003/private/`约20 MB，不进入公开仓库。只同步脚本、结构规范和汇总报告。本轮无真实Gold、模型训练、受控科学实验、完整生产Schema冻结或独立专业验证；这些是后续任务，不因工程回放通过自动转为已完成。
