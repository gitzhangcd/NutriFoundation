from __future__ import annotations

from typing import Any

from ..contracts import ValidationCheck, ValidationContext
from ._util import parse_iso, walk


def validate_temporal(
    objects: list[dict[str, Any]], context: ValidationContext
) -> list[ValidationCheck]:
    if not context.cutoff_time:
        return []
    cutoff = parse_iso(context.cutoff_time)
    checks: list[ValidationCheck] = []
    for obj in objects:
        for path, node in walk(obj):
            if not isinstance(node, dict):
                continue
            value = node.get("available_time")
            if not value:
                continue
            try:
                available = parse_iso(value)
            except (TypeError, ValueError):
                checks.append(
                    ValidationCheck(
                        validator_id="V0.3",
                        rule_id="invalid_available_time",
                        status="FAIL",
                        error_code="TEMPORAL_DEPENDENCY_ERROR",
                        object_ref=obj.get("object_id"),
                        path=f"{path}.available_time",
                        expected=f"ISO time <= {context.cutoff_time}",
                        observed=value,
                    )
                )
                continue
            if available > cutoff:
                checks.append(
                    ValidationCheck(
                        validator_id="V0.3",
                        rule_id="available_time_after_cutoff",
                        status="FAIL",
                        error_code="TEMPORAL_DEPENDENCY_ERROR",
                        object_ref=obj.get("object_id"),
                        path=f"{path}.available_time",
                        expected=f"<= {context.cutoff_time}",
                        observed=value,
                    )
                )
    return checks
