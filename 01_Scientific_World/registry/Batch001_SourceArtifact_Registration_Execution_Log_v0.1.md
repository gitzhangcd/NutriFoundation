# AI Nutri Data Foundation v0.1

## P1.5 Batch-001 SourceArtifact Registration Execution Log

## Objective

建立第一批真实 Scientific Evidence World 注册流程。

本阶段目标：

```
Literature
↓
SourceArtifact-001~020
↓
Evidence Extraction Queue
↓
EvidenceUnit Freeze
```

## Scope

Batch-001 target:

- 20 SourceArtifact
- 100-150 candidate EvidenceUnit
- Verification queue construction

## Registration Requirements

每个 SourceArtifact 必须包含：

- source_id
- source_type
- title
- DOI/PMID
- publication metadata
- nutrition domain
- inclusion rationale
- provenance

## Status Values

- candidate
- screened
- registered
- extraction_ready
- verified
- frozen

## Important Constraint

本文件定义执行流程，不包含未经核验的真实文献记录。
真实 SourceArtifact 必须经过检索、筛选和验证后写入 registry 数据文件。
