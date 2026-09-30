from datetime import datetime, timezone

import pytest

from nutrifoundation.domain.evidence_pipeline import (
    EvidenceExtractionCandidate,
    EvidenceVerificationRecord,
    VerificationChecks,
)
from nutrifoundation.domain.models import EvidenceUnit, Provenance
from nutrifoundation.services.evidence_freeze import F0FreezeEngine


def candidate():
    evidence = EvidenceUnit(
        evidence_id="EU-1",
        source_id="SA-1",
        population="100 adults",
        intervention="Diet",
        comparator="Control",
        outcome="Outcome",
        effect="HR 0.80",
        applicability_boundary="Trial population",
        anchor="Abstract",
        verification_status="candidate",
        status="candidate",
        provenance=Provenance(source="fixture"),
    )
    return EvidenceExtractionCandidate(
        candidate_id="CAND-1",
        evidence=evidence,
        extractor_id="extractor",
        extraction_method="test",
        extraction_confidence=1.0,
        source_text_sha256="abc",
        created_at=datetime.now(timezone.utc),
        provenance=Provenance(source="fixture"),
    )


def verification(status="verified"):
    checks = VerificationChecks(
        source_linkage=True,
        required_fields=True,
        source_anchor_present=True,
        numeric_support=True,
        applicability_boundary_present=True,
        observational_causality_guard=True,
        guideline_authority_guard=True,
    )
    return EvidenceVerificationRecord(
        verification_id="VERIFY-1",
        candidate_id="CAND-1",
        evidence_id="EU-1",
        source_id="SA-1",
        verifier_id="verifier",
        extractor_id="extractor",
        independent_from_extractor=True,
        source_text_sha256="abc",
        checks=checks,
        status=status,
        errors=() if status == "verified" else ("failure",),
        verified_at=datetime.now(timezone.utc),
        provenance=Provenance(source="fixture"),
    )


def test_verified_candidate_can_freeze_f0():
    evidence, freeze = F0FreezeEngine().freeze(
        candidate(), verification(), run_id="RUN-1"
    )
    assert evidence.status == "frozen_F0"
    assert evidence.verification_status == "frozen_F0"
    assert freeze.freeze_level == "F0"


def test_rejected_candidate_cannot_freeze_f0():
    with pytest.raises(ValueError):
        F0FreezeEngine().freeze(
            candidate(), verification("rejected"), run_id="RUN-1"
        )
