"""NDF-D0-A2 deterministic runtime validators.

Implements the minimum D0 runtime gate:
V0.1 structural/revision, V0.2 dependency, V0.3 temporal,
and V0.4 projection closure.

Deterministic by design: no LLM judgment is used here.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _walk_scalars(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield ("key", str(key))
            yield from _walk_scalars(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_scalars(child)
    elif isinstance(value, (str, int, float, bool)):
        yield ("value", str(value))


def _ref_key(ref: dict[str, Any] | None) -> str | None:
    if not ref:
        return None
    oid = ref.get("object_id")
    rev = ref.get("revision")
    if oid is None or rev is None:
        return None
    return f"{oid}@{rev}"


def _all_refs(value: Any):
    if isinstance(value, dict):
        if set(value) >= {"object_id", "revision"}:
            yield value
            return
        for child in value.values():
            yield from _all_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_refs(child)


def _object_index(objects: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for obj in objects:
        key = _ref_key(obj.get("ref"))
        if key and key not in out:
            out[key] = obj
    return out


def validate_structural(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    objects = fixture.get("bundle", {}).get("objects", [])

    seen: dict[str, str] = {}
    for obj in objects:
        ref = obj.get("ref", {})
        revision = ref.get("revision")
        if not isinstance(revision, int) or revision < 1:
            failures.append("REF_UNRESOLVED")

        if isinstance(ref.get("object_id"), str) and ref["object_id"].lower() in {
            "latest", "current", "head", "newest"
        }:
            failures.append("REF_UNRESOLVED")

        key = _ref_key(ref)
        if key:
            digest = sha256_obj(obj)
            if key in seen and seen[key] != digest:
                failures.append("REVISION_IMMUTABILITY_VIOLATION")
            seen[key] = digest

        for node in _walk(obj):
            if "tag" not in node:
                continue
            tag = node.get("tag")
            if tag == "VALUE" and ("value" not in node or node.get("value") is None):
                failures.append("CONDITION_COLLAPSE")
            elif tag == "UNAVAILABLE":
                if not node.get("reason"):
                    failures.append("CONDITION_COLLAPSE")
                if "value" in node and node.get("value") is not None:
                    failures.append("FABRICATED_OBSERVATION")
            elif tag == "NOT_APPLICABLE" and not (node.get("reason") or node.get("policy_ref")):
                failures.append("CONDITION_COLLAPSE")

        if obj.get("kind") == "NutritionObservation":
            if obj.get("knowledge_state") == "UNKNOWN":
                slot = obj.get("value", {})
                if slot.get("tag") == "VALUE":
                    failures.extend(["FABRICATED_OBSERVATION", "CONDITION_COLLAPSE"])

            if (
                obj.get("construction_class") in {"CON", "CFM"}
                and obj.get("instance_class") == "REAL_SOURCE_GROUNDED"
            ):
                failures.extend(["EPISTEMIC_COLLAPSE", "SOURCE_CLASS_INFLATION"])

    return sorted(set(failures))


def validate_dependency(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    objects = fixture.get("bundle", {}).get("objects", [])
    index = _object_index(objects)
    known_refs = set(index)

    for obj in objects:
        for ref in _all_refs(obj):
            key = _ref_key(ref)
            registry = ref.get("registry", "NDF_LOCAL")
            if registry == "NDF_LOCAL" and key and key not in known_refs:
                failures.append("REF_UNRESOLVED")

    for episode in [x for x in objects if x.get("kind") == "NutritionDecisionEpisode"]:
        subject = _ref_key(episode.get("subject_ref"))
        deps = episode.get("observation_refs", []) + episode.get("state_refs", [])
        for dep in deps:
            target = index.get(_ref_key(dep))
            if target is not None:
                target_subject = _ref_key(target.get("subject_ref"))
                if subject and target_subject and subject != target_subject:
                    failures.append("SUBJECT_JOIN_ERROR")

    for obj in objects:
        if obj.get("kind") != "NutritionObservation":
            continue
        if obj.get("instance_class") == "REAL_SOURCE_GROUNDED":
            refs = obj.get("source_anchor_refs", [])
            if not refs:
                failures.append("REF_UNRESOLVED")
            for ref in refs:
                target = index.get(_ref_key(ref))
                if not target or target.get("kind") != "SourceAnchor":
                    failures.append("REF_UNRESOLVED")

    return sorted(set(failures))


def validate_temporal(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    bundle = fixture.get("bundle", {})
    objects = bundle.get("objects", [])
    index = _object_index(objects)
    boundary = bundle.get("boundary", {})
    cutoff = _dt(boundary.get("cutoff_time"))
    evidence_cutoff = _dt(boundary.get("evidence_cutoff_time"))

    for ref in boundary.get("allowed_refs", []):
        obj = index.get(_ref_key(ref))
        if obj is None:
            continue

        available = _dt(obj.get("available_time"))
        if cutoff and available and available > cutoff:
            failures.append("TEMPORAL_DEPENDENCY_ERROR")

        public_availability = _dt(obj.get("public_availability_time"))
        if evidence_cutoff and public_availability and public_availability > evidence_cutoff:
            failures.append("TEMPORAL_DEPENDENCY_ERROR")

        derived_available = _dt(obj.get("available_time"))
        if derived_available:
            for dep in obj.get("input_refs", []):
                parent = index.get(_ref_key(dep))
                parent_available = _dt(parent.get("available_time")) if parent else None
                if parent_available and derived_available < parent_available:
                    failures.append("TEMPORAL_DEPENDENCY_ERROR")

    return sorted(set(failures))


def project_bundle(fixture: dict[str, Any]) -> dict[str, Any]:
    bundle = fixture.get("bundle", {})
    policy = fixture.get("projection_policy", {})
    index = _object_index(bundle.get("objects", []))
    projected: list[dict[str, Any]] = []

    allowed_kinds = set(policy.get("allowed_kinds", []))
    forbidden_kinds = set(policy.get("forbidden_kinds", []))
    forbidden_fields = set(policy.get("forbidden_fields", []))

    for ref in bundle.get("boundary", {}).get("allowed_refs", []):
        obj = index.get(_ref_key(ref))
        if not obj:
            continue
        if obj.get("kind") in forbidden_kinds:
            continue
        if allowed_kinds and obj.get("kind") not in allowed_kinds:
            continue

        copy = deepcopy(obj)
        for node in _walk(copy):
            for field in list(node):
                if field in forbidden_fields:
                    node.pop(field, None)
        projected.append(copy)

    return {"objects": projected, "task_text": bundle.get("task_text", "")}


def validate_projection(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    policy = fixture.get("projection_policy", {})
    projected = project_bundle(fixture)
    forbidden_kinds = set(policy.get("forbidden_kinds", []))
    forbidden_fields = {x.lower() for x in policy.get("forbidden_fields", [])}
    forbidden_terms = [x.lower() for x in policy.get("forbidden_terms", [])]

    for obj in projected.get("objects", []):
        if obj.get("kind") in forbidden_kinds:
            failures.append("PROJECTION_LEAKAGE")
        for typ, scalar in _walk_scalars(obj):
            low = scalar.lower()
            if typ == "key" and low in forbidden_fields:
                failures.append("PROJECTION_LEAKAGE")
            if any(term in low for term in forbidden_terms):
                failures.append("PROJECTION_LEAKAGE")

    task = projected.get("task_text", "").lower()
    if any(term in task for term in forbidden_terms):
        failures.append("PROJECTION_LEAKAGE")

    for record in fixture.get("bundle", {}).get("boundary", {}).get("mask_records", []):
        hidden = str(record.get("hidden_value", "")).strip().lower()
        if not hidden:
            continue
        for _, scalar in _walk_scalars(projected):
            sval = scalar.strip().lower()
            if hidden == sval or hidden in sval:
                failures.append("PROJECTION_LEAKAGE")

    return sorted(set(failures))


def validate_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    by_validator = {
        "V0.1": validate_structural(fixture),
        "V0.2": validate_dependency(fixture),
        "V0.3": validate_temporal(fixture),
        "V0.4": validate_projection(fixture),
    }
    failures = sorted({code for values in by_validator.values() for code in values})
    status = "FAIL" if failures else "PASS"
    return {
        "fixture_id": fixture.get("fixture_id"),
        "status": status,
        "failure_codes": failures,
        "validator_results": {
            key: {"status": "FAIL" if values else "PASS", "failure_codes": values}
            for key, values in by_validator.items()
        },
    }


def run_fixture_suite(suite: dict[str, Any]) -> dict[str, Any]:
    results = [validate_fixture(f) for f in suite.get("fixtures", [])]
    correct = 0
    for fixture, result in zip(suite.get("fixtures", []), results):
        expected_status = fixture["expected"]["status"]
        expected_codes = set(fixture["expected"].get("failure_codes", []))
        observed_codes = set(result["failure_codes"])
        ok = result["status"] == expected_status and expected_codes.issubset(observed_codes)
        result["expectation_met"] = ok
        correct += int(ok)

    negatives = [x for x in results if x["fixture_id"].startswith("FX-")]
    positives = [x for x in results if x["fixture_id"].startswith("PF-")]
    return {
        "suite_id": suite.get("suite_id"),
        "contract_version": "NDF-D0-A2-0.1",
        "results": results,
        "summary": {
            "total": len(results),
            "expectations_met": correct,
            "negative_total": len(negatives),
            "negative_correctly_rejected": sum(
                1 for x in negatives if x["status"] == "FAIL" and x["expectation_met"]
            ),
            "positive_total": len(positives),
            "positive_correctly_accepted": sum(
                1 for x in positives if x["status"] == "PASS" and x["expectation_met"]
            ),
        },
    }
