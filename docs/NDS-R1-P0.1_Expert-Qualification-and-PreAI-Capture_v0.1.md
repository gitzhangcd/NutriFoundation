# NDS-R1-P0.1｜Expert Qualification, Slot Binding, Pre-AI Capture & Exposure Lock

**Status:** \`PASS_OPERATIONAL_READINESS_EMPIRICAL_CAPTURE_PENDING_REAL_EXPERTS\`  
**Date:** 2026-10-07  
**Case:** \`D2-NHANES-L-0001:r3\`

## 1. What P0.1 accomplishes

P0.1 converts the P0 workflow design into executable human-facing control objects:

\[
ExpertQualification
\rightarrow
SlotBinding
\rightarrow
ExposureLock
\rightarrow
IndependentHumanCapture
\rightarrow
ImmutableFreeze
\]

No expert identity or expert judgment is fabricated.

## 2. Expert slots

\`\`\`text
EXP-R1P0-A → R0 → UNBOUND
EXP-R1P0-B → R1 → UNBOUND
EXP-R1P0-C → R2 → UNBOUND
\`\`\`

A real expert may occupy only one slot for this case.

## 3. Exposure locks

### R0

Permanent no-Agent condition.

### R1

Expert verification cannot open until:

\`\`\`text
expert QUALIFIED
+ slot BOUND
+ AgentCandidateSet FROZEN
+ candidate source spans attached
\`\`\`

### R2

Agent expansion is hard-locked until:

\`\`\`text
expert QUALIFIED
+ slot BOUND
+ J_preAI SUBMITTED
+ exposure assertions PASS
+ J_preAI content SHA FROZEN
\`\`\`

Thus:

\[
\boxed{
AgentExposure_{R2}
>
Freeze(J^{preAI})
}
\]

is enforced as a protocol rule.

## 4. Current human source packet

The original P0 human packet was refreshed after A3R.3.

The current packet:

\`Human_Baseline_Source_Packet_v0.2.json\`

contains the current corrected source-level BP classification rules, including Stage-2 DBP threshold, but deliberately excludes the system's case-specific conclusion.

Therefore:

\[
SourceThreshold
\neq
SystemAnswer
\]

R0 and R2 pre-AI still receive the same source substrate.

## 5. Human workpacks

Current executable templates:

- \`R0_Human_DeNovo_Workpack_v0.2.json\`
- \`R2_PreAI_Workpack_v0.2.json\`
- \`R1_AgentFirst_Verification_HoldPack_v0.1.json\`

R0 and R2 are ready for real qualified experts.

R1 remains intentionally on hold until the AgentFirst candidate set is generated and frozen.

## 6. Immutability

For R2:

\[
J^{preAI}
\]

must be frozen using a submission receipt containing:

\`\`\`text
expert slot
submission time
content SHA
exposure check = PASS
\`\`\`

Post-Agent reconciliation creates a new \(J^{postAI}\); it can never overwrite \(J^{preAI}\).

## 7. Current empirical boundary

No real expert has yet been bound.

Therefore:

\`\`\`text
Qualified experts        0 / 3
R0 judgments             0
R2 J_preAI               0
Agent candidate sets     0
Reconciliations          0
QualifiedReference       NOT CREATED
\`\`\`

P0.1 is operationally ready but not empirically complete.

## 8. Required next action

The first true empirical event is not an Agent run.

It is:

\[
\boxed{
QualifiedExpert
\rightarrow
IndependentHumanCapture
}
\]

Most importantly, the R2 expert must submit and freeze \(J^{preAI}\) before any R2 Agent candidate is generated or exposed.
