# GOV-0.3｜Original Materials, Provenance & Controlled-Archive Report v0.1

> Audit date: 2026-10-13  
> Status: **`9/9 FOUND_ORIGINALS_ARCHIVED_AND_READBACK_VERIFIED / 7 REQUIRED_CATEGORIES_OPEN`**  
> Science/rights status: **`PENDING`**; this is an engineering and evidence-preservation audit, **not** clinical-source qualification or scientific-authority ratification.  
> Source of truth for archived bytes: **personal Library path**, not this GitHub PR. Public GitHub stores only document-safe metadata.  
> Parent: [GOV-0.2](GOV-0.2_Scientific_Authority_Adjudication_Report_v0.1.md) Draft PR #44.  
> Machine-readable record: [GOV-0.3 manifest](GOV-0.3_Controlled_Original_Materials_Manifest_v0.1.json).

## 1. Scope and binding decision

GOV-0.3 covers the **identity, byte-integrity, recoverability and rights/visibility boundary** for original scientific standards, design inputs, review artifacts and later true scientific-source originals. It does **not** change a frozen scientific contract, recreate missing originals from generative text, grant source rights, certify medical claims, or admit any real expert into Workbench.

The local project’s archive root now exists:

`/NutriFoundation/GOV-0.3/Source-Snapshots/` within the user's personal **ChatGPT Library**.

Original Markdown was stored as a copy under the same basename. A second read of the stored Library file was materialized independently and compared **byte-for-byte** to the accessible source; for all nine copies the SHA-256 and file sizes matched. This confirms copies were written and can presently be retrieved through this user’s personal Library; it **does not** independently attest platform IAM, backups, or external organizational approval.

## 2. Real source recovery and archive receipts

| Material | Size in bytes | SHA-256 (full in JSON manifest) | Meaning |
|---|---:|---|---|
| Nutrition Foundation v0.1 Integrated Master | 145,696 | `81426a94...` | Exact preserved logical Master |
| NF-P0 identity + SIS R5 alignment | 71,965 | `d5342e70...` | Matches Integrated Master phase hash |
| NF-P1 exact contracts | 123,940 | `6695fb0d...` | Matches Integrated Master phase hash |
| NF-P2 reference/safety/qualification | 21,093 | `a3068e4d...` | Matches Integrated Master phase hash |
| NF-P3 trajectory/monitoring | 14,080 | `a03975dc...` | Matches Integrated Master phase hash |
| NF-P4 adapter/routing/conformance | 21,576 | `e45ed838...` | Matches Integrated Master phase hash |
| AI Nutri v2.1 Aligned Master | 189,759 | `06a50bca...` | Downstream domain authority only; original available |
| SIS R5 alternative regenerated Master | 149,590 | `f7dff71e...` | **Historical alternative; not target 181,565-byte R5 input** |
| SIS-Med R5-L1 regenerated Master | 117,927 | `d3de5027...` | **Historical alternative; not target R6 P0.4** |

The two previously discovered Drive copies of the 149,590-byte SIS R5 version have equal SHA-256, so only **one unique byte snapshot** was copied to this archive; do not infer equal source-of-truth authority from their equality.

### Specific upstream conflict: do not automatically resolve

1. **SIS R5**: AI Nutri v2.1 source lock records original `05-SIS-v0.3.1-R5-Regenerated-Master-Specification.md`, **181,565 bytes**, SHA-256 `3e1da79a14111d2ead7bc49d47665bc05c1879969b9233fdaa060c2f95436a82`; neither the recovered alternative nor the GitHub `SIS-Main@main` R4-era document meets that lock. Exact original still missing.
2. **SIS-MED R6 P0.4**: AI Nutri v2.1 source lock records `04-SIS-MED-v0.3.1-R6-P0.4-Regenerated-Master-Spec-1-.md`, **61,116 bytes**, SHA-256 `f8513b600ea7a2266d56159df7f3cb1a71dd9b6b11d40721d49430da95e4b335`; the available R5-L1 document is a different scientific edition. Exact original still missing.
3. **Nutrition Foundation**: the Integrated Master includes a Part VIII record of NF-P0–P4 SHA-256 digests. **All five original copies match those exact recorded digests**; technical original preservation is now closed. Scientific owner canonical Git repo/tag ratification remains separately open; **do not upload its entire contents to a public GitHub repo without publication authorization**.

## 3. Workbench design and acceptance originals: unresolved after targeted searches

The following materials were sought by their actual identifiers across currently accessible personal Library, current conversation assets, permitted Drive filename searches and the previously reviewed GitHub trees.

| Required original | GOV-0.3 result | Existing substitute (not the original) |
|---|---|---|
| `NutriFoundation Workbench Development Master Plan v1.1` | **NOT RECOVERED** | `docs/workbench/Workbench_System_Master_v0.2.md` and linked engineering contracts, with different identity |
| `nutrifoundation_p2_scientific_source_portal_demo(1).html` | **NOT RECOVERED** | PR #37–#41 implementation, UX specs and synthetic acceptance; not original HTML |
| `Archive.zip` cited for cloud UI review | **NOT RECOVERED** | Prior human report/synthetic CI claim not equivalent to archived screenshot ZIP |
| Actual DOI/PMID/PDF/JATS/HTML used in real expert material preparation with usage rights | **NO RIGHTS-QUALIFIED INVENTORY** | P2 synthetic source objects cannot replace licensed originals |
| Production deployment source revision + artifact + role/security proof | **NO DEPLOYMENT RECEIPT** | PR/CI acceptance not production attestation |

**Absent here** means not recovered in the available inspected surfaces, **not** proven never to exist in another chat, external storage, workstation, or organization repository.

For any later recovered design/QA document, the recovery steward must preserve original bytes + sha256, original provenance and access status, then register an append-only amendment. Existing code/CI must not be backfilled as if it were the lost original.

## 4. Original material classification, no-guess precedence

| Class | Physical storage | Rights | Permitted current use |
|---|---|---|---|
| L0 upstream scientific normative original | Author-owned controlled private repository or personal archive, immutable checksum | Ownership/publication decision required separately | Internal scientific interpretation after exact byte and author ratification |
| L0 Nutrition Foundation complete Master and five frozen phases | Current personal Library archive, byte-verified | No public redistribution attested | Precise review and **synthetic engineering** preparations only |
| L2 original UX/design/master-plan | Controlled design archive; public sanitized derivative only after independent review | UX/technical owner review | Cross-version design comparison, historical non-regression |
| L3 scientific-source original PDFs/JATS/HTML | Private, rights-gated original object storage; SHA-256 and stable provenance | Auditor reviews independent storage, machine-processing and expert-read rights | No admission before qualification |
| L3 parsed structured source and annotation | Derivative storage separated from original, Unit/span/source hash lineage | Bounded right for processing + Expert access | Independent Curator QA before SourcePackage freeze |
| L4 CI/screenshot/server acceptance originals | Access-controlled archive with specific run/commit/artifact digest | QA/security approved | Verify historical visual claims; no production claim from synthetic alone |

## 5. Material identity contract for future sources

The capture ticket must record `source_id`, bibliographic identity (DOI/PMID where relevant), legal acquisition, literal original filename/size/sha256, storage identity, **rights by distinct operation**, release dates, retraction/correction version, parser output version, stable structural Unit/span anchors, QA findings, package freeze receipt, and independent approval receipts.

We require independent decisions for:
- **Storage**: whether original bytes may be retained, on which platform and for how long.
- **Machine processing**: whether extraction, translation, embeddings, model processing or derivatives are allowed.
- **Expert display**: whether and to which authorized role(s) the original and derivatives may be exposed.
- **Redistribution/publication**: distinct from internal processing and expert viewing.
- **Sensitive/clinical data**: privacy, data minimization, deidentification and allowed person-level exposure.

This classification does **not** assert that any given external publisher has granted license merely because a URL, abstract, PDF, open-access flag or DOI is available. The Workbench's Project/Batch selectors only route tasks; they cannot act as license or permission grants.

Corresponding empty receipt template: [GOV-0.3 Scientific Source Qualification Receipt](GOV-0.3_Scientific_Source_Original_Qualification_Receipt_Template_v0.1.json).

## 6. Threat, privacy and leakage restrictions

- **Never** put original restricted PDFs, electronic medical records, named expert identities, credentials, internal correspondence or undisclosed proprietary files into a public GitHub repo or GitHub CI artifact.
- The original SHA-256 is a checksum of raw source bytes, **not** Git blob SHA, parsed HTML/MD SHA or frozen SourcePackage SHA.
- Cross-authority mapping is explicit and narrow; a newer filename or AI summary cannot replace a missing normative source.
- Raw original `->` parser unit/span map `->` independent quality review `->` SourcePackage freeze `->` task exposure follows separate grants. No reverse-flow from an Agent hypothesis, expert Gold, hidden scoring or post-event outcome to an earlier expert input.
- Translation assists reading; original text remains authority for all anchors. Stable span offsets and `UnitID` versions remain reproducible.
- Must not claim **production/IAM security** merely because the personal Library stores material. Organizational access review and backups are independent.

## 7. GOV-0.3 stage acceptance and release boundaries

| Requirement | Decision |
|---|---|
| Source archive directory exists | **PASS** |
| 9 accessible originals persisted as unique copies | **PASS** |
| Archived byte readback compared to sources | **9/9 PASS** |
| NF-P0–P4 hashes compared to integrated logical Master | **5/5 PASS** |
| Source–material public GitHub manifest created, without raw originals | **PASS upon PR check** |
| Downstream design and QA originals fully collected | **OPEN / BLOCK COMPLETENESS** |
| Target exact SIS R5 and SIS-MED R6 originals recovered | **OPEN / BLOCK CANONICAL SCIENCE** |
| Real original source and rights inventory admitted | **OPEN / BLOCK REAL SOURCE** |
| Deployable signed access/IAM/CI receipt | **OPEN / BLOCK PRODUCTION** |

Overall GOV-0.3 status: `CONTROLLED_ARCHIVE_FOR_DISCOVERED_ORIGINALS_COMPLETE / ORIGINALS_INVENTORY_INCOMPLETE`.

This constitutes **completed GOV-0.3 technical deliverables** with explicitly retained seven missing-material classes; it does not authorize raw real-source ingestion or paper/clinical claims. GOV-0.4 scientific compatibility and non-regression must treat unresolved inputs as kill gates, not waived missing data.

## 8. How to inspect and restore

- Open the personal Library folder `/NutriFoundation/GOV-0.3/Source-Snapshots/` to review each original snapshot. The public GitHub manifest records only its **relative private path** and sha256 for recovery.
- For archived snapshot validation: export the directory to an approved secure workstation, compute SHA-256 for each filename, and compare every value with `GOV-0.3_Controlled_Original_Materials_Manifest_v0.1.json`.
- If one differs: quarantine the changed copy, preserve prior hash, request a new archival revision; do not overwrite original scientific history.
- When a missing original is recovered: validate sha256 before changing status, record actual source/right owner, expose only an eligible derivative to Workbench, and request scientific owner signoff where applicable.

## 9. Milestone tracking (non-regressive)

- Master Workbench development ledger remains **A=5/5, B=2/5, C/D/E=0/5 = 7/25**.
- GOV-0.1 document inventory: completed as discovery; gaps open.
- GOV-0.2 scientific version identity: technical evidence checked, owner ratification pending.
- **GOV-0.3 private original archive: 9/9 complete, 7 required categories unresolved.**
- GOV-0.4 source/version compatibility and Strict-Blind regression: not executed by this stage.
- GOV-0.5 cross-document freeze and Git canonical governance release: not executed.
