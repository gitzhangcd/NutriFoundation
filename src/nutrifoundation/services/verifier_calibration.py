from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from nutrifoundation.agents.evidence_extraction import EvidenceExtractionAgent, ExtractionOutput
from nutrifoundation.agents.evidence_verification import IndependentEvidenceVerifier
from nutrifoundation.domain.enums import SourceType
from nutrifoundation.domain.models import EvidenceUnit, Provenance, SourceArtifact
from nutrifoundation.domain.semantic_equivalence import (
    CalibrationConfusionMatrix,
    CalibrationReferenceClass,
    EquivalenceCalibrationSummary,
)
from nutrifoundation.io.loaders import load_structured


class _StaticProvider:
    def __init__(self, evidence: EvidenceUnit):
        self.evidence = evidence

    def extract(self, source, source_text, evidence_id, *, run_id):
        return ExtractionOutput(
            evidence=self.evidence,
            confidence=1.0,
            method="verifier_calibration_fixture",
        )


def _matrix(rows: list[tuple[bool, bool]]) -> CalibrationConfusionMatrix:
    tp = sum(expected and predicted for expected, predicted in rows)
    fp = sum((not expected) and predicted for expected, predicted in rows)
    tn = sum((not expected) and (not predicted) for expected, predicted in rows)
    fn = sum(expected and (not predicted) for expected, predicted in rows)
    return CalibrationConfusionMatrix(tp, fp, tn, fn)


def _build_source(case: dict[str, Any]) -> SourceArtifact:
    return SourceArtifact(
        source_id=case["source_id"],
        source_type=SourceType(case["source_type"]),
        title=case.get("title", "Calibration source"),
        provenance=Provenance(source="contract-generated verifier calibration"),
    )


def _build_evidence(case: dict[str, Any]) -> EvidenceUnit:
    payload = dict(case["evidence"])
    payload.update(
        {
            "evidence_id": case["evidence_id"],
            "source_id": case.get("evidence_source_id", case["source_id"]),
            "verification_status": "candidate",
            "status": "candidate",
            "provenance": Provenance(source="contract-generated verifier calibration"),
        }
    )
    return EvidenceUnit(**payload)


def calibrate_verifier_fixture(
    path: str | Path,
) -> tuple[EquivalenceCalibrationSummary, list[dict[str, Any]]]:
    fixture = load_structured(path)
    reference_class = CalibrationReferenceClass(fixture["reference_class"])
    verifier = IndependentEvidenceVerifier(verifier_id="VerifierCalibration-v0.1")

    rows: list[tuple[bool, bool]] = []
    by_check: dict[str, list[tuple[bool, bool]]] = defaultdict(list)
    details: list[dict[str, Any]] = []
    fps: list[str] = []
    fns: list[str] = []

    for case in fixture["cases"]:
        source = _build_source(case)
        evidence = _build_evidence(case)
        source_text = case["source_text"]
        extractor_id = case.get("extractor_id", "CalibrationExtractor-v0.1")
        candidate = EvidenceExtractionAgent(
            _StaticProvider(evidence),
            extractor_id=extractor_id,
        ).extract(
            source,
            source_text,
            evidence.evidence_id,
            run_id="RUN-E041-VERIFIER-CAL",
        )

        verifier_id = case.get("verifier_id", verifier.verifier_id)
        active_verifier = IndependentEvidenceVerifier(verifier_id=verifier_id)
        record = active_verifier.verify(
            candidate,
            source,
            source_text,
            run_id="RUN-E041-VERIFIER-CAL",
        )

        expected = bool(case["expected_verified"])
        predicted = record.status == "verified"
        rows.append((expected, predicted))

        target_check = case.get("target_check", "overall")
        by_check[target_check].append((expected, predicted))

        if predicted and not expected:
            fps.append(case["case_id"])
        if expected and not predicted:
            fns.append(case["case_id"])

        details.append(
            {
                "case_id": case["case_id"],
                "target_check": target_check,
                "expected_verified": expected,
                "predicted_verified": predicted,
                "status": record.status,
                "errors": list(record.errors),
                "checks": record.checks.model_dump(),
                "label_provenance": case["label_provenance"],
            }
        )

    summary = EquivalenceCalibrationSummary(
        reference_class=reference_class.value,
        case_count=len(rows),
        overall=_matrix(rows),
        by_field={
            key: _matrix(values)
            for key, values in sorted(by_check.items())
        },
        false_positive_ids=tuple(fps),
        false_negative_ids=tuple(fns),
        publication_grade=reference_class == CalibrationReferenceClass.HUMAN_INDEPENDENT,
    )
    return summary, details
