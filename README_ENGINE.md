# NutriFoundation Engine v0.2

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
- Offline deterministic Batch001 replay fixture.
- Live Batch001 replay mode.
- CLI commands for DB initialization, PMID ingestion, PMC fetch and Batch001 replay.

## Install

```bash
python -m pip install -e '.[dev]'
```

## Run

```bash
nutri contract-check
nutri init-db --db nutrifoundation.db
nutri ingest-pmid 19721018 SA-B001-001 --db nutrifoundation.db
nutri fetch-pmc PMC3791615 --source-id SA-B001-005 --db nutrifoundation.db

# deterministic offline replay
nutri replay-batch001   fixtures/Batch001_Verified_SourceArtifact_Registry_v0.1.yaml   --fixture fixtures/pubmed_batch001_articles.json   --db batch001_replay.db

# live NCBI replay
nutri replay-batch001   01_Scientific_World/registry/Batch001_Verified_SourceArtifact_Registry_v0.1.yaml   --live   --db batch001_live.db
```

For NCBI production use, set `NUTRIFOUNDATION_EMAIL`; optionally set `NCBI_API_KEY`.
