from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from nutrifoundation.agents.evidence_extraction import EvidenceExtractionAgent
from nutrifoundation.agents.evidence_verification import IndependentEvidenceVerifier
from nutrifoundation.domain.run_manifest import RunManifest
from nutrifoundation.persistence.sqlite import SQLiteStore
from nutrifoundation.services.evidence_freeze import F0FreezeEngine


class EvidenceProductionService:
    def __init__(
        self,
        extractor: EvidenceExtractionAgent,
        verifier: IndependentEvidenceVerifier,
        store: SQLiteStore,
        *,
        mode: str = "live",
        code_version: str = "0.3.0",
        preferred_text_kinds: tuple[str, ...] = (
            "pmc_fulltext",
            "pubmed_abstract",
        ),
        legacy_f0: bool = False,
    ):
        self.extractor = extractor
        self.verifier = verifier
        self.store = store
        self.mode = mode
        self.code_version = code_version
        self.preferred_text_kinds = preferred_text_kinds
        self.legacy_f0 = legacy_f0
        self.freeze_engine = F0FreezeEngine()

    def produce(
        self,
        mapping: list[tuple[str, str]],
    ) -> RunManifest:
        run_id = (
            f"RUN-EVID-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-"
            f"{uuid4().hex[:8]}"
        )
        manifest = RunManifest(
            run_id=run_id,
            pipeline_name="evidence_extraction_verification_f0",
            pipeline_version="E0.3",
            mode=self.mode,
            started_at=datetime.now(timezone.utc),
            inputs={
                "mapping": [
                    {"source_id": source_id, "evidence_id": evidence_id}
                    for source_id, evidence_id in mapping
                ]
            },
            providers=(
                self.extractor.provider.__class__.__name__,
                self.verifier.__class__.__name__,
            ),
            code_version=self.code_version,
        )

        self.store.initialize()
        self.store.save_run_manifest(manifest)

        extracted = 0
        verified = 0
        frozen = 0
        rejected = 0
        errors: list[str] = []

        for source_id, evidence_id in mapping:
            source = self.store.get_source(source_id)
            if source is None:
                message = f"missing SourceArtifact {source_id}"
                errors.append(message)
                self.store.log_evidence_event(
                    run_id, evidence_id, source_id, "load_source", "failed", message
                )
                continue

            source_text_record = self.store.get_source_text(
                source_id,
                preferred_kinds=self.preferred_text_kinds,
            )
            if source_text_record is None:
                message = f"missing source text for {source_id}"
                errors.append(message)
                self.store.log_evidence_event(
                    run_id, evidence_id, source_id, "load_source_text", "failed", message
                )
                continue

            source_text, text_kind, _ = source_text_record

            try:
                candidate = self.extractor.extract(
                    source,
                    source_text,
                    evidence_id,
                    run_id=run_id,
                )
                self.store.save_evidence_candidate(candidate, run_id)
                extracted += 1
                self.store.log_evidence_event(
                    run_id,
                    evidence_id,
                    source_id,
                    "extract_candidate",
                    "completed",
                    text_kind,
                )

                verification = self.verifier.verify(
                    candidate,
                    source,
                    source_text,
                    run_id=run_id,
                )
                self.store.save_evidence_verification(verification, run_id)

                if verification.status != "verified":
                    rejected += 1
                    self.store.log_evidence_event(
                        run_id,
                        evidence_id,
                        source_id,
                        "verify_candidate",
                        "rejected",
                        "; ".join(verification.errors),
                    )
                    errors.append(
                        f"{evidence_id} verification rejected: "
                        + "; ".join(verification.errors)
                    )
                    continue

                verified += 1
                self.store.log_evidence_event(
                    run_id,
                    evidence_id,
                    source_id,
                    "verify_candidate",
                    "completed",
                )

                if not self.legacy_f0:
                    continue
                evidence, freeze = self.freeze_engine.freeze(
                    candidate,
                    verification,
                    run_id=run_id,
                )
                self.store.freeze_f0(evidence, freeze, run_id)
                frozen += 1
                self.store.log_evidence_event(
                    run_id,
                    evidence_id,
                    source_id,
                    "freeze_F0",
                    "completed",
                )

            except Exception as error:
                message = f"{evidence_id}: {error}"
                errors.append(message)
                self.store.log_evidence_event(
                    run_id,
                    evidence_id,
                    source_id,
                    "pipeline",
                    "failed",
                    str(error),
                )

        completed = frozen if self.legacy_f0 else verified
        status = "completed" if completed == len(mapping) and not errors else "failed"
        final = manifest.model_copy(
            update={
                "finished_at": datetime.now(timezone.utc),
                "status": status,
                "outputs": {
                    "requested_count": len(mapping),
                    "extracted_count": extracted,
                    "verified_count": verified,
                    "frozen_F0_count": frozen,
                    "rejected_count": rejected,
                    "verification_scope": "legacy_mechanical_checks_only",
                    "legacy_f0_enabled": self.legacy_f0,
                },
                "errors": tuple(errors),
            }
        )
        self.store.save_run_manifest(final)
        return final
