# WB-P1.1-B2｜Synthetic Agent Preparation Operations & Provenance

# Engineering Acceptance, Evidence & Non-Regression Receipt v0.1

> **验收日期**：2026-10-11  
> **仓库**：`gitzhangcd/NutriFoundation`  
> **阶段**：`WB-P1.1-B2`  
> **开发分支**：`workbench-p1.1-b2-synthetic-agent-provenance`  
> **PR**：[Draft #33](https://github.com/gitzhangcd/NutriFoundation/pull/33)，base = B1 Draft PR #32  
> **验收代码 SHA**：`1046a0772ddfc57869160360354a62351750412b`  
> **判定**：`SYNTHETIC_ENGINEERING_PASS / INDEPENDENT_REVIEW_PENDING`  
> **真实科研 / 安全 / 生产**：`REAL_RESEARCH_NO_GO / GOLD_NOT_ELIGIBLE / NO_MAIN_MERGE`

## 1. B2 实际完成内容与科学边界

B2 **没有**实现或运行新的 Agent/LLM，也没有对已有候选重做预标注。原 P1 `TaskProduction.prepare` 已向原 EA 引擎交付并冻结固定虚构候选（`SYN-FIXTURE-NOT-AN-LLM`）；B2 仅新增**来源证明、角色投影和不可变核验回执**。

```text
Original D0 Workbench /manage
├─ Original TPA task state machine (Producer validate / freeze / prepare)
│   ├─ Frozen task definition SHA-256
│   ├─ Original TPA PREPARATION_FROZEN hash-chain event
│   └─ Frozen source allowlist (Source ID / Revision / SHA)
├─ Original EA authority
│   ├─ Primary synthetic source revision
│   ├─ Frozen single fixture candidate; source anchoring & content SHA
│   └─ Strict-Blind expert access gate (UNCHANGED)
├─ B1 optional immutable SourcePackage metadata
└─ B2 immutable synthetic provenance attestation (NEW)
    ├─ Producer original-task owner inspect + attest
    ├─ Manager read-only redacted operational projection
    ├─ Idempotent stored receipt + same-transaction TPA audit event
    └─ Agent management tab / task selection / reload recovery
```

B2 的记录**不能**宣称模型真实运行、真实资料结构化抽取、候选科学准确性、专家真值、Gold 或临床使用准备就绪。

## 2. 实现与接口

代码文件：

- `apps/workbench/d0/tpa_agent_operations.py`：原 P1/EA 事实读取、核验与不可变证明、审计事务、角色投影及 25/页的 Agent-mode task list；
- `apps/workbench/d0/tpa_agent_operations_adapter.py`：原 D0 的 session/CSRF/Origin/Host 保护下，挂载 Producer/Manager 专用接口；
- `apps/workbench/d0/d0_app.py`：安装原 D0 同源 B2 路由；
- `apps/workbench/d0/web/tpa_b2.js`：Agent 准备页，原任务状态、核验、不可变证明及回执；
- `apps/workbench/d0/web/tpa_p11.js`：连接导航与刷新；修复重叠刷新被忽略的竞态；
- `apps/workbench/d0/web/manage.html`：在原 `/manage` 加载 B2 客户端逻辑；
- `apps/workbench/d0/tests/test_tpa_b2.py` 与 `apps/workbench/d0/tests/browser_d0.py`：B2 安全及真实 Chromium E2E；
- `.github/workflows/wb-p1-1-b2.yml`：完整 Python/Chromium 门。

| 接口 | Producer | Manager / EA |
|---|---|---|
| `GET /v1/tpa/agent-preparations` | Agent-mode 任务列表、没有正文/候选 payload | Manager 只读且不含独立专家组；EA 拒绝 |
| `GET /v1/tpa/agent-preparations/{task_id}` | 本人任务证明详情，包含核验候选摘要 | Manager 脱敏，只显示运营 provenance；EA 拒绝 |
| `GET /v1/tpa/agent-preparations/{task_id}/inspect` | 本人任务只读检查原 EA/TPA 冻结事实 | 拒绝 |
| `POST /v1/tpa/agent-preparations/{task_id}/attest` | 本人任务完成不可变证明，幂等重放 | 拒绝 |

任何 `HUMAN_INDEPENDENT` 任务均**不进入队列**，通过已知 Task ID 请求 B2 明细、检查或证明也拒绝；没有向独立专家暴露 Agent 候选摘要、候选数量或运行标识。

## 3. 运行中的完整 CI 证据：精确代码 SHA

所有下列 GitHub Actions 均发生于**同一个 B2 代码 SHA `1046a0772ddfc57869160360354a62351750412b`**，状态 `completed/success`：

| 验收层 | CI |
|---|---|
| B2 Python + Native Chromium | [38126739225](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38126739225) |
| A5 Management UX / Expert Handoff | [38126739222](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38126739222) |
| B1 Scientific Source Packages | [38126739219](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38126739219) |
| TPA P1.1-A Synthetic Operations | [38126739217](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38126739217) |
| TPA P1 Integrated Management | [38126739212](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38126739212) |
| EA P1 Original D0 Integration | [38126739221](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38126739221) |
| Original D0 Engineering + Full-Engine Regression | [38126739213](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38126739213) |

原 D0 运行包含 `engineering-acceptance` 和 `Full engine regression (Python 3.11)` 两个成功子作业。

**B2 Python：`59 passed`，6 个依赖弃用 warnings。** 新增的测试覆盖：P1 准备前不能伪称候选已经冻结；固定合成候选 provenance/hash cross-check；B2 证明幂等重复/冲突及 SQL 不可变触发器；独立专家 Strict-Blind 排除；Producer/Manager/EA 角色隔离；可选 B1 Package；来源包登记晚于已冻结证明时**不得倒填证据历史**；原 P1 任务可在没有 B1/B2 证明时正常 assign/publish。

**B2 原生 Chromium：`97 checks`、`page_errors=[]`、`native_pdfjs=true`、`scientific_capture=false`。** 关键新增检查：

- `b2_existing_ea_fixture_inspection_without_llm`；
- `b2_immutable_agent_attestation_survives_reload`；
- `b2_origin_and_candidate_digest_producer_only`；
- `b2_manager_read_only_with_candidate_digest_redacted`。

同时保留 A5 的“服务端真实发布成功、前端收到 502 丢失响应后恢复”的真实 Chromium 验证、B1 Source Library/版本深链接、原 D0 双语/PDF.js/SourceAnchor、NDS 19 字段非回归。

浏览器截图/日志由 GitHub CI artifact 保留：
[Run 38126739225 浏览器证据包](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38126739225/artifacts/11697657399)。
这里的“真实 Chromium”是**合成环境浏览器 E2E**，不是部署到云服务器或真实专家试用。

## 4. 发现的问题与修复证据

1. **Producer 证明视图过度脱敏**。早期测试发现 Producer 回执不含候选集合摘要/数量，导致无法核对来源。修改为 Producer **仅看 hash/count 元数据而不看候选 payload**，Manager 仍隐藏 digest/count/fixture-run origin。
2. **重开恢复测试方法签名错误**。修复调用时增加经审计的 `actor`，并保持服务端任务 Producer owner 约束。
3. **Agent 默认任务深链接**。早期 Chromium 已完成不可变证明，但默认选中 Task ID 未写入 URL，刷新/回退时定位不可靠。现在在选择默认 Task ID 时规范化 hash URL，原 Agent 页面在 reload 后恢复。
4. **B1 包晚于 B2 的历史一致性**。证明确立时没有 B1 引用包的情况，后来登记 B1 包不能倒填之前的证据，也不能让原正确证明变无效。新增原证据快照与回归用例。
5. **A5 原管理端偶发重叠刷新**。一次 PR 重测在 HTTP-502 发布响应丢失场景显示旧 ASSIGNED，另一个独立运行通过。将管理端 reload 修改为串行+排队重读，并增强失败诊断。最终代码 SHA 上重新验证通过，原 502 后提交恢复用例没有被跳过。

GitHub 旧失败 Actions 均保留；**只凭最终代码 SHA 的成功运行判定工程接受**。

## 5. 权威数据、隔离与可解释性

- B2 附着于原 `apps/workbench/d0`，未改动原 `ea_runtime.py`、`ea_seed.py`、`ea_contract`。
- 保护的 `runs/**`、`src/nutrifoundation/**`、`apps/workbench/c1/**`、`c2_1/**`、`c2_2/**` 无 B2 改动。
- `SYN-FIXTURE-NOT-AN-LLM` 与 `SYNTHETIC_FIXTURE_NOT_AN_LLM` 字样不得在 UI 或报告中误称为真实 Agent。
- `B2 proof != task published != expert opened != expert read != expert judgement != Gold`。
- `scientific_capture=false`；`gold_qualification=NOT_ELIGIBLE`；`real_agent_executed=false`。
- 本阶段未完成真人可用性、正式安全威胁建模/渗透测试、真实来源版权/伦理、真实模型 provenance、现实医院临床试用或科研独立复核。

## 6. 阶段冻结与下一步

**`SYNTHETIC_ENGINEERING_PASS`**：可作为后续 B3 的合成开发候选基线；仍需独立代码审查。PR #33 保持 **Draft/Open/Unmerged**，不应在科学/安全门尚未完成时合入 `main`。

推荐进入：

```text
WB-P1.1-B3｜Synthetic Expert Roster, Assignment & Exposure-Safe Handoff
  → WB-P1.1-B4｜Integrated Acceptance, Failure Recovery & Non-Regression Freeze
  → P2 real-source/MinerU rights & security gate, separately
  → P3 real-expert qualification and independent scientific Gold ownership gate
```

**禁止事项**：真实 LLM/Agent 接入、导入患者/临床文件、正式专家权限、独立 Gold 资格、线上正式服务、把冻结合成证明当作真实模型执行证据。
