# Batch001 Evidence Extraction Runbook v0.1

## Input

Registered SourceArtifact objects.

## Agent Pipeline

1. Acquisition Agent
2. Metadata Normalization Agent
3. Evidence Extraction Agent
4. Verification Agent
5. Human Audit

## Output Objects

- SourceArtifact
- EvidenceUnit candidate
- Verification record

## Agent Constraints

Agents may propose objects but cannot directly freeze scientific claims.

Human review remains the authority for scientific validity.
