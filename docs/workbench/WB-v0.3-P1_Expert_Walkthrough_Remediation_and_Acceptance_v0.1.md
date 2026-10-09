# WB-v0.3 P1｜专家走查纠偏、交互契约与验收记录

**基线**：`workbench-v0.3-p1.3-prototype-ui@45f76f4715d49b8ea96cc68969bc8e988d4e46d6`  
**修复分支**：`workbench-v0.3-p1.3-ux-acceptance-remediation` / [Draft PR #23](https://github.com/gitzhangcd/NutriFoundation/pull/23)  
**范围**：仅合成工程工作流。**不构成正式专家科研采集/Gold/真实翻译/阿里云上线许可**。

## 1. 走查差距（原始判定：P1 部分符合）

| 走查反馈 | 修复内容 | 不可夸大的边界 |
|---|---|---|
| 仅 3 处译文，真实论文整段覆盖 0/154 | 新增一份**独立自编** 16/16 中英文双语练习和两张完整 Markdown 表格的渲染；原真实论文保留原始覆盖信息 | 并未翻译/科学审校原真实论文剩余 154 个单元；自编练习不具有 PDF/SourceAnchor 与科学证据资格 |
| 五组问题及 19 字段仍像表单；证据只到字段 | 增设逐条判断卡、逐条证据选择，并由服务端绑定文本 SHA256、位置和保存的草稿版本 | 不是无限制 Agent 语义自动归类；保留独立原文措辞、19 字段、人工类别选择 |
| 中文到英文摘录、PDF 长引用定位失败 | 保留原文锚点的服务端验证，并将 PDF 唯一匹配作为**额外**精确定位状态；失败给出缩短引用、查看来源提示页等路径 | PDF 提示页不等于经验证的精确 BBox，失败不能展示“核验成功” |
| 表格仍呈 Markdown、无法阅读 | 将 `TABLE` 单元渲染为真实语义表格、数值和行列布局，保留每格原始 UTF-16 偏移供后续引用 | 复杂合并单元格、数学和嵌套格式尚需独立验收 |
| 笔记本页面章节导航空间小 | 调整 820px 高桌面窗口的 sidebar/outline 比例、可滚动空间 | 仍需针对典型笔记本尺寸做人工体验 |
| 侧栏键盘焦点漏出背景 | Evidence 抽屉添加 modal dialog、背景 inert、Tab 循环、Escape 退出及返回焦点 | 必须进行 Chrome、屏幕阅读器等实际可用性复核 |
| 0/5 未保存，却把前 3 步显示已完成并宣称可提交 | `submissionReadiness` 绑定真实数据：当前任务阶段、判断至少一组非空、服务端保存版本、未修改/保存中、用户盲法确认；步骤已完成**仅依据真实冻结后的服务端状态** | 0/5 不能进冻结，前端检查不能替代服务端 freeze gate；不足 5/5 不自动否决有合理不确定性的专家 |
| 返回编辑 | 保留无损返回、draft revision，新增完整链路回归 | 正式真人测试尚未执行 |

## 2. 科学不变量

1. 原有 `R0/R1/R2` 任务与来源权限及 Pre-AI strict blind 不变；`/reading-demo` 走 task-scoped `allowed(...,full=True)`，R1 与未授权用户不可读取。
2. 原始文献 0/154 整段已翻译的覆盖现实必须如实呈现。自编 16/16 合成材料不得冒充这篇真实论文的译文，不能被系统引用到原始 PDF。
3. 19 字段 canonical payload、已有原文锚点、服务端冻结和审计继续权威；新增条目级 binding 以 append-only 表/事件作为非破坏式 sidecar。
4. 一条判断修改后，旧 item-binding 不删除/重写，但返回 `current_statement_matches=false`，前端不得统计为当前判断的有效证据。
5. 步骤导航不是准入收据；点击复核或冻结导航不应伪造 completed 或 ready；服务端未确认冻结时不展示终态完成。
6. PDF BBox 只有经 `VERIFIED_UNIQUE_PDF_TEXT`、源哈希与实际 overlay 匹配时显示验证成功。

## 3. 任务级来源与完整合成练习的分离

```text
R0/R2 task authorization
  ├─ Original paper: real English 154 units; demo excerpts only; actual source anchors + PDF
  └─ Self-authored synthetic bilingual reading exercise: 16/16 EN+ZH + 2 tables
        ├─ no original scientific PDF
        ├─ source_anchor_eligible=false, scientific_capture=false
        └─ cannot bind as paper evidence

R1: candidate-spans only (neither original full text nor synthetic full reading demo)
```

## 4. 条目级证据绑定结构

```text
Task + Expert + Saved Draft Revision
    ├─ Canonical field path
    ├─ Judgment index + SHA256(expert exact statement)
    ├─ SourceAnchor ID + Original Source Revision + PDF SHA
    └─ Immutable audit event; on changed draft mark stale at GET

Existing field-level bindings remain for legacy compatibility.
```

此 sidecar 尚未纳入正式冻结 Scientific Contract 与 Receipt；正式科研资格需要独立 Normative Delta 审核。

## 5. 非回归与待补验收

新增验证：
- C2.1 负面测试：任务范围、R1 权限、未保存版本、条目文本改动、条目链接不可变、过期后的 `current_statement_matches=false`。
- D0 / Node：Markdown 表格行列结构、精确 offset。
- Chromium：0/5 未保存阻断、完成导航不过度宣称、双语自编练习、回到英文文献、字段/条目绑定、PDF、键盘抽屉、原有冻结/角色隔离。
- Frozen science diff：不得修改 `runs/NDF`、`runs/NDS`、`src/nutrifoundation`。

**工程门槛**：最新完整 CI PASS + 真实浏览器走查录屏或至少截图/操作表 + 研究负责人确认 P1 观察项目，才可以将本轮标成“P1 工程完成”；目前 PR 为 Draft。

**真人科学采集门槛**：仍受病例 `r2/r3` 版本分歧、文献资格/版权、真人 IdP/MFA/资格、伦理/同意、支持 OS 和安全审查的独立 NO-GO 门控；本轮不规避。

## 6. 下一批工作

- 完成真实论文的完整结构化段落与专业翻译生产、数值/统计/因果词/医学术语对照审校、版本冻结（严格先资格审查、后授权投影）。
- 让判断条目编辑成为真正独立的卡片，而不是仅提供单条引用视图和原始多行文本；保留无损往返 19 字段。
- 增加支持长引用的多 BBox/人工核查确认 workflow，区分准确失败、节选和上下文。
- 在独立合成 staging（不得覆写阿里云现有 D0）执行 P1 回访，记录非静态数据：任务耗时、定位失败、逐条绑定错误率、认知负担和键盘可用性。

## 7. 已验证自动化执行（2026-10-09）

- 代码提交：`1b32650db1189386a79c772e352e61a8c5cd47ea`
- CI：[GitHub Actions #37884242639](https://github.com/gitzhangcd/NutriFoundation/actions/runs/37884242639)
- Workbench 独立模块共 **118 tests PASS**：C1 11、C2 18、C2.1 47、C2.2 26、D0 16。另有两组正式绑定专项 2+2 PASS，未重复计入模块总数。
- 科学引擎 **144 tests PASS**（Python 3.11）。
- Chromium **26 checks PASS**，包括 0/5 未保存阻断、16/16 自编双语练习及表格、原文切换、聚焦、中文到英文选取、逐条绑定、PDF.js、保存/重载、前后 AI 分离、R0/R1/R2 隔离、冻结和审计；`page_errors=[]`。覆盖 1440×1000 与 390×844。
- 冻结科研代码和 NDF/NDS 路径 Non-Regression 检查 PASS。
- 浏览器证据：[synthetic-only screenshots and log](https://github.com/gitzhangcd/NutriFoundation/actions/runs/37884242639/artifacts/11596045905)。
- 前几轮失败分别涉及错误代码替换造成重复源码、表格测试转义、来源切换竞态、模态抽屉测试、旧 UI 文案断言。全部据失败日志修复，最终整套测试绿灯。不得隐瞒此前失败。

**结论**：合成工程验收 PASS；**P1 科学/真实专家使用体验仍为 PARTIAL / PENDING**。需实机人工可用性试测和真实论文权威双语文本资格，才允许任何正式科研阶段转换。不要直接合并 `main` 或覆盖阿里云现运行服务。
