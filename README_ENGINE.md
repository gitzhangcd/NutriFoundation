# NutriFoundation Engine v0.3.1

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
- Independent deterministic Evidence Verifier.
- Numeric/source/applicability/causality/guideline guards.
- EvidenceExtractionCandidate / EvidenceVerificationRecord / F0FreezeRecord.
- Persistence for source text snapshots, candidates, verification and immutable F0 EvidenceUnits.
- Batch001 20-EvidenceUnit deterministic replay.

## E0.3.1 additions

- Provider-neutral `TaskBundle v0.1`.
- Provider-neutral `ResponseEnvelope v0.1`.
- File-based `ChatWindowFileBridge`.
- Deterministic semantic task state machine.
- Response-to-candidate ingestion with strict field allowlist.
- Task/source/contract hash binding.
- Semantic `defer` without forced guessing.
- `SemanticWorkerAdapter` protocol and conformance harness for future API/local-model migration.
- Downstream verifier/F0 pipeline remains provider-unaware.

## Core architecture

```text
Code
  ├─ retrieval
  ├─ task construction
  ├─ schema/rules
  ├─ hashes/provenance
  ├─ persistence/state
  ├─ deterministic verification
  └─ F0 freeze

Semantic Worker
  └─ source text -> structured semantic response
```

Provider-specific logic is restricted to adapters.

## Chat-window workflow

Prepare a task:

```bash
nutri prepare-chat-task   SA-B001-001   EU-B001-001   --db nutrifoundation.db   --outbox semantic_rpc/outbox
```

The command writes an immutable:

```text
TASK-....request.json
```

The chat model reads the TaskBundle and returns a `ResponseEnvelope` JSON file.

Ingest the response:

```bash
nutri ingest-chat-response   semantic_rpc/inbox/TASK-....response.json   --db nutrifoundation.db
```

The engine then executes:

```text
ResponseEnvelope
  ↓ task/source/contract binding
EvidenceExtractionCandidate
  ↓
IndependentEvidenceVerifier
  ↓
F0FreezeEngine
```

The semantic worker cannot directly create F0.

## Provider migration

A future provider implements only:

```python
class MyProviderAdapter:
    adapter_type = "my_provider"

    def execute(self, task: TaskBundle) -> ResponseEnvelope:
        ...
```

Then it must pass:

```python
run_adapter_conformance(adapter, task)
```

No provider-specific code is allowed in the verifier, persistence layer, F0 freeze engine, ScientificClaim pipeline, or GOLD governance.

## Install

```bash
python -m pip install -e '.[dev]'
```

## Important boundary

The chat-window bridge is an execution transport, not scientific authority.

```text
ResponseEnvelope != EvidenceUnit_F0
```

All scientific guards from E0.3 remain mandatory.
