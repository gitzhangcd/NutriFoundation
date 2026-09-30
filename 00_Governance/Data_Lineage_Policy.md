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


## E0.3 Evidence Production Lineage

Executable EvidenceUnit production follows:

```text
RunManifest
    ↓
SourceArtifact
    +
SourceTextSnapshot
    ↓
EvidenceExtractionCandidate
    ↓
EvidenceVerificationRecord
    ↓
F0FreezeRecord
    ↓
EvidenceUnit_F0
```

Requirements:

- Extraction candidate preserves extractor identity, method, confidence and exact source-text SHA-256.
- Independent verifier identity must differ from extractor identity for any `verified` result.
- Verification must explicitly record source linkage, required-field presence, source anchor, numeric support, applicability boundary, observational-causality guard and guideline-authority guard.
- A rejected verification record is retained for audit; rejection must not be silently discarded.
- F0 freeze requires a `verified` EvidenceVerificationRecord and matching candidate/verification source-text hash.
- Frozen F0 payloads are immutable. New evidence or corrected extraction requires a new version/object rather than silent mutation.
- F0 is source-linked factual/source-stated evidence only. It is not F1 methodological qualification and not ScientificClaim/Decision GOLD.
- Batch001 deterministic evidence replay is a regression test of pipeline/state/payload preservation. The frozen fixture is not a new independent scientific source.


## E0.3.1 Semantic Worker Bridge Lineage

Provider-neutral semantic execution follows:

```text
RunManifest
    ↓
SourceArtifact + SourceTextSnapshot
    ↓
TaskBundle
    ↓
SemanticWorkerAdapter
    ↓
ResponseEnvelope
    ↓
Deterministic Binding / Allowlist Validation
    ↓
EvidenceExtractionCandidate
    ↓
IndependentEvidenceVerifier
    ↓
F0FreezeRecord
    ↓
EvidenceUnit_F0
```

Rules:

- `TaskBundle` is immutable and binds source text with SHA-256.
- `ResponseEnvelope` must echo task hash, source-text hash, contract version and response schema version.
- Provider/model identity is execution provenance only; it is not an EvidenceUnit scientific field.
- Unknown provider output fields are rejected by the core engine.
- `defer` is an allowed semantic outcome and must not be converted into a guessed EvidenceUnit.
- Chat-window execution uses file-based request/response transport but the same TaskBundle/ResponseEnvelope contract as future API/local-model adapters.
- A new provider is admissible only after adapter conformance tests pass.
- Downstream verifier, persistence, F0 freeze and GOLD governance must remain provider-unaware.


## E0.4 Blind Evaluation Lineage

Blind semantic evaluation uses a sidecar lineage that is explicitly separated from production truth construction:

```text
SourceArtifact / PubMed SourceText
        ↓
Source-only TaskBundle
        ↓
Frozen ResponseEnvelope
        ↓
IndependentEvidenceVerifier
        ↓
EvidenceUnit_F0 OR OperationalEscalation
        ↓
[only after response freeze]
Hidden Frozen F0 Reference
        ↓
BlindReplaySummary / SemanticErrorTaxonomy
        ↓
Benchmark Adjudication Flags
```

Requirements:

- Hidden reference data is forbidden from TaskBundle construction and semantic-worker input.
- ResponseEnvelope artifacts must be frozen before hidden-reference scoring.
- Operational escalation is computed only from deployment-observable signals: defer/failure/missing response, verifier rejection, no F0 freeze, or explicit semantic uncertainty.
- Benchmark adjudication may use hidden-reference mismatches, but cannot mutate the already frozen semantic response or F0 object.
- Benchmark adjudication rate must not be reported as production human-escalation rate.
- Every run records a `BlindnessClass`.
- `engineering_blind_current_context_prior_exposure` must not be described as strict cognitive blind.
- Lexical/structural hidden-reference scores are evaluation sidecars and are not new EvidenceUnits.


## E0.4.1 Canonical Semantic Evaluation Lineage

Canonical semantic evaluation remains outside the production truth lineage:

```text
Frozen ResponseEnvelope
        +
Frozen F0 Reference
        ↓
CanonicalSemanticForm
        ↓
EquivalenceResult
        ↓
CanonicalBatchSummary
        ↓
Development / Benchmark Evaluation
```

Rules:

- Canonicalization is deterministic evaluation logic and cannot mutate SourceArtifact, EvidenceUnit_F0, ScientificClaim or GOLD.
- Equivalence scoring may use a hidden reference only after semantic responses are frozen.
- Every precision/recall result must record a reference class: contract-generated, model-assisted development, or human-independent.
- Contract-generated and model-assisted development calibration are non-regression evidence only and are never publication-grade validation.
- Human-independent labels must be produced without visibility into model equivalence predictions and frozen before publication-grade scoring.
- Verifier calibration and semantic-equivalence calibration are separate measurement problems.
- Strict-blind scoring is blocked until fresh-context attestation passes.
- Prior Batch001 exposure disqualifies a response set from strict-blind status.
- StrictBlindAttestation is protocol evidence and not cryptographic proof of absence of prior exposure.
