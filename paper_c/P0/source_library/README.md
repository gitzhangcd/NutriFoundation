# G1-Shared｜Scientific Source Library v0.1

> **最新 133-PDF 本地归档快照｜2026-10-10**：用户上传的 `Archived_Papers_133_Manifest.json` 声明 133 篇 PDF 均在本机保存，含原 97 篇和新增 36 篇。GitHub 已分别登记 `SourceLibrary_133_Local_PDF_Manifest_v0.1.json`、`SourceLibrary_133_Archive_Index_v0.1.csv` 和 `SourceLibrary_133_Reconciliation_and_Readiness_v0.1.md`。原 97 份文件的已申报 SHA256/大小/渠道保持不变；新增 36 篇的 PubMed 文献身份一致；纠正 P0/P1 为 18/18。**未上传 PDF 原件，也未独立重算本机 PDF 哈希；不要将旧版 0/100 原始二进制验收计数误读为“本机没有 PDF”。**


**本目录只负责原始文献目录、原始来源文件、版本、授权和文件完整性，不做 PDF→Markdown 转换、知识抽取、专家标注、UI 或 Workbench 适配。**

## 1. 已经实际保存什么

- **100/100**：真实 PubMed 来源书目记录（标题、期刊、发表时间、PMID；其中 99 个 DOI、58 个 PMCID）。
- **100/100**：PMC 版权与自动全文读取状态的初筛；**51** 份允许 PMC 接口进行自动正文获取，剩下 **49** 份需要核对出版社/机构授权或其他获取方式。允许读取不等于允许公开发布。
- **3/100**：此前实际提交 GitHub 的 **CC BY** PMC 正文 Markdown 投影文件：`CAND-G100-004`、`CAND-G100-075`、`CAND-G100-081`。它们属于**衍生文本**，不是原始 PDF、HTML 或 JATS/XML。
- **0/100**：已校验并归档的原始 PDF。
- **0/100**：已校验并归档的原始 HTML。
- **0/100**：已校验并归档的原始 JATS/XML。
- **0/100**：补充文件集合已完整验证。

**没有实际文件的格式不能伪造磁盘路径、文件 SHA256 或文件版本。**

## 2. 三份直接交付

1. `SourceLibrary_100_Manifest_v0.1.json`：100 条完整机器可读来源及每种文件格式的归档状态（最权威）。
2. `SourceLibrary_100_Index.csv`：100 行资料清单，适合筛选、分配获取任务、更新状态。
3. `SourceLibrary_100_Catalog.md`：直接阅读带 PubMed/PMC/DOI 超链接的目录。

既有合法衍生 Markdown 位于 `paper_c/P0/g1_shared_p0_1/source_projections/`，此分支已经继承这 3 份文件。未来的新原件不应沿用 `source_projections` 来混存。

## 3. 每一篇资料的原始来源归档方式

为每个文献（SourceArtifact，不等同于 StudyIdentity）保留相同 `source_id`：

```text
<PRIVATE_SOURCE_VAULT>/G1-Shared/
  sources/
    CAND-G100-004/
      manifest.json                 # 该来源原件级清单与授权
      originals/
        source.pdf                  # 作者/出版社/PMC 提供的原始 PDF
        source.html                 # 原样保存的权威 HTML；不是浏览器转写稿
        source.xml                  # 权威原始 JATS/XML（如能取得）
      supplements/
        supplementary-01.pdf
        source-data-01.xlsx
      derivatives/                  # 供其它任务使用，不应覆盖 originals/
        source.md
      checksums.sha256
```

该结构是**未来私有归档约定**；除上面明示的 3 份既有 Markdown 投影之外，`SourceLibrary_100_Manifest_v0.1.json` 中的目标路径并不表示文件已存在。

### 原件归档最小记录

参考 `Original_Source_File_Receipt_Template_v0.1.json`。

每一个实际取得的文件都必须记录：
`candidate_id`、`format`、`original_download_url`、`canonical_source_page`、`license_or_access_basis`、`retrieved_at`、`file_sha256`、`file_size_bytes`、`storage_reference`、`source_version`、`acquisition_method`、`file_verification`。

若材料是从 HTML 自动转为 Markdown，则标记为 `DERIVED`，并保留其母本 `original_html_sha256` 与转换任务编号。**不能把生成的 Markdown 命名为原生原文。**

## 4. 保存位置与版权边界

- 公开仓库可保存来源目录、DOI/PMID/PMCID、许可说明、哈希、公开可再分发的原文件。
- 机构订阅、非商业限制、禁止演绎、仅允许文本挖掘或版权归属不明确的资料，应保存于**受访问控制的私有源文献库**，GitHub 仅保留无泄露的来源清单及指向私有存储的受控标识。
- PDF、HTML 和 Markdown 应各自独立保存与登记，不能用一个格式代替另一格式。
- DOI 链接、PMCID 页面、附件 URL 只代表可定位的来源，并不等于该文件已下载。
- “来源已保存”必须有真实文件或不可变对象引用及相应校验信息，不能只设置 `status=ARCHIVED`。

## 5. 不属于本任务

- Workbench UI 和 API、专家独立标注页面、双语阅读。
- MinerU、PDF→Markdown／HTML 的格式转换；图表和单元格语义修复。
- Agent 预标注、Gold 裁决与 L1–L4 科学资格审核。
- Paper C Gold100 确认性独立抽样。

这些工作仍在其它研究/工程任务中进行，不回写此库的“原件真实状态”字段。

## 6. 当前验收

`SOURCE_CATALOG_PASS_100 / ORIGINAL_PDF_HTML_XML_ACQUISITION_NOT_COMPLETE`。

**下一步归档工作：** 优先按 51 份 PMC 可自动读取候选进行许可细分和原件获取，再对 49 份来源从出版社/学会/机构渠道取得授权原件。所有格式逐文件保存、逐文件哈希，并维护丢失/拒绝访问原因。
