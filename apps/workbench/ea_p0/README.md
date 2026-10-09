# WB-EA-P0｜Heterogeneous Scientific Source Annotation（设计及契约阶段）

**Authority base:** `gitzhangcd/NutriFoundation@54b4c2eba844f39c07575573a3e834e0bc00c261`  
**Status:** `PROPOSED_DESIGN_ONLY / RUNTIME_NOT_IMPLEMENTED / SCIENTIFIC_OWNER_APPROVAL_PENDING`

本目录为下游 Workbench-Evidence Annotation 的**新增提议性 Adapter**，没有更改既有 NDS-R1、NDF D0/D1/D2 或其他科学对象的冻结语义。

## 文档

- [异质科学来源标注架构](../../../docs/workbench/WB-EA-P0_Heterogeneous_Source_Annotation_Architecture_v0.1.md)
- [Exact Adapter Contract](../../../docs/workbench/WB-EA-P0_Exact_Adapter_Contract_v0.1.md)
- [Conformance、Negative Test 与 Stage Gate](../../../docs/workbench/WB-EA-P0_Conformance_and_Execution_Gate_v0.1.md)
- [已有 Workbench Scientific Adapter Matrix v0.2](../../../docs/workbench/Workbench_Scientific_Adapter_Matrix_v0.2.md)

## 机读交付

- `specs/annotation_contract.v0.1.json`：独立 `EVIDENCE_ECOSYSTEM_CASE` vs `DECISION_CASE` 的路由合同、七类 Profile、最小 source/anchor/review/gold 权限语义。
- `fixtures/conformance_cases.v0.1.json`：七类正向材料、现有决策工作流、跨类型路由/暴露/版本/证据/Gold 负向设计测试，以及科学风险旗标。
- `check_contract.py`：**仅做 P0 manifest 及 fixture 静态一致性检查**，不启动 D0，不读受保护数据、不访问互联网、不构成 Runtime PASS。

本地运行（Python 3.11 标准库即可）：

```bash
python apps/workbench/ea_p0/check_contract.py
```

## 设计边界

- 当前 Workbench `reader.js` + `secure_reader.py` 仍固定 `SYN-5-2-PAPER`，并且 `c1/specs/decision_profile.json` 仍为 19 字段决策标注。
- 原始 5:2 trial 虽真实发表，但本仓库内仅是合成工程阅读器 fixture，`is_qualified_evidence=false`，不属于 NDS 人类 baseline source packet。
- 预期正式来源链：SourceArtifact → CanonicalDocument/source map → type-specific AgentCandidate → ExpertReviewRecord → independent Gold review/adjudication（如适用）→ scientific-owner promotion。
- 正式 P1 多文献进件、Agent 实际抽取、专家证据审核存储、双人标注、Gold 晋级、生产服务**均尚未实现**。
- 任何科研真实专家数据仍受 C2.2 八项门禁与 r2/r3 科学版本冲突约束，不可在合成 D0 内进行。

## 对既有代码的约束

P0 不修改：`runs/NDF/**`、`runs/NDS/**`、`src/nutrifoundation/**`、`apps/workbench/c2_1/**`、`apps/workbench/c1/specs/decision_profile.json`。后续 runtime P1 必须做独立 PR、source allowlist 与 Expert/Agent 盲法端点回归。

## 下一阶段

`WB-EA-P1｜Versioned Multi-Source Registry, Typed Annotation Workpacks & Agent Candidate Round-Trip`

进入时须先由科学负责人审查并签署 P0 profile 及 canonical mapping 的语义，禁止把拟定机读契约当作已经批准的科学标准。
