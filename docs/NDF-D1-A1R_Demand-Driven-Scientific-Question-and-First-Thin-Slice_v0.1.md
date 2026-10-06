# NDF-D1-A1R｜Demand-Driven Scientific Question Intake, Knowledge-Need Contract & First R1/P1 Thin-Slice Selection

**Status:** `PASS_SELECTION / SOURCE ACQUISITION OPEN`  
**Date:** 2026-10-07  
**Branch:** `ndf-d1-scientific-core-thin-slice`

## 1. A1R correction objective

A1R implements the A0R rule that D1 is no longer driven by the legacy fixed 31-EvidenceQuestion plan.

The current path is:

[
oxed{
ActiveScientificQuestion
+
DecisionEpisodeNeed
+
ReferenceConstructionNeed
ightarrow
KnowledgeNeed
ightarrow
ScientificKnowledgeThinSlice
}
]

No legacy EQ number is required to activate D1.

## 2. First active scientific question

The first demand-driven question is bound to the existing D2 object:

- Case: `D2-NHANES-L-0001`
- DecisionEpisode: `EP-NHANES-L-0001`
- Subject alias: `SUBJ-NHANES-L-0001`
- Time mode: `EXPERIMENTALLY_DEFINED_CROSS_SECTIONAL`
- Reference: `REFERENCE_PENDING`
- Evaluator: `PENDING`

The authorized view contains age, sex, measured weight/height, BMI, three systolic BP observations and their derived mean. Day-1 total energy is explicitly UNKNOWN because that source component has not been ingested.

The scientific question is:

> Within this authorized information boundary, is there enough information to support an individualized nutrition recommendation now, or is REQUEST_MORE_INFORMATION / DEFER the scientifically defensible action class; and which missing information categories are decision-critical before an individualized recommendation can be qualified?

This is not a declaration that DEFER is already the correct Gold answer.

## 3. Why this is the first R1/P1 slice

This case simultaneously stresses:

[
CriticalMissingInformation
+
Defer/Ask
+
SafetyBoundary
+
ProfessionalJudgment
]

For NDS-R1, it creates a meaningful comparison between expert focus and agent breadth: experts may identify salient missing information while an Agent may recover a broader candidate set, but neither is allowed to define the final reference alone.

For NDS-P1, it tests whether structured reasoning preserves missingness and avoids unsupported personalized action rather than forcing a recommendation.

## 4. Knowledge-Need Contract

A1R freezes five knowledge dimensions:

1. individualized nutrition assessment prerequisites;
2. action-specific information sufficiency;
3. interpretation boundaries for the visible anthropometric/BP observations;
4. safety/referral/escalation boundaries;
5. conflict, uncertainty and alternative process actions.

The contract deliberately does **not** predefine a universal list of mandatory variables. Such a list may only be promoted when qualified sources support it.

## 5. Source policy

The E0.4.3 migration registry remains a candidate reservoir, not a mandatory source set.

[
LegacyCandidate

otRightarrow
CurrentQuestionRelevant
]

Targeted acquisition is expected, especially for current authoritative guideline/standard/official sources.

Gold100 locked-evaluation sources remain prohibited for D1 reference development. Calibration24 remains calibration-only.

The existing D0 fixture `PMID 36670395` is **not selected** for this first thin slice merely because it already exists in the repository. Its relevance to the current information-sufficiency question has not been established.

## 6. Qualification rule

A source must progress through:

[
L1 Mechanical
ightarrow
L2 SourceSupport
ightarrow
L3 SemanticScope
ightarrow
L4 ScientificQualification
]

and the case cannot be considered D1-ready until decision-relevant sources, critical claims, applicability/boundary conditions, conflict, uncertainty and safety information are case-specifically qualified.

## 7. Non-claims

A1R does not establish:

- that DEFER is the final reference;
- which exact missing variables are mandatory;
- any diagnosis from BMI or BP observations;
- any qualified ScientificClaim;
- any evaluator or NDS-P1 activation.

## 8. Next stage

Proceed to:

[
oxed{
	extbf{
NDF-D1-A2R｜
First Thin-Slice Targeted Source Acquisition,
Study Resolution
& Source-Span Qualification
}
}
]

A2R will acquire and qualify real sources against `SQ-D1-A1R-001` and `KN-D1-A1R-001`, then decide whether this case can progress toward a reproducible ScientificReferenceState.
