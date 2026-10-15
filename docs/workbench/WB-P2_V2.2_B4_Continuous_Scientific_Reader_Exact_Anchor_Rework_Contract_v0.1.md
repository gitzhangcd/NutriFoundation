# WB-P2-V2.2-B4｜连续科学阅读、精确证据锚点与不可变 QA 返工交接 v0.1

> 2026-10-15 · PR #48 合成工程分支。本文属 Workbench L2 工程契约，不替代 PR #46 GOV-0.4 科学规范审计与任何 Frozen SIS/NDS/NDF 科学权威。  
> Gate: **SYNTHETIC_ONLY / CURATOR_ORIGINAL_ISOLATED / NO_REAL_PDF / NO_GOLD / NO_EXPERT_GRANT / NO_DEPLOYMENT_CLAIM**。  
> 发布、正式数据权利、真实专家、临床科学规范符合性须独立签署。

## 1. 功能与身份边界

B3/V2.1 完成受控合成生命周期，B4 只补“可连续读、可精确核验、可按权限返工”：

- 主阅读器按服务端已 SHA 校验的 Canonical Document IR **原序**连续显示 Unit，包含标题、普通段落、表格单元、脚注和图表说明。受控合成 Markdown 原件可展开查看，但**原件字节偏移 ≠ Document IR UTF-16 offset**。
- 辅助中文译文仅显示人工 Curator 已签署的独立 sidecar，随 Unit 关联，可随时隐藏。译文不得代替 source quote 或在 Strict-Blind/R0 任务中隐式投影。
- 按 Unit 目录双向定位，全文与译文检索仅导航、不生成证据，不隐式触发 QA；初始加载 35 Unit，后续每次增加 35；不以目录数量暗示页面 BBox 已核验。
- 原文拖选限**同一 Canonical Unit**（`data-v2-text`）内，使用浏览器 Range 计算原生 JS 字符串 UTF-16 索引；`[start_utf16,end_utf16)`，跨 Unit/跨译文选区立即拒绝。无选区时明确使用**Unit 全文锚点**。
- UI 中候选高亮标记不能被解读为正式签署。提交前重新计算完整 Unit SHA 与选定 Quote SHA，并附准确 offset、UnitID、Document rev、PDF Locator 状态交给现有 `POST /v1/p2/sources/{id}/{rev}/qa`；只有后端独立 Curator 不可变 receipt 才能称“已审核”。
- Curator 的 `GET .../reviews` 仅回读已签署的 UnitID、Decision、Reviewer、start/end、Quote SHA、Document SHA、PDF Locator，不回传 Source Quote。Curator 结合角色隔离的 Document IR 可重建并再次高亮原锚点；Manager/Producer/Auditor 对此 GET 仍 403。
- REJECT 的原始 `findings.notes` 是 Curator 私有备注，可能含敏感原文；不得传给 Producer 或公开 GitHub。

## 2. Least-Privilege Immutable Rework Handoff

新增只读 `GET /v1/p2/sources/{id}/{rev}/rework`：

| 字段 | 允许内容 | 不允许内容 |
|---|---|---|
| `source_id, revision_id, source_status` | 精确服务器版本状态 | 自动替换其他修订 |
| `issues[]` | `unit_id`, `reason_code`, `issue_ref`, `resolution=NEW_REVISION_REQUIRED`, `immutable=true` | 原文、quote、自由文本备注、译文正文 |
| `reason_code` | 受控类别：STRUCTURE_GAP、NUMERIC_MISMATCH、ANCHOR_MISMATCH、OMITTED_CONTENT、TRANSLATION_DISCREPANCY、OTHER | 用户自填自由文本直通 Producer |
| `issue_ref` | SourceVersion、UnitID 与固定 REJECT 决策标签等非敏感不可变标识的 SHA-256（不哈希原文或自由备注） | 可还原原文的摘要字段拼接 |
| 响应资格 | `synthetic_only=true`, `original_text_exposed=false`, `expert_exposure_authorized=false` | 正式证据/Gold/专家授权 |

- 仅 **Producer/Curator** 能 GET 返工摘要；Manager、Auditor、EA Expert/Agent 返回 403。Producer 对 `/original`、`/document`、`/reviews` 仍无权。
- 返工列表从现有不可变 `p2_reviews` 计算，不建立可修改的第二套 Issue 状态机；旧版本 REJECT/QA_HOLD、原 Raw SHA 和 Document SHA 不可覆盖。
- Producer 必须显式提供**新的合成原文**生成 `r2`，并走独立 Auditor 再审、Parser、Curator 全 Unit QA、Producer Freeze。可选 UnitID 仅用于问题分类定位，不代表 Producer 获得 Curator 原文访问。
- Audit 和 `SourcePackage` 仍采用原权威 append-only 事件链及冻结机制。受控类别无法全面表达返工原因是当前刻意的安全边界；复杂情况需要另行签署更细的授权交接通道，不能静默披露自由文本。

## 3. E2E / Kill Tests

| Gate | 测试对象 | 必须满足 |
|---|---|---|
| B4-K01 | 连续 Curator 阅读 | 至少多 Unit 连续可见，不是单段伪全文；目录与主文双向定位 |
| B4-K02 | 双语辅助层 | 人工译文与正确 Unit 绑定；可关/开；仅辅助 |
| B4-K03 | 精确 Unicode/UTF-16 锚点 | 只允许同 Unit 源文本；非跨 Unit、非译文；后端 Quote SHA/Offsets 一致 |
| B4-K04 | Browser review readback | 已签署 Offset、Quote SHA 和 Canonical Doc SHA 刷新后仍可复核，不返回 Source Quote |
| B4-K05 | REJECT 与脱敏返工 | Producer 可得到 `NUMERIC_MISMATCH` 等类别和不可变 Issue ID；不能看到 Curator 内部备注/原文 |
| B4-K06 | 不可变修订 | `r1` REJECT 无法冻包；`r2` 独立重新审核；旧 Raw SHA 及审计链保持不变 |
| B4-K07 | 390px/1440px | 连续阅读、目录和 QA 面板适配，页面不横向溢出；保留视觉风格 |
| B4-K08 | 严格权限与登出 | Manager/Producer/Auditor 对 Original/Document/Reviews 无权，Producer 才可读脱敏 Rework；Curator logout DOM 清除 |
| B4-K09 | Protected Normative Paths | 不修改 Frozen `runs/**`、`src/nutrifoundation/**`、EA/TPA 权威，不新授任何权限；9/9 workflow exact SHA |
| B4-K10 | GOV-0.4 / C / D / E | 真实 PDF BBox、MinerU、安全上传、SIS R5/SIS-MED R6 精确原件与 AI Nutri v2.1 Adapter 仍 NO-GO/PENDING |

测试目录：`apps/workbench/d0/tests/test_p2_source_studio.py`（API / 角色与旧版拒绝），`apps/workbench/d0/tests/browser_d0.py`（真实 Chromium 多角色、拖选、译文、返工、390px 截图与回读）。

## 4. Master Tracker 与发布判定

- Master Tracker Issue #42：A 5/5，B 2/5，C/D/E 0/5 = **7/25 已正式签署工程里程碑**，本 PR 的 B4 增量不自动新增计数；B3 的独立验收/正式关账先行，B4 还需全部 exact-head CI + 独立 UX，B5 需人工视觉/可用性。
- PR #46 GOV-0.4 是**静态语义审计**，目标 SIS R5、SIS-MED R6 P0.4 精确原件及 AI Nutri v2.1 Adapter 尚缺，NDF/NDS 案例兼容性仍待 scientific owner 裁决。不可用 V2 内硬编码的 15 轴表替代 executable conformance。
- **本次属于代码实现与工程测试**。不得因 GitHub 单组 PASS 即宣称正式用户验收、真实资料/专家/Gold 或部署通过。PR #48 保持 Draft；不自动合并 main。
