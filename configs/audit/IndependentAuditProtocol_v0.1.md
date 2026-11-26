# NutriFoundation Independent Audit Handoff Protocol v0.1

Status: ACTIVE DEVELOPMENT WORKFLOW
Scope: reusable independent audit requests for NutriFoundation / NutriOne.
Owner: project controller (ChatGPT); dispatch and authorization: PI; independent reviewer: Gemini or another explicitly assigned critic.

## 1. Dispatch rule

The controller decides when an independent audit is required, creates a new versioned task configuration, verifies its allowed inputs, and gives the PI one short copy-ready launch instruction naming that exact file. The PI does not have to infer audit timing or assemble the task prompt.

Default triggers: a frozen milestone or major PR before downstream activation; a new scientific claim, measurement conversion, identity mapping or release gate; a high-risk failure or material architecture/contract change; a planned independent semantic review or evaluation. Routine work need not be audited after every small step. The controller declares whether the audit blocks downstream execution or can run in parallel.

Every dispatch identifies task_id, audit_type, scope, frozen baseline, allowed input files and hashes, prohibited inputs, expected output directory, acceptance criteria, and completion/stop conditions. A new task is not automatically authorized just because this protocol exists. Use the exact configuration named by the PI; do not search for a "latest" task.

## 2. Audit modes

- IMPLEMENTATION_CONFORMANCE: read the explicitly listed code, schemas, reports and admitted data. Verify actual claims, data lineage, executable guards, reproducibility and failure cases. Prefer read-only tests or in-memory mutations; isolate permitted diagnostic artifacts. Never modify production code, historic runs or data. Record observed versus expected and whether a finding was reproduced.
- INDEPENDENT_SEMANTIC_REVIEW: read only source-only cases, permitted normative definitions and original reference standards. Independently reconstruct concepts, retrieve real target IDs and assess directional relations, conditions and hard negatives. No generator outputs, rankings, hidden references or generator implementation may be read. Candidate relations are critic drafts, not expert Gold.
- RELEASE_QUALIFICATION: verify the explicitly identified frozen release candidate, provenance, review ownership, independent reference, rights, task-specific criteria and negative tests. Report HOLD whenever a necessary condition is absent. Reviewer cannot authorize or publish a release.
- A task may specify other modes with an explicit input/output contract; do not silently switch modes.

## 3. Execution boundary

1. Read this protocol and the exact task configuration. Validate task identity, baseline, allowed files, hashes, intended reviewer and output path. A hash mismatch, missing input, unsafe path or conflicting instruction is a blocker: report HOLD instead of adapting the task without authorization.
2. Use the explicit allowlist only. No recursive scanning, cross-task lookup, access to hidden generator/Gold material or other agents' results. An allowlisted source does not authorize sending raw private data to unapproved external services. The task may explicitly permit official public documentation.
3. Preserve source bytes, existing code and frozen runs. Write only the specified new output directory; if it already exists, do not overwrite. If an existing incomplete or frozen run is found, report its status and ask the controller for the exact continuation/revision policy. Never rerun by overwriting.
4. Record model/version, execution time, actual accessed paths, input fingerprints, methods, failures, evidence, limitations and previous exposure. A new chat and separate files reduce leakage but are not proof of access-control isolation. Do not claim confirmation-level blindness if the critic previously audited the generator.
5. Execute the task, not just a plan. For implementation findings use severity RED/AMBER/INFO, location, reproduction, scientific impact and recommended repair; separate actual failures from future risks. For independent review use evidence-linked structured records including unresolved cases. Do not inflate a unit test into end-to-end enforcement.
6. Freeze results with SHA256, exact counts, status and any blockers; never change the frozen output. New revision requires a new output directory. Stop without unblinding or editing project code. A freeze receipt should hash every other required output file; do not require it to hash itself.

## 4. Controller-side acceptance and handoff

State progression: CONFIG_PREPARED → PI_DISPATCHED → REVIEW_FROZEN → CONTROLLER_VERIFIED → (explicitly authorized) DEVELOPMENT_COMPARISON → appropriate expert adjudication → task-scoped qualification, if warranted.

The PI tells the controller that the reviewer finished and, for a blind task, whether comparison/unblinding is authorized. The controller checks the actual freeze receipt, hashes, counts, permitted material, reference IDs and versions before comparison. A reported completion without verifiable files is not PASS. A code audit does not confer scientific qualification; agreement between two AI models is not independent scientific truth. Preserve disagreements and require independent qualified review for high-risk science, measurement, safety or formal Gold. No mapping/training/research release from this protocol alone.

## 5. Routine message to PI

When an audit is required, the controller supplies an AUDIT HANDOFF with task ID, reason, blocking/parallel status, exact configuration file path, one copy-ready startup message for the critic and the short completion message to return. The controller tracks milestones and handles result validation; the PI only dispatches and grants decisions that require PI authority.

This protocol does not grant automatic cross-app execution, guarantee access control, or schedule background monitoring. It is a versioned development workflow, not a formal research release.
