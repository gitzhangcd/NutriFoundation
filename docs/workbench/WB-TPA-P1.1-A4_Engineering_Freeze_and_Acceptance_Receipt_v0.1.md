# WB-TPA-P1.1-A4｜Engineering Freeze, Acceptance & Non-Regression Receipt v0.1

> **对象**：NutriFoundation Workbench — Management UX & Project → Batch → Task operations  
> **日期**：2026-10-11  
> **仓库**：`gitzhangcd/NutriFoundation`  
> **基线**：`workbench-tpa-p1-synthetic-management` @ `5009763dda194245d9c4dfdd5df45f365c61529a`  
> **开发分支**：`workbench-tpa-p1.1-a-management-ux-spec` · Draft PR #29  
> **最后运行代码提交**：`849ebd4f1edd958b3c0ef9784a1dcab58e32f39f`  
> **状态**：`SYNTHETIC_ENGINEERING_ACCEPTED_FOR_REVIEW / REAL_RESEARCH_NO_GO / NO_MAIN_MERGE`  
> **范围限制**：`SYNTHETIC_ENGINEERING_ONLY`；`scientific_capture=false`；`gold_qualification=NOT_ELIGIBLE`。

## 1. A1 → A4 实施清单

| 阶段 | 交付 | 说明 |
|---|---|---|
| **A1 · Minimal Operational Contract** | `docs/workbench/WB-TPA-P1.1-A1_Minimal_Operational_Contract_v0.1.md` | Project、OperationalBatch、TaskPlacement 和独立幂等回执的最小运营模型；仅新增运营数据，不改变 SIS/NDS/Gold 权威 |
| **A2 · Implementation** | 原 D0 `/manage` 同源 UI、受限 `/v1/tpa/**` API、状态控制器 | 七导航（本期重点为总览/项目批次/任务中心）、五步任务向导、服务端范围统计、来源全 SHA、Legacy 视图、只读详情深链接 |
| **A3 · Acceptance** | Python、Chromium、原 D0/EA/TPA/engine 回归 | `30 passed`；`86 checks, page_errors=[]`；完整数据、权限、回归及备份验证见下 |
| **A4 · Handoff** | 本回执、冻结候选 commit、PR 元信息与后续 GO/NO-GO | 只冻结合成工程实现参考基线；不合并、不公开部署、不招募真实专家 |

### A2 关键变更范围

- 新增 `apps/workbench/d0/tpa_projects.py` 与 `tpa_projects_adapter.py`，在原 `tpa_synthetic.sqlite` 增设不可变 `tpa_project_registry`、`tpa_operational_batches`、`tpa_task_placement`、`tpa_ops_idempotency`。
- 复用 `TaskProduction.build_draft_record` 校验真实的 synthetic task definition、来源版本、SHA、Profile、知识截止与策略；**新任务+归属在同一事务提交**，创建重试不重复。
- `tpa_adapter.py` 的旧未筛选 `/v1/tpa/tasks` 保持响应形状；额外的 `project_id/batch_id/state/limit/offset` 只用于服务端过滤。原 `tpa_batches`（七项批量草稿原子回执）继续保留，与新运营批次不可混淆。
- `web/manage.html` + `tpa_manage.js` 保留原 D0 同源会话/CSRF/Host/Origin；`web/tpa_p11.js/css` 为增量管理 UI。**不在管理端暴露科学原文、受限 Agent 候选、专家真值、Gold 或真实临床信息**。
- `tpa_project_registry`/`tpa_operational_batches`/`tpa_task_placement` 具有不可变触发器；任务提交、授权、撤销与实际证据暴露仍由原 TPA/EA 控制器和 append-only audit 管理。

## 2. 可复现的 GitHub Actions 证据（限合成工程）

| 作业 | Commit | 运行链接 | 结果 |
|---|---|---|---|
| P1.1-A Python + 原生 Chromium | `849ebd4f` | https://github.com/gitzhangcd/NutriFoundation/actions/runs/38119182596 | `SUCCESS (Python + native Chromium)` |
| P1 TPA 合成管理非回归 | `849ebd4f` | https://github.com/gitzhangcd/NutriFoundation/actions/runs/38119182591 | `SUCCESS` |
| EA-P1 原始 D0 非回归 | `849ebd4f` | https://github.com/gitzhangcd/NutriFoundation/actions/runs/38119182611 | `SUCCESS` |
| D0 staging / full engine | `849ebd4f` | https://github.com/gitzhangcd/NutriFoundation/actions/runs/38119182563 | `SUCCESS` |

`30` 项 Python 测试通过、`86` 项 Chromium checks、`page_errors=[]`。工作流使用 Python 3.11 锁定依赖，并在浏览器中实际使用原 D0 PDF.js、双语阅读、证据锚点及 EA 和 NDS 隔离路径。对比 P1 合成基线的 GitHub diff 未触碰 `runs/**`、`src/nutrifoundation/**`、`apps/workbench/c1/**`、`c2_1/**`、`c2_2/**`。

## 3. P1.1-A `A-UI-01`～`A-UI-24` 验收追踪矩阵

> 下表的「合成通过」表示该场景或核心不变量由实际测试覆盖，并非逐 ID 的单独测试函数。任何尚未执行的性能、生产安全、真实专家和科学核验不得被推定通过。

| ID | 验收主题 | 证据与判断 |
|---|---|---|
| A-UI-01 | 同源管理入口/角色标志、七导航 | `/manage` Chromium 登录、导航、会话测试；合成通过 |
| A-UI-02 | 项目、批次、任务详情深链接及刷新/前后退 | Chromium project/batch URL 回放及 task-detail URL 恢复；合成通过 |
| A-UI-03 | Project/Batch 持久化、幂等、分页 | `test_p11_project_batch_create_and_idempotent`、`test_p11_restart_and_sqlite_backup_keep_legacy_and_placement`；合成通过 |
| A-UI-04 | 项目/批次任务原子归属 | `test_p11_atomic_task_placement_and_legacy`、`test_p11_invalid_source_or_scope_has_zero_side_effect`；合成通过 |
| A-UI-05 | 两个来源的版本与 SHA | Chromium 显示完整主/辅来源 SHA-256 + 原有版本列表；合成通过 |
| A-UI-06 | Agent 复核模式草稿与 Profile/cutoff | P1/P1.1 草稿流程、Profile/源时序约束；合成通过 |
| A-UI-07 | 专家独立模式禁止候选泄漏 | `test_independent_no_agent_metadata_exposure` 与专家 workpack 检查；合成通过 |
| A-UI-08 | Validate/Freeze 不可原位改写 | 原控制器状态机 + `test_p11_project_batch_records_are_immutable`；合成通过 |
| A-UI-09 | Producer prepare，但 assign 被拒 | `test_p11_server_state_counts_and_no_gold` 与角色 403；合成通过 |
| A-UI-10 | Manager 分配→发布 | Chromium UI + TPA-P1 角色/发布验收；合成通过 |
| A-UI-11 | publish 幂等重放/冲突 | `test_publishing_idempotency_and_role_denial`；合成通过 |
| A-UI-12 | 已发布撤销、保留暴露历史 | `test_revoke_preserves_read_history_and_blocks_new_access`；合成通过 |
| A-UI-13 | manager/EA/NDS/auditor 越权限制 | `test_p11_strict_roles_original_blindness_and_csrf`、EA 原文拒绝、原 D0 非回归；合成通过 |
| A-UI-14 | 错误 SHA/不合法 cutoff 无污染 | `test_p11_invalid_source_or_scope_has_zero_side_effect`；合成通过 |
| A-UI-15 | 原七类批量创建回执全有或全无 | `test_atomic_batch_seven_types_rollback_and_idempotency`；合成通过 |
| A-UI-16 | Legacy 明确显示/过滤、不自动迁移 | Python Legacy 查询、Chromium Legacy 专项筛选；合成通过 |
| A-UI-17 | 总览正确统计，未知值不伪造 | `test_p11_server_state_counts_and_no_gold`，blocked 显示未统计；合成通过 |
| A-UI-18 | P2/P3 实例入口禁用 | 真实 PDF/import、真实 Agent/专家/Gold 仍拒绝；合成通过（禁止路径） |
| A-UI-19 | 原 D0 EA、PDF.js、双语、锚点及 19-field | 原 D0/EA/TPA Chromium + full engine CI；合成通过 |
| A-UI-20 | 桌面、平板、手机、键盘 | Chromium 1440×900、1024×768、390×844、焦点/Enter；合成通过 |
| A-UI-21 | XSS、hash 注入和错误隔离 | HTML/邮箱字符拒绝、hash allowlist、无浏览器 page_errors；合成通过（不代表渗透测试） |
| A-UI-22 | 角色切换清理私有 UI | 同标签页 logout → manager 登录，角色按钮/缓存不遗留；合成通过 |
| A-UI-23 | SQLite 迁移、备份、恢复、回滚 | `test_p11_restart_and_sqlite_backup_keep_legacy_and_placement`、原备份模块 Fernet seal/open restore；合成通过（不等于云服务器故障演练） |
| A-UI-24 | 原 P1/API & D0/EA/NDS/engine 非回归 | 上述四组最新 CI；合成通过 |

## 4. 非回归与禁止晋级边界

- **保持不变**：NDS R0/R1/R2、原三栏专家界面、既有 19-field、Scientific Gold 所有权、原文权威性、双语译文辅助地位、SourceAnchor、旧七类批量 API。
- **没有实施**：真实 MinerU/PDF 解析导入、真实科学版权/来源资格审核、真实 Agent provenance、真实专家资格核验及入组、双人裁决 Gold、外部渗透测试、公网生产 HTTPS 安全审核。
- **部署边界**：现有阿里云私有合成 staging 仍需独立评估；GitHub CI 通过并不表示该云实例已经升级或可面向真实研究开放。CentOS 7 旧系统、SSH 隧道访问、来源权利审核等问题不可通过此 UI 修复。
- **科学结论**：科学与安全 GO/NO-GO 仍为 **NO-GO**。`scientific_capture=false`、`gold_qualification=NOT_ELIGIBLE` 不变。
- **合并策略**：保留 Draft PR #29；不合并到 `main`，不自动合并上游 #26/#27/#28，不替真实管理员开启实际研究。

## 5. 运维交付与回滚操作原则

1. 将本阶段代码仅部署到**全新隔离、可丢弃的合成 QA 数据目录**，不得覆盖当前真实或唯一的研究工作区。
2. 变更前停止单写入服务、确认私有完整备份、保存回退 release SHA 与 0600/0640 配置；项目/批次数据属于私有工作流数据库，不应通过公共静态 URL 暴露。
3. 回滚软件应优先切换到上一个已验收 release 与兼容的数据备份；如 schema 不兼容，停止写入并在隔离恢复验证后使用受控回滚；不得直接删除已暴露/已冻结的审计记录。
4. 不复制测试凭据到生产；不自动迁移 Legacy 项目归属；不得为“方便测试”更改 Strict-Blind 的角色隔离。
5. 正式验收/部署仍需研究负责人、科学负责人、安全负责人分别确认；本阶段的工程回执不替代三者意见。

## 6. 后续独立阶段

- **P1.1-B**：科学资料库、Agent 准备、专家与分配的可操作界面及必要的非科学运营 API（仍按阶段 gate）。
- **P1.1-C**：质控、审计导出和跨页面效率优化；不得直接建立 Gold promotion 路径。
- **P2/P3**：真实来源与专家研究分别执行 source-rights、解析忠实性、资格与伦理/安全验收；各阶段独立 NO-GO 守门。

---

*本回执仅基于仓库变更、可重放的 GitHub Actions 与保留的 D0 科学边界；不声明已经在阿里云真实环境验收。*