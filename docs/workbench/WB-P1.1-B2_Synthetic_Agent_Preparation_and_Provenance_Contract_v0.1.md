# WB-P1.1-B2｜Synthetic Agent Preparation Operations & Provenance

**Contract:** `WB-SYNTHETIC-AGENT-PROVENANCE-v0.1`  
**Baseline:** B1 Synthetic Source Library, A5 Original D0 Management, P1 EA Strict-Blind.  
**Scope:** `SYNTHETIC_ENGINEERING_ONLY` — real Agent, real source, real experts, clinical data, scientific Gold and production remain `NO_GO`.

## 1. Decision: an attestation layer, not a new Agent runner

The original P1 `TaskProduction.prepare` already prepares an EA task and freezes a single synthetic candidate when `workflow_strategy=AGENT_PROPOSE_EXPERT_VERIFY`. Its candidate is explicitly labeled `SYN-FIXTURE-NOT-AN-LLM`. B2 shall **not** execute an LLM, parse a real document, recompute/replace candidate payload or create another source of scientific truth.

```text
Original TPA Task (DRAFT → VALIDATED → DEFINITION_FROZEN)
       |
  original P1 prepare()
       |
       +--- authoritative EA sealed synthetic candidate set
       |         source anchor + FIXTURE ref + immutable candidate digest
       |
       +--- authoritative TPA PREPARATION_FROZEN hash-chain event
                        |
                        v
B2 Producer inspection (read-only, zero writes)
  verify original task/source SHA, task-definition SHA, EA frozen candidate,
  synthetic extraction_run_ref, PREPARATION_FROZEN digest/event,
  optional already registered B1 source-reference package
                        |
                        v
B2 Producer immutable attestation (idempotent, same transaction event)
                        |
                        v
Manager redacted read-only projection → original P1 Manager assignment/publish
                        |
                        v
Original D0 EA Expert Reader (no change to original access gate)
```

### Scientific invariant

- **Truth owner**: original EA source units, source hashes, SourceAnchor and task candidate frozen records. B2 stores **metadata assertions only**, not original text/candidate payload/annotations.
- **No model fiction**: `execution_kind=SYNTHETIC_FIXTURE_NOT_AN_LLM`, `fixture_origin=SYN-FIXTURE-NOT-AN-LLM`, `real_agent_executed=false`.
- **Expert blind**: `HUMAN_INDEPENDENT` never enters B2 query results; even requesting a known independent task through detail/inspect/attest must return `DENY_INDEPENDENT_AGENT_EXPOSURE`. No candidate existence, count, digest, run identifier or origin should leak through those routes.
- **Role separation**: Producer and creator-of-task inspect and attest; Manager sees non-payload readiness and immutable provenance overview, *not* candidate set digest/count/fixture run ref; EA expert and NDS roles cannot access B2.
- **No release coupling**: B2 attestation is not a new prerequisite for existing P1 Manager publish. Already-prepared legacy synthetic tasks must work without B1/B2 records.
- **No scientific qualification**: `scientific_capture=false`, `gold_qualification=NOT_ELIGIBLE`.

## 2. Authoritative provenance joins

Required exact references:

| Evidence | Source | B2 check |
|---|---|---|
| Task revision and definition SHA | Original `tpa_tasks` immutable frozen definition | sha256 must exist; source allowlist/profile/cutoff remain the same |
| Primary source/version SHA | Original `EvidenceEngine.sources` | `source_id/revision_id/canonical_document_sha256` must match frozen TPA allowlist |
| P1 preparation event | Original `tpa_events` `PREPARATION_FROZEN` | event hash and its frozen candidate digest & strategy match |
| Candidate set | Original EA `candidate_sets` | already frozen; content digest equals P1 event; exactly one synthetic fixture, anchored source, fixed extraction reference |
| B1 source package (optional) | `tpa_source_packages` | if registered, source identity/SHA/Profile/Rights/structure/manifest checked; snapshot provenance, do not retroactively claim a later package |
| B2 immutable attestation | New TPA `tpa_agent_preparation_attestations` | canonical JSON SHA, trigger-protected immutable row and hash-audit event |

No source text, PDF bytes, translated excerpt or candidate payload is copied to B2.

## 3. API and role contract

| Method | API | Producer | Manager |
|---|---|---|---|
| GET | `/v1/tpa/agent-preparations?limit=25&offset=0` | bounded Agent-mode synthetic queue | bounded, no candidate set fields |
| GET | `/v1/tpa/agent-preparations/{task_id}` | own task frozen-proof detail | redacted operational detail |
| GET | `/v1/tpa/agent-preparations/{task_id}/inspect` | read original EA/TPA verified hashes; **no write** | 403 |
| POST | `/v1/tpa/agent-preparations/{task_id}/attest` | immutable receipt after successful inspect | 403 |

Strict attestation body:

```json
{
  "contract": "WB-SYNTHETIC-AGENT-PROVENANCE-v0.1",
  "idempotency_key": "<stable synthetic operation nonce>",
  "expected_preparation_event_hash": "<64-character SHA-256>",
  "expected_candidate_set_digest": "<64-character SHA-256>"
}
```

- Same key and same body by same creator returns exact original receipt.
- Same key with another task/body/actor is `IDEMPOTENCY_CONFLICT`.
- Different key attempting to attest a frozen task is `AGENT_ATTESTATION_ALREADY_FROZEN`.
- A stale or conflicting frozen candidate/event digest fails closed; no partial record.
- Immutable audit event `SYNTHETIC_AGENT_PREPARATION_ATTESTED` is appended in the same SQLite transaction, with no candidate payload.
- Producer detail may show the frozen candidate count/digest (derived from EA); Manager detail excludes both fields. Both views hide source text and candidate content.

## 4. UI interaction in original D0

At `/manage` → `Agent 准备`:

1. The Agent-mode queue is server-paginated, bounded at 25 records per page. Independent expert tasks are absent.
2. Selecting a task displays its original P1 state: `TASK_NOT_PREPARED`, `FIXTURE_NOT_ATTESTED` or `SYNTHETIC_FIXTURE_ATTESTED`.
3. The Producer may inspect the frozen EA + TPA evidence. Inspect does not create or run candidates.
4. The Producer may then freeze an immutable B2 provenance receipt. Idempotency keys are reused after ambiguous network failure; reconciliation requires exact server truth.
5. Manager sees the task/provenance SHA, source version and prebuilt fixture kind, but cannot inspect or attest and cannot see candidate set digest/count.
6. Original A5 task center still owns validate/freeze/prepare, Manager assign/publish and expert handoff. B2 has no button that bypasses those transitions.

The B2 page stays part of the **same** original `/manage` FastAPI application and authenticated D0 cookie/CSRF/Host/Origin middleware. It does not install a separate server.

## 5. Mandatory B2 kill tests

| ID | Acceptance |
|---|---|
| B2-K01 | Before P1 prepare, inspect/attest denied; no false candidate frozen |
| B2-K02 | Only frozen P1 synthetic fixture + exact event/source hashes accepted |
| B2-K03 | HUMAN_INDEPENDENT is absent from Agent queue and returns denial from detail/inspect/attest |
| B2-K04 | Manager/EA/NDS never see candidate set digest, count, payload or original source units |
| B2-K05 | Producer task ownership verified; unrelated user cannot attest |
| B2-K06 | Duplicate nonce replay, nonce conflict, wrong expected event/digest and double freeze blocked |
| B2-K07 | SQLite triggers deny UPDATE/DELETE; audit hash chain remains valid; restart preserves receipt |
| B2-K08 | B1 package reference optional, checked for exact provenance if registered |
| B2-K09 | Browser inspect → attest → refresh/reload; Manager redacted read-only; page errors=0 |
| B2-K10 | Original expert SourceAnchor/PDF.js, NDS R0/R1/R2 and P1 publish work with or without B2 proof |
| B2-K11 | `real_agent_executed=false`, `scientific_capture=false`, `gold_qualification=NOT_ELIGIBLE` remain immutable |

## 6. Next gates

B3 handles *synthetic* expert roster, assignment authorization and exposure-safe workflow; B4 handles integrated Chromium and operational freeze. P2 real source rights-qualified parsing and P3 real expert eligibility/scientific Gold remain independent NO-GO gates. **This B2 attestation implementation cannot be promoted to a real agent executor by a configuration flag.**
