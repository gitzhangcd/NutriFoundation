# Literature Extraction Agent Workflow v0.1

## Goal

Use agents for scalable evidence preprocessing while preserving human scientific ownership.

## Workflow

```text
Scientific Paper
        ↓
Extraction Agent
        ↓
Candidate SourceArtifact
        ↓
Evidence Extraction Agent
        ↓
Candidate EvidenceUnit
        ↓
Verification Agent
        ↓
Human Audit
        ↓
Frozen Registry Object
```

## Agent Roles

### Acquisition Agent

- Search literature
- Collect metadata
- Detect duplicates

### Extraction Agent

Extract:

- Population
- Intervention
- Comparator
- Outcome
- Effect
- Limitations

### Verification Agent

Check:

- Unsupported claims
- Causal overreach
- Missing uncertainty
- Provenance completeness

## Human Role

Humans validate scientific correctness and final freeze decisions.

Agent output is always provisional.
