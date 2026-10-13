# GOV-0.4-P0｜Nutrition Foundation v0.1 对 SIS / SIS-Med / AI Nutri 的静态符合性审计

> **日期**：2026-10-13  
> **适用范围**：仅检查 GOV-0.3 私有归档的 4 份精确 Markdown 字节版本和原文；不访问真实专家记录或临床患者，也不等于 full runtime/empirical conformance。  
> **审计性质**：`SCOPED_STATIC_SEMANTIC_AUDIT / NOT_SCIENTIFIC_OWNER_SIGNOFF`。  
> **机器矩阵**：[15-axis JSON Matrix](GOV-0.4-P0_NDSF_Three_Master_Static_Conformance_Matrix_v0.1.json)  
> **原始归档与哈希**：[GOV-0.3 Manifest](GOV-0.3_Controlled_Original_Materials_Manifest_v0.1.json)。  
> **工程状态**：合成工程 7/25 不变；不修改任何 frozen scientific/master/runtime、无真实专家/Gold/生产放行。

> **版本裁决修订｜2026-10-13（GOV-0.4-P0 Amendment 0.1.1）**  
> 经科研项目负责人明确确认：**临床营养仅以 SIS-MED v0.3.1 R6 P0.4 作为当前 SIS-MED 规范权威**。此前归档的 SIS-Med R5-L1 仅是**历史语义参考**；其任何“相容/一致”字样都**不得解释为 R6 符合性通过**。目前 R6 P0.4 指定 61,116 字节 / SHA-256 `f8513b600ea7a2266d56159df7f3cb1a71dd9b6b11d40721d49430da95e4b335` 原件仍未取回。因此 **R6 条款级比对 NOT ASSESSED**，`CURRENT_CLINICAL_R6_CONFORMANCE=NO_GO`。下列对 R5-L1 的内容比较一律降格为历史 context / delta discovery，不计入正式临床规范符合性。


## 0. Executive finding

**结论：Nutrition Foundation v0.1 在 SIS R5、AI Nutri v2.1 及已归档历史医学文献的部分共享科学语义上没有发现直接的核心矛盾；但由于当前 SIS-MED 权威是 R6 P0.4 且原件尚缺，**临床 R6 合规性未评估**，更不能称已通过三份规范的正式符合性验收。**

形式上需要区别：

```
SIS v0.3.1 R5  --common science-->  Nutrition Foundation v0.1
                                  ├--> general nutrition profiles
SIS-MED v0.3.1 R6 P0.4  ----------┘--> clinical nutrition profiles [ONLY CURRENT SIS-MED AUTHORITY]

Nutrition Foundation  --domain foundation proposal/adapter--> AI Nutri v2.1
AI Nutri v2.1  --project R0–R8 / scientific evidence / benchmark--> implementation and experiments
```

第三个（AI Nutri v2.1）是**项目下游 scientific domain/research specification**，不能与母规范 SIS 在逻辑优先级上简单并列。所有“通过”都需准确标注为何种证据；设计字段一致不等于数据契约、专家参考、临床安全或自动 CI 已实际合格。

## 1. Exact documents actually compared

| ID | Precisely audited original | Bytes | SHA-256 |
|---|---|---:|---|
| NDSF | `Nutrition_Foundation_v0.1_Integrated_Master_Specification.md` | 145,696 | `81426a9423f825681a155b748643ebd9f3b6d992b67304d35e94abd9f9ca90ce` |
| SIS_ALT | `System-Intelligence-Science-v0.3.1-R5-Regenerated-Master-Specification.md` | 149,590 | `f7dff71e2c5973f75a7f83c77f189b6d605c5f1ea50f738506e0d115a857c44d` |
| MED_ALT (**historical-only, non-authoritative**) | `SIS-Med-v0.3.1-R5-L1-Regenerated-Master-Specification.md` | 117,927 | `d3de50276e481311cb9f86ab5e68f94b141bf294c4ce67d90efe2ffddd868955` |
| AI_NUTRI | `AI_Nutri_v2.1_Aligned_Master_Specification.md` | 189,759 | `06a50bca0951e697f47793dad982d18b5ddcf2062ef856d16150708fc2f61d5b` |

**Important**: NDSF Integrated Master Part VIII (§2187–2205) pins a DIFFERENT exact R5 source `181565 bytes/3e1da79a...` and SIS-MED **R6 P0.4** `61116 bytes/f8513b60...`. Those target originals are **not available** among the four byte-verified archives. The archived MED R5-L1 master is an **earlier different edition**, not the science authority explicitly cited by NDSF. Therefore formal exact version conformance remains blocked even when individual scientific rules align.

## 2. 15-axis findings

| # | Check | NDSF clause(s) | Primary comparison clauses | Scoped disposition |
|---:|---|---|---|---|
| 01 | Upstream hierarchy, clinical applicability | NDSF 60–74, 137–169 | AI 209–245; historical MED 233–253 | **R6 authority confirmed; R6 conformance NOT ASSESSED** |
| 02 | No Core primitive / Program / Experiment schema inflation | NDSF 1–11, 184–197, 1744–1823 | SIS 60–78, 1675–1829 | **Aligned** |
| 03 | Observation≠state≠diagnosis, unknown/masked provenance | NDSF 336–397 | SIS 658–694, AI 565–775 | **Aligned** |
| 04 | Scientific knowledge vs individual information; anchors, applicability | NDSF 399–448, 525–536 | AI 825–1107, 1585–1709 | **Thin interface aligned; adapter binding pending** |
| 05 | Information sufficiency, conditional action, scoped safety veto | NDSF 970–1120, 1392–1421 | SIS 3760–3845, AI 1843–1929 | **Aligned in text** |
| 06 | Expert-native → canonical, Human–Ontology separation | NDSF 489–536, 1300–1382 | SIS 3383–3675, MED 4168–4251, AI 3923–4019 | **Aligned in text** |
| 07 | Set-valued reference and retained uncertainty/adjudication | NDSF 1422–1545 | SIS 3890–4058, AI 3948–4019 | **Aligned in text** |
| 08 | Strict exposure, time/visibility and hindsight non-leakage | NDSF 722–782, 1174–1236, 1694–1715 | SIS 3559–3639, MED 2297–2338, AI 4022–4060 | **Aligned semantics; implementation untested** |
| 09 | Monitoring, adherence, transition, redecision; avoid false longitudinal data | NDSF 1556–1743 | MED 1490–1567, AI 4091–4147 | **Aligned base semantics** |
| 10 | Advanced clinical LHDI semantics | NDSF 1605–1689, 1756–1797 | Historical R5-L1 only; R6 source missing | **Historical hints only; R6 exact requirements NOT ASSESSED** |
| 11 | Estimand-first routing, CSCI and boundary axes | NDSF 1798–1887, 1940–1949 | SIS 1411–1549, 1675–1829, AI 4370–4431 | **Aligned in text** |
| 12 | SIS R5 capability-localization status | NDSF 199–207, 1746–1754, 2187–2205 | Actual SIS R5 alternate entire file | **Exact source revision mismatch; target raw missing** |
| 13 | SIS-MED R6 P0.4 vs archived R5-L1 | NDSF 60–74, 137–169, 2187–2205 | R5-L1 historical only | **SIS-MED R6 P0.4 SOLE AUTHORITY; compliance BLOCKED pending exact R6 original** |
| 14 | AI Nutri v2.1 ⇄ NDSF authority/adapter binding | NDSF 199–205, 2041–2058, 2187–2205 | AI 1–26, 209–245, 3841–3882 | **Missing formal binding; no reason to rewrite Core** |
| 15 | Physical contracts, pilot, source/real expert validity, release tests | NDSF 1908–1985, 2077–2140, 2221–2229 | MED 131–175, AI 7–17, 5039–5063 | **Not executed** |

Status interpretation: “Aligned” means the relevant document passages preserve a compatible meaning; it is **not** a complete enumeration of every sentence, machine schema proof, independent scientific non-regression or downstream runtime attestation.

## 3. What is genuinely compatible

### 3.1 SIS common science

NDSF keeps `ScientificCoreDelta=0`, `ProgramArchitectureDelta=0`, `CoreExperimentSchemaDelta=0` (header and I/P4). It distinguishes case referent from SIS system state, records measurement uncertainty and mask separately, and refuses to assign a program from names or workflows. The `NutritionSISAdapter` remains a **domain interpretation tool**; the independent `ProgramClassification` determines claim-level SCF / SDR / ASR based on estimand and scientific conformance. This tracks SIS R5 §40–44, §51–57 and its thin-framework principle.

It also handles SIS R5 human/reference invariants: `ExpertJudgment != LatentTruth`, `Reference != LatentTruth`, `ExpertAgreement != Validity`, `DecisionQuality != RealizedOutcome`, no ex-post hindsight, and set-valued acceptable actions. No direct contradictory invariant was found in those scoped sections.

### 3.2 Archived SIS-Med R5-L1 — *historical* clinical concepts, not current compliance

The archived R5-L1 clinical Master explicitly separates clinician-native elicitation, research semantic mapping, reference adjudication, human role, bounded safety, allowed actions and temporal lineage. NDSF P0/P2/P3 has direct counterparts: unmodified expert judgments, risk and veto scoped per action/plan, independent qualified reference, source/time/visibility, monitoring, authorization vs actual execution, and no synthetic trajectory disguised as real data.

**This is NOT any certification of current SIS-MED R6 clinical conformance:** R5-L1 includes specialized `ClinicalBeliefState`, `AuthorityState`, long-horizon irreversibility and option-space closure / sequential identification (§1157+, §1505–1567, §4352+, §5361+). NDSF does not assert exact field-level implementation of these named contracts. For clinical tasks **that invoke these constructs**, require a loss-aware `ClinicalNutritionProfile`/adapter binding, negative tests and clinical scientific owner review. For general nonclinical nutrition, do not force all high-risk LHDI objects into NDSF common Core.

### 3.3 AI Nutri v2.1 is compatible as a project downstream

AI Nutri v2.1 §2 and §109–132 defines an extensive scientific evidence ecosystem (SourceArtifact/EvidenceUnit/EvidenceSynthesis, temporal knowledge, evidence qualification), nutrition decision system, benchmarking, training/presentation and release governance. NDSF deliberately stops at **thin shared nutrition semantics** and refers detailed scientific evidence objects to its then-received AI Nutri v2.0 annex, rather than duplicating all of R2.1.

Concepts such as observation/state separation, conditional action and safety, expert-native judgment, set-valued reference, provenance and finite suitability, monitoring, causal claim gate, versioning and leakage prohibition remain directly mappable. However **none of this establishes that the exact downstream v2.1 fields/schemas and its R0–R8 architecture have been bound to NDSF v0.1**.

## 4. Four highest-priority deltas

### D-01｜SIS R5 exact snapshot is not the archived copy (P0 SOURCE)

- NDSF Part VIII §2187–2205: expects SHA256 `3e1da79a...` / 181565 bytes, with reference to `Part VII-A capability-localization PROPOSED NORMATIVE PATCH`.
- Actual archived SIS R5 (SHA256 `f7dff71e...` / 149590 bytes) **does not contain** a `Part VII-A` heading, `PROPOSED NORMATIVE PATCH` phrase or `capability-localization` section.
- This is **conclusive revision/source mismatch**, not proof that NDSF adopted a false scientific concept. NDSF conservatively declines to force the proposed patch, which is a reasonable non-inflation position. The exact source must be recovered before a formal “SIS R5 complete” certificate.

### D-02｜SIS-MED R6 P0.4 is the **sole current clinical authority**; R5-L1 is historical only (P0 CLINICAL)

- NDSF Part I §137–169 states the clinical profile must satisfy SIS R5 **and** SIS-MED R6 P0.4 **and** NDSF.
- The available R5-L1 source predates R6 and differs in hash/version; matching its semantics **must not be scored as clinical normative conformance**. It is historical context only, not a fallback authority.
- Exact R6 original + explicit clinical applicability + domain adapter/safety/clinician qualification need independent binding. This does **not** block nonclinical research with suitable scope.

### D-03｜NDSF v0.1 has no explicit alignment to AI Nutri v2.1 (P1 DOWNSTREAM)

- NDSF Part VIII §2187 states that **AI Nutri v2.1 had not been supplied** when NDSF was integrated; it inherits detailed evidence ecosystem object contracts from **AI Nutri v2.0**, not v2.1.
- AI Nutri v2.1 §2/§109 declares SIS R5 and SIS-MED R6, but has **no text occurrence** of `Nutrition Foundation` or `NDSF`.
- This creates a **bilateral source-of-truth/document dependency gap**, not necessarily a meaning contradiction.
- Fix via a **minimal downstream** `AI_Nutri_v2.1_NDSF_v0.1_Domain_Adapter_and_Conformance_Addendum_v0.1`, not by rewriting NDSF from AI Nutri's corpus/training/R8 design.

### D-04｜Advanced long-horizon clinical specialization remains explicit conditional gap (P1 SCOPED)

- NDSF Part V covers broad monitoring and re-decision correctly; MED R5-L1's long-horizon-specific `ClinicalBeliefState`, `AuthorityState`, irreversible transitions, option-space narrowing/closure and sequential identification require targeted mapping if claiming those clinical capabilities.
- Keep clinical domain extensions and trace origin/authority/temporal semantics; `UNMAPPABLE` must not be silently forced to SIS primitives.
- Presence/absence of a named object is **not** itself a proof of non-conformance for a project that never invokes that clinical subtype.

## 5. Recommended minimal non-regressive action order

1. **Upstream source identity**: recover exact 181565-byte SIS R5 and 61116-byte SIS-MED R6 P0.4; verify SHA-256 and owner ratification separately. Keep the archived alternates as historical proof rather than automatically promoting them.
2. **Downstream domain compatibility companion**: formalize NDSF v0.1 → AI Nutri v2.1 `DomainAlignmentProfile`, record object/field-level `EXACT/CONDITIONAL/UNMAPPABLE`, cases and version impact. Do not alter original scientific meaning.
3. **Optional clinical long-horizon adapter**: for relevant clinical research only, record mappings for clinical belief, authority, irreversible/option closure, timing and risk constraints with actual expert/safety owner.
4. **GOV-0.4 runtime non-regression**: implement and execute selected NDSF NF-F01–F22, P2-F01–F10, P3-F01–F10 plus relevant MED kill tests, with exact input projection/negative fixtures. A specified suite without an execution log is **not** PASS.
5. **NDF/NDS active case gate**: separately resolve the branch's D2 case r3 vs materialized view r2, and NDS workpack v0.1 FreezeContract vs current v0.2 and source snapshot. This was not executed by this document-only audit.

## 6. Final decision and constraints

```text
NDSF vs archived SIS R5 general scientific concepts:       SUBSTANTIALLY_TEXT_ALIGNED
NDSF vs archived SIS-Med R5-L1 clinical rules:          HISTORICAL_CONTEXT_ONLY_NOT_COMPLIANCE
NDSF vs AI Nutri v2.1 project scientific semantics:        CONCEPTUALLY_COMPATIBLE_MISSING_EXACT_BINDING
EXACT SIS R5 locked input conformance:                     NOT_VERIFIED
EXACT SIS-MED R6 P0.4 clinical conformance:                NOT_ASSESSED_NO_EXACT_R6_MASTER
Clinical LHDI exact R6 field/role mapping:                 NOT_ASSESSED_NO_EXACT_R6_MASTER
Physical schema/runtime/Strict-Blind/real expert/Gold:     NOT_TESTED_BY_THIS_AUDIT
NDSF Core rewrite required from this audit:                NO
Formal 'fully conforms to all 3 sources' signoff:          NO
```

This report adds **documentary conformance evidence only**, and MUST NOT grant source copyright approval, clinical effectiveness, real-expert exposure, true Gold status or production deployment. All unresolved GOV-0.2/0.3 scientific and source gates remain open. Original private scientific text was not committed to public GitHub.
