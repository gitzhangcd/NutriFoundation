# WB-P1.1-B4｜Integrated Acceptance, Failure Recovery & Non-Regression Freeze

## 合成 Workbench P1.1 综合工程验收与冻结契约 v0.1

**适用分支**：`workbench-p1.1-b4-integration-nonregression-freeze`，基于 B3 Draft PR #34 的代码。  
**阶段类型**：集成 / 失效注入 / 科学与安全非回归验收，**不是新功能开发**。  
**目标结论**：仅可达到 `SYNTHETIC_ENGINEERING_FROZEN`；真实数据、真实 Agent、真实专家、Gold、临床与生产仍为 `NO_GO`。

### 1. 不变的系统边界

原 D0 `make_app` 是唯一应用入口；B1、B2、B3 共用原 TPA SQLite、认证 cookie、Origin/CSRF/Host 与原 EA 科学权威库。B4 不实现额外的后端控制器、独立授权体系、新的 Agent 引擎、新来源解析、专家资格管理或新 UI 页面。

```text
B1: SYNTHETIC_REFERENCE_ONLY 来源结构引用
  -> B2: SYN-FIXTURE-NOT-AN-LLM 固定候选证明
  -> 原 TPA: VALIDATE / FREEZE / PREPARE / ASSIGN / PUBLISH
  -> B3: EXACT 原 GRANT / ASSIGNMENT SHA 交接证明
  -> 原 EA: 独立登录的合成专家访问闸门
  -> 原 TPA: 真实 SOURCE/TASK/CANDIDATE 访问事件、撤销及历史留存
  -> B4: 同一持久化实例、重启、攻击注入和完整链路的跨阶段验收
```

**B1 必须保持可选**：没有 B1 来源包不能中断原 P1 Task Production；B2/B3 证明不能变为原发布必需步骤。  
**B2 不允许模拟真实模型成果**：`real_agent_executed=false`，固定候选 provenance 不能取代原 EA Candidate。  
**B3 不允许伪造授权**：交接 receipt ≠ 原 Grant，也不意味着阅读、理解、完成评估。  
**独立组绝对隔离**：`HUMAN_INDEPENDENT` 不能见候选摘要、数量或 Candidate API，也不能被错误专家号读取。  
**真实来源拒绝**：真实 PDF/MinerU/HTML、病人信息、专家正式账户与生产模式默认拒绝。

### 2. 集成和恢复合同

| 场景 | 期望 |
|---|---|
| 一次性跨 B1→B2→B3 | 绑定相同原 EA `RCT-001:r1`、原 Task SHA、原分配与 Grant 事件，零原文复制 |
| 两条策略同一服务 | Agent 复核与独立组同时存在；独立组不进入 B2 Agent 列表 |
| 独立会话 | Producer、Manager、ea1、ea2、Auditor 均按其原始权限投影，不能串用 cookie/Grant |
| 重启重建 | 在同一 SQLite 路径重新创建 FastAPI/Auth/EA/TPA/B1/B2/B3；不可变回执及原权限均保持 |
| 丢失 HTTP 响应 | 同一幂等键可读取原 receipt；不同键重新写入拒绝；管理 UI 必须基于服务端已提交任务状态确认 |
| 撤销之后 | 已记录的历史来源/候选访问不擦除，原 EA 未来读取 403；不会重发 Grant |
| 元数据/来源漂移 | 原 EA 来源版本 SHA 被故障注入篡改时 B1、B2、B3 投影均 fail closed；旧 receipt 不静默重写 |
| 独立组候选被注入 | 原 EA 的错误 CandidateSet 必须导致 B3 403，不能通过“清理后继续”绕过 |
| 不可变性 | B1/B2/B3 六张注册/证明/重放表全部禁止直接 SQL UPDATE/DELETE |
| 审计链 | 原 TPA hash-chain 伪造事件必须由 Auditor `valid=false` 识别 |
| 真正科研准入 | `allow_synthetic=False` 拒绝启动，真实来源入口拒绝，正式科学采集禁用 |

### 3. 自动化验收证据合同

工作流：`.github/workflows/wb-p1-1-b4.yml`：

- **Python 集成**：执行 `apps/workbench/d0/tests` 全部原 D0、EA、TPA、A5、B1、B2、B3 与 B4 故障注入用例，不准靠重试或跳过失败测试宣布通过。
- **Native Chromium**：实际浏览器启动同源 D0，保留原 PDF.js，执行原 A5 列表与发布 HTTP 502 丢失响应恢复、B1 来源包、B2 Agent 证明、B3 专家交接和独立会话 EA 阅读流程；`page_errors=[]`、`scientific_capture=false`。
- **科学保护树 Guard**：与 B3 基线比较，不允许编辑 `runs/**`、`src/nutrifoundation/**`、`c1/c2_1/c2_2` 或 `ea_runtime/ea_seed/ea_contract`。
- **B4 变更白名单**：只允许 B4 测试、B4 workflow、B4 文档和现有浏览器验收脚本；不允许偷偷新增功能接口。
- **交叉工作流**：原 A5、B1、B2、B3、TPA P1、TPA P1.1-A、EA P1、D0 engineering/full-engine 在同一个精确代码 SHA 上必须全部成功。
- **冻结证明**：列出上述 Actions 链接、测试数、截图 Artifact、原代码 SHA 和 docs-only receipt SHA；已知未解决风险单列。

### 4. Failure/Leakage Kill Gates

```text
B4-K01  B1/B2/B3 同一源 sha 贯通，不写第二份原文             MUST PASS
B4-K02  两条策略共存时 HUMAN_INDEPENDENT B2 隐身            MUST PASS
B4-K03  执行环境重建后保存源包/Proof/Grant /重放证据         MUST PASS
B4-K04  原 EA 相应专家能读；错误/独立组候选强制拒绝           MUST PASS
B4-K05  原源 SHA 篡改造成 B1+B2+B3 拒绝，不自动修复           MUST PASS
B4-K06  独立组注入 CandidateSet 导致 B3 fail closed          MUST PASS
B4-K07  B1/B2/B3 六张不可变/重放表 SQL UPDATE/DELETE 拒绝   MUST PASS
B4-K08  故障注入原 TPA hash-chain 伪造事件，Audit INVALID   MUST PASS
B4-K09  授权发布不等于 TASK_OPENED / 已读 / 完成            MUST PASS
B4-K10  撤销后未来 EA 访问拒绝，历史事件保留                  MUST PASS
B4-K11  模拟网络丢失响应重放须根据原服务端状态验证            MUST PASS
B4-K12  真实来源/真实专家/生产启动仍为 NO_GO                MUST PASS
B4-K13  全量 Python & Chromium 非回归                           MUST PASS
B4-K14  EA/NDS/科学不可变树零侵入                             MUST PASS
```

### 5. 冻结的准确语义与后续职责

只有所有 Kill Gates 和交叉 CI 成功才能写：

`WB-P1.1-B4 SYNTHETIC_ENGINEERING_FROZEN`

该字符串**只表示合成工程测试的冻结候选**，不得简化为 `SCIENCE_READY`、`GOLD_READY`、`CLINICAL_READY` 或 `PRODUCTION_READY`。Draft PR 未经独立审核仍不能合并 main；标签（如果创建）必须绑定已验证的准确 commit，后续任何修改重新审计。

**后续分轨，而非在 B4 打开配置开关**：

1. P2：真实来源版权/许可、PDF/MinerU 结构化导入、SourceAnchor 与无损溯源准入。
2. P3：真实专家资格、临床伦理、盲法历史、身份隔离、标注与质量校准。
3. P4：生产安全、网络访问、监控、密钥和组织部署验收。
