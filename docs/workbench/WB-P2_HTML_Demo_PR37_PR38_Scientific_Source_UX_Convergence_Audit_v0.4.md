# WB-P2｜HTML Demo × PR #37 × PR #38 Scientific Source UX Convergence Audit v0.4

> Source of design intent: user-provided `nutrifoundation_p2_scientific_source_portal_demo(1).html` (title: “P2 科学资料准备工作台（交互原型）”, explicitly marked DEMO ONLY).
>
> Live engineering baseline: [PR #37](https://github.com/gitzhangcd/NutriFoundation/pull/37) on the PR #36 management visual system. Scope of edits: [Draft PR #38](https://github.com/gitzhangcd/NutriFoundation/pull/38), stacked on #37.
>
> User direction: **保持 Workbench 原有视觉语言不变，只调整“科学资料”的交互、信息架构与排版**。
>
> **Claim discipline:** Uploaded HTML is an illustrative, local-memory demo; none of its fictional quality/rights/freeze records prove reality. P2 code performs *synthetic* durable source staging only, not an actual MinerU deployment, real PDF acquisition, real copyright qualification, clinical Gold, expert grant, or public production release.

## 1. Priority order

1. **Overall visual style belongs to PR #37 / PR #36**: left primary navigation, white work surface, emerald-neutral accents, rounded cards, compact typography, top workspace bar and other management sections.
2. **Scientific Source-specific layout and behavior belong to the supplied HTML Demo**: primary four-stage source pipeline, four input modes, independent approval checklist, side drawer, grouped tabs/queues, side-by-side original/structured QA and source version lifecycle.
3. **Science / security ownership belongs to the original D0 + P2 isolated authority contracts**: do not blend B1 source metadata with P2 independent staging or expose source raw content to Manager/Producer; independent Curator/Auditor are synthetic roles; original EA/TPA and NDS must not change.

## 2. Screen-by-screen comparison and outcome

| Surface | Uploaded HTML Demo (explicit requirement) | PR #37 reviewed | PR #38 corrected outcome |
|---|---|---|---|
| Global management chrome | Full navigation and header in demo style, but not intended to replace established Workbench style | PR #36 management with emerald palette and grouped sidebar | **Retain exactly the existing shared shell**; P2 styles scoped under `#workspace .p2-studio` |
| Main scientific nav | Six: 资料总览 / 来源登记 / 结构化处理 / 人工质量核验 / 科学来源资料库 / 审计与版本记录 | Single studio destination with in-module tabs | Six nested scientific destinations in existing sidebar; original B1 synthetic-source route unchanged |
| Overview workflow | **Four stages**: source intake → conversion → human QA → source package freeze | Simple stats/list overview | Four separate sequence cards above main content; no fictitious permission promotion |
| KPI row | Four cards (total, rights pending, QA pending, frozen) | Four overview counters | Four stage-based cards with explicitly synthetic/demo counts and clarifying captions |
| Source intake CTA | **Four choices**: DOI / PMID / PMCID; PDF; XML / HTML; Markdown | One multistep browser memory draft | Four separate entry cards, routing to one existing four-step *synthetic* intake wizard, no real file download or upload |
| Gate checklist | Four approval gates: identity/version, rights, original versus structure QA, immutable freeze | Safety notes and role boundary | Four visible independent checks and persistent Expert Access locked caveat |
| Source list | Recent sources plus dedicated library with type/status/version/actions | Synthetic fixtures with search/status filter and detail | Six demo fixtures + durable synthetic records, status/taxonomy/search, clear source_id+revision_id, metadata right drawer; DOI/PMID identifier searchable |
| Conversion | Queue with explicit source, parser, stage, QA objects, action | Mock ParserRun queue | Durable synthetic deterministic conversion; row now displays `source_id · revision`, enabling stable access and Playwright lookup |
| Quality reader | Original excerpt ↔ Structured Document; selected evidence highlight; QA checklist separate | Hardcoded QA example | Three-column source/structured/anchor layout in existing palette; **highlight only exact selected Unit text**, never arbitrarily highlight a random substring; independent Curator signs server-side QA |
| Versions/library | Named scientific source library with status, version, package details | Client side metadata detail | Existing immutable synthetic source package/version view; no automatic expert publication |
| Governance/audit | Independent audit and version trail | No full P2 audit UI | Dedicated audit sub-view; auditor-only source audit API, other roles view only instructional status |
| Responsive | 1150/820/500px layout changes, mobile navigation | PR #36 responsive management shell | Preserve existing shell; 4→2 cards at tablet and 2-column intake→1-column mobile; no page-wide horizontal overflow |
| Fidelity semantics | “UI concept, demo only”; document examples completely invented | “synthetic preview” | Synthetic-only real staging, protected identity/rights; never claim scientific source qualification or real expert access |

### Deliberate deviations from the uploaded HTML
- **Color palette and page chrome:** deliberate PR #37 inheritance, no imported navy/blue HTML skin.
- **PDF upload:** entry card is a *synthetic workflow affordance*, not a working binary-upload control. Real PDF and MinerU service remain forbidden pending explicit rights/security/science gates.
- **QA view:** three visual columns rather than the Demo’s two-column comparison plus QA card; equivalent Original / IR / Anchor semantics with stricter independent Curator authorization.
- **Source list:** retains PR #37’s full searchable list instead of limiting overview to five recent entries.
- **Data persistence:** Demo state is browser-only; PR #38 retains isolated, auditable *synthetic* backend artifacts. Synthetic QA approval must not be treated as a real scientific source qualification.

## 3. Failure diagnosis and repair

Before these revisions, latest-sha PR #38 CI repeatedly failed at:
```
apps/workbench/d0/tests/browser_d0.py:
  .p2-table tbody tr [has_text=<P2-SYN-source-id>]
    -> button '开始结构化转换'  (Playwright timeout)
```
The conversion table rendered only `x.title`, `x.kind`, stage, unit count and CTA. The test located the specific persisted source version by `source_id`, so **the row was not selectable** even though the backend had persisted independent Auditor rights acceptance and the preceding CI checks had passed. This is a testable UI-information-contract mismatch, not evidence that the original P2 backend was entirely down.

Repair: conversion table first cell shows `title` + `source_id · revision_id`, while retaining server-side state guard `RIGHTS_ACCEPTED && producer`; new Playwright assertion waits for *exactly one* matching row before clicking. No grant, PDF, source authority or role checks relaxed.

## 4. High-value interaction contract

```
Demo-style 4 intake cards
  → existing four-step synthetic source intake
  → immutable raw artifact SHA in isolated P2 store
  → independent Auditor rights record
  → producer conversion (only RIGHTS_ACCEPTED)
  → independent Curator original vs structured Unit QA / exact quote anchor
  → immutable synthetic Source Package / audit
  ╳ original EA / B1 source registration, task publish, Gold, real expert grant: NOT AUTOMATIC
```

Browser checks require: four workflow steps, four intake cards, six nested nav destinations, consistent source_id conversion rows, paired exact QA highlight, 390px viewport no overflow, all original B1/B2/B3/B4 and D0/EA/NDS non-regression. Retain separate Auditor/Curator session checks and real-PDF denial.

## 5. Release gate

- **No merge to main, no production deployment** while PR remains Draft.
- Live rights metadata is only a signed **synthetic** attestation; real licensing remains unverified.
- Do not claim CI PASS until the same exact SHA passes all original D0/EA/TPA/NDS Chromium/Python workflows and P2 tests.
- Any further layout changes must preserve original Workbench shell and be tested against the user-supplied Demo's *four-stage, four-entrance, six-nav* reference.
