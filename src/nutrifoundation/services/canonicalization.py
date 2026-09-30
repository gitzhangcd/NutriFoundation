from __future__ import annotations

import re
import unicodedata
from typing import Any

from nutrifoundation.domain.semantic_equivalence import CanonicalSemanticForm


NUMBER_RE = re.compile(r"(?<![\d.])[-+−]?\d+(?:[\.,·]\d+)?%?")
PMID_RE = re.compile(r"pmid\s*[:#]?\s*(\d+)", re.I)

PHRASE_ALIASES = (
    (r"extra[- ]virgin olive oil", "evoo"),
    (r"type\s*2\s*diabetes(?:\s*mellitus)?|\bt2d\b", "t2d"),
    (r"chronic kidney disease|\bckd\b", "ckd"),
    (r"cardiovascular|\bcv\b", "cardiovascular"),
    (r"body[- ]?weight|weight change|weight loss", "weight"),
    (r"physical activity|physical exercise|exercise", "physical_activity"),
    (r"low[- ]carbohydrate|low carb", "low_carb"),
    (r"low[- ]fat", "low_fat"),
    (r"mediterranean[- ]style|mediterranean diet", "mediterranean"),
    (r"total diet replacement|\btdr\b", "total_diet_replacement"),
    (r"formula meal replacement(?:s)?", "meal_replacement"),
    (r"ultra[- ]?processed[- ]?food(?:s)?|\bupf\b", "ultraprocessed_food"),
    (r"whole[- ]grain(?:s)?", "whole_grain"),
    (r"refined[- ]grain(?:s)?", "refined_grain"),
    (r"medical nutrition therapy|\bmnt\b", "medical_nutrition_therapy"),
    (r"older persons?|older adults?|geriatric", "older_adult"),
    (r"malnutrition screening|screened for malnutrition", "malnutrition_screening"),
    (r"incident type 2 diabetes|incident t2d|diabetes incidence|incident diabetes", "incident_t2d"),
    (r"major cardiovascular event(?:s)?", "major_cardiovascular_event"),
    (r"diabetes remission|remission of diabetes", "diabetes_remission"),
    (r"systolic and diastolic blood pressure", "sbp dbp"),
    (r"systolic blood pressure|\bsbp\b", "sbp"),
    (r"diastolic blood pressure|\bdbp\b", "dbp"),
    (r"glycated hemoglobin|haemoglobin a1c|hemoglobin a1c|\bhba1c\b", "hba1c"),
    (r"impaired glucose tolerance|\bigt\b", "impaired_glucose_tolerance"),
    (r"routine|routinely", "routine"),
    (r"recommend(?:ed|ation)?|should", "recommendation"),
    (r"generaliz(?:e|ed)|generalised|extrapolat(?:e|ed)", "generalize"),
    (r"processed red meat|unprocessed red meat|red meat", "red_meat"),
    (r"poultry", "poultry"),
    (r"hazard ratio|\bhr\b", "hazard_ratio"),
    (r"risk ratio|relative risk|\brr\b", "risk_ratio"),
    (r"odds ratio|\bor(?=\s+\d)", "odds_ratio"),
    (r"confidence interval|\bci\b", "confidence_interval"),
    (r"\bgreater\b|\bhigher\b", "higher"),
    (r"\bconsumption\b|\bintake\b", "intake"),
)

STOPWORDS = {
    "a","an","the","of","to","and","or","for","in","on","at","by","with",
    "from","as","is","was","were","be","been","that","this","these","those",
    "among","across","than","vs","versus","per","after","during","into",
    "their","its","it","all","one","only","using","used","within","without",
}

SEMANTIC_TAG_PATTERNS = (
    (r"observational|cohort|association|associated", "association_level"),
    (r"randomized|randomised|\brct\b", "randomized_evidence"),
    (r"guideline|consensus", "guideline_authority"),
    (r"not randomized causal|not randomised causal|not causal|association rather than", "not_causal"),
    (r"multicomponent|multi-component|cannot attribute.*diet alone", "multicomponent"),
    (r"single[- ]center|single centre", "single_center"),
    (r"self[- ]reported", "self_report"),
    (r"unblind|not blinded", "unblinded"),
    (r"primary[- ]prevention", "primary_prevention"),
    (r"protocol.*deviation|randomization deviations|randomisation deviations", "protocol_deviation"),
    (r"subgroup|\b36 participants with diabetes\b", "subgroup"),
    (r"male[- ]dominant|86% male", "male_dominant"),
    (r"without diabetes|nondiabetic|non-diabetic", "without_diabetes"),
    (r"older_adult|older adult|older person|geriatric", "older_adult_scope"),
    (r"younger_adult|younger adult", "younger_adult_scope"),
    (r"french", "french_population"),
    (r"predominantly female|79\.2% women", "female_dominant"),
    (r"heterogeneity|heterogeneous", "heterogeneity"),
    (r"less robust|weaker under alternative", "robustness_caution"),
    (r"less than or equal to 1 year|<=\s*1 year|1 year or less|no longer than about one year|short[- ]term", "short_followup"),
    (r"full guideline|numerical nutrient target|specific targets require", "fulltext_needed_for_targets"),
)

CONFLICT_TAG_PAIRS = {
    ("association_level", "randomized_evidence"),
    ("not_causal", "randomized_evidence"),
    ("older_adult_scope", "younger_adult_scope"),
    ("without_diabetes", "t2d"),
    ("low_fat", "low_carb"),
    ("mediterranean", "low_fat"),
    ("mediterranean", "low_carb"),
    ("whole_grain", "refined_grain"),
    ("red_meat", "poultry"),
    ("impaired_glucose_tolerance", "t2d"),
}


def _normalize_number(token: str) -> str:
    token = (
        token.replace("−", "-")
        .replace("·", ".")
        .replace(",", "")
        .replace("%", "")
    )
    try:
        value = float(token)
    except ValueError:
        return token
    if value == int(value):
        return str(int(value))
    return f"{value:.8f}".rstrip("0").rstrip(".")


def _base_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = text.replace("−", "-").replace("·", ".")
    text = re.sub(r"(?<=\d)-(?=\d)", " to ", text)
    for pattern, replacement in PHRASE_ALIASES:
        text = re.sub(pattern, replacement, text, flags=re.I)
    return text


def canonicalize(field: str, value: Any) -> CanonicalSemanticForm:
    if value is None:
        return CanonicalSemanticForm(field=field)

    raw = str(value)
    text = _base_text(raw)
    numbers = tuple(sorted({_normalize_number(x) for x in NUMBER_RE.findall(text)}))

    identifiers = tuple(sorted({f"pmid:{m}" for m in PMID_RE.findall(raw)}))

    semantic_tags = {
        tag
        for pattern, tag in SEMANTIC_TAG_PATTERNS
        if re.search(pattern, text, flags=re.I)
    }

    words = re.findall(r"[a-z_][a-z0-9_]*", text)
    concepts = {
        word
        for word in words
        if word not in STOPWORDS
        and len(word) > 1
        and not word.isdigit()
    }

    kind_aliases = {
        "intervention_effect": {"intervention_effect", "causal_intervention"},
        "synthesis_effect": {"synthesis_effect", "evidence_synthesis"},
        "observational_association": {"observational_association", "association_level"},
        "observational_association_synthesis": {
            "observational_association_synthesis",
            "association_level",
            "evidence_synthesis",
        },
        "guideline_recommendation": {"guideline_recommendation", "guideline_authority"},
        "guideline_scope_and_recommendation": {
            "guideline_scope_and_recommendation",
            "guideline_authority",
        },
        "consensus_recommendation": {"consensus_recommendation", "guideline_authority"},
    }
    if field == "kind":
        compact = re.sub(r"[^a-z_]", "", text)
        concepts = set(kind_aliases.get(compact, {compact} if compact else set()))
        semantic_tags |= concepts

    if field == "effect" and "confidence_interval" in concepts:
        numbers = tuple(number for number in numbers if number != "95")

    return CanonicalSemanticForm(
        field=field,
        concepts=tuple(sorted(concepts)),
        numbers=numbers,
        semantic_tags=tuple(sorted(semantic_tags)),
        identifiers=identifiers,
        normalized_text=" ".join(words),
    )


def conflict_tags(
    reference: CanonicalSemanticForm,
    candidate: CanonicalSemanticForm,
) -> tuple[str, ...]:
    ref = set(reference.semantic_tags) | set(reference.concepts)
    cand = set(candidate.semantic_tags) | set(candidate.concepts)
    conflicts: list[str] = []
    for a, b in CONFLICT_TAG_PAIRS:
        forward = a in ref and b in cand and b not in ref and a not in cand
        reverse = b in ref and a in cand and a not in ref and b not in cand
        if forward or reverse:
            conflicts.append(f"{a}!={b}")
    return tuple(sorted(conflicts))
