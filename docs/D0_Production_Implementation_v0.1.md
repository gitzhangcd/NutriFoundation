---
title: NutriFoundation D0 Production Implementation v0.1
document_class: EXECUTION_IMPLEMENTATION
status: STAGING_IMPLEMENTED_SCIENTIFIC_QUALIFICATION_PENDING
authority_reopen: false
contract_version: D0-production-v0.1
canonical_enabled: false
gold_enabled: false
---

# D0 数据生产执行实现 v0.1

本实现将已提出的扩充方案接成可运行的原件、解析、多结果预填写、字段核验、辅助审查、持久任务和 staging 发布链。继承 D0/D0.1 的资格限制，不重定义上游 EvidenceUnit、Recommendation、ScientificClaim 或 ScientificReferenceState。

## 1. 本轮实现与兼容边界

| 范围 | 实现 |
|---|---|
| 旧文本版本选择 | 修复倒序结果被字典覆盖的问题；支持 snapshot_id/expected_sha256 明确绑定 |
| 原件 | SHA-256 内容寻址；每次获取另记事件；重读检查字节和摘要 |
| 获取 | 本地原件导入；官方 NCBI EFetch 原始 XML 适配器、共享限流、范围及身份检查；真实通道资格另行确认 |
| 日期/类型 | 原始 PubDate、精度和区间；不再把 Clinical Trial 自动等同 RCT；未知分类暂缓 |
| 解析 | JATS/XML、UTF-8 text；段落及表格单元锚点，保留表头、同一行、脚注与 rowspan/colspan |
| 抽取 | 新 PrefillDraft 多结果响应；明确 task/source/parser/authority/model/prompt 版本、覆盖与遗漏 |
| 核验 | 绑定锚点与局部原值；缺项/冲突保留；source-only 独立读出对照，记录执行声明而不认证科学真值 |
| 审查 | 辅助与 source-only 后端投影；离线 HTML、JSON；原始值和字段 patch 分存，决定锁定 |
| 批处理 | 持久队列、幂等键、租约、过期恢复、有界重试、共享 provider 限流、结果事务提交 |
| 缓存 | 原件、解析和首个已接收任务结果复用；新模型/提示词/输入版本产生新任务 |
| 筛选与抽检 | 问题覆盖缺口优先级+随机探索；provider/parser/type/risk 分层随机抽检，保存条件抽样概率 |
| 更新 | 明确依赖图、递归失效、禁止从失效依赖生成新对象；保留既有历史记录 |
| 发布 | SYSTEM_FAITHFUL staging manifest；用途门列出阻断原因；canonical/Gold 保持关闭 |

`src/nutrifoundation/production/` 与 `schemas/production/` 是新的**执行 sidecar**。旧 scientific/evaluation YAML schema、fixtures 和冻结 runs 不修改，不把新草稿强制转换成尚有语义差异的旧 EvidenceUnit。

旧 `produce-evidence`、`ingest-chat-response` 默认不再 F0 冻结。显式 `--legacy-f0` 和既有历史回放入口继续使用 E0.3/E0.4 的机械检查合同。`IndependentEvidenceVerifier.verified` 仍是历史词汇，含义仅为这些旧检查通过；其作用域在返回结果/文档中明确。

旧 ResponseEnvelope 字段白名单仍按旧合同保持。新字段、未知状态及多结果使用 `D0-production-v0.1`，不要向旧协议塞入新字段。F0、D0 canonical、语义评价 CanonicalSemanticForm 和独立 Gold 不互相映射。

## 2. 安装与入口

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/nutri production --help
```

Windows 使用 `.venv\Scripts\` 下对应入口。

导出执行 JSON schema：

```bash
nutri production export-schemas schemas/production
```

所有 CLI、Python 调用、聊天文件导入共用 services；不另外复制一份判定规则。

`production curation-plan` 接收 sources 与 question_gaps，输出优先深抽取与随机探索清单；`production audit-plan` 接收 record/provider/parser/source_type/risk，生成随机分层审计清单和抽样概率。输入相关性与来源分类仍是待核验声明，清单不是科学质量排序或已完成专家审查。

## 3. 原件与解析

```bash
nutri production snapshot /path/to/article.xml PMID36670395 PMC9854100.1 \
  JATS_XML fulltext CC-BY-4.0 --db d0.db --blobs d0_blobs
nutri production parse SNAP_ID --db d0.db
```

snapshot 返回 SNAP_ID，parse 返回 PARSED_ID。原件入口必须标明 content_scope 和 lane；metadata/abstract/fulltext/supplement 不互相冒充。科学来源、个体 observation、食物 grounding、实验数据分开；本阶段不会把 NHANES 个体行转换成经验 EvidenceUnit。

可选的官方原件获取入口：

```bash
nutri production fetch-ncbi PMC9854100 pmc PMID36670395 PMC9854100.1 \
  RIGHTS_TO_BE_CHECKED --db d0.db --blobs d0_blobs
```

环境变量沿用 `NUTRIFOUNDATION_EMAIL`、`NCBI_API_KEY`。HTTP 事件不保存含凭据的 URL/异常字符串。并发进程共享同一个 DB 和相同 provider 配额标识；跨主机分散数据库不能保证全局限流。license 参数是输入声明，不是适配器自动完成的许可审计。

JATS parser 保留物理 table cell 与多级表头，不自动声称 colspan/rowspan 的列语义已经正确解析；语义 worker/审查仍需核对。PDF/OCR、HTML、XPT 可保存原件，尚无本合同下合格 parser，调用解析时会明确暂缓。

## 4. 新预填写任务与 worker

```bash
nutri production prepare SNAP_ID PARSED_ID AUTHORITY_SHA256 \
  extractor-A MODEL_VERSION PROMPT_VERSION 'Table 3 models and outcomes' --db d0.db
nutri production enqueue TASK_ID --db d0.db
nutri production work-one 'python /path/to/my_worker.py' --db d0.db
nutri production jobs --db d0.db
```

worker 从 stdin 接收 task、task_sha256、parsed_document、response_schema、rules，stdout 返回一个完整 `PrefillDraft` JSON。具体厂商 API 保持在外部 worker 内，核心服务不要求 API 凭据。也可导出 task/parsed records 在聊天窗口完成，再用：

```bash
nutri production ingest-draft /path/to/response.json --db d0.db
```

`budget_tokens` 传给 worker；厂商侧 token 限额、实际使用量与价格必须由其 adapter 真实执行和回报，本核心不虚报成本或已执行 token 限额。核心提供进程超时、响应体上限和任务最大尝试次数。

覆盖声明与遗漏是必填项，不以“返回了30个结果”假定全文已完整抽取。一篇论文多结果共享 source/task 上下文；每个结果的模型、结局、单位、评分增量、参照、调整与脚注仍分别记录。

## 5. 字段核验与独立读出

每个 `FieldAssertion` 包含 state、source_value、normalized_value、anchor_refs、reason。unknown、源未报告、未取得原件、抽取失败和不适用分开。非 PRESENT 必须说明原因；不能以它代替用途所需作用域。

```bash
nutri production verify DRAFT_ID --db d0.db
nutri production verify DRAFT_ID --readout /path/to/locked_readout.json --db d0.db
```

一个数字出现在全文不算语义支持：原值必须位于所绑定的局部 anchor；模型/结局/单位对应关系还需独立读出。未提供合格读出时报告 UNRESOLVED。规范化值发生转换时也保持待核验，本版不隐式猜测单位、比例、因果方向。

`IndependentReadout` 绑定 task、source、parsed digest、worker/session、source-only 输入范围与锁定时间。`ATTESTED_EXECUTION_ONLY` 仅记录执行声明，不证明模型的认知独立或人的专业资格；同一受污染会话更换身份字符串不能产生科学独立性。本地研究代码不能认证用户自报资格，正式资格记录仍需项目流程。

## 6. 审查与修改回传

辅助审查：

```bash
nutri production export-review DRAFT_ID REVIEWER_ID review.html --db d0.db
```

同目录输出 `review.source.xml` 等原件。HTML 展示字段、候选值、原文、表头/行/脚注；修改或标记未解决时必须填写原因。下载 JSON 不等于提交、签署资格或晋升。

```bash
nutri production submit-review downloaded-decision.json --db d0.db
nutri production apply-review DECISION_ID NEW_DRAFT_ID --db d0.db
```

每个任务只接收一个锁定决定。修改创建新草稿版本，不覆盖机器原值，也不继承旧 verification。未解决/暂缓决定被保存；需要更新候选时另作有理由的 REVISE。源内冲突不会因为改了一个字段而自动关闭。

独立读出使用带原件的 allowlist ZIP 空白包：

```bash
nutri production export-review DRAFT_ID REVIEWER_A reviewer-A.zip \
  --mode source_only --db d0.db
```

source-only 投影不包含候选答案、锚点选择、核验结论、冲突提示或另一审查者答案，附带同一原件。独立审查者填写 `independent_results` 而不是 patch 未见候选。source-only 不允许生成带机器预填写的 HTML。

仅分发生成的 source-only ZIP；不要把同时存有辅助审查文件的整个输出目录交给独立审查者。ZIP 按显式 allowlist 构建，不收集目录中的其他文件。

本版是可信本地协调者使用的 CLI/离线文件工作流，**尚无多用户认证、授权服务器或在线电子签名**。不要把通用 ProductionStore/CLI 直接暴露为公网接口；将来上线时需要独立权限服务和访问审计。已经看过预填写的记录只能标 assisted。

## 7. 发布门与历史状态

```bash
nutri production promotion-gates DRAFT_ID VERIFICATION_ID --use canonical --db d0.db
nutri production invalidate SNAP_ID 'correction acquired' --db d0.db
```

canonical/Gold 门返回 `allowed=false` 与具体理由，包括字段作用域、独立核验、authority/schema reconciliation 和 H0/专家发布资格。用户或模型不能通过提交一个 true 布尔值开放发布。

```bash
nutri production release-staging RELEASE_ID DRAFT_ID \
  --cutoff 2026-10-05T02:00:00Z --mode SYSTEM_FAITHFUL --db d0.db
```

cutoff 必须有时区，成员必须在该时点已入库；新 release 排除已失效依赖，旧 manifest 保留。CONTENT_FAITHFUL 尚缺正式公开可用时间绑定，会明确拒绝，不借用入库时间。该 staging manifest 不是已经核验和晋升的历史 ScientificReferenceState。

## 8. B002-S1-001 实际集成

```bash
python scripts/run_d0_b002_pilot.py \
  --source-pack /path/to/NutriFoundation_D0_2_1_B002_S1_001_v1.0 \
  --authority /path/to/Unified_Master_v1.0.md \
  --out /path/to/d0-pilot-output
```

本次实际结果：既有 89 个锚点中 86 个 XML 锚点重放；新 parser 306 个锚点重放；30 个 Table3 结果进入 staging。摘要/正文/表格 OR/P 差异和评分增量/参照类别缺项保留，0 次模型调用、0 位专家提交、0 次 canonical/Gold。

这里是导入 prior nonblind staging 并验证原件/锚点，不是重新独立抽取。其余 3 个历史锚点不在本脚本 XML 重放范围。真实 pilot pack 不写入仓库，运行时自行指定路径；测试用人工构造输入与真实来源分开。

## 9. 验证与仍待资格化的部分

```bash
python -m pytest -q
git diff --check
```

新增测试覆盖旧版本选择、默认草稿、日期与分类、模型/结局/单位/anchor 负例、多结果、读出暴露、修改留痕、source-only 隔离、命令 worker、缓存、并发领取、陈旧 lease、重试和事务回滚、原件破坏、依赖失效、历史 cutoff、观察输入隔离及凭据日志。

冻结 A2.8 的四项基线失败来自 Python 3.12 `sum` 与原 Python 3.11 的浮点末位差异。v0.1 runner 使用明确逐项加法复现历史运算；不改冻结输出、参考答案或评分标准。

离线页面已通过生成/导出/合同/脚本转义测试。实际 Chromium 渲染/交互验证未完成：当前环境没有 browser binary，下载包无法解压；不宣称视觉或浏览器 QA 通过。

尚待真实资格与测量：

- source/provider/parser/用途分层的真人独立审计及严重错误率；
- H0 的限定范围与批准，不由技术测试代替；
- 专家资质、正式裁定与 Gold，当前为零；
- 新模型 worker 的真实抽取质量、token/费用及加速测量；
- PDF/OCR/HTML/XPT/指南特定 adapter 与归一化资格；
- 大规模负载、依据真实审计标签的加权质量估计、研究依赖分组和生产吞吐基准；
- 多用户在线工作台、认证/授权、PostgreSQL/分布式部署，仅在实测瓶颈和真实需求出现后迁移。

这些资格限制不会阻止现在批量生成、核查和交接 staging 数据；也不会被本轮工程测试悄悄关闭。
