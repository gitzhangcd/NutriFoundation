# Evidence Extraction Protocol v0.1

## Objective

Convert scientific literature into structured AI Nutri evidence objects.

## Input

Supported sources:

- Randomized Controlled Trial
- Meta-analysis
- Systematic Review
- Cohort Study
- Guideline
- Consensus Statement

## Extraction Pipeline

```text
Publication
    ↓
SourceArtifact
    ↓
EvidenceUnit
    ↓
ScientificClaim
```

## EvidenceUnit Required Fields

- Population
- Intervention / Exposure
- Comparator
- Outcome
- Effect estimate
- Follow-up
- Certainty
- Source span

## Scientific Claim Rules

A claim must specify:

- population scope
- intervention scope
- outcome scope
- evidence limitation
- applicability boundary

## Prohibited Transformation

Do not transform:

association → causation

population evidence → individual recommendation

single study → universal claim

## Human Review Gate

Agent extraction is considered candidate output only.

Final scientific objects require verification.
