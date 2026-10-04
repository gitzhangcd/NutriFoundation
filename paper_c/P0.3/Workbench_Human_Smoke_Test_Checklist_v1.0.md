# P0.3 Annotation Workbench｜Human Smoke-Test Checklist v1.0

本清单必须由研究团队在真实浏览器/工作台环境中执行。机器 contract PASS 不能替代本清单。

## 必须全部 PASS

- [ ] WB-H01｜打开 Calibration source 后，显示的 SourceArtifact/PMID/版本与 manifest 一致。
- [ ] WB-H02｜界面显示或后台验证的 worker-visible text SHA 与 manifest 一致。
- [ ] WB-H03｜Annotator A 登录后看不到 Annotator B 的 draft/first-pass；反向同样成立。
- [ ] WB-H04｜source span 可直接在原文选择，并正确回写 exact text + stable token offsets。
- [ ] WB-H05｜刷新/重新打开后 span 仍绑定同一 source hash 与 token offsets。
- [ ] WB-H06｜`FIRST_PASS_LOCK` 后所有科学字段不可编辑。
- [ ] WB-H07｜只有 A/B 都锁定后才能生成 diff。
- [ ] WB-H08｜Round B 在 reliability metric freeze 前不能打开 discussion/adjudication。
- [ ] WB-H09｜incomplete-source case 能提交 `insufficient_source`，界面不会强迫补全。
- [ ] WB-H10｜JSON export 通过 Calibration Annotation Record schema，并包含 record SHA。
- [ ] WB-H11｜active annotation time 与 discussion time 分开记录。
- [ ] WB-H12｜COI / independence attestation 未完成时禁止 lock。
- [ ] WB-H13｜P0.3 workspace 无法打开任何 Gold100 source。
- [ ] WB-H14｜任何 Gold100 越权访问尝试进入 audit log。
- [ ] WB-H15｜AB0–AB6 output、evaluator score、其他模型结果在 workspace 中不可见。

任一项 FAIL：P0.3 不得进入 Round A；修复并重新执行完整 smoke test。