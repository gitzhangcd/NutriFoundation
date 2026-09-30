from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from nutrifoundation.domain.semantic_equivalence import (
    CalibrationConfusionMatrix,
    CalibrationReferenceClass,
    EquivalenceCalibrationSummary,
)
from nutrifoundation.io.loaders import load_structured
from nutrifoundation.services.semantic_equivalence import compare_field


def _matrix(rows: list[tuple[bool, bool]]) -> CalibrationConfusionMatrix:
    tp = sum(expected and predicted for expected, predicted in rows)
    fp = sum((not expected) and predicted for expected, predicted in rows)
    tn = sum((not expected) and (not predicted) for expected, predicted in rows)
    fn = sum(expected and (not predicted) for expected, predicted in rows)
    return CalibrationConfusionMatrix(tp, fp, tn, fn)


def calibrate_fixture(path: str | Path) -> tuple[EquivalenceCalibrationSummary, list[dict[str, Any]]]:
    fixture = load_structured(path)
    reference_class = CalibrationReferenceClass(fixture["reference_class"])

    rows: list[tuple[bool, bool]] = []
    by_field_rows: dict[str, list[tuple[bool, bool]]] = defaultdict(list)
    details: list[dict[str, Any]] = []
    false_positive_ids: list[str] = []
    false_negative_ids: list[str] = []

    for case in fixture["cases"]:
        result = compare_field(
            case["field"],
            case.get("reference"),
            case.get("candidate"),
        )
        expected = bool(case["expected_equivalent"])
        predicted = result.equivalent
        rows.append((expected, predicted))
        by_field_rows[case["field"]].append((expected, predicted))
        if predicted and not expected:
            false_positive_ids.append(case["case_id"])
        if expected and not predicted:
            false_negative_ids.append(case["case_id"])
        details.append(
            {
                "case_id": case["case_id"],
                "field": case["field"],
                "expected_equivalent": expected,
                "predicted_equivalent": predicted,
                "label_provenance": case["label_provenance"],
                "result": result.as_dict(),
            }
        )

    summary = EquivalenceCalibrationSummary(
        reference_class=reference_class.value,
        case_count=len(rows),
        overall=_matrix(rows),
        by_field={
            field: _matrix(field_rows)
            for field, field_rows in sorted(by_field_rows.items())
        },
        false_positive_ids=tuple(false_positive_ids),
        false_negative_ids=tuple(false_negative_ids),
        publication_grade=reference_class == CalibrationReferenceClass.HUMAN_INDEPENDENT,
    )
    return summary, details
