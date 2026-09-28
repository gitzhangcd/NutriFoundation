# AI Nutri Data Foundation Governance Principles v0.1

## Scientific Object Separation

AI Nutri separates:

- Observation
- Evidence
- Scientific Claim
- Applicability
- Decision

## Two World Architecture

### Scientific World

External scientific knowledge available at decision time.

```
SourceArtifact
 -> EvidenceUnit
 -> ScientificClaim
 -> Recommendation
```

### Individual World

Subject-specific observations.

```
ObservationArtifact
 -> SemanticState
```

## Core Rule

A recommendation must not directly transfer evidence to an individual without applicability assessment.

## Data Requirements

Every object must maintain:

- provenance
- version
- source lineage
- uncertainty
- validation status
