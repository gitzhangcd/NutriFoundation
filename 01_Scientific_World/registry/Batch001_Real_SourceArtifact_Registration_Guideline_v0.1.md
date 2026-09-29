# AI Nutri Data Foundation v0.1

# P1.8｜Batch001 Real SourceArtifact Registration Guideline

## Objective

This document defines the operational rules for registering SourceArtifact-001 to SourceArtifact-020.

## Principle

No fabricated records are allowed.

Each SourceArtifact must originate from a verifiable scientific source with provenance.

## Required Fields

- source_id
- title
- source_type
- authors
- publication_year
- DOI/PMID or authoritative identifier
- nutrition_domain
- study_population
- intervention_or_exposure
- comparator
- outcome
- provenance
- verification_status

## Status Lifecycle

candidate → screened → registered → extraction_ready → verified → frozen

## Linkage Rule

Every EvidenceUnit must reference exactly one registered SourceArtifact.
