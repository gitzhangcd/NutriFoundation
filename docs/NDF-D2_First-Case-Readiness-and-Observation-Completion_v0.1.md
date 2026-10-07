# NDF-D2｜Case-Specific Readiness, Observation Completion, Source Fidelity & Projection Qualification

**Status:** \`PASS_D2_INPUT_READY_D1_REBIND_REQUIRED_BEFORE_R1\`  
**Date:** 2026-10-07  
**Case:** \`D2-NHANES-L-0001:r2\`

## 1. D2 result

The first NHANES-grounded case now satisfies all six D2 gates and reaches:

\[
\boxed{INPUT\_READY}
\]

This does **not** mean a reference or evaluator exists.

## 2. Observation completion

Component-level reconstruction restored source-observed BP information omitted by the original merged carrier:

- SBP: 135 / 131 / 132 mmHg;
- DBP: 98 / 96 / 94 mmHg;
- pulse: 82 / 79 / 82 bpm.

Derived values are separately represented:

\[
\overline{SBP}=132.6667,\qquad
\overline{DBP}=96.0,\qquad
\overline{Pulse}=81.0
\]

Day-1 dietary observations were also reconstructed from two independent public XPT-derived carriers and mapped to CDC/NCHS official DR1TOT_L semantics.

## 3. Missingness repair

The former:

\`day1_total_energy = UNKNOWN because source component not ingested\`

is no longer used as the scientific missingness construct.

The base diet observations exist. The current R1 stress case applies an explicit MSK overlay so those values are hidden in R1-facing views.

Therefore:

\[
Masked \neq SourceMissing
\]

and the underlying diet values cannot be used to justify the ex-ante reference action.

## 4. Source fidelity

CDC/NCHS documentation remains the semantic authority for DEMO_L, BMX_L, BPXO_L and DR1TOT_L.

The current runtime additionally uses immutable public carriers and cross-carrier concordance for subject-level values.

Direct CDC-XPT byte equality is **not claimed** because the current runtime did not decode the official binary files directly.

This is qualified for the R1 reference-science pilot, but first-party byte verification should be revalidated before a locked publication benchmark if required by the final protocol.

## 5. Projection qualification

Six role projections are frozen:

- SYSTEM_VIEW;
- EXPERT_PRE_AI_VIEW;
- AGENT_EXPANSION_VIEW;
- EXPERT_POST_AI_VIEW;
- META_ADJUDICATION_VIEW;
- EVALUATOR_VIEW.

Diet values remain hidden from R1-facing views. DBP is now visible because it is a source-observed field and there is no scientific rationale to preserve the prior accidental omission.

## 6. D2 gates

\`\`\`text
D2-G1 Observation fidelity      PASS
D2-G2 Case provenance          PASS_WITH_SOURCE_CAVEAT
D2-G3 Constructed transparency PASS
D2-G4 Boundary integrity       PASS
D2-G5 Dependency integrity     PASS
D2-G6 No fake trajectory       PASS
\`\`\`

## 7. Cross-branch consequence

Observation completion materially changes the case-bound information state because DBP is now restored.

Therefore the existing \`SRS-D1-A3R-001:r3\`, constructed from a systolic-only view, cannot be silently reused.

\[
\boxed{
D2\ PASS
\land
D1\ RebindRequired
}
\]

The required minimal patch is:

\[
\boxed{
\textbf{
NDF-D1-A3R.3｜
D2 Observation Completion Rebind,
BP Applicability Refresh
\& Non-Regression Freeze
}
}
\]

Only after that rebind may this case proceed to NDS-R1.
