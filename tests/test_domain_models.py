from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from nutrifoundation.domain.enums import HumanDecision, IntegrityStatus, ReliabilityState
from nutrifoundation.domain.models import (
    ClaimReliabilitySignal,
    HumanAdjudicationRecord,
    Provenance,
    ReliabilityVector,
)


PROV = Provenance(source="fixture")


def vector(integrity=IntegrityStatus.CLEAN):
    return ReliabilityVector(
        intrinsic_evidence_validity="high",
        evidence_independence="high",
        direct_replication="convergent",
        citation_reception="supportive",
        integrity_status=integrity,
        temporal_maturity="mature",
        applicability_stability="moderate",
    )


def test_influence_cannot_be_only_basis_for_robust_reliability():
    with pytest.raises(ValidationError):
        ClaimReliabilitySignal(
            reliability_id="R1",
            claim_id="C1",
            evidence_refs=(),
            scientific_influence_refs=("I1",),
            reliability_vector=vector(),
            reliability_state=ReliabilityState.ROBUST,
            eligible_for_expert_gold_review=True,
            provenance=PROV,
        )


def test_retracted_evidence_cannot_remain_robust():
    with pytest.raises(ValidationError):
        ClaimReliabilitySignal(
            reliability_id="R1",
            claim_id="C1",
            evidence_refs=("EU1",),
            reliability_vector=vector(IntegrityStatus.RETRACTED),
            reliability_state=ReliabilityState.ROBUST,
            eligible_for_expert_gold_review=False,
            provenance=PROV,
        )


def test_human_gold_approval_must_be_independent():
    with pytest.raises(ValidationError):
        HumanAdjudicationRecord(
            adjudication_id="A1",
            claim_id="C1",
            reviewer_id="expert-1",
            reviewer_role="dietitian",
            independent_from_agent_extraction=False,
            decision=HumanDecision.APPROVE_GOLD_AS_WRITTEN,
            approved_wording="claim",
            adjudicated_at=datetime.now(timezone.utc),
            provenance=PROV,
        )
