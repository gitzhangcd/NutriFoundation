# G1-Shared P0.1-A.3｜133-Source Local PDF Vault Verification & Source-Only Freeze

**任务名称**：133 篇原始资料的本机独立核验、可追溯归档与来源级冻结  
**执行主体**：用户本机 Gemini（可调用本机 Python／命令行工具）  
**日期／版本**：2026-10-10 · v0.1  
**执行模式**：先只读扫描（Read-only Audit），后生成旁路报告（Sidecar Reports）；未经批准不改写 PDF、不替换清单、不合并分支。

## 0. 一句话目标与权威边界

> 以真实本地 PDF 文件字节为最高优先级的**文件存在及完整性事实**，对 133 个 SourceArtifact 逐一核验 `文件→SHA256→PDF 结构→所对应的文献身份→实际全文可用性→格式来源及许可→来源版本和相关原件`，产生机器可复核的源文件登记、异常队列、验收报告。**此任务不进行 EvidenceUnit／ScientificClaim 抽取，不生成 Gold，不做 PDF→Markdown 转换，也不开发 UI。**

严格区分：

1. **Bibliographic identity**：书目 DOI/PMID/PMCID 与文献身份正确。
2. **File integrity**：本地文件存在、可读取、字节数与 SHA256 和 Manifest 一致。
3. **Document identity**：PDF 实际内容确实属于上述文献（而不是出版社登录页、摘要、错文、空白打印）。
4. **Document usability**：该 PDF 有足够正文及必要图表，可供下一任务处理；更正通知按其自身预期内容判断。
5. **Native source fidelity**：这是原始出版社/存档 PDF 还是浏览器生成的渲染快照。**没有可信来源链不可声明 Publisher-Native。**
6. **Scientific qualification**：纳入 Gold/验证临床真值，是其他任务负责；**本任务绝不授予该状态**。

## 1. 输入及预期基数

### 1.1 必需文件

- **本地 PDF 根目录**：优先检查实际存在的 `/Users/zhangcd/Codes/Ai-Nutri/data/g1_source_library`；若不存在，必须依据用户给定路径寻找，**不能猜测然后报告缺失**。
- **用户原始 Manifest**：`Archived_Papers_133_Manifest.json`，应原样保留、只读使用。结构：`records[]`，`source_id`、`batch`、`priority`、`title`、`identifiers.pmid/pmcid/doi`、`archive_asset.relative_pdf_path/vault_path/sha256/size_bytes/acquisition_channel/integrity_verified`、来源链接。
- **GitHub 研究分支**：`gitzhangcd/NutriFoundation` → `research/g1-shared-source-library-20261010`，路径 `paper_c/P0/source_library/`，读取：
  - `SourceLibrary_133_Local_PDF_Manifest_v0.1.json`（规范化的 133 来源，**当前为本地声明而非独立验收**）
  - `SourceLibrary_133_Archive_Index_v0.1.csv`
  - `SourceLibrary_133_Reconciliation_and_Readiness_v0.1.md`
  - `SourceLibrary_100_Manifest_v0.1.json`（继承原 100 来源及科学分层）
  - `README.md`
- 可读取 `01_Scientific_World/source_registry/First_100_Source_Pilot_Design_v0.1.md` 作为覆盖目标背景，但**本任务不直接产生 500 EvidenceUnit／300 ScientificClaim**。

### 1.2 既定数值（本机必须重新检查，不可照抄作为运行结论）

| 属性 | 预期 |
|---|---:|
| SourceArtifact 候选 | **133** |
| 最初 100 篇中实际取得 | **97** |
| 本次补充 | **36** |
| 首批未取得 | `CAND-G100-008`、`CAND-G100-089`、`CAND-G100-092` |
| 补充优先级 | `SUPP-G1-001..018=P0`（18）；`SUPP-G1-019..036=P1`（18） |
| 声明的 PDF 字节数合计 | **273,482,647 bytes**（约 260.81 MiB） |
| 有 DOI／PMCID 的条目 | **132／88** |
| 需重新计算 SHA256 | **133/133** |

注意：上一次只做了 **133 条清单身份与摘要元数据一致性**，并未在 ChatGPT 环境读取本机 PDF 二进制。Gemini 不得继承 `integrity_verified:true` 当成本次已执行的事实。

## 2. 必须遵守的执行约束

1. **只读原件**：任何操作不得覆盖、修复、压缩、重新打印、OCR 后替换、修改 PDF 元信息、改变文件名、改变原 SHA256。所有派生检查数据写在单独的 `verification_runs/` 下。
2. **绝不上传受限 PDF 至公共仓库、公共 API 或不明云服务**；本机可用软件执行离线 SHA256、PDF 解析。若 Gemini 运行需要将 PDF 原文发送到远程模型服务，必须先说明具体上传内容、存储及版权风险，并获得用户许可；优先不传正文。
3. **不下载替换文献来偷偷让检测通过**。错误或无权限文件进入 exception queue，原始字节保留。
4. **保留两个目录映射**：`archive_asset.relative_pdf_path`（如 `pdfs/CAND-G100-001_39348690.pdf`）与 `archive_asset.vault_path`（如 `sources/CAND-G100-001/originals/source.pdf`）。实际使用哪个必须写成 `resolved_local_file_path`，不能把目标路径当成存在的文件。
5. **路径安全**：禁止 `../` 穿越；若文件或目录为 symlink，解析后必须仍处于用户许可的 source vault 内；双路径都存在时分别验收并比较字节／SHA；仅一处存在不一定失败，但必须说明。
6. **幂等、可重放**：同一批原件未变情况下再次运行结果应一致；使用独立 `run_id`、UTC 执行时间、工具版本和代码提交哈希；写入采用临时文件 + 原子替换；中断后能按 source_id 恢复。
7. **不用文件大小、文本长度或 DOI 文本出现与否单独推断全文合格**。所有模型判断要有页码及证据摘要；未能确认则标记 `REVIEW_REQUIRED`。
8. **Strict-Blind**：这一来源库是已暴露探索性语料，禁止升格 Paper C 隐藏 Gold100 或输出专家 Gold 真值。

## 3. 六道分层验收 Gate（全部 133 篇逐篇执行）

### Gate G0｜Manifest / provenance 对账（100% 自动）

- 解析 JSON 与 schema 类型；恰好 133 条：首批 97＋补充 36。
- `source_id`、非空 `PMID`、非空 `DOI`、PDF 相对路径及申报 SHA256 均无重复；空 DOI 允许，例如 `CAND-G100-047`。空 PMCID 也允许。
- 与标准化 GitHub JSON 的 PMID／PMCID／DOI／SourceID 配对一致；保留原始声明，不覆写。
- 初始 97 与历史 `Local_97_PDF_Archive_Receipts_Attested_v0.1.json` 的 SHA256／大小／获取渠道一致。
- 校验批次优先级：上传原始 Manifest **全部补充来源误填 P1**；归档报告必须使用 `normalized_priority`：001–018=P0、019–036=P1，并保留原字段 `original_priority` 以说明纠正。
- 旧 97 条的 `source_type="RCT/观察性研究"` 是过于笼统的原始标签；**不得用于文献类型配额统计**。优先使用已有 100-source 候选的 `proposed_stratum`，与实际文献研究类型区分。

**输出**：身份校验日志、源 ID 缺项及重复项、每条 baseline 对照、不可变输入 Manifest SHA256。

### Gate G1｜本机文件存在及 SHA256（100% 自动，关键门禁）

对每个 PDF：

1. 构建并检查候选路径：`<vault_root>/<relative_pdf_path>`、`<vault_root>/<vault_path>`，只允许 vault 内实际路径。
2. 若存在多个候选文件，逐个检查；若两个位置内容不同，标 `PATH_CONTENT_CONFLICT` 并 HOLD，不选择其中任一个覆盖另一个。
3. 检查 `is_file`、有读取权限、大小 `>0`（建议出现异常小于 10 KiB 的文件要复核，不按绝对大小直接 FAIL）。
4. **流式重算 SHA256**（分块读取，不要一次加载全部 133 个 PDF），与 Manifest 的 64 位十六进制 SHA256 精确比较。
5. 实际 `stat().st_size` 与 `size_bytes` 精确比较；记录毫秒级耗时、复核时间、错误码和实际路径。
6. 任何 `SHA_MISMATCH`、`FILE_MISSING`、`SIZE_MISMATCH`、读取权限失败、路径冲突均独立记录，不自动修复或更新基线。

**强制证明字段**：`expected_sha256`、`actual_sha256`、`expected_size_bytes`、`actual_size_bytes`、`resolved_local_file_path`、`symlink_resolution`、`hash_verified_at`。

### Gate G2｜文件格式及 PDF 容器完整性（100% 自动）

- 前导签名 `%PDF-`：PDF header 有效；检查 EOF 结构标记（可存在合法尾随字节，异常应复核而非盲拒）。
- 用 **PyMuPDF（fitz）＋ pypdf 或 qpdf/pdfinfo（可用哪个用哪个）** 检查是否能打开、页数大于零、索引和 cross-reference 是否异常、是否加密、权限或读取错误。
- 每页至少验证对象可访问；抽检首、中、末页可渲染（低分辨率且不改原件）；已报错页需追加高精度定位。可做全页轻量迭代，避免成百 GB 缓存。
- 记录 `page_count`、`pdf_version`、`encrypted`、`pdf_metadata`、`parse_tool_versions`、`render_errors`、`text_chars_per_page`、`pages_without_extractable_text`。
- PDF 可解析但没有文本层：记 `IMAGE_ONLY_OR_OCR_REQUIRED`（警告／待其他任务处理），**不可在来源验收阶段直接 OCR 全库、更不能替换原文件**。
- `CAND-G100-010` 报告有约 **32.16 MB**，属于大体积异常检查样本，应确认它能打开、包含正确论文与有意义的页面，而非下载缓存／截屏；不可仅凭大文件拒收。
- `CAND-G100-083` 是短篇更正通知，约 59.5 KB；不能按常规 RCT 的页数阈值判断文件损坏。

### Gate G3｜真实文献身份及全文可用性（133 篇自动筛查＋问题样本人工复核）

- 对全部 133 篇获取**临时**页文字／PDF 元数据（不导出全文衍生 Markdown），先从第一页、前 3 页查找与 PMID／DOI／标题相关的证据；必要时检查后续页。
- 判断 PDF 是实际文章、出版社原文、PMC 官方 PDF、浏览器打印文章页，还是 **abstract-only、login page、error page、DOI redirect、reference listing**。
- 身份比对采用 `PMID/DOI` 强匹配与标题归一化近似匹配组合；由于 DOI 常只出现于首页且有换行/大小写差异，不得以纯字符串缺失作自动 FAIL。
- 如果 PDF 标题是翻译版本或精简版，应记录差异并 `REVIEW_REQUIRED`；**不能把另一个研究的摘要当完整原文**。
- 检查引言、方法、结果、讨论、参考文献／附录是否有合理迹象；不同文献类型采用不同判断模板：
  - RCT／队列研究：研究设计、样本、方法、结果和必要的表格/图示。
  - 系统综述／Meta／网络 Meta／伞状综述：检索方法、纳排标准、合并结果／异质性、至少一个相应表/图/引用。
  - 指南／共识：推荐条目、范围、适用人群、方法说明；可能无常规 Methods/Results 小节，**不能据此判缺失全文**。
  - 更正／Erratum：短文符合其类型即有效；**必须检查关联原文是否可定位**，但不要求勘误自身有完整 RCT 方法。
  - 执行摘要：只对执行摘要完整性做判断；**不能标为完整版指南**。
  - Secondary analysis：独立文献，需标注 parent-trial 候选关系，不因不同结局判错文。
- 对表格和图像：统计所在页、可视性/渲染错误和可能丢失的页；无需抽取科学表格数据，不调用 MinerU。
- 不确定时只能 `REVIEW_REQUIRED`，要求人工核查首/中/末页缩略图和带页码提示；**不得令 Gemini 凭标题想象 PDF 内容**。

### Gate G4｜Source format provenance & license（133 篇记录、渠道相关深查）

为每份 PDF 按证据分为：

- `PUBLISHER_NATIVE_PDF_VERIFIED`：可信出版社/存档文件及可复查的原件来源链相吻合，**不能仅凭首页出版社 Logo 判定**。
- `REPOSITORY_NATIVE_PDF_VERIFIED`：权威 PMC／机构仓库提供的原始 PDF 二进制及 provenance 可证实。
- `BROWSER_RENDERED_PDF_SNAPSHOT`：HTML 页面通过打印／浏览器渲染形成的 PDF（**可作为阅读资料，但不可冒称 native PDF**）。
- `PDF_SOURCE_UNCERTAIN`：来源渠道、原始下载 URL 或文件谱系不够。
- `NOT_A_FULL_ARTICLE_PDF`：仅摘要、登录页、错误页、目录页等。

依据 `acquisition_channel`（PMC_FULLTEXT_RENDER、AUTHENTICATED_CHROME_BROWSER、PRE_EXISTING、UNPAYWALL、PUBLISHER_OA 等）制定候选分类，但最后必须结合实际文件检查和可靠来源信息，不允许用 channel 直接决定最终分类。

- 若可合法访问官方原 HTML／JATS／PDF 文件：只**登记可获取 URL、内容类型、许可和状态**；**不强制立即下载，也不执行任何格式转换**。
- 若已有本地 HTML／JATS／supplement 原件，可额外清点真实文件并逐份 SHA256；未有不能标为已归档。
- 版权状态使用 `REDISTRIBUTION_ALLOWED / PRIVATE_USE_ONLY / TEXT_MINING_ONLY / LICENSE_UNVERIFIED`，源自可追溯许可文字与 URL；不允许仅有 PMCID 就声明可公开分发。
- 受限 PDF 和浏览器缓存不得上传公共 GitHub，必要日志只包含引用、哈希与相对路径。

### Gate G5｜SourceArtifact family／抽样风险（只做元数据，禁止科学 Gold）

- 按真实论文类型（不是 97 条错误的泛化 `source_type`）整理：指南、共识、Meta、SR、RCT、队列、补充分析、执行摘要、勘误。
- 标记规范版本和发布关系，不能把 **同一 guideline 的全文、executive summary、publisher correction** 记成独立的科学研究。
- 重点记录而**不自动合并**：
  - `SUPP-G1-001`（GLIM 2019）↔ `SUPP-G1-002`（GLIM 2025）。
  - `SUPP-G1-005`（ASPEN refeeding consensus）↔ `SUPP-G1-006`（勘误）。
  - `SUPP-G1-008`（MASLD 全文指南）↔ `SUPP-G1-009`（执行摘要）↔ `SUPP-G1-010`（摘要更正）。
  - `SUPP-G1-020`（ESPEN IBD practical）↔ `SUPP-G1-021`（较新正式指南），不得臆断是完全相同正文。
  - `CAND-G100-007`（CORDIOPREV 随机试验）↔ `CAND-G100-087`（次级分析）；它们是不同 SourceArtifact，可共享 study family。
  - `CAND-G100-099/100` 已有用户报告的 PDF，不能再不加条件地定义为缺失全文案例。
  - `CAND-G100-071` 是营养学会指南的**论文发表版本**，不能因此推断完整 EAL 指南网页和所有附录已获取。
- `First_100_Source_Pilot_Design_v0.1.md` 的六类预期配额是 20 指南、10 共识、25 Meta、10 SR、25 RCT、10 队列。**可输出统计与剩余缺口，不能因为 133 条数目多而直接判断原设计通过**。如一篇具多个标签，优先来源主类型，同时保留多标签及裁定依据。

## 4. 分批执行策略（降低 Gemini 错误和人工负担）

### 阶段 A：只读基线冻结

- 固定输入 JSON 的 SHA256 和运行参数，记录 Python/fitz/pypdf/qpdf 版本。
- 路径发现、133 ID 的集合对账、36 补充标签校正。
- 预先输出 `manifest_baseline_report.json`；如路径不存在，应停止后续文件扫描并报告正确路径需求，**不能将 133 个全部报作 MISSING**。

### 阶段 B：自动化 133 个 PDF 全量核验

- 分批处理（建议 **20–25 篇/批**），内存受控；每次持久化中间结果，可断点恢复。
- 执行 G1、G2、G3 自动筛查；记录唯一 run_id、精确失败点。
- 单个 PDF 出错不得影响其余 132 篇的执行；每个异常写结构化错误码和 traceback 摘要，不写原文完整内容。

### 阶段 C：基于风险的人工／Gemini 辅助复核

- 所有 `FAIL`、`REVIEW_REQUIRED` 必须排入异常队列；此外即便自动 PASS，也要有**至少 24 篇**的分层人工抽检，尽量覆盖各 source 类型、常见 acquisition_channel、大文件、小文件、指南、网络 Meta、勘误、浏览器渲染 PDF。
- 由 Gemini 提供**每篇需要查看的页码和核查问题**；人工对原件页面确认，不可让 Gemini 在无 PDF 图片输入时宣称已完成视觉检查。
- `CAND-G100-010`、`083`、`071`、`099`、`100` 和 GLIM/ASPEN/MASLD 三组文献家族为强制检查对象。
- 抽检最少包含首／中／末页（短于 3 页的公告按全部页），若出现可疑缺页、图片空白、无法复制公式/表格等，追加定位。

### 阶段 D：资料目录冻结（只冻结通过门禁的事实）

- 形成逐篇结果和批次汇总，不改变 `Archived_Papers_133_Manifest.json`。
- 异常一律 `HOLD`／`REVIEW_REQUIRED`，不能为达到通过率修改 PDF 或期望哈希。
- 报告达成率时至少分开：`METADATA_PASS`、`SHA256_PASS`、`PDF_CONTAINER_PASS`、`DOCUMENT_IDENTITY_PASS`、`FULLTEXT_USABILITY_PASS`、`PUBLISHER_NATIVE_VERIFIED`。
- 不得把 `SOURCE_FILE_QA_PASS` 表述为 `SCIENTIFIC_GOLD_PASS`。

## 5. 必须输出的文件（可直接进入其他任务，原件不动）

写到用户本机：

```text
<vault_root>/verification_runs/G1S-133-YYYYMMDDTHHMMSSZ/
  00_run_environment.json
  01_input_manifest_receipt.json
  02_source_pdf_validation_133.jsonl
  03_source_pdf_validation_133.csv
  04_source_file_exceptions.csv
  05_source_artifact_relationships.csv
  06_format_and_rights_inventory.csv
  07_human_visual_review_queue.csv
  08_coverage_and_readiness_summary.json
  09_Acceptance_Report.md
  10_replay_and_test_results.txt
  evidence/                    # 只允许轻量且不侵犯版权的必要审计证据；默认不上 GitHub
```

### 5.1 每条 `02_source_pdf_validation_133.jsonl` 至少包含

```json
{
  "source_id": "CAND-G100-001",
  "batch": "INITIAL_100",
  "pmid": "39348690",
  "doi": "10.7326/M24-0859",
  "priority": "INITIAL_BATCH_UNPRIORITIZED",
  "relative_pdf_path": "pdfs/CAND-G100-001_39348690.pdf",
  "resolved_local_file_path": null,
  "expected_size_bytes": 572111,
  "actual_size_bytes": null,
  "expected_sha256": "095806bb51bde787a0b89a4aefc6bd828ff9a9a874801e2273e6809c0522d70b",
  "actual_sha256": null,
  "exists": null,
  "sha256_match": null,
  "pdf_signature_ok": null,
  "pdf_parse_ok": null,
  "page_count": null,
  "encrypted": null,
  "title_match_status": "NOT_RUN",
  "doi_match_status": "NOT_RUN",
  "document_identity": "NOT_RUN",
  "fulltext_usability": "NOT_RUN",
  "pdf_provenance_class": "PDF_SOURCE_UNCERTAIN",
  "license_status": "LICENSE_UNVERIFIED",
  "page_evidence": [],
  "review_required": null,
  "exception_codes": [],
  "verdict": "NOT_RUN"
}
```

**这里的 `null` 是执行前模板，不是本机检查结果。** 完成后实际字段不得保留 `NOT_RUN` 却同时设置 `PASS`。

### 5.2 异常队列 CSV 必须有字段

`source_id,stage,severity,exception_code,expected,observed,page_number,evidence_note,recommended_action,reviewer,review_status,reviewed_at`

错误码最低覆盖：

- `FILE_MISSING`、`PERMISSION_DENIED`、`PATH_OUTSIDE_VAULT`、`PATH_CONTENT_CONFLICT`
- `SIZE_MISMATCH`、`SHA256_MISMATCH`、`INVALID_PDF_SIGNATURE`、`PDF_UNREADABLE`、`PDF_ENCRYPTED_UNREADABLE`、`RENDER_FAILED`
- `POSSIBLE_WRONG_ARTICLE`、`TITLE_UNCERTAIN`、`DOI_UNCERTAIN`、`ABSTRACT_ONLY`、`LOGIN_OR_ERROR_PAGE`、`POSSIBLE_TRUNCATION`
- `BROWSER_RENDERED_SNAPSHOT`（一般 WARN）、`PUBLISHER_NATIVE_NOT_VERIFIED`（一般 WARN）
- `SUPPLEMENT_OR_GUIDELINE_SOURCE_INCOMPLETE`（WARN/HOLD）
- `SOURCE_FAMILY_REVIEW_REQUIRED`（仅元数据关系）

### 5.3 关键判定枚举（不得混用）

- 逐 Gate：`PASS / FAIL / WARN / REVIEW_REQUIRED / NOT_APPLICABLE / NOT_RUN`。
- 总验收：
  - `ACCEPTED_AS_VERIFIED_LOCAL_PDF`：G0/G1/G2/文献身份通过、未见错误页/摘要替代，报告的用途内可用；不要求一定是出版社原版。
  - `ACCEPTED_AS_RENDERED_SNAPSHOT`：结构正确、全文可读但来源为网页渲染，不得作原生 PDF 证据。
  - `HOLD_FOR_REVIEW`：内容/来源/版本有真实不确定性，需要人工判断。
  - `REJECTED_OR_WRONG_DOCUMENT`：错文件、损坏、权限不可读、哈希不符或非论文正文。
- 可以另设 `NATIVE_FORMAT_VERIFIED`，**必须提供外部可信来源链证据，不能等同于上两项的 PDF 可用性**。

## 6. 本轮验收标准（明确区分是否具备证明）

| 检查项 | 预期判定 |
|---|---|
| 133 SourceID 唯一、97+36、原 97 未漂移 | 133/133 PASS 才能 G0 PASS |
| 全部 PDF 的存在性、大小、实际 SHA256 | **133/133 必须有真实执行结果**；未通过的逐条 HOLD，不伪造总 PASS |
| PDF 容器打开、页数及页面基本可访问 | 所有非缺失原件执行；失败者入 exception queue |
| 实际 PDF 与 PMID/DOI/标题相符 | 所有 133 篇须有状态；不确定＝REVIEW_REQUIRED |
| 原文、摘要/勘误/执行摘要区分 | 所有 133 篇须有状态；各类型专属规则 |
| 原生 PDF vs 浏览器渲染 | 所有 133 篇分类或标记 UNCERTAIN；**不强求全为 native** |
| P0/P1 真实优先级 | 18/18；上传 Manifest 原字段不得覆写 |
| 人工视觉风险抽检 | 至少 24 篇 + 所有自动异常；未完成则不能声称视觉 FULL PASS |
| Source family／更正／版本关系 | 应有候选关联和证据；无法确证须待审，不自动融合 StudyIdentity |
| 133 个 PDF 公开上传 GitHub | **必须为 0**（除非逐文件已确有可公开再分发授权，且另获用户明确同意） |
| 证据抽取／Gold／Workbench／PDF→Markdown | **必须为 0**（另一个任务） |

**停止或回退条件：** vault 根目录无法定位、Manifest 总数错误、未授权联网/上传、准备更改原 PDF、实际 SHA256 与旧值不一致且系统试图自动覆盖；出现这些必须立即 HOLD 并报告。

## 7. 最终向用户返回什么（Gemini 回复模板）

1. **事实表**：133 总数；独立 SHA256 PASS/FAIL；可读 PDF；身份确认；全文可用；浏览器渲染；原生格式独立确认；人工待审；真实缺失数。
2. **明确异常清单**：每条 ID、哪个 Gate、何种证据、推荐怎么解决、是否需要重新下载（**只建议，不直接覆盖**）。
3. **与旧记录差异**：97 条既有文件是否被修改／丢失；新增 36 条是否满足；是否有相同 PDF 保存于双路径。
4. **风险样本**：特别说明 `010 / 071 / 083 / 099 / 100` 和 3 组文献版本关系。
5. **原始 G1 六类覆盖矩阵**：作为科学目标的候选分层核算，注明 `PROVISIONAL`，明确是否仍缺采样类型，不能自动调整研究计划。
6. **文件链接／位置**：上述 11 项 sidecar 报告及其路径，声明原 PDF 未修改。
7. **实际验收状态**：`SOURCE_METADATA_AND_LOCAL_FILE_QA_READY` 或 `HOLD_WITH_EXCEPTIONS`，不得输出研究 Gold 通过。

## 8. 本机执行的建议工具与命令（Gemini 可修改具体实现）

优先使用隔离 Python 虚拟环境，安装 `pymupdf`、`pypdf`（如果依赖不可用，记录并用系统已有工具）；文件哈希用 Python `hashlib.sha256()` 流式计算。**不得 `pip install` 到影响研究系统的全局运行环境**。

先在自己的机器核对：

```bash
# 以下路径是来自此前本地资料库记录的候选路径；若不在该处，请据真实文件调整。
VAULT="$HOME/Codes/Ai-Nutri/data/g1_source_library"
test -d "$VAULT" && echo "vault exists" || echo "CHECK_VAULT_PATH"
find "$VAULT" -type f -name '*.pdf' | wc -l   # 可能有双份拷贝，不能直接当做 SourceArtifact 数
```

真正验收脚本必须**根据 Manifest 的 source_id 一一定位文件**，不能用 `find *.pdf | wc -l == 133` 代替身份检查。对于 `sources/.../originals/source.pdf` 这种预期规范化保存位，即使缺失也只说明该路径未建立；若 `pdfs/ID_PMID.pdf` 真实存在且哈希正确，不得错误地把来源判为 `FILE_MISSING`。

## 9. 权威文件与分支操作边界

- 仓库：`gitzhangcd/NutriFoundation`
- 分支：`research/g1-shared-source-library-20261010`
- 文档落点（如用户许可 GitHub 同步）：`paper_c/P0/source_library/verification_runs/<run_id>/`，**仅可放匿名化元数据、报告和必要的不含原文的证据指针**。
- 不修改 `main`，不覆盖旧 97/133 原始 Manifest、不清空 100-source 历史账本；原件始终在用户本地权限受控库。
- 若有生成代码，放在独立 `tools/source_archive_verifier/` 并记录版本、单元测试及命令，不扩展 Workbench UI、Source-to-Markdown 流水线或 Gold Controller。
- **默认只在本机产出报告**；完成本地核验后先给用户审阅，未经明确授权不做 GitHub push/merge。

## 10. 面向 Gemini 的最终工作原则

**不要以报告形式假装已经核验；必须实际调用本机工具、逐一读取 133 个 PDF 的字节。** 遇到任何无法访问或不确定，请保留不确定性并说明阻碍。优先交付可以重跑、可检查、有异常证据的源资料审计成果，而不是漂亮的“全部通过”总结。