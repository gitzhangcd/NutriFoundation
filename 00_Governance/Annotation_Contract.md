# AI Nutri Data Foundation v0.1

# Annotation Contract Freeze

## Principle

Human experts define scientific validity boundaries.
Agents perform scalable extraction and organization.

## Annotation Ownership

### Agent Layer

Responsible for:

- candidate evidence extraction
- metadata completion
- preliminary claim generation
- inconsistency detection

### Human Expert Layer

Responsible for:

- scientific correctness
- applicability judgment
- safety boundary
- acceptable decision set

## Annotation Object

Each annotation must contain:

```yaml
annotation_id:
object_id:
annotator_type:
annotation_action:
confidence:
uncertainty:
review_status:
```

## Expert Reference Rule

Experts do not provide only one answer.

They define:

```
acceptable decisions
unsafe decisions
defer conditions
required missing information
```

## Adjudication

Disagreements must be preserved.

The final object stores:

- original annotations
- disagreement
- adjudication decision
- rationale
