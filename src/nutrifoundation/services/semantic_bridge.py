from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from uuid import uuid4

from nutrifoundation.adapters.portability import assert_response_binding
from nutrifoundation.agents.evidence_verification import IndependentEvidenceVerifier
from nutrifoundation.domain.evidence_pipeline import EvidenceExtractionCandidate
from nutrifoundation.domain.models import EvidenceUnit, Provenance
from nutrifoundation.domain.run_manifest import RunManifest
from nutrifoundation.domain.semantic_worker import (
    ResponseEnvelope,
    SemanticTaskState,
    TaskBundle,
)
from nutrifoundation.persistence.sqlite import SQLiteStore
from nutrifoundation.services.evidence_freeze import F0FreezeEngine


REQUESTED_EVIDENCE_FIELDS = (
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
    "source_span",
)

ALLOWED_RESPONSE_FIELDS = set(REQUESTED_EVIDENCE_FIELDS)

SEMANTIC_RULES = (
    "Association must not be upgraded to causation.",
    "Guideline or consensus statements must remain source-stated recommendations.",
    "Every numeric effect must be copied faithfully from source text.",
    "Applicability boundary and source anchor are required.",
    "Do not use external knowledge unless the task explicitly contains it.",
    "Do not invent missing fields; use null or defer when source support is insufficient.",
)


@dataclass(frozen=True)
class SemanticIngestionResult:
    task_id: str
    task_state: str
    response_id: str
    candidate_id: str | None = None
    verification_id: str | None = None
    evidence_id: str | None = None
    f0_frozen: bool = False
    errors: tuple[str, ...] = ()
    verification_scope: str = "legacy_mechanical_checks_only"

    def as_dict(self):
        return asdict(self)


class SemanticTaskOrchestrator:
    def __init__(
        self,
        store: SQLiteStore,
        *,
        code_version: str = "0.3.1",
    ):
        self.store = store
        self.code_version = code_version

    def prepare_evidence_task(
        self,
        source_id: str,
        evidence_id: str,
    ) -> TaskBundle:
        self.store.initialize()

        source = self.store.get_source(source_id)
        if source is None:
            raise ValueError(f"Unknown SourceArtifact: {source_id}")

        text_record = self.store.get_source_text(source_id)
        if text_record is None:
            raise ValueError(f"No persisted source text for: {source_id}")

        source_text, text_kind, source_text_sha256 = text_record
        now = datetime.now(timezone.utc)
        run_id = (
            f"RUN-SEM-{now.strftime('%Y%m%dT%H%M%SZ')}-"
            f"{uuid4().hex[:8]}"
        )
        task_id = (
            f"TASK-EVID-{source_id}-{evidence_id}-"
            f"{uuid4().hex[:8]}"
        )

        manifest = RunManifest(
            run_id=run_id,
            pipeline_name="semantic_task_orchestration",
            pipeline_version="E0.3.1",
            mode="live",
            started_at=now,
            inputs={
                "source_id": source_id,
                "evidence_id": evidence_id,
                "text_kind": text_kind,
            },
            providers=("ChatWindowOrPortableSemanticWorker",),
            code_version=self.code_version,
        )
        self.store.save_run_manifest(manifest)

        provenance = Provenance(
            source=source.provenance.source,
            provider=self.__class__.__name__,
            retrieved_at=now,
            lineage_refs=(source_id,),
            metadata={
                "run_id": run_id,
                "text_kind": text_kind,
                "source_text_sha256": source_text_sha256,
            },
        )

        task = TaskBundle.build(
            task_id=task_id,
            task_type="extract_evidence_unit",
            contract_version="E0.3.1-v0.1",
            run_id=run_id,
            source_id=source_id,
            evidence_id=evidence_id,
            source_snapshot=source.model_dump(mode="json"),
            source_text=source_text,
            source_text_sha256=source_text_sha256,
            requested_fields=REQUESTED_EVIDENCE_FIELDS,
            rules=SEMANTIC_RULES,
            response_schema_version="ResponseEnvelope-v0.1",
            created_at=now,
            provenance=provenance,
        )
        self.store.save_semantic_task(task, SemanticTaskState.PENDING)

        completed = manifest.model_copy(
            update={
                "finished_at": datetime.now(timezone.utc),
                "status": "completed",
                "outputs": {
                    "task_id": task.task_id,
                    "task_sha256": task.task_sha256,
                },
            }
        )
        self.store.save_run_manifest(completed)
        self.store.log_semantic_event(
            task.task_id,
            "prepare_task",
            "completed",
            task.task_sha256,
        )
        return task

    def mark_exported(self, task_id: str, location: str) -> None:
        self.store.transition_semantic_task(
            task_id,
            SemanticTaskState.EXPORTED,
        )
        self.store.log_semantic_event(
            task_id,
            "export_task",
            "completed",
            location,
        )


class SemanticResponseIngestionService:
    def __init__(
        self,
        store: SQLiteStore,
        *,
        verifier: IndependentEvidenceVerifier | None = None,
        legacy_f0: bool = False,
    ):
        self.store = store
        self.verifier = verifier or IndependentEvidenceVerifier(
            verifier_id="IndependentEvidenceVerifier-v0.1"
        )
        self.freeze_engine = F0FreezeEngine()
        self.legacy_f0 = legacy_f0

    def _candidate_from_response(
        self,
        task: TaskBundle,
        response: ResponseEnvelope,
    ) -> EvidenceExtractionCandidate:
        unknown = sorted(set(response.output) - ALLOWED_RESPONSE_FIELDS)
        if unknown:
            raise ValueError(
                "Response output contains non-contract fields: "
                + ", ".join(unknown)
            )

        payload = {
            key: response.output.get(key)
            for key in REQUESTED_EVIDENCE_FIELDS
            if key in response.output
        }
        payload.update(
            {
                "evidence_id": task.evidence_id,
                "source_id": task.source_id,
                "verification_status": "candidate",
                "status": "candidate",
                "provenance": {
                    "source": task.provenance.source,
                    "provider": response.worker.adapter_type,
                    "retrieved_at": response.created_at.isoformat(),
                    "lineage_refs": [task.task_id, response.response_id],
                    "metadata": {
                        "run_id": task.run_id,
                        "worker": response.worker.model_dump(mode="json"),
                        "task_sha256": task.task_sha256,
                        "source_text_sha256": task.source_text_sha256,
                    },
                },
            }
        )

        evidence = EvidenceUnit.model_validate(payload)
        confidence = response.confidence if response.confidence is not None else 0.0

        return EvidenceExtractionCandidate(
            candidate_id=f"CAND-{task.task_id}",
            evidence=evidence,
            extractor_id=response.worker.worker_id,
            extraction_method=(
                f"semantic_response_envelope/{response.worker.adapter_type}"
            ),
            extraction_confidence=confidence,
            source_text_sha256=task.source_text_sha256,
            created_at=response.created_at,
            provenance=Provenance(
                source=task.provenance.source,
                provider=self.__class__.__name__,
                retrieved_at=datetime.now(timezone.utc),
                lineage_refs=(task.task_id, response.response_id),
                metadata={
                    "run_id": task.run_id,
                    "worker_id": response.worker.worker_id,
                    "adapter_type": response.worker.adapter_type,
                },
            ),
        )

    def ingest(
        self,
        response: ResponseEnvelope,
    ) -> SemanticIngestionResult:
        self.store.initialize()
        task_record = self.store.get_semantic_task(response.task_id)
        if task_record is None:
            raise ValueError(f"Unknown semantic task: {response.task_id}")

        task, state = task_record
        if state not in {
            SemanticTaskState.PENDING,
            SemanticTaskState.EXPORTED,
        }:
            raise ValueError(
                f"Semantic task is not accepting responses: {state.value}"
            )

        assert_response_binding(task, response)
        self.store.save_semantic_response(response)
        self.store.transition_semantic_task(
            task.task_id,
            SemanticTaskState.RESPONDED,
        )
        self.store.log_semantic_event(
            task.task_id,
            "ingest_response_envelope",
            response.status,
            response.response_id,
        )

        if response.status == "defer":
            self.store.transition_semantic_task(
                task.task_id,
                SemanticTaskState.DEFERRED,
            )
            return SemanticIngestionResult(
                task_id=task.task_id,
                task_state=SemanticTaskState.DEFERRED.value,
                response_id=response.response_id,
                evidence_id=task.evidence_id,
                errors=response.uncertainties,
            )

        if response.status == "failed":
            self.store.transition_semantic_task(
                task.task_id,
                SemanticTaskState.REJECTED,
            )
            return SemanticIngestionResult(
                task_id=task.task_id,
                task_state=SemanticTaskState.REJECTED.value,
                response_id=response.response_id,
                evidence_id=task.evidence_id,
                errors=((response.error or "semantic worker failed"),),
            )

        source = self.store.get_source(task.source_id)
        if source is None:
            raise ValueError(f"SourceArtifact disappeared: {task.source_id}")

        try:
            candidate = self._candidate_from_response(task, response)
        except Exception as error:
            self.store.transition_semantic_task(
                task.task_id,
                SemanticTaskState.REJECTED,
            )
            self.store.log_semantic_event(
                task.task_id,
                "response_to_candidate",
                "rejected",
                str(error),
            )
            return SemanticIngestionResult(
                task_id=task.task_id,
                task_state=SemanticTaskState.REJECTED.value,
                response_id=response.response_id,
                evidence_id=task.evidence_id,
                errors=(str(error),),
            )

        self.store.save_evidence_candidate(candidate, task.run_id)

        verification = self.verifier.verify(
            candidate,
            source,
            task.source_text,
            run_id=task.run_id,
        )
        self.store.save_evidence_verification(
            verification,
            task.run_id,
        )

        if verification.status != "verified":
            self.store.transition_semantic_task(
                task.task_id,
                SemanticTaskState.REJECTED,
            )
            self.store.log_semantic_event(
                task.task_id,
                "independent_verification",
                "rejected",
                "; ".join(verification.errors),
            )
            return SemanticIngestionResult(
                task_id=task.task_id,
                task_state=SemanticTaskState.REJECTED.value,
                response_id=response.response_id,
                candidate_id=candidate.candidate_id,
                verification_id=verification.verification_id,
                evidence_id=task.evidence_id,
                errors=verification.errors,
            )

        self.store.transition_semantic_task(
            task.task_id,
            SemanticTaskState.INGESTED,
        )

        if not self.legacy_f0:
            return SemanticIngestionResult(
                task_id=task.task_id,
                task_state=SemanticTaskState.INGESTED.value,
                response_id=response.response_id,
                candidate_id=candidate.candidate_id,
                verification_id=verification.verification_id,
                evidence_id=task.evidence_id,
            )

        evidence, freeze = self.freeze_engine.freeze(
            candidate,
            verification,
            run_id=task.run_id,
        )
        self.store.freeze_f0(evidence, freeze, task.run_id)
        self.store.transition_semantic_task(
            task.task_id,
            SemanticTaskState.F0_FROZEN,
        )
        self.store.log_semantic_event(
            task.task_id,
            "freeze_F0",
            "completed",
            freeze.freeze_id,
        )

        return SemanticIngestionResult(
            task_id=task.task_id,
            task_state=SemanticTaskState.F0_FROZEN.value,
            response_id=response.response_id,
            candidate_id=candidate.candidate_id,
            verification_id=verification.verification_id,
            evidence_id=evidence.evidence_id,
            f0_frozen=True,
        )
