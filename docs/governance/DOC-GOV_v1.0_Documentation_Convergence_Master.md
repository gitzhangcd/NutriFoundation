# DOC-GOV v1.0｜Documentation Convergence, Canonical Authority Registry & Living Navigation

> 日期：2026-10-15  
> 状态：**IMPLEMENTED_AS_REVIEW_CANDIDATE / APPROVAL_PENDING**  
> 治理基础：PR #43–#46 现有 GOV 文档；Workbench 工程观测：PR #48 精确 SHA `b3a9ca0f810ca0f5d517fc907c1800d13c24dac0`  
> 范围：导航、元数据、分类、版本指针、自动校验；**零科学规范正文改写**。

## 1. 本轮直接交付

| WP | 内容 | 本分支事实 | 尚待验收 |
|---|---|---|---|
| D0 | 两份准确 Git 树的文件盘点 | `DOC-GOV_v1.0_Cross_Branch_Inventory.json` 包含 Git blob/path，快照一致性可复核 | 附件和非 Git 私有原件不在公共完整性声明范围 |
| D1 | 项目统一入口 / 按角色阅读 | `README.md`, `docs/README.md`, `docs/workbench/README.md`, `docs/archive/INDEX.md` | 团队真实任务阅读 UX |
| D2 | 科学与工程权威版本指针 | `docs/CURRENT_BASELINE.md` + `DOC-GOV_v1.0_Canonical_Authority_Registry.json` | scientific owner 签署 canonical ref；v2.1 adapter |
| D3 | 冗余和历史指针 | 旧 Master 留原位；为历史/PR48 提供精确 SHA 引用，附分类策略 | 以后独立审阅后才考虑搬迁 |
| D4 | 自动校验 | `scripts/check_doc_governance.py` + doc-only GitHub Actions | CI exact-head green 及 review |
| D5 | 正式收敛 | 此工作包拟独立 Draft PR、继承 PR #46 治理链 | Review → dependency merge → branch integration |

## 2. Canonical authority 并非“最新文件获胜”

| 优先级 | 对象 | Owner | Git 与原文策略 |
|---|---|---|---|
| L0 | SIS R5 / SIS-MED R6 / Nutrition Foundation / AI Nutri | 各科学规范负责人 | 精确原文件 SHA-256 + 受控 canonical ref/tag；不由 Workbench 重新发布 |
| L1 | NDF D0–D2 / NDS R1 | 各科学子程序负责人和独立裁决人员 | `runs/**` 原路径 frozen；明确 protocol applicability |
| L2 | Workbench 系统设计和模块合同 | 工程 owner + 科学适配 reviewer | System Master v0.2 + 4 companions，增量 PR 保留分支身份 |
| L3 | 原始资料和派生工件 | Source Steward / Curator / Auditor | 原件仅允许受控存储；公开 Git 仅放安全元数据 |
| L4 | 审计、CI、部署、报告 | QA / Security / Release/Scientific Owner | 精确 commit、实际工作流运行和人工验收分签 |

**物理文件存在 / Git blob SHA / source SHA256 / science authority / source rights / deployment 是不同事实维度。**

## 3. Living Navigation 的写入纪律

- **项目入口**：根 `README.md` 仅回答是什么、从哪里开始和有哪些 NO-GO；阶段数据跳转 `docs/`。
- **阅读路径**：`docs/README.md` 按 PI、研究生、开发、专家、QA 建议最短路径；不在入口复制整份协议。
- **权威版本**：唯一机器入口为 `Canonical_Authority_Registry.json`，每项绑定明确 `document_id/status/locator/release_gate`。
- **现状说明**：`docs/CURRENT_BASELINE.md` 从 Registry 和 Issue #42 核实写作；不能当成另一份规范。
- **Workbench 技术**：`docs/workbench/README.md` 选 5 份 v0.2 核心规格，其他 PR 作为增量或历史；不得无故提升为“Master”。
- **历史**：`docs/archive/INDEX.md` 只做链接和 supersession，不重命名 `runs/**` 原件。
- **Evidence**：PR、CI、Issue/Artifact 带 sha；旧报告反映报告时间点，不就地篡改旧结论。
- **更新方式**：变更机器 registry + 受影响 index + 新 PR；先验收，再改变 `CURRENT` 指针。

## 4. 本轮两个已知分支的实际关系

```text
PR #41 (Workbench baseline)
  ├── PR #43 → #44 → #45 → #46 (science governance)
  │                     └── DOC-GOV v1.0 review candidate (this work)
  └── PR #47 → #48 (latest V2 reader code/docs)

Main branch: independent, not yet containing complete stacked Workbench branches.
```

因此本轮**从 PR #46 继承治理文件**，对 PR #48 六份新增文档采用不可变 commit URI 索引；不执行不安全的跨 PR merge，也不要求先推代码覆盖文档。等 PR48 通过独立审查，再将其权威文档引用转为单一实际路径。

## 5. 明确重复/漂移类别及收敛策略

| 类型 | 例子 | 处置 |
|---|---|---|
| `CURRENT_DESIGN_CORE` | WB System Master v0.2 + 4 companions | 成套导航，既有版本不可被 P2 单文件暗中取代 |
| `CURRENT_SCIENTIFIC_EXECUTION` | NDF D1 / NDS R1 工作包 | 保留 frozen 原位，状态由科学 owner 定 |
| `CANDIDATE_INCREMENT` | PR #48 V2.0/P1/B4 文档 | 用 SHA 精确引用，待验收后刷新当前指针 |
| `ACCEPTANCE_EVIDENCE` | 过去合成 CI / QA Receipt | 带适用 commit/运行环境，禁止引用成生产全局 PASS |
| `HISTORICAL` | E0.4.x、旧 31-EQ、旧 Demo | 进入历史导航，禁止静默移除或复活为当前 R1 规则 |
| `MISSING_OR_UNQUALIFIED` | v2.1 完整 Master ref / source rights | 标记欠缺，绝不编造文件路径或批准者 |

## 6. 必须保持 OPEN 的科学/工程依赖

1. SIS R5 `181565/3e1da…`、SIS-MED R6 P0.4 `61116/f851…`、NDSF `145696/81426…` 本轮有**用户上传原件字节核验**。原 GOV-0.3 替代版本的差异记录依然正确；不能直接宣布已完成私有规范仓库/科学 owner 批准。
2. AI Nutri v2.1 的唯一完整规范、NDSF adapter、R6 逐条符合性及其可执行 negative tests 仍需要正式版本绑定。
3. NDF D2 Case `r3` vs materialized projection `r2` 未签署关闭。
4. NDS R1 Freeze v0.1 所引用的 Workpack 与当前 v0.2 任务输入不等价；需要 signed compatibility。
5. PR #48 开发及 exact-head CI、独立 390/1440 UX、人机审查不能由 DOC-GOV 签署放行。
6. 真实来源版权/存储、原始 PDF/MinerU、真实合格专家、科学 Gold 和云端部署仍为 NO-GO/UNVERIFIED。

## 7. 自动检查和放行标准

运行 `python scripts/check_doc_governance.py`：

- registry JSON schema key、唯一 document_id、locator/状态完整；
- `available_in_doc_gov_base` 本地文件的 Git blob 字节哈希与基准匹配；
- 用户原件 SHA-256 字符串、长度格式可校验，但**不能替代真实原始文件保存的验收**；
- 受控新文档相对 Markdown 链接指向存在的本地路径；绝对外部 SHA 链接语法正确；
- 双树 snapshot unique path、blob sha 结构与 PR48 新增文档清单；
- CI 比较 PR Diff 是否触碰 `runs/NDF/**`、`runs/NDS/**`、`src/**`、`apps/**`。

**Release**：本 PR 代码/文档可通过 technical tests 才能称 `DOC-GOV_IMPLEMENTED_TECHNICALLY`，另有 `OWNER_RATIFIED`、`MERGED_MAIN`、`DEPLOYED` 独立状态。**不增加 Issue #42 的 7/25**。
