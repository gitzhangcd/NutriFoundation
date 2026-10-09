# WB-EA-P1｜Versioned Multi-Source Registry, Typed Annotation Workpacks & Agent Candidate Round-Trip

> Status: **SYNTHETIC ENGINEERING CI PASS / SCIENTIFIC-OWNER REVIEW PENDING / REAL-SOURCE SCIENCE NO-GO**  
> Parent: \`WB-EA-P0_Heterogeneous_Source_Annotation_Architecture_v0.1.md\`, P0 proposed adapter \`0.1.0\`  
> Lineage: P0 branch from frozen UI commit \`54b4c2eba844f39c07575573a3e834e0bc00c261\`.  
> PR dependency: WB-EA-P0 Draft PR #24. P1 child branch must not merge into main until upstream review and non-regression signoff.

## 1. Implemented vs not implemented

| Dimension | P1 delivered | Scientific qualification |
|---|---|---|
| SourceRegistry | SQLite immutable \`source_id + revision\`; seven source-type values; canonical text/sha; source availability, fetch time, synthetic rights; source-family metadata | Only synthetic structured text, not qualified real PDF/HTML/Guidelines |
| Multi-source task | Source allowlist, version/sha binding, named primary source, scientific cutoff, task-scoped ACL | 5:2 official reader fixture not imported; task-scoped synthetic documents only |
| Type Router | Exact P0 source_type→profile resolver; incompatible/unknown type fails closed; no NDS decision fallback | All seven profiles are design/proposed, scientific owner approval pending |
| Typed workpack | Task/read-model exposing source-specific \`required_groups\`, candidate object-type allowlist | Not all canonical object required fields validated; not a finished E0–E8 data exporter |
| Agent candidate producer | Authorized Producer submits source-anchored typed candidates with \`extraction_run_ref\`; server verifies text/span SHA, doc SHA and target type; freezes immutable set | Synthetic fixture \`SYN-FIXTURE-NOT-AN-LLM\`; **no live LLM extraction connector / cost tracking** |
| Expert review round-trip | Expert sees frozen candidates; six disposition classes, MODIFY correction and reason; frozen immutable expert review and \`UNQUALIFIED_EXPERT_REVIEW\` export | Synthetic expert test actors only; no clinical/academic qualification |
| Independent blind mode | \`HUMAN_INDEPENDENT\` expert can read allowed sources and submit original answer; candidate API denies exposure | Not double-blind inter-rater Gold or adjudication |
| UI | Separate responsive three-pane EA-P1 synthetic Workbench: source selection/read, profile groups, candidate review, quote selection | Does **not** replace existing D0 5:2 PDF.js bilingual reader; integration/deployment not authorized |
| Audit | Append-only SHA-chained audit log, independently verified by auditor; immutable sources/candidate sets/reviews | No external attestation, signing HSM, production security certification |
| Regression | Existing D0/NDF/NDS directories untouched; GitHub Actions #37942431364 confirms 15/15 runtime/API tests and protected-path checks PASS | Not scientific approval or production conformance |

## 2. Source registration & version identity

\`register_source\` accepts synthetic structured text units and derives:
- \`original_sha256\`: SHA256 of the **synthetic UTF-8 structured text** (units concatenated by two newlines). It is **not** a PDF byte hash.
- \`canonical_document_sha256\`: SHA256 of normalized serialized \`units\`.
- \`source_type_profile_id\`: exact type resolver.
- \`rights_status=SYNTHETIC_FIXTURE\` and \`scientific_capture=false\`.

Second version of the same \`source_id\` MUST use a new \`revision_id\`. Attempting to mutate an existing \`(source_id,revision_id)\` fails. Sources qualify for a task only if \`available_at<=knowledge_cutoff\`, canonical hash matches allowed grant and exact revision is known. Multiple sources permitted, no global unrestricted original route.

## 3. Candidate / expert review exact round-trip

\`\`\`text
SYN-PRODUCER → source version(s) → exact allowlist + profile
→ typed candidate with source_ref, source raw UTF-16 span, quote SHA,
  model/extraction_run_ref and candidate_payload
→ server-side source-span/version/role/field-group validation
→ immutable candidate-set snapshot SHA256 + append-only event
→ SYN-EXPERT only sees frozen CandidateSet for assigned task
→ per-candidate disposition + reason + optional correction JSON
→ server checks all candidates adjudicated & candidate SHA current
→ immutable ExpertReview snapshot + independent review SHA
→ export labeled UNQUALIFIED_EXPERT_REVIEW
\`\`\`

**Failure invariant:** An evidence-review record is a review of a candidate, *not* an authority to promote \`ScientificClaim\`, \`EvidenceUnit\`, \`Recommendation\` or \`GoldAnnotationUnit\`.

The independent reviewer can only access its source allowlist. Candidate access is denied even if an Agent candidate happens to exist elsewhere. No role may use evidence task APIs to obtain frozen NDS case/hidden diet data.

## 4. Runtime boundaries / API

Launch requires explicit \`--allow-synthetic-execution\`. Server binds \`127.0.0.1:8795\` only, session tokens are random local per-process credentials printed only in operator terminal. No external IdP / MFA or production auth. No original PDF static exposure. Main API:

\`\`\`text
GET  /health
POST /v1/ea/sources                             [producer]
POST /v1/ea/tasks                               [producer]
GET  /v1/ea/tasks                               [scoped]
GET  /v1/ea/profiles                            [authenticated]
GET  /v1/ea/tasks/{task}/workpack                [assigned expert/producer/auditor]
GET  /v1/ea/tasks/{task}/sources                 [scoped]
GET  /v1/ea/tasks/{task}/sources/{id}/{revision} [scoped]
POST /v1/ea/tasks/{task}/candidates/freeze       [producer]
GET  /v1/ea/tasks/{task}/candidates              [expert post freeze, producer, auditor]
POST /v1/ea/tasks/{task}/review/freeze           [assigned expert]
GET  /v1/ea/tasks/{task}/export                  [expert/auditor, NOT GOLD]
GET  /v1/ea/audit                               [auditor]
\`\`\`

UI is a standalone isolated engineering route at \`http://127.0.0.1:8795/\`. Existing Workbench D0 remains unchanged and separate.

## 5. Tests / kill gates

- 7 source kinds via synthetic fixtures, including a two-source RCT + guideline task.
- Type resolution, exact sha-revision and time cutoff.
- Cross-task reading denied; wrong expert denied; role isolation.
- UTF-16 original quote selection including surrogate pair boundaries; source mismatch denied.
- Candidate freeze immutability, existing frozen set duplication denial.
- Frozen Agent candidate snapshot then expert MODIFY/ACCEPT and export \`NOT_ELIGIBLE\`.
- Double freeze denied; DB UPDATE/DELETE on registry/candidate/review/audit records denied.
- Independent human cannot access candidate endpoint; original answer frozen.
- No new endpoint for decision-case; \`DECISION_CASE\` receives \`DECISION_CASE_DELEGATE_EXISTING_NDS_ONLY\`.
- Existing 19 NDS-R1 fields and R0/R1/R2 remain under original profile/engine without changes.

**Not tested, do not infer from synthetic tests:** Real 5:2 paper RCT paragraph/table/PDF binding, PDF parser performance, genuine Agent extraction accuracy, biomedical safety interpretation, independent reviewers, blinded adjudication, source acquisition copyright, real experts, leakage-safe Gold, source family resolution beyond storing refs, signature/certificate-backed attestation, production security.

## 6. Next necessary stages

1. \`WB-EA-P1.1\`: integrate existing D0 scientific reader in a server-ACL-preserving way. A generic \`task/source/version\` router must preserve all original PDF/bilingual/SourceAnchor permissions, without mutating D0's synthetic proof or exposing R1 prohibited full PDF.
2. \`WB-EA-P1.2\`: approved real-source ingestion with verified PDF/HTML→CanonicalDocument mapping and qualified original snapshot/rights; independently reviewed translations.
3. \`WB-EA-P1.3\`: actual LLM/Agent extraction adapter, model/prompt/run provenance, extraction/verifier independence, cost and failure logging, typed science validation.
4. \`WB-EA-P1.4\`: multi-reviewer independent annotation/adjudication and authorized scientific object promotion outside Workbench.
5. After these and separate real-expert C2.2 security/ethics/source-version gates: restricted pilot and Evidence Ecosystem validity measurement. Case \`D2-NHANES-L-0001:r2\` ↔ \`:r3\` still requires scientific owner reconciliation.

## 7. Scope boundary

No source, dataset, expert response or science-object status is silently promoted. A fully green P1 synthetic test suite is **engineering readiness only**, not the start of Evidence Ecosystem Gold100 or NDS-R1 real reference capture. Never upload real patient/real expert or unauthorized copyright material into this isolated service.


## 8. Verified CI acceptance receipt (2026-10-09)

- **Verified code commit:** \`3bab5a304ee9597ccf2a79fcf5eb5579e5cfdaf2\` (includes typed source-support review and expert anchor UI).
- **Workflow:** [WB-EA-P1 isolated synthetic acceptance, GitHub Actions run 37942431364](https://github.com/gitzhangcd/NutriFoundation/actions/runs/37942431364).
- **Outcome:** \`conclusion=success\`; isolated job \`test=success\`.
- **Runtime:** Python 3.11.17; pinned existing D0 hash-locked environment plus \`httpx==0.28.1\` for HTTP tests.
- **Unit + HTTP integration:** 15 tests, all passed (\`Ran 15 tests in 0.835s / OK\`).
- **Static P0 contract:** seven profiles, 24 routing/denial vectors, five scientific-review flags → lint PASS.
- **JS parser:** Node syntax check PASS.
- **Protected-path Git diff:** \`54b4c2e→head\` NDF/NDS/science/D0/C1/C2_1 zero protected changes; workflow uses full history and \`pipefail\` → PASS.
- **Important exclusions:** No browser E2E for the new EA-P1 page, no authorized original 5:2 PDF use, no real LLM extraction, no qualified expert, no real paper scientific reliability/accuracy study and no Gold; none of those receives PASS by this receipt.

**Status decision:** \`P1_SYNTHETIC_ENGINEERING_THIN_SLICE_CI_PASS\`, \`P1_RESEARCH_CAPTURE_NO_GO\`. The specific next implementation item is \`WB-EA-P1.1｜D0 Reader Multi-Source Auth Adapter & Original/PDF/Translation Non-Regression\`.
