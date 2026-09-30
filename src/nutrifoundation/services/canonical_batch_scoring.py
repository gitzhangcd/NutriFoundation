from __future__ import annotations

import json
from pathlib import Path

from nutrifoundation.adapters.chat_window import ChatWindowFileBridge
from nutrifoundation.domain.semantic_equivalence import (
    CanonicalBatchSummary,
    CanonicalCaseResult,
    EquivalenceRelation,
)
from nutrifoundation.io.loaders import load_structured
from nutrifoundation.services.semantic_equivalence import compare_field


FIELDS = (
    "kind",
    "population",
    "intervention",
    "exposure",
    "intervention_or_exposure",
    "comparator",
    "outcome",
    "effect",
    "recommendation",
    "applicability_boundary",
    "anchor",
)


def score_canonical_batch(
    *,
    response_dir: str | Path,
    hidden_reference_path: str | Path,
    batch_id: str,
) -> CanonicalBatchSummary:
    reference = load_structured(hidden_reference_path)
    reference_by_id = {
        item["evidence_id"]: item
        for item in reference["EvidenceUnits"]
    }

    bridge = ChatWindowFileBridge()
    responses = [
        bridge.load_response(path)
        for path in sorted(Path(response_dir).glob("*.response.json"))
    ]
    response_by_evidence = {}
    for response in responses:
        # E0.4 deterministic task IDs end in the same case index.
        suffix = response.task_id.rsplit("-", 1)[-1]
        evidence_id = f"EU-{batch_id}-{suffix}"
        response_by_evidence[evidence_id] = response

    cases: list[CanonicalCaseResult] = []

    for evidence_id, gold in reference_by_id.items():
        response = response_by_evidence.get(evidence_id)
        status = response.status if response is not None else "missing"
        observed = response.output if response is not None else {}

        field_results = []
        for field in FIELDS:
            if gold.get(field) is None:
                continue
            field_results.append(
                compare_field(
                    field,
                    gold.get(field),
                    observed.get(field),
                )
            )

        equivalent = sum(result.equivalent for result in field_results)
        partial = sum(
            result.relation == EquivalenceRelation.PARTIAL.value
            for result in field_results
        )
        mismatch = sum(
            result.relation == EquivalenceRelation.MISMATCH.value
            for result in field_results
        )
        missing = sum(
            result.relation == EquivalenceRelation.MISSING.value
            for result in field_results
        )
        all_equivalent = (
            status == "completed"
            and bool(field_results)
            and all(result.equivalent for result in field_results)
        )

        cases.append(
            CanonicalCaseResult(
                evidence_id=evidence_id,
                source_id=gold["source_id"],
                response_status=status,
                comparable_field_count=len(field_results),
                equivalent_field_count=equivalent,
                partial_field_count=partial,
                mismatch_field_count=mismatch,
                missing_field_count=missing,
                all_critical_fields_equivalent=all_equivalent,
                field_results=tuple(field_results),
            )
        )

    return CanonicalBatchSummary(
        batch_id=batch_id,
        case_count=len(cases),
        completed_response_count=sum(
            case.response_status == "completed"
            for case in cases
        ),
        deferred_count=sum(
            case.response_status == "defer"
            for case in cases
        ),
        comparable_field_count=sum(
            case.comparable_field_count
            for case in cases
        ),
        equivalent_field_count=sum(
            case.equivalent_field_count
            for case in cases
        ),
        partial_field_count=sum(
            case.partial_field_count
            for case in cases
        ),
        mismatch_field_count=sum(
            case.mismatch_field_count
            for case in cases
        ),
        missing_field_count=sum(
            case.missing_field_count
            for case in cases
        ),
        all_critical_equivalent_case_count=sum(
            case.all_critical_fields_equivalent
            for case in cases
        ),
        cases=tuple(cases),
    )


def write_canonical_batch_report(report: CanonicalBatchSummary, path: str | Path) -> None:
    Path(path).write_text(
        json.dumps(report.as_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
