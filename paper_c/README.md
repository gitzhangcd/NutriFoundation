# Paper C｜Scientific Evidence Production

## Scientific purpose

Paper C evaluates evidence-production **workflow architecture**, not model brand.

Primary question:

Which workflow minimizes critical scientific error while reducing expert burden?

## Frozen P0 assets

- `P0/Paper_C_P0_Scientific_Evidence_Production_Study_v0.1.md`
- `P0/Literature_Positioning_v0.1.md`
- `P0/AB0_AB6_Baseline_Contract_v0.1.yaml`
- `P0/Gold100_Corpus_Contract_v0.1.yaml`
- `P0/Gold100_Source_Slot_Manifest_v0.1.json`
- `P0/Endpoint_Statistical_Contract_v0.1.yaml`
- `P0/Publication_Kill_Test_Registry_v0.1.yaml`

## Development vs confirmation

Batch001 / E0.1–E0.4 are development evidence and are excluded from confirmatory Gold100 evaluation.

Gold100 is a new 100-source corpus with Core80 + Stress20 and an 80/20 in-domain/external-domain split.

## Baselines

```text
AB0 Human-only
AB1 One-pass LLM
AB2 Structured-output LLM
AB3 Self-consistency
AB4 Extractor + independent verifier
AB5 Extractor + verifier + adversarial auditor
AB6 Risk-based HITL
```

## Primary endpoint

[
CSER=
rac{CriticalScientificErrorEvents}
{ApplicableCriticalErrorOpportunities}
]

## Central publication gate

AB6 must simultaneously:

- satisfy CSER non-inferiority vs AB0;
- remain below the absolute CSER ceiling;
- reduce human burden by at least the frozen threshold.

## Next stage

[
oxed{
Paper C P0.1｜
Gold100 Eligible	ext{-}Pool Construction,
Exact Source Selection,
Dual	ext{-}Annotation Pack
& Pre	ext{-}Annotation Blindness Freeze
}
]
