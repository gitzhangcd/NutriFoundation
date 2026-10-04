# Paper C P0 Pre-Sampling Feasibility Erratum v0.1.1

## Status

**PROSPECTIVE PRE-SAMPLING NORMATIVE DELTA**
Date: 2026-10-04  
Applies to: Paper C Gold100 confirmatory source selection  
Parent: `paper_c/P0/Paper_C_P0_Scientific_Evidence_Production_Study_v0.1.md`

No Gold100 source selection had occurred when this erratum was issued.

## Trigger

P0.2.4 joint-feasibility audit identified a contradiction between two already-frozen rules:

1. Gold100 Stress20 contains exactly **2 incomplete/missing-source-text slots**.
2. The orthogonal challenge minimum required **incomplete source text >=5**.
3. P0.2.1 ELIG-02 states that failure of full-text sufficiency is allowed **only** for the predefined incomplete/missing-source-text stress stratum.

Therefore the three rules cannot all be satisfied simultaneously.

## Normative correction

The following single line is superseded for confirmatory execution:

```text
OLD:
incomplete source text >=5

NEW:
incomplete source text >=2
```

For Gold100 source selection, the operational rule is:

[
oxed{
	ext{incomplete_source_text minimum}=2
}
]

and those sources must occupy the two predefined incomplete/missing-source-text stress slots.

## Scientific rationale

Unlike numeric complexity, causal-language risk, conflict, version complexity, recommendation exceptions, or StudyIdentity dependency, incomplete source text is not safely orthogonal to Core80 under the exact-text contract.

A Core source requires an exact worker-visible source text package. P0.2.1 permits failure of full-text sufficiency only inside the incomplete-source stress stratum. Therefore requiring five incomplete sources while reserving only two legal incomplete-source slots is structurally inconsistent.

Reducing the orthogonal minimum to two removes the contradiction without:

- changing Gold100 N=100;
- changing Core80 + Stress20;
- changing any other challenge minimum;
- changing any family quota;
- changing the 80/20 domain split;
- changing AB0–AB6;
- changing K01–K14;
- changing the seed;
- using any AB/model performance.

## Non-regression

All other Paper C P0 and E0.4.3 contracts remain unchanged.

This erratum does not reclassify any prior Batch001/A2.8 result and does not alter any observed confirmatory outcome because no Gold100 sampling has yet occurred.

## Authority order for P0.2.4

For the single field `orthogonal_minimums_for_final_Gold100.incomplete_source_text`, this erratum supersedes the value in Paper C P0 v0.1 and P0.2.1 challenge registry v1.0.

All other fields continue to derive from their original frozen authorities.
