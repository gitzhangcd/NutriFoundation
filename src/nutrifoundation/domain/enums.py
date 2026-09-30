from enum import StrEnum


class SourceType(StrEnum):
    RCT = "RCT"
    COHORT = "Cohort"
    META_ANALYSIS = "MetaAnalysis"
    SYSTEMATIC_REVIEW = "SystematicReview"
    GUIDELINE = "Guideline"
    CONSENSUS = "Consensus"
    POSITION_STATEMENT = "PositionStatement"
    DATABASE = "Database"
    CORRECTION = "Correction"
    RETRACTION = "Retraction"


class ClaimType(StrEnum):
    DESCRIPTIVE = "descriptive"
    ASSOCIATIVE = "associative"
    CAUSAL = "causal"
    MECHANISTIC = "mechanistic"
    RECOMMENDATION_SUPPORT = "recommendation_support"


class ReliabilityState(StrEnum):
    INSUFFICIENT = "insufficient"
    PROVISIONAL = "provisional"
    CONVERGENT = "convergent"
    ROBUST = "robust"
    CONTESTED = "contested"
    DEGRADED = "degraded"
    INVALIDATED = "invalidated"


class IntegrityStatus(StrEnum):
    CLEAN = "clean"
    CORRECTED_NONFATAL = "corrected_nonfatal"
    CONCERN = "concern"
    RETRACTED = "retracted"
    UNRESOLVED = "unresolved"


class HumanDecision(StrEnum):
    APPROVE_GOLD_AS_WRITTEN = "APPROVE_GOLD_AS_WRITTEN"
    APPROVE_GOLD_WITH_REVISION = "APPROVE_GOLD_WITH_REVISION"
    REJECT = "REJECT"
    DEFER = "DEFER"
