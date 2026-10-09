# WB-EA-P1 · Isolated Synthetic Evidence Annotation

This package implements the additive, **synthetic-only** P1 portion of the P0 architecture. It is not integrated with D0 and not approved for real expert / real scientific Gold data. **All source data seeded by this package are fictional**; the study names/themes are explanatory only.

## Run (Python 3.11, FastAPI/Pydantic 2/Uvicorn)

Use the existing Workbench D0 hash-locked dependency set and add \`httpx==0.28.1\` if running API tests:

\`\`\`bash
python -m pip install --require-hashes -r apps/workbench/d0/requirements.lock
python -m pip install 'httpx==0.28.1'
python apps/workbench/ea_p0/check_contract.py
python -m unittest discover -s apps/workbench/ea_p1/tests -p 'test_*.py' -v

# Use a FRESH disposable directory and never real research data:
python apps/workbench/ea_p1/seed_demo.py --db /tmp/wb-ea-p1-synthetic.sqlite
python apps/workbench/ea_p1/app.py --db /tmp/wb-ea-p1-synthetic.sqlite --allow-synthetic-execution
\`\`\`

Open \`http://127.0.0.1:8795\`, paste the **expert** token from the local terminal. Seven typed evidence tasks are available for that actor. To exercise \`HUMAN_INDEPENDENT\`, use the \`expert_b\` token instead. Producer is a separate account for source/task/candidate submissions, and audit access is separated.

**Run the demo on an empty DB** or delete the entirely synthetic DB before rerunning \`seed_demo.py\`. The engine intentionally refuses to overwrite frozen task or candidate snapshots.

## Architecture

- \`core.py\`: SQLite versioned SourceRegistry, task allowlist, typed workpacks, exact UTF-16 quote bindings, frozen Agent CandidateSet, irreversible ExpertReviewRecord, independent blind mode, immutable audit chain.
- \`app.py\`: loopback-only synthetic API with per-process bearer role tokens; no production IdP, real expert qualifications or Gold.
- \`seed_demo.py\`: fabricated text across all seven P0 types; 7 Agent Verify + 1 Human Independent tasks; RCT task has TWO authorized source versions.
- \`web/index.html\` and \`web/ea_p1.js\`: dedicated P1 three-pane reviewer UI (separate from the existing D0 reader).
- \`tests/test_core.py\`, \`tests/test_api.py\`: runtime negative-path tests.
- [P1 engineering specification and acceptance](../../../docs/workbench/WB-EA-P1_Multisource_Typed_Annotation_Implementation_and_Acceptance_v0.1.md).

## Known scientific and engineering limitations

- The candidate publisher accepts only synthetic text; candidate \`extraction_run_ref=SYN-FIXTURE-NOT-AN-LLM\` comes from deterministic seed fixtures, **not actual LLM calls**. Real Agent integration is a separately gated step.
- Original PDF / PDF.js / paragraph-level translated real paper remains in existing D0 synthetic fixture; P1 currently reads structured-text units (not a replacement for D0 Reader).
- Only a single reviewer is bound to each P1 task. No independent dual-coder Gold agreement or adjudication.
- No institution IdP/MFA, consent, professional verification, rights qualification, clinical privacy authorization, external pentest, or production deployment.
- P0 types and profiles remain **scientific owner approval pending**. No canonical NDF/D1/D2/NDS objects are modified.
- Read access to candidate endpoints is blocked for HUMAN_INDEPENDENT, even when workpack schema contains the other workflow types. \`DECISION_CASE\` is delegated to the unchanged preexisting NDS controller, not implemented in P1.

## Defining success correctly

A successful P1 test only proves a local, synthetic \`source version → typed task → candidate freeze → human disposition → immutable review\` engineering round-trip. It does not establish paper/expert/Gold scientific validity or real-life nutrition decision safety.
