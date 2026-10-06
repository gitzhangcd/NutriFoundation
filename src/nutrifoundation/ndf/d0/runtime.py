from __future__ import annotations

from uuid import uuid4

from .contracts import ValidationContext, ValidationReport
from .validators import (
    validate_dependency,
    validate_projection,
    validate_structural,
    validate_temporal,
)


def validate_objects(
    objects: list[dict],
    context: ValidationContext | None = None,
    *,
    run_id: str | None = None,
) -> ValidationReport:
    context = context or ValidationContext()
    checks = []
    for validator in (
        validate_structural,
        validate_dependency,
        validate_temporal,
        validate_projection,
    ):
        checks.extend(validator(objects, context))

    return ValidationReport(
        run_id=run_id or f"NDF-D0-{uuid4()}",
        contract_version=context.contract_version,
        projection_policy_version=context.projection_policy_version,
        target_refs=[o.get("object_id", "<missing-object-id>") for o in objects],
        checks=checks,
    )
