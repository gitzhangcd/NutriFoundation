# NF-Q1-P0｜Execution Readout v0.1
Date: 2026-10-16
Scope: downstream of `research/ndf-d1-a2-pilot-two-source-20261011` NDF-D1 A2 pilot.

| Actual measure | Value | Evidence |
|---|---:|---|
| Controlled source set | 2 | R1.3.1/A2 release |
| Upstream EvidenceUnit candidates | 16 | A2 EvidenceUnit_Candidates.jsonl |
| Upstream ScientificClaim candidates | 5 | A2 ScientificClaim_Candidates.jsonl |
| Upstream replayable SourceAnchor index rows | 35 | A2 SourceAnchor_Index.jsonl |
| Source-derived simulated user questions drafted | 16 | NF-Q1-P0 registry |
| Grouped expert fact-review packets | 10 | NF-Q1-P0 review queue |
| Unique question IDs / valid reference links | PASS / PASS | In-memory cross-file ref validation |
| D1 A2 L1/L2 | 16/16 / 16/16 PASS | A2 qualification gates |
| Semantic L3/L4 | 0 qualified / 0 qualified | A2 qualification gates |
| Human approvals executed in NF-Q1 | 0 | No signed review event |
| New full-text extraction executed in NF-Q1 | 0 | Source-based derivation only |
| Independent second extractor/verifier executed in NF-Q1 | 0 | Still required before qualification |
| User-origin question samples collected | 0 | Current questions are synthetic/user-voice generated |
| Production-ready answers / Gold | 0 / 0 | All drafts only |

## Honest interpretation
This run **constructs** a traceable, scoped Question–Evidence candidate corpus from pre-existing A2 records and a grouped human review queue. It **does not** reread 133 PDFs, run a new independent extraction, approve L3/L4, or establish that generated questions reflect observed demand.

## Scientific kill cases included
1. RCT healthy/non-obesity → type-2 diabetes extrapolation (blocked).
2. 5-week/no reported SAE → long-term safety (blocked).
3. RCT short-term weight difference → every individual loses weight (blocked).
4. Observational UPF–obesity association → causal treatment effect (blocked).
5. Exposure quartile vs continuous 10% estimate inconsistency → unsupported mechanistic explanation (blocked).
6. No direct mechanism evidence → no invented causal chain (blocked).
7. Independent source registry 31 evidence questions unavailable → explicit mapping gap, not synthetic upgrade.

## Next implementation gate
Expert must check original source anchors (not only machine paraphrases) on `R-004-HOMA`, `R-033-ASSOC`; then review remaining packets, create immutable judgments, apply L3/L4, and test Workbench persistence/role protections.
