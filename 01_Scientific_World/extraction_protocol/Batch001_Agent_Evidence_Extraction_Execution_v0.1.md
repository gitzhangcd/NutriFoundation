# Batch001 Agent Evidence Extraction Execution v0.1

## Pipeline

```
SourceArtifact
↓
Extraction Agent
↓
Candidate EvidenceUnit
↓
Verification Agent
↓
Human Scientific Review
↓
Frozen EvidenceUnit
```

## Agent Responsibilities

### Extraction Agent

Extract:

- Population
- Intervention/Exposure
- Comparator
- Outcome
- Effect estimate
- Follow-up
- Limitations

### Verification Agent

Check:

- unsupported causal claims
- missing uncertainty
- incorrect population transfer
- incomplete provenance

## Human Review Gate

Human review is required before:

- EvidenceUnit freeze
- ScientificClaim generation
- benchmark usage

## Output Objects

Candidate:

```
EvidenceUnit_candidate
```

Frozen:

```
EvidenceUnit
```

## Non-Regression Rule

Agent output cannot modify scientific truth ownership.
