from __future__ import annotations

from typing import Any

from ..contracts import ValidationCheck, ValidationContext
from ._util import walk

FORBIDDEN_SYSTEM_KEYS = {
    "final_reference",
    "adjudicated_reference",
    "nutrition_decision_reference",
    "expert_reference",
    "hidden_reference",
    "reference_id",
    "future_outcome",
    "future_outcomes",
    "hidden_value",
    "gold",
    "gold_label",
}


def validate_projection(
    objects: list[dict[str, Any]], context: ValidationContext
) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []
    for obj in objects:
        payload = obj.get("projected_payload")
        if payload is None:
            continue

        for path, node in walk(payload, "$.projected_payload"):
            if isinstance(node, dict):
                if node.get("visibility") == "MASKED" and "value" in node and node.get("value") is not None:
                    checks.append(
                        ValidationCheck(
                            validator_id="V0.4",
                            rule_id="masked_value_exposed",
                            status="FAIL",
                            error_code="PROJECTION_LEAKAGE",
                            object_ref=obj.get("object_id"),
                            path=path,
                            expected="masked value omitted",
                            observed=node.get("value"),
                        )
                    )

                if context.authorized_view == "SYSTEM_VIEW":
                    for key in FORBIDDEN_SYSTEM_KEYS.intersection(node):
                        if node.get(key) is not None:
                            checks.append(
                                ValidationCheck(
                                    validator_id="V0.4",
                                    rule_id="forbidden_system_view_field",
                                    status="FAIL",
                                    error_code="PROJECTION_LEAKAGE",
                                    object_ref=obj.get("object_id"),
                                    path=f"{path}.{key}",
                                    expected="not present in SYSTEM_VIEW",
                                    observed=node.get(key),
                                )
                            )
    return checks
