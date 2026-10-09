# WB-EA-P0｜Conformance, Negative Tests & Execution Gate v0.1

> **Status:** P0 DESIGN REVIEW PACKAGE / SCIENTIFIC ACCEPTANCE PENDING / NO LIVE RUN AUTHORIZATION  
> **Base commit:** `54b4c2eba844f39c07575573a3e834e0bc00c261`  
> **Implementation scope:** Proposed additions **only** under `docs/workbench/WB-EA-P0_*` and `apps/workbench/ea_p0/**`.

## 1. Gate taxonomy

| Gate | Purpose | P0 result | Owner |
|---|---|---|---|
| G0 / source-state inventory | Inspect existing D0 reader + NDS adapter; distinguish code vs intention | **DOCUMENTED** | Workbench |
| G1 / architecture | Split `EVIDENCE_ECOSYSTEM_CASE` from `DECISION_CASE` | **SPECIFIED** | Evidence program / NDS |
| G2 / exact contract | Source type router + candidate/review + source access + profile mapping | **SPECIFIED** | Engineering + science |
| G3 / scientific consistency | E0–E8 types, SourceArtifact/StudyIdentity, synthesis/recommendation/consensus distinction | **PENDING SCIENCE SIGNOFF** | Scientific owner |
| G4 / runtime conformance | Generalized Reader, Agent extractor, persistence, API/read-model, five real document classes | **NOT IMPLEMENTED** | Engineering |
| G5 / non-regression | NDS R0/R1/R2 19 fields, source/role isolation; zero upstream science diff | **TO VERIFY AT PR/CI** | CI |
| G6 / external eligibility | Source rights, originals, experts, identity, ethics, production security, D2 r2/r3 | **NO-GO** | Independent authorities |
| G7 / Gold validity | Independent double-review, adjudication, calibration, EEB task validity | **NOT STARTED** | Scientific evaluation |

**Do not write PASS for G3–G7 because a P0 document exists.** Machine-readable profiles are proposed view/annotation field groups; they are **not** final canonical upsteam schema or completed Agent prompting.

## 2. Positive synthetic fixtures to add in P1

| Case ID | Source type | Task | Expected allowed behavior |
|---|---|---|---|
| EA-POS-01 | RCT / 5:2 paper | Evidence annotation | With explicit synthetic allowlist, source unit quote→Anchor→candidate→expert correction; **never Gold** |
| EA-POS-02 | OBSERVATIONAL_STUDY | Evidence annotation | Association estimate, confounder adjustment and analysis model retained |
| EA-POS-03 | SYSTEMATIC_REVIEW_META | Evidence annotation | Members traced by StudyIdentity; no double counting |
| EA-POS-04 | GUIDELINE | Evidence annotation | Recommendation statement, original grade, exception and provenance retained |
| EA-POS-05 | CONSENSUS | Evidence annotation | Deliberation method, dissent, and evidence-gap status separated |
| EA-POS-06 | NARRATIVE_REVIEW | Evidence annotation | Author hypothesis remains tentative with cited-primary lineage |
| EA-POS-07 | CORRECTION_RETRACTION | Evidence annotation | Historical knowledge cutoff preserved; dependents flagged |
| EA-POS-08 | Official NDS-R1 existing case | Decision reference | Existing R0/R1/R2 behavior byte-for-byte unaffected |

## 3. Negative / kill-test fixture matrix

| ID | Attempt | Expected result |
|---|---|---|
| EA-NEG-01 | Unknown `source_type` routed to RCT automatically | `TYPE_UNRESOLVED_HOLD` |
| EA-NEG-02 | Evidence task sent to `NDS_R1_DECISION_CAPTURE` | `BLOCK_PROFILE_TASK_MISMATCH` |
| EA-NEG-03 | Source ID known in repository but missing from task allowlist | `DENY_SOURCE_NOT_ALLOWED` |
| EA-NEG-04 | Same source ID, different revision/SHA | `DENY_SOURCE_REVISION_MISMATCH` |
| EA-NEG-05 | Agent candidate without original source span / no immutable freeze | `BLOCK_UNVERIFIED_CANDIDATE` |
| EA-NEG-06 | Use Chinese translation text as authoritative original span | `BLOCK_TRANSLATION_AS_SOURCE` |
| EA-NEG-07 | PDF page hint promoted to verified BBox | `BLOCK_UNVERIFIED_PDF_LOCATOR` |
| EA-NEG-08 | Agent generation leaks to independent blind annotator | `DENY_EXPOSURE` |
| EA-NEG-09 | `ACCEPT` auto-creates GoldAnnotationUnit | `BLOCK_UNAUTHORIZED_PROMOTION` |
| EA-NEG-10 | Non-significant RCT result asserted as equivalence | `SCIENTIFIC_REVIEW_FLAG` |
| EA-NEG-11 | Observational association promoted to causal effect | `SCIENTIFIC_REVIEW_FLAG` |
| EA-NEG-12 | Meta member duplicated / guideline falsely treated as RCT | `SCIENTIFIC_REVIEW_FLAG` |
| EA-NEG-13 | Guideline exception deleted or grading scale falsely converted | `SCIENTIFIC_REVIEW_FLAG` |
| EA-NEG-14 | Expert consensus vote described as high-certainty effect evidence | `SCIENTIFIC_REVIEW_FLAG` |
| EA-NEG-15 | Future correction/retraction exposed to earlier knowledge snapshot | `DENY_FUTURE_EVIDENCE` |
| EA-NEG-16 | R0 reads Agent or R2 PRE reads candidate bytes/labels | `DENY_EXPOSURE` |
| EA-NEG-17 | Existing R1 exposed to unbounded PDF/full search | `DENY_UNAUTHORIZED_SOURCE` |
| EA-NEG-18 | Scientific Gold requested with 0 real experts/0 adjudication | `BLOCK_UNQUALIFIED_REFERENCE` |

Important distinction: `SCIENTIFIC_REVIEW_FLAG` is **not** a deterministic correctness proof. The system detects a potentially critical mismatch and routes it to scientific judgment. Structural `DENY/BLOCK` gates can be enforced mechanically.

## 4. First five heterogeneous source tests

A qualifying P1 experiment must pass this real-source sequence, with sources/revisions and rights vetted before release:

1. **RCT / 5:2 trial**: exact 6-month and 12-month arm data; ITT/LOCF vs sensitivity; no false equivalence; paragraph + table cell original span validated; source-specific risk-of-bias review.
2. **Observational nutrition cohort**: exposure and outcome windows, adjusted model, residual confounding; no causal overclaim; avoid adjusting for future outcome.
3. **SR/Meta**: exact included StudyIdentity membership, overlaps, heterogeneity; linked primary study publications without duplicate StudyIdentity.
4. **Formal guideline**: recommendation original text and organization grading; target population, qualifier/exceptions, version/correction and evidence dependencies.
5. **Consensus**: Delphi/vote/panel provenance, dissent, expert judgment vs empirical support distinction.

In each test preserve `source bytes → canonical offsets → candidate → human original words → verification → output`. UI and scientific candidate export must reproduce independently from stored digests. Include a synthetic correction/retraction time-travel test; otherwise passing the first five does not demonstrate historical validity.

## 5. Traceability and measurement

For each candidate, collect:

```yaml
CaseReceipt:
  task_kind:
  profile_id:
  source_version_ids: []
  original_source_sha256: []
  canonical_source_sha256: []
  translation_versions: []
  agent_run_digest:
  candidate_set_digest:
  expert_pre_exposure_status:
  review_records: []
  adjudication_ref: null
  promotion_ref: null
  critical_error_labels: []
  expert_minutes:
  audit_root_digest:
```

P1/P2 study endpoints: per-type span fidelity/recall, critical scientific error rate (CSER), numeric fidelity, StudyIdentity deduplication, recommendation exception retention, false causality/false certainty, expert time & clarification, unknown/abstain capture, source lineage reconstruction, time cutoff leak rate. CI engineering tests cannot substitute for independent scientific validity.

## 6. Protected paths and exact no-regression requirements

### Frozen behavior

- `apps/workbench/c1/specs/decision_profile.json`: same 19 fields and seven `reference_set` classes.
- `apps/workbench/c2_1/**`: existing fixed-reader synthetic controller unchanged at P0; P1 generalization must be separately staged with original tests.
- `runs/NDF/**` / `runs/NDS/**` / `src/nutrifoundation/**`: zero code/contract changes at P0.
- `SYN-5-2-PAPER` stays synthetic-only fixture; source version `r2/r3` conflict untouched.
- `R0`: never Agent; `R1`: frozen candidate excerpts only; `R2 PRE`: immutable J_preAI before candidate visibility.
- Task-isolated source ACL, case versions, original source and translation projection, no unbounded export/search / static route.

### Review workflow

1. Engineer produces explicit `diff --name-only` against `54b4c2e`; **only P0 docs/specs/fixtures** are permitted.
2. Contract/profile JSON lints; exact seven source types unique; each profile non-empty, ordered fields, canonical candidate types and type-specific kill tests.
3. Static conformance tests and fixture manifest run; mark as **spec tests only**, not runtime functional tests.
4. Existing Workbench CI and NDF/NDS regression checks must pass on merge candidate (not inferred from historic successful SHA).
5. Scientific owner records schema impact and asserts no conflict with E0–E8 upstream, SIS R5 / SIS-MED R6.
6. Open Draft PR against `workbench-v0.3-p1.3-ux-acceptance-remediation`, not `main`, until pending P1 branch and scientific release decisions.

## 7. Exit criteria

`WB-EA-P0` can be called **DESIGN COMPLETE** after signed review of this package, manifest schema lints and exact path/authority audit; **no** live multi-source capability follows solely from these docs.

`WB-EA-P1` may begin engineering in a child branch and is **not** GO for real expert data. Before real expert pilot: identity/qualification/ethics/source bytes and rights/case version/production security gates independently verified, as detailed in `WB-P0.2-C2.2_Real_Expert_Readiness_and_Security_Report_v0.1.md`.

Recommended next stage:
`WB-EA-P1｜Versioned Multi-Source Registry, Typed Annotation Workpacks & Agent Candidate Round-Trip`.
