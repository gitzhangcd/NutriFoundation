from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from nutrifoundation.domain.enums import HumanDecision
from nutrifoundation.domain.models import ClaimReliabilitySignal, HumanAdjudicationRecord


class WorkflowState(StrEnum):
    RETRIEVED = "RETRIEVED"
    METADATA_VERIFIED = "METADATA_VERIFIED"
    SOURCE_REGISTERED = "SOURCE_REGISTERED"
    EXTRACTED_CANDIDATE = "EXTRACTED_CANDIDATE"
    VERIFIED_CANDIDATE = "VERIFIED_CANDIDATE"
    F0_FROZEN = "F0_FROZEN"
    F1_FULLTEXT_VERIFIED = "F1_FULLTEXT_VERIFIED"
    CLAIM_CANDIDATE = "CLAIM_CANDIDATE"
    RECEPTION_QUALIFIED = "RECEPTION_QUALIFIED"
    RELIABILITY_QUALIFIED = "RELIABILITY_QUALIFIED"
    HUMAN_ADJUDICATION_PENDING = "HUMAN_ADJUDICATION_PENDING"
    GOLD = "GOLD"


TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.RETRIEVED: {WorkflowState.METADATA_VERIFIED},
    WorkflowState.METADATA_VERIFIED: {WorkflowState.SOURCE_REGISTERED},
    WorkflowState.SOURCE_REGISTERED: {WorkflowState.EXTRACTED_CANDIDATE},
    WorkflowState.EXTRACTED_CANDIDATE: {WorkflowState.VERIFIED_CANDIDATE},
    WorkflowState.VERIFIED_CANDIDATE: {WorkflowState.F0_FROZEN},
    WorkflowState.F0_FROZEN: {
        WorkflowState.F1_FULLTEXT_VERIFIED,
        WorkflowState.CLAIM_CANDIDATE,
    },
    WorkflowState.F1_FULLTEXT_VERIFIED: {WorkflowState.CLAIM_CANDIDATE},
    WorkflowState.CLAIM_CANDIDATE: {WorkflowState.RECEPTION_QUALIFIED},
    WorkflowState.RECEPTION_QUALIFIED: {WorkflowState.RELIABILITY_QUALIFIED},
    WorkflowState.RELIABILITY_QUALIFIED: {WorkflowState.HUMAN_ADJUDICATION_PENDING},
    WorkflowState.HUMAN_ADJUDICATION_PENDING: {WorkflowState.GOLD},
    WorkflowState.GOLD: set(),
}


class InvalidTransition(ValueError):
    pass


@dataclass(frozen=True)
class TransitionContext:
    reliability: ClaimReliabilitySignal | None = None
    adjudication: HumanAdjudicationRecord | None = None
    has_f1_anchor: bool = False


def can_transition(current: WorkflowState, target: WorkflowState) -> bool:
    return target in TRANSITIONS[current]


def assert_transition(
    current: WorkflowState,
    target: WorkflowState,
    ctx: TransitionContext | None = None,
) -> None:
    if not can_transition(current, target):
        raise InvalidTransition(f"Illegal transition: {current} -> {target}")

    ctx = ctx or TransitionContext()

    if target == WorkflowState.RELIABILITY_QUALIFIED:
        if ctx.reliability is None:
            raise InvalidTransition("RELIABILITY_QUALIFIED requires ClaimReliabilitySignal")

    if target == WorkflowState.HUMAN_ADJUDICATION_PENDING:
        if ctx.reliability is None or not ctx.reliability.eligible_for_expert_gold_review:
            raise InvalidTransition(
                "Human adjudication gate requires an eligible reliability sidecar"
            )

    if target == WorkflowState.GOLD:
        if ctx.adjudication is None:
            raise InvalidTransition("GOLD requires HumanAdjudicationRecord")
        if ctx.adjudication.decision not in {
            HumanDecision.APPROVE_GOLD_AS_WRITTEN,
            HumanDecision.APPROVE_GOLD_WITH_REVISION,
        }:
            raise InvalidTransition("GOLD requires explicit human approval")
        if not ctx.adjudication.independent_from_agent_extraction:
            raise InvalidTransition(
                "Agent-only or non-independent approval cannot create GOLD"
            )
        if not ctx.has_f1_anchor:
            raise InvalidTransition(
                "GOLD requires at least one F1/full-text qualification anchor"
            )
