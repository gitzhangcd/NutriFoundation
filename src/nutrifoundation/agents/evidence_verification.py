from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from nutrifoundation.domain.enums import SourceType
from nutrifoundation.domain.evidence_pipeline import (
    EvidenceExtractionCandidate,
    EvidenceVerificationRecord,
    VerificationChecks,
)
from nutrifoundation.domain.models import Provenance, SourceArtifact


_NUMERIC = re.compile(r"(?<![\d.])[-+−]?\d+(?:[\.,·]\d+)?%?")


def _normalize_numeric(token: str) -> str:
    return (
        token.replace("−", "-")
        .replace("·", ".")
        .replace(",", "")
        .replace("%", "")
        .strip()
    )


def _candidate_numeric_tokens(candidate: EvidenceExtractionCandidate) -> set[str]:
    evidence = candidate.evidence
    text = " ".join(
        value
        for value in (
            evidence.effect,
            evidence.effect_value,
            evidence.recommendation,
        )
        if value
    )
    return {_normalize_numeric(x) for x in _NUMERIC.findall(text)}


def _source_numeric_tokens(source_text: str) -> set[str]:
    tokens: set[str] = set()
    decrease = re.compile(r"reduc|decreas|lower|fell|declin", re.I)
    for match in _NUMERIC.finditer(source_text):
        token = _normalize_numeric(match.group(0))
        tokens.add(token)
        if not token.startswith("-"):
            context = source_text[max(0, match.start() - 48):match.start()]
            if decrease.search(context):
                tokens.add("-" + token)
    return tokens


class IndependentEvidenceVerifier:
    def __init__(self, *, verifier_id: str = "IndependentEvidenceVerifier-v0.1"):
        self.verifier_id = verifier_id

    def verify(
        self,
        candidate: EvidenceExtractionCandidate,
        source: SourceArtifact,
        source_text: str,
        *,
        run_id: str,
    ) -> EvidenceVerificationRecord:
        evidence = candidate.evidence
        source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()

        errors: list[str] = []
        warnings: list[str] = []

        source_linkage = (
            evidence.source_id == source.source_id
            and candidate.source_text_sha256 == source_hash
        )
        if not source_linkage:
            errors.append("source linkage or source-text hash mismatch")

        if evidence.recommendation is not None:
            required_fields = bool(
                evidence.population
                and evidence.recommendation
            )
        else:
            required_fields = bool(
                evidence.population
                and evidence.outcome
                and (evidence.effect or evidence.effect_value)
            )
        if not required_fields:
            errors.append("required scientific fields missing")

        source_anchor_present = bool(evidence.source_span or evidence.anchor)
        if not source_anchor_present:
            errors.append("source anchor missing")

        candidate_numbers = _candidate_numeric_tokens(candidate)
        source_numbers = _source_numeric_tokens(source_text)
        missing_numbers = sorted(candidate_numbers - source_numbers)
        numeric_support = not missing_numbers
        if missing_numbers:
            errors.append(
                "numeric tokens not found in source text: "
                + ", ".join(missing_numbers)
            )

        applicability_boundary_present = bool(evidence.applicability_boundary)
        if not applicability_boundary_present:
            errors.append("applicability boundary missing")

        kind = (evidence.kind or "").lower()
        observational_source = (
            source.source_type == SourceType.COHORT
            or kind.startswith("observational_")
        )
        observational_causality_guard = True
        if observational_source and not (
            "observational" in kind or "association" in kind
        ):
            observational_causality_guard = False
            errors.append(
                "observational source is not explicitly encoded as association-level evidence"
            )

        guideline_source = source.source_type in {
            SourceType.GUIDELINE,
            SourceType.CONSENSUS,
        }
        guideline_authority_guard = True
        if guideline_source:
            guideline_authority_guard = bool(
                evidence.recommendation
                and (
                    "guideline" in kind
                    or "consensus" in kind
                    or kind == ""
                )
            )
            if not guideline_authority_guard:
                errors.append(
                    "guideline/consensus source must remain a source-stated recommendation"
                )

        independent = self.verifier_id != candidate.extractor_id
        if not independent:
            errors.append("verifier must be independent from extractor")

        checks = VerificationChecks(
            source_linkage=source_linkage,
            required_fields=required_fields,
            source_anchor_present=source_anchor_present,
            numeric_support=numeric_support,
            applicability_boundary_present=applicability_boundary_present,
            observational_causality_guard=observational_causality_guard,
            guideline_authority_guard=guideline_authority_guard,
        )

        status = "verified" if not errors else "rejected"

        return EvidenceVerificationRecord(
            verification_id=f"VERIFY-{run_id}-{evidence.evidence_id}",
            candidate_id=candidate.candidate_id,
            evidence_id=evidence.evidence_id,
            source_id=evidence.source_id,
            verifier_id=self.verifier_id,
            extractor_id=candidate.extractor_id,
            independent_from_extractor=independent,
            source_text_sha256=source_hash,
            checks=checks,
            status=status,
            errors=tuple(errors),
            warnings=tuple(warnings),
            verified_at=datetime.now(timezone.utc),
            provenance=Provenance(
                source=source.provenance.source,
                provider=self.__class__.__name__,
                retrieved_at=datetime.now(timezone.utc),
                lineage_refs=(candidate.candidate_id, source.source_id),
                metadata={"run_id": run_id},
            ),
        )
