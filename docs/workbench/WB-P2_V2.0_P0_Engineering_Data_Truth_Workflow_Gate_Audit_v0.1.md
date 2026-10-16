# WB-P2-V2.0-P0｜工程基线、数据真实性与合成流程闭环审计 v0.1

> 2026-10-15 · Audit scope: PR #48 / `cursor/scientific-source-hifi-v1-6d14`，基线 commit `d2cd0b967f875b09919588984993aff476fed372`；本报告与 P0 修复一起版本化提交于 PR #48。
>
> **Disposition: P0 CODE REMEDIATION / REVERIFY EXACT HEAD CI / FULL V2 WORKFLOW NOT YET CLOSED / REAL_SOURCE_NO_GO / GOLD_NO_GO / EXPERT_NO_GO**
>
> This is not a release receipt, cloud deployment inspection or pixel-fidelity approval. Existing D0 P2 source authority, role gates and all original frozen scientific contracts remain normative.

## 1. 本轮基线证据和性质

PR #48 是 PR #47 之上的 Draft PR，新增 `#/studio-v2`、`p2_source_studio_v2.js/css`，但实际差异也包括现有 `p2_source_studio.js/css`、`p2_source_portal.js`、管理路由与浏览器用例，不能认定“旧页面代码完全不变”。

基线 `d2cd0b9` 的 GitHub Actions：**1/9 PASS（EA）；8/9 FAIL**。失败归因不是九项独立科学失败：
- 多个浏览器工作流复用 `apps/workbench/d0/tests/browser_d0.py`，在旧的 `#p11Nav` “8 个入口”断言处失败；新增 V2 入口后应为 9。必须同时断言旧科学资料、隐藏 B1 和新增 V2 均存在，不能简单跳过断言。
- `.github/workflows/wb-p1-1-b4.yml` 原有精确文件 allowlist 未包含 `p2_source_studio_v2.js/css`。本轮只允许这两个 V2 文件，并增加 Node syntax check；冻结的 `runs/`、`src/nutrifoundation/`、EA 等禁止路径仍拒绝。
- 在浏览器 E2E 提前阻断时，不能依据 Python engine/test PASS 推断全部 UI/权限回归 PASS。

## 2. 逐层职责与实际覆盖（不混淆 Demo/合成/真实）

| 数据层 | 身份来源 | 允许的权威声明 | V2-P0 必须保证 |
|---|---|---|---|
| `DEMO` | 本地 HiFi UI fixtures | 无任何持久化资格或 QA、许可、证据、SHA；仅视觉示例 | 所有 seed 设为 `sourceType=DEMO, live=false`；资格不通过；QA 数值不可作为签署记录 |
| `SYNTHETIC_PERSISTED` | GET `/v1/p2/sources` | 后端已有合成 SourceVersion + 权限内可见的元数据和真实 SHA | 以 `source_id + revision_id` 选择，记录仅由服务端返回；本地预览不能改其 QA/引用/审计状态 |
| `REAL_PENDING` | 真实来源资格服务（未开放） | 版权、采集、版本、来源适用性均待证据确认 | 不通过 V2 混入或冒充已登记合成状态 |
| `REAL_QUALIFIED` | 独立来源/法律/科研质量审核（未实现） | 独立签署才可能达准入门槛 | 当前必须保持 NO-GO |

**P0 实修：**
1. 初始化和重新加载时，前端内置六个视觉 seed 一律归 `DEMO`；清除示例 SHA、QA 数值、Package SHA、来源权限和模拟项目引用；合成统计仅计算服务器投影。
2. 如果 API 失败，清除前次已加载的 `live` 投影并展示显式报错，不假装有最新来源；前端不能凭状态阶段推断真实版权。
3. 来源选择键增补 `revision_id`，同一 `source_id` 的修订版本不能被当成同一阅读实体。
4. 管理 V2 不将 Project/Batch “当前筛选值”复制为单篇来源的引用回执；真实筛选使用服务器 `project_id/batch_id` 查询，逐来源引用仍要求独立详情核对。
5. **对已登记服务器来源，V2 页面上的本地 QA、Issue、ScopeBinding、模拟审计导出全部拒绝**；真正的 Curator QA 必须经独立 `/source-qa` 登录和现有受控 P2 API。
6. Producer 登记必须提交自身明确提供的**受控合成 Markdown 文本**。原先按标题自动合成研究正文及写死 2026-01-01/02 时间戳的行为移除；登记时刻作为合成来源 receipt 时间（不是论文发表日期）。非 Producer 不能“降级为本地 SYNTHETIC 登记”。

## 3. V2 前端操作完整性矩阵

| 业务步骤 | 既有 P2 后端 / 原有 Reviewer 入口 | V2 独立页面 | 当前 P0 决策 |
|---|---|---|---|
| 来源列表 + 版本状态 | 合成读 API 已实现 | 接 `/sources`，有 Demo 混用历史 | **修复来源身份、版本键和回读故障显式暴露** |
| Producer 合成登记 | POST `/sources` 已实现 | P0 前有自动编造正文 | **输入原文后走真实合成 API；不得用真实 PDF** |
| Auditor 独立用途审核 | `/source-qa` + POST `/rights` 已实现 | 未连接 | **维持独立受控入口；不得虚构批准** |
| Producer 转换 | POST `/convert` 已实现 | 尚无 V2 真正转换操作 | **保留原流程；V2 待增量适配** |
| Curator 原件/Document IR | `/original`、`/document` 角色隔离 | 仅四个演示 Unit | **后端来源不显示演示 Unit，提示使用独立入口** |
| Curator 不可变 Unit QA | POST `/qa` + GET `/reviews` 已实现 | local `qaLocal` 模拟 | **禁止在 live 上本地“审核”** |
| SourcePackage Freeze | POST `/freeze` 已实现 | V2 未完整接通 | **不可生成假冻结回执** |
| Project/Batch Binding | POST `/scope` 已实现 | local `commitBind` 模拟 | **禁止 live 本地模拟；来源范围只通过后端筛选** |
| 审计校验和版本谱系 | GET `/audit` + source detail 部分存在 | 静态 timeline/15-axis | **live 页标明静态样例，禁止伪装签署导出** |
| 真实文件/MinerU/Gold/专家 | 明确未开放 | 未开放 | **维持 NO-GO** |

## 4. 权限与真实性 Kill Tests

- `P0-K01`: `#p11Nav` 实际 9 个唯一入口，旧 Studio、隐藏 B1、V2 均在；非放宽 DOM 检查。
- `P0-K02`: `window.__p2v2.sources` 内每条非 live seed 必须为 `DEMO`，`rights=NOT_ELIGIBLE`，无 RAW/Document/Package SHA、无 QA 已审计数。
- `P0-K03`: 只有服务端返回的合成源才能称 `SYNTHETIC` / `live=true`；V2 不允许将假冒的项目筛选值投影为真实引用。
- `P0-K04`: V2 的已登记来源不能用本地 Demo Unit 作 QA，也不得提交本地 QA/Scope/Audit 记录；后端 `/source-qa` 保留独立 Curator 门禁。
- `P0-K05`: 不给 Manager/Producer 受限原文、不向任何身份自动授予 Gold/Expert；旧 D0 role security and Strict-Blind kill cases保持通过。
- `P0-K06`: 仅输入真实提供的受控合成原文且 Producer 有权时 V2 方可 POST；缺失原文、角色不符、后端拒绝必须 fail closed。
- `P0-K07`: 不改变 frozen source authority，B4 的 allowlist 仅显式增加两份独立 V2 UI 资源，不将新系统扩大到 `runs/`、`src/`、原 EA 代码。
- `P0-K08`: 全部原始测试须在**同一最终 Git SHA**上 Chromium/Python 复跑，且截图能标明来源版本；先前 PR #47 的 9/9 不能冒充 PR #48。

## 5. 分阶段交付与未完成事项

| P0 工作项 | 本次交付 | 尚需验收 |
|---|---|---|
| P0-A｜基线锁定与共同故障归因 | PR #48 exact SHA、9 工作流及代码映射 | 完成 |
| P0-B｜导航及受保护变更守卫修复 | Browser assertions + 两个 V2 资源精准 allowlist + Node check | 精确 SHA 复跑 |
| P0-C｜数据真实性与权限保护 | DEMO / server truth、版本键、错误显示、live 操作 fail closed | Chromium + 独立授权负测 |
| P0-D｜受控合成登记 | Explicit raw text、Producer role check、去掉自动编造和假时间 | Producer→API 浏览器完整回执 |
| P0-E｜全流程审计、视觉、运维 | 本文档、真实/合成权限矩阵 | V2 权限审核、转换、QA、冻结、审计 E2E；Demo 4K 人工验收；部署证据 |

**P0 不等于 V2 已全部可用。** 只有合成 QA/版权/解析/冻结/引用在 V2 入口可由对应实际角色跑通，才可以宣称 V2 专页流程闭环；此前原有 P2 后端的合成 E2E 是基础能力，不代表 V2 专页拥有相同行为。

## 6. 规范/代码双轨治理

- GOV-0.3/0.4 的归档和 15 轴报告目前在另一条 Draft 文档分支；V2 的硬编码矩阵只能当**注明版本的静态可视化**。临床权威 SIS-MED R6 P0.4 指定原件未恢复，条款级 `NOT ASSESSED`；AI Nutri v2.1 Domain Adapter 仍待绑定。
- 原 Workbench 来源栏目和新 V2 同时存在是有意的过渡，但不能永久维护两套各自带业务真值的前端状态机。完成 V2 合成 API 对齐及非回归后，再制定单入口收敛方案。
- 真实 PDF/MinerU、版权资格、原件阅读、Expert exposure、Gold、生产服务的独立责任人和验收在 P0 均保持未获授权。
- PR 描述声称阿里云预览已部署只是一条声明；需要确切环境版本、服务端 commit、截图、回滚和权限核查 receipt，不能靠 GitHub CI 自动等价证明。

## 7. 下一轮执行入口与 Gate

`WB-P2-V2.0-P0.1｜Exact-Head Native Chromium + Synthetic Registration/Role Truth Acceptance`

优先验收：V2 route/DEMO isolation → controlled Producer registration → server readback → independent Auditor rights → Producer conversion → independent Curator QA → Producer Freeze → Auditor global audit，所有读写必须来自既有 API 或相应授权的独立入口。

V2 页内未接入的环节只允许明确展示受保护的 **Handoff / Pending**，不得用 browser-local simulated status 冒充已经完成。

**Release decision:** PR #48 保持 Draft；`REAL_SOURCE=NO_GO`、`GOLD=NO_GO`、`EXPERT_EXPOSURE=NO_GO`、`MAIN_MERGE=NO_GO` 直到其独立审计完成。
