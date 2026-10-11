# WB-P1.1-A5｜Management UX Convergence & Expert Handoff — Engineering Acceptance Receipt v0.1

> **日期**：2026-10-11  
> **仓库**：`gitzhangcd/NutriFoundation`  
> **A5 分支**：`workbench-p1.1-a5-management-ux-handoff`  
> **对应 PR**：[#31](https://github.com/gitzhangcd/NutriFoundation/pull/31)（**Draft / 未合并**）  
> **父基线**：B0 Draft PR #30 `df94c2bf9becefbf60e14438e1185a12603559bf`，继承 A4 Draft PR #29  
> **验收代码 SHA**：`c54b4ba31eddd107784b5a7d1540e69debe8079a`  
> **工程判定**：`SYNTHETIC_ENGINEERING_PASS / INDEPENDENT_REVIEW_PENDING`  
> **科学、安全及生产判定**：`REAL_RESEARCH_NO_GO / GOLD_NOT_ELIGIBLE / NO_MAIN_MERGE`。

## 1. 本阶段目标与既有系统继承

本阶段修复 `WB-P1.1-B0` 识别的管理交互差距，**不是新建专家标注系统**。

```text
原 D0 FastAPI + session/CSRF/Origin
├─ /manage — Producer / Manager，同源管理端
│  ├─ Project → OperationalBatch → Task（原事务及不可变关联）
│  ├─ 服务器分页/任务搜索/状态筛选
│  ├─ S1–S5 角色及服务端状态驱动操作
│  └─ 任务详情抽屉与安全专家交接说明
└─ / — 保留原 D0 专家标注三栏页面
   ├─ /v1/ea/** — EA 合成证据模式
   └─ NDS R0/R1/R2 — 独立原有十九字段、双语、PDF.js、SourceAnchor 路径
```

科学不变量：来源原文是唯一权威证据；译文为辅助；管理端只显示合成运营元数据；`HUMAN_INDEPENDENT` 不返回候选、其数量/散列或跨组暴露；`PUBLISHED != OPENED != READ != REVIEW_SUBMITTED`；`scientific_capture=false`；`gold_qualification=NOT_ELIGIBLE`。

## 2. B0 → A5 修复追踪

| B0 缺口 | A5 交付 | 实现锚点 | 验收边界 |
|---|---|---|---|
| B0-04 卡片式任务中心 | 表格 7 列、25 行/页、后端分页、Project/Batch/Legacy 范围和状态/编号查询 | `web/tpa_p11.js` + `tpa_projects.py`、`tpa_adapter.py` | 103 条合成任务分页 Python 测试 |
| B0-05 S3–S5 主要为说明 | S1 来源、S2 草稿、S3 validate/freeze、S4 prepare、S5 manager assign/publish 角色状态驱动；禁止超前的写操作 | `web/tpa_p11.js` | Chromium 浏览器实走原工作流；服务端原状态机保持权威 |
| B0-06 任务详情/回执 | 非模态侧抽屉，项目归属/源版本/全 SHA-256/模式/下一步/关闭及历史导航，Esc 关闭 | `web/tpa_p11.js`, `web/tpa_p11.css` | 浏览器深链接/后退/刷新/两源 SHA |
| B0-06 意图重放与网络故障 | session-scoped 合成元数据与幂等请求键；收到丢失/错误响应时先查服务端状态，草稿需完整不可变定义一致才可恢复 | `web/tpa_manage.js`, `web/tpa_p11.js` | 原生 Chromium 在服务端发布成功后替换响应为 502，验证 UI 归并 |
| B0-07 原 D0 专家交接 | 保留独立 EA 账号、同源 `/`、任务编号、类型化工作流与来源版本说明；不可在 Manager 会话冒充专家 | `web/tpa_p11.js` 和原 `ea_mode.js` | Chromium 发布→独立 EA 会话可见正确任务/两源、原文隔离 |
| B0-08 任务查询规模 | 有界服务端 `limit/offset`、状态 `PREPARING`、检索 `q`；不再在 A5 任务表显示未过滤的全表样本 | `tpa_projects.py`, `tpa_adapter.py` | 103 任务、跨页不重叠、非法查询 422、原无参任务列表响应兼容 |

**明确未实施**：正式研究来源/原始 PDF/MinerU 导入；真实 LLM/Agent 执行与 provenance；临床专家资格与伦理核验；真实患者资料；科学 Gold 的生成及晋级；公网正式部署。这些是 B1–B4 / P2–P3 的独立范围与门。

## 3. 在精确代码 SHA 上观察到的 CI 证据

| CI | 运行链接 | 结果 |
|---|---|---|
| A5 Python + Native Chromium | [38123538199](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38123538199) | **SUCCESS** |
| A5 同 SHA 独立 push 复核 | [38123535482](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38123535482) | **SUCCESS** |
| 原 P1.1-A 工程非回归 | [38123538207](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38123538207) | **SUCCESS** |
| 原 P1 合成管理非回归 | [38123538206](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38123538206) | **SUCCESS** |
| 原 EA D0 集成非回归 | [38123538238](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38123538238) | **SUCCESS** |
| 原 D0 staging/full-engine | [38123538208](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38123538208) | **SUCCESS**（engineering acceptance + full engine 两作业均 success） |

A5 Python：**48 passed**。新增 `test_tpa_a5.py` 验证 103 条合成任务分页、服务器状态过滤、查询错误码、Strict-Blind 与 EA/NDS 角色隔离。

A5 Native Chromium：**88 checks / `page_errors=[]`**。包含桌面 1440、平板 1024、手机 390、PDF.js、原有 19-field、双语和原文证据锚点；新检查包括服务端实际执行 `publish` 后前端响应被 502 替代的恢复，以及管理端抽屉完整两源 SHA 与专家交接指引。保存截图/证据在相应 Actions artifact；**不等价于真人 UX 签字验收**。

首轮测试发现列表非法 `limit=10000` 的 HTTP 状态为 409，预期 422；修复 `tpa_adapter.py` 中该新增过滤路径的错误码映射后 48 项全部通过。保留旧端点无参响应及旧状态机语义。

## 4. 原系统非回归与运维边界

- A5 直接扩展原 `apps/workbench/d0`；未增加新 FastAPI 服务、端口、账号体系或科学真值管道。
- 无变更 `runs/**`、`src/nutrifoundation/**`、`apps/workbench/c1/**`、`apps/workbench/c2_1/**`、`apps/workbench/c2_2/**`。
- 原有 `/v1/tpa/batches/drafts` 七类合成批量回执、Legacy 归属及不可变日志继续保留。
- 不把 task 的发布推断为阅读、完成、来源合格或 Gold；不让管理端读到 EA 的原文、受限候选。
- GitHub Actions 在隔离合成数据上运行；**没有**把 A5 部署到阿里云生产实例，没有以当前 CI 替代生产系统安全审核、真人研究或科学质量鉴定。
- 本轮验收不包含：真实专家阅读理解/可用性试验、真实 100+ 项 Chromium 大规模交互（103 项经服务器测试）、真实系统渗透测试、来源版权/原文翻译科学忠实度、真实 Agent provenance。

## 5. 阶段结论与后续顺序

**A5 可以作为新的合成工程候选基线进入独立代码审查，并作为后续 B1–B4 的开发底座。** 此状态**不**意味着合并 `main` 或真实科研 GO。

建议下一阶段依次：
1. `WB-P1.1-B1｜Scientific Source Library & Source Package Operations`，先做**合成来源包 / 结构化文档 / 版本 lineage**，真实文献授权进入 P2 单独门；
2. `B2｜Synthetic Agent Preparation Operations & Provenance-Shaped Status`；
3. `B3｜Synthetic Expert Roster, Assignment & Exposure-Safe Handoff`；
4. `B4｜Integrated Chromium Acceptance, Failure Recovery & Non-Regression Freeze`；
5. 后续 C 期质控及审计导出；真实 P2/P3 的 source-rights、安全与专家资格独立验收。

**禁止动作**：不要在未获得独立科学/安全审批前合并各个 Workbench Draft PR，开放真实资料导入、线上专家招募或 Gold 晋级。
