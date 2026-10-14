# WB-P2｜HiFi Demo v1 4K Package → `/manage#/studio` 对齐说明

> Status: **UI_ALIGNED / AWAITING_CI_AND_VISUAL_ACCEPTANCE / REAL_SOURCE_NO_GO**
>
> Reference package: `NutriFoundation_Scientific_Source_HiFi_Demo_v1_4K_Package.zip`
> Interactive HTML: `docs/workbench/NutriFoundation_Scientific_Source_Workbench_HiFi_Demo_v1.html`

## Demo IA（权威）

四页步进：

1. **工作队列总览** — 列表 + 详情、状态度量、Project/Batch 筛选、五维资格
2. **筛选与来源登记** — 四步登记与准入说明
3. **QA 阅读与锚点核验** — 结构化阅读与逐 Unit QA
4. **版本谱系与审计** — 谱系、审计事件、GOV-0.4 15 轴静态矩阵

全局壳层（侧栏、任务中心、B1、PR #36 青绿风格）保持不变。

## 已落到原 D0 `/manage#/studio` 的变更

| Demo 要素 | 实现 |
|---|---|
| 01–04 步进导航 | `.p2-page-stepper` 四主页 + 转换/规范审计两辅页 |
| 标题「科学资料处理台」 | 各主页面统一 H1 |
| 队列 + 右侧详情 | `.p2-workgrid` + `.p2-inline-detail` + 五维资格 |
| 彩色状态度量 | 待用途审核 / 待结构化 / 待 QA / 阻断 / 已封存 |
| 版本谱系 + 15 轴矩阵 | `audit` 页 `.p2-lineage` + `.p2-matrix-table` |
| 四步登记文案 | 来源身份 / 原始内容 / 许可与用途 / 范围确认 |

## 非目标 / NO-GO

- 不接入真实 PDF、MinerU、DOI 馆藏、Gold、专家授权
- 不合并进 `main`、不部署阿里云，直至 exact-SHA CI + 人工对照 4K 预览通过
- 15 轴矩阵为静态 GOV-0.4 展示；`NOT ASSESSED` 不得被 UI 提升为 PASS

## 验收

1. Chromium 390/680/740/768/1024/1440 原有 P2 断言 + 新增 workgrid / 五维 / 矩阵断言
2. 人工对照包内 `4K_previews/01–07`
3. 角色门禁与 Strict-Blind 回归保持
