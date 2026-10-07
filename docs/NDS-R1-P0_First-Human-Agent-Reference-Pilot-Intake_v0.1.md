# NDS-R1-P0｜First Human Focus × Agent Breadth Reference Construction Pilot Intake

**Status:** \`PASS_PILOT_INTAKE_READY_FOR_REAL_EXPERT_BINDING\`  
**Date:** 2026-10-07  
**Case:** \`D2-NHANES-L-0001:r3\`  
**ScientificReferenceState:** \`SRS-D1-A3R-001:r4\`

## 1. Scientific question

NDS-R1 asks:

\[
\boxed{
HowShouldHumanExpertiseAndAgenticKnowledgeBreadth
BeCombinedToConstructHighFidelityDecisionReferences?
}
\]

The pilot does not assume that Agent assistance is superior, and does not define Human De Novo as Gold.

## 2. Three workflow arms

### R0｜Human De Novo

\`\`\`text
Common case + source substrate
→ independent human judgment
→ reference candidate
\`\`\`

### R1｜Agent First → Expert Verify

\`\`\`text
Case + structured scientific state
→ Agent candidate expansion
→ expert verification
→ reference candidate
\`\`\`

This is the high-anchoring-risk comparator.

### R2｜Expert Focus → Agent Expand → Expert Reconcile

\`\`\`text
Common case + source substrate
→ independent expert focus
→ freeze J_preAI
→ Agent breadth expansion
→ expert reconciliation
→ J_postAI
\`\`\`

R2 is the primary candidate workflow, but is **not predeclared as the winner**.

## 3. First-case assignment

For the same case, three independent expert slots are frozen:

\`\`\`text
R0 → EXP-R1P0-A
R1 → EXP-R1P0-B
R2 → EXP-R1P0-C
\`\`\`

All identities remain unbound.

A single expert must not occupy multiple slots for this same case.

This protects against:

\[
Memory + Learning + Carryover
\]

## 4. Common human baseline substrate

R0 and R2 pre-AI use the same Human Baseline Source Packet:

\`HBSP-R1P0-001\`

It contains:

- visible case information;
- source identity/version/date;
- bounded source-support material;
- source locators.

It deliberately excludes:

- D1 ScientificClaim labels;
- evidential-state/certainty labels;
- Agent candidate synthesis;
- final reference;
- meta-audit labels;
- hidden diet values.

Therefore workflow comparison does not silently become unequal human source access.

## 5. Expert pre-AI capture

The independent human template preserves at least:

1. decision focus;
2. salient facts;
3. decision-changing missing information;
4. currently acceptable actions;
5. conditional actions;
6. not-indicated/prohibited/unsafe actions;
7. ASK / DEFER / REFER / ESCALATE / NO_CHANGE;
8. monitoring needs.

Once frozen:

\[
\boxed{
J^{preAI}\ \text{is immutable}
}
\]

## 6. Agent breadth

The Agent is asked only to find potentially decision-relevant items that may have been missed:

\`\`\`text
overlooked evidence
subject modifiers
critical missing information
conflicting evidence
applicability conditions
alternative acceptable actions
safety concerns
monitoring dependencies
\`\`\`

Each candidate requires source/provenance.

Forbidden:

\`\`\`text
AgentAnswer = FinalReference
AgentAnswer = FinalSafety
AgentAnswer = FinalAdjudication
\`\`\`

## 7. Anti-circular meta-audit

After workflow outputs exist:

\[
UnionCandidateSet
\]

is constructed, workflow labels are removed, and each item is independently qualified for:

\`\`\`text
support
decision relevance
criticality
safety criticality
decision-changing status
\`\`\`

Neither R0 nor R2 defines its own scoring truth.

## 8. Measurement

The pilot is prepared to measure:

- Critical Decision-Relevant Recall;
- Decision-Relevant Precision;
- Critical Omission;
- Safety-Critical Omission;
- human burden;
- anchoring;
- reference-set quality;
- reference stability.

With one operational fixture, P0 cannot estimate workflow superiority.

## 9. Current boundary

No expert judgment has yet been collected.

No Agent candidate set has yet been generated.

No QualifiedDecisionReference exists.

No evaluator is frozen.

Therefore:

\[
\boxed{
P0\ PASS
=
ReadyToBeginRealReferenceConstruction
}
\]

not:

\[
\cancel{
ReferenceQualified
}
\]

## 10. Next stage

\[
\boxed{
\textbf{
NDS-R1-P0.1｜
Expert Qualification,
Slot Binding,
Pre-AI Capture
\& Exposure Lock
}
}
\]
