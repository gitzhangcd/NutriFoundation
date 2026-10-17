# NF-Q1-P0.1-A0｜Execution Readout v0.1 (2026-10-17)

Scope: provenance-bound, fail-closed **selected A2 span baseline**, not independently enumerated full papers.

## Confirmed upstream inputs
- Reference branch: research/ndf-d1-a2-pilot-two-source-20261011, original baseline commit 5d581e636164de7c959a2be15fabf9e01fdbcc76.
- 2 controlled source artifacts, 2 study identities, 16 EvidenceUnit candidates, 5 ScientificClaim candidates, 35 selected anchored spans.
- A2 upstream L1/L2 for these selected candidates: 16/16. L3/L4: 0. Expert Gold: NOT_GRANTED.
- Existing source collection's PDF hash/identity/rights was checked by A2 previously; **no PDF bytes were reopened in this A0 run**.

## This run
1. Defined document surface and Methods–Results census auxiliary contracts.
2. Materialized source-specific selected anchor census baseline from actual A2 GitHub registries (not a full-paper inventory).
3. Built a **separate downloadable reproducible local test work package** with a standard-library Python contract verifier and deterministic mutation harness.
4. Executed local unit tests: **6/6 PASS**.
5. Injected and checked pre-specified omissions, numerical/causal/scope errors: **16/16 target-specific errors detected**.
6. Kept the full-document census deliberately fail-closed: **HOLD** because raw PDF/table/figure/supplement enumeration was not performed here.

## Scientific interpretation
A2 selected-anchor fidelity is NOT a measure of whole-paper coverage. The 16/16 figure is an exact mutation test result, not an estimate of omission recall in clinical science. A0 does not grant L3/L4, Gold, new source eligibility, or manuscript-ready validity.

## Next real acceptance
G0 source version and rights -> G1 retrieve permitted PDF version+supplement directory -> G2 full page/section/table/figure census -> G3 declared-outcome to reported-result mapping -> G4 independent C coverage auditor -> G5 expert semantics/qualification -> G6 Workbench persistence and UI roundtrip.

## Status
- Contract / selected-span lineage: PREPARED
- Local structural regression: PASS
- Local seeded kill harness: PASS
- Actual full-paper census: HOLD
- Independent PDF coverage re-extraction: NOT_EXECUTED
- Human scientific qualification: NOT_GRANTED
