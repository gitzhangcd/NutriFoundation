# EvidenceUnit Verification Queue v0.1

## Purpose

Define the human and agent verification workflow after candidate EvidenceUnit extraction.

## Queue States

```text
Candidate
  -> Agent Verified
  -> Human Review
  -> Frozen EvidenceUnit
```

## Required Review Dimensions

- Population correctness
- Intervention/exposure correctness
- Comparator correctness
- Outcome definition
- Effect interpretation
- Uncertainty representation
- Source span validity
- Applicability boundary

## Failure Labels

- unsupported_claim
- causal_overstatement
- missing_context
- incorrect_population_transfer
- provenance_missing

## Freeze Rule

Only reviewed EvidenceUnits can enter ScientificClaim generation.
