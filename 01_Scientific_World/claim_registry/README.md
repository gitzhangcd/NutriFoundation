# Scientific Claim Registry

## Purpose

Store validated scientific claims derived from evidence objects.

## Claim Lifecycle

```text
EvidenceUnit
      ↓
Candidate Claim
      ↓
Verification
      ↓
Frozen ScientificClaim
```

## Claim Requirements

Every claim must include:

- evidence references
- population boundary
- uncertainty
- limitations
- applicability boundary

Claims are not recommendations.


## Batch001 Current State — P1.9-E6

- Frozen F0 EvidenceUnits: 20
- Cross-source relation map: completed v0.1
- ScientificClaim candidates: 11
- Frozen ScientificClaim gold: 0

### Critical Rule

Claim strength is evaluated on evidence independence, evidence type, population/outcome alignment, uncertainty, and applicability boundaries — not raw reference count.

Synthesis sources, guidelines, and consensus reports may depend on primary studies already present in the registry and therefore must not be double-counted as independent votes.
