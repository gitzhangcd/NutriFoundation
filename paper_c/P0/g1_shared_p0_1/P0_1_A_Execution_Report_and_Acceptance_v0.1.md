# G1-Shared P0.1-A｜Authorized Full-Text Acquisition, Structural Fidelity & First Five-Source Qualification

**Version:** v0.1 — actual execution and scientific gate  
**Date:** 2026-10-10  
**Baseline:** `54b4c2e`  
**Branch:** `research/gold100-bibliography-candidates-20261009`  
**Decision:** **ACQUISITION (PMC BODY) COMPLETE 5/5 · ANCHOR QA PASS 10/10 · FULL STRUCTURAL AND L4 SCIENTIFIC QUALIFICATION NO-GO**  
**Purpose:** First five heterogeneous sources for *G1-Shared source representation and qualification*, not Paper C blinded confirmatory Gold100.

## 1. Scope and source identity

| ID | Material | PMID | PMCID | DOI |
|---|---|---|---|---|
| CAND-G100-004 | RCT: early vs mid-day time restricted feeding in non-obese volunteers | 35194047 | PMC8864028 | 10.1038/s41467-022-28662-5 |
| CAND-G100-029 | Observational cohort: NutriNet-Santé ultra-processed foods and CVD | 31142457 | PMC6538975 | 10.1136/bmj.l1451 |
| CAND-G100-048 | Systematic review & network meta-analysis: intermittent fasting strategies | 40533200 | PMC12175170 | 10.1136/bmj-2024-082007 |
| CAND-G100-071 | Academy AWM evidence-based guideline abridged journal article | 36462613 | PMC12646719 | 10.1016/j.jand.2022.11.014 |
| CAND-G100-096 | International Safety and Quality of Parenteral Nutrition summit expert consensus | 38869255 | PMC11170495 | 10.1093/ajhp/zxae078 |

**Extra stress fixture, excluded from the primary five:** CAND-G100-081 / PMC12457591 / 10.1038/s44324-025-00084-z, corrected article `10.1038/s44324-023-00002-1`.

## 2. Real acquisition receipts

All five PMID/PMCID identities matched PubMed/PMC. The PubMed PMC OAI service returned 100% of its **article-body text** in the expected contiguous slices:

| ID | Body characters | Chunks | PMC stated rights | GitHub article body stored? |
|---|---:|---:|---|---|
| 004 | 40,271 | 1 | CC BY 4.0 | YES; with credit |
| 029 | 59,562 | 2 | CC BY-NC 4.0 | NO; manifest/links only |
| 048 | 45,559 | 1 | CC BY-NC 4.0 | NO; manifest/links only |
| 071 | 73,139 | 2 | PMC text mining/fair use; no general OA redistribution | NO; manifest/links only |
| 096 | 58,335 | 2 | CC BY-NC-ND 4.0 | NO; manifest/links only |

**Important:** Complete PMC **body text** is not equivalent to a complete primary source PDF, detailed tables, original table geometry, image figures, versioned annexes, supplementary trials, original XML or institutional/full guideline material. A source may have a complete body retrieval but an incomplete scientific source capture. Public redistribution is restricted to separately licensed material. Read authorization and public redistribution authorization differ.

The RCT (`004`) authorized PMC text projection already exists in `source_projections/CAND-G100-004_PMC8864028_PMC_body_CC-BY-4.0.md`, with article attribution. Others have not been published as complete text due to different permissions. Source URLs and PMC retrieval receipts are in the typed task pack.

Attempts to access original 004 PDF through PMC returned 403 and through Nature redirect required unavailable authentication. The full AWM guideline 58-page PDF print queue was not programmatically retrievable in this environment. These are real blockers to a claim of verified original-PDF fidelity, not reasons to substitute an invented PDF.

## 3. Structural fidelity — results and threats

| Fidelity check | Result | Explanation |
|---|---|---|
| PMC body chunks contiguous and length matched | PASS 5/5 | verified 5 bodies, source-side total chars |
| PubMed/PMC authoritative identifiers aligned | PASS 5/5 | PMID/PMCID normalized, earlier DOI check |
| At least two exact source-span locations | PASS 5/5 | 10/10 machine-matched phrases, with UTF16 offsets and source ID |
| Original PDF version, page numbers, visual figure/table geometry | HOLD 5/5 | no original PDF render or page-level cross-check |
| Supplemental appendices, study protocol, tabular cell attribution | HOLD 5/5 | manuscript body mentions supplementary materials; not fully captured |
| Independent SHA256 of original PDF / licensed immutable snapshot | HOLD 5/5 | no verified original-document file; GitHub blob SHA for persisted CC BY projection is NOT PDF SHA256 |
| Original-to-Chinese translation alignment | NOT STARTED | translations are supportive only, never authoritative evidence |
| Native five-source Workbench loading | BLOCKED | current reader.js hardcodes `SYN-5-2-PAPER` |

**Therefore:** All five are **body-text-slice-complete / original-document-fidelity-incomplete**. This is not a claim that source tables and figures are correctly parsed.

## 4. Five type-specific narrow scientific QA objects (not Gold)

### RCT 004

- Supported source question: sample/randomization and prespecified primary endpoint.
- Source-body anchors: `RCT_RANDOMIZATION_SAMPLE` at 3332; `RCT_PRIMARY_OUTCOME` at 27402 (PMC body UTF16 offsets).
- Candidate extraction: five-week, three-arm pilot RCT (90 allocated; 82 completed), early TRF vs mid-day TRF vs ad-libitum control; change in HOMA-IR is the primary endpoint.
- Critical scope: healthy participants without obesity; no automatic extrapolation to obesity therapy, all diabetes contexts or long-term clinical endpoints.
- Scientific HOLD: CONSORT and supplementary protocol verification, attrition/bias review, table/figure fidelity and expert judgment.

### Cohort 029

- Supported question: population/exposure/outcome and **association**, not causal intervention efficacy.
- Anchors: sample 105,159 without baseline CVD at 12730; HR/confidence interval calculation at 16409.
- Candidate: observational NutriNet-Santé cohort; prospective UPF–CVD association.
- Numeric estimates and covariate-dependent table rows are **not** final verified EvidenceUnits: full Table 2 cell structure and original-model columns need recovery.
- StudyIdentity: separate NutriNet-Santé cancer-outcome source CAND-G100-031 shares a cohort family, not necessarily the same outcome claim.

### Network synthesis 048

- Source-body anchors: 99 included articles at 13927; GRADE certainty method at 18634.
- Candidate: systematic review / network meta-analysis of intermittent fasting, calorie restriction and ad-libitum comparators. Reconstruct unique *study* identity vs article count, time points, pooled effects and network certainty before full qualification.
- An ADF-vs-CER mean difference of -1.29 kg (95% CI -1.99 to -0.59), moderate certainty, appears in body; **numeric table/forest-plot qualification remains HOLD**.
- VERSION: BMJ original DOI `10.1136/bmj-2024-082007` has an erratum `10.1136/bmj.r1737`, dated 2025-08-18, addressing a coauthor affiliation. The correction does not state that the effect estimates were changed. Record as `AFFILIATION_CORRECTION`, not fabricated numeric correction.

### Guideline 071

- Journal article is explicitly an **abridged report**, not the entire authoritative guideline document.
- Journal-body anchors: abridgement at 2317; use of `Consensus` recommendation grading at 6636.
- Authoritative AWM EAL family: `https://www.andeal.org/topic.cfm?cat=6109&menu=5276`; recommendation index `https://www.andeal.org/topic.cfm?cat=6246&menu=5276`; detailed recommendation page `https://www.andeal.org/template.cfm?key=4888&template=guide_summary`.
- One specific recommendation in EAL: *Provide Medical Nutrition Therapy*, rated `Level 1(B)` and labeled `Imperative`, explicitly scoped to appropriateness and client wishes. Other advice, for example NCP use, may have `Consensus` and `Conditional` labels. Do not recode the grade/label pair as an unspecified binary strength.
- The EAL page lists contraindication/exception screening issues and supporting evidence question links. Preserve exception logic; do not promote generic weight loss advice across eating disorders, pregnancy or chemotherapy without clinical review.
- HOLD: official full guideline recommendations, PDF page/figure and evidence mapping are linked but not independently archived and fully reconstructed. Copyright reserved.

### Expert consensus 096

- Source-body anchors: not a formal guideline committee or authorized voting body at 4360; adapted Delphi technique at 6084.
- Candidate: adult parenteral nutrition safety/quality consensus process, based on panel deliberations informed by evidence and clinical experience.
- Not equivalent to GRADE guideline normativity or randomized-effect evidence certainty.
- HOLD: detailed vote/response denominator, agreement method, contentious statement history and individual statement-level provenance need expert confirmation. NC-ND terms constrain transformed public source exports.

## 5. Study/document relationship register

See `P0_1_A_SourceFamily_and_Version_Links_v0.1.json` for 7 typed links involving RCT registration, the NutriNet-Santé shared cohort, network-meta published correction, Academy journal↔EAL official guideline family, PN consensus process, and the additional correction stress fixture.

**No study merge is formally frozen.** An independent study is not the same unit as an independent SourceArtifact.

## 6. Workbench-ready *data contract* vs executable integration

Produced `P0_1_A_FirstFive_Typed_Source_TaskPack_v0.1.json`, with each source's:

- `scientific_task_kind`, type-specific question and expected reviewer tasks;
- `PMID/PMCID`, original source URI, source link/version/dependency objects;
- 2 authoritative text-only support-span anchor candidates;
- loss-prevention / counterfactual / causal-upgrade guardrails as appropriate;
- source license and whether full text may be persisted or shown;
- explicit `L1/L2/L3/L4` and `NO_GOLD` qualification gates;
- strict-blind rule: independent Gold annotators cannot see Agent candidates.

**Status:** adapter candidate, **NOT a currently executable Workbench production SourcePackage**. `54b4c2e` hardcodes the single source `SYN-5-2-PAPER`. A multi-source per-task registry, rights-scoped document loader, pre-AI exposure enforcement and tested source snapshot/translation binding are needed. The existing NDS-R1 19-field decision task cannot be silently reused as the scientific source-review schema.

## 7. Acceptance decisions

| Gate | Result |
|---|---|
| A1 PubMed/PMC identity | **PASS** |
| A2 Rights-screened PMC body retrieval | **PASS 5/5** |
| A3 Body-contiguity and length | **PASS 5/5** |
| A4 Minimal text-source span exact matching | **PASS 10/10** |
| A5 Type-specific draft claims and scope guards | **PROVISIONAL** |
| A6 Full PDF/HTML figures, tables, supplements, original/source SHA | **HOLD** |
| A7 External study/document version and correction resolution | **PARTIAL** |
| A8 L4 scientific qualification (explicit question-dependent) | **HOLD 5/5** |
| A9 Real expert Gold dual-blind annotation | **NOT STARTED** |
| A10 Production Workbench implementation | **BLOCKED** |
| A11 Paper C official Gold100 regression/contamination guard | **PASS for no mutation** |

**Final outcome:** `P0.1-A_BODY_ACQUISITION_PILOT_EXECUTED / FIDELITY_AND_L4_QUALIFICATION_NO_GO`.

The result is a completed, reproducible **screening and narrow-anchor pilot with a formal blocking decision**, not 5 scientifically Gold-qualified documents. Do not label any of the five as `Gold`, `FullSourceFidelity=PASS`, `WorkbenchProductionReady` or `PaperCConfirmatoryEligible`.

## 8. Next exact phase

`G1-Shared P0.1-A.1｜Primary-Document Fidelity, Original Tables/Supplements, Version Lineage & Expert L4 Adjudication`.

Require: licensed original PDF/native authoritative full guideline, appropriate private source storage & SHA256, table/figure/supplement extraction parity, version/retraction impact, independent study-family confirmation, type-specific reviewer scientific sign-off and sufficient Workbench loader integration. Escalate sources without such items to documented `HOLD`; do not use a PubMed abstract as source truth. For G1-Shared representation experiments, a separate engineering-only `SourceReadiness` state may still allow debugging noncritical text anchors without scientific Gold status.
