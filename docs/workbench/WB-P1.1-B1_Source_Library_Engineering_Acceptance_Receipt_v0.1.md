# WB-P1.1-B1｜Scientific Source Library & Source Package Operations

# Engineering Acceptance & Non-Regression Receipt v0.1

> **评定日期**：2026-10-11  
> **权威仓库**：`gitzhangcd/NutriFoundation`  
> **实现分支**：`workbench-p1.1-b1-scientific-source-packages`  
> **PR**：[Draft #32](https://github.com/gitzhangcd/NutriFoundation/pull/32)，base = A5 Draft PR #31（未合并）  
> **工程验收代码 SHA**：`961b5e1d244d4819b7d2e66e78bbbcfbd99ab90b`  
> **评定**：`SYNTHETIC_ENGINEERING_PASS / INDEPENDENT_REVIEW_PENDING`  
> **科学与生产**：`REAL_RESEARCH_NO_GO / GOLD_NOT_ELIGIBLE / NO_MAIN_MERGE`

## 1. 实际完成的 B1 工程能力

```text
Original D0 FastAPI — same auth, CSRF, Origin, Host, SQLite and audit chain
|
+-- /manage#/sources
|   |
|   +-- authoritative EA synthetic source version list (7 original fixtures)
|   +-- source_id/revision_id route deep link + reload/history recovery
|   +-- original Source SHA, source rights, profile and temporal metadata
|   +-- validate synthetic structured-source reference (no write)
|   +-- register immutable SourcePackage reference (Producer only)
|   +-- structure index: unit IDs, ordinal, element kind, UTF-16 length, unit SHA
|   +-- source-lineage and two SHA checks; read-only Manager
|   +-- jump to A5 task center with selected source version
|
+-- /v1/tpa/source-packages (new guarded metadata endpoints)
|   |
|   +-- source reference authority validation — original EA source
|   +-- immutable TPA SQLite tables + triggers
|   +-- same-txn registration, idempotency receipt and TPA hash-chain event
|   +-- exact SHA/profile/rights/lineage recheck on read
|
+-- / (original expert Workbench, unchanged)
    +-- original EA source units, 19-field NDS, PDF.js, source anchors,
        bilingual reader and Strict-Blind gated expert access
```

实现变更仅限原 D0 App 的两个新增 B1 Python 模块、一个安装调用、已存在的 `tpa_p11.js/.css`、B1 测试和 CI，以及 B1 文档。未新增外部 MinerU 服务、未新增科学正文存储、未改 `ea_runtime.py` / `ea_seed.py` / `ea_contract.v0.1.json`。

## 2. 问题关闭与保护性行为

| B1 能力/问题 | 验收 |
|---|---|
| 七类来源库 | 原 `/v1/tpa/sources` 合成来源版本，完整元数据且不含原文 |
| SourcePackage 校验 | 固定 `WB-SOURCE-PACKAGE-v0.1`、`EXISTING_SYNTHETIC_SOURCE`、`SYNTHETIC_FIXTURE_ADAPTER`；Source SHA/Profile/Type/Rights 与 EA 一致 |
| 结构化索引 | 依据 EA 已存来源单位生成 `unit_id / ordinal / UTF16 length / unit_text_sha256`，管理端不出现 `text` |
| SHA 与来源谱系 | `manifest_sha256`、`structure_sha256`；禁止不存在 parent、跨来源 parent、时间上倒置的关系 |
| 不可变登记 | `package_id` 及 `source_id/revision_id` 唯一，SQL 事务登记，UPDATE/DELETE triggers；同键同意图重放返回原始回执 |
| 管理端角色 | 只有 Producer 可 POST 校验/登记；Manager 只读；EA 专家无权限；未登录拒绝 |
| URL 状态 | 来源 ID 与 revision 以正则白名单约束的 URL 参数保存，刷新后回到同一版本，不能凭 URL 越权 |
| 原 D0 非回归 | B1 不要求旧合成任务具有 package；已存在来源、草稿、冻结、工作包、专家判读保持原样 |
| 故障处置 | 回执丢失仅在 Package/Authority/Manifest 精确同一时允许恢复；不能假定网络出错等于数据库回滚 |

**真实性约束**：当前 Package 是“结构化来源引用包”，不是携带 Markdown/HTML 原文的完整解析成果。显示 `SYNTHETIC_REFERENCE_ONLY`，不称作 `SCIENTIFIC_QUALIFIED` 或 `REAL_ADMITTED`。

## 3. 精确代码 SHA 上的真实 GitHub CI

| 验收工作流 | GitHub Actions | 最终结果 |
|---|---|---|
| B1 Python + Native Chromium | [Run 38124859419](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38124859419) | **SUCCESS** |
| B1 第二个独立 push 运行 | [Run 38124856766](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38124856766) | **SUCCESS** |
| 原 A5 管理交互回归 | [Run 38124859450](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38124859450) | **SUCCESS** |
| 原 P1.1-A 运营契约回归 | [Run 38124859417](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38124859417) | **SUCCESS** |
| 原 P1 TPA 管理回归 | [Run 38124859438](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38124859438) | **SUCCESS** |
| 原 EA Expert Annotation D0 回归 | [Run 38124859407](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38124859407) | **SUCCESS** |
| 原 D0 工程验收 + full-engine 回归 | [Run 38124859429](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38124859429) | **SUCCESS**，两个子作业均成功 |

**完整 B1 Python**：`53 passed`，6 warnings（依赖弃用提示）。覆盖结构一致性、权限、身份、伪造父版本、版本哈希、相同请求回执、数据库持久性和全套原 D0 安全用例。

**真实 Chromium**：`93 checks`、`page_errors=[]`、`native_pdfjs=true`、`scientific_capture=false`。包含新增的 5 个 B1 浏览器检查：版本深链接刷新；校验与登记；不可变包刷新读取、结构索引；管理端原文不显示；Manager 仅只读。原工作流由同一测试继续跑过完整生产、冻结、发布、独立专家读取和 NDS R0/R1/R2。

B1 原生浏览器截图：`b1-source-library-synthetic.png`，保存在 [Run 38124859419 浏览器证据包](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38124859419/artifacts/11696678430) 内。这是**合成工程 UI 截图**，不是在线可访问的生产实例。

## 4. 修复记录

第一轮 B1 Python 全部通过；Chromium 初次失败显示来源库登记后“未登记”。逐项诊断确认：**服务器已成功入库，原测试在刷新后失去选中来源版本上下文，切回默认资料**。

修复：URL 保留 `source / revision` 白名单参数并在 reload/hash-history 恢复；另一个管理端测试错误是独立 Manager 会话默认选中其他来源，已改为显式定位已登记的 Source ID + revision。最终在正确的来源上下文下全部 93 项 Chromium 检查通过。没有对失败用例采取跳过或放宽服务器准入。

## 5. 尚未允许的事项

- **真实来源**：真实 PDF/MinerU/OCR/结构化 Markdown/HTML 外部字节导入、来源证据资格、版权/隐私授权和结构全文对齐全部禁止。
- **真实 Agent**：没有真实模型运行、token provenance 或候选预标注链（计划 B2 后续）。
- **真实专家**：只使用合成 EA 测试账号，不能视作资质、伦理、招募、临床真值所有权已审核（B3 / P3）。
- **Gold**：全部包 `scientific_capture=false`、`gold_qualification=NOT_ELIGIBLE`，不能因登记或测试成功而晋升。
- **生产**：未部署服务器，没有公网安全评估，没有真人科学验证，没有把 Draft PR 合并 `main`。

## 6. 下一阶段建议

按 Development Master Plan 的增量路径，建议：

```text
B1 SYNTHETIC_ENGINEERING_PASS
  → B2 Synthetic Agent Preparation Operations & Provenance-Shaped Status
  → B3 Synthetic Expert Roster, Assignment & Exposure-Safe Handoff
  → B4 Integrated Acceptance & Non-Regression Freeze
  → P2 rights-qualified genuine source adapter / MinerU isolation / security GO
  → P3 independent real expert qualification + gold ownership gate
```

**冻结判定**：B1 可作为经 CI 验证的合成工程开发底座供代码审查及 B2 分支继承；但仅限此判定。独立科研和安全审核未完成，PR 保持 Draft。
