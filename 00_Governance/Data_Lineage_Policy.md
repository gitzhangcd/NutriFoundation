# AI Nutri Data Foundation v0.1

# Data Lineage Policy Freeze

## Purpose

Define how every scientific object is generated, transformed, validated, versioned and traced.

## Core Principle

```
SourceArtifact
    ↓
EvidenceUnit
    ↓
ScientificClaim
    ↓
ApplicabilityAssessment
    ↓
DecisionEpisode
    ↓
ExpertReference
```

Every downstream object must preserve upstream provenance.

## Lineage Requirements

Each object must record:

- parent objects
- transformation operation
- creator (agent/human)
- timestamp
- version
- validation status

## Scientific World Lineage

Scientific knowledge follows:

```
Publication / Guideline
        ↓
Evidence Extraction
        ↓
Evidence Unit
        ↓
Scientific Claim
```

## Individual World Lineage

Individual observations follow:

```
Dataset Source
        ↓
Observation Artifact
        ↓
Observation Bundle
        ↓
Semantic State
```

## Decision Lineage

```
Scientific Claim
+
Semantic State
+
Applicability Assessment
        ↓
Decision Episode
        ↓
Expert Reference
```

## Freeze Rule

No object can exist without lineage metadata.
