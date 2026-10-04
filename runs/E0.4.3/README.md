# E0.4.3 Runs

## Current state

```text
E0.4.3-R0     = PASS / FROZEN
E0.4.3-P0.1   = PASS / FROZEN
E0.4.3-P0.2.1 = PASS / FROZEN
E0.4.3-P0.2.2 = PASS / RAW REGISTRY FROZEN
E0.4.3-P0.2.3 = PASS / ELIGIBLE POOL FROZEN / SAMPLING AUTHORIZED
E0.4.3-P0.2.4 = PASS / GOLD100 SOURCE SET FROZEN
Primary program = Paper C confirmatory evidence production
Current execution gate = P0.3-H0 Human Workbench Smoke Test
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
sampling_performed_at_P0.2.3 = false
sampling_performed_at_P0.2.4 = true
```

## Planned execution chain

```text
R0 Measurement-System Lock [PASS]
→ P0.1 Independent Gold governance [PASS]
→ P0.2.1 Gold100 source eligibility [PASS]
→ P0.2.2 real candidate SourceArtifacts [PASS]
→ P0.2.3 eligible-pool qualification + hash freeze [PASS: 330 eligible]
→ P0.2.4 deterministic Gold100 selection [PASS: 100 sources frozen]
→ P0.3 independent expert calibration [IN PROGRESS: machine preparation frozen; human calibration not started]
→ P0.4 Gold100 dual annotation + adjudication [BLOCKED UNTIL P0.3 PASS]
→ P1 AB0–AB6 strict-blind confirmatory execution
→ P2 CSER / human-burden / kill-test analysis
```

Important:

```text
No Gold100 sampling occurred during P0.2.3.
P0.2.4 subsequently used the frozen seed = 20260930.
P0.2.4 preserved the frozen 330-source parent pool and its SHA256, then applied the explicit pre-sampling feasibility amendment to form the 333-source sampling universe.
Core80 + Stress20, 80/20 domain split, family quotas, Stress20 quotas, all non-conflicting challenge minima, and StudyIdentity non-duplication remain frozen; the single contradictory incomplete-source minimum is superseded prospectively by the P0.2.4 erratum.
AB0 is a comparator, not Gold.
Gold annotation begins only after deterministic source selection and P0.3 calibration.
```
## P0.2.4 authority

```text
docs/E0.4.3-P0.2.4_Deterministic_Gold100_Source_Selection_Slot_Assignment_Sampling_Audit_Source_Set_Freeze_v1.0.md
paper_c/P0.2.4/Paper_C_P0_PreSampling_Feasibility_Erratum_v0.1.1.md
runs/E0.4.3/P0.2.4/Gold100_Source_Set_FROZEN_v1.0.json
runs/E0.4.3/P0.2.4/Gold100_Source_Set_SHA256_v1.0.txt
runs/E0.4.3/P0.2.4/Gold100_Source_Slot_Manifest_FILLED_v1.0.json
runs/E0.4.3/P0.2.4/Gold100_Sampling_Audit_v1.0.json
runs/E0.4.3/P0.2.4/P0.2.4_Freeze_Manifest_v1.0.json
```

## Frozen Gold100 source set

```text
Gold100 sources = 100
Core = 80
Stress = 20
Nutrition/metabolic/cardiometabolic = 80
External biomedical/public-health = 20
Frozen full text = 98
Predefined incomplete-source stress = 2
Gold100 source-set SHA256 = fdb1189647fe4022411d3ebfd6591da2398135aed398c88ca6f85236678420ad
Expert Gold annotation = NOT STARTED
```

Pre-sampling feasibility audit identified and prospectively corrected one protocol contradiction: the incomplete-source challenge minimum was changed from >=5 to >=2 because ELIG-02 permits incomplete text only in the two dedicated incomplete-source stress slots. No Gold100 sampling or AB/model outcome existed before this correction.
## P0.3 current authority

```text
P0.3 overall = NOT YET PASS
Calibration24 = FROZEN
Calibration24 SHA256 = ec793d52a130b98aaefebdb40b85356ed88543aea2b8eff63a7fcd9f8212af33
Machine workbench-contract conformance = PASS
Runnable P0.3 workbench = PRESENT / P03-WORKBENCH-REF-v0.1.0
Automated implementation acceptance = PASS
Human smoke test = READY / NOT RUN
Expert A/B = UNASSIGNED
Round A = NOT STARTED
Round B = NOT STARTED
Reliability metrics = NOT AVAILABLE
Gold100 expert annotation = PROHIBITED
```

Authority:

```text
docs/E0.4.3-P0.3_Independent_Expert_Calibration_Annotation_Workbench_Validation_Reliability_Gate_Pre_Gold100_Annotation_Lock_v1.0.md
runs/E0.4.3/P0.3/P0.3_Execution_Manifest_v1.0.json
paper_c/P0.3/Annotation_Workbench_Implementation_Acceptance_Contract_v1.0.json
paper_c/P0.3/Annotation_Workbench_Implementation_Handoff_v1.0.md
paper_c/P0.3/Annotation_Workbench_Runbook_v1.0.md
runs/E0.4.3/P0.3/P0.3_Workbench_Implementation_Acceptance_Result_v1.0.json
```

## P0.3 authority

```text
docs/E0.4.3-P0.3_Independent_Expert_Calibration_Annotation_Workbench_Validation_Reliability_Gate_Pre_Gold100_Annotation_Lock_v1.0.md
paper_c/P0.3/P0.3_Calibration_Protocol_v1.0.json
paper_c/P0.3/Annotation_Workbench_Contract_v1.0.json
paper_c/P0.3/Reliability_Gate_Contract_v1.0.json
paper_c/P0.3/Reliability_Computation_Spec_v1.0.md
paper_c/P0.3/Expert_Calibration_Manual_v1.0.md
runs/E0.4.3/P0.3/Calibration24_Source_Set_FROZEN_v1.0.json
runs/E0.4.3/P0.3/Calibration24_PreHuman_Selection_Reconciliation_v1.0.json
runs/E0.4.3/P0.3/P0.3_Execution_Manifest_v1.0.json
```

## P0.3 current gate

```text
Calibration24 = 24 non-Gold100 sources
Calibration24 SHA256 = ec793d52a130b98aaefebdb40b85356ed88543aea2b8eff63a7fcd9f8212af33
Round A = 12 guided-training sources
Round B = 12 blinded-reliability sources
Gold100 SourceArtifact overlap = 0
Gold100 StudyIdentity overlap = 0
Machine conformance = PASS
Human workbench smoke test = READY / NOT RUN
Experts A/B = UNASSIGNED
Round A = NOT STARTED
Round B = NOT STARTED
Reliability metrics = NOT AVAILABLE
Gold100 expert annotation = PROHIBITED
```
