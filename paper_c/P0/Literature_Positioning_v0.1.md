
# Paper C P0｜Literature Positioning v0.1

## Scientific question

Paper C does not ask whether an LLM can extract fields from papers.

It asks:

> Which scientific evidence-production architecture best controls critical scientific error while reducing expert burden, under fixed sources, fixed task semantics, explicit provenance, and prespecified human-escalation rules?

## Current evidence landscape

### Gartlehner et al., 2024
Data extraction for evidence synthesis using a large language model: A proof-of-concept study. Research Synthesis Methods. DOI: 10.1002/jrsm.1710.

A small proof-of-concept on 10 open-access RCT reports established feasibility, but did not test a production-grade verifier/auditor/HITL architecture.

### Gartlehner et al., 2025
Artificial Intelligence-Assisted Data Extraction With a Large Language Model: A Study Within Reviews. Annals of Internal Medicine. PMID: 41183336. DOI: 10.7326/ANNALS-25-00739.

- 6 ongoing systematic reviews;
- 63 studies;
- 9341 data elements;
- AI-assisted extraction followed by human verification;
- accuracy about 91% for AI-assisted versus 89% for human-only;
- median extraction-time reduction about 41 minutes per study.

Implication: human-verified LLM extraction is already a credible comparator. Paper C therefore tests architectural increments rather than repeating LLM-versus-human feasibility.

### Simmons et al., 2025
Assessing the Feasibility and Acceptability of a Bespoke Large Language Model Pipeline to Extract Data From Different Study Designs for Public Health Evidence Reviews. Cochrane Evidence Synthesis and Methods. DOI: 10.1002/cesm.70061.

- 24 articles across heterogeneous designs;
- 173 assessed fields;
- overall acceptability about 68%;
- strong field-specific variation;
- human QA remained necessary.

Implication: average accuracy can hide scientifically important field-level failure modes.

### Park et al., 2026
Large language models in systematic review and meta-analysis of surgical treatments for vaginal vault prolapse. npj Digital Medicine. PMID: 41714807.

The work demonstrates feasibility of LLM support across an end-to-end review workflow. End-to-end automation alone is therefore not sufficient novelty.

### Shankar et al., 2026
Performance of large language models in data extraction for evidence synthesis: A systematic review. Journal of Biomedical Informatics. PMID: 42501879.

- 27 included studies;
- extraction accuracy ranged roughly 47% to 99.9%;
- categorical/string fields generally outperformed numerical outcomes;
- human verification remained the defensible use mode;
- standardized benchmarks and comparative studies were identified as priorities.

### 2026 systematic review of LLM-assisted systematic-review tasks
Large language models show promising performance for some systematic review tasks but call for cautious implementation: a systematic review. Journal of Clinical Epidemiology. PMID: 41831731.

- 63 studies;
- 148 performance assessments;
- substantial methodological heterogeneity;
- complex interpretive tasks remained less reliable.

### BMJ Evidence-Based Medicine methodological warning
From promise to practice: challenges and pitfalls in the evaluation of large language models for data extraction in evidence synthesis. DOI: 10.1136/bmjebm-2024-113199.

Key risks include reference-standard quality, contamination, error definition, metric selection, prompt leakage, and practical validation design.

## Scientific gap retained after current literature

Current evidence supports:

LLM + HumanVerification -> UsefulEvidenceExtraction

but does not establish:

WhichArchitecture -> LowestCriticalScientificError

subject to:

ExpertTime + Cost + Latency + Traceability.

Paper C targets this gap.

## Intended novelty boundary

Novelty is not claimed from:
- using an LLM;
- using structured JSON;
- using RAG;
- using multiple agents;
- building a nutrition corpus.

The methodological contribution is controlled comparison of AB0 through AB6 with explicit measurement of:
- critical scientific error;
- provenance/span validity;
- StudyIdentity/dependency errors;
- causal upgrades;
- recommendation-boundary errors;
- temporal/version failures;
- safe defer/escalation;
- expert workload.

## Claim boundary

A successful Paper C may support:

> A contract-driven evidence-production workflow combining structured extraction, independent verification, targeted auditing, and risk-based human review can reduce expert workload while maintaining or improving critical scientific reliability on a prespecified biomedical evidence benchmark.

It must not claim autonomous scientific truth construction, reviewer replacement, universal generalization, or clinical outcome benefit.
