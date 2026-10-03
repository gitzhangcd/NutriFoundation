# AI Nutri Data Foundation v0.1

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
