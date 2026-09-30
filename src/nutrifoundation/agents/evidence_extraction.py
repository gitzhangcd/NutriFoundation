from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from nutrifoundation.domain.evidence_pipeline import EvidenceExtractionCandidate
from nutrifoundation.domain.models import EvidenceUnit, Provenance, SourceArtifact
from nutrifoundation.io.loaders import load_structured


@dataclass(frozen=True)
class ExtractionOutput:
    evidence: EvidenceUnit
    confidence: float
    method: str


class EvidenceExtractionProvider(Protocol):
    def extract(
        self,
        source: SourceArtifact,
        source_text: str,
        evidence_id: str,
        *,
        run_id: str,
    ) -> ExtractionOutput: ...


def _fixture_item_to_evidence(
    item: dict,
    *,
    run_id: str,
    provider: str,
) -> EvidenceUnit:
    return EvidenceUnit(
        evidence_id=item["evidence_id"],
        source_id=item["source_id"],
        kind=item.get("kind"),
        population=item["population"],
        intervention=item.get("intervention"),
        exposure=item.get("exposure"),
        intervention_or_exposure=item.get("intervention_or_exposure"),
        comparator=item.get("comparator"),
        outcome=item["outcome"],
        effect=item.get("effect"),
        recommendation=item.get("recommendation"),
        applicability_boundary=item.get("applicability_boundary"),
        anchor=item.get("anchor"),
        verification_status="candidate",
        status="candidate",
        verification=tuple(item.get("verification", [])),
        provenance=Provenance(
            source="Batch001 regression fixture",
            provider=provider,
            retrieved_at=datetime.now(timezone.utc),
            metadata={
                "run_id": run_id,
                "regression_fixture_only": True,
                "scientific_authority": False,
            },
        ),
    )


class FixtureEvidenceExtractionProvider:
    """Deterministic regression provider.

    It replays an already-frozen EvidenceUnit registry. It is NOT scientific
    authority and MUST NOT be used to create new scientific evidence.
    """

    def __init__(self, frozen_registry_path: str | Path):
        data = load_structured(frozen_registry_path)
        self._items = {
            item["evidence_id"]: item
            for item in data["EvidenceUnits"]
        }

    def extract(
        self,
        source: SourceArtifact,
        source_text: str,
        evidence_id: str,
        *,
        run_id: str,
    ) -> ExtractionOutput:
        item = self._items[evidence_id]
        if item["source_id"] != source.source_id:
            raise ValueError(
                f"Fixture source mismatch for {evidence_id}: "
                f"{item['source_id']} != {source.source_id}"
            )
        return ExtractionOutput(
            evidence=_fixture_item_to_evidence(
                item,
                run_id=run_id,
                provider=self.__class__.__name__,
            ),
            confidence=1.0,
            method="deterministic_regression_fixture",
        )


class SubprocessEvidenceExtractionProvider:
    """Provider-agnostic adapter for an external LLM/agent process.

    The configured command receives one JSON document on stdin and MUST emit
    one JSON object on stdout with:
      {"evidence": {...EvidenceUnit fields...}, "confidence": 0..1}

    This keeps the core engine independent of any model vendor.
    """

    def __init__(self, command: list[str], *, timeout: int = 120):
        if not command:
            raise ValueError("command is required")
        self.command = command
        self.timeout = timeout

    def extract(
        self,
        source: SourceArtifact,
        source_text: str,
        evidence_id: str,
        *,
        run_id: str,
    ) -> ExtractionOutput:
        payload = {
            "task": "extract_evidence_unit",
            "contract_version": "E0.3-v0.1",
            "evidence_id": evidence_id,
            "source": source.model_dump(mode="json"),
            "source_text": source_text,
            "rules": [
                "Association must not be upgraded to causation.",
                "Guideline/consensus statements must remain source-stated recommendations.",
                "Every numeric effect must be copied faithfully from source text.",
                "Applicability boundary and source anchor are required.",
            ],
        }
        result = subprocess.run(
            self.command,
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=self.timeout,
            check=True,
        )
        response = json.loads(result.stdout)
        evidence_payload = dict(response["evidence"])
        evidence_payload["evidence_id"] = evidence_id
        evidence_payload["source_id"] = source.source_id
        evidence_payload["verification_status"] = "candidate"
        evidence_payload["status"] = "candidate"
        evidence_payload["provenance"] = {
            "source": source.provenance.source,
            "provider": self.__class__.__name__,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "run_id": run_id,
                "external_command": self.command,
            },
        }
        evidence = EvidenceUnit.model_validate(evidence_payload)
        return ExtractionOutput(
            evidence=evidence,
            confidence=float(response.get("confidence", 0.0)),
            method="external_subprocess_json",
        )


class EvidenceExtractionAgent:
    def __init__(
        self,
        provider: EvidenceExtractionProvider,
        *,
        extractor_id: str = "EvidenceExtractionAgent-v0.1",
    ):
        self.provider = provider
        self.extractor_id = extractor_id

    def extract(
        self,
        source: SourceArtifact,
        source_text: str,
        evidence_id: str,
        *,
        run_id: str,
    ) -> EvidenceExtractionCandidate:
        output = self.provider.extract(
            source,
            source_text,
            evidence_id,
            run_id=run_id,
        )
        digest = hashlib.sha256(source_text.encode("utf-8")).hexdigest()
        return EvidenceExtractionCandidate(
            candidate_id=f"CAND-{run_id}-{evidence_id}",
            evidence=output.evidence,
            extractor_id=self.extractor_id,
            extraction_method=output.method,
            extraction_confidence=output.confidence,
            source_text_sha256=digest,
            created_at=datetime.now(timezone.utc),
            provenance=Provenance(
                source=source.provenance.source,
                provider=self.__class__.__name__,
                retrieved_at=datetime.now(timezone.utc),
                lineage_refs=(source.source_id,),
                metadata={
                    "run_id": run_id,
                    "source_text_sha256": digest,
                    "provider": self.provider.__class__.__name__,
                },
            ),
        )
