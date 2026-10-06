from __future__ import annotations

from typing import Any

from ..contracts import ValidationCheck, ValidationContext


def _fail(code: str, obj: dict[str, Any], path: str, expected=None, observed=None):
    return ValidationCheck(
        validator_id="V0.2",
        rule_id=code.lower(),
        status="FAIL",
        error_code=code,
        object_ref=obj.get("object_id"),
        path=path,
        expected=expected,
        observed=observed,
    )


def validate_dependency(
    objects: list[dict[str, Any]], context: ValidationContext
) -> list[ValidationCheck]:
    del context
    checks: list[ValidationCheck] = []
    index = {o.get("object_id"): o for o in objects if o.get("object_id")}

    for obj in objects:
        deps = obj.get("dependency_refs") or []
        for dep_ref in deps:
            dep = index.get(dep_ref)
            if dep is None:
                checks.append(_fail("ORPHAN_REF", obj, "$.dependency_refs", "resolvable", dep_ref))
                continue
            subject = obj.get("subject_id")
            dep_subject = dep.get("subject_id")
            if subject is not None and dep_subject is not None and subject != dep_subject:
                checks.append(
                    _fail(
                        "SUBJECT_JOIN_ERROR",
                        obj,
                        "$.subject_id",
                        dep_subject,
                        subject,
                    )
                )

    graph = {oid: [d for d in (o.get("dependency_refs") or []) if d in index] for oid, o in index.items()}
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str, trail: tuple[str, ...]):
        if node in visiting:
            obj = index[node]
            checks.append(
                _fail("CIRCULAR_DEPENDENCY", obj, "$.dependency_refs", "acyclic", list(trail + (node,)))
            )
            return
        if node in visited:
            return
        visiting.add(node)
        for nxt in graph.get(node, []):
            dfs(nxt, trail + (node,))
        visiting.remove(node)
        visited.add(node)

    for oid in graph:
        dfs(oid, ())
    return checks
