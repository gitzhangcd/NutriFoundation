# Batch001 P0 Human Adjudication Pack v0.1

## Stage

P1.9-E7 — P0 Claim-Critical F1 Full-Text Upgrade, Correction / Evidence-Overlap Resolution, Human Adjudication Pack & First ScientificClaim-Gold Freeze

## Purpose

This pack is the mandatory human/expert gate before any ScientificClaim_GOLD freeze.

Agent output is advisory and lineage-preserving. The adjudicator must independently approve, revise, reject, or defer each claim.

---

## Claim 1 — SC-B001-C01

### Proposed Gold wording

> In adults with impaired glucose tolerance or similarly high-risk dysglycemia represented by prevention trials, intensive multicomponent lifestyle interventions targeting weight reduction, dietary change and physical activity can reduce or delay incident type 2 diabetes compared with usual/control care; effect magnitude varies by population and attenuates over long-term follow-up.

### Reliability state

robust

### Core evidence

- Finnish DPS primary randomized trial (PMID 11333990): 4-year cumulative diabetes incidence 11% vs 23%; 58% risk reduction.
- DPP primary randomized trial (PMID 11832527): 58% reduction vs placebo during the original trial.
- DPPOS 15-year full-text follow-up (PMID 26377054 / PMCID PMC4623946): lifestyle HR 0.73; effect persisted but attenuated.
- Finnish DPS long-term follow-up (PMID 23093136): total-follow-up HR 0.614; post-intervention HR 0.672.
- Independent replication: IDPP-1 (PMID 16391903), Japanese IGT trial (PMID 15649575), Japanese IFG trial (PMID 21824948) with subgroup-dependent strength.

### F1 / lineage assessment

- DPPOS full text retrieved and checked.
- Finnish primary publisher/PubMed evidence checked.
- Follow-up evidence-family de-duplication performed: DPP/DPPOS count as one family; DPS/follow-ups count as one family.
- India/Japan trials are independent evidence families.

### Critical boundaries

- Multicomponent intervention; do not attribute effect to diet alone.
- Applies to high-risk dysglycemia/IGT-like populations, not low-risk general populations.
- Long-term effect attenuates; prevention/delay is not permanent prevention for all participants.

### Adjudicator decision

- [ ] APPROVE_GOLD_AS_WRITTEN
- [ ] APPROVE_GOLD_WITH_REVISION
- [ ] REJECT
- [ ] DEFER

Reviewer name/ID: ____________________
Role/expertise: ____________________
Independent from Agent extraction: [ ] Yes [ ] No
Conflict of interest declared: ____________________
Approved wording/revision: ____________________
Date: ____________________

---

## Claim 2 — SC-B001-C05

### Proposed Gold wording

> Improvement in body weight, HbA1c, fitness, or cardiovascular risk factors is not, by itself, sufficient evidence that an intervention reduces hard cardiovascular events; hard-outcome benefit requires outcome-specific evidence.

### Reliability state

convergent

### Core evidence

- Look AHEAD full text (PMID 23796131 / PMCID PMC3791615): significant improvements in weight, fitness and several risk factors, but primary cardiovascular endpoint HR 0.95 (95% CI 0.83–1.09), p=0.505.
- Later reviews preserve the distinction between intermediate/risk-factor improvement and cardiovascular outcome evidence.

### Correction resolution

NEJM correction DOI 10.1056/NEJMx140022 corrects a Table 2 secondary-outcome label to include hospitalization for angina. It does not alter the primary endpoint, primary HR, or overall cardiovascular conclusion.

### Critical boundaries

- This is an epistemic inference guard.
- It does NOT mean lifestyle or weight loss can never improve hard cardiovascular outcomes.
- Different interventions/populations can have hard-outcome benefits and must be evaluated separately.

### Adjudicator decision

- [ ] APPROVE_GOLD_AS_WRITTEN
- [ ] APPROVE_GOLD_WITH_REVISION
- [ ] REJECT
- [ ] DEFER

Reviewer name/ID: ____________________
Role/expertise: ____________________
Independent from Agent extraction: [ ] Yes [ ] No
Conflict of interest declared: ____________________
Approved wording/revision: ____________________
Date: ____________________

---

## Claim 3 — SC-B001-C02

### Proposed Gold wording

> Across adults with overweight/obesity or type 2 diabetes, current evidence does not support a single diet or macronutrient distribution as universally superior for sustained weight loss across populations and time horizons; modest context- and duration-specific advantages can occur.

### Reliability state

convergent

### F1 evidence

- POUNDS LOST full text: no significant 2-year weight-loss differences by protein, fat or carbohydrate target; adherence waned.
- 2015 meta-analysis full text: low-fat not superior to similarly intensive alternatives; low-carb showed a modest long-term advantage over low-fat.
- 2022 meta-analysis full text: low-carb modestly favored weight/TG/HDL at 6–23 months; no meaningful advantage after 24 months.
- T2D umbrella review full text: no generally superior macronutrient profile; TDR/VLED effects depend heavily on energy restriction/program intensity.
- 2024 network meta-analysis: low-carb ranked first within its 7-RCT/9-trial network; authors acknowledge effect modification/context.

### Dependency resolution

The 2022 meta-analysis explicitly includes:

- Sacks / POUNDS LOST
- Gardner / DIETFITS
- Gardner / A TO Z low-carb vs low-fat subset
- Shai / DIRECT-like comparison

These primary trials and the synthesis must not be counted as independent replications.

### Critical boundary

The claim is 'no universal winner', NOT 'all diets are equivalent'.

### Adjudicator decision

- [ ] APPROVE_GOLD_AS_WRITTEN
- [ ] APPROVE_GOLD_WITH_REVISION
- [ ] REJECT
- [ ] DEFER

Reviewer name/ID: ____________________
Role/expertise: ____________________
Independent from Agent extraction: [ ] Yes [ ] No
Conflict of interest declared: ____________________
Approved wording/revision: ____________________
Date: ____________________

---

## Gold Freeze Rule

A claim enters ScientificClaim_GOLD only when:

1. the adjudicator selects APPROVE_GOLD_AS_WRITTEN or APPROVE_GOLD_WITH_REVISION;
2. reviewer identity/role/date are recorded;
3. the approved wording is explicit;
4. the reviewer confirms independence from Agent extraction;
5. any declared conflict is preserved in provenance;
6. the Gold object references the F1 record, reception record, reliability sidecar and adjudication record.

Unsigned or Agent-only approval is not valid Gold.