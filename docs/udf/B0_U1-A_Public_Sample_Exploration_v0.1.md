---
title: "B0 / U1-A — Public Sample Exploration & Native Linkage Audit"
version: "0.1"
date: 2026-11-25
authority: "AI Nutri Unified Data Foundation v2.1"
status: "PARTIAL_PASS_PUBLIC_SAMPLE_EXPLORATION / GLOBAL_B0_OPEN"
run_id: "B0-public-samples-20261125-001"
---

# B0 / U1-A｜公开数据小样本探索与原生关联审计 v0.1

## 1. 执行结论

依据 [UDF v2.1](../AI_Nutri_Unified_Data_Foundation_v2.1.md) 的 B0 合同和用户要求，先通过官方公开端点、作者样例及候选公开镜像获取小样本，不复制大型完整媒体档案。实际尝试原22个顶层来源；17个取得目标源记录、原生标注/词表或作者处理样例（含待核验镜像）；1个取得官方替代资产 Nutrition5k，而非 N5k360 原生场景；4个暂未取得目标记录。共保存104份文件（含被拒镜像、来源说明、元数据及样本图），58,567,784字节，逐文件核对大小及SHA256，0项指纹不一致。保存字节不等于网络总流量。

本轮覆盖的是在线快照及其局部样本，不等于用户2026-09-30已下载文件的原始版本。所有样本均为 CURATION_DEV_ONLY；无科学资格化数据 release，无独立评测或训练集冻结。NutriData 既有真实审计不覆盖、不改变。完整 B0 仍开放。

## 2. 逐源实际取得结果

| ID | 数据集 | 取得性质 | 实测结构与限制 |
|---|---|---|---|
| NDF-G001 | Food-101 | 官方索引与样本 | 75,750条唯一训练索引；101类；12条viewer记录；发布SHA256一致 |
| NDF-G002 | UEC-Food100 | 档案镜像样本 | 100类词表；2个边界框文件共221条；2张样本图 |
| NDF-G003 | UEC-Food256 | 档案镜像样本 | 256类词表；2个边界框文件共726条；2张样本图 |
| NDF-G004 | SNAPMe | 原生主关联表 | 4,761行、121字段；95名参与者、275个subject-day、1,153种FoodCode |
| NDF-G005 | ISIA Food-500 | 官方元数据 | 500类、40,204条完整val_finetune索引；另含有限文本前缀 |
| NDF-G006 | Food-11 | 纠错后的档案镜像 | 目录索引16,643张、正确11类别和3划分；2张样本图 |
| NDF-G007 | FoodX-251 | 第三方标注镜像 | 118,475条两列记录；首列唯一，次列均为数字；原始版本待核对 |
| NDF-G008 | Food-101N | HOLD | 官方介绍；原生verified_train/val等文件待取得，未代为同意访问条件 |
| NDF-G009 | Fruits-360 | 官方样本 | 279个目录名、大小写归一278个；2张图、属性字典及单项元数据；版本待核对 |
| NDF-G010 | Food2K | HOLD | 官方项目与作者代码说明；未取得原生类别表及训练记录 |
| NDF-G011 | VIREO Food-172 | 作者处理后样例 | 32训练、32测试模型输入矩阵；309维词指示、30位索引；非原始353维食材标注 |
| NDF-G012 | XiaChuFang | 第三方镜像样本 | 12条真实菜谱记录；7个原始风格字段；镜像报告行数1,550,151与原版不一致 |
| NDF-G013 | N5k360 | 原版Nutrition5k替代资产 | 5,006餐盘、555食材、28,455食材明细；原版RGB及深度图；N5k360场景尺度仍HOLD |
| NDF-G014 | Food-5K | 纠错后的档案镜像 | 5,000图档案索引；food/non_food；正确三划分；2张图 |
| NDF-G015 | FoodieQA | HOLD | 官方代码说明；数据访问需要接受条件，未绕过 |
| NDF-G016 | Open Food Facts | 官方API当前快照 | 11个不同条码，11个nutriments对象及100g基准 |
| NDF-G017 | Menu-Match | 官方原生标注 | 646个图像键；1,386个菜单标签出现；41个菜单项；关联全部成功 |
| NDF-G018 | RecipeNLG | 第三方备选样本 | 12条含title/ingredients/directions/link/source/NER字段；首个tokenized镜像不用于原生合同 |
| NDF-G019 | eButton | HOLD | 仅原论文网页，未取得原生参与者图像标注 |
| NDF-G020 | RecipeQA | 官方原生验证集 | 3,562题、983个recipe_id；qid唯一；本次已暴露，仅开发用途 |
| NDF-G021 | UNIMIB2016 | 镜像转化标注 | 3份image-keyed JSON、1份COCO-like JSON；非原生MAT资格验证 |
| NDF-G022 | EPIC-KITCHENS-100 | 官方训练元数据 | 67,217训练记录；97动词、300名词、700视频元数据；主候选键与三类FK核对 |

## 3. 科学及工程发现

### 3.1 真实文件优先于文档描述：Nutrition5k

官方原版发布目录可单独获得两份dish CSV、ingredients_metadata.csv及RGB/depth split。完整解析两份dish CSV共5,006行、5,006唯一dish_id。实测所有行均为6个固定字段 + 7个/食材重复字段；不符合把README所列num_ingrs直接作为固定列的做法。重复组起点为第7列，包含ingredient ID、名称及五个数值量。食材表实际列为 ingr,id,cal/g,fat(g),carb(g),protein(g)。通过显式将原生整数id转为 ingr_ 加10位零填充编号，28,455条食材明细全部匹配555个父食材ID。RGB train/test=4059/709、depth=2758/507；各自直接ID交集0、未知ID 0。尚未验证跨媒体增量扫描家族的实际分组，更不意味着不存在预训练污染。

一个来自原版depth train的餐盘取得640×480 RGB、8-bit彩色深度图和16-bit原始深度PNG。原版README说明深度单位；实际NeRF场景尺度、COLMAP外参与N5k360 scene crosswalk未取得，因此不得用原版RGB-D证据宣称N5k360绝对几何通过。K5按任务启用Nutrition5k原版薄切片作为替代路线；营养参考依旧区分称重、数据库计算与独立化学测量。

来源：https://github.com/google-research-datasets/Nutrition5k 与 https://storage.googleapis.com/nutrition5k_dataset/nutrition5k_dataset/ 。N5k360来源：https://github.com/amughrabi/N5k360 。

### 3.2 SNAPMe 一条膳食记录不能简单视为一张图

从官方公开tar.gz有限前缀提取完整的 master_SNAPME_linkfile.csv（2,710,352字节），没有下载完整2GB压缩包。4,761行均121列。95个subject_id、275个subject-day、1,153种FoodCode；filename非空原始字符串去重为1,678，不将字符串计数解释为独立图片数。实际候选键 subject_id + snapme_study_day + FoodNum1 仅3,481个不同组合；加入Occ_No也仅3,493个不同组合，二者均不是唯一主键。FoodAmt与FoodAmt.1原始文本4,761/4,761完全相同；两者都可数值解析，仍需原生字段字典确认。禁止重复合计、丢弃重复关联或跨源合并参与者身份。B1应保留原始行锚点，单独表示食品记录、照片关联和营养测量，并验证照片列表的编码语义和ASA24版本。

来源：https://agdatacommons.nal.usda.gov/articles/dataset/SNAPMe_A_Benchmark_Dataset_of_Food_Photos_with_Food_Records_for_Evaluation_of_Computer_Vision_Algorithms_in_the_Context_of_Dietary_Assessment/24856449 与 https://ndownloader.figshare.com/files/44532971 。原生照片媒体未取得或与主表核对。

### 3.3 镜像身份错误是真实风险

第一份Food-11 HF镜像的11个标签为具体菜品（例如披萨、沙拉等），而EPFL原版为11大类；第一份Food-5K镜像有5,000行却提供101类标签而非food/non_food。两者从原生任务入口隔离。另用Kaggle trolukovich 两份档案的有限HTTP Range获取目录与2张训练样本图，核对Food-11 16,643张、11类、三个split，Food-5K 5,000张、二分类、三个split；正确镜像仍为待版本核验的候选资产，不是已验收的原档。

来源：https://www.epfl.ch/labs/mmspg/downloads/food-image-datasets/ ；https://www.kaggle.com/datasets/trolukovich/food11-image-dataset ；https://www.kaggle.com/datasets/trolukovich/food5k-image-dataset 。

RecipeNLG的首个镜像含tokenized input_ids/attention_mask/labels，缺link/source，无法恢复原生来源链；备选样例有原生风格字段但只有12条、镜像报告总量1,000。XiaChuFang备选镜像报告1,550,151行，与原项目1,520,327条不符，原始版本与去重需实物验证。Fruits-360官方当前训练目录279名、casefold后278，不直接合并大小写或将目录当作实物身份。

### 3.4 原生训练与样例合同

- Food-101：75,750条训练索引唯一，原发布checksum匹配；12条viewer记录具有image、label字段和101类字典。图片/标注角色分离，viewer快照与用户原档版本仍待对照。
- UEC：100/256类字典与两份bbox文件分别取得；221/726条bbox均五列、坐标为非负且顺序正确。未核验全部图像尺寸、跨库图片重复及坐标边界。
- VIREO作者处理后输入样例：train/test label各32，wordIndicator 32×309、indexVector 32×30、wordVector 309×300。不能替代原始353维可见食材标注、食材词表与图片原生ID绑定。来源：https://github.com/PublicRelease/FoodRecog 。
- ISIA：官方元数据包中500条类别标签、40,204条val_finetune索引及有限其他文本前缀。截断前缀不是完整split。已下载的验证集仅用于开发结构探索。
- Menu-Match：实际labels为分号分隔的图像到菜单标签列表；items_info分号分隔含菜单名称、数据库标签、热量和餐厅。646个唯一图片键、1,386个标签出现全部关联41个菜单项。菜单热量不是实测摄入。来源：https://neelj.com/projects/menumatch/data/ 。
- Open Food Facts：官方API取得11个不同条码及100g标记，字段和数据库版本仍需区分，商品标签不是独立化学测量。来源：https://world.openfoodfacts.org/data 。
- RecipeQA：官方下载val.json中的3,562题、qid唯一，983个recipe_id；visual_coherence 830、visual_cloze 842、textual_cloze 961、visual_ordering 929。原生validation文件已暴露，不充当未见确认集。来源：https://hucvl.github.io/recipeqa/ 。
- EPIC：训练表67,217行、narration_id唯一；97个动词和300个名词类别，700条视频元数据；按观测字段检验，verb_class、noun_class、video_id孤儿均0，start/stop frame顺序异常0。未下载视频、核对时间单位或验证全量分组。来源：https://github.com/epic-kitchens/epic-kitchens-100-annotations 。
- UNIMIB镜像仅转化后的image-keyed JSON及COCO-like JSON；文件之间可能重叠、COCO类别定义可能改变，不能加总当独立实例数，也不能冒充原MAT分割参考。

## 4. B1薄切片准入建议

| 资产与数据任务 | 当前准入边界 |
|---|---|
| 已有NutriData 01/02 | 延续已审计原生记录、嵌套JSON、食材业务键与候选链接；原生摄取/round-trip草案；单位、缺失、来源、配方量化仍待资格化 |
| Food101、UEC、ISIA、Fruits、FoodX、Food11、Food5K | 真实类别、媒体及bbox合同草案；原生与镜像保持独立身份 |
| VIREO、XiaChuFang、RecipeNLG | 处理后矩阵/菜谱候选合同；不冻结原生353维标签或镜像版本等价 |
| Nutrition5k原版、Menu-Match、OFF | 质量/成分/食品标签等类型化测量合同；不产生跨库实例真值 |
| SNAPMe | 原生行、食品与图片多对多关系、报告属性；主键和测量字典需进一步核对 |
| RecipeQA、EPIC、UNIMIB | 过程及任务记录、QA或区域候选；验证集暴露与转换来源保留 |

B1仅允许针对已具备实际薄切片的source-native adapter、typed envelope、source anchor、round-trip及负例测试。不能将这些样本直接用作模型训练、正式benchmark或SIS确认性实验；不能冻结尚未恢复源字段语义的全局物理schema。NutriData的菜肴—成分实际原生关联仍按此前审计处理。

## 5. 后续最小缺口，而非要求全量复制

目前网络侧未拿到四个目标源的实际记录：Food-101N（访问条款及原生验证标注）、Food2K（原生词表/索引）、FoodieQA（需同意访问条件）、eButton（未发现可用原生记录）。N5k360几何任务另需原生scene ID、相机/尺度文件，VIREO需完整原生类别/食材词表与几条图片级标签。XiaChuFang原版快照也需后续比对。用户现阶段无需搬运TB媒体；待对应任务真正需要且无法从公开源取得时，才请求最小文件/授权目录。优先Food2K和VIREO原生标签，而非大规模图像下载。

## 6. 可复现性及归档

本地原始快照（不修改、不复制既有原档）：
- source_data/public_samples/20261125_run001/
- source_data/public_samples/20261125_run002/

本地完整来源及原始文件hash清单在 runs/B0/U1-A/public_samples_001/ 的 NativeAcquisitionManifest_private.json 与 NativeAcquisitionFollowup_private.json。仅以下聚合、脱敏工件入仓库：
- [PublicSampleAudit_shareable.json](../../runs/B0/U1-A/public_samples_001/PublicSampleAudit_shareable.json)
- [PublicSampleAdmissionReceipt.json](../../runs/B0/U1-A/public_samples_001/PublicSampleAdmissionReceipt.json)
- [collect_public_samples.py](../../scripts/udf/b0/collect_public_samples.py)、[collect_public_samples_followup.py](../../scripts/udf/b0/collect_public_samples_followup.py)、[audit_public_samples.py](../../scripts/udf/b0/audit_public_samples.py)

原始图片、标签、个人记录、可能有临时凭据的媒体URL和private manifests不发布。公开聚合manifest只保留必要字段名、计数、hash及不含query的来源URL。HTTP Range/压缩包前缀有限读取、文件级cap与只读验证已经真实执行；不宣称通用生产下载器已通过完整CI、法务或安全验收。镜像源访问与后续使用仍需按许可和源版本治理。

## 7. 总体里程碑

U0 v2.1 已在main；U1 NutriData 25个工作簿原生画像已完成；U1公开样本探索本次17/22目标源、1替代、4HOLD，原始用户22档案未验收；U2 B1核心草案可推进、未冻结；U3-U9未执行。下一步优先利用真实薄切片编写并测试B1 source-native合同，而非等待所有公开媒体数据齐备。
