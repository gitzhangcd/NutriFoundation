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

E03_INVARIANTS = (
    ContractInvariant("extractor_verifier_independence", "Extractor != IndependentVerifier"),
    ContractInvariant("numeric_support_required_for_f0", "UnsupportedNumericEffect != F0"),
    ContractInvariant("observational_not_causal", "ObservationalAssociation != CausalEffect"),
    ContractInvariant("guideline_not_independent_effect", "GuidelineStatement != IndependentEffectEstimate"),
    ContractInvariant("f0_is_not_f1", "F0 != F1"),
    ContractInvariant("f0_is_not_gold", "F0 != ScientificClaim_GOLD"),
    ContractInvariant("f0_payload_immutable", "FrozenF0Payload == Immutable"),
)

EXECUTABLE_INVARIANTS = E01_INVARIANTS + E03_INVARIANTS
