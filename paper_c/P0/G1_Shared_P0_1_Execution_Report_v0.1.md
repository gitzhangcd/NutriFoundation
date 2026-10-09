# G1-Shared P0.1｜100-Source Acquisition, StudyIdentity Resolution & Scientific Qualification

**Version:** v0.1 execution report  
**Audit date:** 2026-10-10  
**Input snapshot:** `54b4c2eba844f39c07575573a3e834e0bc00c261`  
**Working branch:** `research/gold100-bibliography-candidates-20261009`  
**Scientific status:** **L1 bibliographic identity passed; rights-screen passed; acquisition partial; StudyIdentity pending; L2/L3/L4 scientific qualification NO-GO.**  
**Authority:** SIS R5 → Nutrition Foundation → AI Nutri domain scientific evidence contract → NDF-D0/D1 and experiment-purpose contracts. Clinical nutrition additionally inherits SIS-MED R6.

## 0. Scope, intended unit and nonclaims

The 100 candidates are *exploratory G1-Shared heterogeneous-source validation assets*, NOT the frozen Paper C Gold100 confirmatory source selection. The 100 catalog and selected texts have been exposed to the research/Agent workflow. The confirmatory Gold100 requires independent eligible-pool freeze/hash, prespecified deterministic random selection, and blind Gold construction. Exposed/used sources cannot be silently treated as held-out confirmatory tests. The official `Gold100_Source_Slot_Manifest_v0.1.json` remains untouched with 0/100 source assignments.

Units are distinct: `SourceArtifact ≠ StudyIdentity ≠ EvidenceUnit ≠ ScientificClaim ≠ Recommendation`. A correction, reprint, secondary analysis or related guideline is an independent *document* only, not necessarily an independent *study*.

## 1. Verified actual work in this execution

| Audit | Actual checked or acquired | Status |
|---|---:|---|
| Re-query bibliographic metadata by exact PMID | 100/100 | PASS at PubMed record-identity level |
| DOI/PMCID/title conflicts for listed records | 0 observed | PASS at metadata level only |
| Cross-overlap with 20 Batch001 PMIDs/DOIs | 0 | PASS on exact identifier checks |
| PMC full-text rights screening | 100/100 | DONE; rights vary |
| PMC automated retrieval permitted | 51/100 | 51 potential intake targets, NOT 51 acquired docs |
| Rights unresolved/restricted for automated PMC interface | 49/100 | Alternate lawful publisher access needed |
| PMC body text persisted under CC BY 4.0 with attribution | 3/100 | Text body only; original PDF/tables/figures/supplements not verified |
| Additional partial body PMC reads | 3/100 | QA receipts only, not persistent complete source |
| Provisional internal identity/dependency edges | 8 | RESOLUTION REQUIRED |
| External parent/source dependency queue | 7 | RESOLUTION REQUIRED |
| Topical/design review flags | 8 | CASE-BY-CASE REVIEW |
| L2 span-supported EvidenceUnit qualification | 0/100 | NOT YET PERFORMED |
| L3 precise semantic scope qualification | 0/100 | NOT YET PERFORMED |
| L4 question-specific Scientific Qualification | 0/100 | NOT YET PERFORMED |
| Independent expert GOLD | 0/100 | NOT STARTED |

Important: `PMCID` means indexed presence, not permission to redistribute. Some PMC articles allow text mining but are not open redistribution. Noncommercial or no-derivatives licenses require purpose-appropriate handling. Only three explicitly CC BY 4.0 body projections are stored in this public research branch.

### Acquired persistent example source projections

- `g1_shared_p0_1/source_projections/CAND-G100-004_PMC8864028_PMC_body_CC-BY-4.0.md`: RCT; PMC article body 40,271 characters.
- `g1_shared_p0_1/source_projections/CAND-G100-075_PMC11343900_PMC_body_CC-BY-4.0.md`: Clinical consensus; PMC article body 71,241 characters over two sequential API slices. This is hyperglycaemic crisis management, so domain eligibility for nutrition-specific claims is not presumed.
- `g1_shared_p0_1/source_projections/CAND-G100-081_PMC12457591_PMC_body_CC-BY-4.0.md`: Published correction; PMC article body 4,385 characters.

The projection retains article body text, not necessarily the source document's tables/figure geometry, supplemental documents, exact PDF reading order or translation. `SourceArtifact` original-document qualification remains OPEN.

The initial five-type PMC reader test also accessed three further source bodies partially: `CAND-G100-001` (RCT), `CAND-G100-029` (cohort) and `CAND-G100-048` (network meta-analysis); no redistribution is claimed.

## 2. StudyIdentity and document-version risks

First provisional edges requiring actual trial-registration and source-level reconciliation:

| Candidate pair | Proposed relation | Grounding level |
|---|---|---|
| 007 ↔ 087 | CORDIOPREV parent trial ↔ renal secondary analysis | PubMed abstract level |
| 003 ↔ 090 | TRE + low-carb metabolic-syndrome original ↔ psychosocial secondary analysis | PubMed abstract level |
| 088 ↔ 089 | PREDIMED-Plus different secondary outcomes | PubMed abstract level |
| 073 ↔ 074 | ESPEN kidney clinical-nutrition guideline family (2021/2024 practical) | Guideline publication metadata |
| 029 ↔ 031 | NutriNet-Santé cohort overlap, different endpoints | PubMed abstract level |
| 084 ↔ 098 | 2025 pediatric UC guideline, separate parts | PubMed metadata |
| 018 ↔ 079 | NEGATIVE control: DIRECT-PLUS ≠ DiRECT | Distinct research programs |
| 001 ↔ 002 | NEGATIVE control: TIMET ≠ TREAT | Different trials |

External-family references additionally require parent studies/guidelines for `081/082/083` corrections and `077/078/079/080` secondary/extension publications.

**Important version finding:** PubMed's display for `CAND-G100-081` says *Author Correction*, while the retrieved PMC source body is headed *Publisher Correction*. The original corrected article is identified by DOI `10.1038/s44324-023-00002-1`. Do not normalize away this representation difference; retain source/version/retrieval layer and resolve the authoritative correction relation before qualification.

All above edges are *review hypotheses*, not an immutable final `StudyIdentity` graph. Distinct DOI or PMID is not a guarantee of independent study.

## 3. Domain relevance & corpus risks

Eight records are flagged for science-scope/design assessment: `014,037,046,063,075,084,086,098`. Examples: `063` concerns urine test-ratio conversion rather than a diet intervention; `037` is a colonoscopy bowel-preparation study; `075` is a clinical hyperglycaemic-crisis consensus rather than a dietary recommendation. These can be valid **external biomedical/public-health** sources if the source-type role and prespecified task justify them, but may not silently count toward nutritional-core coverage.

At present, the **80 nutrition + 20 external** domain quota has not been independently classified; the minimum orthogonal challenge tags have not been checked. Four `conflicting_evidence` labels indicate candidate contrast only: a genuine *scientific conflict* requires comparable PICO/estimand/time/context and cannot be inferred from opposing headlines. Two `incomplete_source_text` labels also remain hypotheses: missing PMCID does not prove missing full text.

### Extraction gates from NDF-D1

- **L1 — Mechanical identity:** PMID metadata revalidated; physical document integrity pending.
- **L2 — Source-span support:** NOT QUALIFIED, including tables/figures/source exact locations.
- **L3 — Semantic scope:** NOT QUALIFIED; P/I/C/O, timing, attribution, association/causation and recommendation status require review.
- **L4 — Scientific qualification:** NOT QUALIFIED for a specific evidence question, reference-state or decision task.

**Acquired ≠ Structurally reconstructed ≠ Supported ≠ Qualified ≠ Expert Gold.**

## 4. P0.1 work packages and exit requirements

### P0.1-A｜Authorized Acquisition & Exact Source Snapshot

Process the 51 PMC-retrievable items first, respecting license, and route the remaining 49 through official publisher, society, library or authorized subscription channels. Each SourceArtifact must have exact authoritative URL, version/correction status, acquisition time, retrieval class, license scope, original document checksum or immutable storage reference, and independent PDF/body/table/supplement availability status. Persist restricted sources to approved private storage only; keep public GitHub to manifests, hashes and legally permitted projections.

**Exit:** all targeted items have either a lawful recoverable source snapshot or a reasoned `HOLD_MISSING_SOURCE` decision. Do not invent PDF snapshots.

### P0.1-B｜StudyIdentity, Dependency & Revision Resolution

Build typed source-to-study and source-to-source edges: `PRIMARY_REPORT_OF`, `SECONDARY_ANALYSIS_OF`, `SAME_TRIAL_FAMILY`, `SHARED_COHORT`, `GUIDELINE_VERSION_OF`, `CORRECTS`, `RETRACTS`, `INCLUDES_STUDY`, with `NOT_SAME_STUDY` negative controls. Cross-check primary DOI, trial registry ID, cohorts/enrollment, authors, endpoints, study periods, guideline authority and version.

**Exit:** identity merge/split is independently justified with source anchors. Conflicts and unresolved identities must remain visible, not averaged away.

### P0.1-C｜Scientific Eligibility & Type-Specific Qualification

Create explicit per-source `EvidenceQuestion` and `TaskID`, classify RCT/cohort/synthesis/guideline/consensus/correction type, evaluate relevance and target domain, preserve scope/certainty/normativity. Run L1–L4 checks separately. Reviewer may reject or defer source. Hold any source with insufficient original text, unresolvable version/identity, unsupported claim linkage, or unclear rights.

**Exit:** independent reviewers can reconstruct each admitted claim from a precise authorized source span, including numeric table cell and all population/exposure/comparator/outcome/time restrictions.

### P0.1-D｜Workbench Source Package Readiness

Only after source legal and structural checks, export a `TaskScopedSourcePackage` with typed source profile, source span IDs, PDF/HTML/Markdown qualified views, bilingual original-authority alignment, and safe expert/Agent projections. Test cross-task isolation, original/translation mismatch, stale span updates, table cell attribution and source version swaps. Strict-blind reference work must not leak Agent candidates into R0/R2 Pre-AI.

**Exit:** actual expert reviewer can open, highlight and verify a pre-specified source span without needing the raw copyrighted document copied into a public repository.

### P0.1-E｜G1-Shared Validity Pilot and Gold Governance

G1's evidence-representation validity pilot may use qualified heterogeneous sources under a declared purpose, exposure and source-family split. Gold for a confirmatory paper requires **separately designed independent expert adjudication**, not an Agent's source extraction plus model self-check. Paper C Gold100 remains a different held-out confirmation protocol; its official slot manifest is not changed.

**Exit:** human reviewer source reconstruction, semantic scope audit, study identity audit, independent agreement/adjudication and authorized benchmark purpose recorded. Sample size and source types follow their owning protocol.

## 5. Gate decision as of 2026-10-10

| Gate | Decision |
|---|---|
| Bibliographic registry check | PASS |
| Batch001 20-source exact identifier exclusion | PASS |
| Authorized full-source acquisition | PARTIAL |
| Source file / tables / figures / supplement fidelity | NO-GO |
| StudyIdentity final resolution | NO-GO |
| L2/L3/L4 scientific qualification | NO-GO |
| Workbench production expert package | NO-GO |
| Independent expert Gold freeze | NOT STARTED |
| Paper C confirmatory independence | OFFICIAL SLOTS PRESERVED; candidate exposure warning |

**Overall:** `P0.1_SCREEN_DONE / SCIENTIFIC_QUALIFICATION_NO_GO` — meaningful acquisition and identity audit progress, but not an executed 100-source qualified corpus.

## 6. Output artifact index

- `G1_Shared_P0_1_Bibliographic_Identity_Revalidation_v0.1.json`
- `G1_Shared_P0_1_Rights_and_Acquisition_Screen_v0.1.json`
- `G1_Shared_P0_1_Five_Type_PMC_Reader_Acquisition_Receipts_v0.1.json`
- `G1_Shared_P0_1_Acquisition_and_Qualification_Registry_v0.1.json`
- `G1_Shared_P0_1_StudyIdentity_Dependency_Queue_v0.1.json`
- `G1_Shared_P0_1_Conformance_and_NonRegression_v0.1.json`
- `g1_shared_p0_1/source_projections/*.md` (three CC BY body-only snapshots)
- `candidate_pool/Gold100_Exploratory_Candidate_Registry_100.{json,csv}` (exploratory input, not confirmation set)

## 7. Next action in execution

First isolate a **minimum fully qualified 5-source heterogeneous slice** (RCT, cohort, synthesis, nutrition guideline, consensus/version-correction) with distinct source type profiles and original anchor support, *before* scaling to 100 scientific annotations. Permit up to one source in `HOLD` state to exercise the abstention route; do not force five passes. Then validate the source package against the Workbench expert–Agent exposure boundary.

A public index or model-retrieved snippet is only a discovery artifact, never a substitute for exact original-source, study identity and scientific qualification evidence.
