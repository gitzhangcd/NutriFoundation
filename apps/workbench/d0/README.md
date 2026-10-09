# WB-P0.2-D0 · Unified private engineering Workbench

One task center and three-pane reader/judgment/evidence workflow, reusing C2.1's task authorization, C1's exact 19-field profile and C2.2's manager readiness assessment. R0 permanent no-Agent, R1 excerpt-only verification and R2 immutable Pre-AI/post-AI separation remain server-enforced.

**Only synthetic internal engineering exercises. Real experts and formal NDS-R1 capture remain NO-GO.** The public 5:2 paper is a reader fixture, not a new NDS source. No patient details or actual expert research responses may be entered. Fixed synthetic account roles are not professional qualification.

## Current deployment boundary

Aliyun is CentOS 7. User explicitly chose SSH tunnel-only internal testing and accepted that D0 OS/security acceptance does not pass. Application always listens on `127.0.0.1:8793`, runs as non-login `nutriwb`, and has no public Workbench Caddy vhost. FRP owns ports 80/443; Caddy owns download port 8000. Both are preserved. Do not activate a new Caddy vhost in place while FRP owns those ports. Domain `nutri.logicgene.com` is reserved for a later supported-OS HTTPS deployment; the included password-protected Caddy example is inactive.

Open a local encrypted tunnel:

```sh
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:18793:127.0.0.1:8793 Aliyun
```

Visit `http://127.0.0.1:18793`. Loopback HTTP is inside the encrypted SSH forwarding path; it is not public HTTPS acceptance. Keep local port 18793 exact because Host/Origin checks are intentional. Independent usernames: `r0`, `r1`, `r2`, `manager`, `producer`, `auditor`. Passwords are provisioned locally outside the public repo and never printed or logged. Manager cannot read expert source routes; producer prepares fixed synthetic candidate sets; auditor only views audit chains.

## Reproducible build and run

```sh
python -m pip install --require-hashes -r apps/workbench/d0/requirements.lock
bash apps/workbench/d0/install_pdfjs.sh
python apps/workbench/d0/provision.py /PRIVATE/NEW_DIRECTORY
python apps/workbench/d0/d0_app.py \
  --repo-root /PATH/TO/CHECKOUT --root /PRIVATE/data \
  --accounts /PRIVATE/NEW_DIRECTORY/accounts.json --auth-db /PRIVATE/auth/sessions.sqlite \
  --origin http://127.0.0.1:18793 --port 8793 --allow-synthetic-execution
```

Credentials/config directory must be private. Accounts configuration is 0600, or root-owned 0640 with a dedicated application group. Code and runtime are root-owned/read-only to the application user. Sessions use HttpOnly/SameSite=Strict cookies, eight-hour expiry, per-session CSRF, exact Origin/Host checks, revocation on logout/password rotation and login throttling. No external synthetic token can bypass the cookie gate. HTTPS origin enables Secure cookies and HSTS but does not approve real enrollment.

Locked Python runtime libraries and PDF.js 4.10.38 are deployed together. Python 3.11.17 standalone runtime and uv 0.12.23 were verified on the current host; OS EOL is not repaired by this isolation. One worker with SQLite is intentional. Multiple replicas require a separate data/authorization design before switching to PostgreSQL.

## Operator paths

- `/opt/nutriwb/releases/<commit>` and `/opt/nutriwb/current`: versioned source and active link.
- `/opt/nutriwb/venv`, `/opt/nutriwb/python`, `/opt/nutriwb/tools`: isolated runtime.
- `/etc/nutriwb/accounts.json`: hashed credentials, root-owned/dedicated group read only.
- `/etc/nutriwb/backup.key`: root-only encrypted-backup key; keep a secure offline copy.
- `/var/lib/nutriwb/data`: synthetic controller, source/anchor databases and reader files.
- `/var/lib/nutriwb/auth`: session store, excluded from data backups.
- `/var/backups/nutriwb/*.fernet`: encrypted snapshots; no public serving or automatic retention deletion.
- `journalctl -u nutriwb`: service events without access-token/password logs.

For acceptance, use a separate data/auth directory and local port 18794; do not freeze the normal workspace merely to rerun tests.

## Backups and rollback

`nutriwb-backup.timer` runs daily at 03:15 in the server timezone. Its root-owned helper stops the only writer, verifies the workflow database exists, creates SQLite backup-API snapshots and file SHA manifest, encrypts with authenticated Fernet, decrypts into a disposable directory to verify integrity/restore, then restarts the worker. This causes brief downtime. No expired-backup deletion is scheduled. Initial deployment also retains an empty-workspace snapshot. Verify the key is securely retained before relying on encrypted recovery.

To verify an encrypted snapshot separately:

```python
from pathlib import Path
from backup import open_backup
open_backup(Path('/var/backups/nutriwb/SNAPSHOT.fernet'),
            Path('/PRIVATE/NEW_RESTORE_DIRECTORY'),
            Path('/etc/nutriwb/backup.key').read_bytes())
```

Restoration refuses to overwrite an existing directory. Stop all writers before replacing live data; inspect restored drafts, frozen records and audit chain first. Account files and session records are not restored; invalidate sessions when restoring data. Record any newer drafts that would be lost, rather than silently discarding them.

Initial deployment rollback: stop/disable `nutriwb` and its backup timer, close SSH forwarding. Existing Caddy/download services need no rollback because no configuration changes are made to them. For an upgrade: stop service, retain current symlink and pre-change encrypted backup, switch current to the prior immutable release, restore data only if schema compatibility requires it, invalidate sessions and recheck health. No automatic deletion of releases or server reinstallation.

## Verification

Run C1/C2/C2.1/C2.2 suites in separate Python processes to avoid their legacy absolute-import module collisions. Run D0 tests and native browser test:

```sh
python -m pytest apps/workbench/d0/tests -q
python apps/workbench/d0/tests/browser_d0.py
```

The browser runner uses disposable synthetic identities/data and a real local HTTP server, requiring native PDF.js, 19 fields, save/reload, anchors/PDF BBox highlights, freeze, R1 verification, R2 reconciliation, source denial, manager NO-GO and audit/logout checks. It records runtime errors and desktop/mobile screenshots. Browser plugin was unavailable; regular Playwright was used. Python tests require Node for the asynchronous save regression.

The D0 workflow has separate Workbench acceptance and full-engine jobs, both passed for deployed `b664b89`: 99 Workbench tests and 144 engine tests, plus native browser acceptance. Initial local Python 3.13 produced four consolidation/serialization failures, also on pristine `33e9704`; using the same locked libraries under Python 3.11 passed all 144 on macOS and Linux CI. Use Python 3.11 for this frozen scientific serialization validation; no frozen science was edited.

Known exclusions: no public HTTPS activation, supported OS/security PASS, external pen test, real identity provider, expert credential verification, formal scientific r2/r3 reconciliation, study enrollment or NDS empirical outputs.


## WB-EA-P1 · 同一原始 D0 工作台的科学来源标注（合成工程版）

修复版从原始 D0 UX commit \`54b4c2eba844f39c07575573a3e834e0bc00c261\` 直接派生。**不是第二套工作台、第二个 FastAPI 端口或独立 Token 登录。** \`d0_app.py\` 下的 \`/v1/ea/**\` 使用已有 cookie/Origin/CSRF 控制；\`reader.js\` 继续提供段落/表格渲染、原文选区高亮与当前文档检索，右侧原有专家面板新增类型化 Evidence Annotation 模式。旧 \`NDS_R1_DECISION_CAPTURE\`、R0/R1/R2、原 PDF.js、部分双语 sidecar 和所有既有来源权限不变。

**必须使用新增独立账号**：新建测试凭据包时，\`provision.py\` 现在会生成 \`ea1\`、\`ea2\` 两个 evidence-only 合成专家账号。它们与现有 \`r0/r1/r2\` 完全分离，后者不能读取 EA 来源；前者不能读取 NDS 决策案例。切换科学任务不需要新网页或重新登录，但必须在 evidence-only 独立会话内操作；要查看 NDS，需要退出并使用另一授权账号。老版本私有账号配置**不会自动获得新账号**，只能在隔离测试环境按私密配置流程新建，不要覆盖生产凭据或在聊天中公开密码。

初始 EA 数据包是七类**自编虚构**结构化材料（第一任务授权 RCT＋Guideline 两份来源），内含 Producer 固定工程候选和一项独立盲法任务；来源不属于真实 Hajek 5:2 RCT 或任何真实指南。记录状态 \`scientific_capture=false\`、\`gold_qualification=NOT_ELIGIBLE\`。EA 原文目前仅有结构化文本，尚未在本模式下集成真实原件 PDF 和具备授权的段落级全文译文。原 D0 PDF/双语能力仍为 NDS 合成阅读演练，不得误称 EA 已实现 PDF 科学核验。

详见 [P1 修复与验收](../../../docs/workbench/WB-EA-P1_D0_54b4c2e_Integration_Remediation_v0.1.md)。

\`\`\`bash
python -m pytest apps/workbench/d0/tests/test_d0.py apps/workbench/d0/tests/test_ea_integrated.py -q
python apps/workbench/d0/tests/browser_d0.py
\`\`\`

本模块未获正式科研专家、原始来源版权、伦理、生产安全和 Gold 晋级授权；服务端继续保持 \`SYNTHETIC_ENGINEERING_ONLY\`。
