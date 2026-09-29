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


## P1.9-E6.1 — Citation Reception & Reliability Layer

Before a ScientificClaim candidate can enter E7 Claim-Gold adjudication, high-priority claims must obtain sidecar qualification objects:

- CitationReceptionRecord
- ScientificInfluenceSignal
- ClaimReliabilitySignal

Critical separation:

```text
Scientific Influence != Scientific Reliability
Citation Count != Support Count
Supportive Citation != Independent Replication
Journal Metric != Article Validity
```

Journal metrics, raw citations and field-normalized citations may describe visibility, maturity and scientific uptake. They cannot independently upgrade a claim's reliability state.

Claim reliability is evaluated as a vector over intrinsic validity, evidence independence, replication, claim-level reception, integrity, temporal maturity and applicability stability.

Current state:
- ScientificClaim candidates: 11
- Citation-reception work queue: 11
- Populated reception records: 0
- Populated reliability signals: 0
- ScientificClaim_GOLD: 0


## P1.9-E6.2 — P0 Reliability Sidecars

Completed claims:
- SC-B001-C01 → robust
- SC-B001-C05 → convergent; correction-impact escalation required
- SC-B001-C02 → convergent; mixed reception + evidence-overlap escalation required

Current populated sidecars:
- CitationReceptionRecord: 3
- ScientificInfluenceSignal: 3
- ClaimReliabilitySignal: 3

ScientificClaim_GOLD remains 0.

Key lesson from execution:

```text
High Influence + Independent Replication -> may strengthen reliability
High Influence + unresolved correction -> does not remove blocker
High Influence + mixed claim-level reception -> remains mixed/convergent
```
