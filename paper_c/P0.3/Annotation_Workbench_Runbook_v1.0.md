# P0.3 Annotation Workbench｜Local Runbook v1.0

## 1. Purpose

This runbook starts the runnable P0.3 reference workbench for the **human** WB-H01–WB-H15 smoke test and later Calibration12A/12B execution.

The workbench is part of the Paper C scientific measurement system. It is not a general document viewer.

Current build:

```text
P03-WORKBENCH-REF-v0.1.0
tokenizer = ws-token-v1
Calibration24 SHA256 =
ec793d52a130b98aaefebdb40b85356ed88543aea2b8eff63a7fcd9f8212af33
Gold100 SHA256 =
fdb1189647fe4022411d3ebfd6591da2398135aed398c88ca6f85236678420ad
```

## 2. Prerequisites

From the repository root on branch:

```text
e0.4.3-batch002-independent-gold
```

install the current package and tests:

```bash
python -m pip install -e '.[dev]'
```

The machine running the workbench needs network access to PubMed/PMC because source text is reconstructed from authoritative identifiers and checked against the frozen worker-visible-text SHA before annotation opens.

## 3. Start

From the repository root:

```bash
PYTHONPATH=src python -m nutrifoundation.workbench.p0_3 \
  --repo-root . \
  --db runs/E0.4.3/P0.3/workbench.sqlite3 \
  --host 127.0.0.1 \
  --port 8765
```

Open:

```text
http://127.0.0.1:8765
```

The SQLite file and source cache are local execution artifacts and are ignored by Git. They may contain reconstructed source text and must not be committed.

## 4. Human smoke-test setup

Use two genuinely separate browser contexts:

```text
Browser profile/window 1 → Annotator A
Browser profile/window 2 → Annotator B
```

Use pseudonymous expert IDs. Do not use the same browser session for both roles during the isolation checks.

Authoritative checklist:

```text
paper_c/P0.3/Workbench_Human_Smoke_Test_Checklist_v1.0.md
```

Record the result using:

```text
paper_c/P0.3/Human_Workbench_Smoke_Test_Result_Template_v1.0.json
```

## 5. Smoke-test sequence

Perform WB-H01 through WB-H15 in order.

For source/hash tests, use Calibration12A. Opening a source causes the server to:

```text
PMID/PMCID
→ reconstruct worker-visible source text
→ normalize using the frozen P0.2.x rule
→ compute SHA-256
→ compare with Calibration manifest
→ allow annotation only on exact match
```

Any mismatch must block annotation.

For A/B isolation:

1. Open the same Calibration12A source as A and B.
2. Save A draft.
3. Verify B cannot retrieve A's record.
4. Lock only A.
5. Verify B still cannot retrieve A.
6. Lock B.
7. Verify peer/diff access becomes available.

For lock immutability:

1. Lock a first-pass record.
2. Attempt to edit/save scientific fields again.
3. Both UI and server must reject mutation.

For span round-trip:

1. Select text directly in the source panel.
2. Bind it to one or more scientific object IDs.
3. Save.
4. Reopen the source/record.
5. Confirm exact text, source SHA and half-open token interval are unchanged.

For Round B ordering:

```text
A lock + B lock
→ pair lock
→ discussion remains denied
→ reliability report SHA freeze
→ discussion becomes eligible
```

Do not use a fabricated reliability report for real Round B execution. A synthetic 64-character SHA is acceptable only for H0 state-machine smoke testing and must be clearly recorded as a smoke-test artifact.

## 6. Gold100 deny test

Gold100 content must never be shown in P0.3.

Attempting a Gold100 candidate ID through the API must return access denied and emit an `unauthorized_access_attempt` audit event.

Do not copy Gold100 text into the workbench to test this condition.

## 7. Expected H0 result

Automated implementation acceptance is already PASS.

Human H0 can become PASS only when all WB-H01–WB-H15 are directly observed in the real browser/workbench environment and recorded.

Until then:

```text
P0.3 overall = NOT YET PASS
Round A       = BLOCKED PENDING H0 + H1
Gold100 expert annotation = PROHIBITED
```

## 8. After H0

If every WB-H item passes:

```text
H0 PASS
→ H1 expert eligibility / COI / role separation
→ H2 Calibration12A independent first passes
```

If any item fails, do not start Round A. Fix the implementation, rerun automated acceptance, and repeat the full H0 smoke test.
