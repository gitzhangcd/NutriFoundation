from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from functools import reduce
from operator import add
from typing import Iterable

from nutrifoundation.domain.semantic_worker import ResponseEnvelope
from nutrifoundation.evaluation.v2.compatibility import (
    MAPPING_VERSION,
    CompatibilityCaseV2,
    map_v1_case,
)
from nutrifoundation.evaluation.v2.report import (
    BatchCaseReportV2,
    BatchEvaluationReportV2,
    DimensionAggregateV2,
    FieldAggregateV2,
    InputArtifactV2,
    ResponseSetEvidenceV2,
    StrictBlindEvidenceV2,
)
from nutrifoundation.evaluation.v2.scoring import (
    EVALUATOR_VERSION,
    ScoredCaseV2,
    score_batch_v2,
)
from nutrifoundation.io.loaders import load_structured


REPORT_VERSION = "E0.4.2-E3-A2.6-v1.0"
REFERENCE_AUTHORITY = "Batch001_F0_reference_not_independent_expert_gold"


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_response_set(path: str | Path) -> tuple[ResponseEnvelope, ...]:
    payload = load_structured(path)
    if not isinstance(payload, list):
        raise ValueError("Frozen response set must be a JSON array")
    responses = tuple(ResponseEnvelope.model_validate(item) for item in payload)
    if not responses:
        raise ValueError("Frozen response set is empty")
    return responses


def _strict_blind_evidence(
    responses: tuple[ResponseEnvelope, ...],
) -> StrictBlindEvidenceV2:
    metadata = [response.worker.metadata for response in responses]
    fresh_context = all(bool(item.get("fresh_context_attestation")) for item in metadata)
    prior_batch_exposure = any(
        bool(item.get("prior_batch_exposure", True)) for item in metadata
    )
    hidden_reference_available = any(
        bool(item.get("hidden_reference_available_to_worker", False))
        for item in metadata
    )
    independent_worker_session = all(
        bool(item.get("independent_worker_session")) for item in metadata
    )
    classes = {
        str(item.get("blindness_class") or "")
        for item in metadata
    }
    blindness_class = (
        next(iter(classes))
        if len(classes) == 1
        else "mixed"
    )
    qualifies = (
        fresh_context
        and not prior_batch_exposure
        and not hidden_reference_available
        and independent_worker_session
        and blindness_class == "strict_blind_fresh_context"
    )
    return StrictBlindEvidenceV2(
        fresh_context=fresh_context,
        prior_batch_exposure=prior_batch_exposure,
        hidden_reference_available_to_worker=hidden_reference_available,
        independent_worker_session=independent_worker_session,
        blindness_class=blindness_class,
        qualifies=qualifies,
    )


def _map_response_set(
    *,
    responses: tuple[ResponseEnvelope, ...],
    source_fixture_path: str | Path,
    hidden_reference_path: str | Path,
    task_manifest_path: str | Path,
) -> tuple[CompatibilityCaseV2, ...]:
    source_items = load_structured(source_fixture_path)
    source_by_id = {item["source_id"]: item for item in source_items}

    reference_payload = load_structured(hidden_reference_path)
    reference_items = reference_payload["EvidenceUnits"]
    reference_by_id = {item["evidence_id"]: item for item in reference_items}

    manifest = load_structured(task_manifest_path)
    task_items = manifest["tasks"]
    task_by_id = {item["task_id"]: item for item in task_items}

    response_task_ids = [response.task_id for response in responses]
    if len(response_task_ids) != len(set(response_task_ids)):
        raise ValueError("Frozen response set contains duplicate task_id")

    expected_task_ids = set(task_by_id)
    observed_task_ids = set(response_task_ids)
    if observed_task_ids != expected_task_ids:
        missing = sorted(expected_task_ids - observed_task_ids)
        extra = sorted(observed_task_ids - expected_task_ids)
        raise ValueError(
            "Frozen response set does not exactly cover task manifest: "
            f"missing={missing}, extra={extra}"
        )

    cases: list[CompatibilityCaseV2] = []
    for response in sorted(responses, key=lambda item: item.task_id):
        task_record = task_by_id[response.task_id]
        source_record = source_by_id.get(task_record["source_id"])
        if source_record is None:
            raise ValueError(
                f"Source fixture missing source_id: {task_record['source_id']}"
            )
        reference = reference_by_id.get(task_record["evidence_id"])
        if reference is None:
            raise ValueError(
                f"Hidden reference missing evidence_id: {task_record['evidence_id']}"
            )
        cases.append(
            map_v1_case(
                response,
                task_record=task_record,
                source_record=source_record,
                reference=reference,
            )
        )
    return tuple(cases)


def _aggregate(
    dimension: str,
    values: Iterable[float | None],
    *,
    eligible_case_count: int,
) -> DimensionAggregateV2:
    scores = [value for value in values if value is not None]
    return DimensionAggregateV2(
        dimension=dimension,
        eligible_case_count=eligible_case_count,
        scored_case_count=len(scores),
        # Preserve v0.1's Python 3.11 left-to-right arithmetic on Python 3.12+.
        mean_score=(reduce(add, scores, 0) / len(scores)) if scores else None,
        min_score=min(scores) if scores else None,
        max_score=max(scores) if scores else None,
    )


def _dimension_summary(
    mapped: tuple[CompatibilityCaseV2, ...],
    scored: tuple[ScoredCaseV2, ...],
) -> tuple[DimensionAggregateV2, ...]:
    completed = [
        (case, score)
        for case, score in zip(mapped, scored, strict=True)
        if case.response_status == "completed"
    ]

    scientific = [
        score.evaluation.scientific_core.score
        for _, score in completed
    ]
    ontology = [
        score.evaluation.ontology.score
        for _, score in completed
    ]
    numeric = [
        score.evaluation.numeric.score
        for _, score in completed
        if score.evaluation.numeric.normalized_numeric_fields > 0
    ]
    provenance = [
        score.evaluation.provenance.score
        for score in scored
        if score.evaluation.provenance.score is not None
    ]
    abstention = [
        score.evaluation.abstention.score
        for score in scored
        if score.evaluation.abstention.applicable
    ]

    return (
        _aggregate(
            "scientific_semantic_recovery",
            scientific,
            eligible_case_count=len(completed),
        ),
        _aggregate(
            "ontology_alignment",
            ontology,
            eligible_case_count=len(completed),
        ),
        _aggregate(
            "provenance_recovery",
            provenance,
            eligible_case_count=len(provenance),
        ),
        _aggregate(
            "numeric_fidelity",
            numeric,
            eligible_case_count=len(numeric),
        ),
        _aggregate(
            "safe_abstention_quality",
            abstention,
            eligible_case_count=len(abstention),
        ),
    )


def _field_summary(
    mapped: tuple[CompatibilityCaseV2, ...],
    scored: tuple[ScoredCaseV2, ...],
) -> tuple[FieldAggregateV2, ...]:
    values: dict[tuple[str, str], list[float]] = defaultdict(list)
    relations: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    eligible: Counter[tuple[str, str]] = Counter()

    completed_ids = {
        case.task_id
        for case in mapped
        if case.response_status == "completed"
    }

    for score in scored:
        for item in score.field_comparisons:
            if not item.applicable:
                continue
            if (
                item.dimension in {"scientific_core", "ontology", "numeric"}
                and score.evaluation.task_id not in completed_ids
            ):
                continue
            key = (item.dimension, item.field)
            eligible[key] += 1
            relations[key][item.relation] += 1
            if item.score is not None:
                values[key].append(item.score)

    return tuple(
        FieldAggregateV2(
            dimension=dimension,
            field=field,
            eligible_case_count=eligible[(dimension, field)],
            scored_case_count=len(values[(dimension, field)]),
            mean_score=(
                reduce(add, values[(dimension, field)], 0) / len(values[(dimension, field)])
                if values[(dimension, field)]
                else None
            ),
            relation_counts=dict(sorted(relations[(dimension, field)].items())),
        )
        for dimension, field in sorted(eligible)
    )


def run_frozen_response_set_v2(
    *,
    response_set_path: str | Path,
    source_fixture_path: str | Path,
    hidden_reference_path: str | Path,
    task_manifest_path: str | Path,
    batch_id: str = "B001",
    evaluated_at: datetime | None = None,
    expected_response_set_sha256: str | None = None,
) -> BatchEvaluationReportV2:
    response_set_path = Path(response_set_path)
    source_fixture_path = Path(source_fixture_path)
    hidden_reference_path = Path(hidden_reference_path)
    task_manifest_path = Path(task_manifest_path)

    response_sha = sha256_file(response_set_path)
    if (
        expected_response_set_sha256 is not None
        and response_sha != expected_response_set_sha256
    ):
        raise ValueError(
            "Frozen response set SHA-256 mismatch: "
            f"{response_sha} != {expected_response_set_sha256}"
        )

    responses = _load_response_set(response_set_path)
    attestation = _strict_blind_evidence(responses)
    if not attestation.qualifies:
        raise ValueError(
            "Frozen response set does not qualify as strict_blind_fresh_context: "
            f"{attestation.model_dump(mode='json')}"
        )

    mapped = _map_response_set(
        responses=responses,
        source_fixture_path=source_fixture_path,
        hidden_reference_path=hidden_reference_path,
        task_manifest_path=task_manifest_path,
    )

    timestamp = evaluated_at or datetime.now(timezone.utc)
    scored = score_batch_v2(mapped, evaluated_at=timestamp)

    status_counts = Counter(response.status for response in responses)
    cases = tuple(
        BatchCaseReportV2(
            task_id=case.task_id,
            response_id=case.response_id,
            evidence_id=case.evidence_id,
            source_id=case.source_id,
            response_status=case.response_status,
            score_vector=score.score_vector,
            evaluation=score.evaluation,
            field_comparisons=score.field_comparisons,
        )
        for case, score in zip(mapped, scored, strict=True)
    )

    return BatchEvaluationReportV2(
        report_version=REPORT_VERSION,
        evaluator_version=EVALUATOR_VERSION,
        mapping_version=MAPPING_VERSION,
        batch_id=batch_id,
        evaluated_at=timestamp,
        reference_authority=REFERENCE_AUTHORITY,
        publication_grade=False,
        response_set=ResponseSetEvidenceV2(
            path=str(response_set_path),
            sha256=response_sha,
            response_count=len(responses),
            completed_count=status_counts.get("completed", 0),
            deferred_count=status_counts.get("defer", 0),
            failed_count=status_counts.get("failed", 0),
            attestation=attestation,
        ),
        source_fixture=InputArtifactV2(
            path=str(source_fixture_path),
            sha256=sha256_file(source_fixture_path),
        ),
        hidden_reference=InputArtifactV2(
            path=str(hidden_reference_path),
            sha256=sha256_file(hidden_reference_path),
        ),
        task_manifest=InputArtifactV2(
            path=str(task_manifest_path),
            sha256=sha256_file(task_manifest_path),
        ),
        aggregation_policy={
            "scientific_semantic_recovery": "completed_responses_only",
            "ontology_alignment": "completed_responses_only",
            "numeric_fidelity": "completed_responses_with_reference_numeric_fields_only",
            "provenance_recovery": "all_cases_with_applicable_provenance_score",
            "safe_abstention_quality": "cases_where_abstention_is_required_or_observed",
            "overall_score": "forbidden",
        },
        dimension_summary=_dimension_summary(mapped, scored),
        field_summary=_field_summary(mapped, scored),
        cases=cases,
    )


def write_batch_report_v2(
    report: BatchEvaluationReportV2,
    path: str | Path,
) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump_json(indent=2) + "\n"
    path.write_text(payload, encoding="utf-8")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    checksum_path = path.with_suffix(path.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return digest
