# Source Registry

This directory stores registered scientific sources.

## Planned Structure

```text
source_registry/

├── guidelines/
├── rct/
├── meta_analysis/
├── cohort/
└── databases/
```

Each source must map to:

```
SourceArtifact schema
```

No EvidenceUnit can exist without a valid SourceArtifact reference.
