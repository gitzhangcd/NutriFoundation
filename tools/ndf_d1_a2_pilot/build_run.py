#!/usr/bin/env python3
"""Write the NDF-D1-A2-PILOT run. Does not modify the frozen R1.3.1 directory."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

from tools.ndf_d1_a2_pilot.extract import extract_anchors
from tools.ndf_d1_a2_pilot.needles import NEEDLES
from tools.ndf_d1_a2_pilot.verify import arithmetic_checks, compare, rebuild
from tools.source_archive_verifier.identity_evaluator import calculate_sha256, evaluate_pdf_identity_canonical

FROZEN = Path("/Users/zhangcd/Codes/Ai-Nutri/data/g1_source_library/verification_runs/G1S-R131-IDENTITY-BLOCK-D1-RECOVERY-20261010T101500Z")
VAULT = Path("/Users/zhangcd/Codes/Ai-Nutri/data/g1_source_library")
CUTOFF = "2026-10-07"
REPO = Path("/Users/zhangcd/Codes/NutriFoundation")


def _jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _redact(value):
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if "cookie" in key.lower() or key.lower() in {"set-cookie", "authorization"}:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, str) and ("set-cookie" in value.lower() or value.lower().startswith("bearer ")):
        return "[REDACTED]"
    return value


def build(run_dir: Path) -> dict:
    if FROZEN in run_dir.parents or run_dir == FROZEN:
        raise SystemExit("refusing to write inside the frozen R1.3.1 run")
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = {row["source_id"]: row for row in _load(VAULT / "Archived_Papers_133_Manifest.json")["records"]}
    pdfs = {}
    artifacts = []
    studies = []
    for sid, title_key in (("CAND-G100-004", "004"), ("CAND-G100-033", "033")):
        qual = _load(FROZEN / "ndf_d1_12_source_recovery" / sid / "qualification.json")
        source_pdf = FROZEN / "ndf_d1_12_source_recovery" / sid / "reacquired_source.pdf"
        copied = run_dir / "private_originals" / sid / "reacquired_source.pdf"
        copied.parent.mkdir(parents=True, exist_ok=True)
        if not copied.exists():
            shutil.copy2(source_pdf, copied)
        pdfs[sid] = copied
        record = manifest[sid]
        identity = evaluate_pdf_identity_canonical(
            copied,
            record["title"],
            record["identifiers"].get("doi") or "",
            record["identifiers"].get("pmid") or "",
            source_id=sid,
            expected_journal=record.get("journal") or "",
            expected_date=record.get("publication_date") or "",
        )
        event = qual["new_asset_revision"]["event"]
        file_sha = calculate_sha256(copied)
        published = qual.get("version_of_record_date")
        artifacts.append({
            "source_artifact_id": f"SA-{sid}",
            "source_id": sid,
            "title": record["title"],
            "doi": record["identifiers"].get("doi"),
            "pmid": record["identifiers"].get("pmid"),
            "journal": record.get("journal"),
            "manifest_publication_date": record.get("publication_date"),
            "version_of_record_date": published,
            "license_evidence": qual.get("license_evidence"),
            "license_note": "CC BY 4.0 requires attribution. Internal extraction does not remove that requirement.",
            "acquisition_revision": qual["new_asset_revision"]["asset_revision_id"],
            "retrieved_at": event["retrieved_at"],
            "source_url": event["source_url"],
            "sha256": file_sha,
            "sha256_matches_acquisition_event": file_sha == event["asset_sha256"],
            "identity_verdict": identity["identity_verdict"],
            "identity_status": identity["identity_status"],
            "article_identity_block_id": identity.get("article_identity_block_id"),
            "evidence_cutoff": CUTOFF,
            "publication_on_or_before_cutoff": bool(published and published <= CUTOFF),
            "retrieval_after_cutoff": event["retrieved_at"][:10] > CUTOFF,
            "retrieval_is_not_publication_date": True,
            "historical_acquisition": "HISTORICAL_ACQUISITION_UNPROVEN",
        })
        studies.append({
            "study_identity_id": "STUDY-CHICTR2000029797" if sid.endswith("004") else "STUDY-UKB-APP-29239",
            "source_artifact_id": f"SA-{sid}",
            "source_id": sid,
            "design": "RANDOMIZED_THREE_ARM_COMPLETER_ANALYSIS" if sid.endswith("004") else "PROSPECTIVE_COHORT_OBSERVATIONAL",
            "registry_or_cohort": "ChiCTR2000029797" if sid.endswith("004") else "UK Biobank Application Number 29239",
            "related_publications_in_this_pilot": [record["identifiers"].get("doi")],
            "synthesis_with_other_pilot_source": "NOT_MERGED",
        })
    anchors = extract_anchors(pdfs)
    _jsonl(run_dir / "SourceAnchor_Index.jsonl", anchors)
    verifier_rows = rebuild(pdfs)
    verification, disagreements = compare(anchors, verifier_rows, pdfs)
    for check in arithmetic_checks(pdfs):
        verification.append({"anchor_id": check["check_id"], "source_id": "ARITHMETIC", "evidence_unit_id": None, "verifier_rebuilt_from_pdf": False, "extractor_literal_matches_verifier": None, "replay_ok": check["ok"], "risk": check.get("risk", "NONE" if check["ok"] else "ARITHMETIC"), "detail": check})
        if not check["ok"]:
            disagreements.append({
                "source_id": "CAND-G100-004" if "004" in check["check_id"] else "CAND-G100-033",
                "object_id": check["check_id"],
                "field": "consistency",
                "extractor_value": "",
                "verifier_value": json.dumps(check.get("observed", check["ok"]), ensure_ascii=False),
                "risk": check.get("risk", "CHECK_FAILED"),
            })
    _jsonl(run_dir / "Independent_Verification_Results.jsonl", verification)
    with (run_dir / "Disagreement_Log.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, ["source_id", "object_id", "field", "extractor_value", "verifier_value", "risk"])
        writer.writeheader()
        writer.writerows(disagreements)
    located = {row["anchor_id"]: row for row in anchors if row["locator_status"] == "LOCATED"}
    missing = [row["anchor_id"] for row in anchors if row["locator_status"] != "LOCATED"]
    unit_ids = []
    for spec in NEEDLES:
        if spec["evidence_unit_id"] not in unit_ids:
            unit_ids.append(spec["evidence_unit_id"])
    descriptions = {
        "EU-004-ALLOC": "Allocation counts and trial registry for the three eating windows.",
        "EU-004-COMPLETERS": "Completer counts and exclusion of participants who did not finish. Table 1 age string is from the analyzed sample.",
        "EU-004-HOMA": "Five-week completer comparison of HOMA-IR change. Abstract names the primary outcome as insulin resistance. Significance threshold is stated as P < 0.05 and is not an evidence-strength grade.",
        "EU-004-FPG": "Fasting plasma glucose change for eTRF versus control, and the reported mTRF change.",
        "EU-004-MASS": "Body-mass change for eTRF, mTRF, and control.",
        "EU-004-ENERGY": "Reported energy-intake change. This is not the named primary outcome.",
        "EU-004-SAE": "No serious adverse events were reported during the trial. This does not establish long-term safety.",
        "EU-004-BP-LIPIDS": "Blood-pressure changes were reported as not significantly different. Lipid p values are not copied here unless their own span is attached.",
        "EU-033-COHORT": "UK Biobank application, first 24-hour recall exposure, and included sample size.",
        "EU-033-OBESITY": "Incident overall obesity, BMI at least 30 kg/m2, highest versus lowest ultra-processed quartile, adjusted hazard ratio.",
        "EU-033-ABDOMINAL": "Incident abdominal obesity hazard ratio, highest versus lowest quartile.",
        "EU-033-BMI5": "Hazard ratio for a gain of at least 5 percent in BMI.",
        "EU-033-WC5": "Hazard ratio for a gain of at least 5 percent in waist circumference.",
        "EU-033-BF5": "Hazard ratio for a gain of at least 5 percent in body fat.",
        "EU-033-CONTINUOUS-OBESITY": "Per 10 percent higher ultra-processed energy share, overall obesity hazard ratio whose interval includes 1.",
        "EU-033-LIMITATION": "Authors state residual confounding cannot be completely ruled out. The design is observational.",
    }
    scopes = {
        "EU-004-ALLOC": {"population": "healthy volunteers without obesity", "intervention": "eTRF, mTRF, or ad libitum control", "time": "five-week trial"},
        "EU-004-COMPLETERS": {"analysis_population": "participants who completed five weeks", "missing": "eight non-completers excluded from analysis"},
        "EU-004-HOMA": {"outcome": "change in HOMA-IR", "comparison": "eTRF versus mTRF and eTRF versus control", "time": "five weeks", "effect_measure": "mean change plus or minus SD and pairwise p values"},
        "EU-004-FPG": {"outcome": "change in fasting plasma glucose", "comparison": "eTRF versus control; mTRF change also reported", "time": "five weeks"},
        "EU-004-MASS": {"outcome": "change in body mass", "comparison": "eTRF versus control; mTRF change also reported", "time": "five weeks"},
        "EU-004-ENERGY": {"outcome": "change in estimated energy intake", "time": "five weeks", "role": "not the named primary outcome"},
        "EU-004-SAE": {"outcome": "serious adverse events during the trial", "reported_count_language": "none reported"},
        "EU-004-BP-LIPIDS": {"outcome": "SBP, DBP, and MAP change", "result_language": "not significantly different at the reported p values"},
        "EU-033-COHORT": {"population": "UK Biobank adults with a valid first 24-hour recall and repeated adiposity measures", "exposure": "ultra-processed food as percent of energy, NOVA, first recall"},
        "EU-033-OBESITY": {"outcome": "incident BMI >= 30 kg/m2", "exposure": "highest versus lowest sex-specific quartile", "design": "observational Cox model", "causal_claim": "NOT_MADE"},
        "EU-033-ABDOMINAL": {"outcome": "incident high waist circumference", "design": "observational", "causal_claim": "NOT_MADE"},
        "EU-033-BMI5": {"outcome": ">=5% BMI increase", "design": "observational", "causal_claim": "NOT_MADE"},
        "EU-033-WC5": {"outcome": ">=5% waist circumference increase", "design": "observational", "causal_claim": "NOT_MADE"},
        "EU-033-BF5": {"outcome": ">=5% body-fat increase", "design": "observational", "causal_claim": "NOT_MADE"},
        "EU-033-CONTINUOUS-OBESITY": {"outcome": "incident overall obesity per 10% higher ultra-processed energy share", "interval_contains_1": True, "causal_claim": "NOT_MADE"},
        "EU-033-LIMITATION": {"limitation": "residual confounding not excluded", "design": "observational"},
    }
    units = []
    for unit_id in unit_ids:
        own = [row for row in anchors if row["evidence_unit_id"] == unit_id]
        all_located = all(row["locator_status"] == "LOCATED" for row in own) and bool(own)
        sid = own[0]["source_id"]
        units.append({
            "evidence_unit_id": unit_id,
            "source_id": sid,
            "study_identity_id": "STUDY-CHICTR2000029797" if sid.endswith("004") else "STUDY-UKB-APP-29239",
            "question_id": "Q-PILOT-004-001" if sid.endswith("004") else "Q-PILOT-033-001",
            "description": descriptions[unit_id],
            "scope": scopes[unit_id],
            "anchor_ids": [row["anchor_id"] for row in own],
            "status": "SOURCE_SPAN_VERIFIED" if all_located else "HOLD",
            "lineage": "PDF page text span; abstract was not used as a substitute for a missing body span",
            "statistical_significance_is_not_evidence_strength": True,
            "values_not_reported_in_attached_spans": "NOT_IMPUTED",
        })
    _jsonl(run_dir / "EvidenceUnit_Candidates.jsonl", units)
    claims = [
        {
            "claim_id": "SC-004-HOMA",
            "source_id": "CAND-G100-004",
            "question_id": "Q-PILOT-004-001",
            "evidence_unit_ids": ["EU-004-HOMA", "EU-004-COMPLETERS", "EU-004-ALLOC"],
            "anchor_ids": ["A-004-HOMA", "A-004-COMPLETERS", "A-004-PRIMARY-NAME", "A-004-WINDOWS"],
            "scope": "Five-week completer comparison in healthy volunteers without obesity.",
            "relation": "eTRF mean HOMA-IR change was more negative than mTRF and control in the reported pairwise tests.",
            "causal_semantics": "RANDOMIZED_ARM_COMPARISON_WITHIN_THIS_TRIAL",
            "prohibited_reading": "Not an individualized clinical benefit and not a claim that human outcomes improved beyond the reported trial measurements.",
            "status": "HUMAN_REVIEW_REQUIRED",
            "expert_gold": "NOT_GRANTED",
        },
        {
            "claim_id": "SC-004-FPG",
            "source_id": "CAND-G100-004",
            "question_id": "Q-PILOT-004-001",
            "evidence_unit_ids": ["EU-004-FPG"],
            "anchor_ids": ["A-004-FPG", "A-004-FPG-MTRF"],
            "scope": "Fasting plasma glucose over five weeks.",
            "relation": "eTRF versus control difference is reported; mTRF versus control is reported as no difference.",
            "causal_semantics": "RANDOMIZED_ARM_COMPARISON_WITHIN_THIS_TRIAL",
            "status": "HUMAN_REVIEW_REQUIRED",
            "expert_gold": "NOT_GRANTED",
        },
        {
            "claim_id": "SC-004-MASS",
            "source_id": "CAND-G100-004",
            "question_id": "Q-PILOT-004-001",
            "evidence_unit_ids": ["EU-004-MASS"],
            "anchor_ids": ["A-004-MASS-ETRF", "A-004-MASS", "A-004-MASS-CONTROL"],
            "scope": "Body mass over five weeks.",
            "relation": "eTRF versus control reduction is reported; mTRF change is reported separately.",
            "causal_semantics": "RANDOMIZED_ARM_COMPARISON_WITHIN_THIS_TRIAL",
            "status": "HUMAN_REVIEW_REQUIRED",
            "expert_gold": "NOT_GRANTED",
        },
        {
            "claim_id": "SC-033-QUARTILE",
            "source_id": "CAND-G100-033",
            "question_id": "Q-PILOT-033-001",
            "evidence_unit_ids": ["EU-033-OBESITY", "EU-033-ABDOMINAL", "EU-033-BMI5", "EU-033-WC5", "EU-033-BF5", "EU-033-LIMITATION"],
            "anchor_ids": ["A-033-OB-HR", "A-033-TABLE-OB", "A-033-ABD-HR", "A-033-BMI5", "A-033-WC5", "A-033-BF5", "A-033-CONFOUNDING"],
            "scope": "UK Biobank adults, first 24-hour recall, follow-up adiposity, adjusted Cox models.",
            "relation": "Higher ultra-processed quartile is associated with higher hazard for the reported obesity indicators.",
            "causal_semantics": "OBSERVATIONAL_ASSOCIATION_NOT_A_CAUSAL_EFFECT",
            "status": "HUMAN_REVIEW_REQUIRED",
            "expert_gold": "NOT_GRANTED",
        },
        {
            "claim_id": "SC-033-CONTINUOUS-NOT-SIGNIFICANT",
            "source_id": "CAND-G100-033",
            "question_id": "Q-PILOT-033-001",
            "evidence_unit_ids": ["EU-033-CONTINUOUS-OBESITY"],
            "anchor_ids": ["A-033-CONT"],
            "scope": "Overall obesity per 10 percent higher ultra-processed energy share.",
            "relation": "The adjusted interval includes 1. The paper calls this association not statistically significant.",
            "causal_semantics": "OBSERVATIONAL_ASSOCIATION_NOT_A_CAUSAL_EFFECT",
            "status": "HUMAN_REVIEW_REQUIRED",
            "expert_gold": "NOT_GRANTED",
        },
    ]
    _jsonl(run_dir / "ScientificClaim_Candidates.jsonl", claims)
    _jsonl(run_dir / "SourceArtifact_2.jsonl", artifacts)
    _jsonl(run_dir / "StudyIdentity_2.jsonl", studies)
    relations = [
        {"relation_id": "REL-004-033", "type": "NOT_ELIGIBLE_FOR_JOINT_SYNTHESIS", "members": ["CAND-G100-004", "CAND-G100-033"], "reason": "Different designs, populations, exposures, and estimands."},
    ]
    dependencies = [
        {"dependency_id": "DEP-004-REGISTRY", "study_identity_id": "STUDY-CHICTR2000029797", "depends_on": "ChiCTR2000029797", "fact_anchor": "A-004-REGISTRY"},
        {"dependency_id": "DEP-033-UKB", "study_identity_id": "STUDY-UKB-APP-29239", "depends_on": "UK Biobank Application Number 29239", "fact_anchor": "A-033-APP", "reuse_risk": "SAME_COHORT_MAY_APPEAR_IN_OTHER_PAPERS"},
    ]
    (run_dir / "ScientificRelation_and_StudyDependency.json").write_text(json.dumps({"relations": relations, "dependencies": dependencies}, indent=2), encoding="utf-8")
    replay_report = {
        "anchors_expected": len(NEEDLES),
        "anchors_located": len(located),
        "anchors_missing": missing,
        "replay_failures": [row["anchor_id"] for row in verification if row.get("replay_ok") is False and row.get("source_id") != "ARITHMETIC"],
        "arithmetic_failures": [row["anchor_id"] for row in verification if row.get("source_id") == "ARITHMETIC" and row.get("replay_ok") is False],
    }
    (run_dir / "SourceSpan_Replay_Report.json").write_text(json.dumps(replay_report, indent=2), encoding="utf-8")
    gates = []
    for unit in units:
        identity_ok = next(item["identity_verdict"] == "CONFIRMED" and item["sha256_matches_acquisition_event"] for item in artifacts if item["source_id"] == unit["source_id"])
        l2 = unit["status"] == "SOURCE_SPAN_VERIFIED"
        gates.append({
            "evidence_unit_id": unit["evidence_unit_id"],
            "source_id": unit["source_id"],
            "L1_mechanical": "PASS" if identity_ok else "HOLD",
            "L2_source_span": "PASS" if l2 else "HOLD",
            "L3_semantic_scope": "HOLD_HUMAN_REVIEW_REQUIRED",
            "L4_scientific_qualification": "HOLD",
            "status": "SOURCE_SPAN_VERIFIED" if identity_ok and l2 else "HOLD",
            "QUALIFIED_FOR_SPECIFIC_QUESTION": False,
            "expert_gold": "NOT_GRANTED",
        })
    (run_dir / "Evidence_Qualification_Gates.json").write_text(json.dumps({
        "scale": {"L1": "mechanical integrity", "L2": "source-span support", "L3": "semantic scope", "L4": "scientific qualification"},
        "promotion_rule": "Agent span verification does not grant L3, L4, Expert Gold, or QUALIFIED_FOR_SPECIFIC_QUESTION.",
        "units_extracted": len(units),
        "units_l1_pass": sum(1 for row in gates if row["L1_mechanical"] == "PASS"),
        "units_l2_pass": sum(1 for row in gates if row["L2_source_span"] == "PASS"),
        "units_l3_pass": 0,
        "units_l4_pass": 0,
        "units_qualified_for_specific_question": 0,
        "records": gates,
    }, indent=2), encoding="utf-8")
    (run_dir / "EvidenceQuestion_Alignment.json").write_text(json.dumps({
        "registry_search": {
            "sought": "itemized legacy 31 Evidence Question registry",
            "found_in_repository": False,
            "named_historical_item": {"id": "EQ-010", "text": "Dietary patterns in prediabetes/T2D", "exact_match_to_either_source": False},
            "active_question": {"id": "SQ-D1-A1R-001", "exact_match_to_either_source": False, "reason": "That question is information sufficiency for one NHANES-derived episode."},
            "ontology_modified": False,
        },
        "sources": [
            {"source_id": "CAND-G100-004", "mapping": "QUESTION_GAP", "candidate_question_id": "Q-PILOT-004-001", "candidate_question": "Among healthy adults without obesity, what are the five-week completer differences of eTRF, mTRF, and ad libitum intake for HOMA-IR, fasting glucose, and body mass?", "elements": ["time: five weeks", "population: healthy volunteers without obesity", "intervention: eTRF eating window", "comparator: mTRF and ad libitum", "outcomes: HOMA-IR, fasting plasma glucose, body mass"]},
            {"source_id": "CAND-G100-033", "mapping": "QUESTION_GAP", "candidate_question_id": "Q-PILOT-033-001", "candidate_question": "Among UK Biobank adults, what is the observational association between the ultra-processed share of energy on the first 24-hour recall and later obesity indicators after the reported covariate adjustment?", "elements": ["exposure measurement: first 24-hour recall, NOVA, percent of energy", "covariate adjustment: models described in the paper", "design: prospective cohort", "causal claim: not made"]},
        ],
        "joint_synthesis": "NOT_CREATED",
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "ScientificReferenceState_Drafts.json").write_text(json.dumps({
        "status": "DRAFT",
        "formal_qualification": "NOT_GRANTED",
        "expert_gold": "NOT_GRANTED",
        "drafts": [
            {"reference_id": "SRS-PILOT-004-DRAFT", "question_id": "Q-PILOT-004-001", "supporting_claim_ids": ["SC-004-HOMA", "SC-004-FPG", "SC-004-MASS"], "gaps": ["L3 and L4 not reviewed by an expert", "completer analysis is not an intention-to-treat estimate", "no joint synthesis with the cohort paper"]},
            {"reference_id": "SRS-PILOT-033-DRAFT", "question_id": "Q-PILOT-033-001", "supporting_claim_ids": ["SC-033-QUARTILE", "SC-033-CONTINUOUS-NOT-SIGNIFICANT"], "gaps": ["observational residual confounding stated by the authors", "same-cohort reuse not audited beyond this paper", "L3 and L4 not reviewed by an expert"]},
        ],
    }, indent=2), encoding="utf-8")
    (run_dir / "VerificationRecord.json").write_text(json.dumps({
        "verifier": "tools.ndf_d1_a2_pilot.verify",
        "rule": "Verifier re-opened the PDF and compared literals. Extractor JSON was a diff target, not the evidence.",
        "change_log": ["Initial pilot extraction. No upstream ontology edit."],
        "replay_report_file": "SourceSpan_Replay_Report.json",
    }, indent=2), encoding="utf-8")
    _write_oa_pack(run_dir)
    snapshot = run_dir / "source_snapshot"
    snapshot.mkdir(exist_ok=True)
    for rel in [
        "tools/source_archive_verifier/fixtures/quarantine_registry_r1_3.json",
        "tools/ndf_d1_a2_pilot/needles.py",
        "tools/ndf_d1_a2_pilot/extract.py",
        "tools/ndf_d1_a2_pilot/verify.py",
        "tools/source_archive_verifier/identity_evaluator.py",
    ]:
        dest = snapshot / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest)
    summary = {
        "evidence_units": len(units),
        "units_by_source": {
            "CAND-G100-004": sum(1 for row in units if row["source_id"] == "CAND-G100-004"),
            "CAND-G100-033": sum(1 for row in units if row["source_id"] == "CAND-G100-033"),
        },
        "source_span_verified": sum(1 for row in units if row["status"] == "SOURCE_SPAN_VERIFIED"),
        "hold_units": [row["evidence_unit_id"] for row in units if row["status"] == "HOLD"],
        "missing_anchors": missing,
        "l1_pass": sum(1 for row in gates if row["L1_mechanical"] == "PASS"),
        "l2_pass": sum(1 for row in gates if row["L2_source_span"] == "PASS"),
        "l3_pass": 0,
        "l4_pass": 0,
        "qualified_for_specific_question": 0,
        "expert_gold": "NOT_GRANTED",
        "reference_state": "DRAFT",
    }
    (run_dir / "pilot_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_hold_note(run_dir, summary)
    _write_share_projection(run_dir)
    return summary


def _write_oa_pack(run_dir: Path) -> None:
    rows = []
    recovery = FROZEN / "ndf_d1_12_source_recovery"
    manual = ["CAND-G100-095", "CAND-G100-096", "CAND-G100-005", "CAND-G100-046", "CAND-G100-048", "CAND-G100-055"]
    no_route = ["CAND-G100-002", "CAND-G100-047", "CAND-G100-051", "CAND-G100-064"]
    for sid in manual + no_route:
        qual = _load(recovery / sid / "qualification.json")
        attempts = qual.get("acquisition", {}).get("attempts") or []
        last = attempts[-1] if attempts else {}
        urls = " | ".join(item.get("requested_url", "") for item in attempts)
        rows.append({
            "source_id": sid,
            "task": "HUMAN_DOWNLOAD" if sid in manual else "NO_QUALIFYING_OA_ROUTE_FOUND_THIS_RUN",
            "expected_doi": qual["external_crosscheck"].get("manifest_title") and "",
            "expected_title": qual["external_crosscheck"].get("manifest_title"),
            "recorded_urls": urls,
            "last_http_status": last.get("http_status", ""),
            "last_content_type": last.get("content_type", ""),
            "save_path": f"ndf_d1_12_source_recovery/{sid}/reacquired_source.pdf",
            "new_revision_id": "",
            "sha256": "",
            "retrieved_at_utc": "",
            "license_evidence": "",
            "operator_id": "",
            "instruction": "Save the publisher or PMC PDF without bypassing access control. Fill the empty revision fields after the file exists. Do not overwrite the vault original.",
        })
    manifest = {row["source_id"]: row for row in _load(VAULT / "Archived_Papers_133_Manifest.json")["records"]}
    for row in rows:
        row["expected_doi"] = manifest[row["source_id"]]["identifiers"].get("doi") or ""
    with (run_dir / "OA_Human_Download_Workpack.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_hold_note(run_dir: Path, summary: dict) -> None:
    text = """# HOLD 与例外

`RELEASE_FOR_EXTRACTION` 只允许内部候选抽取。本试点没有授予 Expert Gold，也没有把两条来源合成一个证据体。

## 仍为 HOLD 的来源

人工下载任务，公开地址有记录但本次没有拿到 PDF：`CAND-G100-095`、`096`、`005`、`046`、`048`、`055`。

本次 Europe PMC / Crossref 没有找到符合规则的公开 PDF 入口：`CAND-G100-002`、`047`、`051`、`064`。这个记录的名称是 `NO_QUALIFYING_OA_ROUTE_FOUND_THIS_RUN`。它表示本轮工具没有找到合格公开路线，不表示机构订阅、作者授权文本或其他合法渠道都不存在。

## 两条已抽取来源

L1 与 L2 见 `Evidence_Qualification_Gates.json`。L3 与 L4 保持 `HOLD_HUMAN_REVIEW_REQUIRED`。`QUALIFIED_FOR_SPECIFIC_QUESTION` 为 0。ScientificReferenceState 只有 DRAFT。

重新获取时间是 2026-10-10，晚于证据 cutoff `2026-10-07`。该时间是获取事件，不是论文发表日期，也不是历史可获得时间。

图 1 的文本层把 “Allocated to eTRF” 出现了两次，并且没有 “Allocated to control” 字符串。正文写明三个组。这记为文本层风险，不改写原图。
"""
    (run_dir / "HOLD_And_Exceptions.md").write_text(text, encoding="utf-8")
    (run_dir / "pilot_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _write_share_projection(run_dir: Path) -> None:
    share = run_dir / "share_redacted"
    if share.exists():
        shutil.rmtree(share)
    share.mkdir()
    skip_parts = {"private_originals", "share_redacted"}
    for path in run_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(run_dir)
        if any(part in skip_parts for part in relative.parts):
            continue
        if path.suffix == ".pdf" or path.name == "http_response_headers.json":
            continue
        dest = share / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                dest.write_bytes(path.read_bytes())
                continue
            dest.write_text(json.dumps(_redact(payload), indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            dest.write_bytes(path.read_bytes())
    private_headers = FROZEN / "ndf_d1_12_source_recovery"
    redacted_dir = share / "redacted_http_headers"
    redacted_dir.mkdir()
    for path in private_headers.glob("*/http_response_headers.json"):
        payload = _redact(json.loads(path.read_text(encoding="utf-8")))
        (redacted_dir / f"{path.parent.name}_http_response_headers.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def seal(run_dir: Path) -> None:
    import zipfile
    manifest_path = run_dir / "Run_Integrity_Manifest.json"
    private_zip = run_dir / "A2_PILOT_Private_Package.zip"
    share_zip = run_dir / "A2_PILOT_Share_Package.zip"
    for path in (manifest_path, private_zip, share_zip):
        if path.exists():
            path.unlink()
    files = sorted(path for path in run_dir.rglob("*") if path.is_file() and "share_redacted" not in path.parts)
    entries = [{"path": str(path.relative_to(run_dir)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size} for path in files]
    manifest_path.write_text(json.dumps({"run_id": run_dir.name, "self_hash": "EXCLUDED", "file_count": len(entries), "files": entries}, indent=2), encoding="utf-8")
    with zipfile.ZipFile(private_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(path for path in run_dir.rglob("*") if path.is_file() and path != private_zip and path != share_zip and "share_redacted" not in path.parts):
            archive.write(path, path.relative_to(run_dir).as_posix())
    with zipfile.ZipFile(share_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        share = run_dir / "share_redacted"
        for path in sorted(path for path in share.rglob("*") if path.is_file()):
            archive.write(path, path.relative_to(share).as_posix())


if __name__ == "__main__":
    import sys
    destination = Path(sys.argv[1])
    print(json.dumps(build(destination), indent=2))
