from datetime import datetime, timezone

import pytest

from nutrifoundation.domain.enums import HumanDecision, IntegrityStatus, ReliabilityState
from nutrifoundation.domain.models import (
    ClaimReliabilitySignal,
    HumanAdjudicationRecord,
    Provenance,
    ReliabilityVector,
)
from nutrifoundation.workflow.state_machine import (
    InvalidTransition,
    TransitionContext,
    WorkflowState,
    assert_transition,
)

PROV = Provenance(source="fixture")
RELIABILITY = ClaimReliabilitySignal(
    reliability_id="CRS-C01",
    claim_id="SC-C01",
    evidence_refs=("EU-1", "EU-2"),
    citation_reception_refs=("CRR-1",),
    scientific_influence_refs=("SIS-1",),
    reliability_vector=ReliabilityVector(
        intrinsic_evidence_validity="high",
        evidence_independence="high",
        direct_replication="convergent",
        citation_reception="supportive",
        integrity_status=IntegrityStatus.CLEAN,
        temporal_maturity="mature",
        applicability_stability="moderate",
    ),
    reliability_state=ReliabilityState.ROBUST,
    eligible_for_expert_gold_review=True,
    provenance=PROV,
)


def test_cannot_skip_from_claim_candidate_to_gold():
    with pytest.raises(InvalidTransition):
        assert_transition(WorkflowState.CLAIM_CANDIDATE, WorkflowState.GOLD)


def test_gold_requires_human_adjudication():
    with pytest.raises(InvalidTransition):
        assert_transition(
            WorkflowState.HUMAN_ADJUDICATION_PENDING,
            WorkflowState.GOLD,
            TransitionContext(reliability=RELIABILITY, has_f1_anchor=True),
        )


def test_gold_requires_f1_anchor():
    adj = HumanAdjudicationRecord(
        adjudication_id="A1",
        claim_id="SC-C01",
        reviewer_id="expert-1",
        reviewer_role="nutrition scientist",
        independent_from_agent_extraction=True,
        decision=HumanDecision.APPROVE_GOLD_AS_WRITTEN,
        approved_wording="bounded claim",
        adjudicated_at=datetime.now(timezone.utc),
        provenance=PROV,
    )
    with pytest.raises(InvalidTransition):
        assert_transition(
            WorkflowState.HUMAN_ADJUDICATION_PENDING,
            WorkflowState.GOLD,
            TransitionContext(
                reliability=RELIABILITY,
                adjudication=adj,
                has_f1_anchor=False,
            ),
        )


def test_valid_gold_transition():
    adj = HumanAdjudicationRecord(
        adjudication_id="A1",
        claim_id="SC-C01",
        reviewer_id="expert-1",
        reviewer_role="nutrition scientist",
        independent_from_agent_extraction=True,
        decision=HumanDecision.APPROVE_GOLD_AS_WRITTEN,
        approved_wording="bounded claim",
        adjudicated_at=datetime.now(timezone.utc),
        provenance=PROV,
    )
    assert_transition(
        WorkflowState.HUMAN_ADJUDICATION_PENDING,
        WorkflowState.GOLD,
        TransitionContext(
            reliability=RELIABILITY,
            adjudication=adj,
            has_f1_anchor=True,
        ),
    )
