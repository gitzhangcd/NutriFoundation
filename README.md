# AI Nutri Data Foundation v0.1

## Current UDF execution baseline (v2.1, 2026-11-25)

For new unified nutrition data foundation work, use **[AI Nutri Unified Data Foundation v2.1](docs/AI_Nutri_Unified_Data_Foundation_v2.1.md)** as the governing implementation plan for NutriFM, nutrition decision intelligence, E2H nutrition science communication, and SIS controlled experiments.

- B0/U1-A: [NutriData native audit](docs/udf/B0_U1-A_NutriData_Real_Asset_Audit_v0.1.md) and [public sample exploration](docs/udf/B0_U1-A_Public_Sample_Exploration_v0.1.md) are bounded development receipts; original 22 archives and scientific qualification remain open.
- B1/U2-A: [real source-native contract and round-trip audit](docs/udf/B1_U2-A_Source_Native_Contract_and_Real_Roundtrip_v0.1.md) has passed the bounded real draft gate (23 input files, 747 records, 5,699 typed objects, 46 contract checks); global B1 freeze and production release remain HOLD. [Machine-readable receipt](runs/B1/U2-A/real_003/B1AdmissionReceipt.json).
- B1/U2-B: [measurement semantics, namespace qualification and D0 shared bridge](docs/udf/B1_U2-B_Measurement_Semantics_Namespace_D0_Bridge_v0.1.md) passed the bounded real draft gate (43 definitions, 2,851 measurement interpretations, 19 namespaces, 770 exact shared bridge round-trips, 49/49 checks). [Machine-readable receipt](runs/B1/U2-B/real_003/B1BAdmissionReceipt.json). Full B1 freeze and research releases remain HOLD; source arithmetic conflicts and unresolved code domains must not be promoted.
- B2/U3-A: [canonical vocabulary, source families and candidate alignment](docs/udf/B2_U3-A_Canonical_Vocabulary_Source_Family_Candidate_Alignment_v0.1.md) passed the bounded development gate (65,592 native vocabulary records, 17,079 candidate food mappings, 112 candidate component mappings, 216,827 persisted objects, 34/34 contract checks; 44 source-only review queue entries, 0 reviewed). [Machine-readable receipt](runs/B2/U3-A/real_002/B2AdmissionReceipt.json). No accepted cross-source semantic equivalence or MappingRelease; global B0/B1/U3 freeze remains HOLD.
- U2-C: [joint scientific-contract hardening and non-regression](docs/udf/B1_U2-C_Scientific_Contract_Consolidation_Runtime_Enforcement_v0.1.md) passed bounded development validation (253,249 schema-validated and replayed objects; 56/56 integration and 141/141 historical checks; all 2,851 actual measurement requests held, including 65 explicitly conflicted totals). [Admission receipt](runs/B1/U2-C/U2CAdmissionReceipt.json). The new versioned consumer boundary is required for subsequent UDF development; preserve PR55–57 legacy runs. Real OFF nonstandard-unit evidence, production consumer integration, rights and global physical freeze remain HOLD; no scientific release.
- B2/U3-B: [local multilingual generator pilot and independent-review preparation](docs/udf/B2_U3-B_Bilingual_Semantic_Expansion_Independent_Review_Pilot_v0.1.md) passed bounded generator conformance and freeze (284 queries, 28,845 targets, 29,081 pre-rank candidates, 568 rule-conflict candidates, 2,556 shortlists, 29,366 typed objects, 24/24 checks). Original 44 review cases unchanged; separate 44-case review packet frozen. Fixed-top-k coverage is not accuracy or recall. [Admission receipt](runs/B2/U3-B/U3BAdmissionReceipt.json). Independent review and scientific qualification remain HOLD.
- B2/U3-B-C1: [independent Critic freeze verification and development disagreement analysis](docs/udf/B2_U3-B-C1_Independent_Critic_Freeze_and_Development_Disagreement_v0.1.md) passed bounded development comparison on the original 44 U3-A cases after PI-authorized unblinding (195 verified Critic target citations; 355 generator candidates; 32 shared target edges; 23 Critic hard-negative overlaps; 36 priority expert cases; 16/16 replay checks). No independent accuracy/recall or expert qualification; U3-B new queue unchanged. [Admission receipt](runs/B2/U3-B/C1/C1AdmissionReceipt.json).
- B2/U3-B-C2: [FoodOn scope, semantic risk remediation and expert preparation](docs/udf/B2_U3-B-C2_FoodOn_Scope_Semantic_Risk_Expert_Preparation_v0.1.md) passed bounded development execution and full replay (40,107 scope assessments, 35,710 risk records, 656 query decisions, 36 source-first expert tasks; 76,509/76,509 objects, 26/26 checks and 8/8 synthetic response-schema tests). Six omitted classes recovered in typed candidate lanes; 250/284 historical dense queries abstained under deliberately conservative eligibility. Zero scientific transfer or MappingRelease; expert review and independent implementation audit remain HOLD. [Admission receipt](runs/B2/U3-B/C2/C2AdmissionReceipt.json).
- B2/U3-B-C2-R1: [verified admission and audit regressions](docs/udf/B2_U3-B-C2-R1_Verified_Admission_and_Expert_Isolation_v0.1.md). C2-A1 frozen findings verified (5 RED/6 AMBER/1 INFO); 76,473 exact overlays replayed, 52/52 checks, both original bypasses reproduced and rejected at the new gate, five specific semantic mismatches held. Crucial coverage HOLD: 284/284 original Chinese queries abstain; only seven prior exposed edges have development review eligibility. Expert dispatch and actual isolation/qualification remain HOLD. [Admission receipt](runs/B2/U3-B/C2/R1/R1AdmissionReceipt.json).
- B2/U3-B-C2-R2-P0: [independent semantic calibration and conditional question comparison](docs/udf/B2_U3-B-C2-R2_Independent_Semantic_Calibration_v0.1.md). R1-A2 verified 32 inputs and 3 outputs, five original RED regressions blocked, 3 residual AMBER. Frozen 34,766 candidate questions and 4,544 ranked comparator groups across 284 queries and four target scopes; 33/33 validation checks. No relaxation of R1: scientific equivalence, independent reference, new concept review admission, expert dispatch and release remain HOLD. Source-only 44 review plus reserved disjoint 32 development cases. [Admission receipt](runs/B2/U3-B/C2/R2/R2AdmissionReceipt.json).
- Next gate: **R2-P1 independent source-only reference44**, using [the exact review task](configs/audit/tasks/B2_U3R2_REF44_Gemini_001.json). Verify receipt and explicit PI-authorized unblinding before comparison. Reserve the 32 stratified development cases for post-method-freeze review. EA-P0 Workbench integration and expert isolation/Phase-B evidence binding before actual expert assignment. No C3 or B3 scientific release.
- Inspect actual source files before freezing B1 physical schemas. Respect the task-specific qualification, provenance, information boundary, independent-reference, private-probe, and non-regression gates in v2.1.
- The adopted planning baseline is not a claim of empirical validation: the master document retains its design-candidate status and open real-data/experimental gates.
- SIS, SIS-MED (where applicable), Nutrition Foundation and NDF-D0–D2 retain upstream scientific authority. Existing frozen experiments, tags, reference/scoring artifacts and historical reports remain unchanged; reconcile any conflicts explicitly rather than silently rewriting them.

Every new UDF work package should cite the version and relevant section of this document, record the current milestone, actual evidence and unresolved gates, and identify decisions requiring PI confirmation.

## Purpose

AI Nutri Data Foundation is the scientific data infrastructure for evidence-grounded, applicability-aware, state-aware, safety-constrained nutrition decision intelligence.

Core principle:

```
Observation != Evidence != Claim != Applicability != Decision
```

## P0 Freeze Scope

- Schema Design
- Repository Architecture
- Data Contract
- Provenance and Version Control
- Leakage Prevention

## Architecture

```
Scientific World
SourceArtifact
    -> EvidenceUnit
    -> ScientificClaim
    -> EvidenceSynthesis

Individual World
ObservationArtifact
    -> SemanticState

Bridge
ScientificClaim + SemanticState
    -> ApplicabilityAssessment
    -> DecisionEpisode

Gold
ExpertReference
```

## Current Status

Scientific data construction has progressed through Batch001 strict-blind execution, Evaluator V2 repair, discrepancy attribution, and E0.4.2-E3-A2.8 paper-level evidence freeze.

Engineering reference implementation:

- E0.1 NutriFoundation Engine: executable contract frozen
- E0.2 Persistence + PubMed/PMC + RunManifest + Batch001 SourceArtifact replay: implemented
- E0.3 Evidence Extraction + Independent Verification + F0 Freeze + Batch001 Evidence replay: **PASS (remote CI verified)**
- E0.3.1 Chat-Window Semantic Worker Bridge + Provider Portability: **PASS (remote CI verified)**
- E0.4 Batch001 Blind Semantic Replay + Verifier / Escalation Audit: **PASS (engineering-blind, remote CI verified)**
- E0.4.1 Canonical Semantic Normalization + Calibration + Strict-Blind Gate: **development calibration frozen**
- E0.4.2-A0 Strict-Blind TaskPack + Blind-Wall Audit + Fresh-Context Handoff: **PASS (71 tests / 47 invariants)**
- E0.4.2 strict-blind ResponseSet: **FROZEN (20 responses = 19 completed + 1 safe defer)**
- E0.4.2-E3 Evaluator V2 A2.3–A2.8: **PASS / FROZEN**
- E0.4.2-E3-A2.8 paper-level evidence package: **METHODS_RESULTS_DRAFT_READY_NOT_PUBLICATION_GRADE**
- Frozen authority tag: `E0.4.2-E3-A2.8-FROZEN` → `83a33bbdbb9a647c3aea96a67bf47ba5f246c05a`
- Python package: `src/nutrifoundation/`
- Domain models: Pydantic v2 immutable types
- Workflow state machine: retrieval → F0/F1 → claim → reception → reliability → human gate → GOLD
- CLI: `nutri contract-check`, `nutri validate-gold-gate`, `nutri init-db`, `nutri ingest-pmid`, `nutri fetch-pmc`, `nutri replay-batch001`, `nutri produce-evidence`, `nutri replay-evidence-batch001`, `nutri prepare-chat-task`, `nutri ingest-chat-response`, `nutri list-semantic-tasks`, `nutri prepare-blind-batch`, `nutri blind-task-manifest`, `nutri score-blind-batch`
- Regression fixture: Batch001 Gold gate
- CI: GitHub Actions

Current GOLD invariant:

```text
Agent-only approval != ScientificClaim_GOLD
```

Current Batch001 state:

```text
3 machine-qualified Gold-ready claims
0 frozen GOLD claims
human/expert adjudication pending
```

E0.2 deterministic SourceArtifact replay result:

```text
20 expected SourceArtifacts
20 stored SourceArtifacts
20/20 PMID match
20/20 DOI match
0 mismatch
```

E0.3 deterministic EvidenceUnit replay result:

```text
20 expected EvidenceUnits
20 frozen F0 EvidenceUnits
20/20 scientific payload match
0 mismatch
27 remote tests passed
15 executable invariants passed
```

E0.3 production path:

```text
SourceArtifact
+ SourceTextSnapshot
      ↓
EvidenceExtractionCandidate
      ↓
Independent EvidenceVerificationRecord
      ↓
F0FreezeRecord
      ↓
EvidenceUnit_F0
```

The Batch001 evidence fixture is a regression fixture, not a new independent scientific re-extraction.

See:

- `docs/E0.1_Executable_Contract.md`
- `docs/E0.2_Executable_Contract.md`
- `docs/E0.2_Execution_Report.md`
- `docs/E0.3_Executable_Contract.md`
- `docs/E0.3_Execution_Report.md`


## E0.3.1 provider-portability result

```text
TaskBundle
    ↓
Chat Window / Future Provider Adapter
    ↓
ResponseEnvelope
    ↓
Deterministic binding
    ↓
Independent verifier
    ↓
F0
```

Remote CI:

```text
35 tests passed
23 executable invariants passed
20/20 SourceArtifact replay
20/20 EvidenceUnit F0 replay
Gold remains 0
```

Provider-specific logic is frozen to the adapter boundary. Chat-window execution can later be replaced by API/local-model adapters without changing the scientific pipeline.

See:

- `docs/E0.3.1_Executable_Contract.md`
- `docs/E0.3.1_Execution_Report.md`


## E0.4 engineering-blind semantic replay

```text
20 source-only cases
19 completed responses
1 safe defer

19/20 verifier pass
19/20 F0 freeze
95% verifier/F0 yield

1/20 operational escalation = 5%
14/20 hidden-reference benchmark adjudication = 70%
```

The operational escalation and benchmark adjudication metrics are deliberately separate. Hidden-reference differences cannot trigger production escalation.

This run is **engineering blind**, not strict cognitive blind, because the current conversation had prior Batch001 exposure.

See:

- `docs/E0.4_Executable_Contract.md`
- `docs/E0.4_Execution_Report.md`
- `runs/E0.4/Batch001/Blind_Replay_Report_v0.1.json`


## Paper C｜Scientific Evidence Production

Paper C P0 is now frozen as a publication-level methodology study.

```text
AB0–AB6 workflow comparison
+
new Gold100 confirmatory corpus
+
Critical Scientific Error Rate
+
expert-burden endpoints
+
publication-level kill tests
```

Batch001/E0.1–E0.4 remain development evidence and are excluded from confirmatory Gold100 claims.

See:

- `paper_c/README.md`
- `paper_c/P0/Paper_C_P0_Scientific_Evidence_Production_Study_v0.1.md`


## E0.4.1 canonical semantic calibration

```text
semantic-equivalence development calibration:
43 cases, precision 1.00, recall 1.00

verifier contract calibration:
20 cases, precision 1.00, recall 1.00

Batch001 unchanged responses:
128/137 critical fields equivalent = 93.43%
15/20 complete canonical cases = 75%
```

These calibration sets are not independent expert Gold and are explicitly non-publication-grade.

The current conversation is disqualified from fresh-context strict-blind evaluation. The handoff package is frozen under `runs/E0.4.1/StrictBlind/`.

See:

- `docs/E0.4.1_Executable_Contract.md`
- `docs/E0.4.1_Execution_Report.md`
- `docs/E0.4.1_Strict_Blind_Handoff.md`



## E0.4.2-A0 strict-blind TaskPack

The fresh-context input surface is now frozen independently from hidden reference and scoring artifacts.

```text
20 source-only tasks
same E0.4 task hashes
frozen TaskPack SHA-256
blind-wall audit
fresh-context startup prompt
ResponseEnvelope template
```

The A0 handoff was subsequently executed in a fresh context. The frozen strict-blind response set is preserved under `runs/E0.4.2/A0/StrictBlind_ResponseSet_FROZEN_v1.0.json`; hidden-reference evaluation occurs only after response freeze.

See:

- `runs/E0.4.2/A0/StrictBlind_TaskPack_Manifest_v1.0.json`
- `runs/E0.4.2/A0/Blind_Wall_Audit_v1.0.json`
- `runs/E0.4.2/A0/Fresh_Context_Startup_Prompt_v1.0.md`
- `docs/E0.4.2-A0_Executable_Contract.md`


## E0.4.2-E3 evaluator repair and paper-evidence freeze

The frozen strict-blind Batch001 responses were evaluated through the fixed Evaluator V2 sequence A2.3–A2.8 without regenerating worker outputs.

```text
A2.3 Evaluator V2 schema
→ A2.4 V1→V2 compatibility mapping
→ A2.5 five-dimensional scoring
→ A2.6 frozen batch report
→ A2.7 discrepancy attribution
→ A2.8 non-regression + paper-level evidence freeze
```

Frozen V2 descriptive vector:

```text
Scientific Semantic Recovery  0.9474
Ontology Alignment            0.8596
Provenance Recovery           1.0000
Numeric Fidelity              0.8088
Safe Abstention Quality       1.0000
```

No overall scalar score is defined.

The 44 V1 canonical discrepancy events are frozen as:

```text
21 confirmed evaluator artifacts
 8 preserved scientific residuals
 6 ontology / contract ambiguity
 9 non-isomorphic unresolved
44 total
```

A2.8 remains development/benchmark evidence, not publication-grade evidence. Independent expert Gold and replication remain required.

See:

- `docs/E0.4.2-E3-A2.8_Paper_Level_Evidence_Freeze_v1.0.md`
- `runs/E0.4.2/E3/A2.8/E3_Paper_Evidence_Package_v1.0.json`
- tag `E0.4.2-E3-A2.8-FROZEN`

## Post-Freeze Repository Convergence

On 2026-10-03, `main` was fast-forwarded without force to the frozen A2.8 lineage. Stacked PRs #10–#14 were closed as superseded after verifying that their heads are fully contained in the frozen lineage.

The immutable A2.8 tag remains unchanged. New scientific work must branch from the converged `main`; frozen E0.4.2 artifacts must not be rewritten.

Next program stage:

```text
E0.4.3
Independent Gold / Batch002
Candidate Mining → Case Reconstruction → Candidate Pool → Expert Gold
```
