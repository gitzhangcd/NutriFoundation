# G1-Shared P0.1-A.3-R1.3 shareable summary

Run: `G1S-133-R1-3-TRUTHFULNESS-20261010T075311Z`

Local package (not in git; contains short PDF spans):  
`/Users/zhangcd/Codes/Ai-Nutri/data/g1_source_library/verification_runs/G1S-133-R1-3-TRUTHFULNESS-20261010T075311Z`

Scientific Gold: `NOT_GRANTED`. Expert signature: `NOT_OBTAINED`. Public redistribution license: `NOT_OBTAINED`.

## Gates

| Gate | Verdict | Basis |
| --- | --- | --- |
| G0 | PASS | 133 unique SourceIDs, 0 invalid DOI/PMID, 0 unstated duplicate DOI, 1 DOI absent (`CAND-G100-047`) |
| G1 | PASS | 133/133 hash and size |
| G2 | PASS | 133/133 dual parser and sampled render |
| G3 | HOLD | CONFIRMED 86, PROBABLE 28, HOLD 19, MISMATCH 0; 5 hash-bound administrative holds; completeness not universal |
| G4 provenance | HOLD | 0 VERIFIED, 133 EVIDENCE_PENDING |
| G4 rights | HOLD | Legal status `NOT_ASSESSED`; project policy allows local research only |
| G5 | HOLD | 18 legacy rows marked `legacy_issue_derived`; not a new methodological measurement |
| Human review | PENDING | 0 signatures |

Semantic drift after mapping historical `PASS` to `CONFIRMED`: R1.1→R1.3 = 42. Raw enum differences = 128. R1.2→R1.3 semantic drift = 44.

Anchor replay failures on the 133 local PDFs: 0.

`RELEASE_FOR_EXTRACTION`: 0. Twelve KN-D1-A1R-001 candidates remain HOLD because no fetch log binds source URL, retrieval time, record signature, and asset hash.

Unit tests during the run: 24 tests, exit code 0. Pre-fix log: 9 failures and 7 errors.
