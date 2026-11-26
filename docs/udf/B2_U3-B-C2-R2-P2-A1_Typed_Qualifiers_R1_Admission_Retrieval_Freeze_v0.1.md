# R2-P2-A1 | Typed Food Qualifier Validation, New-Edge R1 Admission & Retrieval Policy Freeze

**Status:** PASS_BOUNDED_TYPED_QUALIFIER_AND_R1_POLICY_REEVALUATION / RETRIEVAL_EXPERIMENT_FROZEN / SCIENTIFIC_AND_NEW_RUNTIME_ADMISSION_HOLD.

Base: PR66 HEAD 3703e0b87f26843dc3feb6cb319e73295c0d65c8, stacked on merged PR65. This is one bounded development execution; it is not a formal scientific mapping release.

## Actual data and identity closure

19 source records (11 ingredient / 8 recipe reference), 2,999 distinct native targets, 4,500 distinct source-target edges from 7,007 arm-level rows. Of 4,500, 2,427 prior R1 edges exactly reproduce the original policy evaluations and target/scope identities; 2,073 are new. Source native records, alias records, context locator, raw source and query identities checked; target labels, native identity, raw standard locator and verified scope bound to immutable records. 212 input digests rechecked. The original full R1 verifier replayed 76,473 objects, 35,710 risk records and 656 query decisions, 52/52 checks; report byte-identical to historical R1 validation report. Existing 7 development-review-only edges elsewhere in original R1 are unchanged.

## Typed records

Separate source and target qualifier records: native identity and grain, species/edible-part mentions, processing and cooking state, native state metadata, source-origin and negation, peel, product form, reference recipe components, aliases and residual. Distinguish native label mentions, bilingual hypothesis, unknown, not expressed and reference recipe (not physical composition). All 19 source native food_state values unresolved. 4 source species hypotheses, 2 edible-part hypotheses, 3 native processing mentions, 2 cooking-state mentions, 8 reference recipe components. No taxonomic identity or nutrition value inferred from these. Raw target identity and locator verification does not establish equivalence.

## R1 policy re-evaluation

| Population | Distinct edges | R1 unresolved | R1 explicit conflict | R1 scope/role hold | Policy review eligible |
|---|---:|---:|---:|---:|---:|
| All | 4500 | 4458 | 39 | 3 | 0 |
| Prior | 2427 | 2395 | 29 | 3 | 0 |
| New | 2073 | 2063 | 10 | 0 | 0 |

New final disjoint dispositions: 2003 unresolved, 60 additional typed/inherited risk holds, 10 explicit conflict. There are 62 typed flags among new edges, including overlap with explicit conflicts. No actual new runtime concept-review authorization: new proposals have no original VerifiedGate identity; do not fabricate a VerifiedRiskOverlay with a fake historical parent. All mapping, nutrient transfer and equivalence stay HOLD/UNRESOLVED. Full original R1 risk function invoked unchanged; new endpoint/qualifier checks and a separate audit record do not silently change the R1 ontology or runtime contract.

## Fixed development comparison

| Arm | Pool overlap /43 | Hit@12 /18 | Top12 supported edges | Top12 Critic-negative overlap |
|---|---:|---:|---:|---:|
| BASELINE_FUSION | 4 | 3 | 3 | 1 |
| SOURCE_SPARSE | 34 | 11 | 27 | 27 |
| SOURCE_SPARSE_CONDITIONAL | 34 | 11 | 28 | 29 |
| SOURCE_SPARSE_A1_RISK_TAIL | 34 | 11 | 27 | 26 |
| HYBRID | 28 | 11 | 26 | 25 |
| HYBRID_CONDITIONAL | 28 | 11 | 26 | 28 |
| HYBRID_A1_RISK_TAIL | 28 | 11 | 26 | 23 |

Risk tail stable partition retains every edge and cap, marks 187 of 4,500 edges (39 explicit, 3 scope/role, 145 typed/inherited residual); overlaps 7 Critic negative, 0 Critic positive. These counts are incomplete reference overlap, not precision or validated safety. Prior P2 sparse pool size 1,868 vs baseline/hybrid 2,034; same caps, different realized counts. A1 risk sorting is dev-only; no claim that it generalizes.

## Reproducibility and method freeze

24/24 synthetic A1 tests, 52/52 inherited R1 tests; 4/4 private A1 output artifacts byte-identical across independent runs, complete A1 receipt byte-identical, 212/212 inputs unchanged. New retrieval-only runner accepts an explicit trusted source packet with native records + prior rank hints, never reviewer results; first19 independent-input replay reproduces all 228 rank groups and 19 query hypotheses byte-for-byte. 72-entry dev lexicon remains private; not validated bilingual dictionary. No new models or external calls.

Freeze sparse primary, original fusion and hybrid comparators, exact code, source lexicon, native universes, target versions, cap rule and evaluation protocol. This freeze is only the prospective retrieval experiment; full scientific semantic qualification and new runtime admission remain HOLD. Risk-tail and previous conditional arms not selected as generalizable methods. No further optimization on reserved32. Primary metric original-universe case Reference-Hit@12; all K and pool counts retained, separate extension and non-RELATED sensitivity. Independent reviewer and source-first packet must be authorized, independent access/rights demonstrated, controller retrieval artifacts frozen before outcomes exposed, and native/evidence validation before comparison. Reserved32 source/reviewer packet not parsed for this run (byte digests checked only); frozen existing upstream R1 full replay includes original historical baseline, not a new reserved32 evaluation. Source-only program allowlist is not OS isolation. No reviewer dispatch or actual 32-case results. No new expert Gold, MappingRelease, B3 or C3. Detailed contract in the policy freeze JSON.

## Reproduction

Authorized local workspace only, fresh output paths. Full R1 replay uses original pinned execution profile + receipt and original expert packet (synthetic tests, no actual expert dispatch). Run A1 generation with hash-pinned profile, then comparison with exact freeze digest. Source-only prepare-dev projects first19 without reviewer outcomes; source-only run requires trusted packet SHA. Private per-edge records and packets stay local; public archive contains portable code, aggregate report and receipts only.

- `src/u3r2p2a1/run_a1.py`
- `src/u3r2p2a1/source_only_retrieval.py`
- `tests/u3r2p2a1/verify_a1.py`
- `configs/udf/u3r2p2a1/A1_Profile_v0.1.json`
- `configs/udf/u3r2p2a1/RetrievalPolicyFreeze_v0.1.json`
- [Development report](../../runs/B2/U3-B/C2/R2/P2/A1/dev_001/A1DevelopmentReport.json)
- [Admission receipt](../../runs/B2/U3-B/C2/R2/P2/A1/A1AdmissionReceipt.json)

Next: within R2-P2, reserve32 controlled source-only retrieval execution and independent review preparation under the frozen policy, then validated comparison. Do not substitute review candidates for qualified experts; no scientific release.
