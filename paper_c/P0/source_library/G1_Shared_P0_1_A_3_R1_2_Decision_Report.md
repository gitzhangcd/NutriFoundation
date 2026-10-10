# NutriFoundation｜G1-Shared P0.1-A.3-R1.2
# 生产核验器重构、负向控制复审与来源资产独立资格化裁决书

> **报告执行 Run ID**：`G1S-133-R1-2-VALIDATOR-REQUALIFICATION-20261010T070815Z`  
> **执行时间**：`2026-10-10T07:08:15.405872+00:00`  
> **核验规则版本**：`v1.2-canonical-multidimensional`  
> **执行工程师**：NutriFoundation 独立科学资料库验收工程师（Gemini 本机实证环境）  
> **总体裁决状态**：**`HOLD_WITH_EXCEPTIONS`**（明确声明：`NOT_GRANTED_BY_THIS_AUDIT`）  

---

## 一、Gate 级分层裁决大表（100% 数据动态聚合，无硬编码）

| 验收门禁 (Gate) | 检验范围 | 实证裁决 | PASS / 确认 | 待审 / 隔离 (HOLD) | 严格证据标准与真实检验结论 |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Gate G0: Manifest 账本** | 133 条清单 | **PASS** | 133 | 0 | 账本 SourceID/PMID/DOI 零重复，哈希基线固化无篡改 |
| **Gate G1: 文件真实与 SHA256** | 133 个本地文件 | **PASS** | **133** | 0 | 64KB 分块流式重算，与申报值 100% 精确匹配，双路径一致 |
| **Gate G2: PDF 容器可读性** | 133 个 PDF 容器 | **PASS** | **133** | 0 | PyMuPDF 与 pypdf 双解析器交叉核验通过，首中末页抽检渲染 100% 成功 |
| **Gate G3: 身份资格重定** | 133 篇实际文献 | **HOLD** | **CONFIRMED: 127**<br>**PROBABLE: 0** | **HOLD: 3**<br>**MISMATCH: 3** | 单一规范核验器执行：防范 DOI 假阳性与词汇散落，3 篇资产错配与手稿版本严格隔离 |
| **Gate G4: 来源 Provenance** | 133 篇来源链 | **HOLD** | 16 | **117** | 格式特征与来源证明彻底解耦；117 篇保持 `UNVERIFIED` |
| **Gate G4: 版权与分发权限** | 133 篇版权状态 | **HOLD** | 0 | **133** | 解除错配资产许可继承；除政府公有领域外，133 篇严格保持 `UNVERIFIED` |
| **Gate G5: 科学研究类型** | 133 篇研究分层 | **HOLD** | 0 | **133** | 18 条审计冲突条目隔离，全量 133 篇保持 `PROVISIONAL`，未授予 Scientific Gold |
| **HUMAN_REVIEW: 人工审核** | 34 篇复核队列 | **PENDING** | **0** | **34** | **实事求是声明：当前 0 篇有人类签名完成，34 篇处于 PENDING，已纠正越界页码** |

---

## 二、六类核心负向控制测试结果 (NC-01 ~ NC-06)

针对 ChatGPT 报告指出的 RA-01 ~ RA-04 严重漏洞，本次研发的单一规范核验器 `evaluate_pdf_identity_canonical` 在生产与测试中 100% 共享调用，实测 6 类杀伤性用例通过率 **100%**：

1. **NC-01 (DOI in References Only)**: **PASS** (返回 `HOLD / DOI_IN_REFERENCES_ONLY`)。文档第一页无关论文引用了目标 DOI，生产函数成功拒绝放行。
2. **NC-02 (Dispersed Keywords Only)**: **PASS** (返回 `HOLD / DISPERSED_KEYWORDS_REJECTED`)。页面散落词汇表中出现目标标题单词，生产函数成功识别缺乏连续性并拒绝放行。
3. **NC-03 (CAND-G100-090 Wrong PDF)**: **PASS** (返回 `HOLD / INSUFFICIENT_EVIDENCE`)。彻底移除 SourceID 硬编码特例，当传入无关 PDF 时坚决返回 HOLD。
4. **NC-04 (True Positive Grounded)**: **PASS** (返回 `CONFIRMED / CONFIRMED_TITLE_AND_DOI_GROUNDED`)。真实标题与协同 DOI 在头部区域命中。
5. **NC-05 (DOI Title Conflict)**: **PASS** (返回 `HOLD / CONFLICTING_DOI_DETECTED`)。PDF 中存在外来冲突 DOI 且标题不符，坚决返回 HOLD。
6. **NC-06 (No DOI Valid Source)**: **PASS** (返回 `CONFIRMED / CONFIRMED_TITLE_NO_DOI_REQUIRED`)。无 DOI 合法文献在首页连续短语 100% 吻合时安全确认。

---

## 三、重大资产错配与异常事件台账

1. **三项重大资产错配（维持 `HOLD / MISMATCH`，必须重新获取正确原文）**：
   - **`CAND-G100-010`**：申报为 JAMA Low-Carb RCT，实测为美国膳食指南全本 (164p/32.16MB)；
   - **`CAND-G100-019`**：申报为 JAMA AI-Powered RCT，实测为 CDC DPRP 运营标准规范 (52p/1.92MB)；
   - **`SUPP-G1-017`**：申报为 BMJ 2024 全因死亡率队列，实测为 JACC Adv. MESA 心血管风险研究 (11p)。
2. **一项手稿版本争议（维持 `HOLD / VERSION_VARIANT_REVIEW`）**：
   - **`CAND-G100-020`**：PLIS 试验作者手稿排版版 (31p/1.38MB)，待方法学审查仲裁。
3. **一项投稿审查表单缺失正文（维持 `HOLD / CONTENT_PARTIAL`）**：
   - **`CAND-G100-014`**：本地文件为 63 页 CONSORT-EHEALTH 投稿表单，非发表论文全文。
4. **一项规范核验通过项（`CAND-G100-090`）**：
   - 移除代码特例后，由通用算法在真实文件第 1 页完整提取到连续标题，安全进入复审。
5. **18 条研究设计冲突文献**：
   - 包含 `CAND-G100-014` 等 18 条，全数转入方法学隔离表 `08`，标为 `PROVISIONAL`。

---

## 四、ChatGPT 审计发现 RA-01 ~ RA-11 逐项处置表

详见配套交付文件 [`11_issues_RA01_to_RA11_disposition.csv`](file:///Users/zhangcd/Codes/Ai-Nutri/data/g1_source_library/verification_runs/G1S-133-R1-2-VALIDATOR-REQUALIFICATION-20261010T070815Z/11_issues_RA01_to_RA11_disposition.csv)，11 项审计缺陷均已在 R1.2 中落实代码闭环。

---

## 五、交付物与 ZIP 证据包清单

成果位于目录：`/Users/zhangcd/Codes/Ai-Nutri/data/g1_source_library/verification_runs/G1S-133-R1-2-VALIDATOR-REQUALIFICATION-20261010T070815Z`
- `00_environment_and_git_state.json`
- `01_original_inputs_sha256_manifest.json`
- `02_G1_byte_and_G2_container_replay.jsonl`
- `03_G3_identity_requalification_133.jsonl`
- `04_G3_negative_control_suite_results.jsonl`
- `05_G3_r11_to_r12_delta.csv`
- `06_G4_acquisition_provenance_evidence.csv`
- `07_G4_rights_asset_identity_mapping.csv`
- `08_G5_study_type_quarantine.csv`
- `09_human_review_queue_and_signatures.csv`
- `10_gate_reasoned_verdicts.json`
- `11_issues_RA01_to_RA11_disposition.csv`
- `12_actual_test_commands_logs_exit_codes.txt`
- `13_run_integrity_manifest.json`
- `r1_independent_replay_verifier.py`
- `test_r1_replay.py`
- **`R1_2_Independent_Audit_Package.zip`**
