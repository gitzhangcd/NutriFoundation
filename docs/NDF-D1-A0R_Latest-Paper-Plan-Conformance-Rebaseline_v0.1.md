# NDF-D1-A0R｜Latest Paper-Plan Conformance Re-baseline, Legacy EQ Deactivation & Repository Program Routing Freeze

**Status:** `FROZEN_CORRECTION_BASELINE`  
**Date:** 2026-10-07  
**Branch:** `ndf-d1-scientific-core-thin-slice`

## 1. Correction decision

The latest paper plan supersedes the older Paper 1 planning path that treated a fixed 31-EvidenceQuestion registry and EQ-010 as the current D1 execution authority.

The current authoritative execution chain is:

[
oxed{
NDF	ext{-}D0
ightarrow
(NDF	ext{-}D1 parallel NDF	ext{-}D2)
ightarrow
NDS	ext{-}R1
ightarrow
NDS	ext{-}P1
ightarrow
P2/P3/P4/P5
}
]

Historical files are preserved for lineage; their current authority is explicitly removed.

## 2. Latest paper routing

| Program | Source workline | Scientific role |
|---|---|---|
| NDS-R1 | N1 + N7 | Reference Construction Science: Human Focus × Agent Breadth × Expert Reconciliation |
| NDS-P1 | N2 | Structured Decision Intelligence |
| NDS-P2 | N3 | Active Information Acquisition |
| NDS-P3 | N4 + N6 | Decision Trajectory + Failure & Recovery |
| NDS-P4 | N5 | Component × System / capability interaction |
| NDS-P5 | N8 | Transportability |

The critical separation is:

[
oxed{
NDS	ext{-}R1 
eq NDS	ext{-}P1
}
]

R1 asks how a high-fidelity reference should be constructed. P1 asks whether structured scientific decision architecture improves decision capability.

## 3. What remains valid from D1-A0

The E0.4.3 migration audit remains valid for:

- source identity and provenance migration;
- purpose separation;
- Gold100 locked-evaluation quarantine;
- Calibration24 isolation;
- SourceArtifact → StudyIdentity → SourceAnchor recoverability;
- legacy candidate reuse only after new D1 qualification.

Therefore the 330-source migration registry is retained as a migration substrate, not as a Paper 1 knowledge universe.

## 4. What is deactivated

The following are no longer current execution authority:

- the legacy 31 Evidence Questions as the D1 driver;
- EQ-010 as the first authoritative thin slice;
- the old fixed Paper 1 reference package;
- any assumption that Paper C challenge coverage equals NDS-P1 knowledge completeness.

The previous `Thin_Slice_Candidate_Lock_v0.1.json` is retained only as historical planning lineage and must not activate acquisition, qualification, reference construction or P1 evaluation.

## 5. D1 re-baseline

D1 is now demand-driven:

[
oxed{
ActiveScientificQuestion
+
DecisionEpisodeNeed
+
ReferenceConstructionNeed
ightarrow
ScientificKnowledgeThinSlice
}
]

The controlling invariant is:

[
oxed{
EvidenceQuestionRegistry 
eq PaperPlan
}
]

A numbered EvidenceQuestion may still be created later as a local execution object, but only after it is derived from a current R1/P1 scientific need. Legacy EQ numbering has no automatic authority.

## 6. Program-routing freeze

Repository interpretation is now:

[
SIS R5
succ
Nutrition Foundation
succ
NDF
succ
NDS Research Program
succ
Experiment/Benchmark
succ
Engineering
]

Legacy `paper_c/` and `runs/E0.4.x/` assets remain preserved as historical or conditional scientific evidence-production lineage. They do not define the current NDS-P1 research question.

## 7. Gate result

| Gate | Result |
|---|---|
| Latest paper-plan authority recovered | PASS |
| Legacy EQ authority deactivated | PASS |
| E0.4.3 migration lineage preserved | PASS |
| Repository program route frozen | PASS |
| Silent history rewrite avoided | PASS |

## 8. Next executable stage

Proceed to:

[
oxed{
	extbf{
NDF-D1-A1R｜
Demand-Driven Scientific Question Intake,
Knowledge-Need Contract
& First R1/P1 Thin-Slice Selection
}
}
]

A1R must begin from an active NDS-R1 or NDS-P1 need and derive its scientific question and knowledge requirements. It must **not** start by migrating the old 31-EQ registry.
