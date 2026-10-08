# WB-P0.2-C2.2｜Real-Expert Pilot Readiness Gate

**Engineering mode only. No real-person registration, no research enrollment, no source widening, and no scientific Gold.**

This is a reproducible readiness evaluator for the current NDS-R1 case and frozen source packet, plus a **read-only synthetic-admin** dashboard; it is not a production identity or clinical data application.

## Scientific authority and source qualification

- `authority.py` is the identical pinned 10-Git-blob ScientificAdapter from WB-P0.2-C2.1.
- `source_packet.py` produces one deterministic, six-source **bounded excerpt projection** for R0 and R2 Pre-AI, based **only** on `Human_Baseline_Source_Packet_v0.2.json` and current R0 workpack. It carries original source metadata and supports; does not retrieve full website HTML or import the 5:2 diet engineering paper.
- The source projection **is not an independently verified full-text source archive**. For a pilot, source rights, dates, and exact text snapshots must be reviewed separately.
- `Materialized_Projection_Views_v0.2.json` claims case **r2**, whereas the current R0/R2 workpack and HBSP refer to **r3**. The system records this as an open scientific-owner reconciliation gate (even if visible numerical values appear identical). This phase does not modify frozen upstream artifacts.

## Credential preflight

`credentialing.py` demonstrates verified RS256 token signature, known kid/issuer/audience/expiry/nonce/MFA checks using **trusted server keys only**. A valid JWT is **authentication only**. No test token converts someone into a qualified expert; real license, experience, prior exposure and same-case arm exclusion must be independently checked and approved. No operational production IdP is currently connected.

`gates.py` requires 8 independent evidence receipts. Until those receipts have a verified authority and the source version issue is resolved, **real usability pilot NO-GO and formal NDS-R1 NO-GO**. Untrusted input flags cannot turn any gate green.

## Local use

Install dependencies:

```bash
python -m pip install -r requirements.txt
python -m pytest tests -q -rs
python tests/browser_readiness.py
```

Tests under `test_official.py` are skipped in isolated copied bundles; CI in the full GitHub repository must run them with **zero skips**.

Run **read-only synthetic manager dashboard** against a full repo checkout:

```bash
python app.py --repo-root /path/to/NutriFoundation --allow-synthetic-readiness --host 127.0.0.1 --port 8792
```

A one-time random local test token is printed to the terminal. Open `http://127.0.0.1:8792` and paste it into the dashboard to view the readiness blockers. Do not expose this server on the public internet, use it for real credential collection, or assign real experts.

## Test scope and exclusion

- Positive: 6 known frozen source rows, R0/R2 identical projections, hash identity, reasoned source provenance; authentic OIDC cryptographic primitive under synthetic keys.
- Negative: no R1 baseline, no source expansion, no bad source URLs, no unverified attestation, no unsigned/expired/wrong-audience token, no self-declared gate approval, no open file/pdf/task/Gold endpoints, no anonymous admin API, no upstream scientific changes.
- Not tested/approved: real provider connection, expert license verification, remote penetration test, healthcare privacy review, scientific content revalidation, consent and institutional/ethics approval, live-use multi-user security, or real NDS-R1 human judgments.
