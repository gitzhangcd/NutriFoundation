
# Paper C P0｜Scientific Evidence Production Study

## AB0–AB6 Baseline Freeze, 100-Source Gold Corpus, CSER/Human-Burden Endpoints & Publication-Level Kill Tests

Version: v0.1  
Status: P0 SCIENTIFIC + EXECUTION CONTRACT FROZEN / GOLD100 SOURCE SELECTION PENDING  
Repository: gitzhangcd/NutriFoundation

---

## 0. Scientific identity

Paper C studies:

How should trustworthy scientific evidence-production systems be designed?

The comparison unit is workflow architecture, not model brand.

Primary question:

WhichWorkflow -> LowestCriticalScientificError

subject to:

HumanBurden, Cost, Time, Traceability.

This implements the Automation Validation Suite defined in AI Nutri Master Specification v2.0.

---

## 1. Relationship to E0.1–E0.4

E0.1–E0.4 are development and engineering evidence.

They established provider-neutral model I/O, EvidenceUnit extraction, independent verification, F0 freeze, safe defer, blind software isolation, provenance, immutability and an error taxonomy.

E0.4 also showed unchanged semantic outputs moving from 60% to 75% to 95% verifier/F0 yield after verifier defects were repaired.

That observation motivates Paper C but is not confirmatory evidence.

Therefore:

DevelopmentSet != Gold100ConfirmatorySet

All 20 Batch001 sources are excluded from Gold100 confirmatory evaluation.

---

## 2. Hypotheses

### H1 Independent verification

CSER_AB4 < CSER_AB2.

### H2 Adversarial auditing

CSER_AB5 < CSER_AB4 only if the auditor captures additional critical failures not already detected by verification.

### H3 Risk-based HITL

AB6 should retain scientific safety relative to AB0 while reducing expert workload.

Safety:
CSER_AB6 - CSER_AB0 < Delta_NI

Burden:
HBR_AB6 >= 0.30

where:

HBR = 1 - ExpertTime_AB6 / ExpertTime_AB0

### H4 Transportability

Architecture gains should not collapse on held-out source types, stress cases or external biomedical/public-health sources.

### H5 Traceability

Explicit source spans, provenance, StudyIdentity and version tracking should improve scientific traceability over flat extraction.

---

## 3. Frozen baselines

AB0 Human-only reference workflow:
human extractor -> independent human verifier -> disagreement resolution.

AB1 One-pass LLM:
single source-conditioned generation with minimal transport constraints.

AB2 Structured-output LLM:
one-pass extraction into exact EvidenceUnit schema with requested source spans.

AB3 Self-consistency:
three independent AB2-style runs -> deterministic consensus -> unresolved disagreement becomes defer.

AB4 Extractor + independent verifier:
AB2 plus source-hash, numeric, anchor, applicability, causal, guideline, StudyIdentity and version checks where applicable.

AB5 Extractor + verifier + adversarial auditor:
AB4 plus an independent semantic auditor focused on omissions, scope corruption, causal upgrade, numeric mismatch, recommendation exception loss, provenance/version failure and StudyIdentity/dependency failure. One bounded repair pass is allowed.

AB6 Risk-based HITL:
AB5 plus deterministic human-escalation rules. Human review is limited to prespecified risk cases.

Exact contract:
paper_c/P0/AB0_AB6_Baseline_Contract_v0.1.yaml

---

## 4. Fair-comparison contract

AB1–AB6 MUST hold fixed where technically possible:
- foundation model/version;
- provider;
- source universe;
- exact source text;
- evidence cutoff;
- task identity;
- schema version;
- decoding policy.

Architecture-specific additional calls are allowed but their compute, token, latency and throughput costs MUST be reported.

A weaker model or deliberately weak retrieval system may not be used as a straw-man comparator.

---

## 5. Gold100 corpus

Gold100 is a new confirmatory corpus:

N = 100 SourceArtifacts.

Gold100 = Core80 + Stress20.

Core80:
- 28 primary interventional;
- 18 primary observational;
- 18 evidence syntheses;
- 12 guidelines/consensus;
- 4 companion/secondary.

Stress20:
- 6 correction/republication/retraction/living-version;
- 4 StudyIdentity/companion-dependency;
- 4 conflicting-evidence;
- 2 recommendation-exception/normative-boundary;
- 2 temporal-cutoff-sensitive;
- 2 incomplete/missing-source-text.

Domain split:
- 80 nutrition/metabolic/cardiometabolic;
- 20 held-out external biomedical/public-health.

Orthogonal minimum challenge tags:
- numeric complexity >=20;
- causal-language risk >=15;
- StudyIdentity/dependency >=15;
- correction/retraction/living-version >=10;
- conflict >=15;
- recommendation exception >=10;
- temporal-cutoff sensitive >=10;
- incomplete source text >=5.

Eligible pool is frozen and hashed before sampling.

Core sampling is stratified deterministic random.
Stress sampling is rule-based eligibility followed by deterministic random sampling within challenge strata.

Frozen seed: 20260930.

Exact slots:
paper_c/P0/Gold100_Source_Slot_Manifest_v0.1.json

---

## 6. Gold annotation

Gold means best available adjudicated reference, not infallible scientific truth.

Each source receives:
- SourceArtifact;
- StudyIdentity where applicable;
- one or more EvidenceUnits;
- source spans;
- provenance;
- version status;
- critical-error opportunities.

Design:

Annotator A + Annotator B -> disagreement -> adjudicator -> Gold.

Both annotators are blind to AB outputs.

Minimum gates before Gold freeze:
- critical categorical fields: Gwet AC1 >=0.80;
- ordinal fields: weighted agreement >=0.80;
- numeric values: >=95% exact/predeclared-tolerance agreement;
- source spans: token F1 >=0.85.

If a gate fails:
RepairCodebook -> Recalibrate before confirmatory execution.

Gold cannot be edited post hoc to improve model performance.

---

## 7. Primary endpoint

Primary endpoint:

CSER = CriticalScientificErrorEvents / ApplicableCriticalErrorOpportunities.

The source is the clustering unit.

Critical opportunities:
1. effect direction;
2. critical numeric result;
3. StudyIdentity/dependency;
4. causal level;
5. recommendation normativity/exception;
6. provenance/source span;
7. version/retraction/temporal status;
8. critical P/I/C/O scope.

Critical errors include:
- effect reversal;
- materially wrong numeric result;
- wrong StudyIdentity causing double counting;
- association -> causation upgrade;
- false formal recommendation;
- deleted material recommendation exception;
- unsupported scientific assertion;
- invalid source/version use;
- future-information leakage;
- material population/intervention/outcome scope corruption.

High average field accuracy cannot neutralize a critical error.

---

## 8. Human-burden endpoint

ExpertMinutesPerSource is measured from active application events.

HBR = 1 - ExpertTime_Workflow / ExpertTime_AB0.

Idle periods >5 minutes are excluded.

Gold adjudication time is reported separately and is not AB6 production burden.

---

## 9. AB6 publication gate

The central AB6 claim requires all of the following.

Safety non-inferiority:
Delta_CSER = CSER_AB6 - CSER_AB0.

Frozen margin:
Delta_NI = 0.02 absolute.

Decision:
upper one-sided 95% CI < 0.02.

Absolute safety ceiling:
CSER_AB6 point estimate <=0.05.

Human-burden superiority:
HBR_AB6 >=30% and paired 95% CI for time reduction excludes zero.

Any failure reduces the publication claim.

---

## 10. Statistical analysis

All AB comparisons are paired by source.

Primary uncertainty:
10,000-resample source-cluster bootstrap.

Secondary:
- exact McNemar for paired source-level critical failure where applicable;
- paired bootstrap and Wilcoxon sensitivity for expert minutes;
- Holm adjustment for secondary pairwise claims.

Always report absolute and relative effects, confidence intervals, denominators, critical-opportunity counts and source-type strata.

Gold100 may expand only before confirmatory outputs are unblinded if:
- fewer than 600 applicable critical-error opportunities exist; or
- a frozen stratum cannot be filled.

After unblinding, N, thresholds, Gold, prompts and code cannot be changed to improve the result.

---

## 11. Publication-level kill tests

K01 Gold unreliability:
failure of critical-field agreement gates stops confirmatory runs.

K02 Verifier no incremental value:
if AB4 fails to meaningfully reduce CSER over AB2 and catches no unique critical errors, verifier incremental claims are removed.

K03 Auditor redundancy:
if AB5 adds negligible CSER improvement and negligible unique error capture, the auditor-is-required claim is removed.

K04/K05 HITL burden or safety failure:
failure of either gate kills the risk-based-HITL advantage claim.

K06 Unsafe silent failure:
any critical unsupported/missing object silently frozen without escalation hard-kills the current escalation policy.

K07/K08 Generalization collapse:
held-out source/domain failure restricts the claim.

K09 No provenance benefit:
lack of source-span improvement reduces provenance incremental-value claims.

K10 Temporal/version failure:
failure on correction/retraction/living-version cases removes living-evidence claims.

K11 Complexity not justified:
trivial marginal gain relative to cost/latency favors the minimum sufficient architecture.

K12 Strict-blindness violation:
any Gold100 leakage invalidates confirmatory model-accuracy claims.

K13/K14 Unfair baseline or post-hoc adaptation:
either invalidates confirmatory architecture-superiority claims.

Exact kill rules:
paper_c/P0/Publication_Kill_Test_Registry_v0.1.yaml

---

## 12. Strict-blind execution

Gold100 MUST be evaluated in strict_blind_fresh_context or an independently provisioned provider context.

The E0.4 current-context run is development evidence only.

Hidden Gold may not appear in prompt history, TaskBundle, worker context, repair prompt, verifier input or escalation routing.

Hidden Gold enters only after final outputs are frozen.

---

## 13. Publication claim ladder

C0: typed evidence production is representable.
C1: source-linked EvidenceUnits can be extracted reliably.
C2: independent verification reduces critical scientific error.
C3: adversarial auditing adds unique error capture.
C4: risk-based HITL maintains safety with lower expert burden.
C5: effects transport across held-out source types/domains.

Each level has its own endpoint and kill test.

---

## 14. Intended contribution

The paper is not:

We used an LLM to build a nutrition database.

The intended contribution is:

> We empirically decomposed scientific evidence production into extraction, verification, auditing and risk-based human review, and identified the minimum workflow architecture that controls critical scientific errors while reducing expert burden.

Nutrition is the primary development domain.
The external 20-source block tests broader transportability.

---

## 15. Next stage

Paper C P0.1｜Gold100 Eligible-Pool Construction, Exact Source Selection, Dual-Annotation Pack & Pre-Annotation Blindness Freeze.

P0.1 populates the 100 frozen slots without modifying P0 quotas, endpoints or kill criteria.
