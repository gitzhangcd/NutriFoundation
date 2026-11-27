# A2.5-R1 — AGY Reference Execution Granularity & Immutable Recovery

## Scope

This is an execution-only revision inside R2-P2-A2. The evaluated A1 bilingual retrieval method, lexicon, target universe, candidate caps and evaluation metrics remain unchanged. No evaluated ranking, comparison reference, scientific release, nutrient transfer or expert Gold is accessed/authorized. AGY native ACP is the only reviewer runtime; the ACP-reported model remains gemini-4-neon-high (not a backend version attestation). Existing authenticated reviewer HOME and mandatory parent macOS sandbox are retained. Each prompt stage uses a new ACP session. Dedicated HOME contains synthetic and previous source-only review sessions; prior provider/model-family exposure is unknown. No strict confirmatory blindness claim.

## Actual failure recovery anchor

Parent agy_reference_001 receipt SHA256 0c34c871bb9be9c76cf308b83807117dda07faaa02737870083ff157517c923f, method SHA256 56b060354db262b8981b6e2f5a97deccbd51918d5ba8022425a1f37a73d47993. Four cases sent, independent query terms and actual raw-standard results saved, no completed records. Four-case review prompt 87,252 bytes; raw response zero bytes; terminal failure ACP_PROMPT_NOT_COMPLETED. Prior 3 output files and 5 raw-batch files hash verified, original broker code and 9 source staging hashes checked. First four original queries are read only within the local reference runner, recomputed against the exact same raw-standard browser, and compared for exact equality. No new query generation for these cases.

## Execution contract frozen before new real prompts

- One case per review prompt, original case order; first 4 inherit original query/hit checkpoints, remaining cases get independently authored queries.
- Exact previous browser search and caps: up to 5 query terms per system, 5 raw records per term; up to 3 candidate edges and 3 negatives per system; full raw authority snapshots. No evaluated ranker inputs.
- Lossless target deduplication preserves every returned row, its exact native key/label/locator/alias/definition, and query-to-row membership.
- Compact response: reviewer supplies every source dimension value/state/evidence reference, edge relation/rationale/conditions/applicability, conflict, search result, disposition, extension, and unresolved reason. Deterministic carrier projection copies source identity, target row metadata, selected raw evidence observations, actual query terms and fixed HOLD flags into the original R2ReferenceReview schema. It does not infer or modify substantive decisions. Original full schema and original native-locator validator still apply. Per-case model wall time is recorded, reviewer_minutes=0 when not independently measured.
- Fresh isolated ACP process/session per stage; no client tool permission, no other agent or external search tool allowed. Hosted inference is authorized through selected AGY, not an offline model. Actual reviewer process startup and read-denial probes are checked. Outer Seatbelt profile retains loopback/PTY support, previously tested inner-worker denial, and fresh runtime scratch. Actual source material is sent only in task-scoped prompts, not mounted into AGY.
- Two maximum attempts per stage, one structural repair only after complete invalid response; repair prompt carries original response and structural error, not comparator results. A terminal runtime failure requires explicit bounded retry; uncertain dispatch without terminal receipt stops instead of automatically repeating. 150-second prompt limit; if insufficient, preserve partial bytes/receipt and HOLD.
- Each stage records immutable launch intent, raw response stream, terminal receipt and validation receipt. CaseFreeze is emitted only after exact schema/native-reference validation. Atomic no-overwrite publication, hash checks, controller lock, original artifacts unchanged. Resume walks original order, rederives accepted record from original raw response and query checkpoint, skips accepted cases without any model redispatch. Final 32-case receipt only if all 32 pass. No incomplete run qualifies as a 32-case evaluation.
- A1 tested retrieval and A2 reference outputs remain separate. No unblind or scientific qualification.

## Implementation and tests

- agy_r1_transport.py: compact judgment transport and exact metadata projection.
- agy_r1_runner.py: fixed per-case execution, immutable checkpoint chain, exact parent replay.
- tests/u3r2p2a2/verify_a2_r1.py: synthetic transport/recovery tests. These are engineering tests only.
- Preflight exact recovered queries/hits: 4/4; first four single-case prompt byte sizes 33,933 / 16,682 / 15,085 / 28,062. No candidate hits dropped. Local synthetic tests 15/15 pass.

Run real execution only in authorized local workspace. To continue a bounded segment, use the exact same frozen code and run directory with --limit N for N new cases; previously completed cases are replay-validated, not redispatched. Do not overwrite previous receipts or retry uncertain launch. The --retry-terminal-failure flag allows a second attempt for a terminal failed stage only; maximum attempt count unchanged. Independent reference and generalization remain HOLD until actual completion and separate controller authorization for comparison.
