# Batch-001 First EvidenceUnit Freeze Protocol v0.1

## Objective

Define the execution protocol for converting registered SourceArtifact objects into verified EvidenceUnit objects.

## Workflow

```text
Registered SourceArtifact
        |
        v
Agent Candidate EvidenceUnit
        |
        v
Verification Queue
        |
        v
Human Scientific Review
        |
        v
Frozen EvidenceUnit
```

## Freeze Criteria

A frozen EvidenceUnit must contain:

- Population
- Intervention or Exposure
- Comparator
- Outcome
- Effect interpretation
- Follow-up duration
- Evidence certainty
- Source span
- Provenance record

## Non-regression Rules

EvidenceUnit must not:

- transform association into causation
- remove population boundaries
- omit uncertainty
- create individual recommendations

## Status Labels

- candidate
- under_verification
- verified
- frozen
