# AI Nutri Literature Acquisition Pipeline v0.1

## Purpose

Define the reproducible workflow for acquiring scientific nutrition sources and converting them into SourceArtifact objects.

## Pipeline

```text
Query Strategy
    ↓
Literature Retrieval
    ↓
Eligibility Screening
    ↓
SourceArtifact Registration
    ↓
Evidence Extraction Queue
```

## Supported Sources

- PubMed
- Crossref
- Guideline repositories
- Consensus documents
- Clinical trial registries
- Public cohort databases

## Acquisition Metadata

Each source must record:

- source_id
- retrieval_date
- query_strategy
- database
- inclusion_reason
- exclusion_reason
- provenance

## Principle

Raw literature is not directly used for decision making. Every source must pass through SourceArtifact and EvidenceUnit transformation contracts.
