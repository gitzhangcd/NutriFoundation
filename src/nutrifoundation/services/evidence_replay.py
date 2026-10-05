from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from nutrifoundation.agents.evidence_extraction import (
    EvidenceExtractionAgent,
    FixtureEvidenceExtractionProvider,
)
from nutrifoundation.agents.evidence_verification import IndependentEvidenceVerifier
from nutrifoundation.connectors.fixture import FixturePubMedConnector
from nutrifoundation.io.loaders import load_structured
from nutrifoundation.persistence.sqlite import SQLiteStore
from nutrifoundation.services.evidence_pipeline import EvidenceProductionService
from nutrifoundation.services.replay import replay_batch001


@dataclass(frozen=True)
class EvidenceReplayReport:
    expected_count: int
    stored_f0_count: int
    payload_match_count: int
    mismatch_count: int
    mismatches: tuple[dict[str, Any], ...]
    source_replay_run_id: str
    evidence_run_id: str
    status: str

    def as_dict(self):
        return asdict(self)


def _support_fixture_text(item: dict) -> str:
    """Regression-only support text.

    This is deliberately generated from the frozen registry and is not
    scientific authority. Live mode must use persisted PubMed/PMC text.
    """
    keys = (
        "population",
        "intervention",
        "exposure",
        "intervention_or_exposure",
        "comparator",
        "outcome",
        "effect",
        "recommendation",
        "applicability_boundary",
    )
    return " | ".join(
        str(item[key])
        for key in keys
        if item.get(key) is not None
    )


def _projection_from_expected(item: dict) -> dict[str, Any]:
    keys = (
        "evidence_id",
        "source_id",
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
    return {key: item.get(key) for key in keys if key in item}


def _projection_from_actual(evidence) -> dict[str, Any]:
    values = {
        "evidence_id": evidence.evidence_id,
        "source_id": evidence.source_id,
        "kind": evidence.kind,
        "population": evidence.population,
        "intervention": evidence.intervention,
        "exposure": evidence.exposure,
        "intervention_or_exposure": evidence.intervention_or_exposure,
        "comparator": evidence.comparator,
        "outcome": evidence.outcome,
        "effect": evidence.effect,
        "recommendation": evidence.recommendation,
        "applicability_boundary": evidence.applicability_boundary,
        "anchor": evidence.anchor,
    }
    return values


def replay_batch001_evidence(
    source_registry_path: str | Path,
    pubmed_fixture_path: str | Path,
    frozen_evidence_registry_path: str | Path,
    store: SQLiteStore,
) -> EvidenceReplayReport:
    source_report = replay_batch001(
        source_registry_path,
        FixturePubMedConnector(pubmed_fixture_path),
        store,
        mode="offline_replay",
    )
    if source_report.status != "PASS":
        return EvidenceReplayReport(
            expected_count=0,
            stored_f0_count=0,
            payload_match_count=0,
            mismatch_count=1,
            mismatches=({"stage": "source_replay", "status": "FAIL"},),
            source_replay_run_id=source_report.run_id,
            evidence_run_id="",
            status="FAIL",
        )

    registry = load_structured(frozen_evidence_registry_path)
    expected = registry["EvidenceUnits"]

    for item in expected:
        store.save_source_text(
            item["source_id"],
            "regression_support_fixture",
            _support_fixture_text(item),
            "Batch001EvidenceRegressionFixture",
        )

    extractor = EvidenceExtractionAgent(
        FixtureEvidenceExtractionProvider(frozen_evidence_registry_path),
        extractor_id="FixtureEvidenceExtractionAgent-v0.1",
    )
    verifier = IndependentEvidenceVerifier(
        verifier_id="IndependentEvidenceVerifier-v0.1"
    )
    service = EvidenceProductionService(
        extractor,
        verifier,
        store,
        mode="offline_replay",
        preferred_text_kinds=("regression_support_fixture",),
        legacy_f0=True,
    )
    mapping = [
        (item["source_id"], item["evidence_id"])
        for item in expected
    ]
    evidence_manifest = service.produce(mapping)

    actual = {
        evidence.evidence_id: evidence
        for evidence in store.list_f0_evidence()
    }

    mismatches: list[dict[str, Any]] = []
    matches = 0

    for item in expected:
        evidence_id = item["evidence_id"]
        stored = actual.get(evidence_id)
        if stored is None:
            mismatches.append(
                {
                    "evidence_id": evidence_id,
                    "field": "evidence",
                    "expected": "present",
                    "actual": "missing",
                }
            )
            continue

        expected_projection = _projection_from_expected(item)
        actual_projection = _projection_from_actual(stored)

        local_mismatch = False
        for key, expected_value in expected_projection.items():
            actual_value = actual_projection.get(key)
            if actual_value != expected_value:
                local_mismatch = True
                mismatches.append(
                    {
                        "evidence_id": evidence_id,
                        "field": key,
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )
        if not local_mismatch:
            matches += 1

    status = (
        "PASS"
        if (
            evidence_manifest.status == "completed"
            and len(actual) == len(expected)
            and not mismatches
        )
        else "FAIL"
    )

    return EvidenceReplayReport(
        expected_count=len(expected),
        stored_f0_count=len(actual),
        payload_match_count=matches,
        mismatch_count=len(mismatches),
        mismatches=tuple(mismatches),
        source_replay_run_id=source_report.run_id,
        evidence_run_id=evidence_manifest.run_id,
        status=status,
    )
