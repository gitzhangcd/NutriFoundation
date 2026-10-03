# Gold100 Independent Scientific Evidence Annotation Manual v1.0

## 1. Purpose

This manual governs Gold Annotator A, Gold Annotator B, and the Gold Adjudicator for Paper C Gold100.

The task is not to answer a patient question and not to judge an AB workflow. The task is to construct a source-grounded scientific reference that can later score AB0–AB6 independently.

\[
\boxed{\text{Read Source} \rightarrow \text{Represent Scientific Evidence} \rightarrow \text{Enumerate Critical Opportunities}}
\]

Gold creation must never follow the reverse path from model output to truth.

## 2. What annotators receive

Annotators receive only the frozen SourceArtifact package, evidence cutoff/version metadata, public bibliographic identity, the annotation manual, the annotation record form, and the R0 ontology/applicability definitions required to complete the record.

Annotators must not receive AB0–AB6 outputs, evaluator scores, verifier/auditor flags, per-source expected workflow failures, Batch001 case-specific error labels, or the other annotator's first-pass record.

## 3. First-pass procedure

1. Verify source identity, exact source-text binding, version state, and evidence cutoff.
2. Determine whether StudyIdentity/dependency resolution is applicable.
3. Determine whether one or more EvidenceUnits are extractable from the frozen source package.
4. For each EvidenceUnit, annotate population, intervention/exposure, comparator, outcome, effect direction, effect measure/value/unit when present, claim type, causal level, recommendation status when applicable, and supporting source spans.
5. Complete all nine source-level applicability-boundary dimensions.
6. Enumerate the applicable critical-error opportunities from the frozen eight opportunity types.
7. Use not_applicable or insufficient_source explicitly rather than inventing missing content.
8. Complete uncertainty, protocol-ambiguity, independence, and conflict-of-interest attestations.
9. Lock the first-pass record and its hash.
10. Do not silently revise the first pass after viewing A↔B differences.

## 4. EvidenceUnit boundary rule

Create separate EvidenceUnits when a scientifically material combination of population, intervention/exposure, comparator, outcome, time point, effect estimate, or recommendation differs.

Do not split only because wording differs. Do not merge if merging would erase a material subgroup, arm, outcome, direction, numeric result, or recommendation exception.

## 5. Claim type

Use only: descriptive, associative, causal, mechanistic, recommendation_support.

If a source phrase cannot be mapped unambiguously, flag protocol ambiguity. Do not invent a sixth claim type and do not force an ambiguous mapping.

## 6. Causality

Observational association must not be upgraded to causal because it seems biologically plausible. Use causal_supported only when source content and design warrant it under the R0 contract.

## 7. Numeric fidelity

Copy source-reported critical values with measure and units. Equivalent formatting may be normalized, but the underlying value and unit relationship must be preserved. Derived values cannot become critical Gold unless formula and tolerance were predeclared.

## 8. Provenance and source spans

Every critical scientific object must bind to source evidence. A valid span must occur in the exact annotation source text, support the scientific object, and preserve any material qualifier or exception whose omission would change meaning.

## 9. Applicability boundary

Paper C uses source-level evidence scope, not patient-level applicability. Complete population scope, intervention/exposure scope, comparator scope, outcome scope, setting/context, temporal scope, normative exceptions, exclusions/contraindications, and evidence limitations.

When the source cannot support a boundary, use insufficient_source. Do not supply a boundary from outside knowledge.

## 10. StudyIdentity and version

Resolve companion publications, secondary analyses, duplicate/overlapping reports, correction/republication/retraction/living-version chains where applicable. If identity is genuinely ambiguous, use ambiguous_escalate rather than guessing.

## 11. Critical-error opportunity map

This map defines the future CSER denominator and must be created before AB outputs are used for scoring.

Review all eight types: effect direction; critical numeric result; StudyIdentity/dependency; causal level; recommendation normativity/exception; provenance/source span; version/retraction/temporal status; and critical P/I/C/O scope.

For every type, record applicable, not_applicable, or insufficient_source. Mark an opportunity critical only when an error could materially alter scientific interpretation, source validity, or safety-relevant normative meaning.

Model performance must never determine whether an opportunity exists.

## 12. Insufficient source

Insufficient evidence is a legitimate Gold state. Do not fill missing information with memory, another paper, general domain knowledge, or inference unless the frozen source package explicitly includes that linked source as part of the StudyIdentity/version package.

## 13. Adjudication

After A and B first passes are locked, generate a field-level disagreement diff.

Adjudication is mandatory for every disagreement affecting scientific content, source spans/provenance, StudyIdentity/version, applicability, critical-opportunity applicability, criticality, or any future scoring field.

The adjudicator may accept A, accept B, synthesize a source-supported value, mark insufficient_source, or escalate unresolved protocol ambiguity.

AB outputs may never be used as tie-break evidence.

## 14. Protocol ambiguity versus scientific disagreement

If A and B differ because the source itself is ambiguous, adjudicate the best source-grounded representation. If they differ because the manual or ontology does not define a representation, flag protocol ambiguity and escalate to codebook governance. Do not invent a case-specific scoring rule.

## 15. Source-level freeze

A source may reach SOURCE_GOLD_PROVISIONAL only when A and B are complete and locked, all Gold-relevant disagreements are adjudicated, no critical disagreement remains unresolved, source identity/text/version/cutoff are bound, EvidenceUnits or a valid insufficiency state exist, critical source spans are bound, the opportunity map is complete, and independence/COI attestations are valid.

## 16. Corpus-level freeze

Gold100 may reach GOLD100_FROZEN only when all selected sources pass the source-level gate, prespecified agreement thresholds pass, Gold100 quotas and domain split remain valid, strict-blind wall audit passes, a hidden Gold package hash is generated, and the applicable critical-opportunity count is known.

If total applicable critical-error opportunities are below 600 before confirmatory unblinding, invoke only the prespecified expansion rule.

## 17. Role separation

Gold annotators and adjudicators must not serve as AB0 operators and must not develop or operate AB1–AB6 confirmatory workflow logic.

AB0 is not Gold. It is a human-only comparator that will itself be scored against hidden Gold.

Gold annotation/adjudication time is benchmark-construction cost and is excluded from AB0 and AB6 burden time.

## 18. Prohibited actions

Do not view or request AB outputs during Gold creation. Do not use model agreement as evidence of truth. Do not alter Gold to make a workflow look better or worse. Do not add or remove critical opportunities after seeing AB performance. Do not silently edit first-pass records after disagreement visibility. Do not use the old decision-oriented schemas/expert_reference.yaml as Paper C Gold100. Do not invent content absent from the frozen source package.

## 19. Calibration requirement

Before Gold100 annotation begins, annotators must pass P0.3 calibration on non-Gold100 sources.

Minimum corpus-level gates remain: Gwet AC1 ≥ 0.80 for critical categorical fields; weighted agreement ≥ 0.80 for ordinal fields; numeric agreement ≥ 95% under exact/predeclared tolerance; source-span token F1 ≥ 0.85.

Failure stops Gold100 freeze and triggers codebook repair plus recalibration.