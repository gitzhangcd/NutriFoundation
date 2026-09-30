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

Scientific data construction has progressed through Batch001 P1.9-E7 machine qualification.

Engineering reference implementation:

- E0.1 NutriFoundation Engine: executable contract frozen
- E0.2 Persistence + PubMed/PMC + RunManifest + Batch001 SourceArtifact replay: implemented
- E0.3 Evidence Extraction + Independent Verification + F0 Freeze + Batch001 Evidence replay: **PASS (remote CI verified)**
- E0.3.1 Chat-Window Semantic Worker Bridge + Provider Portability: **PASS (remote CI verified)**
- E0.4 Batch001 Blind Semantic Replay + Verifier / Escalation Audit: **PASS (engineering-blind, remote CI verified)**
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
