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


## P1.9-E6.1 Claim Qualification Sidecar Lineage

Scientific reception and bibliometric data do not enter the core truth lineage as new EvidenceUnits.

The qualification sidecar lineage is:

```text
SourceArtifact / EvidenceUnit
        ↓
ScientificClaim_candidate
        +
CitationReceptionRecord
        +
ScientificInfluenceSignal
        ↓
ClaimReliabilitySignal
        ↓
E7 Human / Expert Adjudication
        ↓
ScientificClaim_GOLD
```

Rules:

- CitationReceptionRecord must preserve citing-source identifiers, citation context, classification confidence, provider and snapshot date.
- ScientificInfluenceSignal is a visibility/maturity object and cannot directly mutate ScientificClaim truth.
- ClaimReliabilitySignal must preserve all supporting reception and evidence references.
- Historical reception snapshots are immutable; later snapshots create new versions.
- Correction, retraction, failed replication and major critique events require explicit lineage and escalation.
- E7 Claim-Gold freeze must reference the reliability sidecar used at adjudication time.


## E0.2 Execution Lineage

Every SourceArtifact ingestion/replay operation is now bound to an immutable execution record:

```text
RunManifest
    ↓
PubMed / PMC retrieval
    ↓
SourceArtifact
    ↓
ingestion_event
    ↓
persistent registry
```

Requirements:

- RunManifest is created before retrieval begins.
- RunManifest records execution mode, provider, code version, inputs, outputs and failures.
- Completed RunManifest records are immutable.
- SourceArtifact provenance metadata carries the originating `run_id`.
- Database `ingestion_event` independently links each SourceArtifact write to the same run.
- Replay output exposes its `run_id`.
- PMC XML is stored byte-faithfully as retrieved, with SHA-256 and retrieval timestamp.
- Offline replay fixtures are regression inputs only and are not scientific authority.
- Live PubMed/PMC provider records remain the authoritative retrieval source for new scientific ingestion.
