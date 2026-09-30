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
- Python package: `src/nutrifoundation/`
- Domain models: Pydantic v2 immutable types
- Workflow state machine: retrieval → F0/F1 → claim → reception → reliability → human gate → GOLD
- CLI: `nutri contract-check`, `nutri validate-gold-gate`
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

See `docs/E0.1_Executable_Contract.md` for the executable contract.
