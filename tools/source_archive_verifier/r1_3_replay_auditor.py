#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1.3 replay auditor. Writes a new run directory and does not modify prior runs or PDFs."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import fitz
from pypdf import PdfReader

from tools.source_archive_verifier.identity_evaluator import (
    aggregate_identity_gate,
    aggregate_provenance_gate,
    aggregate_rights_gate,
    aggregate_study_type_gate,
    calculate_sha256,
    evaluate_acquisition_provenance,
    evaluate_content_completeness,
    evaluate_manifest_integrity,
    evaluate_pdf_identity_canonical,
    evaluate_rights_posture,
    replay_proof_anchor,
    resolve_administrative_hold,
    semantic_verdict,
)

VAULT_ROOT = Path("/Users/zhangcd/Codes/Ai-Nutri/data/g1_source_library")
MANIFEST_FILE = VAULT_ROOT / "Archived_Papers_133_Manifest.json"
REPO = Path("/Users/zhangcd/Codes/NutriFoundation")
RULE_VERSION = "v1.3-content-identity-and-evidence-qualification"
PRIOR_RUNS = {
    "R1": VAULT_ROOT / "verification_runs" / "G1S-133-R1-INDEPENDENT-REPLAY-20261010T032025Z",
    "R1.1": VAULT_ROOT / "verification_runs" / "G1S-133-R1-1-CONSISTENCY-REPAIR-20261010T034353Z",
    "R1.2": VAULT_ROOT / "verification_runs" / "G1S-133-R1-2-VALIDATOR-REQUALIFICATION-20261010T070815Z",
}
AUDIT_18 = {
    "CAND-G100-014": "Legacy study-type disagreement carried forward.",
    "CAND-G100-015": "Legacy study-type disagreement carried forward.",
    "CAND-G100-018": "Legacy study-type disagreement carried forward.",
    "CAND-G100-031": "Legacy study-type disagreement carried forward.",
    "CAND-G100-032": "Legacy study-type disagreement carried forward.",
    "CAND-G100-033": "Legacy study-type disagreement carried forward.",
    "CAND-G100-046": "Legacy study-type disagreement carried forward.",
    "CAND-G100-052": "Legacy study-type disagreement carried forward.",
    "CAND-G100-054": "Legacy study-type disagreement carried forward.",
    "CAND-G100-056": "Legacy study-type disagreement carried forward.",
    "CAND-G100-058": "Legacy study-type disagreement carried forward.",
    "CAND-G100-061": "Legacy study-type disagreement carried forward.",
    "CAND-G100-082": "Legacy study-type disagreement carried forward.",
    "CAND-G100-083": "Legacy study-type disagreement carried forward.",
    "SUPP-G1-012": "Legacy study-type disagreement carried forward.",
    "SUPP-G1-017": "Legacy study-type disagreement carried forward.",
    "SUPP-G1-029": "Legacy study-type disagreement carried forward.",
    "SUPP-G1-033": "Legacy study-type disagreement carried forward.",
}
KN_TERMS = {
    "KN-001": ("guideline", "consensus", "assessment", "recommendation", "standard"),
    "KN-002": ("individualized", "decision", "sufficient", "nutrition care"),
    "KN-003": ("blood pressure", "obesity", "overweight", "anthropometr", "body mass", "weight"),
    "KN-004": ("safety", "referral", "screening", "diabetes prevention"),
}


def _git(repo: Path, *args: str) -> str:
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=8)
        return proc.stdout.strip() if proc.returncode == 0 else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _snapshot_directory(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "status": "NOT_PROVEN", "reason": "DIRECTORY_MISSING", "files": []}
    files = []
    for item in sorted(path.rglob("*")):
        if item.is_file() and item.name != ".DS_Store":
            files.append({
                "filename": str(item.relative_to(path)),
                "size_bytes": item.stat().st_size,
                "sha256": calculate_sha256(item),
            })
    return {"path": str(path), "status": "PROVEN" if files else "NOT_PROVEN", "file_count": len(files), "files": files}


def _year_usable(value: str) -> bool:
    import re
    return bool(re.search(r"(?:19|20)\d{2}", value or ""))


def _load_download_index() -> dict:
    path = VAULT_ROOT / "download_summary.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row.get("source_id"): row for row in data.get("details", []) if row.get("source_id")}


def _candidate_log(sidecar: dict, download_row: dict | None) -> dict | None:
    log = {}
    if sidecar.get("archived_at"):
        log["retrieved_at"] = sidecar["archived_at"]
    if sidecar.get("file_sha256"):
        log["asset_sha256"] = sidecar["file_sha256"]
    elif download_row and download_row.get("sha256"):
        log["asset_sha256"] = download_row["sha256"]
    # Bibliographic links and channel names are not fetch logs.
    return log or None


class R1_3_ReplayAuditor:
    def __init__(self):
        self.now = datetime.now(timezone.utc)
        self.run_id = f"G1S-133-R1-3-TRUTHFULNESS-{self.now.strftime('%Y%m%dT%H%M%SZ')}"
        self.run_dir = VAULT_ROOT / "verification_runs" / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=False)
        self.records: list[dict] = []
        self.per_source: list[dict] = []
        self.manifest_sha = ""
        self.test_exit = None
        self.gates = {}

    def run(self):
        print(f"Run ID: {self.run_id}")
        self.records = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))["records"]
        self.manifest_sha = calculate_sha256(MANIFEST_FILE)
        self._write_env()
        self._write_input_snapshot()
        self._replay_sources()
        self._write_deltas()
        self._write_human_queue()
        self._write_release()
        self._write_gates()
        self._run_unit_tests()
        self._write_issues()
        self._write_report()
        self._copy_sources()
        self._seal()
        print(f"Package: {self.run_dir / 'R1_3_Independent_Audit_Package.zip'}")

    def _write_env(self):
        payload = {
            "run_id": self.run_id,
            "rule_version": RULE_VERSION,
            "execution_timestamp_utc": self.now.isoformat(),
            "python_executable": sys.executable,
            "python_version": sys.version,
            "pymupdf_version": fitz.version[0] if hasattr(fitz, "version") else "UNKNOWN",
            "pypdf_version": getattr(PdfReader, "__module__", "pypdf"),
            "git_branch": _git(REPO, "branch", "--show-current"),
            "execution_commit": _git(REPO, "rev-parse", "HEAD"),
            "delivery_commit": "PENDING_REPO_SUMMARY_COMMIT",
            "ci_status": "NOT_QUERIED_BEFORE_PUSH",
            "scientific_gold_status": "NOT_GRANTED",
            "pdf_replay_scope": "Local vault PDFs were opened by this run. This package does not contain those PDFs.",
            "expert_signature": "NOT_OBTAINED",
            "redistribution_license": "NOT_OBTAINED",
        }
        (self.run_dir / "00_environment_and_git_state.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _write_input_snapshot(self):
        prior = {name: _snapshot_directory(path) for name, path in PRIOR_RUNS.items()}
        payload = {
            "manifest_file": str(MANIFEST_FILE),
            "manifest_sha256": self.manifest_sha,
            "manifest_size_bytes": MANIFEST_FILE.stat().st_size,
            "manifest_modified": False,
            "record_count": len(self.records),
            "prior_run_sha256_snapshot": prior,
        }
        (self.run_dir / "01_original_inputs_and_prior_run_sha256.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )

    def _replay_sources(self):
        downloads = _load_download_index()
        g1_rows = []
        for index, record in enumerate(self.records, start=1):
            sid = record["source_id"]
            if index % 10 == 0 or index == 1:
                print(f"  source {index}/{len(self.records)} {sid}")
            asset = record["archive_asset"]
            vault_pdf = VAULT_ROOT / asset["vault_path"].strip()
            flat_pdf = VAULT_ROOT / asset["relative_pdf_path"].strip()
            expected_sha = asset["sha256"].strip()
            g1 = self._g1_g2(sid, vault_pdf, flat_pdf, expected_sha, asset["size_bytes"])
            g1_rows.append(g1)
            observed_sha = g1.get("observed_sha256") or ""
            identity = evaluate_pdf_identity_canonical(
                vault_pdf,
                record["title"],
                (record["identifiers"].get("doi") or ""),
                (record["identifiers"].get("pmid") or ""),
                source_id=sid,
                expected_journal=record.get("journal") or "",
                expected_date=record.get("publication_date") or "",
            )
            hold = resolve_administrative_hold(sid, observed_sha, manifest_revision=self.manifest_sha)
            completeness = evaluate_content_completeness(vault_pdf) if vault_pdf.exists() else {
                "content_completeness": "UNRESOLVED",
                "completeness_scope": "FILE_MISSING",
                "evidence": "Vault PDF missing.",
                "triggered_rules": ["FILE_MISSING"],
            }
            sidecar_path = VAULT_ROOT / "sources" / sid / "manifest.json"
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8")) if sidecar_path.exists() else {}
            provenance = evaluate_acquisition_provenance(
                asset.get("acquisition_channel"),
                _candidate_log(sidecar, downloads.get(sid)),
                observed_sha,
            )
            provenance["sidecar_path"] = str(sidecar_path) if sidecar_path.exists() else "MISSING"
            provenance["download_summary_path"] = str(VAULT_ROOT / "download_summary.json")
            provenance["bibliographic_links_are_not_fetch_logs"] = record.get("links") or {}
            rights = evaluate_rights_posture()
            legacy = sid in AUDIT_18
            study = {
                "source_id": sid,
                "manifest_claimed_type": record.get("source_type"),
                "study_type_qualification": "PROVISIONAL",
                "legacy_issue_derived": legacy,
                "adjudication_method": "LEGACY_ISSUE_CARRY_FORWARD_NOT_R1_3_MEASUREMENT" if legacy else "NOT_ADJUDICATED_THIS_RUN",
                "legacy_note": AUDIT_18.get(sid, ""),
                "triggered_rules": ["G5_NO_NEW_METHODOLOGICAL_MEASUREMENT"],
            }
            replay = replay_proof_anchor(vault_pdf, identity["proof_anchor"]) if vault_pdf.exists() else {"ok": False, "reason": "FILE_MISSING"}
            date_ok = _year_usable(record.get("publication_date") or "")
            row = {
                "source_id": sid,
                "asset_sha256": observed_sha,
                "expected_asset_sha256": expected_sha,
                "title": record["title"],
                "doi": record["identifiers"].get("doi") or "",
                "pmid": record["identifiers"].get("pmid") or "",
                "journal": record.get("journal") or "",
                "publication_date": record.get("publication_date") or "",
                "publication_date_usable": date_ok,
                "gate_g1_verdict": g1["gate_g1_verdict"],
                "gate_g2_verdict": g1["gate_g2_verdict"],
                "identity_verdict": identity["identity_verdict"],
                "observed_identity_verdict": identity["observed_identity_verdict"],
                "identity_status": identity["identity_status"],
                "match_rule": identity["match_rule"],
                "policy_id": identity.get("policy_id"),
                "secondary_credentials": identity.get("secondary_credentials") or [],
                "proof_anchor": identity["proof_anchor"],
                "anchor_replay_ok": replay.get("ok", False),
                "anchor_replay_reason": replay.get("reason"),
                "content_completeness": completeness["content_completeness"],
                "completeness_scope": completeness.get("completeness_scope"),
                "completeness_evidence": completeness.get("evidence"),
                "completeness_rules": completeness.get("triggered_rules"),
                "acquisition_provenance": provenance["acquisition_provenance"],
                "provenance_rules": provenance["triggered_rules"],
                "provenance_missing_fields": provenance["missing_fields"],
                "provenance_evidence_paths": {
                    "sidecar": provenance["sidecar_path"],
                    "download_summary": provenance["download_summary_path"],
                },
                "rights_legal_status": rights["rights_legal_status"],
                "redistribution_permission": rights["redistribution_permission"],
                "project_use_policy": rights["project_use_policy"],
                "project_policy_check": rights["project_policy_check"],
                "legal_verification_completed": rights["legal_verification_completed"],
                "study_type_qualification": study["study_type_qualification"],
                "legacy_issue_derived": legacy,
                "study_type_adjudication_method": study["adjudication_method"],
                "administrative_hold": hold,
                "human_review_status": "PENDING",
                "state_transitions": [
                    {"field": "identity_verdict", "to": identity["identity_verdict"], "reason": identity["match_rule"]},
                    {"field": "content_completeness", "to": completeness["content_completeness"], "reason": completeness.get("evidence")},
                    {"field": "acquisition_provenance", "to": provenance["acquisition_provenance"], "reason": provenance["reason"]},
                    {"field": "administrative_hold", "to": hold["active"], "reason": hold["reason"]},
                    {"field": "study_type_qualification", "to": "PROVISIONAL", "reason": study["adjudication_method"]},
                ],
            }
            self.per_source.append(row)
        with (self.run_dir / "02_G1_G2_replay.jsonl").open("w", encoding="utf-8") as handle:
            for row in g1_rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        with (self.run_dir / "03_per_source_results.jsonl").open("w", encoding="utf-8") as handle:
            for row in self.per_source:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._write_tables()

    def _g1_g2(self, sid, vault_pdf: Path, flat_pdf: Path, expected_sha: str, expected_size: int) -> dict:
        if not vault_pdf.exists() or not flat_pdf.exists():
            return {"source_id": sid, "file_exists": False, "gate_g1_verdict": "FAIL", "gate_g2_verdict": "FAIL", "observed_sha256": ""}
        observed = calculate_sha256(vault_pdf)
        flat_hash = calculate_sha256(flat_pdf)
        size = vault_pdf.stat().st_size
        g1 = observed.lower() == expected_sha.lower() and size == expected_size and observed == flat_hash
        can_fitz = can_pypdf = render_ok = False
        pages_fitz = pages_pypdf = 0
        try:
            doc = fitz.open(vault_pdf)
            can_fitz = True
            pages_fitz = len(doc)
            if pages_fitz:
                render_ok = True
                for page_index in {0, pages_fitz // 2, pages_fitz - 1}:
                    pix = doc[page_index].get_pixmap(dpi=36)
                    if pix.width == 0 or pix.height == 0:
                        render_ok = False
            doc.close()
        except Exception:
            pass
        try:
            reader = PdfReader(str(vault_pdf))
            can_pypdf = True
            pages_pypdf = len(reader.pages)
        except Exception:
            pass
        g2 = can_fitz and can_pypdf and pages_fitz == pages_pypdf and render_ok
        return {
            "source_id": sid,
            "file_exists": True,
            "expected_sha256": expected_sha,
            "observed_sha256": observed,
            "expected_size_bytes": expected_size,
            "observed_size_bytes": size,
            "dual_path_consistent": observed == flat_hash,
            "gate_g1_verdict": "PASS" if g1 else "FAIL",
            "page_count_pymupdf": pages_fitz,
            "page_count_pypdf": pages_pypdf,
            "render_sampled_pass": render_ok,
            "gate_g2_verdict": "PASS" if g2 else "FAIL",
        }

    def _write_tables(self):
        def dump(name, rows, fields):
            with (self.run_dir / name).open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
        dump("06_G4_provenance.csv", [
            {"source_id": r["source_id"], "acquisition_provenance": r["acquisition_provenance"], "missing_fields": "|".join(r["provenance_missing_fields"]), "sidecar": r["provenance_evidence_paths"]["sidecar"]}
            for r in self.per_source
        ], ["source_id", "acquisition_provenance", "missing_fields", "sidecar"])
        dump("07_G4_rights.csv", self.per_source, [
            "source_id", "rights_legal_status", "redistribution_permission", "project_use_policy", "project_policy_check", "legal_verification_completed"
        ])
        dump("08_G5_study_type.csv", self.per_source, [
            "source_id", "study_type_qualification", "legacy_issue_derived", "study_type_adjudication_method"
        ])

    def _write_deltas(self):
        r11 = {row["source_id"]: row for row in _read_jsonl(PRIOR_RUNS["R1.1"] / "04_identity_matching_replay_133.jsonl")}
        r12 = {row["source_id"]: row for row in _read_jsonl(PRIOR_RUNS["R1.2"] / "03_G3_identity_requalification_133.jsonl")}
        fields = [
            "source_id", "r11_raw_verdict", "r11_semantic_verdict", "r12_raw_verdict", "r12_semantic_verdict",
            "r13_verdict", "r13_status", "raw_enum_differs_r11_r13", "semantic_drift_r11_r13", "semantic_drift_r12_r13",
        ]
        rows = []
        for current in self.per_source:
            sid = current["source_id"]
            old11 = (r11.get(sid) or {}).get("gate_g3_verdict", "NOT_PROVEN")
            old12 = (r12.get(sid) or {}).get("identity_verdict", "NOT_PROVEN")
            rows.append({
                "source_id": sid,
                "r11_raw_verdict": old11,
                "r11_semantic_verdict": semantic_verdict(old11),
                "r12_raw_verdict": old12,
                "r12_semantic_verdict": semantic_verdict(old12),
                "r13_verdict": current["identity_verdict"],
                "r13_status": current["identity_status"],
                "raw_enum_differs_r11_r13": old11 != current["identity_verdict"],
                "semantic_drift_r11_r13": semantic_verdict(old11) != current["identity_verdict"],
                "semantic_drift_r12_r13": semantic_verdict(old12) != current["identity_verdict"],
            })
        with (self.run_dir / "05_semantic_delta_r11_r12_r13.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        summary = {
            "normalization": "Historical PASS is compared as CONFIRMED. Raw enum differences are reported separately.",
            "r11_rows_loaded": len(r11),
            "r12_rows_loaded": len(r12),
            "semantic_drift_r11_r13": sum(1 for row in rows if row["semantic_drift_r11_r13"]),
            "raw_enum_differs_r11_r13": sum(1 for row in rows if row["raw_enum_differs_r11_r13"]),
            "semantic_drift_r12_r13": sum(1 for row in rows if row["semantic_drift_r12_r13"]),
            "r13_counts": dict(Counter(row["r13_verdict"] for row in rows)),
        }
        if not r11:
            summary["r11_status"] = "NOT_PROVEN"
        if not r12:
            summary["r12_status"] = "NOT_PROVEN"
        (self.run_dir / "05_semantic_delta_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    def _write_human_queue(self):
        rows = []
        for row in self.per_source:
            reasons = []
            if row["identity_verdict"] != "CONFIRMED":
                reasons.append("IDENTITY_NOT_CONFIRMED")
            if row["administrative_hold"]["active"]:
                reasons.append("ADMINISTRATIVE_HOLD")
            if row["legacy_issue_derived"]:
                reasons.append("LEGACY_STUDY_TYPE")
            if not reasons:
                continue
            rows.append({
                "source_id": row["source_id"],
                "queue_reasons": "|".join(reasons),
                "legacy_issue_derived": row["legacy_issue_derived"],
                "anchor_page_this_run": row["proof_anchor"].get("page"),
                "identity_status": row["identity_status"],
                "human_review_status": "PENDING",
                "human_reviewer": "NOT_SIGNED",
                "expert_signature": "NOT_OBTAINED",
                "assigned_role": "METHODOLOGY_REVIEWER" if row["legacy_issue_derived"] else "LIBRARIAN",
            })
        fields = list(rows[0].keys()) if rows else ["source_id"]
        with (self.run_dir / "09_human_review_queue.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def _release_gaps(self, row: dict) -> list[str]:
        gaps = []
        if row["identity_verdict"] != "CONFIRMED":
            gaps.append("IDENTITY_NOT_CONFIRMED")
        if row["administrative_hold"]["active"]:
            gaps.append("ADMINISTRATIVE_HOLD")
        if row["acquisition_provenance"] != "VERIFIED":
            gaps.append("PROVENANCE_NOT_TRACEABLE")
        if not row["anchor_replay_ok"]:
            gaps.append("ANCHOR_REPLAY_FAILED")
        if not row["publication_date_usable"]:
            gaps.append("TIME_NOT_USABLE")
        if row["project_policy_check"] != "APPLIED":
            gaps.append("PROJECT_POLICY_NOT_CHECKED")
        if row["content_completeness"] == "UNRESOLVED":
            gaps.append("CONTENT_UNRESOLVED")
        return gaps

    def _write_release(self):
        eligible = []
        held = []
        for row in self.per_source:
            gaps = self._release_gaps(row)
            item = {
                "source_id": row["source_id"],
                "identity_verdict": row["identity_verdict"],
                "acquisition_provenance": row["acquisition_provenance"],
                "content_completeness": row["content_completeness"],
                "completeness_scope": row["completeness_scope"],
                "anchor_page": row["proof_anchor"].get("page"),
                "anchor_replay_ok": row["anchor_replay_ok"],
                "publication_date": row["publication_date"],
                "project_use_policy": row["project_use_policy"],
                "redistribution_permission": row["redistribution_permission"],
                "gaps": gaps,
            }
            if not gaps:
                item["disposition"] = "RELEASE_FOR_EXTRACTION"
                eligible.append(item)
            else:
                item["disposition"] = "HOLD"
                held.append(item)
        candidates = []
        for row in self.per_source:
            text = f"{row['title']} {row['journal']}".lower()
            hits = [need for need, terms in KN_TERMS.items() if any(term in text for term in terms)]
            if not hits:
                continue
            if row["identity_verdict"] not in {"CONFIRMED", "PROBABLE"}:
                continue
            candidates.append((len(hits), row["identity_verdict"] == "CONFIRMED", row))
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        thin = []
        for _, _, row in candidates[:12]:
            thin.append({
                "source_id": row["source_id"],
                "title": row["title"],
                "identity_verdict": row["identity_verdict"],
                "identity_status": row["identity_status"],
                "anchor_page": row["proof_anchor"].get("page"),
                "anchor_role": "IDENTITY_EVIDENCE_NOT_A_RELEASED_SPAN",
                "disposition": "HOLD",
                "gaps": self._release_gaps(row),
            })
        payload = {
            "artifact": "NDF-D1 Case-Specific Source Release Candidate",
            "release_meaning": "RELEASE_FOR_EXTRACTION allows internal stratified extraction only. It is not Scientific Gold and does not allow public redistribution.",
            "eligible_count": len(eligible),
            "eligible": eligible,
            "gate_status": "PASS" if eligible else "HOLD",
            "thin_slice_target": "8-12 sources for KN-D1-A1R-001 if the release gate is met",
            "thin_slice_released": [],
            "thin_slice_candidates_not_released": thin,
            "hold_reason": "No source had a fetch log binding source URL, retrieval time, record signature, and asset hash. Channel strings and bibliographic links were not treated as provenance.",
        }
        (self.run_dir / "14_NDF_D1_case_specific_release_candidate.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _write_gates(self):
        g0 = evaluate_manifest_integrity(self.records, research_relationships=[])
        g1_pass = sum(1 for row in self.per_source if row["gate_g1_verdict"] == "PASS")
        g2_pass = sum(1 for row in self.per_source if row["gate_g2_verdict"] == "PASS")
        total = len(self.per_source)
        g1_rules = [] if g1_pass == total else [{"rule_id": "G1_HASH_OR_SIZE_MISMATCH", "pass": g1_pass, "total": total}]
        g2_rules = [] if g2_pass == total else [{"rule_id": "G2_CONTAINER_OR_RENDER_FAILURE", "pass": g2_pass, "total": total}]
        g3 = aggregate_identity_gate(self.per_source)
        g4p = aggregate_provenance_gate(self.per_source)
        g4r = aggregate_rights_gate(self.per_source)
        g5 = aggregate_study_type_gate(self.per_source, human_completed=0)
        self.gates = {
            "run_id": self.run_id,
            "rule_version": RULE_VERSION,
            "G0_MANIFEST_INTEGRITY": g0,
            "G1_BYTE_LEVEL_SHA256": {"verdict": "PASS" if not g1_rules else "FAIL", "triggered_rules": g1_rules, "pass": g1_pass, "total": total},
            "G2_CONTAINER_READABILITY": {"verdict": "PASS" if not g2_rules else "FAIL", "triggered_rules": g2_rules, "pass": g2_pass, "total": total},
            "G3_DOCUMENT_IDENTITY_AND_COMPLETENESS": g3,
            "G4_ACQUISITION_PROVENANCE": g4p,
            "G4_RIGHTS": g4r,
            "G5_STUDY_TYPE": g5,
            "HUMAN_REVIEW": {"verdict": "PENDING", "triggered_rules": [{"rule_id": "NO_EXPERT_SIGNATURE", "completed": 0}]},
            "scientific_gold_status": "NOT_GRANTED",
        }
        (self.run_dir / "10_gate_reasoned_verdicts.json").write_text(json.dumps(self.gates, indent=2, ensure_ascii=False), encoding="utf-8")

    def _run_unit_tests(self):
        cmd = [sys.executable, "-m", "unittest", "tools.source_archive_verifier.test_r1_replay"]
        proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
        self.test_exit = proc.returncode
        fixture_dir = REPO / "tools" / "source_archive_verifier" / "fixtures"
        before = (fixture_dir / "r1_3_adversarial_before.txt").read_text(encoding="utf-8", errors="replace") if (fixture_dir / "r1_3_adversarial_before.txt").exists() else "NOT_PROVEN"
        after_saved = (fixture_dir / "r1_3_adversarial_after.txt").read_text(encoding="utf-8", errors="replace") if (fixture_dir / "r1_3_adversarial_after.txt").exists() else ""
        text = "\n".join([
            f"command: {' '.join(cmd)}",
            f"cwd: {REPO}",
            f"exit_code: {proc.returncode}",
            "----- stdout -----",
            proc.stdout,
            "----- stderr -----",
            proc.stderr,
            "----- before (pre-fix unittest) -----",
            before[-4000:],
            "----- after fixture captured before this audit process -----",
            after_saved[-2000:],
        ])
        (self.run_dir / "12_test_commands_logs_exit_codes.txt").write_text(text, encoding="utf-8")

    def _write_issues(self):
        rows = [
            ("F01", "HIGH", "SourceID branches removed from the content evaluator. Holds bind to hash and manifest revision.", "AT-03, AT-04"),
            ("F02", "CRITICAL", "Title plus DOI inside references cannot confirm document identity.", "AT-01, AT-05"),
            ("F03", "CRITICAL", "A six-word prefix with a divergent continuation stays HOLD.", "AT-02"),
            ("F04", "MEDIUM", "NC-05 now requires CONFLICTING_DOI_DETECTED and the cover-DOI rule.", "NC-05"),
            ("F05", "HIGH", "G0-G5 verdicts are computed from triggered rules.", "test_g0_duplicate_doi_without_relationship_holds"),
            ("F06", "HIGH", "Provenance VERIFIED requires URL, time, signature, and hash.", "AT-09"),
            ("F07", "HIGH", "Completeness is not inferred from page count.", "AT-10"),
            ("F08", "MEDIUM", "Legal status, redistribution, and project policy are separate fields.", "07_G4_rights.csv"),
            ("F09", "MEDIUM", "Prior run hashes are snapshotted or marked NOT_PROVEN. The decision report is inside the integrity manifest.", "01_original_inputs_and_prior_run_sha256.json"),
            ("F10", "MEDIUM", "Anchors use page character spans and must round-trip.", "AT-11"),
        ]
        with (self.run_dir / "11_issues_disposition.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["issue_code", "severity", "remedy", "test_id", "unit_test_exit_code"])
            writer.writeheader()
            for code, severity, remedy, test_id in rows:
                writer.writerow({
                    "issue_code": code,
                    "severity": severity,
                    "remedy": remedy,
                    "test_id": test_id,
                    "unit_test_exit_code": self.test_exit,
                })

    def _write_report(self):
        counts = Counter(row["identity_verdict"] for row in self.per_source)
        comp = Counter(row["content_completeness"] for row in self.per_source)
        prov = Counter(row["acquisition_provenance"] for row in self.per_source)
        admin = sum(1 for row in self.per_source if row["administrative_hold"]["active"])
        replay_fail = sum(1 for row in self.per_source if not row["anchor_replay_ok"])
        delta = json.loads((self.run_dir / "05_semantic_delta_summary.json").read_text(encoding="utf-8"))
        lines = [
            f"# G1-Shared R1.3 truthfulness run `{self.run_id}`",
            "",
            f"Rule `{RULE_VERSION}`. Scientific Gold: NOT_GRANTED. Expert signature: NOT_OBTAINED.",
            "",
            "## Gate results",
            "",
        ]
        for key in ["G0_MANIFEST_INTEGRITY", "G1_BYTE_LEVEL_SHA256", "G2_CONTAINER_READABILITY", "G3_DOCUMENT_IDENTITY_AND_COMPLETENESS", "G4_ACQUISITION_PROVENANCE", "G4_RIGHTS", "G5_STUDY_TYPE", "HUMAN_REVIEW"]:
            gate = self.gates[key]
            rules = [item.get("rule_id") for item in gate.get("triggered_rules", [])]
            lines.append(f"- {key}: {gate.get('verdict')} rules={rules or 'NONE'}")
        lines += [
            "",
            "## Identity counts",
            "",
            f"CONFIRMED {counts.get('CONFIRMED', 0)}; PROBABLE {counts.get('PROBABLE', 0)}; HOLD {counts.get('HOLD', 0)}; MISMATCH {counts.get('MISMATCH', 0)}.",
            f"Completeness {dict(comp)}.",
            f"Provenance {dict(prov)}.",
            f"Hash-bound administrative holds: {admin}. Anchor replay failures: {replay_fail}.",
            f"Semantic drift R1.1 to R1.3 after PASS→CONFIRMED normalization: {delta.get('semantic_drift_r11_r13')}. Raw enum differences: {delta.get('raw_enum_differs_r11_r13')}. Semantic drift R1.2 to R1.3: {delta.get('semantic_drift_r12_r13')}.",
            "",
            "RELEASE_FOR_EXTRACTION was not granted. No fetch log bound a source URL, retrieval time, signature, and asset hash.",
            "D1 thin-slice candidates are listed only as HOLD with gaps. No synthetic PDF or invented span was added.",
            "",
            "Limits: this run did not obtain publisher redistribution licenses, expert signatures, or an external DOI registry check. Replaying the package on another machine requires the local vault PDFs, which are not in the ZIP.",
        ]
        (self.run_dir / "09_G0_G5_Decision_Report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _copy_sources(self):
        names = [
            "identity_evaluator.py",
            "r1_independent_replay_verifier.py",
            "r1_3_replay_auditor.py",
            "test_r1_replay.py",
        ]
        base = REPO / "tools" / "source_archive_verifier"
        for name in names:
            target = self.run_dir / name
            target.write_text((base / name).read_text(encoding="utf-8"), encoding="utf-8")
        registry = base / "fixtures" / "quarantine_registry_r1_3.json"
        (self.run_dir / "quarantine_registry_r1_3.json").write_text(registry.read_text(encoding="utf-8"), encoding="utf-8")

    def _seal(self):
        excluded = {"13_run_integrity_manifest.json", "R1_3_Independent_Audit_Package.zip"}
        items = []
        for path in sorted(self.run_dir.iterdir()):
            if path.name in excluded or not path.is_file():
                continue
            items.append({"filename": path.name, "size_bytes": path.stat().st_size, "sha256": calculate_sha256(path)})
        manifest = {"run_id": self.run_id, "self_hash": "EXCLUDED", "files": items}
        manifest_path = self.run_dir / "13_run_integrity_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        mismatches = []
        for item in items:
            current = calculate_sha256(self.run_dir / item["filename"])
            if current != item["sha256"]:
                mismatches.append(item["filename"])
        if mismatches:
            raise SystemExit(f"Integrity mismatch before seal: {mismatches}")
        zip_path = self.run_dir / "R1_3_Independent_Audit_Package.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(self.run_dir.iterdir()):
                if path.suffix == ".zip" or path.suffix.lower() == ".pdf":
                    continue
                archive.write(path, arcname=path.name)
        print(f"Sealed {len(items)} hashed files; zip bytes={zip_path.stat().st_size}")


def main():
    R1_3_ReplayAuditor().run()


if __name__ == "__main__":
    main()
