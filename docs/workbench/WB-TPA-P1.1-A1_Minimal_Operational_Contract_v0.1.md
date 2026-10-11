# WB-TPA-P1.1-A1｜Minimum Operational Contract Delta & Non-Regression Plan v0.1

> Scope: **synthetic engineering only**. Design/implementation delta to the P1 synthetic TPA runtime; **NOT** a scientific protocol revision, real research GO, security certification, or Gold authorization.  
> Source: `WB-TPA-P1.1-A_Management_Page_Level_Spec_v0.1.md` and P0 freeze `WB-TPA-v0.1_P0_Task_Production_Assignment_Normative_Design_Freeze.md`.  
> Baseline: `workbench-tpa-p1-synthetic-management` at `5009763dda194245d9c4dfdd5df45f365c61529a`.

## A1 decision and invariants

Keep one same-origin D0 `/manage` under existing session cookie + exact Host/Origin + CSRF. The project/batch registry is **purely operational**. It is not a science study arm, an assignment protocol, a qualification authority, or a source entitlement. All sources are synthetic fixtures. Preserve every P1 route/request body/response for unfiltered usage, the 19-field NDS pipeline, original three-pane D0, `/v1/ea/**`, R0/R1/R2, strict-blind candidate controls and `UNQUALIFIED_EXPERT_REVIEW`/`NOT_ELIGIBLE`.

**Do not repurpose** existing `tpa_batches` (the old 1–7-item atomic create receipt). **Add** `tpa_project_registry`, `tpa_operational_batches`, `tpa_task_placement`, `tpa_ops_idempotency`. Tables live in *the same* private `tpa_synthetic.sqlite` as `tpa_tasks`, to permit atomic new-task+placement transactions. Source/EA/SIS/GOLD database tables remain untouched. `tpa_events` remains the append-only hash-linked operator log; all successful operational changes append events through the existing `TaskProduction.event` within the same transaction.

### Minimal persisted records

| Object | Schema and guards |
|---|---|
| Project | `project_id` unique `PRJ-SYN-[A-Z0-9-]{3,40}`, `name` 2–100 chars, `description` max 500 chars, server `owner_actor`, `created_at`, lifecycle `ACTIVE` (archive future, not implemented); reject rich markup and suspicious personal/secret-bearing content, do not claim reliable PHI classification |
| BatchRegistry | `batch_id` unique `BATCH-SYN-[A-Z0-9-]{3,40}`, immutable `project_id`, `label` 2–100 chars, `purpose` max 500 chars, server `created_by`, `created_at`; foreign-key valid project; no arm/Gold state |
| Placement | immutable `(task_id, task_revision_id, batch_id, project_id, definition_hash)` and server timestamp, exactly one membership; **never change after creation**, including for frozen/published task |
| Idempotency | unique request key with action, server actor, exact request digest, immutable receipt; conflicting replays raise `IDEMPOTENCY_CONFLICT`; no duplicate project, batch or task |

All writes require `producer` role; reads are `producer` or `manager`, session-specific. No new source read grants. Other roles including auditor, EA and NDS are refused on all management APIs. Audit stays auditor-only. All views return **metadata only**: no source units, PDF bytes, candidate payload/count/digest, model response, gold, expert judgment, patient data or private filenames.

### Proposed P1.1-A2 endpoints

| Route | Permission | Role-safe contract |
|---|---|---|
| `GET /v1/tpa/projects` | producer/manager | `{projects, total, limit, offset, synthetic_only}` with bounded server pagination |
| `POST /v1/tpa/projects` | producer | `{project_id,name,description,idempotency_key}`; persistent idempotent receipt |
| `GET /v1/tpa/projects/{project_id}` | producer/manager | metadata and safe aggregate only |
| `GET /v1/tpa/projects/{project_id}/batches` | producer/manager | registry list, not legacy create receipts |
| `POST /v1/tpa/projects/{project_id}/batches` | producer | `{batch_id,label,purpose,idempotency_key}`, idempotent |
| `GET /v1/tpa/projects/{project_id}/batches/{batch_id}` | producer/manager | versioned batch metadata and safe task counts |
| `POST /v1/tpa/tasks/in-batch` | producer | existing strict Draft fields plus `project_id,batch_id,idempotency_key`; **single transaction** creates `tpa_tasks` and immutable placement |
| `GET /v1/tpa/overview` | producer/manager | optional `project_id,batch_id`, server-derived preparing/ready/assigned/published/revoked/total/legacy; `blocked=null` (not yet measured) |
| `GET /v1/tpa/tasks/{task_id}/management` | producer/manager | role-safe metadata, placement, server next-action name; no source/candidate |
| `GET /v1/tpa/tasks` | existing producer/manager | unchanged when no filters; additional optional `project_id,batch_id,state,limit,offset` with authorized server filters |

`POST /v1/tpa/batches/drafts` remains unchanged and atomic on ≤7 new draft tasks. A batch of >7 operational tasks can contain multiple separate atomic sub-operations, **not** a single aggregate transaction. All existing unplaced P1 tasks render in an explicit **Legacy** bucket; no inferred migration. Frozen task definition and source checks remain owned by the exact original P1 controller, reused via `build_draft_record` for in-batch creation.

### Status/state correctness

Overview counts use only recorded TPA states. `preparing = DRAFT + VALIDATED + DEFINITION_FROZEN`; `ready = READY_FOR_ASSIGNMENT`; `assigned = ASSIGNED`; `published = PUBLISHED`; `revoked = REVOKED`; `blocked = null/unavailable`. No inference of opened/read/submitted, clinical quality or Gold readiness. Task next actions map to existing controller state transitions; UI role permissions mirror server role guards. Current version P1.1 creates/reads operations data only: no update/delete/reassignment of project/batch or placement.

### Errors, privacy, and robustness

- Exact origin/CSRF/session gates inherited from D0. No new public APIs or process.
- 401 clears private UI; 403 is authorization denial without source details; 409 means no side effects; 422 invalid input. Never render server-controlled strings as `innerHTML`.
- Strict regex IDs, bounded text (no markup/links, emails, phone-like personal data patterns), duplicate/partial transactions rejected, source version/hash/cutoff checks applied by existing `build_draft_record`.
- Project/batch scope is **additional filtering**, not entitlement. `manager` may never call EA source/candidate routes. All sidecar translations stay auxiliary with original-authoritative constraints.
- Legacy P1 routes remain import, single draft, 7-item batch, source metadata, validate/freeze/prepare/assign/publish/revoke, audit. Do not make old app depend on new project records for these routes.
- Same D0 security middleware; no changes to frozen science files, no true Agent, no MinerU real import, no real expert enrollment.

## A1 implementation and non-regression gates

A2: create small operational runtime/adapter, register in `d0_app.py`, extend `/manage` with Overview / Project–Batch / Task tabs plus honest placeholders for four later modules; reuse existing task builder, session and security controls. A3: run both new route tests and pre-existing D0, EA, NDS and TPA tests; Chromium desktop/mobile and keyboard, including CSRF denial, strict-blind independence, Legacy, retries and screen sizes. A4: report exact CI run IDs/outcomes, test gaps, code SHA, do not state PASS without observed successful checks. Code merge into `main`, public deployment, science/security acceptance and true experts remain **NO-GO**.

### Kill tests

K1 unauthorized roles cannot read/alter projects/batches; K2 manager cannot write and cannot read source content; K3 stale/invalid batch or duplicate task leaves no tasks/placements; K4 retry same idempotency key yields same receipt; K5 conflicting key yields 409; K6 task and placement commit atomically; K7 role change clears cached management data; K8 old 1–7-task batch unchanged; K9 Legacy task remains unplaced; K10 no Agent candidate metadata in independent/manager projection; K11 no cross-arm exposure, no premature publication; K12 original D0/NDS/EA/PDF.js/bilingual/anchor/19-field passes; K13 overview counts match server states including REVOKED; K14 CSRF/Origin enforcement; K15 no real PDF/PHI/Agent/Gold promotion; K16 no false completion or qualification metrics; K17 immutable assignment/exposure history. All P1.1 24 UI acceptance cases in P1.1-A spec remain targets; limited test coverage must be documented rather than misrepresented.