# NutriFoundation Engine v0.1

Executable reference implementation for the AI Nutri Data Foundation scientific evidence pipeline.

## E0.1 scope

- Frozen domain models for SourceArtifact, EvidenceUnit, ScientificClaim, CitationReceptionRecord, ScientificInfluenceSignal, ClaimReliabilitySignal and HumanAdjudicationRecord.
- Explicit workflow state machine from retrieval to GOLD.
- Hard guard: Agent-only approval can never create ScientificClaim_GOLD.
- JSON/YAML loaders and CLI validation commands.
- Regression tests against the Batch001 Gold gate contract.

## Install

```bash
python -m pip install -e '.[dev]'
```

## Run

```bash
nutri contract-check
nutri validate-gold-gate 01_Scientific_World/claim_registry/Batch001_ScientificClaim_Gold_Registry_v0.1.yaml
pytest -q
```
