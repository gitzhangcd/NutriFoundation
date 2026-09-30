
# Paper C P0｜Execution Report

## Stage

Scientific Evidence Production Study, AB0–AB6 Baseline Freeze, 100-Source Gold Corpus, CSER/Human-Burden Endpoints & Publication-Level Kill Tests

Version: v0.1  
Status: PASS — protocol/contract freeze complete; Gold100 source selection not yet executed.

## What was frozen

### 1. AB0–AB6 baseline namespace

The canonical workflow comparison is now fixed:

- AB0 Human-only reference workflow
- AB1 One-pass LLM
- AB2 Structured-output LLM
- AB3 Self-consistency
- AB4 Extractor + independent verifier
- AB5 Extractor + verifier + adversarial auditor
- AB6 Risk-based HITL

Fairness rules freeze the same model family, source universe, task identity and hidden-reference isolation across AB1–AB6 where technically possible.

### 2. Confirmatory Gold100 corpus architecture

Batch001 remains development-only and is excluded from confirmatory claims.

Gold100 is a new 100-source corpus:

- Core80
- Stress20
- 80 nutrition/metabolic/cardiometabolic
- 20 external biomedical/public-health

Exact 100 source slots are frozen before source selection.

### 3. Primary endpoint

Critical Scientific Error Rate:

CSER = CriticalScientificErrorEvents / ApplicableCriticalErrorOpportunities

Critical opportunities include:

- effect direction;
- critical numeric result;
- StudyIdentity/dependency;
- causal level;
- recommendation normativity/exception;
- provenance/source span;
- version/retraction/temporal status;
- critical P/I/C/O scope.

### 4. Human-burden endpoint

ExpertMinutesPerSource and Human Burden Reduction are frozen.

HBR = 1 - ExpertTime_workflow / ExpertTime_AB0

### 5. AB6 central publication gate

AB6 must satisfy all:

- CSER non-inferiority versus AB0;
- one-sided 95% CI below absolute margin 0.02;
- AB6 CSER point estimate <=0.05;
- HBR >=30%;
- paired time-reduction CI excludes zero.

### 6. Publication kill tests

Fourteen kill tests were frozen, including:

- Gold unreliability;
- verifier no incremental value;
- auditor redundancy;
- HITL burden failure;
- HITL safety failure;
- unsafe silent failure;
- held-out source-type collapse;
- external-domain collapse;
- no provenance benefit;
- temporal/version failure;
- complexity not justified;
- strict-blindness violation;
- unfair baseline;
- post-hoc benchmark adaptation.

## Literature-positioning result

Recent literature already demonstrates that LLM-assisted data extraction can be useful and can reduce reviewer time.

Therefore Paper C is explicitly not framed as:

“Can an LLM extract data from scientific papers?”

The retained methodological gap is:

“Which evidence-production architecture minimizes critical scientific error while reducing expert burden?”

This shifts the scientific object from model performance to workflow architecture.

## Development/confirmation separation

E0.1–E0.4 and Batch001 are retained as development evidence.

They may be used for:

- engineering calibration;
- verifier debugging;
- ontology repair;
- code testing;
- workflow feasibility.

They may not be used as the confirmatory Gold100 evaluation set.

Gold100 must be run in strict_blind_fresh_context or an independently provisioned provider context.

## Gold100 status

Current status:

- source slots: 100/100 frozen;
- source identities selected: 0/100;
- independent annotation: not started;
- adjudication: not started;
- Gold freeze: not started;
- confirmatory baseline runs: prohibited until Gold freeze.

This is intentional. P0 freezes the experiment before selecting/seeing confirmatory sources.

## Remote validation

GitHub Actions workflow:

- workflow: NutriFoundation Engine CI
- initial P0 validation run: 36697194585
- result: success
- pytest: 50 passed
- existing executable invariants: 30 passed
- Batch001 ScientificClaim Gold gate: PASS
- frozen Gold claims remain 0
- Gold-ready candidates remain 3

A CI path rule was added so future modifications under paper_c/** automatically rerun contract regression tests.

## Non-regression tests added

The P0 CI contract checks:

- exact AB0–AB6 baseline namespace;
- exact Gold100 source count = 100;
- Core80/Stress20 split;
- 80/20 domain split;
- Batch001 confirmatory exclusion;
- frozen random seed;
- primary endpoint = CSER;
- AB6 non-inferiority margin = 0.02;
- absolute CSER ceiling = 0.05;
- HBR threshold = 0.30;
- 10,000 source-cluster bootstrap resamples;
- minimum publication kill-test coverage;
- strict hidden-Gold isolation;
- prohibition on post-hoc prompt/Gold adaptation.

## Scientific interpretation

P0 does not establish that AB6 is superior.

P0 establishes a falsifiable study in which AB4, AB5 or AB6 may fail.

NoIncrementalBenefit -> ClaimReduction

is preserved as a hard scientific rule.

## Exit decision

Paper C P0 = PASS

Reason:

- scientific question frozen;
- literature gap defined;
- baselines frozen;
- confirmatory corpus architecture frozen;
- endpoints/statistics frozen;
- Gold reliability gates frozen;
- publication kill tests frozen;
- strict-blindness requirement frozen;
- executable non-regression tests passed.

## Next stage

Paper C P0.1｜Gold100 Eligible-Pool Construction, Exact Source Selection, Dual-Annotation Pack & Pre-Annotation Blindness Freeze

P0.1 may populate source slots but must not alter P0 quotas, endpoints, baseline definitions or kill-test thresholds.
