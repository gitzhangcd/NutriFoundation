# WB-P1.1-B4｜Integrated Acceptance, Failure Recovery & Non-Regression Freeze

# Final Synthetic Engineering Freeze Receipt v0.1

> **日期**：2026-10-11  
> **Repository**：`gitzhangcd/NutriFoundation`  
> **Branch**：`workbench-p1.1-b4-integration-nonregression-freeze`  
> **PR**：[Draft PR #35](https://github.com/gitzhangcd/NutriFoundation/pull/35)，基于 B3 Draft PR #34  
> **精确验收代码 SHA**：`a9bb15285f4c96746d5bdf4d8ef9a4d883b8ee00`  
> **冻结范围**：`WB-P1.1-B1+B2+B3+B4 SYNTHETIC ENGINEERING ONLY`  
> **冻结结论**：`SYNTHETIC_ENGINEERING_FROZEN`（就当前代码版本的自动化合成工程验收而言）  
> **保留项**：`INDEPENDENT_CODE_AND_SECURITY_REVIEW_PENDING`；`REAL_RESEARCH_NO_GO`、`GOLD_NOT_ELIGIBLE`、`PRODUCTION_NO_GO`、`NO_MAIN_MERGE`

## 1. 与 B3 的准确变更

B4 没有新增 FastAPI、Agent、专家角色、来源导入、任务授权或 UI 功能。相对于 B3 基线 `eb580f69627a3323371dfaaf9847a22154eb8448`，只增加：

1. `apps/workbench/d0/tests/test_tpa_b4_integration.py`：一个真实应用实例联通 B1/B2/B3 + 重启持久化与故障注入的 **6 项集成 Kill 测试**；
2. `.github/workflows/wb-p1-1-b4.yml`：全套 Python、原生 Chromium、原 D0、科学权威树和 B4 范围白名单；
3. `docs/workbench/WB-P1.1-B4_Integrated_Acceptance_Failure_Recovery_and_NonRegression_Freeze_Contract_v0.1.md`：集成准入与冻结边界；
4. 本文档：经真实 CI 支撑的冻结回执。

未改动 `ea_runtime.py`、`ea_seed.py`、EA contract、原 NDS、P1/P1.1 A5/B1/B2/B3 运营代码、原页面 JS、PDF.js 或学术实验冻结目录。

## 2. B4 集成证据与科学边界

**B4-01｜完整贯通**：在同一个 D0 实例中先注册 B1 RCT 合成来源包，再对 Agent 工作流生成原 P1 固定候选并完成 B2 不可变证明；同时运行独立专家模式任务。Manager 使用原 TPA `assign/publish` 授权各自正确合成专家，B3 绑定原 `EXPERT_ASSIGNED` 和 `GRANT_ISSUED` hash 签发交接证明。

**B4-02｜持久化与重启**：构建**新的 FastAPI/Auth/EA/TPA/B1/B2/B3 实例**，指向原 SQLite 数据路径。校验来源包 manifest SHA、B2 candidate-proof SHA、两组 B3 handoff SHA、注册/证明幂等回执均未变化。再次使用独立 cookie 登录验证原 EA 允许正确专家、拒绝跨组专家。

**B4-03｜Strict-Blind / Exposure**：Agent R1 与独立 R0 并存，独立组在 B2 队列中不可见且不能请求候选。原 EA workpack 访问前 `recorded_exposure_events=0`，真正访问后来自原 TPA 的记录会增加，但 `expert_read_or_completed_inferred=false`。原 TPA `revoke` 后未来 EA 访问为 403，历史暴露事件数量与不可变回执保持。

**B4-04｜恶意独立组 Candidate 注入**：测试仅在独立隔离的合成 SQLite fixture 中模拟错误写入 EA CandidateSet。B3 `preview/detail/list/attest` 应 fail closed，B2 禁止任何已知 Task ID 绕过隔离，不能在运营界面“自动修复后继续”。

**B4-05｜真实来源漂移**：测试通过临时移除隔离实例中原 EA 的 UPDATE trigger，并离线篡改原 RCT source SHA 来模拟数据库外部污染；B1、B2、B3 均拒绝错误 Source 版本，旧 Proof/Grant 不得被静默重写。这是故障注入，不是提供正常的源修改 API。

**B4-06｜审计及不可变性**：对 B1/B2/B3 六张 SourcePackage、Attestation、Handoff 与 Replay 表逐一执行 SQL UPDATE/DELETE，均被不可变触发器拒绝；原 TPA 审计链在合成伪造事件写入后报告 `valid=false`。最终重新核对显式合成模式开关和真实 PDF/真实来源拒绝。

以上是**合成工程**杀伤测试，不是现实医疗隐私合规证明，也不是专家标注科学质量验证。

## 3. 验收数值与浏览器证据

所有结果严格对应同一验收代码 SHA `a9bb15285f4c96746d5bdf4d8ef9a4d883b8ee00`。

**B4 Python**：`70 passed, 6 warnings`（warnings 为依赖项弃用提示）。包括原 64 项 B3 及前序回归和新增 B4 6 项集成 Kill 测试。

**Native Chromium**：`103 checks`，`page_errors=[]`，`native_pdfjs=true`，`scientific_capture=false`。继续覆盖原 A5 模拟发布响应丢失后的准确服务端状态恢复、B1 来源包、B2 固定合成候选 provenance、B3 Expert roster/不可变交接、原 EA 独立会话与 PDF.js 阅读器，以及桌面/移动端非回归。

[原生浏览器截图与运行证据 Artifact](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38134366241/artifacts/11700167785)。

## 4. 全部 CI：在相同代码 SHA 下的成功运行

| CI 层 | GitHub Actions | 结论 |
|---|---|---|
| B4 integrated fault injection + original Chromium | [38134366241](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38134366241) | **SUCCESS** |
| B4 independent push run | [38134311713](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38134311713) | **SUCCESS** |
| B3 fixed synthetic expert & handoff | [38134366246](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38134366246) | **SUCCESS** |
| B2 frozen fixture provenance | [38134366233](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38134366233) | **SUCCESS** |
| B1 source packages | [38134366207](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38134366207) | **SUCCESS** |
| A5 management + expert handoff | [38134366208](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38134366208) | **SUCCESS** |
| TPA P1.1-A operations | [38134366216](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38134366216) | **SUCCESS** |
| TPA P1 | [38134366219](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38134366219) | **SUCCESS** |
| EA P1 original D0 | [38134366210](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38134366210) | **SUCCESS** |
| Original D0 engineering + full-engine | [38134366215](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38134366215) | **SUCCESS：两个子作业** |

GitHub Actions 的各历史失败或早期调试记录（如有）均保留；本判定只依据上面相同精确代码 SHA 的独立成功运行。

## 5. 冻结判定

```text
WB-P1.1-B4:
  original_d0_ea_nds_preserved: TRUE
  b1_reference_package: SYNTHETIC_ONLY
  b2_agent_execution: FIXTURE_ONLY_NOT_AN_LLM
  b3_expert_qualification: SYNTHETIC_ACCOUNT_ONLY
  b4_fault_injection_suite: PASS
  python_total: 70_PASS
  chromium_total: 103_PASS
  native_pdfjs: TRUE
  browser_page_errors: 0
  original_full_engine: PASS
  protected_science_trees_unchanged: TRUE
  real_source_import: NO_GO
  real_agent_executed: FALSE
  clinical_experts: NOT_QUALIFIED
  independent_gold: NOT_ELIGIBLE
  scientific_capture: FALSE
  deployment: NO_PRODUCTION
  independent_review: PENDING
  main_merge: NO_GO
  final_decision: SYNTHETIC_ENGINEERING_FROZEN
```

**注意**：`SYNTHETIC_ENGINEERING_FROZEN` 不代表 GitHub 上已创建不可变 tag，也不代表 PR 已合并、外部代码复审、安全审计、真实专家或生产权限放行。GitHub Draft PR #35 仍应保留独立审查闸门；任何修改验收代码都必须以新 SHA 全量重跑 B4 和原 CI。

## 6. 后续工作边界

- **工程冻结后**：把 B1–B4 的任务流、角色投影、不可变来源/候选/专家交接单据当作下一阶段产品定义的运营合同基线。
- **真实来源 P2**：版权、使用权、医学科学来源可靠性、真实 PDF/Markdown/HTML/MinerU 结构化和原文证据锚点。
- **真实专家 P3**：资格认证、临床伦理、访问数据隔离、医生原生判断、盲法历史与多人一致性质量审核。
- **生产 P4**：私有部署、网络密钥与审计、安全渗透测试、灾备与组织权限接入。

B4 不得通过将 `synthetic=false` 或其他配置值反转而冒充完成以上真实准入。
