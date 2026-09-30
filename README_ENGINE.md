# NutriFoundation Engine v0.3

Executable reference implementation for the AI Nutri Data Foundation scientific evidence pipeline.

## E0.1 foundation

- Frozen scientific domain models.
- Explicit workflow state machine from retrieval to GOLD.
- Hard guard: Agent-only approval can never create ScientificClaim_GOLD.
- Regression tests against the Batch001 Gold gate contract.

## E0.2 additions

- SQLite persistence for RunManifest, SourceArtifact, full-text XML and ingestion events.
- Live NCBI PubMed connector using E-utilities.
- Live PMC full-text XML connector.
- Immutable RunManifest for every ingestion/replay run.
- SourceArtifact ingestion service.
- Offline deterministic Batch001 SourceArtifact replay.

## E0.3 additions

- Provider-agnostic Evidence Extraction Agent.
- External subprocess JSON adapter for any LLM/agent implementation.
- Independent deterministic Evidence Verifier.
- Numeric support, source linkage, applicability, observational-causality and guideline-authority guards.
- EvidenceExtractionCandidate / EvidenceVerificationRecord / F0FreezeRecord.
- Persistence for source text snapshots, candidates, verification and immutable F0 EvidenceUnits.
- Batch001 20-EvidenceUnit deterministic replay.
- F0 freeze remains distinct from F1 and expert GOLD.

## Install

```bash
python -m pip install -e '.[dev]'
```

## Core commands

```bash
nutri contract-check
nutri init-db --db nutrifoundation.db

# SourceArtifact ingestion
nutri ingest-pmid 19721018 SA-B001-001 --db nutrifoundation.db

# PMC full text
nutri fetch-pmc PMC3791615 --source-id SA-B001-005 --db nutrifoundation.db

# SourceArtifact replay
nutri replay-batch001   fixtures/Batch001_Verified_SourceArtifact_Registry_v0.1.yaml   --fixture fixtures/pubmed_batch001_articles.json   --db batch001_replay.db

# Live EvidenceUnit production through an external structured extractor
nutri produce-evidence   SA-B001-001   EU-B001-001   --extractor-command "python my_extractor.py"   --db nutrifoundation.db

# deterministic EvidenceUnit replay
nutri replay-evidence-batch001   --source-registry fixtures/Batch001_Verified_SourceArtifact_Registry_v0.1.yaml   --evidence-registry fixtures/Batch001_EvidenceUnit_Frozen_v0.1.yaml   --pubmed-fixture fixtures/pubmed_batch001_articles.json   --db batch001_evidence_replay.db
```

## External extractor contract

The subprocess receives one JSON document on stdin with:

- source metadata,
- source text,
- evidence_id,
- frozen E0.3 extraction rules.

It must emit:

```json
{
  "evidence": {
    "population": "...",
    "intervention": "...",
    "comparator": "...",
    "outcome": "...",
    "effect": "...",
    "applicability_boundary": "...",
    "anchor": "..."
  },
  "confidence": 0.95
}
```

The engine injects source/evidence IDs and provenance, validates the EvidenceUnit schema, then runs a separate verifier before F0 freeze.

## F0 authority boundary

```text
Agent candidate
    ↓
Independent machine verification
    ↓
F0 frozen factual/source-stated EvidenceUnit
```

F0 does **not** authorize:

- ScientificClaim GOLD,
- individualized recommendation,
- observational-to-causal promotion,
- guideline statement as independent causal effect,
- F1 full-text methodological qualification.
