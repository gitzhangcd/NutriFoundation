# WB-TPA v0.1 P0｜Task Production & Assignment — Normative Design Freeze

> Status: **USER-APPROVED P0 DESIGN FROZEN / SCIENCE-SECURITY-DEPLOYMENT NO-GO**  
> Date: 2026-10-10  
> Repository: gitzhangcd/NutriFoundation  
> Implementation anchor: draft PR #26, branch workbench-ea-p1-d0-54b4c2e-integration, descendant of exact baseline 54b4c2eba844f39c07575573a3e834e0bc00c261  
> Implementation branch: workbench-tpa-p0-contract-freeze, based on the PR #26 integration branch  
> Owner decision: confirmed by user; **not** independent scientific signoff, regulatory approval, ethics approval or production readiness.

## 0. Explicit user choices (frozen)
| Decision | Normative choice |
|---|---|
| Management UI | **Existing D0 origin, protected independent route /manage**. Same authenticated security perimeter, separate principal authorizations and views. |
| Scope | **Only EVIDENCE_ECOSYSTEM_CASE** for WB-EA. NDS R0/R1/R2 DecisionCase remains owned upstream and cannot be created or modified by TPA. |
| Document processing | **External parser** (MinerU or replaceable equivalent) produces an import package. TPA validates, registers and projects; expert Workbench does not become a raw-PDF extraction interface. |
| Rollout | **P1 synthetic-management loop first → P2 real-source qualification → P3 genuine Agent and pilot-gated expert delivery**. No PR #26 merge, public launch or real expert deployment is authorized by this freeze. |

## 1. Scientific and implementation authority
1. Existing SIS v0.3.1 R5, SIS-MED v0.3.1 R6, AI Nutri and NutriFoundation scientific contracts remain upstream authority; TPA is an operational adapter, never an ontology or reference authority. These sources support separation of expert-native judgment from scientific mapping, immutable evidence provenance, temporal information boundaries and non-equivalence of expert answers with qualified Gold. Alignment still requires future formal science-owner review; no false blanket conformance claim.
2. PR #26 is an engineering-only synthetic thin slice. Its registered SourceArtifact is synthetic structured text; existing EA API **rejects rights_status != SYNTHETIC_FIXTURE**, and EA users are dedicated SYN-EA-EXPERT actors. Real-source support is a future controlled adapter, not a flag to disable.
3. Preserve unchanged: runs/NDF/**; runs/NDS/**; src/nutrifoundation/**; apps/workbench/c1/**; apps/workbench/c2_1/**; apps/workbench/c2_2/**; D0 R0/R1/R2 exposure, original reader/PDF.js/bilingual and 19-field DecisionCase. No change to frozen authority based on this document.
4. GOLD / ReferenceConstruction / QualifiedDecisionReference ownership stays entirely outside TPA. TPA records return **UNQUALIFIED_EXPERT_REVIEW**, scientific_capture=false and gold_qualification=NOT_ELIGIBLE until separate authorized adjudication; approval of a task does not change these fields.
5. All P0 contract additions are **proposed operational specifications** frozen as design for implementation, not claims of implemented runtime behavior.

## 2. Component topology and trust boundaries

~~~
External original files (private)              Original D0 same-origin site
         |                                                |
  Independent document parser                   /manage (admin/producer UI)
         |                                                |
  Immutable ImportPackage manifest ---------> Import Qualification Gate
  original bytes + parse provenance                       |
  canonical units + optional translations       SourceRevision + RightsDecision
  optional PDF locator hints                              |
                                           TaskDefinitionRevision (immutable)
                                                       |
                                         Preparation & scoped source projection
                                                  /                \
                                 independent human pack       real Agent run candidate
                                     (NO Agent)              verification + freeze
                                                  \                /
                                             Assignment eligibility
                                                       |
                                             immutable delivery grant
                                                       |
                                D0 existing / Evidence mode expert interface
                                                       |
                                            ExpertReview freeze & audit
                                                       |
                              upstream separate scientific adjudication (NOT TPA)
~~~

In P1 use *synthetic documents only*. Design for P2 must keep:
- Original bytes and source checksum authoritative; CanonicalDocument is a traceable transformation, not a substitute for original. Translation sidecar is auxiliary and must never supply authoritative source spans.
- Parser identity/version, extraction configuration, unit-to-original mapping, extraction confidence/unresolved spans, original_sha256 and canonical_document_sha256.
- Explicit publication/available_at vs fetched_at vs task knowledge_cutoff vs assignment vs actual exposure timestamps; no future-information leakage.
- Original exact quote + unit_id + UTF-16 offsets + sha256 verified against the *authorized source revision*. PDF page/bounding box remains UNVERIFIED until verified independently. Never promote inferred bbox to VERIFIED_UNIQUE_PDF_TEXT.
- License/rights/retention/copyright/access restrictions and task-scoped projections; no public static original files.
- Source-family relations including guideline versions, corrections/retractions, secondary vs primary evidence and lineage; revision never mutates existing tasks.

## 3. Operator workflows — P1 through P3
### 3.1 Research team on /manage (P1)
1. **Source Library:** list/import *synthetic* documents; filter by type/version/parse status; source details and original/derived preview. No public upload endpoint in P1.
2. **Task Builder:** draft task, primary source, supplementary task-authorized source versions; seven existing EA profiles, knowledge cutoff, workflow strategy, read projection, protocol and immutable revision.
3. **Preparation:** For AGENT_PROPOSE_EXPERT_VERIFY require frozen provenance-checked candidate set before delivery; P1 uses labeled prebuilt synthetic fixture, **not genuine model inference**. For HUMAN_INDEPENDENT prepare a candidate-free read model; producer cannot project candidate payload or existence to the expert.
4. **Assignment:** pick eligible synthetic EA expert and only that identity; a rule gate checks grants, qualification, conflicts, prior exposure, experimental arm, assignment concurrency and prior freezes. Persist explicit assigned-vs-delivered-vs-opened exposure status.
5. **Operations:** list jobs, blocks, assignments, dates, access denials and receipts. The dashboard cannot infer validity or "accuracy" from mere completion.
6. **Release:** single task or batch only after all preconditions pass, with idempotency key, immutable task revision and delivery authorization. No silent in-place edits; revoke/retire and create new revision on change.

### 3.2 Expert on original Workbench
- Unchanged 54b4c2e three-column shell. EA-only identity logs in and sees **only its allowed tasks and source revisions** and only its designated workflow phase.
- Expert may inspect source-original and auxiliary translation, choose claims/evidence anchor, give expert-native decision and freeze review. Agent candidate is visible only if strategy permits it and candidate set is frozen.
- No navigation from EA session into NDS R0/R1/R2; switch requires logout and another authorized identity. Hide-only UI gating is never sufficient.

### 3.3 Pilot-gated real-source phase (P2/P3, not now)
- P2: signed source qualification, parser-output verification, rights, bilingual alignment and security tests, human review of source fidelity.
- P3: actual Agent run metadata (model/prompt/input projection/version/tool outputs), independent adjudication design and expert identity/ethics/security signoff before genuine study use.
- Imported real sources must never be admitted through the current synthetic EvidenceEngine by altering only rights_status acceptance.

## 4. Frozen logical objects
Objects are **versioned snapshots**; all create/update APIs require authorization, JSON schema version, mutation request idempotency key and auditable actor/reason.
| Object | Stable identifier and minimum properties | Ownership |
|---|---|---|
| SourceImportJob | import_id, parser_id/version, origin ref, original_sha256, canonical sha256, structured units, import-status, rights | Curator/Parser adapter |
| SourceQualificationRecord | source_id:revision_id, rights_decision_ref, quality/coverage, classification, availability, qualification status, reviewer | Source authority |
| TaskDefinitionRevision | task_id + task_revision_id, kind, profile/version, source allowlist+hashes, cutoff, strategy, exposure_policy_ref, protocol | Producer/Manager proposal, server freeze |
| TaskSourceProjection | task revision, consumer role, authorized source/version/units, original text spans, translation mode, policy digest | Scope gate |
| AgentPreparationRun | run_id, exact model/prompt/tool/config/input projection, candidate refs, candidate-set digest, freeze receipt, provenance | Agent producer |
| ExpertQualificationRecord | expert ID, scope, competency basis, active status, conflict refs, approver; **not** a science Gold claim | Qualified assessor |
| TaskAssignmentRevision | assignment_id, task revision, expert, eligibility receipt, conflict result, arm, authorized scope, assignment history | Assignment authority |
| TaskDeliveryExposureRecord | immutable assignment/issued/eligible/available/opened/spans-visible/agent-visible timestamps and content digests | Server exposure logger |
| TaskExecutionReceipt | task revision, candidate digest if permitted, review digest, reviewer, audit pointers, non-Gold export | Existing EA engine adapter |
| BatchProductionManifest | batch_id, immutable list of proposed task revisions, per-task eligibility and atomic/partial-failure policy | Manager/Producer |

**Separate clocks and states:** Task-definition lifecycle, source qualification, preparation, assignment, delivery/exposure, expert execution and scientific reference are different state machines. In particular ASSIGNED does not imply OPENED; OPENED does not imply ACTUALLY_READ; qualified source does not imply qualified Reference.

## 5. State machines and promotion guards
**Source:** IMPORT_DRAFT → PARSE_RECEIVED → SOURCE_HOLD or SOURCE_VALIDATED → SOURCE_QUALIFIED (separate signoff); never rewrite an existing source revision.  
**Task definition:** DRAFT → SOURCE_HOLD or VALIDATED → DEFINITION_FROZEN → RETIRED. Immutable after frozen.  
**Preparation:** NOT_STARTED → PREPARATION_PENDING → CANDIDATE_FROZEN (Agent workflow) OR INDEPENDENT_PACK_FROZEN (independent workflow) → READY_FOR_ASSIGNMENT; rejects candidates for independent.  
**Assignment:** UNASSIGNED → ELIGIBILITY_CHECKED → ASSIGNED → REVOKED / DELIVERED. Changing expert creates a new assignment revision; previously delivered data cannot be unexposed.  
**Delivery:** NOT_ISSUED → AVAILABLE → OPENED → REVIEW_SUBMITTED, logging **exposure events** separately.  
**Expert execution:** existing EA engine REGISTERED → CANDIDATE_FROZEN (Agent) → EXPERT_REVIEW_FROZEN; independent follows REGISTERED → EXPERT_REVIEW_FROZEN, **do not replace or conflate this with new planning states**.  
**Scientific reference:** NOT_EVALUATED/NOT_ELIGIBLE → external independent scientific process only. TPA must never emit QUALIFIED/PROMOTED GOLD itself.

Minimal release invariant:
~~~
ReleaseAllowed =
  source_qualification_pass
  AND temporal_rights_profile_alignment_pass
  AND immutable_task_definition
  AND projection_acl_and_blind_pass
  AND preparation_frozen_for_selected_workflow
  AND qualified_nonconflicted_expert_assignment
  AND no_prohibited_prior_exposure
  AND explicit publish_permission
~~~

Hard error without side effects on any failed condition. Nonatomic batch imports are explicitly reported and never count a rejected task as published. Retrying a create/publish request with the same idempotency key cannot produce a second task.

## 6. Strict-Blind / security rules
- **SB-01** Explicit EA-vs-NDS principal disjointness, role and task ACL on every API and private source; a manager/producer UI does not inherit expert reader grants.
- **SB-02** HUMAN_INDEPENDENT projection excludes Agent candidate payload, candidate metadata, scored suggestions, candidate count/digest and any embedded answer or feedback; enforced on server response and caches.
- **SB-03** Agent and independent arm allocation must be balanced only via authorized scientific controller; TPA does not invent randomization or quietly expose outcomes. Expert cross-arm contamination is prohibited unless upstream protocol explicitly authorizes within-subject crossover with washout/boundaries.
- **SB-04** Delivery exposure ledger records actual endpoint/units/phase, actor, timestamp, content hash and authorization context; do not claim reading comprehension from OPENED.
- **SB-05** No answer-bearing leakage through translations, titles, filenames, UI default selected candidates, shared browser state, browser cache, debug endpoints, logs, previews, metadata, search results or network response.
- **SB-06** POST/PUT/PATCH/DELETE only within existing D0 cookie + Origin + CSRF perimeter, with manager-specific permissions, no broad CORS and no unprotected /static files.
- **SB-07** Same-origin /manage is **not the same session privilege**: every API verifies explicit authenticated authorization; expose only safe aggregate operational stats to managers where arm-specific data is restricted.
- **SB-08** Assignment revocation blocks future access but never deletes historic exposure; previous read must remain flagged for eligibility review. Draft rollback not equivalent to revoking already issued grants.
- **SB-09** Do not expose PII/PHI or production secrets in synthetic fixtures, audit fixtures, browser test snapshots or UI logs.
- **SB-10** Immutable record conflict (source/task/assignment/version) produces DENY/HOLD, not UPDATE/REPLACE.

## 7. API delta and implementation boundary (proposed, NOT implemented)
- GET /manage — authenticated manager/producer layout in original D0 origin.
- GET /v1/tpa/sources — projected management source library.
- POST /v1/tpa/source-imports/validate — verify a synthetic ImportPackage manifest and hashes in P1; no public PDF ingestion.
- POST /v1/tpa/tasks/drafts — create typed draft + immutable revision ID.
- POST /v1/tpa/tasks/{task_id}/validate — source/profile/cutoff/rights/projection gates.
- POST /v1/tpa/tasks/{task_id}/freeze — immutable definition version.
- POST /v1/tpa/tasks/{task_id}/prepare — synthetic fixture candidates or independent pack in P1.
- POST /v1/tpa/tasks/{task_id}/assign — eligibility check, versioned assignment.
- POST /v1/tpa/tasks/{task_id}/publish — idempotent authorization/delivery.
- GET /v1/tpa/tasks; GET /v1/tpa/batches; GET /v1/tpa/receipts — scoped operational views.
- GET /v1/tpa/audit — auditable ops receipts for auditor roles only.
The real runtime's /v1/ea/** semantics remain unchanged in P0. These endpoints are **contract proposal**, NOT currently callable. Formal request/response JSON Schemas, error catalog and permission test fixtures are P1 deliverables, never inferred from the current EA adapter.

## 8. P0 scientific and non-regression kill tests (must be converted to executable fixtures in P1)
| ID | Attack | Expected |
|---|---|---|
| K01 | EA admin invokes NDS DecisionCase creation | DENY |
| K02 | Real PDF import during P1 synthetic-only phase | HOLD / NO TASK |
| K03 | Wrong profile for registered primary source type | DENY |
| K04 | Unallowlisted source revision or hash substitution | DENY |
| K05 | Source publicly available after knowledge cutoff | DENY |
| K06 | Unknown rights/expired license | HOLD |
| K07 | Translation without matching original-unit anchor | AUXILIARY_ONLY / no evidence promotion |
| K08 | Parser asserts PDF bbox without independent verification | UNVERIFIED |
| K09 | Agent candidate lacks verified original quote/hash or extraction_run_ref | DENY |
| K10 | Publish Agent-review task before candidate freeze | DENY |
| K11 | Independent task returns any candidate metadata | DENY + exposure incident |
| K12 | NDS R0 identity opens EA source; EA identity opens NDS source | DENY both |
| K13 | Manager/producer opens expert-only source under dashboard session | DENY |
| K14 | Expert has prior answer-bearing cross-arm exposure | HOLD / manual adjudication |
| K15 | Assignment revoked after open; claim zero exposure | DENY; keep history |
| K16 | Reuse prior task revision after source correction | DENY, new revision |
| K17 | Retry same batch/publish request twice | Same receipt, no duplicate |
| K18 | Submit expert review and silently generate Gold | DENY |
| K19 | Future correction/retraction contaminates historical cutoff | DENY |
| K20 | Original D0 R0/R1/R2 PDF.js, bilingual and 19 fields regress | P1 NON-REGRESSION FAIL |
| K21 | Import package contains PHI/PII in synthetic demo | HOLD |
| K22 | Static URL/cache/search or translation leaks ungranted source | DENY |
| K23 | Concurrent assign/publish races result in two owners | DENY conflicting transaction |
| K24 | UI hides a control but backend permits forbidden operation | SECURITY FAIL |

P1 acceptance is conditional on running these fixtures plus baseline 14 original D0+EA tests and Chromium actual-browser checks; static review alone is insufficient. P2/P3 add real original-vs-canonical matching, translation fidelity, source qualification reliability, independent expert validity, ethics and production security.

## 9. Stage acceptance and release decisions
| Stage | Minimum acceptance | Stage authority |
|---|---|---|
| **TPA-P0 (current)** | Exact design decisions recorded; normative workflow/roles/states/invariants; explicit source-of-truth mapping; negative fixture manifest; protected-paths unchanged; document diff reviewed | User-approved **DESIGN FREEZE** only |
| TPA-P1 | Operational /manage + API using synthetic source only; independent identity gates; task draft/import/validate/freeze/prepare/assign/publish; idempotency; real browser and CI negative tests | Engineering SYNTHETIC ACCEPTANCE only |
| TPA-P2 | Independently imported real source, rights/time qualification, CanonicalDocument+original anchor fidelity, bilingual sidecar and review; signed source qualification | Real-source access only after approval |
| TPA-P3 | Genuine Agent-run provenance and expert workflow protocol, pilot and security/ethics/expert authorization; independent reference lane | Pilot GO requires external signoffs |

**NO GO:** P0 does not authorize PR #26 merge, real-data API enablement, real-user account provisioning, network deployment or Gold promotion.

## 10. Baseline and scope
- Parent PR: https://github.com/gitzhangcd/NutriFoundation/pull/26 (DRAFT; never merge as part of P0).
- Accepted upstream original-D0 + synthetic EA run 37965935534 (14 tests PASS) and native Chromium run 37965935533. These receipts **predate this document** and must not be reported as new TPA runtime acceptance.
- Normative machine companion: docs/workbench/contracts/WB-TPA-P0_v0.1.json
- Behavioral cases: docs/workbench/contracts/WB-TPA-P0_Negative_Fixtures_v0.1.json
- Frozen design change policy: amendments require a new WB-TPA contract version, impact audit and explicit user approval; no silent changes to this v0.1 record.

## 11. References consulted for boundaries
- Actual repo: apps/workbench/d0/{ea_runtime.py,ea_adapter.py,ea_seed.py,ea_contract.v0.1.json,d0_app.py,auth.py,web/ea_mode.js} at PR #26 head.
- Uploaded materials: SIS-v0.3.1-R5-Regenerated-Master-Specification.md; SIS-MED v0.3.1 R6 P0.4 Regenerated Master Spec; AI Nutri Research + Scientific Data + Evidence Ecosystem Master Specification v2.0; Nutrition_Foundation_v0.1_Integrated_Master_Specification.md; Nutrition-Data-Foundation-D0–D2-+-NDS-R1.txt.
- Interpretation: scientific models inform safeguards, but this new TPA operational design is an extension requiring scientific-owner and security review before any real data.
