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

E031_INVARIANTS = (
    ContractInvariant("provider_logic_adapter_only", "ProviderLogic -> AdapterOnly"),
    ContractInvariant("core_pipeline_provider_agnostic", "CorePipeline != ProviderSpecific"),
    ContractInvariant("task_hash_binding", "ResponseTaskHash == TaskBundleHash"),
    ContractInvariant("source_text_hash_binding", "ResponseSourceTextHash == TaskSourceTextHash"),
    ContractInvariant("contract_version_binding", "ResponseContractVersion == TaskContractVersion"),
    ContractInvariant("response_not_f0", "ResponseEnvelope != EvidenceUnit_F0"),
    ContractInvariant("unknown_response_fields_rejected", "UnknownProviderField -> Reject"),
    ContractInvariant("defer_without_guessing", "SemanticUncertainty -> DeferAllowed"),
)

E04_INVARIANTS = (
    ContractInvariant("blind_task_has_no_gold_input", "BlindTaskFactory !<- HiddenGold"),
    ContractInvariant("gold_loaded_post_response", "HiddenGold -> ScoringOnly"),
    ContractInvariant("engineering_blind_not_cognitive_blind", "EngineeringBlind != CognitiveBlind"),
    ContractInvariant("verifier_yield_not_accuracy", "VerifierYield != SemanticAccuracy"),
    ContractInvariant("defer_requires_escalation", "BlindDefer -> HumanEscalation"),
    ContractInvariant("blind_context_recorded", "BlindnessClass -> Required"),
    ContractInvariant("benchmark_not_operational_escalation", "BenchmarkAdjudication != OperationalEscalation"),
)

EXECUTABLE_INVARIANTS = (
    E01_INVARIANTS
    + E03_INVARIANTS
    + E031_INVARIANTS
    + E04_INVARIANTS
)
