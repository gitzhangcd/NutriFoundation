# G1-Shared P0.1-A.1｜Primary-Document Fidelity, Original Tables & Supplements, Version Lineage & Expert L4 Adjudication

**Version:** v0.1  
**Execution date:** 2026-10-10  
**Base commit:** `54b4c2eba844f39c07575573a3e834e0bc00c261`  
**Working branch:** `research/gold100-bibliography-candidates-20261009`  
**Completion state:** `REAL_SOURCE_FIDELITY_AND_LINEAGE_AUDIT_DONE_PARTIALLY / EXPERT_L4_PENDING / NO_GO_FULL_PRIMARY_SOURCE_FIDELITY`

## 0. Scientific scope and immutable boundaries

This phase is a **G1-Shared source-validity development pilot** using five publicly identifiable real papers/official guidance, plus correction case `CAND-G100-081`. It is **not** Paper C Gold100 independent confirmation. All 100 Gold100 official slots remain unbound. The first-five development sources and Agent-derived observations are exposed to research workflow, not valid as pristine hold-out confirmation.

**SourceArtifact ≠ original PDF ≠ PMC body text ≠ StudyIdentity ≠ EvidenceUnit ≠ Recommendation.** An authorized PMC article-body read can support bounded fields without yielding an original-image, supplement-complete or adjudicated scientific reference.

## 1. Accomplished acquisition and QA

First five exact PubMed identifiers:

| Source | PMID | PMCID | DOI | Complete PMC body | Original PDF fidelity |
|---|---|---|---|---|---|
| RCT `004` | 35194047 | PMC8864028 | 10.1038/s41467-022-28662-5 | 40,271 chars, PASS | HOLD |
| Cohort `029` | 31142457 | PMC6538975 | 10.1136/bmj.l1451 | 59,562 chars, PASS | HOLD |
| Network meta `048` | 40533200 | PMC12175170 | 10.1136/bmj-2024-082007 | 45,559 chars, PASS | HOLD |
| Academy EBPG `071` | 36462613 | PMC12646719 | 10.1016/j.jand.2022.11.014 | 73,139 chars, PASS | HOLD |
| PN expert consensus `096` | 38869255 | PMC11170495 | 10.1093/ajhp/zxae078 | 58,335 chars, PASS | HOLD |

All five complete bodies were fetched in contiguous text-offset chunks, using PMC rights checks, and their concatenated lengths matched PMC totals. Existing `P0_1_A_FirstFive_Acquisition_and_Span_QA_v0.1.json` retains 10 short text-span anchors. Additional *publisher authority* checks confirmed journal or original guideline web material where available; they do NOT amount to downloaded immutable full PDF or supplement binary integrity.

Authority check and supplemental file map: `P0_1_A_1_Primary_Document_and_Supplement_Inventory_v0.1.json`. 

## 2. Original documents, tables and supplements — honest fidelity decision

- RCT 004: Nature Communications primary publisher HTML confirms ChiCTR2000029797; 90 randomized (30/30/30), 82 completed, primary HOMA-IR. Publisher lists Supplementary Information PDF, peer review/reporting summary PDFs and source-data XLSX. Fetching these annex binaries failed from available endpoints, so **table/plot parity NOT VERIFIED**. Original PDF not independently rendered.
- Cohort 029: BMJ indexed primary publisher narrative supports sample 105,159 and Model-1 adjusted HR 1.12 (95% CI 1.05–1.20) per absolute 10 percentage point rise in ultra-processed food. Original PDF direct access failed 403. Table-2 cell/column fidelity and appendix 9 are pending. Numeric source anomaly discovered below.
- Network meta 048: Original BMJ 2025 article; PMC body refers to GRADE comparison tables 5–21 and appendices. 99 reports/clinical trials and 6,582 participants are reported, but independent StudyIdentity deduplication and network plot/appendix parity remain pending.
- Guideline 071: The journal manuscript calls itself an **abbreviated report**; Academy EAL official recommendation source is a separate authority. The actual EAL web page confirms a `Level 1(B)/Imperative` MNT recommendation and `Consensus/Conditional` NCP recommendation, with client-specific exceptions and Evidence-to-Decision context. The full EAL guide, evidence tables and PDF export were not saved with page-level file checksums.
- PN consensus 096: PMC text reports adapted Delphi method, 13 panel members and all voting in agreement for statements; source also states the panel is **not a formally authorized guideline committee**. Table 1/2 native cell cross-validation has NOT been performed; `CC BY-NC-ND` constraints preclude open modified republication.

**Actual verified full original PDF + figures/tables/attachment parity: 0/5.** Source links discovered and native HTML inspected are not binary file qualification. Lack of PDF access must remain explicit; do not claim faithful source-document capture or file SHA256.

## 3. Scientific source-native numeric inconsistency (important positive discovery)

For cohort `029`, the manuscript's sensitivity-analysis narrative reports:
- HR `1.44`, 95% CI `1.05–1.25` (excluded first three years);
- HR `1.44`, 95% CI `1.03–1.25` (excluded first four years).

Each point estimate exceeds the reported CI upper bound. Both strings were found in PMC body text and the BMJ indexed publisher article body, suggesting a **source-reported numeric inconsistency**, not an Agent extraction error. It may be a publisher typo or downstream presentation problem; the correct numbers cannot be inferred from the other values.

**Disposition:** `SOURCE_REPORTED_NUMERIC_INCONSISTENCY / DEFER_AFFECTED_HR_EVIDENCE_UNIT`. Review original Table 2, supplemental appendix 9, source corrigenda and publisher/author clarifications before updating any numeric claim. Never silently autocorrect. This event is a strong candidate for an error-detection scientific benchmark, provided it is separated from the confirmatory Gold test.

Registry: `P0_1_A_1_Source_Numeric_Integrity_and_Version_Events_v0.1.json`.

## 4. Evidence/version relationship resolution

| Document | Related authority | Supported relation | What remains open |
|---|---|---|---|
| 004 RCT | ChiCTR2000029797 | trial registry explicitly cited in journal source | independently fetch trial registry record; compare prespecified outcome |
| 029 cohort | NutriNet-Santé 031 cancer source | shared prospective cohort family; outcomes differ | quantify participant overlap and follow-up windows |
| 048 network meta | BMJ `10.1136/bmj.r1737`, PMID 40825602, dated 2025-08-18 | actual published author-affiliation correction | attach versioned original article/PDF checksum; no outcome modification inferred |
| 071 Academy EBPG | official EAL Adult Weight Management + Recommendation Summary | journal report is abridged; EAL official recommendation labels verified | immutable full guideline/score/evidence hierarchy snapshot |
| 096 PN consensus | International PN Summit panel | adapted Delphi best-practice consensus, not formal guideline | complete statement-level voting/attachment and committee provenance |

This is a **typed provisional/fact-scoped lineage result**, not five independently certified StudyIdentity records and not a full versioned knowledge graph. The separate `081` diet-paper correction fixture remains in the wider source-version stress queue, not substituted into first five.

## 5. Expert L4 adjudication packages: REAL WORK NOT REPLACED BY AGENT

Generated `P0_1_A_1_Blind_Expert_L4_Independent_Review_Packets_v0.1.json` with **10 blank reviewer assignments = 5 documents × independent reviewers A and B**, each having 14 required common/type-specific fields. Created researcher-accessible procedure `P0_1_A_1_Expert_Independent_L4_Annotation_Manual_v0.1.md`.

**Observed state:** 0 real expert assignments, 0 submissions, 0 actual adjudications. The packets include source links and questions but deliberately withhold pre-extracted Agent answers and the research-team anomaly alert. In Workbench, task scoped authorization and role isolation still need to enforce this separation. Do not treat a blank review form as a signed L4 result.

L4 cannot be PASS until the source is sufficiently documented, the independent reviewers submit immutable decisions, disagreements are adjudicated, all critical evidence has source-span support, and applicable clinical normative scope is preserved.

## 6. Measured acceptance and non-regression

| Gate | Result |
|---|---|
| PMID/DOI/PMCID identity and complete PMC **body** reads | PASS 5/5 |
| Source-body narrow text anchor | PASS 10/10 |
| Primary publisher/official guidance links | PARTIAL / source-dependent |
| Original PDF/attachment-level hash and visual fidelity | **NO-GO 0/5** |
| Tables, figure data, supplementary source parity | **NO-GO 0/5** |
| Explicit source anomaly handling | PASS: one flagged high-severity issue; correction prohibited |
| Trial/cohort/meta/guideline version relationships | PARTIAL |
| Independent L4 expert qualification | **NOT STARTED 0/5** |
| Production multitype Workbench source loader | **BLOCKED** on baseline reader hardcoded source |
| Gold100 official independent source assignment | **0/100**; NO MUTATION |

**Phase conclusion: `P0.1-A.1_SOURCE_RETRIEVAL_AND_NARROW_SCIENTIFIC_AUDIT_EXECUTED / PRIMARY_DOCUMENT_FIDELITY_AND_L4_NO_GO`.**

If calling this phase “completed”, it is a completed documented *attempt with verified partial successes and scientifically valid NO-GO*, **not** “five fully qualified scientific sources”.

## 7. Next execution requirements, priority ordered

1. Acquire licensed native original PDF (or authoritative structured HTML with verifiable frozen snapshot) and source data/figures/tables/supplements. Verify binary SHA256, source version timestamp, figures and tables cell by cell; store restricted articles in approved private controlled store, only public manifests on GitHub.
2. Immediately adjudicate identified cohort sensitivity HR/CI anomaly against publisher supplemental table, official corrigenda or authors. **Do not fill guessed fixes.**
3. For each source, build versioned `SourceArtifact -> StudyIdentity/DocumentFamily -> EvidenceUnit/Recommendation -> SourceSpan` graph with explicit original and derivative lineage.
4. Implement the multi-source reading adapter with rights-scoped source delivery, original/translation alignment, per-role strict blind and immutable reviewer submissions.
5. Dispatch ten genuine expert A/B forms. Only after both independent submissions and an adjudicator's traceable decision can any L4 scientific Gold status change.
6. Keep all five source cases outside Paper C blinded independent confirmation because these have already been exposed in the Agent/research workflow.

### Auditable artifacts

- `P0_1_A_1_Primary_Document_and_Supplement_Inventory_v0.1.json`
- `P0_1_A_1_Source_Numeric_Integrity_and_Version_Events_v0.1.json`
- `P0_1_A_1_Blind_Expert_L4_Independent_Review_Packets_v0.1.json`
- `P0_1_A_1_Expert_Independent_L4_Annotation_Manual_v0.1.md`
- `P0_1_A_1_Qualification_Gate_and_Adjudication_Status_v0.1.json`
- `P0_1_A_1_Execution_Report_v0.1.md` (this file)

*Evidence provenance:* original PMC articles and Nature/BMJ publisher articles, Academy EAL official recommendation page; PMIDs and external DOIs in the source inventory. Missing binary attachments are logged rather than inferred.
