# NDF-D1-A0｜E0.4.3 Source-Universe Migration, Purpose Audit & Thin-Slice Candidate Lock

**Status:** `PASS_MIGRATION_WITH_SCIENTIFIC_GAPS`  
**Date:** 2026-10-07

## Executive decision

E0.4.3 is a valuable **migration substrate**, but it is not the Paper 1 scientific knowledge universe.

The frozen eligible pool contains 330 sources. Purpose/overlap audit yields:

- 98 overlap with Paper C Gold100 locked evaluation → **QUARANTINE**.
- 24 overlap with Calibration24 → **CALIBRATION ONLY**.
- 208 remain eligible for D1 scientific audit.
- Of those 208, 153 are nutrition/metabolic/cardiometabolic primary candidates and 55 are external biomedical/public-health stress candidates.

Therefore:

[
330 - 98 - 24 = 208
]

and the Paper 1-oriented primary candidate universe begins from:

[
153 	ext{nutrition-domain candidates}
]

not from all 330 legacy records.

## What passed

1. PMID identity is recoverable for all 330 legacy eligible records.
2. StudyIdentity cluster is present for all 330.
3. Worker-visible source-text hash and PubMed record hash are present for all 330.
4. No duplicate PMID exists in the frozen eligible pool.
5. Purpose isolation between Gold100, Calibration24 and D1 development candidates is now explicit.

## What did not transfer

The following legacy states **do not transfer** into D1:

- legacy `ELIGIBLE` → D1 scientific qualification;
- source-level Gold → NutritionDecisionReference;
- Paper C source challenge coverage → Paper 1 EvidenceQuestion coverage;
- E0.4.3 evidence cutoff → Paper 1 evidence cutoff.

## Temporal audit

Legacy pool cutoff is `2026-10-03T23:26:00+08:00`.  
The Paper 1 P0 protocol still contains a candidate cutoff of `2026-08-31T23:59:59Z`.

All 208 remaining sources have original publication-date basis no later than that Paper 1 candidate cutoff, but 16 are correction/living/version-sensitive. Therefore publication date alone is insufficient; exact version-as-of-cutoff reconstruction remains required.

## Scope audit

The legacy universe was created with broad PubMed family queries and coverage repair for source-level extraction/verification stress testing. It has **no explicit mapping to the 31 Paper 1 EvidenceQuestions**.

This creates four gaps:

1. decision relevance is not yet qualified;
2. formal guideline / official recommendation coverage is not guaranteed;
3. official nutrient/safety reference coverage is not guaranteed;
4. 55 external-domain records need explicit EQ justification before any reference use.

## First case-relevant slice

A provisional 8-source candidate lock has been created for **EQ-010｜Dietary patterns in prediabetes/T2D**.

It includes the current D0 seed `PMID 36670395`, which is not present in the legacy E0.4.3 eligible pool. This is direct evidence that D1 must support targeted acquisition beyond legacy migration.

This lock is **candidate-only**:

[
CandidateLock 
eq ScientificReferenceState 
eq QualifiedReference
]

## Gate decision

| Gate | Result |
|---|---|
| A0-G1 Lineage / identity | PASS |
| A0-G2 Purpose isolation | PASS |
| A0-G3 Source→Study→Anchor recoverability | PASS_WITH_DEPENDENCY_MONITORING |
| A0-G4 Temporal compatibility | RECONSTRUCTION_REQUIRED |
| A0-G5 EvidenceQuestion relevance | NOT_YET_PASSED |
| A0-G6 First thin-slice candidate lock | PASS_PROVISIONAL |

## Next stage

Proceed to:

[
oxed{	ext{NDF-D1-A1｜EvidenceQuestion Registry Migration, Scope Reconciliation & Targeted Acquisition Lock}}
]

A1 should first qualify EQ-010 end-to-end, then expand across the remaining 30 EQs.
