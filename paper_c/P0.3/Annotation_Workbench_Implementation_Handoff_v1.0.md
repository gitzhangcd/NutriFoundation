# P0.3 Annotation Workbench Implementation Handoff v1.0

## Goal

实现一个可运行的专家标注工作台，使 P0.3 可以从“contract 已验证”进入真实 Human Smoke Test 和专家 Calibration。

该应用不是普通文献阅读器。它是 Paper C scientific measurement system 的一部分。

## Authority inputs

实现时必须直接读取并遵守以下文件：

```text
paper_c/P0.3/Annotation_Workbench_Contract_v1.0.json
paper_c/P0.3/Calibration_Annotation_Record_Schema_v1.0.json
paper_c/P0.3/P0.3_Calibration_Protocol_v1.0.json
paper_c/P0.3/Reliability_Gate_Contract_v1.0.json
paper_c/P0.3/Expert_Calibration_Manual_v1.0.md
paper_c/P0.3/Workbench_Human_Smoke_Test_Checklist_v1.0.md
runs/E0.4.3/P0.3/Calibration12A_Training_Manifest_v1.0.json
runs/E0.4.3/P0.3/Calibration12B_Reliability_Manifest_v1.0.json
```

Gold100 只能作为 access-deny fixture 使用，不得在 P0.3 工作区展示正文：

```text
runs/E0.4.3/P0.2.4/Gold100_Source_Set_FROZEN_v1.0.json
```

## Required user flow

```text
Role login / pseudonymous expert ID
→ Calibration round list
→ source hash verification
→ read-only document viewer
→ scientific annotation form
→ in-document evidence-span binding
→ COI / independence attestation
→ first-pass lock
→ immutable locked state
→ pair lock
→ Round A diff/discussion OR Round B metric freeze
→ export + audit log
```

## Security / blindness invariants

Annotator A 与 B 使用独立 namespace。任何 API/UI endpoint 在 pair lock 前都不能返回另一方 record。Gold100 source ID、title、text、annotation record 都不能出现在 P0.3 workspace 可访问路径中。AB0–AB6 output/evaluator data 也不得进入 workbench 数据依赖。

## Evidence-span implementation

对每个 worker-visible source 生成稳定 token 序列。span 保存 `(source_sha256, start_token, end_token, exact_text, supported_object_ids)`。重新打开页面必须 round-trip 到同一 token offsets；source hash 变化必须阻断 annotation。

## Lock semantics

`FIRST_PASS_LOCK` 必须对 canonical JSON 计算 SHA-256，并写 immutable audit event。锁后禁止 PATCH/PUT 修改科学字段。若实现允许管理员直接改数据库，则不符合 contract。

## Round A / Round B difference

Round A：pair lock 后可显示 diff 与讨论入口。Round B：pair lock 后先进入 reliability export/metric freeze，只有 metric freeze 成功后才能显示讨论。

## Minimal automated test set

必须自动验证：source hash mismatch blocks；A/B visibility blocked；lock immutable；span round-trip；Round B discussion blocked before metric freeze；Gold100 access denied；schema-valid export；audit event completeness。

## Human acceptance

代码测试全部 PASS 后，由真实研究人员执行 `Workbench_Human_Smoke_Test_Checklist_v1.0.md`。机器测试不能代签人工 smoke test。

## Output required before P0.3-H0 PASS

```text
workbench build/version ID
automated implementation test report
human smoke-test result JSON
zero blocking defects
```