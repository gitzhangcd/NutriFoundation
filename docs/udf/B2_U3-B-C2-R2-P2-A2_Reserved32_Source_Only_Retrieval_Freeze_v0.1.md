# R2-P2-A2｜Reserved-32 Source-Only Retrieval, Independent Reference Construction & Generalization Validation

**Status: PASS_LOCAL_SOURCE_VERIFICATION_AND_FROZEN_RETRIEVAL / INDEPENDENT_REFERENCE_AND_GENERALIZATION_HOLD.**

Base PR66 HEAD 961f83aa247932bcfee5b16affafdd90841ef236; A1 policy SHA256 58c53ab63cf4ac25d030d78e03dcdded8a51fb5a5802e7623ee75bd93af5ddc6. No changes to the frozen lexicon, retrieval algorithm, standards, target universe or budget. No external model call or independent reviewer dispatch.

## 1. Real source-only preparation

32/32 original source records verified against pinned native vocabulary and QueryContextRecord plus two actual SHA-verified NutriData XLSX originals; exact native key, original row, source label, raw alias and reference ingredient names agree. Four originally fixed strata, eight per stratum (16 ingredient, 16 recipe). Zero source ID and review ID overlap with first44. 3,875 original frozen rank hints, 128 case/scope groups. 221 input file digests unchanged. The entire sample shares the NutriData source family and the original dense baseline was previously generated for all 284 queries. No claim of external dataset validation or historically unexposed model knowledge.

All 32 source records have NUTRIDATA_RIGHTS_UNRESOLVED. Bounded local CURATION_DEV under the existing local access scope only. Independent use, external model processing, commercial use, redistribution and actual evaluation release remain gated. No raw records, queries, rank hints or reviewer materials uploaded to GitHub.

## 2. Frozen real retrieval (pre-reference)

Unchanged A1 source-only runner, 32 queries × four scopes × three arms = 384 groups. Two independent processes with PYTHONHASHSEED=17 and 73 yield two identical output files; 32 query hypotheses and 384 rank lists. The unchanged runner requires fresh output under the A1 namespace, so A2 retrieval outputs live at A1/reserved32_retrieval_001 and _002; A2 controller receipt binds both. No reviewer result parsed, no refitting, no new inference.

| Arm | Original universe cases with any candidate | Original pool edges | Original Top12 edges | Empty original scope groups /96 | Extension pool edges | Extension cases with candidates |
|---|---:|---:|---:|---:|---:|---:|
| BASELINE_FUSION | 32 | 3236 | 1152 | 0 | 639 | 32 |
| SOURCE_SPARSE | 23 | 2367 | 828 | 27 | 379 | 20 |
| HYBRID | 32 | 3236 | 1152 | 0 | 639 | 32 |

14/32 queries have identity tokens, 16/32 label hypotheses, 8/32 alias tokens, 15/32 recipe component tokens; 32/32 have untranslated residual. These are pre-reference coverage diagnostics, not scientific recall or accuracy. No supported-reference denominator or actual generalization performance is available. Preserve empty groups; do not tune 72-entry lexicon or rank on this sample.

## 3. Review packet prepared, dispatch HOLD

Local private staging contains exactly nine allowed files (52,736,143 bytes): original 32-case source-only packet, existing response schema, prior independent audit protocol, normative UDF v2.1, four fixed standard files, A2 task. Byte hashes verified, owner-only file modes 0600; no candidate results, prior development answers, private lexicon, dense rank hints or full raw NutriData workbooks in staging. Reviewer unassigned. This is not independent OS-level access isolation, a rights clearance or provider dispatch authorization.

Task requires source-first search of FoodOn 2026-09-20, FDC SR Legacy 2018-04, and FNDDS 2015-16; up to 3 supported candidate proposals and 3 difficult negatives per standard per case, eight source dimensions, explicit unknowns, directional typed relations, actual native labels and exact source locators, actual exposure and search disclosure. No forced mappings. Required four outputs: ExecutionManifest.json, ReviewRecords.jsonl, ReviewReport.md, CriticFreezeReceipt.json. All 32 cases must be retained even if unresolved.

Before reviewer dispatch, PI/data custodian must identify authorized reviewer, resolve intended use and access permissions, and verify reviewer isolation. An external model or subscription interface is not automatically authorized to receive the source packet. A1 freeze requires actual ACL proof, not owner-only directories or self-report. Independent source-first reviewer may be a qualified human or a separately authorized AI critic; AI critic result is never qualified expert Gold. Confirmatory blindness may not be claimed without evidence. Controller checks frozen output identities, response schema, actual source and standard evidence, version/key/label/locator; FNDDS dual carrier exception only via independent exact CSV/same-cycle ARS addendum, original reviewer bytes unchanged. Explicit comparison authorization after reference freeze required. No actual response or outcome access this round.

## 4. Prespecified scoring core

Added pure scoring module; it does not read real outputs, dispatch a reviewer, or authorize comparison. It requires complete case identities and frozen rank groups, separates original and extension, calculates per-case reference-hit@1/3/5/12 and pool, supported target overlaps, difficult-negative overlaps, counts of unreviewed and reviewed-but-neither-supported-nor-negative candidates, out-of-universe supported references, paired primary-vs-comparator Hit@12 results and non-RELATED sensitivity. The latter keeps excluded reviewed edges distinct from truly unreviewed. Reference-case denominator is cases with at least one supported target in each domain; zero denominator yields null. No incomplete result accepted as 32-case evaluation. Scoring core assumes references already validated; actual authorized import and qualification gate still to execute. No new performance claim from synthetic tests.

## 5. Engineering evidence and reproduction

18/18 new synthetic tests passed. Original A1 runner and policy SHA unchanged; pre-reference receipt and raw source verification actual. Controller preparation and retrieval hashes retained locally. Public archive contains code, aggregate report, test and summary receipt only.

Local runs, new dirs required:
- `src/u3r2p2a2/prepare_a2.py prepare --out runs/B2/U3-B/C2/R2/P2/A2/local_001`
- unchanged `src/u3r2p2a1/source_only_retrieval.py run --packet <private packet> --packet-sha <trusted hash> --out <fresh A1 run>` (seeds 17 and 73)
- `prepare_a2.py summarize --out <A2 run> --prep-sha <trusted preparation hash> --retrieval <first run> --replay <second run>`
- `python -B tests/u3r2p2a2/verify_a2.py`

Next: A2 independent reviewer authorization, controlled source-only review and verified reference freeze; only then separately authorized comparison. Source rights and actual reference qualification remain open. C3/B3/EA-P0, scientific mappings and nutrient transfer remain HOLD. No new task-number expansion or development tuning on reserved32.
