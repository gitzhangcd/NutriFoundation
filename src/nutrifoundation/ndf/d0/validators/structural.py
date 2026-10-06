from __future__ import annotations

from typing import Any

from ..contracts import ValidationCheck, ValidationContext
from ._util import canonical_digest, walk

REQUIRED_ENVELOPE_FIELDS = (
    "object_id",
    "revision_id",
    "kind",
    "schema_version",
    "lifecycle",
    "producer_role",
    "created_time",
    "provenance_refs",
    "dependency_refs",
    "source_class",
    "purpose_release_ref",
    "supersedes_ref",
)
LIFECYCLES = {"DRAFT", "FROZEN", "SUPERSEDED", "WITHDRAWN"}
PURPOSES = {
    "CURATION_DEV",
    "WORKFLOW_DEVELOPMENT",
    "REFERENCE_CONSTRUCTION",
    "MEASUREMENT_CALIBRATION",
    "LOCKED_EVALUATION",
    "EXTERNAL_VALIDATION",
    "FUTURE_TRAINING",
}


def _fail(code: str, obj: dict[str, Any], path: str, expected=None, observed=None):
    return ValidationCheck(
        validator_id="V0.1",
        rule_id=code.lower(),
        status="FAIL",
        error_code=code,
        object_ref=obj.get("object_id"),
        path=path,
        expected=expected,
        observed=observed,
    )


def validate_structural(
    objects: list[dict[str, Any]], context: ValidationContext
) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []
    for obj in objects:
        for field in REQUIRED_ENVELOPE_FIELDS:
            if field not in obj:
                checks.append(_fail("REQUIRED_FIELD_MISSING", obj, f"$.{field}", "present", None))

        lifecycle = obj.get("lifecycle")
        if lifecycle is not None and lifecycle not in LIFECYCLES:
            checks.append(_fail("INVALID_ENUM", obj, "$.lifecycle", sorted(LIFECYCLES), lifecycle))

        purpose = obj.get("purpose_release_ref")
        if purpose is not None and purpose not in PURPOSES:
            checks.append(_fail("INVALID_ENUM", obj, "$.purpose_release_ref", sorted(PURPOSES), purpose))

        key = f"{obj.get('object_id')}@{obj.get('revision_id')}"
        if lifecycle == "FROZEN" and key in context.frozen_revisions:
            observed_digest = canonical_digest(obj)
            expected_digest = context.frozen_revisions[key]
            if observed_digest != expected_digest:
                checks.append(
                    _fail(
                        "REVISION_IMMUTABILITY_VIOLATION",
                        obj,
                        "$",
                        expected_digest,
                        observed_digest,
                    )
                )

        for path, node in walk(obj):
            if not isinstance(node, dict):
                continue

            epistemic = node.get("epistemic_expression")
            normalized = node.get("normalized_interpretation")
            if epistemic == "UNKNOWN" and normalized in {"NORMAL", "NEGATIVE", "ZERO"}:
                checks.append(
                    _fail(
                        "FABRICATED_OBSERVATION",
                        obj,
                        f"{path}.normalized_interpretation",
                        None,
                        normalized,
                    )
                )
                checks.append(
                    _fail(
                        "CONDITION_COLLAPSE",
                        obj,
                        path,
                        "UNKNOWN remains UNKNOWN",
                        f"UNKNOWN -> {normalized}",
                    )
                )

            origin = node.get("construction_origin")
            semantic_origin = node.get("semantic_origin")
            if origin in {"CON", "CFM"} and semantic_origin == "OBSERVED":
                checks.append(
                    _fail(
                        "EPISTEMIC_COLLAPSE",
                        obj,
                        path,
                        "constructed/confirmed condition distinct from observed datum",
                        f"{origin} -> OBSERVED",
                    )
                )
                checks.append(
                    _fail(
                        "SOURCE_CLASS_INFLATION",
                        obj,
                        path,
                        "construction origin preserved",
                        "OBSERVED",
                    )
                )
    return checks
