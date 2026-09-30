from __future__ import annotations

from pathlib import Path

from nutrifoundation.adapters.chat_window import ChatWindowFileBridge
from nutrifoundation.domain.semantic_equivalence import (
    SemanticBatchCase,
    SemanticBatchSummary,
)
from nutrifoundation.io.loaders import load_structured
from nutrifoundation.services.semantic_equivalence import compare_field


CRITICAL_FIELDS = (
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


def _evidence_id_from_task_id(task_id: str) -> str:
    suffix = task_id.rsplit("-", 1)[-1]
    return f"EU-B001-{suffix}"


def score_semantic_batch(
    *,
    hidden_reference_path: str | Path,
    response_dir: str | Path,
    batch_id: str = "B001",
) -> SemanticBatchSummary:
    reference = load_structured(hidden_reference_path)
    gold_by_id = {
        item["evidence_id"]: item
        for item in reference["EvidenceUnits"]
    }

    bridge = ChatWindowFileBridge()
    cases: list[SemanticBatchCase] = []
    completed = 0
    deferred = 0

    response_by_evidence = {}
    for path in sorted(Path(response_dir).glob("*.response.json")):
        response = bridge.load_response(path)
        evidence_id = _evidence_id_from_task_id(response.task_id)
        response_by_evidence[evidence_id] = response

    for evidence_id, gold in sorted(gold_by_id.items()):
        response = response_by_evidence.get(evidence_id)
        response_status = response.status if response is not None else "missing"
        if response_status == "completed":
            completed += 1
        elif response_status == "defer":
            deferred += 1

        candidate = (
            dict(response.output)
            if response is not None and response.status == "completed"
            else {}
        )

        field_results = tuple(
            compare_field(
                field,
                gold.get(field),
                candidate.get(field),
            )
            for field in CRITICAL_FIELDS
        )

        comparable = [
            result
            for result in field_results
            if result.relation != "not_applicable"
        ]
        equivalent = [result for result in comparable if result.equivalent]
        non_equivalent = tuple(
            result.field
            for result in comparable
            if not result.equivalent
        )

        all_equivalent = (
            response_status == "completed"
            and bool(comparable)
            and not non_equivalent
        )

        cases.append(
            SemanticBatchCase(
                evidence_id=evidence_id,
                source_id=gold["source_id"],
                response_status=response_status,
                comparable_field_count=len(comparable),
                equivalent_field_count=len(equivalent),
                all_critical_fields_equivalent=all_equivalent,
                non_equivalent_fields=non_equivalent,
                field_results=field_results,
            )
        )

    total_comparable = sum(case.comparable_field_count for case in cases)
    total_equivalent = sum(case.equivalent_field_count for case in cases)
    all_equivalent_count = sum(
        case.all_critical_fields_equivalent for case in cases
    )
    adjudication_count = sum(
        not case.all_critical_fields_equivalent for case in cases
    )
    n = len(cases)

    return SemanticBatchSummary(
        batch_id=batch_id,
        reference_authority="Batch001_F0_reference_not_independent_expert_gold",
        publication_grade=False,
        case_count=n,
        completed_response_count=completed,
        deferred_count=deferred,
        comparable_field_count=total_comparable,
        equivalent_field_count=total_equivalent,
        critical_field_equivalence_rate=(
            total_equivalent / total_comparable if total_comparable else 0.0
        ),
        all_critical_fields_equivalent_count=all_equivalent_count,
        all_critical_fields_equivalent_rate=(
            all_equivalent_count / n if n else 0.0
        ),
        benchmark_adjudication_count=adjudication_count,
        benchmark_adjudication_rate=(
            adjudication_count / n if n else 0.0
        ),
        cases=tuple(cases),
    )
