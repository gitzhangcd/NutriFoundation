# NutriFoundation Engine v0.4.0

Executable reference implementation for the AI Nutri Data Foundation scientific evidence pipeline.

## E0.1–E0.3.1 foundation

The engine already provides:

- immutable scientific domain models;
- PubMed / PMC ingestion and persistence;
- RunManifest execution lineage;
- EvidenceExtractionCandidate / independent verification / F0 freeze;
- deterministic Batch001 source and EvidenceUnit replay;
- provider-neutral TaskBundle / ResponseEnvelope contracts;
- ChatWindowFileBridge;
- SemanticWorkerAdapter portability contract;
- mandatory human gate before ScientificClaim_GOLD.

## E0.4 additions

E0.4 adds a source-only semantic evaluation harness:

```text
Source-only PubMed fixture
    ↓
Deterministic TaskBundle
    ↓
Chat-window semantic response
    ↓
Independent verifier
    ↓
F0 / operational escalation
    ↓
Hidden frozen reference loaded only for scoring
    ↓
Benchmark adjudication + error taxonomy
```

New capabilities:

- deterministic blind task generation;
- hidden-reference isolation from task construction;
- persisted chat-window ResponseEnvelope benchmark artifacts;
- BlindReplaySummary;
- SemanticErrorTaxonomy;
- verifier-yield measurement;
- operational human-escalation measurement;
- hidden-reference benchmark adjudication;
- numeric verifier calibration for percent and range syntax;
- explicit blindness classification.

## E0.4 final Batch001 result

```text
cases                         20
completed responses           19
safe defer                     1

verifier pass                 19/20
F0 freeze                     19/20
verifier / F0 yield           95%

operational escalation         1/20 = 5%
benchmark adjudication        14/20 = 70%
```

The sole operational escalation was EU-B001-015 because PubMed did not expose an abstract.

The 70% benchmark-adjudication rate is a conservative hidden-reference triage result and must not be interpreted as 70% model failure or 70% production human workload.

## Blindness limitation

The executed E0.4 run is:

```text
engineering_blind_current_context_prior_exposure
```

because this conversation had prior Batch001 exposure.

For a publication-grade model-accuracy estimate, rerun the same frozen TaskBundle contract in a fresh context or independently provisioned provider using:

```text
strict_blind_fresh_context
```

## Core production architecture

```text
Code
  ├─ retrieval
  ├─ task construction
  ├─ schema / rules
  ├─ hashes / provenance
  ├─ persistence / state
  ├─ deterministic verification
  ├─ operational escalation
  └─ F0 freeze

Semantic Worker
  └─ source text -> structured semantic response
```

Provider-specific logic remains restricted to adapters.

## Core E0.4 commands

Generate source-only blind tasks:

```bash
nutri prepare-blind-batch
```

Print deterministic task/hash manifest:

```bash
nutri blind-task-manifest
```

Score frozen semantic responses after generation:

```bash
nutri score-blind-batch \
  --source-fixture fixtures/Batch001_Blind_SourceText_v0.1.json \
  --response-dir runs/E0.4/Batch001/responses \
  --hidden-gold fixtures/Batch001_EvidenceUnit_Frozen_v0.1.yaml \
  --blindness-class engineering_blind_current_context_prior_exposure
```

## Interpretation invariants

```text
VerifierYield != SemanticAccuracy
BenchmarkAdjudication != OperationalEscalation
EngineeringBlind != CognitiveBlind
HiddenReference -> ScoringOnly
BlindDefer -> OperationalEscalation
```

See:

- `docs/E0.4_Executable_Contract.md`
- `docs/E0.4_Execution_Report.md`
- `runs/E0.4/Batch001/Blind_Replay_Report_v0.1.json`
- `runs/E0.4/Batch001/Run_Metadata_v0.1.yaml`
