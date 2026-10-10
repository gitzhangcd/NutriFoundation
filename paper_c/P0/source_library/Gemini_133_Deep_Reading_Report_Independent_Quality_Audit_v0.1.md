# G1-Shared｜Gemini 133-source Deep-Reading Report Independent Reliability Audit v0.1

**Audit date:** 2026-10-10  
**Status:** **SCIENTIFIC_CARD_NO-GO / FILE_VERIFICATION_NOT_DEMONSTRATED / SOURCE_LIBRARY_UNCHANGED**  
**Input:** user-uploaded `SourceLibrary_133_Deep_Reading_and_Evaluation_Report.md`; SHA256 `9372a7eab164d5bbc9d20d645856f8072d66803afabe736c47a1decf355d8264` (the reported Markdown report, **not a PDF checksum**).  
**Audit basis:** local static report inspection, pattern/consistency checks, spot-checks against PubMed articles and abstracts. Actual user-local PDF files were **not accessible** to this audit.

## Executive disposition

- Gemini provided **133 Markdown study cards**, with **79 `ACCEPTED_AS_VERIFIED_LOCAL_PDF`**, **53 `ACCEPTED_AS_RENDERED_SNAPSHOT`**, and **1 `HOLD_FOR_REVIEW`**. Those 132 accepted labels must **not** be promoted to independent file/identity/scientific acceptance without the required per-file logs.
- 18 **title-to-study-type conflicts** were found by deterministic heuristic on 133 cards. These are **review candidates, not 18 final gold classifications**; `CAND-G100-046` has potentially mixed indexed publication types and requires full-text methodology adjudication. Other examples are unequivocally misclassified according to article title and PubMed abstract.
- **132/133** core-finding fields repeat only five broad template statements (49 RCT, 45 guideline/consensus, 27 synthesis, 8 secondary, 3 correction); only `CAND-G100-010` carries a source-specific statement. **No per-study effect estimates and no page-span anchors** support the 132 generically worded findings.
- **47/133** cards state `未明确提取` for sample/extraction, while many others confuse total N, subgroup N, cases/events or number of component trials.
- No per-file independent SHA256, actual file size, path resolution, PDF opening log, page-validation log, visual review evidence, rights proof, or replay evidence occurs in this submitted Markdown. Absence of evidence in the Markdown **does not establish** whether separate local logs may exist; those logs must be provided.
- This is **not** an approval to overwrite `SourceLibrary_133_Local_PDF_Manifest_v0.1.json`, paper scientific truth, or any SourceArtifact identity in an authoritative ledger.

## Must-isolate reported asset mismatch

`CAND-G100-010`: The Gemini report says the registered RCT `PMID 36287562 / DOI 10.1001/jamanetworkopen.2022.38645` points to a 164-page, ~32.16 MB USDA/HHS `Dietary Guidelines for Americans 2020-2025` local file.

**Disposition:** `USER_AGENT_REPORTED_ASSET_BIBLIOGRAPHY_MISMATCH / HOLD_FOR_REVIEW`. Strong and testable finding, **not independently verified** without the PDF bytes or first-page evidence. Preserve the original file and checksum, do not rename or overwrite it silently; obtain the correct RCT separately, and register the government guideline as a separate potential SourceArtifact only after independent source-identity confirmation and explicit approval.

## 18 title-classification conflicts (triage list)

| SourceID | Title-implied design | Gemini label | Initial action |
|---|---|---|---|
| CAND-G100-014 | RCT | Guideline | Paper and PubMed title state randomized trial |
| CAND-G100-015 | Randomized crossover trial | Consensus | Keto-Med trial |
| CAND-G100-018 | Randomized trial | Guideline | DIRECT PLUS |
| CAND-G100-031 | Prospective cohort | RCT | NutriNet-Sante cohort |
| CAND-G100-032 | Prospective cohort | RCT | Title/abstract cohort |
| CAND-G100-033 | UK Biobank prospective cohort | RCT | Title/abstract cohort |
| CAND-G100-046 | Cohort (title) | RCT | Ambiguous PubMed RCT index; verify primary methods before adjudication |
| CAND-G100-052 | Systematic review and meta-analysis | Guideline | DASH risk synthesis |
| CAND-G100-054 | Systematic review and meta-analysis | Guideline | Low-GI clinical evidence synthesis |
| CAND-G100-056 | Systematic review and meta-analysis | Guideline | Dietary patterns and fertility review |
| CAND-G100-058 | Systematic review and meta-analysis | Secondary analysis | Protein systematic review |
| CAND-G100-061 | Systematic review and meta-analysis | Guideline | Breast-cancer-risk review |
| CAND-G100-082 | Correction | Guideline | PKU correction |
| CAND-G100-083 | Correction | Prospective clinical intervention | AHA advisory correction |
| SUPP-G1-012 | Systematic review and meta-analysis | Guideline | Sodium and BP dose response |
| SUPP-G1-017 | Population based cohort study | RCT | Ultra-processed food mortality cohort |
| SUPP-G1-029 | Systematic review and meta-analysis | Guideline | EN PN comparison |
| SUPP-G1-033 | Systematic review and meta-analysis | Guideline | Protein and resistance training review |

This is a **lower-bound title-heuristic test**; it does not certify the other 115 records as correct. PubMed abstracts confirmed clear errors including PMID 38578692 (RCT), 35641199 (randomized crossover RCT), 33461965 (DIRECT PLUS RCT), 37513679 (systematic review/meta-analysis), 34348965 (systematic review/meta-analysis), 37299551 (systematic review/meta-analysis), 35187864 (systematic review/meta-analysis), 36731160 (systematic review/meta-analysis), 32873338 and 38527138 (correction notices), and 32094151, 39796444, 38374703 (systematic reviews and meta-analyses).

## Sample-number conflation from PubMed abstract spot-checks

| SourceID | Gemini `N` | Original PubMed abstract | Why this matters |
|---|---:|---|---|
| CAND-G100-002 | 25 | 116 participants overall; 25 only within one in-person arm | subgroup vs total study size |
| CAND-G100-029 | 159 | 105,159 participants overall | thousands stripped |
| CAND-G100-031 | 2,228 | 104,980 participants, **2,228 cases of cancer** | outcome events vs cohort N |
| CAND-G100-030 | 19,503 | 198,636 people across 3 cohorts; 19,503 incident T2D cases | incidence cases vs cohort N |
| CAND-G100-048 | 76 | 99 randomized trials and 6,582 adults; 76 trials in particular short-term subgroup | subgroup study count vs synthesis N |

- TREAT trial `CAND-G100-002`: PubMed reports *no significant between-group weight-loss advantage*, contrary to the broad `significant difference` template applied. See https://pubmed.ncbi.nlm.nih.gov/32986097/.
- Cohort `CAND-G100-029`: https://pubmed.ncbi.nlm.nih.gov/31142457/
- Cohort `CAND-G100-031`: https://pubmed.ncbi.nlm.nih.gov/29444771/
- Cohorts/meta `CAND-G100-030`: https://pubmed.ncbi.nlm.nih.gov/36854188/
- Network meta `CAND-G100-048`: https://pubmed.ncbi.nlm.nih.gov/40533200/

**Required type-specific semantic fields:** `total_enrolled_n`, `analysed_n`, `subgroup_n`, `event_n`, `trials_k`, `guideline_scope`, with units and source-anchor. Unknown values must remain `null`; a number is not permitted without type and denominator.

## Additional internal contradictions

1. MASLD family at section III lists the complete guideline as **46 pages** and executive summary as **11 pages**, whereas the per-source cards list `SUPP-G1-008` as **133 pages**, `SUPP-G1-009` as **18 pages**. This does not prove either local PDF count; must reconcile file versions and print layouts using local PDF tools.
2. Some domain labels are also inappropriate: breast cancer nutrition/exercise feasibility RCT `CAND-G100-025` is labelled T2D management; `CAND-G100-009` low-carb feeding trial is classified as TRE/fasting.
3. The report states `53` `PMC_FULLTEXT_RENDER` documents `ACCEPTED_AS_RENDERED_SNAPSHOT` but gives no PDF source-url or binary-provenance evidence. `acquisition_channel` alone is not sufficient to validate original-vs-browser-rendered fidelity.
4. There are no exact quotations, page-specific evidence anchors, extraction method/version fields, per-file hash receipts or visual reviewer decisions to support a **deep-reading** scientific gold claim.

## G0-G5 acceptance status (this submitted report only)

| Gate | Disposition | Evidence still required |
|---|---|---|
| G0 Manifest identity | INSUFFICIENT_EVIDENCE | Immutable input manifest SHA256, per-source identity/duplicate status, baseline `97` hash history |
| G1 Local file existence/size/SHA256 | **NOT_DEMONSTRATED** | `expected_sha256`, independently computed `actual_sha256`, `expected_size_bytes`, `actual_size_bytes`, actual path, time |
| G2 PDF open/container integrity | NOT_DEMONSTRATED | Exact parser/library version, page iteration logs, signature, encryption, failures and file checksum |
| G3 Correct PDF identity/fulltext | **NO-GO FOR ACCEPTANCE** | Fix or quarantine 010 mismatch, PDF title/DOI/page evidence for 133 items, abstract-only vs fulltext |
| G4 Provenance/license | NOT_DEMONSTRATED | Native-publisher vs repository-PDF vs rendered snapshot with proof and license for each |
| G5 Artifact family/scientific strata | **NO-GO** | Resolve title-type conflicts and mixed denominators, source family and errata evidence |
| Human risk-stratified check | NOT_DEMONSTRATED | At least 24 cases plus all exceptions with reviewer, page, evidence and decision |

## Remediation / scope

**Track A - source-only G0-G5 verification:** On the local machine run required actual PDF checks, without expanding into abstract synthesis, MinerU or Workbench. Must deliver at least these evidence artifacts: `00_run_environment.json`, `01_input_manifest_receipt.json`, `02_source_pdf_validation_133.jsonl`, `03_source_pdf_validation_133.csv`, `04_source_file_exceptions.csv`, `05_source_artifact_relationships.csv`, `06_format_and_rights_inventory.csv`, `07_human_visual_review_queue.csv`, `08_coverage_and_readiness_summary.json`, `09_Acceptance_Report.md`, `10_replay_and_test_results.txt`.

**Track B - scientific coding:** Isolate the Gemini deep-reading report as an **unverified candidate**. For a separately authorized future task, recode scientific metadata against actual article methods/abstract with source anchors and typified denominators; do not use generic result templates; do not overwrite source-only archives.

**No silent file repair, ID renaming, PDF content redistribution, Gold promotion, UI development, full-document markdown conversion, or main merge.**
