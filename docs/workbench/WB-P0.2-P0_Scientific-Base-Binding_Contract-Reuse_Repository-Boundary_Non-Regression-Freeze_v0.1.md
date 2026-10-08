# Workbench WB-P0.2-P0｜Scientific-Base Binding, Contract Reuse Map, Repository Boundary & Non-Regression Freeze

**Status:** `PASS_WITH_EXPLICIT_COMPATIBILITY_BINDING`  
**Date:** 2026-10-08  
**Engineering branch:** `workbench-wb-p0.2-real-paper-roundtrip`  
**Pinned scientific base:** `ndf-d1-scientific-core-thin-slice@2259fdac9502541909a70d5d79c3460cecb6f657`

## 1. Gate purpose

This gate authorizes Workbench engineering to begin without redefining or silently mutating the current NDF/NDS scientific program.

The engineering phase name is:

[
oxed{
WB	ext{-}P0.2 
eq NDS	ext{-}R1	ext{-}P0.2
}
]

- **WB-P0.2** = Workbench engineering validation.
- **NDS-R1-P0.2** = scientific/empirical next stage and remains gated by real expert capture.

No Workbench implementation artifact may be interpreted as empirical completion of NDS-R1-P0.1 or entry into NDS-R1-P0.2.

## 2. Scientific base binding

Workbench is bound to the current scientific route already frozen on the pinned base:

`SIS R5 → Nutrition Foundation v0.1 → NDF-D0 → NDF-D1 || NDF-D2 → NDS-R1`.

The current NDS-R1-P0.1 state remains:

- operational readiness: PASS;
- real experts bound: 0 / 3;
- R0 judgments: 0;
- R2 J_preAI: 0;
- Agent candidate sets: 0;
- reconciliations: 0;
- QualifiedReference: not created.

Workbench must not fabricate any of these empirical outputs.

## 3. Contract reuse map

### 3.1 Reuse unchanged as scientific authority

| Scientific artifact | Workbench use | Mutation |
|---|---|---|
| `runs/NDS/R1/P0/Role_Input_Surface_Contract_v0.1.json` | Defines permitted/forbidden role input surfaces and leakage boundary | **NO** |
| `runs/NDS/R1/P0.1/Exposure_Lock_Registry_v0.1.json` | Defines R0/R1/R2 exposure ordering and hard lock semantics | **NO** |
| `runs/NDS/R1/P0.1/Judgment_Freeze_Contract_v0.1.json` | Defines immutable pre/post judgment semantics and freeze receipt requirements | **NO** |
| `runs/NDS/R1/P0.1/Expert_Slot_Binding_Registry_v0.1.json` | Defines expert-slot eligibility and same-case cross-arm exclusion | **NO** |
| `runs/NDS/R1/P0.1/Expert_Qualification_Instance_Registry_v0.1.json` | Defines qualification fields and binding gate | **NO** |
| `runs/NDS/R1/P0/Reconciliation_Exposure_Templates_v0.1.json` | Defines post-exposure reconciliation and exposure-log semantics | **NO** |
| `runs/NDS/R1/P0.1/Human_Baseline_Source_Packet_v0.2.json` | Current bounded human source substrate | **NO** |
| `runs/NDS/R1/P0.1/R0_Human_DeNovo_Workpack_v0.2.json` | Current R0 operational form/content binding | **NO** |
| `runs/NDS/R1/P0.1/R2_PreAI_Workpack_v0.2.json` | Current R2 pre-AI operational form/content binding | **NO** |

### 3.2 Workbench-owned engineering objects

Workbench may introduce, version and test these new objects without claiming new scientific truth:

- `AnnotationSourcePackage`
- `CanonicalDocument`
- `DocumentUnit`
- `ParseRun`
- `SourceAnchor`
- `PdfLocator` / optional future `PDF_PAGE_BBOX`
- `WorkbenchDraft`
- `LockSnapshot` as an engineering realization of the existing judgment-freeze semantics
- `WorkbenchAuditEvent`
- reader/importer/view-model objects

These objects must remain adapters/infrastructure. They do **not** create `EvidenceUnit`, `ScientificClaim`, `QualifiedDecisionReference`, expert qualification, or empirical Gold by themselves.

## 4. Compatibility binding note

`Judgment_Freeze_Contract_v0.1.json` names the original v0.1 R0/R2 workpack paths, while the current operational workpacks are v0.2 and explicitly supersede v0.1.

This gate does **not** rewrite the frozen judgment-freeze contract.

Workbench therefore binds:

[
	ext{freeze semantics from Judgment_Freeze_Contract v0.1}
+
	ext{current operational payload from R0/R2 Workpack v0.2}
]

through an explicit adapter/version map.

Any future semantic conflict between the frozen contract and a later workpack version is a hard gate failure; Workbench must not silently resolve it.

## 5. Repository boundary

### 5.1 Protected scientific lineage

During WB-P0.2, the following are treated as read-only upstream authority unless a separate scientific revision is explicitly opened:

- `runs/NDF/**`
- `runs/NDS/R1/P0/**`
- `runs/NDS/R1/P0.1/**`
- current NDF/NDS scientific specification documents
- existing scientific engine behavior unrelated to an explicitly approved adapter

### 5.2 Workbench implementation namespace

New Workbench implementation SHOULD be isolated under:

```text
apps/workbench/
packages/workbench_contracts/
fixtures/workbench/
tests/workbench/
docs/workbench/
runs/workbench/
```

The first vertical slice should not require mutation of frozen scientific run artifacts.

## 6. Non-regression invariants

WB-P0.2 must preserve all of the following:

1. **No stage promotion:** NDS-R1-P0.1 remains empirical-capture-pending.
2. **No synthetic expert completion:** UI demos/tests cannot create real qualification/binding/judgment records.
3. **No pre-AI leakage:** R2 machine output remains inaccessible until an eligible J_preAI freeze exists.
4. **No overwrite after freeze:** post-AI reconciliation creates a new object; it never overwrites J_preAI.
5. **No cross-arm identity reuse:** same-case expert-slot exclusion remains enforceable.
6. **No source-surface widening:** Workbench UI cannot expose forbidden labels, hidden values, other-arm outputs or final reference data.
7. **No parser-as-truth:** parsing/Markdown/canonicalization status is not scientific verification.
8. **No Workbench-owned Gold:** Workbench capture infrastructure cannot promote scientific Gold or QualifiedReference.
9. **Version-bound replay:** source package, canonical revision, judgment snapshot and exposure events must be replayable by immutable identifiers/hashes.
10. **Fail closed:** stale revision, mismatched hash, missing anchor target, or exposure-order violation must reject rather than auto-repair.

## 7. Gate decision

[
oxed{
	extbf{WB-P0.2-P0 = PASS}
}
]

with one explicit compatibility binding note: frozen judgment-freeze semantics v0.1 are reused together with current superseding R0/R2 workpack payloads v0.2 via a versioned Workbench adapter; no upstream frozen artifact is rewritten.

### Authorized next step

[
oxed{
	extbf{
WB-P0.2-A｜
Real-Paper AnnotationSourcePackage
ightarrow
CanonicalDocument
ightarrow
Reader Vertical Slice
}
}
]

Initial acceptance scope is limited to real-paper import, canonical reading, SourceAnchor round-trip and original-PDF traceability. Team dashboard, AI comparison and full collaboration UI remain out of scope for this first slice.
