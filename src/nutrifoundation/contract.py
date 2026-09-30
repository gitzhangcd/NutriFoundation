from dataclasses import dataclass


@dataclass(frozen=True)
class ContractInvariant:
    key: str
    statement: str


E01_INVARIANTS = (
    ContractInvariant("observation_is_not_evidence", "Observation != Evidence"),
    ContractInvariant("citation_is_not_evidence", "Citation != EvidenceUnit"),
    ContractInvariant("evidence_is_not_claim", "EvidenceUnit != ScientificClaim"),
    ContractInvariant("influence_is_not_reliability", "ScientificInfluence != ClaimReliability"),
    ContractInvariant("citation_count_is_not_support_count", "CitationCount != SupportCount"),
    ContractInvariant("support_is_not_replication", "SupportiveCitation != IndependentReplication"),
    ContractInvariant("journal_metric_is_not_validity", "JournalMetric != ArticleValidity"),
    ContractInvariant("agent_only_gold_is_invalid", "AgentOnlyApproval != ScientificClaim_GOLD"),
)
