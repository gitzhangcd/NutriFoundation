# E0.4.3 Runs

## Current state

```text
E0.4.3-R0     = PASS / FROZEN
E0.4.3-P0.1   = PASS / FROZEN
E0.4.3-P0.2.1 = PASS / FROZEN
E0.4.3-P0.2.2 = PASS / RAW REGISTRY FROZEN
E0.4.3-P0.2.3 = PASS / ELIGIBLE POOL FROZEN / SAMPLING AUTHORIZED
Primary program = Paper C confirmatory evidence production
Current execution gate = P0.2.4 Deterministic Gold100 Source Selection
```

## Upstream freeze

```text
E0.4.2-E3-A2.8-FROZEN
83a33bbdbb9a647c3aea96a67bf47ba5f246c05a
```

## P0.2.3 authority

```text
docs/E0.4.3-P0.2.3_Eligible_Pool_Qualification_Exact_Text_Version_StudyIdentity_Resolution_Exclusion_Adjudication_Pre_Sampling_Hash_Freeze_v1.0.md
runs/E0.4.3/P0.2.3/Gold100_Eligible_Pool_FROZEN_v0.1.json
runs/E0.4.3/P0.2.3/P0.2.3_Qualification_Report_v0.1.json
runs/E0.4.3/P0.2.3/Gold100_Exclusion_Registry_v0.1.json
runs/E0.4.3/P0.2.3/Exact_Text_Hash_Manifest_v0.1.json
runs/E0.4.3/P0.2.3/Eligible_Pool_SHA256_v0.1.txt
runs/E0.4.3/P0.2.3/Coverage_Repair_Lineage_v1.0.json
runs/E0.4.3/P0.2.3/P0.2.3_Freeze_Manifest_v1.0.json
```

## Frozen eligible pool

```text
raw source universe = 724
eligible sources    = 330
excluded sources    = 394
eligible pool SHA256 = ff33d849367c335e5b5cb8345b40a332b1417d0e8a4372eb462a0464a807565c
sampling_authorized = true
sampling_performed  = false
```

## Planned execution chain

```text
R0 Measurement-System Lock [PASS]
→ P0.1 Independent Gold governance [PASS]
→ P0.2.1 Gold100 source eligibility [PASS]
→ P0.2.2 real candidate SourceArtifacts [PASS]
→ P0.2.3 eligible-pool qualification + hash freeze [PASS: 330 eligible]
→ P0.2.4 deterministic Gold100 selection [NEXT]
→ P0.3 independent expert calibration
→ P0.4 Gold100 dual annotation + adjudication
→ P1 AB0–AB6 strict-blind confirmatory execution
→ P2 CSER / human-burden / kill-test analysis
```

Important:

```text
No Gold100 sampling occurred during P0.2.3.
P0.2.4 must use seed = 20260930.
Sampling must use the frozen 330-source eligible pool and its SHA256.
Core80 + Stress20, 80/20 domain split, family quotas, challenge minima, and StudyIdentity non-duplication remain frozen.
AB0 is a comparator, not Gold.
Gold annotation begins only after deterministic source selection and P0.3 calibration.
```