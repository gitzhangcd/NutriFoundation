# A2.5-R3.6 — Versioned Exhausted-Budget Exception & Bounded Case 016 Recovery v0.1

## Decision and invariants

The owner explicitly authorized exactly one additional case 016 semantic review after the separate R3.5 source-free requalification passed 3/3. The original v0.2 method (SHA-256 08056819875d23e3c507b72d55eca479319fe737dbf4d7fa45bedc78ad2a6bd8), original two-attempt budget, query checkpoint, exact regenerated prompt, model declaration gemini-4-neon-high, native ACP transport, OS read-denial checks, and 210-second deadline are unchanged. The execution-only exception is an additional third local attempt, not retroactive relabeling of the two previous attempts. Attempt 01 timed out and retained 5,277 bytes; attempt 02 returned a location-precondition error (400) confirmed by an identical source-free diagnostic response. R3.5 demonstrated three successful synthetic responses; it does not guarantee current/future access or model identity beyond the ACP declaration.

The original 230 private files, 124 runtime files, 3 retry-contract files, prior diagnostic directories and R2 case 008 lineage are pinned. Real source-only context is used locally to rederive the original query/hits, prompt and native evidence validation. No evaluated ranks, actual comparator outcomes, unblind, scientific promotion, mapping release, or partial-response acceptance. No remote exactly-once or billing claim.

## Execution state machine

- `prepare`: verify previous receipts and exact method/diagnostic/source lineage; run synthetic guard tests, freeze ExceptionContract and SyntheticTestReceipt.
- `execute`: under original controller lock reverify baseline, ensure no previous third/fourth attempt or consumed grant. Atomically consume the single-use grant before the unchanged v0.2 invocation; write attempt 03 separately. It is consumed even if interrupted before dispatch. Do not retry automatically.
- `finalize`: recover solely from actual third-attempt terminal evidence and original raw bytes. If absent, fail closed, not a fabricated terminal. Validate real normal terminal, same model and prompt, fresh session, original projection/schema/native locators. Only valid complete responses produce CaseFreeze with explicit exception lineage. Failure remains HOLD.
- `replay`: validate the exception lineage and actual record; call the existing R2 adapter with dispatch denied. Require exact accepted-record replay. If case 016 passes, require initial 16/16 zero-dispatch replay before continuation. If failed, verify history and stop.
- `continue --start N --limit K`: only after accepted 016 and initial replay. Explicit original-order next contiguous range; current owner work order is 017–020 (N=17, K=4). Later ranges require their own explicit continuation instruction. Reuse R2 adapter and frozen v0.2 runner, with guard restricting new dispatches to the bounded range and no terminal retry flag. The earlier exception applies only to case 016. Stop on terminal failure or uncertain dispatch. No fourth attempt.

Run in the exact existing local `agy_r1_002` directory. The exception contract and private records stay local; only aggregate hashes/statuses and safe implementation/test files go to the draft PR. The scientific reference set remains developmental and not expert Gold; comparison and unblind remain HOLD.
