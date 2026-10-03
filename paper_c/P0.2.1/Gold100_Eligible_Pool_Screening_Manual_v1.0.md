# Gold100 Eligible-Pool Screening Manual v1.0

## 1. Purpose

P0.2.1 defines the prospective rules for creating the source universe from which Gold100 will later be sampled. It does not select the final 100 sources.

The workflow is:

```text
real source discovery
→ candidate record
→ identity/text/version checks
→ StudyIdentity resolution
→ challenge tagging
→ eligibility gate
→ eligible-pool freeze + hash
→ deterministic Gold100 sampling
```

## 2. Candidate unit

The candidate unit is one SourceArtifact. The underlying study is separately represented by a StudyIdentityCluster so that multiple reports from one study are not accidentally treated as independent evidence.

Every candidate receives a stable candidate ID before screening.

## 3. Core source families

Only five core families are used for Gold100 sampling: primary interventional, primary observational, evidence synthesis, guideline/consensus, and companion/secondary.

Stress status is not a sixth source family. It is a prospectively tagged property/selection stratum layered on top of a real source.

## 4. Minimum source identity

Each candidate must have a recoverable canonical identity. Preferred identifiers are PMID, DOI, PMCID, or an official guideline/document identifier. Title-only records without authoritative identity resolution are not eligible.

## 5. Exact source text

Core candidates require an exact worker-visible source-text package that can be content-addressed with SHA-256. Open access is preferred for reproducibility but is not a scientific eligibility requirement if the study team lawfully accesses and hashes the exact text.

Reproducibility tiers:

- A: open/official full text, stable identity, frozen hash.
- B: lawfully accessed full text, stable identity, frozen hash, redistribution may be restricted.
- C: partial/abstract/missing text; only eligible for prespecified insufficiency stress use.

Do not create an incomplete-text stress case by artificially deleting text that is available to the study.

## 6. Evidence cutoff and version

The source must be compatible with the frozen evidence cutoff. Correction, retraction, republication, living-version, or supersession state must be resolved before eligible-pool freeze.

A version problem can be a stress feature; it cannot remain an unaudited provenance defect.

## 7. StudyIdentity

Resolve whether the source is an independent primary report, companion publication, secondary analysis, duplicate/overlapping report, guideline dependency, synthesis dependency, or another resolved relationship.

Accidental duplicate sampling of the same underlying study is prohibited. Multiple reports from the same study may enter only through prespecified companion/secondary or StudyIdentity stress rules.

Unresolved StudyIdentity means HOLD, not ELIGIBLE.

## 8. Scientific object extractability

A normal Core candidate must contain at least one prospectively annotatable scientific object or critical-error opportunity under the R0 contract.

A source need not be difficult for a model. Difficulty is not an eligibility criterion.

Prespecified incomplete-source stress cases are the exception: their scientific value is precisely that the worker-visible text is insufficient and safe insufficiency can be measured.

## 9. Development-set exclusion

All Batch001 sources remain development evidence and are excluded from Gold100 confirmatory evaluation. Near-duplicate or source-specific derivative candidates that recreate the same development case are also excluded from confirmatory sampling.

## 10. Challenge tags

Tags are assigned only from source-grounded evidence and before any AB output is seen. They describe measurable scientific properties, not expected model failure.

Use the frozen Challenge Tag Registry for numeric complexity, causal-language risk, StudyIdentity/dependency, version-chain risk, conflict, recommendation exception, temporal cutoff sensitivity, and incomplete source text.

Every positive tag must carry an auditable evidence reference.

## 11. Conflict tag

Conflict requires a linked source cluster showing a material discordance in direction, magnitude, certainty, population applicability, or recommendation normativity. One source described as controversial without linked evidence is insufficient.

## 12. Screening decisions

Use terminal states ELIGIBLE_CORE, ELIGIBLE_STRESS, ELIGIBLE_CORE_AND_STRESS, or EXCLUDED. Pending states are allowed during construction but cannot remain at eligible-pool freeze.

Every exclusion must use a frozen exclusion reason code. Free-text notes can supplement but not replace the code.

## 13. What screeners must not use

Screeners must not view or use AB0–AB6 outputs, evaluator scores, downstream error rates, or per-source model behavior when deciding eligibility or tags.

## 14. Pool freeze

Before deterministic sampling, every record must have a terminal state, every eligible source must have provenance and StudyIdentity status, every positive challenge tag must have evidence, and the deterministically sorted eligible registry must be SHA-256 frozen.

Sampling starts only from that frozen registry.

## 15. Separation from Gold annotation

Eligible-pool screening answers whether a source may enter the sampling universe. It does not create scientific Gold. Gold A/B annotation begins only after deterministic Gold100 source selection and calibration.