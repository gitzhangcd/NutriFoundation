# WB-P1.1-B3｜Synthetic Expert Roster, Assignment & Exposure-Safe Handoff

**契约**：`WB-SYNTHETIC-EXPERT-HANDOFF-v0.1`  
**工程范围**：`SYNTHETIC_ONLY`，继承 B2 Draft PR #33。  
**科学与生产**：`REAL_RESEARCH_NO_GO / GOLD_NOT_ELIGIBLE / NO_MAIN_MERGE`。

## 1. 核心决策：原 TPA / EA 仍然是唯一权限权威

B3 不新建账户、密码、专家资格数据库、授权令牌、任务发布状态机或候选保存层。它只把原有固定测试账号和同源任务操作组织成可以观察、校验及追溯的 UI 与不可变交接证明。

```text
原 D0 /manage 专家与分配
├─ 已固定合成名册 (非真实资格)
│   ├─ SYN-EA-EXPERT-A → AGENT_PROPOSE_EXPERT_VERIFY → ea1
│   └─ SYN-EA-EXPERT-B → HUMAN_INDEPENDENT        → ea2
├─ B3 分配前源版本 / 模式 / 原事务状态 preflight
├─ 原 TPA Manager assign → ASSIGNED（B3 不替换）
├─ 原 TPA Manager publish → PUBLISHED + GRANT_ISSUED
│   └─ 原 EA expert_gate：仅授权任务 + 对应合成专家账号可读取
├─ B3 Manager 合成交接 attest (必须已经发生原 GRANT_ISSUED)
│   └─ 绑定原 EXPERT_ASSIGNED / TASK_PUBLISHED / GRANT_ISSUED event hash
└─ 后续暴露跟踪：仅投影原 TPA 记录的真实 EA 访问事件
    ├─ TASK_OPENED
    ├─ SOURCE_LIST_OPENED
    ├─ SOURCE_UNIT_VIEWED
    └─ AGENT_CANDIDATE_VIEWED (仅 Agent 模式)
```

### B3 不能替代的权威

- 医生/专家资格、身份核验、伦理授权和冲突处理没有在 B3 发生；这属于真实专家阶段。
- 原文、双语结构、SourceAnchor、PDF.js、NDS 19 字段与 EA 候选真值不由 B3 拥有。
- `PUBLISHED` **不等于** `TASK_OPENED`、`SOURCE_UNIT_VIEWED`、专家已读、标注完成或 Gold。
- 暴露统计是可观察到的**已记录访问事件**；不声称覆盖全部现实暴露通道或用户真实理解行为。
- `HUMAN_INDEPENDENT` 必须没有 EA 候选集；一旦发现候选存在，B3 preflight **拒绝**，绝不能补救性清理后继续发布。

## 2. 固定合成名册

| Actor | 原 D0 测试入口登录名提示 | 工作模式 | 资格 |
|---|---|---|---|
| `SYN-EA-EXPERT-A` | `ea1` | `AGENT_PROPOSE_EXPERT_VERIFY` | `SYNTHETIC_ACCOUNT_ONLY` |
| `SYN-EA-EXPERT-B` | `ea2` | `HUMAN_INDEPENDENT` | `SYNTHETIC_ACCOUNT_ONLY` |

只返回合成 actor 和 login hint，不创建密码、密钥、真实专家名录。原 D0 `Auth` 会话与原 TPA `assign`、`expert_gate` 为唯一有效分配/发布/读取机制。

## 3. B3 接口

| 方法 | 路径 | Role | 语义 |
|---|---|---|---|
| GET | `/v1/tpa/expert-roster` | Manager/Producer | 固定合成账号-模式映射、资格状态、无凭据 |
| GET | `/v1/tpa/expert-handoffs?limit=25&offset=0` | Manager/Producer | 有界合成任务队列和授权/暴露投影 |
| GET | `/v1/tpa/expert-handoffs/{task_id}/preview` | Manager/Producer | 实时校验来源、角色、分配与原 hash-chain |
| GET | `/v1/tpa/expert-handoffs/{task_id}` | Manager/Producer | 原授权与最新暴露摘要；可附已固定交接回执 |
| POST | `/v1/tpa/expert-handoffs/{task_id}/attest` | **Manager** | 仅在原任务 PUBLISHED + 原 GRANT_ISSUED 已存在后冻结交接证明 |

校验请求：

```json
{
  "contract": "WB-SYNTHETIC-EXPERT-HANDOFF-v0.1",
  "idempotency_key": "<stable 8–100 character nonce>",
  "expected_assignment_event_hash": "<original 64-character SHA-256>",
  "expected_grant_event_hash": "<original 64-character SHA-256>"
}
```

回执以 `SYNTHETIC_HANDOFF_ATTESTED` 表示 Manager 已确认**原授权事实**。原 TPA 审计日志在同一 SQLite 事务写 `SYNTHETIC_HANDOFF_ATTESTED`，与不可变回执一一对应；禁止 SQL UPDATE/DELETE。

任务 `PUBLISHED` 之前不准固化交接；`REVOKED` 以后关闭未来访问，保留既存回执及已记录暴露统计。即便确实发生了 `TASK_OPENED`，也不能由此推断专家已完整阅读或完成判断。

## 4. 操作界面（沿用原 D0）

路径：`/manage` → 「专家与分配」。

1. 顶部固定合成账号名册，明确两种模式和资格为 `SYNTHETIC_ACCOUNT_ONLY`。
2. 左侧服务器分页任务队列；右侧展示 Task ID、来源版本全 SHA、唯一允许专家 actor、任务状态及原分配/发布/授权 hash。
3. 未分配时可用 **通过原 TPA 分配合成专家**；已分配时可用 **通过原 TPA 授权发布**，均调用既有 `window.opsTaskAction`，不新建 Grant。
4. 原任务已经 PUBLISHED，Manager 才能点击 **固化不可变专家交接回执**；幂等键可以恢复网络响应丢失。
5. Manager 可撤销未来访问；原文权限立即由原 `expert_gate` 关闭，已暴露历史不得删除。
6. 专家在另一个独立会话登录原 `/` 阅读器，界面不向 Manager/Producer 发放专家账号密码或会话令牌。

## 5. 必需 Kill Tests

| ID | 预期 |
|---|---|
| B3-K01 | 名册仅固定两账号，不产生真实资格、密钥或凭据 |
| B3-K02 | AGENT 模式不分配给独立组；HUMAN_INDEPENDENT 不分配给 Agent 组 |
| B3-K03 | 任务尚未 PUBLISHED 时禁止交接证明；原 EA 专家访问 403 |
| B3-K04 | Manager attest 必须与原分配、授权事件 hash 一致，假或过期 hash 拒绝 |
| B3-K05 | 同键同意图回执幂等；另一键重复冻结拒绝；不可变 SQL 触发器有效 |
| B3-K06 | 发布后允许正确专家独立登录原 EA；错误 EA 账号拒绝 |
| B3-K07 | 独立模式拒绝任何 EA Candidate，B3 不显示候选 payload/digest |
| B3-K08 | `PUBLISHED` 在访问前暴露事件数为 0；访问后仅统计真实原 EA 事件 |
| B3-K09 | 撤销后正确 EA 也不能再次访问；保留历史暴露计数与不可变交接 |
| B3-K10 | 原 PDF.js、SourceAnchor、双语、NDS R0/R1/R2、A5/B1/B2 全部非回归 |
| B3-K11 | 原同源 Cookie、CSRF、Origin、Host 保护不回退，未登录/Expert/Auditor 无管理接口 |
| B3-K12 | `scientific_capture=false`、`gold_qualification=NOT_ELIGIBLE`、`real_expert_qualified=false` |

## 6. 迁移与阶段界限

B3 专家 roster 是合成固定身份的**操作投影**，不能通过切换一个配置开关使真实专家自动获得权限。真实专家必须独立完成资质、伦理、隐私、冲突、培训、研究真值所有权以及 Strict-Blind 暴露历史验收。

工程代码通过 CI 也不能充当科学认可；真实研究、临床试用与生产部署仍为 `NO_GO`。

下一阶段建议 `WB-P1.1-B4｜Integrated Acceptance, Failure Recovery & Non-Regression Freeze`，收敛 B1/B2/B3 的操作契约与安全边界。
