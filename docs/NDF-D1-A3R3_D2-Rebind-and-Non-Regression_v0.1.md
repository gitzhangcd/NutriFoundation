# NDF-D1-A3R.3｜D2 Observation Completion Rebind, BP Applicability Refresh & Non-Regression Freeze

**Status:** \`PASS_D1_D2_REBIND_READY_FOR_NDS_R1\`  
**Date:** 2026-10-07  
**Case:** \`D2-NHANES-L-0001:r2\`  
**SRS:** \`SRS-D1-A3R-001:r4\`

## 1. Why rebind was required

D2 restored source-observed diastolic blood pressure that was absent from the earlier systolic-only case view:

\[
SBP = [135,131,132], \quad
DBP = [98,96,94]
\]

The deterministic means are:

\[
\overline{SBP}=132.6667,\qquad
\overline{DBP}=96.0
\]

Under the current 2025 AHA/ACC framework:

- stage 1: SBP 130–139 **or** DBP 80–89 mmHg;
- stage 2: SBP ≥140 **or** DBP ≥90 mmHg.

Therefore the completed-view numerical mapping is:

\[
SBP\ component = Stage\ 1
\]

\[
DBP\ component = Stage\ 2
\]

and, because the framework uses OR logic:

\[
\boxed{OverallNumericalCategory=Stage\ 2}
\]

This remains a numerical category mapping, **not a confirmed diagnosis**.

## 2. Minimal claim delta

Only three claims changed at all:

- \`SC-A3R-001\`: wording-only rebind from “systolic-BP observations” to “blood-pressure observations”;
- \`SC-A3R-003\`: boundary scope refreshed to include systolic and diastolic measurements;
- \`SC-A3R-004\`: material case-mapping revision from the prior systolic-only stage-1 interpretation to completed-view stage-2 numerical mapping.

The prior v0.2 claim is preserved in history and marked superseded for the completed D2 view rather than deleted.

## 3. Non-regression

The following claims remain scientifically unchanged:

- \`SC-A3R-002\`;
- \`SC-A3R-005\`;
- \`SC-A3R-006\`;
- \`SC-A3R-007\`.

Aggregate epistemic state remains:

\`\`\`text
SUPPORTED             5
PARTIALLY_SUPPORTED   2
Effect certainty N/A  7
\`\`\`

No source set, methodological appraisal or certainty framework was silently changed.

## 4. SRS r4

\`SRS-D1-A3R-001:r4\` is now bound to:

\[
D2\text{-}NHANES\text{-}L\text{-}0001:r2
\]

with:

- completed visible BP tuple;
- explicit diet mask;
- refreshed BP applicability;
- impacted-claim replay;
- non-regression record.

Status:

\`D1_D2_REBOUND_EPISTEMICALLY_APPRAISED_AND_REPRODUCIBILITY_QUALIFIED\`.

## 5. Convergence decision

For this first thin slice:

\[
D1Ready \land D2InputReady
\]

is now true.

Therefore:

\[
\boxed{
ReadyForNDS\text{-}R1ReferenceWorkflow
}
\]

This does not mean \`REFERENCE_QUALIFIED\`.

The next scientific stage is the first NDS-R1 Human Focus × Agent Breadth reference-construction pilot.
