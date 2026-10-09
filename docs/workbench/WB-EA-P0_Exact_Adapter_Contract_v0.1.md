# WB-EA-P0｜Exact Adapter Contract v0.1

> **Normative status:** PROPOSED_ADAPTER_CONTRACT / SCIENTIFIC_OWNER_APPROVAL_PENDING  
> **Baseline:** `54b4c2eba844f39c07575573a3e834e0bc00c261`  
> **Scope:** Source→AnnotationTask→Agent Candidate→Expert Review→Scientific Export, **NOT** NDS-R1 modification, **NOT** a production API declaration.  
> **Companion:** `WB-EA-P0_Heterogeneous_Source_Annotation_Architecture_v0.1.md`, `apps/workbench/ea_p0/specs/annotation_contract.v0.1.json`.

## 1. Exact routing contract

```yaml
AnnotationTask:
  task_id: stable_string
  task_kind: EVIDENCE_ECOSYSTEM_CASE | DECISION_CASE
  protocol_version: explicit_version
  profile_id: explicit_versioned_id
  source_type: controlled_enum
  scientific_question_ref: nullable_ref
  knowledge_cutoff: ISO8601_offset_timestamp
  allowed_source_versions: [{source_id, revision_id, source_sha256, canonical_sha256}]
  allowed_roles: [role_enum]
  exposure_policy_ref: versioned_policy
  workflow_strategy: AGENT_PROPOSE_EXPERT_VERIFY | HUMAN_INDEPENDENT | DOUBLE_BLIND_GOLD | NDS_R1_EXISTING
  gold_qualification: NOT_ELIGIBLE | ELIGIBLE_FOR_INDEPENDENT_REVIEW
```

**Routing rules:**
1. `task_kind=DECISION_CASE` → existing frozen NDS-R1 controller/profile, **no WB-EA profile injection**. No reference_set field may be removed or recoded.
2. `task_kind=EVIDENCE_ECOSYSTEM_CASE` → profile registry with exact `source_type/profile_id/version` match. No default fallback to `NDS_R1_DECISION_CAPTURE` or `RANDOMIZED_TRIAL`.
3. Unknown or ambiguous `task_kind`, incompatible profile version, missing source manifest, time/rights failure → `HOLD`, fail closed.
4. Multiple source versions allowed per task only if every source tuple is explicitly allowlisted. The task may read a primary source plus companion, appendix and correction; `source_family_refs` remain independent of source permissions.
5. `source_type` is artifact classification. Profile selection is by **task goal + source kind**, not by filename or PDF extension.

## 2. Scientific source projection

```yaml
SourceProjection:
  source_id:
  artifact_id:
  study_identity_ref: null
  source_family_refs: []
  source_type:
  revision_id:
  original_sha256:
  canonical_document_sha256:
  original_locator:
  original_publication_time:
  publicly_available_at:
  fetched_at:
  rights_decision_ref:
  authorized_units: []
  authorized_tables: []
  translation_sidecar:
    version: null
    source_sha256: null
    coverage: PARTIAL | FULL | NONE
    scientific_review_status: UNREVIEWED | QUALIFIED
```

`SourceArtifact` 和 `StudyIdentity` 由科学上游管理；`SourceProjection` 仅是可重建的页面读模型。Byte hash 必须对实际字节计算；Git blob SHA 不等于 raw source SHA256。转换流水线应独立完成 `Original → CanonicalDocument`，支持 HTML/Markdown、段落、表格、图/补充材料与原始 PDF 双向定位。文档转换失败保持 `STRUCTURING_HOLD`，不得伪造 quote 匹配。

```yaml
EvidenceAnchor:
  task_id:
  source_id:
  revision_id:
  canonical_document_sha256:
  unit_id:
  start_utf16: nonnegative_integer
  end_utf16: positive_integer
  source_quote: original_utf16_substring
  source_quote_sha256:
  exact_match: true
  pdf_locator:
    status: VERIFIED_UNIQUE_PDF_TEXT | PAGE_HINT_ONLY | UNRESOLVED
    page: nullable_integer
    bboxes: []
```

Must hold: `0 <= start_utf16 < end_utf16 <= len(raw_unit_utf16)`, decoded original slice `== source_quote`, exact SHA match; PDF `PAGE_HINT_ONLY` is not verified BBox. Translation cannot own the anchor, but bilingual selection MAY map back to validated original offsets.

## 3. Profile + candidate science objects (sidecar only)

```yaml
AnnotationProfile:
  profile_id:
  version:
  task_kind: EVIDENCE_ECOSYSTEM_CASE
  source_type:
  required_groups: []
  optional_groups: []
  review_fields: []
  type_specific_kill_tests: []
  canonical_object_candidate_types: []
```

科学对象定义仍来自 E0–E8/Nutrition Foundation 权威层；此处 `CandidatePayload` 是结构化**提议和 reviewer 输入**，不是另造同名 canonical schema。建议元字段：

```yaml
AnnotationCandidate:
  candidate_id:
  task_id:
  source_ref: {source_id, revision_id}
  profile_ref: {profile_id, version}
  target_canonical_object_type: EvidenceUnit | ScientificClaim | EvidenceSynthesis | Recommendation | ConsensusJudgment | ...
  candidate_payload: {}
  original_anchors: [EvidenceAnchor]
  extraction_run_ref:
  extraction_prompt_digest:
  foundation_model_ref:
  generated_at:
  provenance_status: VERIFIED_SPAN | UNVERIFIED | MISSING
  lifecycle: PROPOSED
```

An `AgentCandidateSet` snapshot contains ids, content digest, source tuple digest, input cutoff, role and `freeze_receipt`. The bytes must be server-persisted and hashed before a candidate can become visible. No write-on-reveal, candidate swapping or unrecorded "re-run".

## 4. Expert review and judgment separation

```yaml
EvidenceReviewRecord:
  review_id:
  task_id:
  target_candidate_id:
  reviewer_identity_ref:
  qualification_receipt_ref:
  exposure_log_ref:
  read_source_version_refs: []
  disposition: ACCEPT | MODIFY | REJECT | NEEDS_MORE_EVIDENCE | IRRELEVANT | UNCERTAIN
  field_decisions: [{field_path, review_status, correction, reason, anchor_ids}]
  corrected_candidate_payload: null
  source_support_status: SUPPORTED | PARTIAL | UNSUPPORTED | NOT_VERIFIED
  statistical_interpretation_status: ACCEPTABLE | NEEDS_QUALIFICATION | INCORRECT | NOT_APPLICABLE | UNRESOLVED
  applicability_boundaries: []
  uncertainty_notes: []
  reviewer_free_text: null
  server_timestamp:
  immutable_receipt: {content_sha256, revision, server_signature_ref}
```

`MODIFY` 不得修改原始 `AnnotationCandidate`；应产生新 reviewer proposal version 并保留 diff。专家允许缺省/弃权，不能强迫 `UNRESOLVED` 变成一个推荐。`GoldAnnotationUnit` 的 independent_annotation_records、agreement_status、adjudication_ref、unresolved_disagreement、reference_confidence 由**独立资格化流程**设置；Workbench 只提交证据和原生专家意见，不能通过 `ACCEPT` 直接产生 Gold。

### 4.1 Annotation workflow state machine

```text
REGISTERED → SOURCE_QUALIFIED → PROFILE_LOCKED
   → [INDEPENDENT_CAPTURE | AGENT_CANDIDATE_GENERATION]
   → CANDIDATE_FROZEN (Agent path only)
   → EXPERT_VERIFICATION / INDEPENDENT_REVIEW
   → EXPERT_REVIEW_FROZEN
   → QUALIFICATION_PENDING
   → [QUALIFIED | REJECTED | UNRESOLVED]
   → PROMOTED (scientific owner's signed receipt only)
```

`QUALIFIED` is not equivalent to `PROMOTED`; publication and evidence-graph integration are separate controlled operations. `INDEPENDENT_CAPTURE` is not allowed to receive candidate bytes/counts/labels; the reviewer sees only authorized raw source material and neutral task instructions.

## 5. Canonical scientific mapping requirements

| Task profile | Candidate type | Required relation / supporting constraints | Disallowed upgrade |
|---|---|---|---|
| RCT | StudyIdentity + EvidenceUnit + ScientificClaim | PICO arms, outcome, time, effect estimate, missingness, comparator, source anchor | no non-significance→equivalence; no observational→causal |
| Observational | StudyIdentity + EvidenceUnit | exposure/association/adjustment, temporality, bias, confounding | no association→causation |
| SR/Meta | EvidenceSynthesis + ScientificRelation | member StudyIdentity refs, weight/overlap, heterogeneity, assessment | no pooled estimate as independent raw RCT |
| Guideline | Recommendation + EtDAssessment | source authority, statement class, original grade, target, exceptions, original quote, evidence dependencies | no guideline statement→effect-estimate evidence |
| Consensus | DeliberationProcess + ConsensusJudgment | panel/process/votes/dissent, evidence-gap binding | no agreement rate→certainty of evidence |
| Narrative | ScientificClaim candidate + cited-source lineage | cited SourceArtifact + claim type, hypotheses flagged | no citation laundering |
| Correction/retraction | Source Version/Dependency impact | effective availability time and affected descendants | no retroactive future leak |

A single source may yield multiple related candidates; `StudyIdentity` must support companion papers and reviews. Meta and guideline cannot independently "discover" Gold certainty without qualifying their cited primary sources and provenance. EtD decision criteria and Recommendation are distinct from effect estimates.

## 6. Exposure and access matrix

| Program/phase | Human source surface | Candidate access | Canonical outputs |
|---|---|---|---|
| Evidence production / Agent extraction | exact source-task allowlist | extractor own generated output | candidate only |
| Evidence production / Expert Verify | allowlisted source + immutable candidate-linked spans | frozen candidates only | ReviewRecord; no Gold |
| Evidence Gold / Human Independent | equal bounded canonical source snapshots; no candidate | **DENY** before freeze | independent annotation |
| Evidence Gold / Adjudicator | frozen independent reviews, assigned source versions | only phase-authorized | adjudication proposal |
| Existing NDS R0 | HBSP bounded case source | **NEVER** | existing J_human_de_novo |
| Existing NDS R1 | frozen candidate-linked quotations | post freeze only | existing CandidateDisposition |
| Existing NDS R2 preAI | same HBSP as R0 | **DENY** | existing J_preAI |
| Existing NDS R2 postAI | frozen J_preAI + frozen Agent set | post preAI freeze only | existing J_postAI |

Authorization must be enforced in server-issued read-model, source/translation/search/PDF/asset endpoints, exports, candidate APIs **and DOM caches**. Role and task-scoped access cannot be inferred from an exposed source title; signed snapshot/digest binds to raw source bytes.

## 7. Minimal normative delta / non-regression proof

**Additive only:** `AnnotationTask` `EVIDENCE_ECOSYSTEM_CASE`; versioned profile registry; source allowlist; review record; independent reference qualification requests. No alterations to pre-existing 19 field semantics or upstream frozen object payloads.

**Explicit compatibility assertions:**
- `NDS_R1_DECISION_CAPTURE` still has exactly 19 distinct fields, including all seven `reference_set` classes.
- `R0/R1/R2` hold and exposure gates match `Workbench_Scientific_Adapter_Matrix_v0.2.md` and frozen NDS contracts.
- `D2-NHANES-L-0001:r2` ↔ `:r3` mismatch is **unresolved**; this P0 does not choose a case reference.
- Fixed 5:2 sample is `SYNTHETIC_ENGINEERING_ONLY` even though the publication itself is real.
- `GoldAnnotationUnit` and `QualifiedDecisionReference` stay scientifically upstream-owned.
- Retraction event timestamps cannot be applied before their knowledge availability cutoff.
- Unknown source/profile or missing source span → deterministic **HOLD**.

## 8. Deliverables and acceptance semantics

This file defines **intended exact contracts** and implementation checks; it does not declare a working `/v1/evidence/**` production API. Subsequent implementation must version API schemas separately, build source grants and profile resolver, and demonstrate test matrices (positive/negative/temporal/permission/legacy regression) defined in Conformance doc before scientific owner signs freeze.
