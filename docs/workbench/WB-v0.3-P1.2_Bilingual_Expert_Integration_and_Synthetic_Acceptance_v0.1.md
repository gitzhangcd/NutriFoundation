# NutriFoundation Workbench v0.3 — P1.2 implementation and acceptance

**Stage**: WB-v0.3-P1.2｜Production-Grade Bilingual Reader, Expert-Native Judgment Adapter, Cross-Language Evidence Fidelity & Synthetic Pilot Readiness

**Development branch**: `workbench-v0.3-p1.2-source-translation-judgment`  
**Base**: `workbench-v0.3-p1.1-bilingual-integration` (P1.1 PR #20)  
**Scope**: restricted synthetic engineering. **Not** live NDS-R1 scientific capture, licensed expert enrollment, production security accreditation, signed human translation qualification, clinical advice or Gold construction.

## A. Scientific translation / source contract

New components:

- `c2_1/translation_contract.py`: versioned source/document SHA, PDF SHA, unit SHA and exact UTF-16 source ranges; reject any stale/ambiguous/wrong original; distinguish `FULL_UNIT` from `SOURCE_EXCERPT_ONLY`; count true whole-unit coverage; warn numeric mismatches, without purporting semantic equivalence.
- `c2_1/translation_prepare.py`: offline local-only pack preparation from exact canonical source + `unit_id→Chinese` mapping; explicit `--synthetic-only`. No translation service calls; refuses overwrite; permissions 0600. Source rights must be approved separately.
- `c2_1/bilingual.py`: P1.1's three illustrative excerpts compiled through the strict schema; backward compatible for current synthetic browser.
- `c2_1/secure_reader.py`: `/translations` can read a locally provisioned **private** manifest at `<working-data-root>/translation_sidecars/<document_id>.json` after task authorization and original PDF/Markdown SHA checks. It fails closed if the pack is invalid, never silently falls back to demo data. No public upload endpoint.
- An append-only `TRANSLATION_PROJECTION_DELIVERED` event binds document/translation version and fixture digest once per task+expert. Future changes to translation version or bytes after delivery fail with HTTP 409. **Delivery is not proof that a human actually read it**, and is not yet part of the frozen judgment receipt.

## B. Expert-native judgment without scientific-schema loss

The UI offers an expert-friendly quick-entry composer for one original statement at a time, with **explicit expert-selected** categories (facts, missing information, currently acceptable actions, uncertainty, rationale, monitoring). The string is written to the corresponding canonical array. No LLM infers or rewrites medical judgment. Existing 19 paths remain present and validated; detailed `reference_set` categories are accessible in an advanced foldout, not discarded.

The adapter `d0/web/expert_native.js` verifies 19 unique canonical fields, preserves untouched fields and rejects unknown fields or multiline entries that could be split ambiguously by the current array form. Source provenance types beyond existing FieldAnchorBinding are **not yet versioned scientific sidecars**, and ad-hoc freeform multi-paragraph semantic mapping is **not claimed**.

## C. Cross-language fidelity

- Original English text selection now obtains the **actual selection Range UTF-16 offsets**, not the first occurrence of a matching quotation.
- Typed English quote fallback refuses ambiguous repeated matches.
- Chinese selected text is *not* saved as an original SourceAnchor. It maps to the authorized versioned original `SOURCE_EXCERPT_ONLY` or `FULL_UNIT` scope; the server still verifies exact quote offset and hash.
- `FULL_UNIT` may not claim more precise alignment than the source unit; precise PDF BBox is only displayed after separate PDF resolver verification.
- Reader shows translated unit coverage and the **unverified** translation version. Numeric/semantic review flags do not imply approval.
- Independent source scope: R0/R2 authorized full source, R1 only permitted candidate excerpt projection; R1 full bilingual endpoint rejected.

## Private synthetic full-unit translation example

Use a **disposable** test fixture data directory, not the existing user workspace:

```bash
# Offline, from authorized local files and a synthetic canonical source only.
python apps/workbench/c2_1/translation_prepare.py \
  --document /PRIVATE/SYNTHETIC_CANONICAL.json \
  --translations /PRIVATE/SYNTHETIC_ZH_UNITS.json \
  --output /PRIVATE/D0_DATA/translation_sidecars/DOC_ID.json \
  --version WB-UX-SYN-PACK-001 --synthetic-only
```

The source document ID in the filename must match the loaded authorized document. `SYNTHETIC_ZH_UNITS.json` is a JSON object mapping immutable `unit_id` to translated text. Untranslated units remain visible in English; they are **not counted as translated**. Existing P1.1 demo excerpts remain fallback only where **no** operator-provisioned pack exists.

## Verification matrix (not equivalent to formal sign-off)

| Gate | Test | Pass condition |
|---|---|---|
| Source identity | doc/pdf SHA, unit raw hash, UTF-16 span | All exact; invalid pack 409 |
| Coverage honesty | optional full-unit private pack | n/N complete units reported, others untranslated |
| Translation QA | numeric mismatch and review status | warnings; no self-verified scientific approval |
| Translation isolation | R1/other role/cross-arm, cache | denied; no sensitive bytes |
| Exposure logging | first projection delivery, version swap | one audit event, no silent version replacement |
| Expert-native map | category entry, save, reload | exact 19 canonical keys preserved |
| English selection | repeated quote and UTF-16 | source range is selection-specific |
| Original PDF | native PDF.js BBox | hash and resolver before highlight |
| Freeze and source audit | existing C2 controller | baseline tests and browser replay green |
| Real-person pilot | credential/consent/ethics/source rights | **NO-GO pending independent evidence** |

## Synthetic usability plan S1–S8

1. S1: four reading modes and untranslated English fallback.
2. S2: paragraph-level translation pack, coverage label and source binding.
3. S3: select Chinese and confirm bound original text, correct precision.
4. S4: select identical English phrases in different positions and verify offsets independently.
5. S5: expert quick-entry to facts/missing information/actions/uncertainty; inspect advanced taxonomy.
6. S6: save/reload and unsaved-entry conflict; ensure precise original wording remains.
7. S7: hash-mismatch and post-exposure translation replacement failure, R1 leak denial.
8. S8: read-only independent freeze, R2 post-AI separation and audit chain.

Suggested 2–3 independent domain experts only **after** required institutional approvals, privacy and professional-credentialing and separate synthetic-case determination. Until then, conduct researcher-only synthetic QA; do **not** count those as expert Gold labels.

## Scientific/operational gates remaining

1. Full clinical scientific translation is **NOT GENERATED**. Only architecture to receive private, versioned unverified unit translations has been implemented; the demo contains three excerpts. Obtain appropriately authorized source packets, translate, independently evaluate numerical and semantic fidelity, and freeze qualified versions separately.
2. Expert-native source-type / uncertainty sidecars and standalone Expert Native → Canonical semantic loss testing need further work before claiming unrestricted freeform input. Current explicit categories preserve 19 canonical fields.
3. Immutable translation-exposure linkage inside the judgment freeze receipt remains a separate backend-contract delta; delivery is currently append-only auditable but **not** included in the scientific snapshot.
4. R2 workpack case `D2-NHANES-L-0001:r3` vs frozen view `r2` conflict remains unresolved.
5. Real IdP/MFA, credential verification, institutional ethics/consent, source rights and production TLS/supported OS/security acceptance remain unmet.
6. All changes must remain on isolated branches until the code review, CI, manual usability review and independent scientific-owner permissions pass.

**P1.2 scientific disposition:** ENGINEERING IMPLEMENTATION UNDER REVIEW; qualified bilingual reading and real expert pilot **NOT YET APPROVED**. CI results must be appended after execution, not presumed.
