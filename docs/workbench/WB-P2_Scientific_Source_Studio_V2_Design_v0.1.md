# 科学资料管理 V2 · 设计 v0.1

## 目标

在不改动现有「科学资料」栏目（`#/studio` + `p2_source_studio.*`）的前提下，新增独立栏目 **科学资料管理 V2**，使界面贴近 HiFi Demo v1，并接通现有 `/v1/p2/*`，支持合成资料真实工作流。

## 非目标

- 不重写 / 不破坏旧 studio
- 不新开后端 API
- 不开真实 PDF / MinerU / Gold / 专家暴露

## 挂载

| 项 | 值 |
|---|---|
| 侧栏 | `科学资料管理 V2`（旧「科学资料」保留） |
| Hash | `#/studio-v2` |
| 前端 | `p2_source_studio_v2.js` / `.css` |
| API | 既有 `/v1/p2/sources`、`overview`、`rights`、`convert`、`qa`、`freeze`、`audit`、`scope` |

## 分阶

1. **壳 + 队列（本步）**：四页 IA、Demo 级队列/详情；列表读真实 P2 sources
2. **登记 + 权利**：四步向导 POST 登记；Auditor rights
3. **QA 阅读器**：document / original / reviews
4. **谱系 / 冻结 / 审计**：freeze、scope、audit + 15 轴静态矩阵

## 验收（本步）

- 侧栏可进 V2，旧栏目仍可用
- 队列列含 checkbox / 资料资格 / 引用范围等 Demo 列
- 有真实登记时列表显示 API 数据；无数据时可用合成占位说明
- 部署到 `nutriwb-v03` 可截图对照
