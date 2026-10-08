# WB-P0.2-D0 · SSH tunnel internal acceptance — 2026-10-09

**Internal synthetic engineering staging is usable. Full public HTTPS/OS-security acceptance and real expert/research admission remain incomplete/NO-GO.**

Deployed application commit: `b664b891d90792a8c1f2cdb9b2a1ab623a5cf8c1`. Archive SHA-256: `540a05737d1d7811e04cd39b0b6e123a14f0e2fe5587349397078f8fd9915f5b`.

## What can be used

Open `http://127.0.0.1:18793` on the Mac with the active SSH tunnel. Independent synthetic accounts expose their own permitted task and role. The task center integrates the 19-field C1 judgment profile, C2/C2.1 phase-controlled reading, source anchors, original PDF.js and immutable submissions, plus the C2.2 manager NO-GO dashboard. Account passwords are in a private local file, outside this public repo. A local launcher reconnects the SSH tunnel when necessary.

The public `nutri.logicgene.com` A record points at Aliyun but no Workbench HTTPS vhost was activated. Current FRP owns 80/443; Caddy's protected download service owns 8000. Neither configuration was changed. New application runs as non-login `nutriwb`, with root-owned read-only code and account configuration, listening only on `127.0.0.1:8793`.

## Exact verification

| Check | Result |
|---|---|
| C1 / C2 / C2.1 / C2.2 regression | 11 / 18 / 30 / 26 PASS, zero skips |
| New D0 account/session/CSRF/isolation/persistence/backup/UI tests | 14 PASS |
| Complete engine, Python 3.11 | 144 PASS on macOS and Linux CI |
| Official binding checks, CI | 4 PASS, zero skips; repeated subset of module tests |
| Native Chromium, local and Aliyun through tunnel | 17 checks PASS, native PDF.js, zero page exceptions |
| Browser viewports | 1440×1000 and 390×844 screenshots captured |
| App/session and Pre-AI/post-AI persistence after server restart | PASS |
| Encrypted online-API SQLite snapshot with writer stopped | PASS |
| Decrypt and restore populated acceptance records | 4 frozen synthetic records preserved; immutability PASS |
| Initial stop/recover rollback | PASS; existing download remains 401 before/after |
| Application code and account config unwritable by service user | PASS |
| Frozen NDF/NDS/scientific engine files changed | 0 |
| Public HTTPS and supported-OS security | NOT ACCEPTED / deferred |
| Real experts / formal NDS-R1 | NO-GO |

[GitHub CI: both jobs passed](https://github.com/gitzhangcd/NutriFoundation/actions/runs/37822586582).

Initial Python 3.13 local runs had four `test_consolidation.py` failures, reproduced on the untouched baseline. Switching validation to Python 3.11 with the locked libraries passed all 144 tests; no scientific artifact was rewritten. This environment difference is recorded rather than silently suppressing tests.

Browser flow: independent login → native PDF and structured text → field-bound anchor and PDF highlight → save/reload → R2 Pre-AI freeze → producer fixed synthetic candidate preparation → R2 post-AI reconciliation/reload → R1 excerpt-only verification/reload → R0 independent freeze/reload → manager blocked readiness → auditor chain → logout revocation.

Independent review identified and verified fixes for edits during pending save and empty/missing backup roots. Native/concurrency tests additionally caught first-exposure races and import-time reader writes; fixes preserve existing scientific constraints. Final review had no blocking findings.

## Operations and rollback

See `apps/workbench/d0/README.md` and `deploy/`. Immutable release is active via `/opt/nutriwb/current`. Daily encrypted backup is scheduled for 03:15 Asia/Shanghai, verified on the host; retention deletion is not scheduled. Backup key is retained outside the repo on the Mac and root-only on the host. Logs are in `logs/`; full CI logs are retained locally and in GitHub.

Acceptance ran in separate data/auth directories. Its service and its local port forwarding were stopped afterward. The normal workspace has no frozen submissions; R2 draft revision remains 0. Synthetic acceptance data and its encrypted proof snapshot are retained for review.

Initial rollback: stop/disable new application and backup timer, close the local tunnel. Existing FRP/Caddy services remain untouched. Upgrade installer checks archive checksum, preserves previous units, backs up data, switches versioned source, checks health and attempts rollback on failure. Data restoration requires a new directory, inspection of newer writes and session invalidation; never silently discard drafts.

## Remaining boundaries

CentOS 7 EOL prevents full OS/security acceptance. External TCP probe accepted a handshake but returned no HTTP application response; host checks confirm loopback-only application listener, no NAT forwarding and route_localnet=0. This is not an independent external penetration test. Public HTTPS/access-password activation requires supported-host and FRP/gateway planning. Actual expert identity, qualifications, governance, source rights/snapshots and r2/r3 reconciliation remain unapproved. No synthetic record is a formal NDS-R1 observation, QualifiedDecisionReference or scientific Gold.
