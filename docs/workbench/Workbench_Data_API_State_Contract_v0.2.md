# Workbench Data, API, State Machine & Audit Contract v0.2

> WB-P0.2-M0｜**DESIGN_FROZEN / EXECUTABLE_SCHEMA_AND_RUNTIME_PENDING**。下列类型和 API 为下一阶段实现目标，不宣称它们已存在于 WB-B1 代码。优先级低于 NDF/NDS frozen scientific objects；以 `Workbench_System_Master_v0.2.md` 为依据。

## 1. Engineering domain entities

```text
Project ─── TaskProfile / ProfileQuestionMapping
   └── AnnotationTask ── Assignment ── ExpertQualification
                 ├── AuthorizedInputSurface ── SourceArtifact/Package/CanonicalDocument
                 │                                └── DocumentUnit ── SourceAnchor ── PDF_PAGE_BBOX
                 ├── ExpertDraft (many revisions) ── FieldAnchorBinding[]
                 │   └── ImmutableJudgmentSnapshot (R0 or R2) ── FreezeReceipt
                 ├── FrozenAgentCandidateSet (R1/R2, always isolated)
                 ├── ReconciliationRecord ── J_postAI (R2 only)
                 ├── ReviewRecord / AdjudicationRecord (downstream)
                 └── AuditEvent / ExposureEvent / VersionedExport
```

### 1.1 Common identity and provenance (proposal)

Every durable object should carry: `id`, `schema_version`, `project_id`, `task_id?`, `created_at`, `created_by`, `source_contract_ref`, `source_revision`, `content_sha256`, `previous_revision?`. Audit events also bind monotonic `sequence` and `session_id` where applicable. Hashing uses a specified deterministic canonical JSON strategy (candidate: RFC 8785 / JCS) and fixed UTF-8 encoding. The exact canonicalization algorithm and duplicate-key behavior must be frozen by test fixtures before production; **this is a proposed implementation rule, not an already verified scientific hash format**.

### 1.2 TaskProfile / AuthorizedInputSurface

```json
{
  "task_id": "TASK-EXAMPLE",
  "profile": {"id": "NDS_R1_DECISION", "version": "v0.2"},
  "case_ref": "D2-NHANES-L-0001:r3",
  "arm": "R2",
  "phase": "PRE_AI_DRAFT",
  "assignment": {"expert_slot": "EXP-R1P0-C", "qualification_ref": "..."},
  "input_surface": {
    "source_packet_ref": "Human_Baseline_Source_Packet_v0.2",
    "manifest_sha256": "sha256-from-canonical-bytes",
    "allowed_source_ids": ["..."],
    "projection_version": "R2_PREAI/v0.1"
  }
}
```

**重要**：以上是字段结构范例，值中 `...` 和样例任务不是实际专家数据；不能当作真实提交。`allowed_source_ids` 必须来自科学批准的投影 manifest，不得由前端提交任意来源 ID 去解锁。

### 1.3 Anchors

```json
{
  "anchor_id": "a-...",
  "canonical_document_id": "DOC-...",
  "canonical_revision": "r1-...",
  "source_pdf_sha256": "...",
  "unit_id": "U-0001",
  "start_utf16": 0,
  "end_utf16": 20,
  "quote": "exact quote from immutable unit",
  "quote_sha256": "...",
  "locator_status": "EXACT_PDF_BBOX_VERIFIED",
  "pdf_page_bbox_ref": "pdf-bbox-sidecar-..."
}
```

No BBox is created from guessed Markdown page hint. BBox metadata can be a separate versioned sidecar, currently `PDF_PAGE_BBOX/0.2`, with source SHA, unique text match, page crop/rotation and normalized rectangles. Signed/locked historical anchors must not be mutated by re-conversion; migration generates a new anchor version + mapping report.

### 1.4 ExpertDraft & FreezeReceipt

`ExpertDraft` carries `workpack_id`, `arm`, `source_manifest_sha`, `revision`, `payload_json`, `field_anchor_bindings`, `updated_at`. Only the owning currently assigned qualified expert may modify; do not store old cleartext drafts in unaudited localStorage/browser analytics.

`FreezeReceipt` must include `expert_slot`, `submitted_at`, `content_sha`, `exposure_check: PASS`, `snapshot_id`, `input_surface_sha`, `workpack_version`, `audit_event_id` (additional engineering fields; four required scientific receipt members must remain exact). The immutable snapshot references the actual source and task version visible **at the moment of submission**.

For R2, `J_preAI` is immutable; `J_postAI` is a different object with `pre_ai_judgment_ref`, `candidate_set_ref`, `reconciliation_item_refs`. For R0, a candidate set must never be projected; R1 verification must never be mistaken for independent `J_preAI`.

## 2. Three independent state machines

### R0

```text
PENDING_QUALIFICATION → QUALIFIED_UNBOUND → BOUND_R0 → PRE_OPEN_PASS
→ DRAFTING_J_HUMAN → READY_FOR_FREEZE → J_HUMAN_FROZEN → CLOSED
```

Invariant: `AGENT_EXPOSURE` has no legal outgoing transition or token across **all** R0 states.

### R1

```text
PENDING_QUALIFICATION → QUALIFIED_UNBOUND → BOUND_R1
→ WAIT_AGENT_SET_FROZEN → READY_FOR_AGENT_FIRST_VERIFY
→ VERIFYING → VERIFIED_OUTPUT_FROZEN → CLOSED
```

R1 must wait for `CandidateSet.status = FROZEN` and `referenced_source_spans.status = AVAILABLE`. No separate pre-AI freeze screen.

### R2

```text
PENDING_QUALIFICATION → QUALIFIED_UNBOUND → BOUND_R2 → PRE_OPEN_PASS
→ DRAFTING_J_PREAI → READY_FOR_FREEZE → J_PREAI_FROZEN
→ AGENT_EXPANSION_AUTHORIZED → AGENT_SET_FROZEN
→ REVEAL_AUTHORIZED_AND_LOGGED → RECONCILING
→ J_POSTAI_FROZEN → CLOSED
```

Never allow `AGENT_SET_FROZEN` or `REVEAL` to bypass required earlier transitions. R2 protocol deviation is a terminal contamination indicator for clean anchoring analysis, not an automatic rollback of an observed exposure.

## 3. Suggested API contract (not yet implemented)

All endpoints below require `Authorization`, project/assignment authorization and server-side arm/phase projection. Sources, PDF, thumbnails and downloads must be checked identically to field JSON. API errors use a stable `code`, optional `allowed_actions`, `correlation_id`, **never hidden candidate metadata**.

| Verb/path | Function | Required guard | State-changing? |
|---|---|---|---|
| `GET /v1/tasks` | my tasks | assignee/admin filtered only | no |
| `GET /v1/tasks/{id}/read-model` | sanitized task, current phase, allowed sources | RBAC + assignment + arm + phase + scientific allowlist | no |
| `POST /v1/tasks/{id}/qualification` | real expert screen | expert identity + evidence + no cross-arm reuse | yes |
| `POST /v1/tasks/{id}/binding` | assign expert slot | manager + qualified + conflict check | yes |
| `GET /v1/tasks/{id}/sources/{source_id}` | original PDF / markdown | same read-model guard + allowed source/version | no |
| `GET /v1/tasks/{id}/canonical` | authorized document units | source allowlist + revision | no |
| `POST /v1/tasks/{id}/anchors` | create exact source anchor | correct source + valid quote/offset | yes |
| `GET /v1/tasks/{id}/anchors/{a}` | read/replay own anchor | source/assignment/version check | no |
| `GET /v1/tasks/{id}/draft` | current editable draft | arm-specific owning expert | no |
| `PUT /v1/tasks/{id}/draft` | optimistic-save draft | `If-Match` revision and form schema | yes |
| `POST /v1/tasks/{id}/freeze` | atomic J_human or J_preAI | qualification/exposure receipt/current source | yes |
| `GET /v1/tasks/{id}/freeze-receipt` | read immutable receipt | same authorized expert or authorized auditor | no |
| `GET /v1/tasks/{id}/agent-candidates` | candidate projection | **R0 NEVER**; R1 frozen set; R2 J_preAI freeze and logged exposure | no but exposure event may commit |
| `POST /v1/tasks/{id}/candidate-exposure` | authorized reveal handoff | atomic authorize + durable event | yes |
| `POST /v1/tasks/{id}/verification` | R1 candidate-by-candidate disposition | candidate frozen, spans attached | yes |
| `POST /v1/tasks/{id}/reconciliation` | R2 postAI | J_preAI frozen, candidate logged and frozen | yes |
| `POST /v1/tasks/{id}/reviews` | authorized reviewer | assignment + frozen judgment | yes |
| `GET /v1/tasks/{id}/audit` | authorized audit stream | auditor + case/field filter | no |
| `POST /v1/tasks/{id}/exports` | version-bound export | privacy/arm guard and explicit format | yes |

**严禁**将 `agent-candidates` 设为常规 list API 再前端隐藏；建议 `candidate-exposure` 返回仅一次有效短期 signed capability token，对具体 candidate set/version/session 一次性授权并同步写 exposure event。Capability token 不能延长整个 R0/R2 preAI 访问权限。

## 4. Transaction and concurrency semantics

### Atomic freeze sequence

1. Authenticate/authorize exact expert slot and correct arm/case.
2. Verify real qualification, signed pre-open exposure assertions, available input packet and source hashes.
3. Read draft with `expected_revision`; validate all workpack fields and attached anchor validity, ensure no previous frozen result.
4. Compute canonical bytes and `content_sha`; write immutable snapshot and receipt plus `FREEZE` audit event in **one transaction**.
5. Commit; return receipt. On network retry require idempotency key; same key returns same receipt and **must not create another snapshot**.

### Candidate reveal sequence

1. Verify arm/phase and source/candidate set version; R0 deny unconditionally.
2. For R1 ensure frozen AgentCandidateSet, span refs available and expert qualified; for R2 ensure persisted valid J_preAI freeze.
3. Persist `CANDIDATE_EXPOSURE` with candidate version, user/session/case/arm and timestamp in an atomic authorized grant operation.
4. Return only the dedicated signed read projection and audit correlation. If atomic event fails, fail closed; do not serve cached bytes.

### Concurrency

- `PUT draft` with stale version ⇒ HTTP `409 REVISION_CONFLICT`.
- `POST freeze` repeated ⇒ idempotent replay or `409 ALREADY_FROZEN`; no overwrite.
- Source was replaced ⇒ `412 SOURCE_VERSION_MISMATCH`, offer new task binding, not implicit migration.
- Unauthorized user or phase ⇒ `403 FORBIDDEN`, no candidate hint; missing permitted resource ⇒ `404` according to no-existence-leak policy.
- Invalid quote/UTF16/BBox ⇒ `422 ANCHOR_INVALID`/`ANCHOR_AMBIGUOUS`.
- Scientific adapter semantic conflict ⇒ `409 CONTRACT_CONFLICT`, force review.
- Protocol invalid exposure attempt ⇒ `403 EXPOSURE_LOCKED` and privacy-safe audit event.

## 5. Read-model projection and transport policy

Server must construct `TaskReadModel` by **positive allowlist**, not serialize entire `Task` and delete a few fields. Cache keys require `(project, user/slot, arm, phase, projection_revision, source_sha, candidate_visibility_revision)`. Invalidate after authorized state transition; never prefetch hidden candidate endpoints to the browser. SSE/WebSocket events must be equally scoped (no candidate-count leaks). SSR/HTML hydration, search results, PDF thumbnails, signed object URLs and bulk exports all use the same permissions.

## 6. Append-only audit & provenance

Event model `event_id`, `task_id`, `actor/role`, `arm`, `phase`, `kind`, `sequence`, `timestamp_utc`, `session_id`, `source_manifest_sha`, `object_version`, `payload_digest`, `parent_event_hash`. Events include `QUALIFICATION_SCREEN`, `ASSIGNMENT`, `OPEN_SOURCE`, `VIEW_UNIT`, `ANCHOR_CREATED`, `DRAFT_SAVED`, `JUDGMENT_SUBMITTED`, `PRE_AI_LOCK`, `CANDIDATE_EXPOSURE`, `RECONCILIATION`, `PROTOCOL_DEVIATION`, `EXPORT`, `REVIEW`. Raw medical content should not be dumped into security logs. A hash chain helps detect tampering but does **not** replace restricted write permissions, backups or scientific independent verification.

## 7. Storage topology and migrations

- Engineering MVP: standalone current B1 reader + SQLite where appropriate, used only for fixtures and developer E2E.
- Team collaboration: PostgreSQL transactions + unique `(case_ref, expert_identity)` binding constraint for arm exclusivity; immutable snapshot tables with UPDATE/DELETE prohibited at app role; object store for PDF and assets with signed short-lived requests; dedicated controlled export path.
- The SQLite→Postgres schema migration is a **C2 ADR**, not assumed implemented by M0.
- Every schema or source revision migration needs explicit backup, checksum, dry-run/rollback, old-vs-new anchor replay and a signed report.

## 8. Acceptance obligations

For each endpoint/state implement positive and negative tests: unauthorized R0/R2 candidate access, role/session swaps, cache poisoning, stale source hash, idempotent double freeze, replay after refresh, cross-arm same expert binding, reviewer premature access, malformed ZIP, fake exact BBox, audit failure at reveal. A UI-only test is insufficient; server/DB responses must be inspected for sensitive bytes.