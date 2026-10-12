# WB-P2.1-B｜Source-Centric Queue & Guided Scientific Source Operations v0.1

> Baseline: Draft PR #40 (P2.1-A) → PR #38 → PR #37 → PR #36.
> Scope: presentation/interaction + native Chromium acceptance on the original D0 Workbench. **Synthetic-only; real-source NO-GO.**
> No change to core styling, original EA/TPA/NDS, source database, rights signatures, source QA authority, Gold, or expert grants.

## UX problem and remedy

Previously, `资料总览` showed a long process explainer, four cards, gate descriptions, KPI panels and only then the source table. This required routine operators to scroll before finding work; detail drawers exposed many hashes without indicating the *next permitted action*.

P2.1-B keeps the existing six P2 content tabs, but makes the default view:

1. A concise source-work summary with counts for real persisted **synthetic** rights/convert/QA queues.
2. **Scientific source work queue** (first substantial content): identity + revision, lifecycle stage, recommended next role/action, independent Unit QA count, scope filter semantics, and CTA.
3. Secondary KPI statistics and four-stage/how-to/how-not-to-use-science explanation **below** the queue, retaining HTML Demo interaction entry points and the four cards.
4. Right-side source drawer with clear lifecycle summary before detailed provenance, versions, and SHA fields.
5. Curator QA viewer with accurate server-confirmed Unit progress, reviewed flags and desktop bounded scrolling while preserving scrolling positions on SPA rerender.

## Role-safe next-step rules

| Version stage | User-facing next action | Authorized operation |
|---|---|---|
| RIGHTS_HOLD | Wait for Auditor rights approval | Independent Auditor uses existing separate review identity; other roles view metadata |
| RIGHTS_ACCEPTED | Start parser conversion | Producer only, preexisting server gate |
| QA_PENDING | Curator continues Unit-by-Unit review | Independent Curator loads original; Manager/Producer do not read restricted original |
| QA_HOLD | Inspect rejection and create a new version as needed | Rejection remains immutable; no in-place editing |
| PACKAGE_FROZEN | Inspect immutable package | No automatic Task / Gold / Expert exposure |
| DEMO_* | Open illustrative metadata only | No new rights or scientific eligibility |

All front-end buttons use the existing guarded APIs/permissions. No new server paths or backdoors.

## Acceptance and non-regression

The native Chromium test in `apps/workbench/d0/tests/browser_d0.py` now checks:

- Work queue is visible **above** the large process explainer.
- Existing 6 fictional rows and four process stages/four intake cards remain; no duplicate navigation.
- All rows have a next-step explanation; Demo drawer shows workflow context.
- Newly registered synthetic source is in rights review and shows correct next-step state.
- Rights acceptance changes its next-step CTA to Producer conversion.
- Curator QA progress counts server-confirmed immutable decisions from 0 to all Units.
- Original P2.1-A responsive, B1/B2/B3/B4 and EA/TPA/NDS role isolation remain applicable.

## Explicit limitations

- This does **not** turn PDF placeholder into real binary upload or operate MinerU.
- It does not fetch DOI/PMID metadata, qualify actual copyright, adjudicate real science or provide true original PDF location.
- It does not make the expert reader bilingual over an entire scientific manuscript; only available Unit translation sidecars remain.
- Current flow uses a synthetic source registry; real P2.0 Source Authority and P2.1-C/D require separate acceptance.
- Keep PR Draft/Open/Unmerged pending exact-code-sha checks and a human screenshot/design review.
