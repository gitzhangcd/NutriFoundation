# WB-P2-V2.1-P1｜Role-Preserved Synthetic Source Lifecycle & Workbench Integration v0.1

> 2026-10-15 · PR #48 stacked on PR #47. **SYNTHETIC ENGINEERING ONLY**.  
> Authoritative API: existing D0 `/v1/p2/*`; existing `p2_source_registry.py` and `p2_source_adapter.py` unchanged.  
> This is a bounded Workbench V2.1 implementation contract, **not** a new Nutrition Foundation/SIS norm, copyright approval, clinical conformity, Gold, expert entitlement or cloud release.

## 1. Change scope and scientific invariants

V2 page `/manage#/studio-v2` is available only to Producer/Manager under existing HTTP role gates. Independent `/source-qa#/studio-v2` uses only **Auditor / Curator** accounts through an explicit independent session. Legacy `/source-qa` continues to open the established Source Studio, preserving its original acceptance.

No new backend endpoints, SQL schema, parser capability, IAM privilege, EA/TPA semantic authority, NDF/NDS/JFreeze or Gold primitive is introduced. Original real PDF and MinerU adapter are deliberately excluded from this phase.

`DEMO` = in-browser non-persisted visual reference, no source/QA/license/SHA truth.  
`SERVER_SYNTHETIC` = API-sourced `source_id + revision_id`; all relevant transition claims require a server receipt.  
`REAL_SCIENTIFIC_SOURCE` = not eligible in this build.

`Project/Batch` are optional source-use references and **never** rights grants, Expert exposure, case eligibility or Gold.

## 2. Exact role-preserved workflow

| Stage | Actor | Existing API | Required V2.1 behavior |
|---|---|---|---|
| Register r1 | Producer | `POST /v1/p2/sources` | Explicit user-authored synthetic Markdown; server returns `RIGHTS_HOLD` and raw SHA; non-Producer denied |
| Approve/HOLD | independent Auditor | `POST /sources/{id}/{rev}/rights` | Evidence ref `SYN-*`, exact three uses; server signs immutable receipt; HOLD terminal for revision |
| Convert | Producer | `POST /sources/{id}/{rev}/convert` | Only `RIGHTS_ACCEPTED`; deterministic parser; record `run_id`, Document SHA, unit count |
| Source + IR read | independent Curator only | `GET .../document, original, reviews, translations` | Compare original SHA, Document SHA, SourceVersion; Manager/Producer/Auditor never render originals |
| Unit QA | independent Curator only | `POST .../qa` | Only untouched Unit, exact UTF-16 boundaries and fresh SHA256 of authoritative `u.text`, `ACCEPT / REJECT`; no DOM-local signoff |
| Auxiliary translation | independent Curator | `POST .../translations` | Separate human-provenance sidecar, never replaces original quote or grants expert exposure |
| REJECT recovery | Producer + independent reviewers | `POST /v1/p2/sources` new revision | `QA_HOLD` cannot freeze; explicit new raw content under r2 with source-family reference; fresh rights/Parser/QA |
| Freeze | Producer | `POST .../freeze` | Requires server-confirmed full Unit coverage, no REJECT, exact current Document SHA; immutable package |
| Bind usage | Producer | `POST .../scope` | Only after freeze, only existing Project/Batch; no auto-expert permission |
| Audit | independent Auditor | `GET /v1/p2/audit` | Validate hash-chain `valid/events_checked/last_hash`, not fictional static event rows |

### Known read-model limit (explicit)

Existing audit API provides *integrity summary* rather than an authorized itemized event history. V2.1 therefore displays server SourceVersion detail, package SHA, actual usage bindings, current-session server action receipt metadata and independent Auditor integrity summary. The static 15-axis PR #46 matrix remains documentary, never elevated to executable scientific conformance. A future per-source audit event endpoint would need separately scoped permission and signed API contract; no fake timeline may substitute.

### Scope of access

- Manager: metadata only, never document/original or global auditor API, no mutation.
- Producer: source creation/convert/freeze/scope/new revision, but not original/document or human QA.
- Auditor: independent evidence/rights and audit integrity, **no original**.
- Curator: independent original/document/reviews/translation and immutable Unit decisions, **no rights/freeze**.
- EA Expert/Agent: forbidden from P2, unchanged.
- Same-origin session handoff from Manager/Producer requires explicit logout; link cannot bypass `/source-qa` server role gate.

## 3. Verification / non-regression plan

**Browser proof:** `apps/workbench/d0/tests/browser_d0.py` adds V2 registration and server readback; separate Auditor V2 login and signed rights; Producer V2 conversion; separate Curator V2 original/IR + translation + exact-quote Unit QA; Producer V2 Package Freeze; V2 Project/Batch binding after actual operational project/batch creation; QA/rights/audit negative checks and screenshots. Existing legacy P2/EA/TPA/B1-B4/A5 flow remains in same native Chromium run.

**API proof:** `apps/workbench/d0/tests/test_p2_source_studio.py` adds rejected r1 → new r2 raw artifact, new independent rights, conversion, all-Unit re-review and r2 freeze while r1 rejection remains immutable; original P2 permission, UTF-16, SHA drift, PDF handoff negative tests retained.

**Required final gate:** 9/9 original workflow CI on **exact PR #48 head SHA**, plus native source-QA/role checks, 1440/390 screenshot review, no protected scientific source changes. Never reuse a prior commit's acceptance.

### Current acceptance record

- Initial implementation committed to Draft PR #48. Browser and scientific kill-test execution must be recorded at the **final exact head**.
- GOV-0.4-P0 PR #46 remains a separate static-documented branch. Its status stays:
  `SIS_R5_EXACT_SOURCE=PENDING; SIS_MED_R6_EXACT_SOURCE=PENDING;`
  `AI_NUTRI_V2_1_ADAPTER=PENDING; EXECUTABLE_NF_CONFORMANCE=PENDING;`
  `REAL_SOURCE=NO_GO; REAL_EXPERT=NO_GO; GOLD=NO_GO`.
- Visual Demo pixel-level parity and independent human UX acceptance remain **B5 open** even if native Chromium workflow returns PASS.

## 4. Global milestone ledger alignment

Issue #42 defines 25 milestones: A=5/5, B=2/5, C/D/E=0/5 (**7/25 formally signed engineering milestones** before this stage). P1 is an **incremental implementation of B3/B4**, not a new counted milestone; B3/B4/B5 need their own independent UX/role/science evidence and acceptance. C1–C5 real sources, D1–D5 expert research and E1–E5 governance/security/release stay open. PR #48 remains Draft until separate integration gates.

The next engineering gates after this synthetic lifecycle are **B4 complete long-document independent QA + B5 human UX** and parallel **GOV-0.4-P1/P2 exact scientific source/adapter/non-regression**. Do not enable C/D/E real-workflow gates by a Workbench UI flag.
