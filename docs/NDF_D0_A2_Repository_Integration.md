# NDF-D0-A2 Repository Integration

Status: `IMPLEMENTED ON NDF NAMESPACE / LEGACY LINEAGE UNTOUCHED`

This change lands the NDF-D0 A2 validator runtime as an additive namespace under the
existing `NutriFoundation` repository.

## Scientific boundary

The implementation preserves:

```text
Repository != Scientific Authority
Validator PASS != Scientific Truth
D0 Conformance != D1 Qualification
Physical Representability != Reference Validity
10/10 A2 fixtures != Full NF-F01–F22 Conformance
```

No Nutrition Foundation ontology is added or changed.

## Canonical paths

```text
src/nutrifoundation/ndf/d0/
fixtures/ndf/d0/
tests/ndf/
runs/ndf/D0/A2/
```

The legacy E0.x, Batch001, evaluator-v2, and `paper_c` paths are not moved,
rewritten, re-scored, or re-qualified.

## Runtime

A2 implements the four frozen D0 validator classes:

- V0.1 Structural
- V0.2 Dependency
- V0.3 Temporal
- V0.4 Projection

It reproduces the expected behavior of eight negative fixtures and two positive
fixtures and checks the first real scientific object graph for `B002-S1-001`
(PMID 36670395) at physical-conformance level only.

## Next boundary

After this repository integration passes CI/non-regression:

```text
NDF-D1 || NDF-D2
```

may begin. Scientific claim qualification and human reference construction remain
open and are explicitly out of scope for A2.
