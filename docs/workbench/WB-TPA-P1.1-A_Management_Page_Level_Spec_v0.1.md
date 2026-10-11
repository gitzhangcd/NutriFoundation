# WB-TPA-P1.1-A｜Management Information Architecture, Overview & Project–Batch–Task UX Specification v0.1

> **阶段**：P1.1-A 页面级规范（DESIGN READY FOR IMPLEMENTATION；不是代码验收，不是科研放行）  
> **日期**：2026-10-11  
> **仓库**：`gitzhangcd/NutriFoundation`  
> **基线分支**：`workbench-tpa-p1-synthetic-management`  
> **基线 HEAD**：`5009763dda194245d9c4dfdd5df45f365c61529a`  
> **基线代码验收**：`fbdd71a2569a6c3972d41b0915e7fa1cf54c0c4b`  
> **权限边界**：SYNTHETIC ENGINEERING ONLY；`scientific_capture=false`；`gold_qualification=NOT_ELIGIBLE`  
> **设计层级**：操作管理与 UI 合约，不变更上游 SIS、SIS-MED、AI Nutri、NDF、NDS 科学契约

## 0. 执行摘要与决策状态

### 0.1 本次确定的产品方向

1. 工作空间分离：外部 MinerU/解析器文档处理 → 同源 `/manage` 研究运营管理 → 原 D0 `/` 专家三栏标注；三者通过授权来源版本、任务 ID 和不可变回执连接，而非合并成单页应用。
2. 管理端导航七模块：**工作总览、科学资料库、任务中心、Agent 准备、专家与分配、进度与质控、审计与导出**。
3. 项目组织采用 **Project → Batch → Task**，但 Project/Batch 只是**管理组织实体**，不自动成为科学参考、Gold 或盲法分组的权威。
4. **本阶段仅交付导航框架、工作总览、项目/批次/任务中心**，并复用现有合成工作流；其余四个模块只展示受控占位说明/跳转，不谎称已实现。
5. 用户按照任务自然流程操作；服务器保持角色分工：producer 创建/验证/冻结/准备，manager 分配/发布/撤销；expert 使用原 D0 EA，不获得管理权限。
6. 不合并 PR #26/#27/#28，不进行真实来源导入、真实 Agent 调用、真实专家招募或 Gold 晋级；后续科学/安全审查另设放行门。

### 0.2 重要的“当前代码 vs P1.1-A 目标”差别

| 能力 | 现有 P1 代码事实 | P1.1-A 目标 / 状态 |
|---|---|---|
| `/manage` | `manage.html` 三栏：来源库/任务生产/分配；单页 | 保持同源入口；替换为七模块左侧导航 + 任务中心的分层交互；**拟实现** |
| 来源 | `/v1/tpa/sources` 仅返回 7 类已注册合成资料元数据 | 在任务向导内复用；真实来源登记和质量审核归 P2；**P1.1-A 不实施** |
| 项目 | 无独立 Project 实体与持久化 API | 新增最小合成运营 ProjectRegistry；**拟实现** |
| 批次 | `/v1/tpa/batches/drafts` 可原子创建 1–7 个任务，`/v1/tpa/batches` 仅回执 | 新增持久化 BatchRegistry + 显式任务关联；保留原原子批量 API 语义；**拟实现** |
| 单任务 | `/v1/tpa/tasks` 含 ID、状态、来源类型、profile、模式、受分配者等 | 列表筛选/详情/状态时间线需安全投影 API；**拟实现** |
| 工程工作流 | drafts→validate→freeze→prepare→assign→publish/revoke | **原端点保留**，改变交互编排而非替换状态机 |
| 专家结果 | 原 `/v1/ea/**` 独立、非 Gold | 本阶段只显示经服务端授权的执行状态；没有真实质控/Gold 功能 |

> **禁止把“界面示例”“UI 本地状态”“已有测试通过”描述成真实科研放行。** 若 API 未提供状态，界面显示“暂无可核验记录”，不得推断。

## 1. 信息架构（IA）与范围

### 1.1 导航

| 顺序 | 导航名称 | P1.1-A 交付 | 主要承载 |
|---|---|---|---|
| 01 | 工作总览 | **完整合成运营 UI** | 范围选择、任务统计、待办、阻断/异常入口 |
| 02 | 科学资料库 | **受控占位/链接** | 指向已注册合成来源元数据；无原文无真实上传 |
| 03 | 任务中心 | **完整合成运营 UI** | 项目、批次、任务列表、任务创建向导、状态与详情 |
| 04 | Agent 准备 | **受控占位/任务内阶段** | 任务向导中准备步骤复用合成 fixture；无真实模型执行 |
| 05 | 专家与分配 | **受控占位/任务内阶段** | 管理角色任务内分配/发布；无真实人员凭证管理 |
| 06 | 进度与质控 | **受控占位** | 已授权运营状态；无质量评分与 Gold 判定 |
| 07 | 审计与导出 | **受控占位** | `/v1/tpa/audit` 原为 auditor-only，不向 manager 透传 |

左侧始终保留七导航，但占位模块显示“P1.1-B/C 或 P2/P3 扩展中”，不提供假的可点击业务动作。布局与登录态共享 D0 源站，不共享角色授权。

### 1.2 Web URL / 浏览器历史策略

- 入口保持 **GET `/manage`**。由于现有 D0 只提供该受控页面入口，P1.1-A 推荐在页面内使用 **Hash 路由**，不要求服务器新增动态页面 route：
  - `/manage#/overview`
  - `/manage#/projects`
  - `/manage#/projects/{project_id}`
  - `/manage#/projects/{project_id}/batches/{batch_id}`
  - `/manage#/tasks/{task_id}`
  - `/manage#/tasks/new?batch={batch_id}`
- `project_id`、`batch_id`、`task_id` 应仅为不含秘密/患者/答案的合成 ID；URL 不放 Token、来源原文、候选、敏感参数。
- 刷新与浏览器前进/后退能恢复视图；未授权/不存在时显示受控错误，禁止从 UI URL 猜测获得数据。
- API 始终走同源 `/v1/tpa/**` cookie + CSRF + Origin/Host；Hash 路由**只是 UI 导航**，不构成授权。

### 1.3 响应式外壳

- 桌面 ≥ 1280px：左侧导航 224px；内容区 max 1600px；顶部“环境限制 / 当前账号角色 / 刷新 / 退出”；内容按页面自适应，不强行三列。
- 平板 768–1279px：导航可收起，表格必要时横向滚动，关键操作仍可见。
- 手机 360–767px：折叠导航抽屉，卡片替代表格，底部不悬浮危险动作。
- 使用清晰层次：全局标题、面包屑、单一主要 CTA、筛选/排序、任务详情；所有说明以科研人员自然语言为主，技术字段保留在展开“高级信息”中。

## 2. 页面 O-01｜工作总览（Overview）

### 2.1 用户问题

> “我的研究项目目前在哪个阶段？哪些任务阻塞？我应该优先处理什么？”

### 2.2 页面结构（从上至下）

| 区域 | 组件 ID | 展示内容 | 数据与交互 | 空/异常态 |
|---|---|---|---|---|
| 全局头 | `O01-HEADER` | 产品标识、合成环境警示、账号角色、退出 | `/v1/session`、`/v1/tpa/status`；身份变化清除私有缓存 | 未授权返回登录/403 |
| 范围筛选 | `O01-SCOPE` | 选择“全部可见项目 / 单项目 / 单批次” | project/batch scoped summary（新）；过滤权限在后端实施 | 无可见项目→空状态 |
| 状态卡 | `O01-KPI` | 准备中、待分配、已分配未发布、已发布、已撤销、阻断/失败 | 服务器认可的任务状态快照；卡片点击带筛选跳任务中心 | 未支持的指标显式 N/A |
| 待办区 | `O01-ACTIONS` | producer：草稿待验证/冻结/准备；manager：待分配/待发布 | 依据**实际角色**动态渲染；按钮前二次校验 | 无待办→“当前无可处理事项” |
| 最近活动 | `O01-ACTIVITY` | 经授权的创建/冻结/分配/发布等**安全回执摘要** | 不读取 `/v1/tpa/audit` 角色隔离数据；若无合法摘要 API，先隐藏模块 | 不显示未经授权的日志 |
| 问题/阻断 | `O01-BLOCKS` | 任务服务器拒绝、未知状态、流程 HOLD；显示安全错误码与解决动作 | 不产生错误信息泄露；当前 P1 无独立 Blocker 实体 → 仅来自授权回执/实时操作，不杜撰历史 | 无阻断源→“尚未建立历史阻断统计” |

### 2.3 状态卡精确定义

- **准备中**：`DRAFT` + `VALIDATED` + `DEFINITION_FROZEN`。
- **待分配**：`READY_FOR_ASSIGNMENT`。
- **已分配未发布**：`ASSIGNED`。
- **已发布**：`PUBLISHED`，表示已发放授权，**不等于已打开/已阅读/已完成**。
- **已撤销**：`REVOKED`，表示停止未来访问；不抹除既往暴露。
- **阻断/失败**：**只统计有持久化、经过服务端授权的记录**。不可由页面计算“无报告错误即零阻断”。
- 所有计数显示“合成工程任务”；不得显示成“真实专家完成率”“准确率”或“Gold 合格率”。

### 2.4 角色行为

- `producer`：CTA `新建合成任务` / `待验证` / `待冻结` / `待准备`；不能 assign/publish/revoke。
- `manager`：CTA `待分配` / `待发布` / `撤销授权`；不能 draft/validate/freeze/prepare；manager 不能读取完整原文或专家候选。
- `expert`、`r0/r1/r2`、`auditor`：管理端禁止进入；审计员使用原有独立 `/v1/tpa/audit` 授权边界，本阶段不引入“查看所有资料”能力。

## 3. 页面 P-01｜项目与批次（Project / Batch Index）

### 3.1 用户问题

> “我的研究按哪些项目开展，每个项目包含哪些批次，哪批任务现在需要处理？”

### 3.2 页面结构

| 区域 | 组件 ID | 内容 | 核心操作 |
|---|---|---|---|
| 页头 | `P01-TITLE` | 项目列表 / 合成研究运营组织 | `producer` 可新建合成项目；manager 只读项目组织信息 |
| 搜索筛选 | `P01-FILTER` | 项目名/ID、状态、负责人（合成 actor）、更新时间 | 服务端分页/筛选；不加载全部数据进行越权过滤 |
| 项目表/卡片 | `P01-LIST` | 名称、ID、创建者、包含批次数、任务计数、最近活动 | 点项目进入项目详情 |
| 项目详情 | `P01-DETAIL` | Project 元数据、批次列表、可处理任务聚合 | `producer` 新建批次；进入批次 |
| 批次详情 | `P01-BATCH` | Batch ID、项目、任务数、任务状态分布、任务入口 | `producer` 新建任务；发起批量草稿（≤7 条，仍原子） |

### 3.3 新建项目字段（仅合成运营元数据）

| 字段 | 必填 | UI 校验 | 后端要求 |
|---|---|---|---|
| `project_id` | 是 | `PRJ-SYN-` + 3–40 位 A-Z/0-9/-，只读自动生成，可复制 | 唯一性，创建后不可变 |
| `name` | 是 | 2–100 字符，纯文本；禁止个人信息/答案性内容 | 保存**安全展示文本**；不向未授权角色透露 |
| `description` | 否 | ≤ 500 字，明确“不得包含患者信息、科学答案、私人源文” | 服务端限制长度并过滤越权输出 |
| `owner_actor` | 服务器赋值 | 不提供下拉绕过角色 | 仅 actor ID，禁止任意指定他人 |
| `lifecycle` | 自动 | `ACTIVE` / `ARCHIVED`（未来归档只影响运营组织） | 不触碰已冻结 TaskDefinitionRevision |

**不新增科学研究协议、实验分组或临床受试者实体**，Project 是运营分组容器。

### 3.4 新建批次字段

| 字段 | 必填 | UI 校验 | 后端要求 |
|---|---|---|---|
| `batch_id` | 是 | `BATCH-SYN-` + 3–40 位 A-Z/0-9/- | 唯一、不可变 |
| `project_id` | 是 | 必须来自有权访问的项目 | 外键/ACL 服务端验证 |
| `label` | 是 | 2–100 字纯文本；展示用 | 不作为实验 arm/blinding 标识 |
| `purpose` | 否 | ≤500 字，非敏感内容 | 后端文本长度、审计 |
| `created_by` / `created_at` | 自动 | 只读 | 服务端写入 |
| `mode` | 可选展示筛选 | Agent 复核 / 独立专家，两种模式可在同一运营批次，但分配与暴露由单 Task 控制 | 批次不自动覆盖子任务的 `workflow_strategy` |

**区分两种批次**：
- `BatchRegistry`：持久化科研运营分组，容纳任意数量受控创建的任务；**P1.1-A 新增**。
- 现有 `POST /v1/tpa/batches/drafts`：一次提交 1–7 个草稿的**原子批量操作回执**；不等价于长期 BatchRegistry，不得静默改写其幂等/原子语义。

### 3.5 批次/任务关联规则

- 只有 `producer` 可创建项目、批次及将**新建草稿**纳入授权的 BatchRegistry；现有任务在关联前必须满足迁移资格与不可变性策略。
- 关联采用服务端持久化的 `(project_id, batch_id, task_id, task_revision_id)`；不依赖 ID 字符串前缀猜测，也不依赖浏览器 localStorage 作为唯一来源。
- **已冻结或已发布任务不得通过换批次改变知识截止、来源、策略或可访问性。** 后续“运营展示重分组”如确有必要，必须是审计化映射变更，不改变原 TaskDefinitionRevision；P1.1-A 默认不提供该功能。
- 对 P1 遗留任务：呈现“未归档至项目（Legacy）”虚拟视图；有可靠原始 batch 事件关联的任务可提供审计化只读展示；禁止悄悄把历史任务归到新批次。
- 在一个页面同时展示 Agent 审核和独立标注任务时，遵守不同角色/arm 的元数据投影；对专家端仍不得暴露跨 arm 候选信息。

## 4. 页面 T-01｜任务列表与任务详情（Task Center）

### 4.1 任务列表

| 组件 | 精确定义 |
|---|---|
| 面包屑 | `项目 > 批次 > 任务`，筛选不丢失上下文 |
| 搜索 | 精确 ID / 安全标题检索；服务端范围过滤；空结果有重置筛选 |
| 筛选 | Project、Batch、状态、来源类型、Profile、工作模式、分配状态 |
| 排序 | 创建时间（默认新→旧）、更新时间、Task ID；后端稳定排序 |
| 列 | 任务 ID、项目/批次、来源类型、Profile、工作模式、定义修订、状态、受分配者（角色许可时）、下一步动作 |
| 操作 | 点击进入详情；只有符合角色/状态的行操作可用；二次服务端验证 |
| 分页 | ≥ 25 条时服务端分页，带可见总数；禁止未经授权拉取全库 |
| 批量操作 | 本阶段仅“批量创建草稿”，不可批量冻结/发布；保留原 API all-or-nothing / idempotent |

### 4.2 单任务详情页区块

- 头部：Task ID、revision ID、state、所属项目/批次、环境 `SYNTHETIC ONLY`。
- **定义概览**：`task_kind=EVIDENCE_ECOSYSTEM_CASE`、`profile_id`、来源 ID+revision+canonical SHA 摘要、知识截止 UTC、策略（Agent/Independent）。来源原文不出现在管理会话。
- **分阶段进度**：草稿 → 验证 → 冻结 → 准备 → 分配 → 发布。只渲染**实际服务器状态**，不根据顺序自动宣称未来环节通过。
- **阶段操作**：每一步展示可执行角色、前置条件、按钮、回执摘要、阻断原因；producer 与 manager 之间以“需管理员继续处理”交接。
- **历史记录**：仅使用授权安全回执；若无 task-scoped timeline 接口，显示“此版本暂不提供历史时间线”，不读取全量 auditor 审计接口。
- **危险操作**：manager 撤销未来访问权限，要求二次确认，展示“不能消除历史暴露”；禁止删除冻结任务。
- **不可变性**：冻结后不允许修改已授权来源、知识截止时间、任务策略、Profile；改动需新 TaskDefinitionRevision（**P1.1-A 不实现新的 r2 编辑功能**）。

### 4.3 真实状态字典（直接映射现有 TPA Runtime）

| 原始 state | 中文标签 | 页面“下一步” | 操作者 |
|---|---|---|---|
| `DRAFT` | 草稿待核验 | 验证任务 | producer |
| `VALIDATED` | 定义已验证 | 冻结任务定义 | producer |
| `DEFINITION_FROZEN` | 定义已冻结 | 准备工作包 | producer |
| `READY_FOR_ASSIGNMENT` | 工作包已准备 | 分配合成专家 | manager |
| `ASSIGNED` | 已分配待发布 | 发布授权 | manager |
| `PUBLISHED` | 已发布可访问 | 查看安全状态 / 必要时撤销 | manager |
| `REVOKED` | 后续访问已撤销 | 只读留痕 | manager |

**强制术语区分**：`PUBLISHED ≠ OPENED ≠ READ ≠ REVIEW_SUBMITTED`；目前列表只有 `PUBLISHED` 等运营状态，无法无证据展示“已阅读/已完成”。`DEFINITION_FROZEN` 和 `READY_FOR_ASSIGNMENT` 也不意味着真实来源已科学合格。

## 5. 页面 T-02｜新建任务向导（Wizard）

> 向导仍调用原 D0 `/v1/tpa/**` 合成 API；不会创建一个独立应用或更改后端科学合同。

### 5.1 操作分五步；分为两个有权限的会话阶段

| 步骤 | 页面内容 | 输入/只读字段 | 主动作 | 角色与状态门 |
|---|---|---|---|---|
| S1 选择来源 | 项目/批次上下文、主来源、可选授权辅助来源、版本摘要、类型和 rights | 来源选择；无自由文本原文 | `下一步` | producer；只列合成已注册源 |
| S2 任务定义 | 任务 ID、`task_kind`、自动 profile、知识截止 UTC、工作模式、授权来源汇总 | ID、cutoff、Agent 复核/专家独立；Profile 只读 | `创建草稿` | producer；调用 `/tasks/drafts` |
| S3 验证/冻结 | 校验回执、失败原因、不可变信息预览 | 全字段只读确认 | `验证任务` → `冻结任务定义` | producer；状态分别为 `DRAFT`、`VALIDATED` |
| S4 准备工作包 | Agent 合成预置候选 / 独立无候选包，标记不是真实 LLM | 只读策略、合成准备摘要 | `准备工作包` | producer；`DEFINITION_FROZEN` → `READY_FOR_ASSIGNMENT` |
| S5 分配/发布 | 分配规则、合成 expert actor、发布边界和回执 | 预置合成 actor 只读/受控、不可任意绕过盲法 | `分配` → `发布` | **manager 独立登录会话**；`READY_FOR_ASSIGNMENT` → `ASSIGNED` → `PUBLISHED` |

**跨角色交接**：producer 完成 S4 后，页面显示“已准备，等待 manager 分配/发布”，附任务链接；不可在 producer 会话提供可执行的 manager 按钮。Manager 打开该链接进入同一任务详情的 S5；不要求或暗示切换账号可共享越权操作。

### 5.2 S1 输入和验证

- 下拉只从 `GET /v1/tpa/sources` 加载已注册 `SYNTHETIC_FIXTURE`；source type、revision、SHA 摘要可见，**原文和候选不可见**。
- 选择主源后 `profile_id` 从该源服务器返回属性自动设置；用户不能自由编辑以规避 Profile gate。
- 可选第二来源；不得重复同一个 `(source_id, revision_id)`；最多 7 个已授权版本由服务端规则限定。P1.1-A UI 可先保持“主 + 一份辅助”，服务端仍验证完整 allowlist。
- `available_at > knowledge_cutoff` 拒绝；辅助来源也必须逐一验证。翻译与 PDF bbox 不代表权威原文。
- `POST /v1/tpa/source-imports/validate` 仅允许对**已存在合成源**进行身份与 Hash 验证，不是上传/导入真实 PDF。

### 5.3 S2 字段字典及默认值

| 字段 | 类型/规则 | 默认 | 不合法提示 |
|---|---|---|---|
| `task_id` | `TPA-SYN-[A-Z0-9-]{3,50}`，唯一，不含患者资料 | 生成 UUID 短码 | 编号格式错误/已存在 |
| `task_kind` | 固定 `EVIDENCE_ECOSYSTEM_CASE` | 固定 | 不可修改 |
| `primary_source` | 选定 source_id + revision_id | 无 | 请先选资料 |
| `allowed_source_versions` | 版本 + canonical SHA 列表 | 包含主源 | 来源版本缺失或重复 |
| `profile_id` | 从主源类型决定 | 只读 | 来源类型和 Profile 不匹配 |
| `knowledge_cutoff` | 必须是有明确时区的 ISO 8601；显示本地时间 + UTC 确认 | **不自动使用现在作为科学截止时间**；用户手动确定，或仅在演示种子任务使用显式合成值 | 截止时间格式/来源发布时间不合法 |
| `workflow_strategy` | `AGENT_PROPOSE_EXPERT_VERIFY` / `HUMAN_INDEPENDENT` | 必须主动选择，避免自动落入候选模式 | 必须选择工作模式 |
| `project_id` / `batch_id` | 新增运营关联 | 从进入上下文带入 | 未选择已授权项目与批次 |

**注意**：不能将任务 cutoff 的默认值设置为浏览器当前时刻来替代科学设计；必须明确该任务所允许的知识边界。在 P1 合成演示中仍通过服务器时序验证。

### 5.4 S3/S4/S5 写操作反馈

- 成功回执展示 `action`、`task_id`、旧/新状态、`task_revision_id`（如可提供）、服务器时间、回执/Hash（如已存在）。
- 各动作保存期间禁用重复提交，刷新后由服务端重新获取状态；不得仅靠浏览器步骤变量推进。
- `assign` 和 `publish` 的 `idempotency_key` **同一用户意图重试必须复用**，不能在网络超时后重新随机生成造成重复或冲突；新业务意图才生成新 key。
- `revoke` 需要确定/取消弹层，提交成功后保留“历史访问无法撤销”的提示及实际审计记录。
- `prepare` 如为 Agent 路径，P1 明示 `SYN-FIXTURE-NOT-AN-LLM`；独立路径**不能包含候选对象、数量、Hash 或 Agent 提示**。

## 6. 角色与功能矩阵（P1.1-A）

| 行为/信息 | producer | manager | EA expert | NDS r0/r1/r2 | auditor |
|---|---|---|---|---|---|
| 进入 `/manage` 数据视图 | 允许 | 允许 | 拒绝 | 拒绝 | 拒绝 |
| 查看合成来源元数据 | 允许 | 允许 | 仅自身任务投影，经 EA API | 不可看 EA | 拒绝 |
| 新建项目/批次、草稿 | 允许 | 只读 | 拒绝 | 拒绝 | 拒绝 |
| 任务 validate/freeze/prepare | 允许 | 拒绝 | 拒绝 | 拒绝 | 拒绝 |
| assign/publish/revoke | 拒绝 | 允许 | 拒绝 | 拒绝 | 拒绝 |
| 阅读专家 EA 来源全文 | 仅原 EA 生产者授权路径，不在管理 UI 展示 | **拒绝** | 发布且获授权后允许 | 拒绝 | 拒绝 |
| 读取独立组 Agent 候选/元数据 | **不投影给独立组** | **不投影** | **拒绝** | 拒绝 | 拒绝 |
| 修改专家判断/创建 Gold | 拒绝 | 拒绝 | 只能提交自身非 Gold 评审 | NDS 独立路径 | 非本模块 |
| 查看完整 `/v1/tpa/audit` | 拒绝 | 拒绝 | 拒绝 | 拒绝 | 仅原专门审计角色 |

UI 的权限按钮与服务端 Authorization 必须完全一致；隐藏按钮不能替代 API 拒绝。任一管理端 API 禁止返回原文 units、原始 PDF、Agent 非授权候选和“答案提示”字段。

## 7. 必需的最小 API/数据扩展（**建议，尚未实现**）

### 7.1 保持原 API 原样

- `GET /v1/tpa/status`, `/sources`, `/tasks`, `/batches`
- `POST /v1/tpa/source-imports/validate`
- `POST /v1/tpa/tasks/drafts`，`/tasks/{id}/validate`，`/freeze`，`/prepare`，`/assign`，`/publish`，`/revoke`
- `POST /v1/tpa/batches/drafts`（1–7 条，原子、幂等）
- `/v1/tpa/audit` 仍为 auditor-only；`/v1/ea/**` 专家执行保持不变。

### 7.2 P1.1-A 新增的运营 API（草案）

| Method + endpoint（草案） | 调用角色 | 作用与返回约束 |
|---|---|---|
| `GET /v1/tpa/projects` | manager/producer | 只列授权合成运营项目，分页/过滤 |
| `POST /v1/tpa/projects` | producer | 创建 Project，唯一、幂等、审计；禁止修改科学 Task |
| `GET /v1/tpa/projects/{id}` | manager/producer | 项目安全元数据与聚合，不含原文 |
| `GET /v1/tpa/projects/{id}/batches` | manager/producer | 项目下批次列表 |
| `POST /v1/tpa/projects/{id}/batches` | producer | 创建运营批次、不可变 ID、审计 |
| `GET /v1/tpa/projects/{id}/batches/{bid}` | manager/producer | 批次安全元数据、任务 ID 关联 |
| `GET /v1/tpa/overview?project_id=&batch_id=` | manager/producer | 服务端计算安全聚合；可见范围权限先行 |
| `GET /v1/tpa/tasks/{id}/management` | manager/producer | 单任务授权详情与可用操作，不含来源全文/候选 |
| `GET /v1/tpa/tasks?project_id=&batch_id=&state=&cursor=` | manager/producer | 复用原列表路由的**可选**过滤参数，返回 pagination；不得改变旧无参行为 |
| `POST /v1/tpa/task-placements` | producer | 将**新草稿**放入有权访问的项目/批次，或者在草稿创建事务中原子绑定；必须保证“任务创建+关联”不出现孤儿 |

**实施偏好**：为避免“先创建任务后关联失败”，优先设计 **单事务 `create_draft_in_batch`**，在 TPA 运营存储中对项目/批次/任务绑定一次提交，保留原 `tasks/drafts` 的旧协议和独立调用兼容性；独立 `task-placements` 只能用于受限的安全迁移/关联流程。不得在前端拼接多 API 并宣称原子成功。

### 7.3 持久化与迁移（建议）

- 在**同一私有 D0 运营数据库**内使用 `tpa_projects`, `tpa_batch_registry`, `tpa_task_placement` 等运营表或等价结构；现有 `tpa_tasks` / `tpa_events` / `tpa_idempotency` / `tpa_batches` 原样兼容，迁移为新增表/列的保守升级。
- 新运营写入使用 server-authenticated actor、幂等 request key、事务、唯一约束、追加式审计回执；原有不可变审计表的 UPDATE/DELETE 触发器不能弱化。
- Project/Batch 元数据不能提供来源和专家的额外读权限；Project/Batch ACL 是列表收敛，不能扩大已有 TaskSourceProjection。
- `tpa_task_placement` 与 TaskDefinitionRevision 的哈希绑定，应确保关联不会换入另一来源/另一个 cutoff/策略；不可变任务的项目重新归档必须有独立授权与审计，P1.1-A 默认禁止。
- 发布界面/统计必须从后端工作流真实记录派生，而非 localStorage/浏览器缓存。私有工作空间升级前做加密备份并验证恢复，回滚兼容。
- **不要把实验随机化、专家 Gold、SourceQualificationRecord 放在新增 Project/Batch 模型里。**

### 7.4 UI 与 API 契约兼容性

- 先写适配层 response mapper 和 OpenAPI/Pydantic contract tests，保证旧 `GET /v1/tpa/tasks` 的字段、身份/403、原 `POST` 体不被破坏。
- 新列表 query 参数默认空时保持现有任务视图；新新增字段可选，无法提供时 UI 显示“未记录”，不能伪填。
- BatchRegistry 不能取代 `tpa_batches` 的批量创建 receipt；若一批含 >7 个任务，拆成多次**有明确定义的运营子批次操作**，不能声称多次 API 调用总体原子。

## 8. 关键界面状态与错误提示

| 场景/状态 | UI 行为 | 服务端保护 |
|---|---|---|
| 首次空项目 | 展示“暂无项目”，producer 可创建；manager 只读 | 授权后的空结果 |
| 无批次 | 引导创建批次，禁止跳过 project/batch 直接声称已归属 | 校验外键和权限 |
| 无合成来源 | 禁用创建任务，并说明目前没有可用来源 | 不借真实上传绕过 synthetic gate |
| 401 会话失效 | 安全清空页面私有缓存，回到登录页 | cookie/session/CSRF 保持原 D0 机制 |
| 403 权限不足 | 明示“当前账号无此操作权限”，不暴露拒绝资源详情 | API role/task ACL deny |
| 409 状态冲突 | 更新任务真实状态，展示原动作未生效和重试/刷新入口 | 原事务不产生部分副作用 |
| 422 请求格式不合法 | 字段级提示，敏感 server error 不回显 | 严格 body schema、参数校验 |
| 网络请求超时 | 保留上下文和 idempotency key，先查状态/回执再决定重试 | 不生成新请求意图 |
| S2 草稿填写未保存离开 | 二次确认，返回后不宣称服务端已保存 | local draft 只当临时 UI 状态，不能携原文跨角色共享 |
| 定义已冻结 | 输入只读，提供“新版本需独立操作”说明；不出现修改已冻结对象按钮 | immutable definition |
| 发布后撤销 | 必须确认历史阅读不可抹除，结果显示 `REVOKED` | 保留 exposure ledger |
| Agent/独立组切换 | 草稿可切换；冻结后不可切换，独立组 UI/API 不返候选痕迹 | projection deny |
| 切换账号 | 清空私有筛选缓存、回执、未保存草稿和隐藏的敏感结果 | 不复用跨账户数据 |
| 未启用模块点击 | 只展示阶段说明、无伪操作按钮 | 无未实施的 API 调用 |

### 8.1 对应错误码参考（后端已存在的常见码）

- `ROLE_FORBIDDEN` → “当前角色不能执行此操作。”
- `SOURCE_NOT_REGISTERED` / `SOURCE_REVISION_MISMATCH` → “来源不存在或版本校验失败，请刷新来源版本。”
- `FUTURE_SOURCE_AT_CUTOFF` → “资料公开时间晚于任务知识截止时间。”
- `PROFILE_SOURCE_TYPE_MISMATCH` → “资料类型与任务 Profile 不匹配。”
- `INVALID_TASK_TRANSITION` → “任务状态已变化，请刷新后继续。”
- `TASK_ALREADY_EXISTS` → “编号已存在，请生成新任务编号。”
- `CANDIDATES_NOT_FROZEN` → “Agent 候选尚未冻结，不能发布。”
- `DENY_INDEPENDENT_AGENT_EXPOSURE` → “独立标注任务检测到候选暴露风险，操作被阻止。”
- `IDEMPOTENCY_CONFLICT` → “请求已存在且内容不一致，无法作为同一操作重试。”
- `SYNTHETIC_ONLY_REAL_SOURCE_DENY` → “当前仅允许登记的合成资料。”

错误码映射需以 backend 的正式枚举为准，未知错误使用通用错误信息和可追踪的安全 request ID；不得将敏感堆栈展示给用户。

## 9. 页面交互规范和可用性

- **术语**：展示“草稿/已验证/已冻结/已准备/已分配/已发布/已撤销”，技术枚举在悬停或高级信息中提供；“发布”只代表访问授权。
- **单主操作原则**：同一区域只突出一个与当前角色和状态匹配的 CTA；下一步不可执行则显示受控原因，不给假按钮。
- **避免弹窗过多**：新建项目/批次使用抽屉；任务定义冻结与发布可使用确认对话；撤销使用显式风险文案。
- **列表状态保留**：进入任务详情返回时保留筛选、页码、项目/批次上下文；浏览器 History 支持回退；切账号清空。
- **无障碍**：键盘可达、焦点管理、表单明确 label 和 aria-describedby、错误有 role=alert、至少 WCAG 2.2 AA 对比度目标、状态不能只靠颜色表达；手机触摸目标≥44px。
- **数据透明**：统计注明“合成演练”；页面展示数据刷新时间；无法实时证实的“已阅读/专家完成”等指标不得出现。
- **性能基线**：支持 25–100 行分页和 100+ 任务数据浏览，优先按需加载；项目/批次数据后端过滤，禁止从 `/v1/tpa/audit` 全量拉日志到前端。
- **安全前端**：所有服务端字符串用 textContent，不能 innerHTML 注入；禁 URL/token/原文暴露；不把任何受限制原文、候选、审计存入 localStorage/sessionStorage。

## 10. P1.1-A 实施切片与目录建议（不代表已完成）

| 顺序 | 交付 | 说明 |
|---|---|---|
| A-01 | IA 和路由外壳 | 保留 `/manage` 入口；增加 hash-router，七模块导航和登录守卫 |
| A-02 | 运营 Project/Batch 最小合约 + 存储 | synthetic-only、新实体/ACL/事件/迁移/回滚 |
| A-03 | 总览安全聚合 | 仅可证实的状态计数与角色待办 |
| A-04 | 项目/批次索引及详情 | CRUD 限于 create/read，immutable IDs；批次内任务视图 |
| A-05 | 任务列表与任务详情 | 过滤、排序、分页、回执、安全状态时间线 |
| A-06 | 五步向导 | 复用原 drafts/validate/freeze/prepare/assign/publish 分角色操作 |
| A-07 | 浏览器/后端/安全回归 | Chromium 桌面/手机，批次/任务兼容，严格盲法与 NDS 不回归 |

推荐文件边界：在 `apps/workbench/d0/` 内对管理层做增量实现，例如 `web/manage.html`、`web/tpa_manage.js`、`web/tpa_manage.css` 和新增 `tpa_project_runtime.py` / `tpa_project_adapter.py` / tests（名称为建议）；保留 `d0_app.py` 现有会话/安全中间件，不另启服务/端口。

## 11. 可执行验收矩阵（提议的测试 ID）

> **注意：下表是要在 P1.1-A 实施时新增并运行的测试，不是“已经 PASS”。** 原 P1 的 21 项 Python 和 Chromium 成功属于旧阶段。

| ID | 验收场景 | 通过标准 |
|---|---|---|
| `A-UI-01` | 已登录 producer 打开 `/manage#/overview` | 正确七导航、角色和合成环境标识，无来源原文 |
| `A-UI-02` | 通过 hash 路由在 overview / project / batch / task 返回 | 刷新及浏览器前进/后退保留正确页面，权限不丢失 |
| `A-UI-03` | producer 新建项目与批次 | 服务端生成持久化、可分页检索，UUID/ID 无重复，审计 actor |
| `A-UI-04` | 同批次建立合成单任务 | task 与 project/batch 服务端原子绑定，无孤儿 |
| `A-UI-05` | 单任务 S1 选择两份授权来源 | 明确 SHA/版本；不出现 PDF 原文/候选泄露 |
| `A-UI-06` | S2 创建 Agent 复核草稿 | 正确 `EVIDENCE_ECOSYSTEM_CASE`、自动 Profile、显式 cutoff 和 mode |
| `A-UI-07` | S2 创建独立专家草稿 | 不带 Agent 候选/数量/Hash/元数据，服务端投影也不可见 |
| `A-UI-08` | S3 validate/freeze 后尝试修改定义 | 定义只读、服务端不可变；无静默修改 |
| `A-UI-09` | S4 prepare、producer 试图 assign | prepare 可执行；assign 请求 403，UI 显示“待管理员” |
| `A-UI-10` | manager 打开 S5 分配并发布 | 正确两阶段状态和后端回执；真实专家未启用 |
| `A-UI-11` | 网络超时后重试 publish | 同 idempotency key 对同一意图只产生一条发布事务 |
| `A-UI-12` | manager 撤销 PUBLISHED 任务 | 未来访问 403；历史暴露/回执仍可审计；页面不显示“未打开”推断 |
| `A-UI-13` | manager/EA/NDS/auditor 越权尝试 | UI 不显示越权操作，服务端 403；manager 无原文/候选 |
| `A-UI-14` | 来源 cutoff 晚于允许日期/版本 SHA 改动 | 服务器拒绝且无草稿污染，显示准确错误 |
| `A-UI-15` | 批量草稿重复同 key / 部分条目非法 | 原 `batches/drafts` 全有或全无，同 key 同回执，无双重创建 |
| `A-UI-16` | P1 遗留任务列表 | 显示 Legacy 视图，不自动伪造 project/batch 归属 |
| `A-UI-17` | Dashboard 统计 vs 服务端状态 | 准备中/待分配/已发布/撤销计数一致；不混淆 opened/read/submitted |
| `A-UI-18` | 真实 PDF/PHI 或真正 Agent 作业入口 | 禁止且显式标注 P2/P3；不能从新 UI 绕过原 gate |
| `A-UI-19` | 原 D0 EA 三栏、PDF.js、双语、锚点、NDS 19-field | 与原 P1 对照，全部 non-regression PASS |
| `A-UI-20` | Desktop 1440×900，tablet 1024，mobile 390×844，键盘 | 关键导航/表单/错误/焦点/列表无丢失或水平裁剪；无 page_errors |
| `A-UI-21` | XSS 字符串、哈希 URL 注入、响应错误状态 | 无任意 HTML 执行、越权数据读取或错误中敏感信息泄露 |
| `A-UI-22` | 切换 manager/producer 会话 | 缓存被清理，旧角色操作与私有结果不再呈现 |
| `A-UI-23` | 数据库升级、备份与回滚 | 既有合成任务/批次回执保留，现有 Audit、盲法和账号不退化 |
| `A-UI-24` | 旧 API 向后兼容 | P1 tests（21 项）+ 原 D0/EA/NDS/engine suite + Chromium 全 PASS |

**P1.1-A 工程验收判定**：A-UI-01～24 均需真实执行、日志可复现且无高严重级泄露；任何安全、来源、盲法或不可变性 Kill Test 失败即 `NO-GO`。不得将“设计完成”写成“工程验收通过”。

## 12. 交付判定与下一阶段接口

### 12.1 本文件的完成条件

- 三级 IA、七导航与 P1.1-A 范围明确。
- Overview、Project/Batch、Task List/Detail、五步 Wizard 的组件、字段、权限、空/异常态已明确。
- 现有 P1 API 与 P1.1-A 必需的 proposal delta 分开陈述。
- Synthetic-only、Strict-Blind、原文权威、不可变冻结、非 Gold 与 NDS 隔离均可追溯。
- 有能够交给 Codex 的实现切片及 24 项可执行验收目标。

### 12.2 不构成本文件放行的事项

- 本文件**不**包含 P1.1-A UI 代码提交、数据库迁移、浏览器验收或真实部署。
- 项目与批次语义属于**P1.1 新增运营合约提案**，不是假定 P1 已存在；正式冻结须完成最小合约影响审查，确认不侵犯 P0 已冻结规则。
- 本文未授权真实 MinerU 源文件上传、原件全段双语资格认定、真实 Agent 候选、真实专家资格、正式科学研究或 Gold 构建。

### 12.3 下一步实施输入

Codex 需读取并遵守：

1. 本文件（P1.1-A 页面级规范）。
2. `docs/workbench/WB-TPA-v0.1_P0_Task_Production_Assignment_Normative_Design_Freeze.md`。
3. `docs/workbench/contracts/WB-TPA-P0_v0.1.json`。
4. `docs/workbench/WB-TPA-P1_Synthetic_Management_Engineering_Acceptance_Receipt_v0.1.md`。
5. `apps/workbench/d0/{README.md,d0_app.py,tpa_adapter.py,tpa_runtime.py}`。
6. `apps/workbench/d0/web/{manage.html,tpa_manage.js,tpa_manage.css,index.html,reader.js,workbench.js}`。
7. `apps/workbench/d0/tests/{test_d0.py,test_ea_integrated.py,test_tpa_integrated.py,browser_d0.py}`。

**推荐后续命名**：`WB-TPA-P1.1-A1｜Minimum Operational Contract Delta & Non-Regression Plan` → `A2｜Layout / Routes / Project–Batch–Task Runtime` → `A3｜Role-Safe Chromium Acceptance`。

---

*文档状态：页面级设计规范已形成；须在实现前审核新增运营对象和 API 的最小科学/安全影响。*