# WB-P2｜HTML Demo × PR #37 科学资料栏目界面收敛验收回执 v0.1

**核验日期**：2026-10-12 (Asia/Tokyo)  
**权威基线**：PR #37 `2b1979c3a0486185735cf2b71e404d5f7a6ff56b`  
**验收代码 SHA**：`6e34d7306cd0be702e502e76a91d05d5c00aaebe`  
**交付**：[Draft PR #39](https://github.com/gitzhangcd/NutriFoundation/pull/39)，未合并。  
**结论**：`SYNTHETIC_UI_INTEGRATION_PASS / HUMAN_VISUAL_REVIEW_PENDING / REAL_SOURCE_NO_GO`。

## 1. 精确实现与范围

用户上传的 `nutrifoundation_p2_scientific_source_portal_demo(1).html` 是此次唯一指定的具体页面/交互参照，其中明确有六个导航板块、四步转换链、四种登记入口、四项统计、两栏原件与结构化文档、人工 QA、右侧抽屉和审计时间线。PR #37 管理全局样式、布局、权限和 B1 来源引用是必须保留的实现基线。

PR #39 在此前端基线上完成：默认“资料总览”，四步流程与入口卡、来源登记队列、结构化处理任务列表、原文/IR 双栏高亮与 QA 侧栏、来源库状态筛选及右侧详情/登记抽屉、审计与版本示意，保留 Project/Batch 范围显示与原 manager/producer 投影；把全局菜单“科学资料”设为 P2 入口，原 B1 显式改名“来源引用 · B1”（路由和服务未变）。

只调整既有原 P2 JavaScript/CSS、局部管理导航文案、Chromium 验收测试和受保护文件名单内的文档白名单。**未采纳 PR #38 新增的 P2 后端、独立数据库/认证、真实来源文件准入或 QA 服务。**

## 2. 精确代码 SHA 的 GitHub Actions：9/9 SUCCESS

| Workflow | Run | 判定 |
|---|---|---|
| B4 full D0/EA/TPA/NDS Python + Chromium | [38186175584](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38186175584) | SUCCESS |
| Original EA P1 | [38186175511](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38186175511) | SUCCESS |
| B2 Agent Fixture provenance | [38186175470](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38186175470) | SUCCESS |
| B3 expert assignment/handoff | [38186175472](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38186175472) | SUCCESS |
| A5 original management UI | [38186175479](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38186175479) | SUCCESS |
| TPA P1.1-A | [38186175501](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38186175501) | SUCCESS |
| Original D0 staging & full engine | [38186175507](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38186175507) | SUCCESS |
| TPA P1 | [38186175496](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38186175496) | SUCCESS |
| B1 original SourcePackage | [38186175490](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38186175490) | SUCCESS |

B4 **70 Python passed, 6 warnings**。原生 Chromium **115 checks PASS**、`page_errors=[]`、`native_pdfjs=true`、`scientific_capture=false`。浏览器新断言覆盖上传 Demo 对齐后的四步流程、四种入口、右抽屉、登记与转换队列、两栏 QA 高亮、审计时间线、390px 手机适配及原 B1/Manager 权限不回归。

[真实浏览器截图与结果 Artifact](https://github.com/gitzhangcd/NutriFoundation/actions/runs/38186175584/artifacts/11719269388)，包含 `p2-demo-aligned-overview-desktop.png`、`p2-demo-aligned-overview-mobile.png`、`p2-demo-aligned-qa-two-pane.png` 等。

## 3. 与 PR #38 的责任边界

PR #38 `85579f9172f7220d03493063409a8df5aa7af700` 在当时 GitHub Actions 9 项中 8 项 FAIL，尚未具备验收条件；其更大范围的 `p2_source_registry.py`、`p2_source_adapter.py`、认证修改、Source QA 新入口等不在本次修复中。PR #39 不关闭或自动合并 PR #38，仅提供可信、低侵入的前端交互与布局基线。

## 4. 未完成的真实能力

前端所有 source records、引用与 QA 文本均为虚构演示；无真实文件上传/读取、MinerU、DOI 接口、科学可信 SHA、版权证明、人类 QA 数值验收、真实身份或专家授权。原严格盲法、Agent fixture 非真实 LLM、Gold NOT_ELIGIBLE 保留。

本自动化结论不替代最终人工可用性/视觉比对，亦不代表真实 P2 科学数据准入、生产发布或 GitHub 主干合并。
