# AI Nutri Agent Workflow Freeze

## Objective

Define how agents participate in scientific data construction without replacing scientific ownership.

## Workflow

```
Raw Source
    ↓
Extraction Agent
    ↓
Candidate Object
    ↓
Verification Agent
    ↓
Human Review
    ↓
Frozen Scientific Object
```

## Agent Roles

## Evidence Extractor Agent

Input:

- papers
- guidelines
- datasets

Output:

- SourceArtifact candidates
- EvidenceUnit candidates

## Claim Verification Agent

Checks:

- unsupported inference
- causal overstatement
- missing limitations

## Data Quality Agent

Checks:

- schema compliance
- provenance completeness
- version consistency

## Human-in-the-loop Boundary

Agents cannot:

- approve final scientific claims
- define safety boundaries
- generate expert gold labels

## Output Requirement

Every agent output must include:

```yaml
agent_id:
input_objects:
output_objects:
confidence:
uncertainty:
validation_state:
```
