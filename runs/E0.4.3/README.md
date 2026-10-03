# E0.4.3 Runs

## Current state

```text
E0.4.3-R0     = PASS / FROZEN
E0.4.3-P0.1   = PASS / FROZEN
E0.4.3-P0.2.1 = PASS / FROZEN
E0.4.3-P0.2.2 = PASS / RAW REGISTRY FROZEN
Primary program = Paper C confirmatory evidence production
Current execution gate = P0.2.3 Eligible-Pool Qualification & Pre-Sampling Freeze
```

## Upstream freeze

```text
E0.4.2-E3-A2.8-FROZEN
83a33bbdbb9a647c3aea96a67bf47ba5f246c05a
```

## R0 authority

```text
docs/E0.4.3-R0_Publication_Goal_Reconciliation_Measurement_System_Lock_Gold100_Alignment_Non_Regression_Freeze_v1.0.md
paper_c/P0/Gold100_Measurement_System_Lock_v1.0.yaml
runs/E0.4.3/R0/R0_Freeze_Manifest_v1.0.json
```

## P0.1 authority

```text
docs/E0.4.3-P0.1_Gold100_Independent_Scientific_Evidence_Ownership_Annotation_Independence_Adjudication_Gold_Freeze_Contract_v1.0.md
paper_c/P0.1/Gold100_Gold_Governance_Contract_v1.0.json
paper_c/P0.1/Gold100_Annotation_Record_Schema_v1.0.json
paper_c/P0.1/Gold100_Independent_Annotation_Manual_v1.0.md
runs/E0.4.3/P0.1/P0.1_Freeze_Manifest_v1.0.json
```

## P0.2.1 authority

```text
docs/E0.4.3-P0.2.1_Gold100_Eligible_Pool_Source_Eligibility_Provenance_StudyIdentity_Challenge_Tag_Freeze_v1.0.md
paper_c/P0.2.1/Gold100_Source_Eligibility_Contract_v1.0.json
paper_c/P0.2.1/Gold100_Candidate_Source_Record_Schema_v1.0.json
paper_c/P0.2.1/Gold100_Challenge_Tag_Registry_v1.0.json
paper_c/P0.2.1/Gold100_Eligible_Pool_Screening_Manual_v1.0.md
runs/E0.4.3/P0.2.1/P0.2.1_Freeze_Manifest_v1.0.json
```

## Planned execution chain

```text
R0 Measurement-System Lock [PASS]
→ P0.1 Independent Gold governance [PASS]
→ P0.2.1 Gold100 source eligibility [PASS]
→ P0.2.2 >=260 real candidate SourceArtifacts [PASS: 342]
→ P0.2.3 eligible-pool qualification + hash freeze [NEXT]
→ P0.2.4 deterministic Gold100 selection
→ P0.3 independent expert calibration
→ P0.4 Gold100 dual annotation + adjudication
→ P1 AB0–AB6 strict-blind confirmatory execution
→ P2 CSER / human-burden / kill-test analysis
```

Important:

```text
Candidate unit = SourceArtifact.
Dependency unit = StudyIdentityCluster.
Stress is a tag/selection stratum, not a sixth source family.
Eligibility and challenge tags are assigned before any AB output is seen.
Unresolved StudyIdentity cannot survive eligible-pool freeze.
No pool hash → no deterministic Gold100 sampling.
AB0 is a comparator, not Gold.
Gold opportunity maps are created before AB scoring.
260 is a candidate-mining floor, not the final sample size.
Gold100 = Core80 + Stress20 is the confirmatory corpus.
NHANES individual-subject DecisionEpisode cases are outside Paper C scope.
```