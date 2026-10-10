# G1-Shared｜133 篇本地 PDF 资料库：身份对账与文献清单验收 v0.1

**日期：2026-10-10**

**记录性质：** 用户提供的本地 PDF 文件 Manifest；当前 GitHub 仅记录元数据与文件摘要，**不保存上传 PDF 正文**。

## 1. 本轮实际对账结果

| 指标 | 核验值 |
|---|---:|
| 用户申报的 PDF | **133** |
| 原 100 候选中已下载 | 97 |
| 按上一轮下载清单新增 | 36 |
| 原有三条未下载（008、089、092） | 3 |
| 已有 97 的 SHA256、大小、获取渠道逐条与旧仓库登记吻合 | **97/97** |
| 新增 36 与 PubMed PMID、DOI、PMCID、题名一致 | **36/36** |
| 重复 source_id / PMID / 报告的 SHA256 / 相对文件路径 | **0** |
| 有 DOI | **132/133** |
| 有 PMCID | **88/133** |
| 用户申报的总文件大小 | **273,482,647 bytes（260.81 MiB）** |
| 本会话直接访问 PDF 文件字节并独立重算 SHA256 | **0/133** |
| PDF 是否为出版社原版、全文结构是否完整 | 未检验 |

**严格的验收用词：** `133_USER_ATTESTED_LOCAL_PDF / BIBLIOGRAPHY_MATCH_PASS / NATIVE_FILE_BYTES_NOT_VERIFIED`。

与此前 97-source 登记相比，原有 SHA256 和大小全部一致；新增 36 条不与先前 97 条重复。仍存在同一研究／同一规范的不同发表版本，应当作为不同 SourceArtifact 保存，但不能据此计算 133 项独立研究。

## 2. 已校正的两项上传元数据错误

1. 上传文件把 **SUPP-G1-001..036 全部标为 P1**，但此前下载决策清单明确指定 **SUPP-G1-001..018 为 P0（18 条）**、**019..036 为 P1（18 条）**。规范化库保留 `original_user_priority` 与 `normalized_priority`，不更改上传的原始记录。
2. 上传文件中 36 条补充文献的 `journal` 和 `publication_date` 均为空，规范化清单按原 PMID 从 **PubMed** 补齐 36 条。原 97 条的 `source_type` 全写成 `RCT/观察性研究`；规范化库改用原 `SourceLibrary_100_Manifest` 中的初拟 scientific stratum，不因此宣称经过科学质量审核。

新增 36 的 PubMed 身份字段均无不一致事件，未自动修改 DOI 或标题。

## 3. 格式和来源的真实边界

- 所有 133 篇都在上传清单中标记 `ARCHIVED`、`integrity_verified: true`、并记录 PDF SHA256。这是**本地工具／用户的声明**，本会话没有实际 PDF 文件，所以不能说本次独立复核了文件字节。
- 存在 PMC 正文渲染、浏览器捕获、Publisher OA、Unpaywall、本地预存等获取渠道。**有 PDF 文件 ≠ 原始出版社 PDF**，尤其是网页另存为 PDF 的材料，后续必须加 `PDF_RENDERED_SNAPSHOT` 一类格式来源标记。
- 没有检查 133 篇的补充材料、原生 HTML/JATS、图表、表格、页面完整性或版权授权。只用文献清单无法通过上述门禁。
- 一些来源是指南、共识、执行摘要、正式更正或次级分析，不能当作彼此独立的 RCT 或科研证据。
- 不应将受版权保护的 PDF 放入公开 GitHub；保留在本地／私有源文件库，GitHub 仅跟踪来源引用与摘要。
- Paper C Gold100 不在本次资料库工作范围。

## 4. 两个特别保留的测试边界

- `CAND-G100-099`、`100` 原设计为“全文不易获得”的 stress 来源，本轮和上一轮均报告已有 PDF；不能继续把这两篇视为现实中只有摘要的案例。若希望测试 abstract-only，应构造独立的受控可见性条件或另选真实缺失全文的来源。
- 原始 `First_100_Source_Pilot_Design_v0.1` 的六类配额（20 指南／10 共识／25 Meta／10 SR／25 RCT／10 队列）**未因拥有 133 条文献就自动宣告满足**。必须先统一实际文献类型并按设计配额筛选，区分 SourceArtifact 与 StudyIdentity。

## 5. 科学使用建议

当前数量与异质性**足以启动来源获取、版本关系、格式保真及来源结构原件核验的第一轮开发测试**。不需要继续只为增加数量下载更多相似论文。

首先在用户本机执行 133 个实际 PDF 的 `存在性 → 大小 → SHA256 → PDF 签名 → 标题/PMID 与全文对应` 复核；再单独收集原始 HTML／JATS、supplement 和规范文件版本信息。真正的科学证据单位、StudyIdentity、指南权威和专家 Gold 不在本工作包自动生成。

## 6. 本阶段产物

- [133-source JSON 归档主清单](https://github.com/gitzhangcd/NutriFoundation/blob/research/g1-shared-source-library-20261010/paper_c/P0/source_library/SourceLibrary_133_Local_PDF_Manifest_v0.1.json)
- [133-source CSV 索引](https://github.com/gitzhangcd/NutriFoundation/blob/research/g1-shared-source-library-20261010/paper_c/P0/source_library/SourceLibrary_133_Archive_Index_v0.1.csv)
- [原 100-source 权威候选目录](https://github.com/gitzhangcd/NutriFoundation/blob/research/g1-shared-source-library-20261010/paper_c/P0/source_library/SourceLibrary_100_Manifest_v0.1.json)（未覆盖）
- [原 97 PDF 入库声明](https://github.com/gitzhangcd/NutriFoundation/blob/research/g1-shared-source-library-20261010/paper_c/P0/source_library/Local_97_PDF_Archive_Receipts_Attested_v0.1.json)（保留）

本阶段不做 Workbench UI、不做 PDF→Markdown 转换、不合并到 main。
