from datetime import datetime, timezone

import pytest

from nutrifoundation.domain.evidence_pipeline import (
    EvidenceExtractionCandidate,
    EvidenceVerificationRecord,
    F0FreezeRecord,
    VerificationChecks,
)
from nutrifoundation.domain.enums import SourceType
from nutrifoundation.domain.models import EvidenceUnit, Provenance, SourceArtifact
from nutrifoundation.domain.run_manifest import RunManifest
from nutrifoundation.persistence.sqlite import SQLiteStore


def test_f0_evidence_is_immutable(tmp_path):
    store = SQLiteStore(tmp_path / "x.db")
    store.initialize()

    source = SourceArtifact(
        source_id="SA-1",
        source_type=SourceType.RCT,
        title="Trial",
        provenance=Provenance(source="fixture"),
    )
    store.upsert_source(source)

    manifest = RunManifest(
        run_id="RUN-1",
        pipeline_name="evidence",
        pipeline_version="E0.3",
        mode="test",
        started_at=datetime.now(timezone.utc),
    )
    store.save_run_manifest(manifest)

    evidence = EvidenceUnit(
        evidence_id="EU-1",
        source_id="SA-1",
        population="100 adults",
        intervention="Diet",
        outcome="Outcome",
        effect="HR 0.80",
        applicability_boundary="Trial population",
        anchor="Abstract",
        verification_status="frozen_F0",
        status="frozen_F0",
        provenance=Provenance(source="fixture"),
    )
    freeze = F0FreezeRecord(
        freeze_id="F0-1",
        evidence_id="EU-1",
        source_id="SA-1",
        candidate_ref="CAND-1",
        verification_ref="VERIFY-1",
        source_text_sha256="abc",
        frozen_at=datetime.now(timezone.utc),
        provenance=Provenance(source="fixture"),
    )
    store.freeze_f0(evidence, freeze, "RUN-1")

    changed = evidence.model_copy(update={"effect": "HR 0.50"})
    with pytest.raises(ValueError):
        store.freeze_f0(changed, freeze, "RUN-1")
