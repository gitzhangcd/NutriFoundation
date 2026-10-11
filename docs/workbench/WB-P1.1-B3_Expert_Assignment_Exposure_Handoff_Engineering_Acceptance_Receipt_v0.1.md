# WB-P1.1-B3｜Synthetic Expert Roster, Assignment & Exposure-Safe Handoff

# Engineering Acceptance & Non-Regression Receipt v0.1

> **仓库**：`gitzhangcd/NutriFoundation`  
> **日期**：2026-10-11  
> **分支**：`workbench-p1.1-b3-expert-assignment-handoff`  
> **PR**：[Draft PR #34](https://github.com/gitzhangcd/NutriFoundation/pull/34)，base = B2 Draft PR #33  
> **验收代码 SHA**：`e700bdd88671a328bdb7b9ee492e71525cc9f5ce`  
> **工程判定**：`SYNTHETIC_ENGINEERING_PASS / INDEPENDENT_REVIEW_PENDING`  
> **科学、真实数据与生产判定**：`REAL_RESEARCH_NO_GO / PRODUCTION_NO_GO / GOLD_NOT_ELIGIBLE / NO_MAIN_MERGE`

## 1. 交付概览

B3 的中心约束为：**原 TPA 分配/发布/撤销，以及原 EA `expert_gate`，继续拥有唯一的合成操作授权真值**。B3 不创建第二套身份、专家权利、源原文、候选或访问 Grant。

新增 `tpa_expert_handoff.py` / `tpa_expert_handoff_adapter.py`、原 D0 安装路由、`tpa_b3.js`、管理端页面脚本接线、B3 Python 与真实 Chromium 验收、B3 CI 工作流与本阶段契约文档。

```text
固定合成名册
  SYN-EA-EXPERT-A / ea1 / AGENT_PROPOSE_EXPERT_VERIFY
  SYN-EA-EXPERT-B / ea2 / HUMAN_INDEPENDENT
           |
           v
B3 只读 preview：Task ID、流程模式、权威来源 SHA、
原 TPA assigned/published/grant 事件与唯一允许 Actor
           |
           v
原 TPA assign → ASSIGNED
原 TPA publish → PUBLISHED + GRANT_ISSUED
           |
           v
B3 Manager 按原授权事件 SHA 固化不可变 Handoff Receipt
           |
           v
另一独立浏览器会话原 EA 专家访问 / workpack / source
           |
           v
原 TPA 访问记录投影：TASK_OPENED / SOURCE_LIST_OPENED /
 SOURCE_UNIT_VIEWED / AGENT_CANDIDATE_VIEWED
           |
           v
原 TPA revoke → 未来访问 CLOSED + 既有暴露历史保留
```

**B3 回执不是专家已登录、已打开、已读、已完成标注或 Gold 的确认**。PUBLISHED 时即使已有 Grant，如果尚未发生真实 EA 读取，`recorded_exposure_events=0`。

## 2. 实际访问/角色规则

| Role/身份 | B3 名册与任务只读 | B3 Handoff attest | 原专家工作包 |
|---|---|---|---|
| Producer | 可以；不创建真实专家资格 | 拒绝 | 原 EA Producer 行为，沿用原权限 |
| Manager | 可以；暴露统计仅反映原记录 | **仅当原 TPA 已 PUBLISHED + GRANT_ISSUED** 才可冻结 | Manager 原文访问拒绝 |
| ea1 (`SYN-EA-EXPERT-A`) | B3 管理端拒绝 | 拒绝 | 仅可访问被发布给 Agent 复核组的原 EA 工作包 |
| ea2 (`SYN-EA-EXPERT-B`) | B3 管理端拒绝 | 拒绝 | 仅可访问被发布给独立组的原 EA 工作包，Candidate 拒绝 |
| NDS/auditor/匿名 | 拒绝管理操作 | 拒绝 | 仍依照原角色约束 |

固定名册为 `SYNTHETIC_ACCOUNT_ONLY`，不创建账户、密码或授予临床研究资格。独立组任务如果存在 EA Candidate，B3 fail closed，不会自动清除候选后继续。

## 3. 不可变证明与失败恢复

冻结 `WB-SYNTHETIC-EXPERT-HANDOFF-v0.1` 需要确认：

1. 原 `tpa_tasks` 定义及 `primary_source` 属于现有合成来源与原 allowlist，原文版本 SHA 一致。
2. Task 指派的 actor 与工作模式及固定名册完全匹配。
3. 原 `EXPERT_ASSIGNED`、`TASK_PUBLISHED`、`GRANT_ISSUED` 审计事件记录与真实 task 状态一致；不存在已撤销后冒充仍发布的授权。
4. `expected_assignment_event_hash`、`expected_grant_event_hash` 与原事务事件 hash 精确匹配。
5. 单次不可变回执在原 TPA 锁与 SQLite 事务内完成，连同 `SYNTHETIC_HANDOFF_ATTESTED` 事件入原审计 hash-chain。
6. 相同幂等键/内容返回原历史回执；换键重复冻结或撤销后新申请一律拒绝。相同键在撤销后重放只是历史回执读取，不会产生新 Grant。

B3 改造后还修复了**原管理页 A5 异步丢失响应回调偶发卡住的问题**：在用户明确点击发布的上下文中，使用限时单次、只读的服务端任务状态查询；必须以精确 Task ID + `state=PUBLISHED` 才能标记操作已完成。它不发送重复发布调用，也不会因超时就推断事务成功。成功后沿用 A5 的幂等意图回收与排队刷新机制。

## 4. 真实 CI 证据——所有工作流在相同的验收代码 SHA

下列工作流均已在 **`e700bdd88671a328bdb7b9ee492e71525cc9f5ce`** 完成且 `conclusion=success`。

| 测试 | GitHub Actions | 结果 |
|---|---|---|
| B3 原生 Python + Chromium | [38132952091](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38132952091) | **SUCCESS** |
| B3 独立追加运行 | [38132947927](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38132947927) | **SUCCESS** |
| B2 合成候选来源证明 | [38132952124](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38132952124) | **SUCCESS** |
| B1 来源版本包 | [38132952103](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38132952103) | **SUCCESS** |
| A5 管理交互与专家交接 | [38132952096](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38132952096) | **SUCCESS** |
| TPA P1.1-A 运营合同 | [38132952100](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38132952100) | **SUCCESS** |
| TPA P1 原管理工作流 | [38132952150](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38132952150) | **SUCCESS** |
| EA P1 原 D0 专家阅读器 | [38132952109](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38132952109) | **SUCCESS** |
| 原 D0 工程 + full-engine | [38132952094](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38132952094) | **SUCCESS；两个子作业均成功** |

**B3 Python：`64 passed`，6 个依赖弃用 warnings。** 新增检查合成固定名册、Manager 与 Producer 的权限边界、Agent/独立专家组分隔、原 TPA 正确发布之前 Expert 不能读取、准确 Grant SHA、幂等冲突、SQLite immutable、撤销后原 EA 访问拒绝及历史暴露保留。原 D0、NDS、A5、B1、B2 安全测试未跳过。

**原生 Chromium：`103 checks`、`page_errors=[]`、`native_pdfjs=true`、`scientific_capture=false`。** B3 新增 6 项检查：合成专家 roster 与 task deep link、发布前禁止交接、原 Grant 之后的不可变回执、未阅读不可推断、刷新回执持久、原 EA 真实访问事件计数。原 A5 `server_committed_publish_lost_http_reply_reconciled` 同样在最终代码上成功。

[Run 38132952091 Chromium 截图与测试记录 Artifact](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38132952091/artifacts/11699498524) 包含 B3 合成专家管理截图及原工作流证据；不代表已发布公网可用网页。

## 5. 缺陷关闭

1. **暴露事件名称与真实 EA 行为不一致**：起初未包括 `TASK_OPENED` 等原事件名称，导致真实打开 Workpack 后计数为 0。改为严格引用原 EA 的四类事件；不制造额外的已读状态。
2. **历史回执重放与撤销竞态**：原设计可能在核验授予事实和写入回执之间发生 revoke；修为原 TPA 同一互斥锁及事务。撤销后重放同键回执仍得到原历史记录，但新 key 不得再固化。
3. **旧 A5 发布丢失 HTTP 响应竞态**：某次跨阶段 CI 在服务端已 PUBLISHED 时 Manager UI 仍显示 ASSIGNED，并且旧操作回执未更新。修正为基于服务端状态的限时只读恢复；B2、B3 与 A5 的最终独立浏览器验收均成功。

以前的失败 run 保留作可追溯调试历史，不会被解释为最终验收结果。

## 6. 科学保护与未完成事项

变更限定在 `apps/workbench/d0/**`、B3 测试、CI 工作流和 B3 文档；并未修改 `runs/**`、`src/nutrifoundation/**`、`apps/workbench/c1/**`、`c2_1/**`、`c2_2/**`、原 `ea_runtime.py`、`ea_seed.py` 或 EA contract。

```text
scientific_capture        = false
gold_qualification        = NOT_ELIGIBLE
real_expert_qualified     = false
real_agent_executed       = false
production_deployed       = false
real_source_import        = NO_GO
main_merge                = NO_GO
independent_code_review   = PENDING
```

B3 解决了合成工程中的名册、权限、交接可追踪性，并不解决真正的专家资格/暴露历史、科研来源授权、真实 Agent 或 Gold 构建。

## 7. 决策与下一阶段

**`SYNTHETIC_ENGINEERING_PASS`**。本阶段可作为 B4 集成工程验收候选基线；PR #34 继续保持 Draft/Open/Unmerged，未经独立安全与科研 Gate 不可作为生产系统。

建议下一个任务：

```text
WB-P1.1-B4｜Integrated Acceptance, Failure Recovery & Non-Regression Freeze

B1 Source Package
  + B2 Agent fixture provenance
  + B3 Expert roster / assignment / handoff
  + Original D0/EA/NDS Strict-Blind
  → E2E integration, crash/restart, replay, drift, multi-role and safety kill tests
  → P1.1 synthetic-only engineering freeze (NOT real research go-live)
```
