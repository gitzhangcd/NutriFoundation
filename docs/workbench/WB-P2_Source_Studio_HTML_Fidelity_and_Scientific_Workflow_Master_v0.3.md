# WB-P2｜Scientific Source Studio: HTML v0.2 Fidelity + Operational Source-Staging Master v0.3

> **Authority**: `gitzhangcd/NutriFoundation` · Draft PR #38 stacked on PR #37, itself based on PR #36.
>
> **Disposition**: P2 synthetically executable staging + visual integration. **NOT** validated real copyright, real PDF/MinerU deployment, Source Curator real identity or expert authorization. This is not a waiver of P2.0 or B4.
>
> **Original frozen owners remain unchanged**: `apps/workbench/d0/ea_runtime.py`, original `tpa_runtime.py`, `runs/**`, `src/nutrifoundation/**`, `c1/**`, `c2_1/**`, `c2_2/**`.

## 1. PR #37 vs HTML v0.2: observed gap / revision contract

| Surface | PR #37 as reviewed | P2 v0.3 action |
|---|---|---|
| Main overview | Four basic fixture statistics and compact list; no HTML five-phase process | Four compact KPI cards, five-phase pathway, three action cards, independent qualification gate and HTML-style source-list hierarchy |
| Global menu | New `#/studio` route but no scientific library child nav | Keep original B1 `#/sources`, add five P2 child routes under `#/studio` without replacing B1 or PR #36 tasks |
| Source list | Four demonstration entries; superficial search/status | Six distinct, unmistakably fictitious designs plus independent *persisted* synthetic records; status/taxonomy filters, rights, QA and Project/Batch scope |
| Intake | Browser-only four-step memory draft | Four-stage D0 cookie/Origin/CSRF controlled synthetic SourceVersion registration; original bytes content SHA and immutable artifact |
| Conversion | Parser-run mock rows | Deterministic Markdown, JATS XML, text-only HTML adapters and unverified external PDF structured-handoff; immutable ConversionRun+document SHA |
| Source QA | Hardcoded three example spans | Curator-only original/text reading and structured Unit comparison, raw byte SHA check, UTF-16 quote/SHA verification, per-unit irreversible QA and replay read model |
| Bilingual | Fictional per-paragraph translation | Original still authoritative; optional curator-entered zh-CN translation sidecars with source Unit SHA, independent immutable provenance, `AUXILIARY_ONLY`; no machine translator used |
| Freeze | Deliberate UI block only | Rights accepted + all units reviewed ACCEPT + exact document SHA required before synthetic Source Package; all other states fail closed |
| Source binding | Only select Project/Batch display | New P2 global SourceVersion to existing TPA Project/Batch exact-reference ledger; still does **not** register in EA, create Task, issue B3 Grant or Gold |
| Governance | UI-only roles | Original synthetic Auth + independent Curator credential /source-qa, separate Auditor right review, server-side role denial, hash-chained journal and SQL immutability |

Styles: keep P1.1-A / PR #36 Workbench typography, white cards, muted emerald and small controls; HTML determines information hierarchy and three-pane QA rather than pixel-for-pixel detached dashboard recreation.

## 2. Architectural boundary

```text
Original synthetic D0 session /manage
  ├── Original TPA Project/Batch/Task + B1 + B2 + B3 (unchanged)
  └── /manage#/studio
       ├── P2 source list / metadata / statuses
       ├── four-stage synthetic source intake → P2 sqlite source/artefact
       ├── producer conversion → immutable Document IR and parser receipt
       └── source version / P2-only Project/Batch reference

/source-qa (independent synthetic auditor / curator identity)
  ├── Auditor: approve or hold SYNTHETIC intended uses; NO original
  └── Curator: original SHA-bound text → IR per-unit QA
       ├── UTF-16 quote+hash / PDF locator status
       └── optional independent auxiliary translation

P2 synthetic immutable package
  ╳ does NOT automatically enter original EA
  ╳ does NOT create TPA Task, B2 candidate, B3 expert grant or Gold
  ╳ does NOT qualify a real scientific document/clinical use
```

Primary staging store: `p2_synthetic_staging.sqlite`, **physically separate** from `ea_synthetic.sqlite` and `tpa_synthetic.sqlite`. Current D0 startup still requires explicit `--allow-synthetic-execution`, loopback/SSH-tunnel origin and private account fixtures. Do not deploy P2 to a public internet endpoint.

## 3. Data objects and immutable ownership

- `P2SourceVersion`: source_id, revision_id, source_type, title, synthetic identifier, publication/acquisition date with timezone, raw format, creator, projected lifecycle; source versions are never overwritten.
- `P2RawArtifact`: original text payload / format with SHA-256 **of bytes**, immutable. **Not an actual PDF or external licensed manuscript store.** No binary PDF upload is installed.
- `P2RightsDecision`: separate auditor, `APPROVE_SYNTHETIC` / HOLD, exact uses `INTERNAL_SOURCE_REVIEW`, `MACHINE_PROCESSING`, `RETAIN_ORIGINAL`, evidence reference, append-only; may not imply actual copyright clearance.
- `P2StructuredDocument`: source/revision, raw artifact SHA, deterministic parser id, stable ordered units and document SHA. Units preserve `PARAGRAPH`, `HEADING`, `TABLE_CELL`, `FOOTNOTE`, `CAPTION` with exact UTF-16 length, unit text SHA; PDF handoff units may contain only page hints.
- `P2EvidenceQA`: source/revision/document SHA, unit ID, start/end UTF-16, quote, original quote SHA, PDF locator state, human decision, signed curator and timestamp; cannot be updated after insertion.
- `P2AuxiliaryTranslation`: same source/revision and exact unit text SHA; its SHA is **not** the original quote SHA; written language is zh-CN; all translations remain `AUXILIARY_ONLY` / not approved for expert exposure.
- `P2SourcePackage`: immutable source artifact SHA, canonical P2 document SHA, rights evidence digest, full per-unit QA set digest, package SHA and explicit `NOT_ELIGIBLE` Gold and NO expert access.
- `P2ScopeBinding`: exact global P2 source version to existing TPA Project+Batch; scope references never duplicate source bytes or force a new Task; binding only possible after package freeze.
- `P2AuditEvent`: hash-chained append-only source/rights/conversion/QA/translation/freeze/scope events. Auditor validates the full chain.

## 4. Lifecycle and server-side Kill Gates

```text
RIGHTS_HOLD ─ independent auditor APPROVE_SYNTHETIC ─> RIGHTS_ACCEPTED
RIGHTS_ACCEPTED ─ producer deterministic convert ──────> QA_PENDING
QA_PENDING ─ curator reviews every unit ACCEPT ────────> eligibility to freeze
QA_PENDING ─ any REJECT ────────────────────────────────> QA_HOLD
QA_PENDING + full review + exact SHA ─ producer freeze ─> PACKAGE_FROZEN
PACKAGE_FROZEN ─ producer P2-only usage reference ─────> Project/Batch association
```

Hard rejection conditions:
1. Real source submissions or unclear source `rights_assertion` → `REAL_SOURCE_INTAKE_DISABLED` (403).
2. Identity collision, duplicate version, temporally invalid source, oversize payload, unsafe XML DOCTYPE/ENTITY and script-driven HTML → DENY or safely text-only extraction.
3. Manager, Auditor, Producer, clinical Expert attempts to read raw original → 403; raw source and original document only Curator after synthetic rights reviewed.
4. Converted source cannot be modified in place; source revision change requires new version and SHA. Unsupported unverified PDF original cannot pass final PDF QA.
5. UTF-16 mid-surrogate index, Quote mismatch, wrong hash, source/document drift and unverified PDF bbox promotion → fail closed.
6. Every Unit must have a *distinct* immutable QA decision; any REJECT or missing QA prevents freeze.
7. No source status can imply expert access, scientific Gold or human review completeness by itself.
8. Raw artifacts, rights, documents, reviews, translations, packages, scope reference and hash-chain events reject SQL UPDATE/DELETE.
9. UI uses DOM text nodes for untrusted scientific text, not source-controlled innerHTML; no network ingestion/CDN and no output model generated by default.
10. All existing A5/B1/B2/B3/B4/EA/TPA/NDS native-browser and Python tests must remain green.

## 5. API operations in the isolated synthetic namespace

| Verb | Route | Authenticated role | Result |
|---|---|---|---|
| GET | `/v1/p2/overview`, `/v1/p2/sources` | Producer, Manager, Curator, Auditor | metadata-only, paginated |
| POST | `/v1/p2/sources` | Producer | synthetic source + raw bytes SHA |
| GET | `/v1/p2/sources/{source_id}/{revision_id}` | above | metadata, QA count, frozen package SHA, scope refs |
| POST | `.../rights` | Auditor | independent immutable intended-use record |
| POST | `.../convert` | Producer | immutable ParserRun / StructuredDocument |
| GET | `.../original`, `.../document` | Curator only | permitted read-only raw bytes/text, source SHA-bound IR |
| GET / POST | `.../qa` [POST only] / `.../reviews` [GET only] | Curator only | immutable unit QA decisions and resumable record |
| GET / POST | `.../translations` | Curator only | provenance-bound auxiliary per-unit translations |
| POST | `.../freeze` | Producer | immutable P2 synthetic package after total QA coverage |
| POST | `.../scope` | Producer | TPA Project/Batch reference only; no expert grants |
| GET | `/v1/p2/audit` | Auditor | journal integrity decision |

Authenticated access uses the original D0 HTTP-only SameSite cookie, exact Origin and CSRF. Curator/auditor login is on `/source-qa`, **not a manager role switch**. No real curators are qualified by adding a testing account.

## 6. Scientific blockers for production and real-source acceptance

The code implements a **complete synthetic execution loop**, NOT a fully approved real-science ingestion service. The following require dedicated P2.0/P2-F/P2-G acceptance and cannot be bypassed with a configuration toggle:

- Source owner signoff, DOI/PMID lookup with official provenance, authenticity/withdrawal/correction graph and real allowed-use/copyright review.
- Private binary PDF/PMC XML storage/retention and safe upload scanning; no real protected patient data.
- Actual external MinerU service, parser version pinning and deterministically validated PDF–IR unique bounding boxes; current external handoff is **unverified** and cannot be promoted.
- Qualified human Source Curator identities, duty separation, real journal credentials, independent QA adjudication, source privacy and access approvals.
- Independent real experts, SIS/SIS-MED clinical Gold, calibration, P3 exposure-safe assignment, actual Agent provenance and production deployment.
- Full visual image-match and accessibility acceptance beyond Chromium interaction/viewport checks, document-level file preview for real PDF, real multilingual translation engine and translation qualification.

**Claim limit:** `SYNTHETIC_P2_SOURCE_WORKFLOW_ENGINEERING_PASS` can be asserted only when the exact PR #38 code SHA passes original B4 Python + Chromium + EA/TPA and new P2 tests. Otherwise status remains `PENDING_CI`.

## 7. GitHub PR review and integration guidance

- PR #38 base: `workbench-p2-source-studio-ui-v02-pr36-aligned` (PR #37), ultimately PR #36. Leave Draft; do not auto-merge `main`.
- Review `p2_source_registry.py` for immutable storage, deterministic adapters and no invalid real rights claims.
- Review `p2_source_adapter.py`, `auth.py`, `d0_app.py`, `provision.py` for role boundaries and no original EA/TPA changes.
- Compare the original HTML v0.2 screenshot: 4 KPI boxes, 5-stage journey, right safety gate, status tabs, 6-row data list, same management shell, right metadata drawer, four-step intake, 3-pane QA.
- Review native Chromium screenshot artifact, source-origin leakage kills, role cross-over, package freeze and full rollback/resume.
- A verified freeze tag is a separate user-approved action; neither PR creation nor test passing constitutes production approval.
