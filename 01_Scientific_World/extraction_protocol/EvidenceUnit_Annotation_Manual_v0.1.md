# EvidenceUnit Annotation Manual v0.1

## Purpose

Define how AI Nutri converts scientific publications into verifiable EvidenceUnit objects.

## Core Principle

```
Publication != EvidenceUnit
EvidenceUnit != ScientificClaim
```

## Required Fields

### Population
- Who was studied?
- Inclusion criteria
- Baseline characteristics

### Intervention / Exposure
- Dietary intervention
- Nutrient exposure
- Lifestyle factor

### Comparator
- Control group
- Alternative intervention
- Baseline condition

### Outcome
- Clinical outcome
- Biomarker
- Functional outcome

### Effect
Record:
- effect direction
- effect size
- uncertainty
- statistical information

### Follow-up
Record study duration and observation window.

### Certainty
Record:
- evidence quality
- limitations
- risk of bias

### Source Span
Every EvidenceUnit must link back to the original text location.

## Annotation Workflow

```
SourceArtifact
      |
      v
Agent Candidate EvidenceUnit
      |
      v
Verification
      |
      v
Human Audit
      |
      v
Frozen EvidenceUnit
```

## Forbidden Transformations

Do not convert:

```
Association -> Causation

Population finding -> Individual recommendation

Single study -> Universal nutrition rule
```
