from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from nutrifoundation.domain.blind_replay import (
    BlindReplaySummary,
    CaseScore,
    FieldMatch,
    FieldScore,
    SemanticErrorType,
)
from nutrifoundation.io.loaders import load_structured


WORD_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?%?", re.I)
NUM_RE = re.compile(r"[-+−]?\d+(?:[\.,·]\d+)?%?")

CRITICAL_FIELDS = (
    "population",
    "intervention",
    "exposure",
    "intervention_or_exposure",
    "comparator",
    "outcome",
    "effect",
    "recommendation",
    "applicability_boundary",
    "anchor",
)

ERROR_BY_FIELD = {
    "kind": SemanticErrorType.EVIDENCE_KIND_MISMATCH,
    "population": SemanticErrorType.POPULATION_SCOPE_MISMATCH,
    "intervention": SemanticErrorType.INTERVENTION_EXPOSURE_MISMATCH,
    "exposure": SemanticErrorType.INTERVENTION_EXPOSURE_MISMATCH,
    "intervention_or_exposure": SemanticErrorType.INTERVENTION_EXPOSURE_MISMATCH,
    "comparator": SemanticErrorType.COMPARATOR_MISMATCH,
    "outcome": SemanticErrorType.OUTCOME_MISMATCH,
    "effect": SemanticErrorType.EFFECT_SEMANTIC_MISMATCH,
    "recommendation": SemanticErrorType.RECOMMENDATION_MISMATCH,
    "applicability_boundary": SemanticErrorType.APPLICABILITY_BOUNDARY_MISMATCH,
    "anchor": SemanticErrorType.SOURCE_ANCHOR_MISMATCH,
}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = text.replace("−", "-").replace("·", ".")
    return " ".join(WORD_RE.findall(text))


def token_set(value: Any) -> set[str]:
    return set(normalize_text(value).split())


def lexical_similarity(a: Any, b: Any) -> float:
    ta, tb = token_set(a), token_set(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def numeric_tokens(value: Any) -> set[str]:
    if value is None:
        return set()
    return {
        x.replace("−", "-").replace("·", ".").replace(",", "")
        for x in NUM_RE.findall(str(value))
    }


def classify_match(gold: Any, observed: Any) -> tuple[FieldMatch, float | None]:
    if gold is None:
        return FieldMatch.NOT_APPLICABLE, None
    if observed is None or normalize_text(observed) == "":
        return FieldMatch.MISSING, 0.0
    ng, no = normalize_text(gold), normalize_text(observed)
    if ng == no:
        return FieldMatch.EXACT, 1.0
    sim = lexical_similarity(gold, observed)
    if sim >= 0.70:
        return FieldMatch.NEAR, sim
    if sim >= 0.35:
        return FieldMatch.PARTIAL, sim
    return FieldMatch.MISMATCH, sim


def score_field(field: str, gold: Any, observed: Any) -> FieldScore:
    match, sim = classify_match(gold, observed)
    errors: list[str] = []

    if gold is not None and match == FieldMatch.MISSING:
        errors.append(SemanticErrorType.MISSING_CRITICAL_FIELD.value)

    if field in {"effect", "recommendation"} and gold is not None and observed is not None:
        gold_nums = numeric_tokens(gold)
        obs_nums = numeric_tokens(observed)
        if gold_nums and gold_nums != obs_nums:
            errors.append(SemanticErrorType.NUMERIC_EFFECT_MISMATCH.value)

    if match in {FieldMatch.MISMATCH, FieldMatch.MISSING} and field in ERROR_BY_FIELD:
        errors.append(ERROR_BY_FIELD[field].value)

    return FieldScore(
        field=field,
        match=match.value,
        lexical_similarity=sim,
        gold_value=gold,
        observed_value=observed,
        errors=tuple(dict.fromkeys(errors)),
    )


def _causality_error(gold: dict[str, Any], observed: dict[str, Any]) -> bool:
    gold_kind = str(gold.get("kind") or "").lower()
    obs_kind = str(observed.get("kind") or "").lower()
    if "observational" in gold_kind and "causal" in obs_kind:
        return True
    if (
        ("guideline" in gold_kind or "consensus" in gold_kind)
        and observed.get("effect")
        and not observed.get("recommendation")
    ):
        return True
    return False


def score_case(
    gold: dict[str, Any],
    observed: dict[str, Any],
    *,
    response_status: str,
    verifier_status: str,
    f0_frozen: bool,
) -> CaseScore:
    fields = ("kind",) + CRITICAL_FIELDS
    scores = tuple(
        score_field(field, gold.get(field), observed.get(field))
        for field in fields
    )

    reasons: list[str] = []
    critical_errors = sum(len(score.errors) for score in scores)

    if response_status == "defer":
        reasons.append(SemanticErrorType.SEMANTIC_DEFER.value)

    if verifier_status != "verified":
        reasons.append(SemanticErrorType.VERIFIER_REJECTION.value)

    if _causality_error(gold, observed):
        reasons.append(SemanticErrorType.CAUSALITY_LEVEL_MISMATCH.value)
        critical_errors += 1

    for score in scores:
        reasons.extend(score.errors)

    reasons = list(dict.fromkeys(reasons))

    exact = sum(
        1 for score in scores
        if score.match == FieldMatch.EXACT.value
    )
    comparable = sum(
        1 for score in scores
        if score.match != FieldMatch.NOT_APPLICABLE.value
    )

    high_risk_fields = {
        "population",
        "intervention",
        "exposure",
        "intervention_or_exposure",
        "outcome",
        "effect",
        "recommendation",
        "applicability_boundary",
    }
    high_risk_mismatch = any(
        score.field in high_risk_fields
        and score.match in {FieldMatch.MISMATCH.value, FieldMatch.MISSING.value}
        for score in scores
    )

    escalate = (
        response_status != "completed"
        or verifier_status != "verified"
        or not f0_frozen
        or high_risk_mismatch
        or SemanticErrorType.NUMERIC_EFFECT_MISMATCH.value in reasons
        or SemanticErrorType.CAUSALITY_LEVEL_MISMATCH.value in reasons
    )

    return CaseScore(
        evidence_id=gold["evidence_id"],
        source_id=gold["source_id"],
        response_status=response_status,
        verifier_status=verifier_status,
        f0_frozen=f0_frozen,
        field_scores=scores,
        critical_error_count=critical_errors,
        exact_field_count=exact,
        comparable_field_count=comparable,
        human_escalation_required=escalate,
        escalation_reasons=tuple(reasons if escalate else ()),
    )


def summarize_cases(
    batch_id: str,
    blindness_class: str,
    cases: list[CaseScore],
) -> BlindReplaySummary:
    completed = sum(c.response_status == "completed" for c in cases)
    deferred = sum(c.response_status == "defer" for c in cases)
    verifier_pass = sum(c.verifier_status == "verified" for c in cases)
    frozen = sum(c.f0_frozen for c in cases)
    escalated = sum(c.human_escalation_required for c in cases)
    critical = sum(c.critical_error_count for c in cases)
    exact = sum(c.exact_field_count for c in cases)
    near_or_exact = sum(
        1
        for case in cases
        for score in case.field_scores
        if score.match in {FieldMatch.EXACT.value, FieldMatch.NEAR.value}
    )
    comparable = sum(c.comparable_field_count for c in cases)
    n = len(cases)

    error_counts: dict[str, int] = {}
    for case in cases:
        seen = set(case.escalation_reasons)
        for score in case.field_scores:
            seen.update(score.errors)
        for error in seen:
            error_counts[error] = error_counts.get(error, 0) + 1

    return BlindReplaySummary(
        batch_id=batch_id,
        blindness_class=blindness_class,
        case_count=n,
        completed_response_count=completed,
        deferred_count=deferred,
        verifier_pass_count=verifier_pass,
        f0_freeze_count=frozen,
        human_escalation_count=escalated,
        critical_error_count=critical,
        exact_field_count=exact,
        near_or_exact_field_count=near_or_exact,
        comparable_field_count=comparable,
        exact_field_rate=(exact / comparable if comparable else 0.0),
        near_or_exact_field_rate=(
            near_or_exact / comparable if comparable else 0.0
        ),
        verifier_yield=(verifier_pass / n if n else 0.0),
        f0_yield=(frozen / n if n else 0.0),
        human_escalation_rate=(escalated / n if n else 0.0),
        error_counts=error_counts,
        cases=tuple(cases),
    )
