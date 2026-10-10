# G1-Shared｜97 篇本地 PDF 归档清单对账报告

**记录日期：** 2026-10-10  
**来源：** 用户上传的 `Archived_Papers_97_Manifest.json`（文件自行报告 `ARCHIVED_VERIFIED`）。  
**验收口径：** `LOCAL_ARCHIVE_REPORTED / METADATA_RECONCILED / PDF_BYTES_NOT_INDEPENDENTLY_VERIFIED`。

## 1. 现有真实结果

- 用户本地报告 **97 个 PDF 文件**，总共 **197,481,888 字节**（约 188.33 MiB）。
- 原 100 条探索性来源中恰好排除 **CAND-G100-008、CAND-G100-089、CAND-G100-092**。其余 **97/97** 与此前 GitHub 100-source 书目目录的四元组 `SourceID/PMID/PMCID/DOI` 对齐。
- 本地 Manifest 给出的 97 个 `source_id`、97 个 PMID、96 个非空 DOI、58 个非空 PMCID、97 个声明的 SHA256 及 97 个相对 PDF 路径均**无重复**。
- 所有 97 条均报告 `format=PDF`、`integrity_verified=true`、文件字节数及 64 位小写十六进制 SHA256。
- **PDF 实际文件没有上传到当前对话**；因此本次不能独立重算文件 SHA256、打开文件判定内容是否为目标文献、核对 PDF 总页数、出版社原件版本或获取合法性。
- 当前 GitHub 仅写入**文件清单和许可无关的哈希/大小/相对路径**，没有上传 PDF 内容或用户本地的绝对主目录路径。

## 2. 获取渠道

| Manifest 记录的获取方式 | 份数 |
|---|---:|
| `PMC_FULLTEXT_RENDER` | 39 |
| `PRE_EXISTING` | 28 |
| `AUTHENTICATED_CHROME_BROWSER` | 16 |
| `USER_MANUAL_DOWNLOAD` | 8 |
| `PMC_OFFICIAL_POW` | 2 |
| `ZOTERO_NUTRITION_COLLECTION` | 2 |
| `CHROME_ACTIVE_TAB_CAPTURED` | 1 |
| `INSTITUTIONAL_IR` | 1 |
| **合计** | **97** |

**注意：** PMC 网页渲染与浏览器打印的 PDF 可以作为可引用的**PDF 版面快照**，但除非独立校验出版社/档案馆原件，不能直接标作 `PUBLISHER_NATIVE_PDF_VERIFIED`。

## 3. 存储状态的定义

| 验收层级 | 当前结果 |
|---|---|
| 用户报告的本地文件存在、已计算 SHA256 | 97/97（由本地 Manifest 陈述） |
| 本次 GitHub 书目身份一致性 | 97/97，通过 |
| 本会话独立读取原始 PDF 文件字节 | 0/97 |
| 本会话独立计算 SHA256 | 0/97 |
| 原版出版社 PDF 证实 | 0/97；未检查 |
| PDF 对应标题/研究的第一页视觉确认 | 0/97；未检查 |
| PDF 补充资料完整性 | 未确认 |
| 原始 HTML/JATS/XML 已在 GitHub 归档 | 0 |
| 原有 CC BY 派生 Markdown | 3 |

**不能混淆：** 来源身份对账通过 ≠ PDF 文件内容验收通过 ≠ 完整 SourceArtifact 保真通过。

## 4. 值得单独标注的边界

- `CAND-G100-099` 和 `CAND-G100-100` 原本属于 `incomplete_or_missing_source_text` 压力分层；用户已报告保存 PDF。以后是否仍能测试“缺失原文”必须单独重新定义，不应简单当作缺失全文案例。
- `CAND-G100-010` 的报告大小约 30.67 MiB（32,157,287 字节）。可能为包含高清图片的版面 PDF 或扫描文件，本身不代表损坏；可优先核查其文本层及对应文献。
- `CAND-G100-083` 只有 59,538 字节，属于更正通知，这一大小不应直接判为错误。
- `CAND-G100-071` 的 PMID 对应期刊精简版指南，不能因保存该 PDF 就推断 Academy EAL 详细正式指南与附件已经完整归档。
- 具有出版社订阅或其他访问限制的 PDF 不应直接纳入公开仓库；可继续只在 GitHub 归档目录与文件摘要，正文留在私有受控位置。
- 确认性 Paper C Gold100 槽位仍然是另外一条独立工作流；本清单是已暴露的 G1-Shared 探索性来源。

## 5. 不再需要做什么

此目录任务**不开发专家 UI，不运行 MinerU，不将 PDF 变 Markdown，不创建 Gold 或 EvidenceUnit**。只负责原始文件保存、身份、版权、大小、哈希、版本及格式清单。

## 6. 后续完成的唯一必需验证

在用户自己的电脑上，以这份 Manifest 与真实 PDF 逐一执行：

`文件存在 → 文件大小匹配 → SHA256 重算一致 → PDF 文件签名有效 → 正文标题/PMID 与文献一致`。

这一步真正通过后，才允许从 `USER_REPORTED_LOCAL_PDF_UNVERIFIED_REMOTE` 晋级到 `LOCAL_PDF_BYTES_REHASHED_AND_IDENTITY_VALIDATED`。不同格式 HTML/JATS/Markdown 日后分别记录，不需覆盖 PDF。

数据文件：`Local_97_PDF_Archive_Receipts_Attested_v0.1.json`（97 记录），`SourceLibrary_100_Manifest_v0.1.json`（100 个来源 + 本地 PDF 97 份状态）。
