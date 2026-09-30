from __future__ import annotations

from datetime import datetime, timezone

from nutrifoundation.domain.evidence_pipeline import (
    EvidenceExtractionCandidate,
    EvidenceVerificationRecord,
    F0FreezeRecord,
)
from nutrifoundation.domain.models import EvidenceUnit, Provenance


class F0FreezeEngine:
    def freeze(
        self,
        candidate: EvidenceExtractionCandidate,
        verification: EvidenceVerificationRecord,
        *,
        run_id: str,
    ) -> tuple[EvidenceUnit, F0FreezeRecord]:
        if verification.status != "verified":
            raise ValueError("F0 freeze requires verified EvidenceVerificationRecord")
        if verification.candidate_id != candidate.candidate_id:
            raise ValueError("verification does not belong to candidate")
        if verification.evidence_id != candidate.evidence.evidence_id:
            raise ValueError("evidence identity mismatch")
        if verification.source_text_sha256 != candidate.source_text_sha256:
            raise ValueError("source-text hash mismatch")

        passed_checks = tuple(
            key
            for key, value in verification.checks.model_dump().items()
            if value
        )

        evidence = candidate.evidence.model_copy(
            update={
                "verification_status": "frozen_F0",
                "status": "frozen_F0",
                "verification": passed_checks,
                "provenance": Provenance(
                    source=candidate.evidence.provenance.source,
                    provider=self.__class__.__name__,
                    retrieved_at=datetime.now(timezone.utc),
                    lineage_refs=(
                        candidate.candidate_id,
                        verification.verification_id,
                    ),
                    metadata={
                        "run_id": run_id,
                        "freeze_level": "F0",
                        "extractor_id": candidate.extractor_id,
                        "verifier_id": verification.verifier_id,
                        "source_text_sha256": candidate.source_text_sha256,
                    },
                ),
            }
        )

        freeze = F0FreezeRecord(
            freeze_id=f"F0-{run_id}-{evidence.evidence_id}",
            evidence_id=evidence.evidence_id,
            source_id=evidence.source_id,
            candidate_ref=candidate.candidate_id,
            verification_ref=verification.verification_id,
            source_text_sha256=candidate.source_text_sha256,
            frozen_at=datetime.now(timezone.utc),
            provenance=Provenance(
                source=candidate.evidence.provenance.source,
                provider=self.__class__.__name__,
                retrieved_at=datetime.now(timezone.utc),
                lineage_refs=(
                    candidate.candidate_id,
                    verification.verification_id,
                ),
                metadata={"run_id": run_id},
            ),
        )

        return evidence, freeze
