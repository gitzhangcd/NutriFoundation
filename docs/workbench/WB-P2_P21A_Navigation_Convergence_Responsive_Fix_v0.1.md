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
