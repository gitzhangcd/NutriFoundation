from datetime import date, datetime, timezone

from nutrifoundation.agents.evidence_extraction import EvidenceExtractionAgent, ExtractionOutput
from nutrifoundation.agents.evidence_verification import IndependentEvidenceVerifier
from nutrifoundation.domain.enums import SourceType
from nutrifoundation.domain.models import EvidenceUnit, Provenance, SourceArtifact


class StaticProvider:
    def __init__(self, evidence):
        self.evidence = evidence

    def extract(self, source, source_text, evidence_id, *, run_id):
        return ExtractionOutput(
            evidence=self.evidence,
            confidence=0.99,
            method="static_test",
        )


def source(source_type=SourceType.RCT):
    return SourceArtifact(
        source_id="SA-1",
        source_type=source_type,
        title="Test",
        publication_date=date(2024, 1, 1),
        provenance=Provenance(source="fixture"),
    )


def evidence(**updates):
    data = dict(
        evidence_id="EU-1",
        source_id="SA-1",
        kind="intervention_effect",
        population="100 adults",
        intervention="Diet A",
        comparator="Diet B",
        outcome="Weight",
        effect="-5.0 kg vs -2.0 kg",
        applicability_boundary="Adults represented in the trial",
        anchor="Abstract",
        verification_status="candidate",
        status="candidate",
        provenance=Provenance(source="fixture"),
    )
    data.update(updates)
    return EvidenceUnit(**data)


def candidate(ev, text, extractor_id="extractor"):
    return EvidenceExtractionAgent(
        StaticProvider(ev),
        extractor_id=extractor_id,
    ).extract(
        source(SourceType.COHORT if ev.kind == "causal" else SourceType.RCT),
        text,
        ev.evidence_id,
        run_id="RUN-1",
    )


def test_numeric_support_passes_when_effect_numbers_exist():
    text = "100 adults were assigned. Weight change was -5.0 kg versus -2.0 kg."
    cand = candidate(evidence(), text)
    record = IndependentEvidenceVerifier(verifier_id="verifier").verify(
        cand, source(), text, run_id="RUN-1"
    )
    assert record.status == "verified"
    assert record.checks.numeric_support is True


def test_fabricated_numeric_effect_is_rejected():
    text = "Weight change was -5.0 kg versus -2.0 kg."
    cand = candidate(evidence(effect="-9.9 kg vs -2.0 kg"), text)
    record = IndependentEvidenceVerifier(verifier_id="verifier").verify(
        cand, source(), text, run_id="RUN-1"
    )
    assert record.status == "rejected"
    assert record.checks.numeric_support is False


def test_observational_source_cannot_be_encoded_as_causal():
    ev = evidence(kind="causal")
    text = "100 adults were observed. Weight change was -5.0 kg versus -2.0 kg."
    cand = EvidenceExtractionAgent(
        StaticProvider(ev),
        extractor_id="extractor",
    ).extract(
        source(SourceType.COHORT),
        text,
        ev.evidence_id,
        run_id="RUN-1",
    )
    record = IndependentEvidenceVerifier(verifier_id="verifier").verify(
        cand,
        source(SourceType.COHORT),
        text,
        run_id="RUN-1",
    )
    assert record.status == "rejected"
    assert record.checks.observational_causality_guard is False


def test_same_extractor_and_verifier_identity_cannot_verify():
    text = "Weight change was -5.0 kg versus -2.0 kg."
    cand = candidate(evidence(), text, extractor_id="same")
    record = IndependentEvidenceVerifier(verifier_id="same").verify(
        cand, source(), text, run_id="RUN-1"
    )
    assert record.status == "rejected"
    assert record.independent_from_extractor is False
