# WB-P2.1-A | Navigation Convergence & Responsive Layout Fix v0.1

## Scope and lineage

- Base: PR #38 (`1a61ff5de9fd2155a69604b2830f36082467e19e`), stacked on PR #37 and PR #36 management shell.
- User evidence: `Archive.zip` desktop/browser audit, especially `02-窄屏首屏.png` (source sidebar squeezing P2 child nav into vertical glyphs) and `03-桌面总览.png` (duplicate scientific navigation).
- This is **A only**: navigation IA and viewport stability. List-first, Demo isolation, per-source workspace, long-form bilingual QA, scope aggregates belong to B/C/D.
- No change to EA/TPA/NDS persistence, independent source QA, identity, Gold, provenance, rights, source package, or expert exposure permissions.

## UI contract

1. **Exactly one primary scientific entry**: the Workbench sidebar retains `data-p11-route="studio"` as **科学资料**. There is no duplicate P2 six-button tree in the sidebar.
2. **Exactly one P2 subnavigation**: the original six `tabs` render only as in-content `.p2-tabs` buttons, preserving the six P2 views and existing handlers.
3. **Legacy B1 preserved**: `/manage#/sources` remains an independent, reachable metadata-only synthetic B1 route. The sidebar B1 button stays as a hidden backwards-compatible route hook; users enter through `科学资料 → B1 合成来源引用 ↗`. B1 page offers `返回科学资料工作台`. B1 is never folded into P2 scientific authority or raw records.
4. **Responsive containment**: at widths ≤740px, the *primary* `.p11-nav` is a single horizontal scroll container, with nowrap labels and no per-glyph line wrapping. The *secondary* `.p2-tabs` independently scrolls horizontally, at all widths when needed. Tables scroll within their own containers; the document must not expand beyond viewport.
5. **Keyboard**: all six tabs are native buttons, have `aria-current=page` on one active item, remain keyboard operable, and restore focus after the SPA replaces its subtree.
6. **Original design system**: existing white surfaces, muted emerald palette, typography, headings, drawer, synthetic-only warnings, and independent Curator/Auditor QA source authority unchanged.

## Release gates

| Category | Test |
|---|---|
| Width sweep | Chromium 390 / 680 / 740 / 768 / 1024 / 1440 px |
| Page overflow | `document.documentElement.scrollWidth <= innerWidth + 1` |
| Navigation heights | Mobile primary nav <110px; P2 secondary tab bar <90px |
| Entry cardinality | One visible `data-p11-route="studio"`, hidden B1 legacy route, 0 legacy `#p2NavGroup` |
| Active state | Exactly one visible selected P2 tab |
| Keyboard | Focus Enter on QA tab preserves focus on its replacement after render |
| B1 linkback | B1 source Package reference can be reached, validated, registered, reloaded and revisited |
| Authorization | Existing EA, B1/B2/B3/B4, manager denial, Curator QA, strict-blind and NDS regressions remain green |
| Screenshots | `p2-1-a-source-overview-{390,680,768,1440}.png` produced by native Chromium job |

## No-Go and limitations

- No real scientific source, licensed PDF, live MinerU, real institution IAM, Gold eligibility, or expert access.
- Mobile nav is horizontally scrollable; the visual affordance and discoverability need human screenshot review. CI DOM assertions are not a complete accessibility audit.
- Do not merge this stacked PR to main or call UX frozen until exact-SHA CI and visual review are complete.


## User review addendum: Project / Batch scope toolbar

The user-provided audit screenshot of `科学资料 → 审计与版本记录` showed two full-width Project/Batch dropdown rows consuming much of the first viewport, despite the P2 audit endpoint being a **global hash-chain audit**, not a scoped source list.

The following UI contract now applies to the P2.1-A branch:

- In regular management Source Studio views, replace the always-expanded form with a compact one-row **资料范围 / 全部来源 · 未筛选** indicator and `按项目 / 批次筛选` disclosure button.
- The visible explanatory text states: **只筛选已关联的来源版本，不改变资料资格或专家权限**. The filter selects exact source-version usage references (P2 `p2_usage`), not source qualifications, raw access, expert grants or permissions.
- Show labeled Project and dependent Batch dropdowns **only when expanded**. Batch is disabled until a Project is selected; no projects shows a truthful empty state linking creation conceptually to the Task Center. Active scope shows a summary with a one-click `清除`.
- The global `审计与版本记录` view **must not display** these controls. Independent `/source-qa` auditor / curator sessions have no management Project/Batch selector.
- Keep source-qualification QA, per-unit provenance and Strict-Blind gates unchanged.
- Native browser check: collapsed control height under 120px across 390–1440px viewport samples, expand/collapse works, explanatory copy is visible, global audit has no context control. No page-wide overflow is permitted.

This addendum addresses the actual feedback only. Source-list priority, demo fixture isolation, lifecycle context and long-document QA remain deferred to P2.1-B/C/D.
