# WB-P1.1-B1｜Scientific Source Library & Source Package Operations

**版本**：v0.1（合成工程实施规范）  
**上游**：WB-P1.1-A5 `Management UX Convergence & Expert Handoff`；B0 Audit  
**仓库实现**：`apps/workbench/d0/tpa_source_packages.py`、`tpa_source_packages_adapter.py`、`web/tpa_p11.js`、`d0_app.py`  
**状态**：仅代表工程候选，不是来源科学验收，不是生产部署许可。

## 1. B1 第一性原理与硬性界限

**证据所有权不得被管理功能复制或改写。**

```text
External MinerU / OCR / PDF extraction (P2: blocked, not installed in B1)
                  |
                  v
SourcePackage canonical structure / provenance adapter contract (B1 reference only)
                  |
         existing synthetic fixture reference
                  |
                  v
Original EA EvidenceEngine authoritative source + immutable source version/SHA
                  |
                  +--> B1 TPA package registry: hashes/structure index/lineage metadata ONLY
                  |
                  +--> Original authorized expert EA reader: original units, PDF.js,
                       source-anchors, quote verification, expert decision
```

B1 的可执行数据流严格限定于**已经由原 EA 引擎生成**的 7 份 `[SYNTHETIC]`、`rights_status=SYNTHETIC_FIXTURE` 虚构资料。**不存在真实文件上传、MinerU 运行、Markdown/HTML 文本存储、全段落回显、自动 Gold 晋级、真实模型输出或新建科学来源。**

本阶段的 `SourcePackage` 是**被动引用与结构索引包**，不是可替代 EA 的“原始科学文档”。登记过程不得创建、更新原 EA `sources` 记录。

## 2. 契约 `WB-SOURCE-PACKAGE-v0.1`

请求字段：

| 字段 | 约束 | 权威来源 |
|---|---|---|
| `schema_version` | 固定 `WB-SOURCE-PACKAGE-v0.1` | B1 契约 |
| `import_kind` | 固定 `EXISTING_SYNTHETIC_SOURCE` | 安全 Gate |
| `parser_adapter` | 固定 `SYNTHETIC_FIXTURE_ADAPTER` | B1；**不是 MinerU** |
| `source_id` / `revision_id` | 必须匹配已有 EA 来源版本 | EA Source |
| `source_type` / `profile_id` | 必须与已有 EA 的 profile 映射一致 | EA Profile |
| `canonical_document_sha256` | 必须与 EA 权威原文 digest 完全匹配 | EA Source |
| `rights_status` | 仅 `SYNTHETIC_FIXTURE` | 合成固定 Fixture |
| `parent_package_id` | null，或引用同来源先前可证明的**不同且更早**版本 | B1 Registry + EA Source |
| `package_id` | 登记时：`SPKG-SYN-[A-Z0-9-]{3,40}` | 登记调用方 |
| `idempotency_key` | 登记时：8–100 位允许字符，同键不同内容拒绝 | TPA Registry |

每条结构单元由服务器**从 EA 已存原文**推导：

```json
{
  "unit_id": "u1",
  "ordinal": 0,
  "element_kind": "PARAGRAPH",
  "utf16_length": 83,
  "unit_text_sha256": "<server-derived SHA-256>"
}
```

上例的 `utf16_length` 和 SHA 均为格式示意而非任何真实来源的校验值；生产接口返回以服务端计算结果为准。**接口不返回 `text`、`source_quote`、`candidate_payload`、未经盲法允许的候选和专家判断。**

```text
structure_sha256 = SHA256(canonical JSON(structure_index))
manifest_sha256  = SHA256(canonical JSON({
  manifest: normalized_manifest,
  structured_units: structure_index
}))
```

沿用原 `ea_runtime.digest` 的 canonical JSON 规则，避免前后端摘要规范漂移。

## 3. 可执行 API

| 方法 | 路径 | 权限 | 作用 |
|---|---|---|---|
| GET | `/v1/tpa/sources` | Producer、Manager | 既有 7 个来源的只读元数据；完全保留 |
| POST | `/v1/tpa/source-packages/validate` | Producer | 原始来源 / Rights / Profile / SHA / 结构索引校验；零状态变更 |
| POST | `/v1/tpa/source-packages` | Producer | 同一事务、同一请求键进行不可变包登记和审计事件落地 |
| GET | `/v1/tpa/source-packages?limit=25&offset=0` | Producer、Manager | 有界只读元数据分页 |
| GET | `/v1/tpa/source-packages/{package_id}` | Producer、Manager | 完整版本索引、摘要和谱系元数据，不返回原文 |
| POST | `/v1/tpa/source-imports/validate` | Producer | 原 P1 老接口保留；`REAL_PDF` 仍 403 |

原 D0 `/v1/login`、`/v1/session`、`nutri_session`、`x-csrf-token`、Host/Origin、`/manage` 与专家端 `/` 全部原样继承。不增加第二套认证/服务。

## 4. 版本与状态语义

```text
EA existing source (r1, authoritative SHA)
    |
    +-- POST validate ----------------> VALIDATED_SYNTHETIC_REFERENCE (ephemeral)
    |                                    |
    |                                    +-- no DB write
    |
    +-- POST register, valid nonce ----> SYNTHETIC_REFERENCE_ONLY (immutable)
                                         |
                                         +-- row has unique (source_id, revision_id)
                                         +-- event in original TPA hash audit chain
                                         +-- replay same key / same body -> same receipt
                                         +-- new key or changed payload -> 409
```

`SYNTHETIC_REFERENCE_ONLY` 不代表真实科研 `ADMITTED`、`ELIGIBLE`、`QUALIFIED`、`GOLD`。

已有的 `source_id / revision_id / source SHA` 构成 authority identity；`parent_package_id` 仅允许在同源、旧版真实存在及 EA `available_at` 更早时建立版本边。**目前仅 r1 合成素材，不得伪造 r2 / 修改 SHA 来展示新版本功能**。当真实多版本可用时必须另行准入后验证正向版本链。

## 5. UI 交互

进入 `/manage` → `科学资料库`：

1. 左侧展示原已注册的合成来源（7 个），可定位某一 `source_id / revision_id`；
2. 右侧展示标题、类型、Profile、原文版本 SHA、可用时间、合成 Rights、EA 上游谱系；
3. Producer 可先点击**校验结构化来源包**，校验只获取服务器结构索引/摘要；
4. 校验成功后启用**登记不可变合成来源包**，进行幂等事务登记；
5. 已登记版本呈现 Package/Structure SHA、unit id、UTF-16 长度和 unit text 摘要（不呈现原文），Manager 仅有查看权限；
6. 点击“前往任务中心选择此版本”，沿用 A5 S1–S5 任务向导，并复用原授权流程。

任何包登记都不能写 EA 来源表，不能绕过 Producer→Manager→EA Specialist 的角色分离，不能把“已校验引用包”解释为来源资格已通过。

## 6. 故障、重放与不可变性

- **不可信来源**：陌生来源、假的 SHA、假的 Profile、假的 source_type、非合成 `import_kind` / `parser_adapter` 必须 fail closed。
- **伪造权限**：Manager 不能验证/登记；EA 专家、NDS 角色不能调用管理端来源包接口。
- **入库事务**：源码引用、包唯一性、幂等键与审计日志写入同一个 SQLite 事务，任一失败不得部分登记。
- **不可变**：来源包表及重放日志 `UPDATE/DELETE` 由 SQL trigger 禁止；读回时重新检查 EA 版本、结构摘要与包摘要是否漂移。
- **网络不确定结果**：前端保留同一请求键；如果 POST 响应丢失，只允许精确匹配 package id + source id / revision id + authority SHA + manifest SHA 时恢复。
- **旧任务非回归**：不要求原七类合成任务先创建包；原 D0/EA 旧任务仍可运行。B1 仅新增结构化运营投影。
- **最小可见**：Manager 可检查单位计数/定位及摘要，不查看全文；专家原文访问仍通过 EA 的任务授权/Strict-Blind Gate。

## 7. Kill Tests（实施后应复验）

| ID | 必须判定 |
|---|---|
| B1-K01 | 真实 PDF、MinerU adapter 和外部 Markdown/HTML 输入 403/422；不生成 Package |
| B1-K02 | Source SHA / Profile / Type 错误无持久化副作用 |
| B1-K03 | 幂等键同意图返回原回执；变更内容 / 重复版本登记拒绝 |
| B1-K04 | 跨来源假 parent 和缺失 parent 不能产生假谱系 |
| B1-K05 | Manager 不可写；EA 专家不能读取来源库；未登录 401 |
| B1-K06 | 列表/详情不泄漏原文句子、模型候选和独立专家敏感状态 |
| B1-K07 | SQLite 重开仍有相同包摘要和重放回执；修改或删除被触发器拒绝 |
| B1-K08 | EA task draft → validate → freeze → prepare 与 B1 包相互独立，原 NDS 19 字段和 PDF.js、原文证据锚点无回归 |
| B1-K09 | 真实 Chromium 管理端可以校验、登记、刷新后只读查看；页面脚本错误 0 |
| B1-K10 | 任何未复核真实 PDF 均不可通过本阶段 UI、API 或快捷入口导入 |

## 8. 通往 P2 实际结构化文档适配的门槛

后续只有在独立 P2 阶段完成科学/安全门后，才可开发真实 MinerU/LLM 解析包的接收：

- 来源 provenance / DOI 或 Guideline ID、原件抓取时间与授权、版权/隐私；
- 原文 bytes hash、OCR/解析模型与版本、可定位结构化 Markdown/HTML、完整 PDF 页码 / bbox；
- 段落和表格 SourceAnchor 的 lossless mapping / quote checksum、跨版本重映射；
- 人工核查、不可删除原件、质量门、风险内容识别；
- 真实知识截止日期与 Source Rights / Scope / Leakage-Safe / Strict-Blind；
- 验收后才考虑把真实源版本放入生产任务编排。

**绝不能把 B1 的 synthetic-only Registry 通过简单调参切成“真实来源导入模式”。** 必须独立扩展数据契约、审核、授权、版本和科学资格机制。

## 9. 非回归对象

- EA source 的原文与 candidate 管道；
- 原 NDS R0/R1/R2 十九字段 Scientific Decision Contract；
- 双语阅读、PDF.js 原文高亮、SourceAnchor 以及独立专家真值所有权；
- TPA 的任务、冻结、发布与重放语义；
- `src/nutrifoundation/**`、`runs/**`、`apps/workbench/c1/**`、`c2_1/**`、`c2_2/**` 均为冻结/保护源，B1 不改。

> 实际 CI 证据与接受代码 SHA 在后续 B1 Engineering Receipt 单独记录。
