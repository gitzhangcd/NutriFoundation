# Evidence Review Implementation Plan
## Goal
Implement the user-approved on-demand evidence review in the real Workbench.
## Architecture
Use a shared pure status helper for inline rows, drawer cards and submission review. Replay uses the existing authorized document and PDF resolver. Keep the drawer accessible and allow background reading.
## Tasks
- [x] Add behavioral tests for missing evidence, changed judgments and independently verified PDF status.
- [x] Add evidence_status.js; render per-judgment cards and warnings in workbench.js.
- [x] Add drawer review list and explicit submission-review entry in index.html; use nonmodal drawer with Escape and focus restoration.
- [x] Add authorized source replay and visible feedback in reader.js; style cards and responsive drawer.
- [x] Run D0 unit/browser acceptance, inspect UI, commit and push the existing PR branch.

## Validation
19 D0/item-binding tests passed; 30 Chromium desktop/mobile checks passed with no page errors. Source replay verifies exact saved quote highlighting; editing or removing a judgment flags its previous links. Screenshot layout reviewed. GitHub sync targets existing PR #23; no Aliyun deployment in this change.
