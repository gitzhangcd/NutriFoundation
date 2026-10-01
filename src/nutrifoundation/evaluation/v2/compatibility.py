from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import Field

from nutrifoundation.adapters.chat_window import ChatWindowFileBridge
from nutrifoundation.domain.models import FrozenModel
from nutrifoundation.domain.semantic_worker import ResponseEnvelope
from nutrifoundation.io.loaders import load_structured
from nutrifoundation.services.canonicalization import canonicalize


MAPPING_VERSION = "E0.4.2-E3-A2.4-v0.1"

_SOURCE_TYPE_ALIASES = {
    "rct": "randomized_controlled_trial",
    "randomized_controlled_trial": "randomized_controlled_trial",
    "randomised_controlled_trial": "randomized_controlled_trial",
    "cohort": "cohort",
    "metaanalysis": "meta_analysis",
    "meta_analysis": "meta_analysis",
    "systematicreview": "systematic_review",
    "systematic_review": "systematic_review",
    "guideline": "guideline",
    "consensus": "consensus",
}

_KIND_TO_CLAIM_TYPE = {
    "intervention_effect": "interventional_effect",
    "synthesis_effect": "evidence_synthesis",
    "observational_association": "observational_association",
    "observational_association_synthesis": "observational_association",
    "guideline_scope_and_recommendation": "recommendation",
    "guideline_recommendation": "recommendation",
    "consensus_recommendation": "recommendation",
}

_PMID_RE = re.compile(r"\bPMID\s*[:#]?\s*(\d+)\b", re.I)
_PMCID_RE = re.compile(r"\b(PMC\d+)\b", re.I)
_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", re.I)


class CanonicalScientificPayload(FrozenModel):
    population: Any | None = None
    intervention_exposure: Any | None = None
    comparator: Any | None = None
    outcome: Any | None = None
    effect: Any | None = None
    recommendation: Any | None = None
    applicability_boundary: Any | None = None


class CanonicalOntology(FrozenModel):
    study_design: str | None = None
    claim_type: str | None = None
    evidence_role: str | None = None


class CanonicalNumericPayload(FrozenModel):
    by_field: dict[str, tuple[str, ...]] = Field(default_factory=dict)

    @property
    def fields_with_numeric_content(self) -> tuple[str, ...]:
        return tuple(sorted(self.by_field))

    @property
    def numeric_field_count(self) -> int:
        return len(self.by_field)


class CanonicalProvenance(FrozenModel):
    semantic_anchor: str | None = None
    legacy_anchor: str | None = None
    provided_identifiers: tuple[str, ...] = ()
    context_visible_identifiers: tuple[str, ...] = ()
    context_retrieval_identifier: str | None = None


class CanonicalArtifactV2(FrozenModel):
    scientific: CanonicalScientificPayload
    ontology: CanonicalOntology
    numeric: CanonicalNumericPayload
    provenance: CanonicalProvenance


class CanonicalAbstentionInput(FrozenModel):
    abstained: bool
    source_information_insufficient: bool | None = None
    uncertainties: tuple[str, ...] = ()


class CompatibilityMetadata(FrozenModel):
    mapping_version: str = MAPPING_VERSION
    worker_visible_information: tuple[str, ...]
    reference_visible_information: tuple[str, ...]


class CompatibilityCaseV2(FrozenModel):
    task_id: str
    response_id: str
    task_sha256: str
    source_text_sha256: str
    contract_version: str
    response_schema_version: str
    evidence_id: str
    source_id: str
    response_status: str
    candidate: CanonicalArtifactV2
    reference: CanonicalArtifactV2
    abstention: CanonicalAbstentionInput
    metadata: CompatibilityMetadata


def _snake(value: str) -> str:
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value)
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value)
    return value.strip("_").lower()


def normalize_study_design(source_type: str | None) -> str | None:
    if not source_type:
        return None
    key = _snake(source_type).replace("_", "")
    if key in _SOURCE_TYPE_ALIASES:
        return _SOURCE_TYPE_ALIASES[key]
    snake = _snake(source_type)
    return _SOURCE_TYPE_ALIASES.get(snake, snake)


def infer_claim_type(
    *,
    kind: str | None,
    payload: dict[str, Any],
    study_design: str | None,
) -> str | None:
    if kind:
        normalized_kind = _snake(kind)
        if normalized_kind in _KIND_TO_CLAIM_TYPE:
            return _KIND_TO_CLAIM_TYPE[normalized_kind]

    if payload.get("recommendation") is not None:
        return "recommendation"
    if payload.get("exposure") is not None and payload.get("intervention") is None:
        return "observational_association"
    if payload.get("intervention") is not None:
        return "interventional_effect"
    if study_design in {"guideline", "consensus"}:
        return "recommendation"
    if study_design in {"meta_analysis", "systematic_review"}:
        return "evidence_synthesis"
    return _snake(kind) if kind else None


def infer_evidence_role(study_design: str | None) -> str | None:
    if study_design in {"randomized_controlled_trial", "cohort"}:
        return "primary_study"
    if study_design in {"meta_analysis", "systematic_review"}:
        return "evidence_synthesis"
    if study_design == "guideline":
        return "guideline"
    if study_design == "consensus":
        return "consensus"
    return None


def _first_not_none(*values: Any) -> Any | None:
    for value in values:
        if value is not None:
            return value
    return None


def map_scientific_payload(payload: dict[str, Any]) -> CanonicalScientificPayload:
    return CanonicalScientificPayload(
        population=payload.get("population"),
        intervention_exposure=_first_not_none(
            payload.get("intervention"),
            payload.get("exposure"),
            payload.get("intervention_or_exposure"),
        ),
        comparator=payload.get("comparator"),
        outcome=payload.get("outcome"),
        effect=payload.get("effect"),
        recommendation=payload.get("recommendation"),
        applicability_boundary=payload.get("applicability_boundary"),
    )


def _numeric_payload(
    scientific: CanonicalScientificPayload,
) -> CanonicalNumericPayload:
    field_values = {
        "population": scientific.population,
        "intervention_exposure": scientific.intervention_exposure,
        "comparator": scientific.comparator,
        "outcome": scientific.outcome,
        "effect": scientific.effect,
        "recommendation": scientific.recommendation,
        "applicability_boundary": scientific.applicability_boundary,
    }
    by_field: dict[str, tuple[str, ...]] = {}
    for field, value in field_values.items():
        if value is None:
            continue
        canonical_field = (
            "intervention" if field == "intervention_exposure" else field
        )
        numbers = canonicalize(canonical_field, value).numbers
        if numbers:
            by_field[field] = tuple(numbers)
    return CanonicalNumericPayload(by_field=by_field)


def _provided_identifiers(anchor: str | None) -> tuple[str, ...]:
    if not anchor:
        return ()
    values: list[str] = []
    values.extend(f"pmid:{item}" for item in _PMID_RE.findall(anchor))
    values.extend(f"pmcid:{item.upper()}" for item in _PMCID_RE.findall(anchor))
    values.extend(f"doi:{item.lower()}" for item in _DOI_RE.findall(anchor))
    return tuple(dict.fromkeys(values))


def _context_identifiers(source_record: dict[str, Any]) -> tuple[str, ...]:
    snapshot = source_record.get("source_snapshot") or {}
    identifiers = snapshot.get("identifiers") or {}
    values: list[str] = []
    for key in ("pmid", "pmcid", "doi"):
        value = identifiers.get(key)
        if value:
            normalized = str(value).upper() if key == "pmcid" else str(value)
            if key == "doi":
                normalized = normalized.lower()
            values.append(f"{key}:{normalized}")
    return tuple(values)


def map_provenance(
    payload: dict[str, Any],
    source_record: dict[str, Any],
) -> CanonicalProvenance:
    legacy_anchor = payload.get("anchor")
    return CanonicalProvenance(
        semantic_anchor=payload.get("source_span"),
        legacy_anchor=legacy_anchor,
        provided_identifiers=_provided_identifiers(legacy_anchor),
        context_visible_identifiers=_context_identifiers(source_record),
        context_retrieval_identifier=source_record.get("source_url"),
    )


def map_artifact(
    payload: dict[str, Any],
    source_record: dict[str, Any],
) -> CanonicalArtifactV2:
    study_design = normalize_study_design(
        (source_record.get("source_snapshot") or {}).get("source_type")
    )
    scientific = map_scientific_payload(payload)
    return CanonicalArtifactV2(
        scientific=scientific,
        ontology=CanonicalOntology(
            study_design=study_design,
            claim_type=infer_claim_type(
                kind=payload.get("kind"),
                payload=payload,
                study_design=study_design,
            ),
            evidence_role=infer_evidence_role(study_design),
        ),
        numeric=_numeric_payload(scientific),
        provenance=map_provenance(payload, source_record),
    )


def _source_information_insufficient(source_text: str | None) -> bool:
    if not source_text or not source_text.strip():
        return True
    normalized = source_text.casefold()
    return (
        "pubmed abstract: unavailable" in normalized
        or "abstract unavailable" in normalized
        or "abstract is unavailable" in normalized
    )


def _assert_binding(
    response: ResponseEnvelope,
    task_record: dict[str, Any],
    source_record: dict[str, Any],
    reference: dict[str, Any],
) -> None:
    expected = {
        "task_id": task_record["task_id"],
        "task_sha256": task_record["task_sha256"],
        "source_text_sha256": task_record["source_text_sha256"],
        "contract_version": task_record["contract_version"],
        "response_schema_version": task_record["response_schema_version"],
    }
    observed = {
        "task_id": response.task_id,
        "task_sha256": response.task_sha256,
        "source_text_sha256": response.source_text_sha256,
        "contract_version": response.contract_version,
        "response_schema_version": response.response_schema_version,
    }
    mismatches = [
        key for key, expected_value in expected.items()
        if observed[key] != expected_value
    ]
    if mismatches:
        raise ValueError(
            "Frozen V1 response does not bind to task manifest: "
            + ", ".join(mismatches)
        )

    if source_record.get("source_id") != task_record.get("source_id"):
        raise ValueError("Source fixture does not bind to task manifest source_id")
    if source_record.get("evidence_id") != task_record.get("evidence_id"):
        raise ValueError("Source fixture does not bind to task manifest evidence_id")
    if reference.get("source_id") != task_record.get("source_id"):
        raise ValueError("Hidden reference does not bind to task manifest source_id")
    if reference.get("evidence_id") != task_record.get("evidence_id"):
        raise ValueError("Hidden reference does not bind to task manifest evidence_id")


def map_v1_case(
    response: ResponseEnvelope,
    *,
    task_record: dict[str, Any],
    source_record: dict[str, Any],
    reference: dict[str, Any],
) -> CompatibilityCaseV2:
    _assert_binding(response, task_record, source_record, reference)

    candidate_payload = dict(response.output)
    reference_payload = dict(reference)
    return CompatibilityCaseV2(
        task_id=response.task_id,
        response_id=response.response_id,
        task_sha256=response.task_sha256,
        source_text_sha256=response.source_text_sha256,
        contract_version=response.contract_version,
        response_schema_version=response.response_schema_version,
        evidence_id=task_record["evidence_id"],
        source_id=task_record["source_id"],
        response_status=response.status,
        candidate=map_artifact(candidate_payload, source_record),
        reference=map_artifact(reference_payload, source_record),
        abstention=CanonicalAbstentionInput(
            abstained=response.status == "defer",
            source_information_insufficient=_source_information_insufficient(
                source_record.get("source_text")
            ),
            uncertainties=response.uncertainties,
        ),
        metadata=CompatibilityMetadata(
            worker_visible_information=(
                "source_text",
                "source_snapshot.source_type",
                "source_snapshot.identifiers",
                "source_snapshot.publication_types",
                "source_url",
                "task_contract",
            ),
            reference_visible_information=(
                "frozen_evidence_unit",
                "source_fixture",
                "task_manifest",
            ),
        ),
    )


def map_frozen_v1_batch(
    *,
    response_dir: str | Path,
    source_fixture_path: str | Path,
    hidden_reference_path: str | Path,
    task_manifest_path: str | Path,
) -> tuple[CompatibilityCaseV2, ...]:
    response_dir = Path(response_dir)
    response_paths = sorted(response_dir.glob("*.response.json"))
    if not response_paths:
        raise ValueError(f"No frozen V1 responses found in {response_dir}")

    source_items = load_structured(source_fixture_path)
    source_by_id = {item["source_id"]: item for item in source_items}

    reference_payload = load_structured(hidden_reference_path)
    reference_items = reference_payload["EvidenceUnits"]
    reference_by_id = {item["evidence_id"]: item for item in reference_items}

    manifest = load_structured(task_manifest_path)
    task_items = manifest["tasks"]
    task_by_id = {item["task_id"]: item for item in task_items}

    bridge = ChatWindowFileBridge()
    cases: list[CompatibilityCaseV2] = []
    seen_tasks: set[str] = set()

    for path in response_paths:
        response = bridge.load_response(path)
        if response.task_id in seen_tasks:
            raise ValueError(f"Duplicate frozen V1 response task_id: {response.task_id}")
        seen_tasks.add(response.task_id)

        task_record = task_by_id.get(response.task_id)
        if task_record is None:
            raise ValueError(
                f"Frozen V1 response task_id missing from task manifest: "
                f"{response.task_id}"
            )

        source_record = source_by_id.get(task_record["source_id"])
        if source_record is None:
            raise ValueError(
                f"Source fixture missing source_id: {task_record['source_id']}"
            )

        reference = reference_by_id.get(task_record["evidence_id"])
        if reference is None:
            raise ValueError(
                f"Hidden reference missing evidence_id: "
                f"{task_record['evidence_id']}"
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
