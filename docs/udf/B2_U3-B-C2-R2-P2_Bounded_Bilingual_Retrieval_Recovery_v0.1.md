# B2 / U3-B-C2-R2-P2 — Source-Grounded Bilingual Query Reconstruction, Hybrid Retrieval & Conditional Alignment Recovery

**Status:** PASS_BOUNDED_DEVELOPMENT_EXECUTION / METHOD_SELECTION_AND_R1_QUALIFICATION_HOLD. Base PR65 merge 684ffc221a2c86b1f860f3afa11ecdc9dff1d345. No new model call, no reserved32 dispatch, no scientific mapping or nutrient transfer.

## 1. Execution and method

19 exposed development cases only, original frozen target universe 28,845 and separate FoodOn extension 1,174. Source records retain native label, unparsed aliases, original source locator, artifact digest and reference recipe ingredients. Authored 72 component-level bilingual hypotheses from source terminology only; no reviewer target IDs in lookup rules. The lexicon is local-only, not an authoritative dictionary or general-purpose translation model. Sparse lexical retrieval uses label, alias and definition channels; existing dense label/context ranks are reused for RRF hybrid comparison, with equal original per-case/per-scope caps (not necessarily equal realized counts). No new dense inference. No new target-universe records. Generate candidates and freeze before comparison against the exposed critic reference.

## 2. Actual results

| Method | Pool reference edges / 43 | Cases Hit@12 / 18 | Pool difficult-negative overlap | Pool size |
|---|---:|---:|---:|---:|
| Original FUSION | 4 | 3 | 3 | 2034 |
| Source sparse | 34 | 11 | 39 | 1868 |
| Hybrid | 28 | 11 | 35 | 2034 |
| Sparse + conditional routing | 34 | 11 | 39 | 1868 |
| Hybrid + conditional routing | 28 | 11 | 35 | 2034 |

The positive signal is incomplete Critic reference overlap, not scientific recall/precision. Conditional reranking keeps pool membership. Sparse Top1 positive edges 16→16, negative edges 7→6; Top12 positive edges 27→28, negative edges 27→29. Sparse condition flags 74 edges, of which 6 critic-negative and 0 critic-positive; not independently qualified. Hybrid results mixed. Candidate alignment remains unresolved, all new edges require R1 revalidation. Do not equate dish with ingredient; component relation and conditional direction are questions only. No final method selection, no mapping release, no nutrition-value transfer. Regional-native asset development remains a complementary path; no claim of population-wide gap or country-level equivalence.

## 3. Engineering and replay

Initial source-specific implementation and all original local run directories retained. Public-safe portable v2 uses a hash-pinned private lexicon file and deterministic sorted math.fsum. Initial portable replay reproduced 19 query rows and 228 rank groups, but 72 candidate score rows showed floating-point roundoff differences. V2 replay on seeds 17 and 73 reproduced all three private candidate artifacts byte-for-byte, original rank hashes and query hashes identical, aggregate metrics and conditional report reproduced. New synthetic tests 15/15 on original and on portable v2; prior P1 non-regression 23/23, 127 pinned inputs and 8 frozen outputs unchanged. Initial P1 replay rejected an incorrect output directory; rerun with allowed new directory succeeded without changing verifier.

Public archive contains portable code, synthetic tests, aggregate reports and receipt only. Private lexical hypotheses, source labels, candidate IDs, source packets and per-edge evidence stay local. No reserved32 semantic or outcome access; frozen byte fences checked. GitHub CI is a synthetic check, not a real-data run.

## 4. Reproduction (local authorized data only)

Run in NutriOne workspace with its exact P1 frozen materials. All outputs must be fresh, under the P2 namespace. The private lexicon file is not included in GitHub.

```sh
PYTHONHASHSEED=17 /Users/zhangcd/miniconda3/bin/python -B src/u3r2p2/run_p2_portable_v2.py generate --out runs/B2/U3-B/C2/R2/P2/portable_v2_003 --lexicon runs/B2/U3-B/C2/R2/P2/private/DevelopmentLexicon_v0.1.json --lexicon-sha 846b8baa30a8bd1782cf93876163bdd37d625e169497fe77b007df240804b778
/Users/zhangcd/miniconda3/bin/python -B src/u3r2p2/run_p2_portable_v2.py evaluate --out runs/B2/U3-B/C2/R2/P2/portable_v2_003
/Users/zhangcd/miniconda3/bin/python -B src/u3r2p2/conditional_p2_portable_v2.py generate --parent runs/B2/U3-B/C2/R2/P2/portable_v2_003 --out runs/B2/U3-B/C2/R2/P2/portable_v2_conditional_002
/Users/zhangcd/miniconda3/bin/python -B src/u3r2p2/conditional_p2_portable_v2.py evaluate --parent runs/B2/U3-B/C2/R2/P2/portable_v2_003 --out runs/B2/U3-B/C2/R2/P2/portable_v2_conditional_002
python -B tests/u3r2p2/verify_p2_portable_v2.py
```

## 5. Next gate (inside R2-P2)

Before dispatching reserved32: source-grounded typed qualifiers and entity/recipe role validation; evaluate new edges under full R1 admission without weakening its rules; account for target-specific conditions; choose and freeze a bounded method and candidate budget on development only. Retain sparse-only and hybrid arms; no post-hoc tuning on reserved32. Independent source-first reference review, then separate development validation; still no formal expert Gold. C3/B3/EA-P0 remain HOLD. Do not ask PI to repeat prior review.

[Aggregate development report](../../runs/B2/U3-B/C2/R2/P2/portable_v2_001/P2DevelopmentReport.json) · [Conditional report](../../runs/B2/U3-B/C2/R2/P2/portable_v2_conditional_001/P2ConditionalReport.json) · [Admission receipt](../../runs/B2/U3-B/C2/R2/P2/P2DevelopmentAdmissionReceipt.json).
