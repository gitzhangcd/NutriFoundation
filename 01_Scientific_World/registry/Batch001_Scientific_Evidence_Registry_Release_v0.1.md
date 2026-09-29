# Batch001 Scientific Evidence Registry Release v0.1

## Purpose

This document defines the first release contract for the AI Nutri Scientific Evidence Registry.

## Release Boundary

This release contains:

- SourceArtifact registration records
- EvidenceUnit candidate records
- Verification queue references

It does not contain frozen scientific claims or individual recommendations.

## Data Lineage

```text
SourceArtifact
      |
      v
EvidenceUnit Candidate
      |
      v
Verification Queue
      |
      v
Frozen EvidenceUnit
```

## Freeze Rule

Only evidence objects with complete provenance and verification status can enter the frozen registry.
