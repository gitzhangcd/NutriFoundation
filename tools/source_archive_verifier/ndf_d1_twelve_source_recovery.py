#!/usr/bin/env python3
"""Official-source recovery for the 12 R1.3 thin-slice candidates.

Does not overwrite vault PDFs, invent historical timestamps, or bypass access controls.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from tools.source_archive_verifier.identity_evaluator import (
    calculate_sha256,
    evaluate_pdf_identity_canonical,
    replay_proof_anchor,
)

VAULT = Path("/Users/zhangcd/Codes/Ai-Nutri/data/g1_source_library")
R13_RELEASE = VAULT / "verification_runs" / "G1S-133-R1-3-TRUTHFULNESS-20261010T075311Z" / "14_NDF_D1_case_specific_release_candidate.json"
MANIFEST = VAULT / "Archived_Papers_133_Manifest.json"
CUTOFF = "2026-10-07"
TOOL_ID = "ndf-d1-official-recovery-r1.3.1"
OPERATOR_ID = "cursor-local-agent"
USER_AGENT = "NutriFoundation-R1.3.1-source-recovery/1.0 (internal research; lawful OA only)"
REDISTRIBUTABLE = {"cc by", "cc-by", "cc0", "cc-by-sa", "public domain", "cc by-sa"}


def _get(url: str, timeout: int = 45) -> tuple[int, dict, bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/pdf, */*"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            headers = {key.lower(): value for key, value in response.headers.items()}
            return response.status, headers, body, response.geturl()
    except urllib.error.HTTPError as exc:
        body = exc.read() if exc.fp else b""
        headers = {key.lower(): value for key, value in (exc.headers.items() if exc.headers else [])}
        return exc.code, headers, body, url


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _audit_digest(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _date_from_parts(parts) -> str | None:
    if not parts:
        return None
    values = [str(part) for part in parts if part]
    if not values:
        return None
    if len(values) == 1:
        return f"{values[0]}-01-01" if len(values[0]) == 4 else None
    if len(values) == 2:
        return f"{int(values[0]):04d}-{int(values[1]):02d}-01"
    return f"{int(values[0]):04d}-{int(values[1]):02d}-{int(values[2]):02d}"


def _cutoff_status(iso_date: str | None, raw_date: str) -> str:
    if not iso_date and not raw_date:
        return "DATE_UNKNOWN_HOLD"
    if iso_date and len(iso_date) == 10:
        if iso_date < CUTOFF:
            return "ON_OR_BEFORE_CUTOFF"
        if iso_date == CUTOFF:
            return "SAME_DAY_AMBIGUOUS_HOLD"
        if iso_date[:7] == "2026-10" and iso_date[8:] == "01" and "day" not in raw_date.lower():
            return "MONTH_PRECISION_AMBIGUOUS_HOLD"
        return "AFTER_CUTOFF_HOLD" if iso_date > CUTOFF else "ON_OR_BEFORE_CUTOFF"
    return "DATE_UNKNOWN_HOLD"


def _license_text(epmc: dict, crossref: dict) -> str:
    chunks = []
    if epmc.get("license"):
        chunks.append(str(epmc.get("license")))
    for item in (crossref.get("message") or {}).get("license") or []:
        if item.get("URL"):
            chunks.append(item["URL"])
    return " | ".join(chunks).lower()


def _license_allows_retrieval(license_text: str, open_access: bool) -> bool:
    lowered = license_text.lower()
    if "elsevier.com" in lowered and "creativecommons.org" not in lowered:
        return False
    return open_access or any(token in lowered for token in REDISTRIBUTABLE) or "by-nc" in lowered or "by/4.0" in lowered


def _pdf_candidates(epmc: dict, crossref_msg: dict, license_text: str, open_access: bool) -> list[str]:
    if not _license_allows_retrieval(license_text, open_access):
        return []
    urls: list[str] = []
    for item in epmc.get("fullTextUrlList", {}).get("fullTextUrl", []) or []:
        if str(item.get("documentStyle", "")).lower() == "pdf" and item.get("url"):
            urls.append(item["url"])
    pmcid = epmc.get("pmcid")
    if open_access and pmcid:
        urls.append(f"https://europepmc.org/articles/{pmcid}?pdf=render")
    for item in crossref_msg.get("link") or []:
        url = item.get("URL") or ""
        kind = str(item.get("content-type") or "").lower()
        if not url or "/tdm/" in url or "syndication.highwire.org" in url:
            continue
        if kind == "application/pdf" or url.lower().endswith(".pdf") or "/pdf" in url.lower():
            urls.append(url)
    seen = set()
    ordered = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered


def _crosscheck(record: dict, epmc: dict, crossref_msg: dict) -> dict:
    manifest_doi = (record["identifiers"].get("doi") or "").lower()
    manifest_pmid = str(record["identifiers"].get("pmid") or "")
    epmc_doi = str(epmc.get("doi") or "").lower()
    epmc_pmid = str(epmc.get("pmid") or "")
    cross_doi = str(crossref_msg.get("DOI") or "").lower()
    return {
        "manifest_doi_matches_europepmc": bool(manifest_doi) and manifest_doi == epmc_doi,
        "manifest_doi_matches_crossref": bool(manifest_doi) and manifest_doi == cross_doi,
        "manifest_pmid_matches_europepmc": bool(manifest_pmid) and manifest_pmid == epmc_pmid,
        "europepmc_title": epmc.get("title"),
        "crossref_title": (crossref_msg.get("title") or [None])[0],
        "manifest_title": record["title"],
    }


def _browser_doi_hits(dois: list[str]) -> dict:
    import shutil
    import sqlite3
    import tempfile
    source = Path.home() / "Library/Application Support/Google/Chrome/Default/History"
    if not source.exists():
        return {"status": "CHROME_HISTORY_ABSENT", "hits": {}}
    temporary = Path(tempfile.mkdtemp()) / "History"
    try:
        shutil.copy(source, temporary)
        connection = sqlite3.connect(temporary)
        hits = {}
        for doi in dois:
            if not doi:
                continue
            rows = connection.execute(
                "SELECT url, last_visit_time FROM urls WHERE url LIKE ? LIMIT 3",
                (f"%{doi}%",),
            ).fetchall()
            hits[doi] = [
                {
                    "url": url,
                    "chrome_last_visit_time": ts,
                    "note": "A browser URL hit is not a signed download log.",
                }
                for url, ts in rows
            ]
        connection.close()
        return {"status": "SEARCHED", "hits": hits}
    except Exception as exc:
        return {"status": "CHROME_HISTORY_NOT_READ", "error": type(exc).__name__, "hits": {}}


def recover(run_dir: Path) -> dict:
    release = json.loads(R13_RELEASE.read_text(encoding="utf-8"))
    wanted = [item["source_id"] for item in release["thin_slice_candidates_not_released"]]
    records = {row["source_id"]: row for row in json.loads(MANIFEST.read_text(encoding="utf-8"))["records"]}
    download_rows = {row.get("source_id"): row for row in json.loads((VAULT / "download_summary.json").read_text(encoding="utf-8")).get("details", [])}
    out_dir = run_dir / "ndf_d1_12_source_recovery"
    out_dir.mkdir(parents=True, exist_ok=True)
    packages = []
    browser = _browser_doi_hits([(records[sid]["identifiers"].get("doi") or "").strip() for sid in wanted])
    (out_dir / "browser_doi_url_hits.json").write_text(json.dumps(browser, indent=2), encoding="utf-8")
    for sid in wanted:
        record = records[sid]
        asset = record["archive_asset"]
        old_pdf = VAULT / asset["vault_path"].strip()
        old_sha = calculate_sha256(old_pdf) if old_pdf.exists() else ""
        sidecar_path = VAULT / "sources" / sid / "manifest.json"
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8")) if sidecar_path.exists() else {}
        doi = (record["identifiers"].get("doi") or "").strip()
        pmid = (record["identifiers"].get("pmid") or "").strip()
        epmc_result = {}
        crossref_msg = {}
        metadata_errors = []
        if doi or pmid:
            query = f'DOI:"{doi}"' if doi else f"EXT_ID:{pmid}"
            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({
                "query": query, "format": "json", "resultType": "core", "pageSize": "1",
            })
            status, _headers, body, final_url = _get(url)
            if status == 200:
                hits = json.loads(body.decode("utf-8", errors="replace")).get("resultList", {}).get("result", [])
                epmc_result = hits[0] if hits else {}
                epmc_result["_request_url"] = final_url
            else:
                metadata_errors.append(f"EUROPEPMC_HTTP_{status}")
        if doi:
            status, _headers, body, final_url = _get("https://api.crossref.org/works/" + urllib.parse.quote(doi))
            if status == 200:
                payload = json.loads(body.decode("utf-8", errors="replace"))
                crossref_msg = payload.get("message") or {}
                crossref_msg["_request_url"] = final_url
            else:
                metadata_errors.append(f"CROSSREF_HTTP_{status}")
        issued = _date_from_parts(((crossref_msg.get("issued") or {}).get("date-parts") or [None])[0])
        cutoff = _cutoff_status(issued, record.get("publication_date") or "")
        license_text = _license_text(epmc_result, {"message": crossref_msg})
        open_access = epmc_result.get("isOpenAccess") == "Y" or _license_allows_retrieval(license_text, False)
        pdf_urls = _pdf_candidates(epmc_result, crossref_msg, license_text, epmc_result.get("isOpenAccess") == "Y" or "creativecommons.org" in license_text)
        source_dir = out_dir / sid
        source_dir.mkdir(parents=True, exist_ok=True)
        new_revision = None
        acquisition = {
            "historical_status": "HISTORICAL_ACQUISITION_UNPROVEN",
            "historical_note": "Existing sidecar and download_summary have no source URL, HTTP evidence, or record signature. archived_at was not reused as a retrieval signature.",
            "sidecar_path": str(sidecar_path) if sidecar_path.exists() else "MISSING",
            "download_summary_row_present": sid in download_rows,
            "full_text_access": None,
            "attempts": [],
        }
        if not pdf_urls:
            acquisition["full_text_access"] = "FULL_TEXT_NOT_LAWFULLY_AVAILABLE"
            acquisition["blocker"] = "No open license or open-access PDF URL was published by Europe PMC or Crossref."
        else:
            retrieved_pdf = None
            for pdf_url in pdf_urls:
                retrieved_at = datetime.now(timezone.utc).isoformat()
                status, headers, body, final_url = _get(pdf_url, timeout=90)
                content_type = headers.get("content-type", "")
                attempt = {
                    "requested_url": pdf_url, "final_url": final_url, "http_status": status,
                    "content_type": content_type, "retrieved_at": retrieved_at,
                    "stored_pdf": bool(status == 200 and body.startswith(b"%PDF")),
                }
                acquisition["attempts"].append(attempt)
                if attempt["stored_pdf"]:
                    retrieved_pdf = (pdf_url, status, headers, body, final_url, content_type, retrieved_at)
                    break
            (source_dir / "landing_attempt.json").write_text(json.dumps(acquisition["attempts"], indent=2), encoding="utf-8")
            if retrieved_pdf:
                pdf_url, status, headers, body, final_url, content_type, retrieved_at = retrieved_pdf
                new_path = source_dir / "reacquired_source.pdf"
                new_path.write_bytes(body)
                new_sha = _sha256_bytes(body)
                event = {
                    "source_id": sid,
                    "source_url": final_url,
                    "requested_url": pdf_url,
                    "retrieved_at": retrieved_at,
                    "http_status": status,
                    "content_type": content_type,
                    "operator_id": OPERATOR_ID,
                    "tool_id": TOOL_ID,
                    "asset_sha256": new_sha,
                    "byte_length": len(body),
                }
                event["audit_record_sha256"] = _audit_digest(event)
                (source_dir / "new_acquisition_event.json").write_text(json.dumps(event, indent=2), encoding="utf-8")
                (source_dir / "http_response_headers.json").write_text(json.dumps({"status": status, "final_url": final_url, "headers": headers}, indent=2), encoding="utf-8")
                identity = evaluate_pdf_identity_canonical(
                    new_path, record["title"], doi, pmid, source_id=sid,
                    expected_journal=record.get("journal") or "", expected_date=record.get("publication_date") or "",
                )
                title_replay = replay_proof_anchor(new_path, identity["title_anchor"]) if identity.get("title_anchor") else {"ok": False}
                doi_replay = replay_proof_anchor(new_path, identity["doi_anchor"]) if identity.get("doi_anchor") else {"ok": False}
                new_revision = {
                    "asset_revision_id": f"{sid}-R131-NEW",
                    "path": str(new_path),
                    "sha256": new_sha,
                    "binary_relation_to_vault_asset": "BINARY_EQUIVALENT" if new_sha == old_sha else "HASH_DISTINCT",
                    "content_equivalence": "NOT_ASSERTED_WHEN_HASHES_DIFFER" if new_sha != old_sha else "SAME_BYTES",
                    "identity_verdict": identity["identity_verdict"],
                    "identity_status": identity["identity_status"],
                    "article_identity_block_id": identity.get("article_identity_block_id"),
                    "title_anchor_replay_ok": title_replay.get("ok"),
                    "doi_anchor_replay_ok": doi_replay.get("ok"),
                    "event": event,
                }
                acquisition["full_text_access"] = "NEW_OA_PDF_RETRIEVED"
                acquisition["new_acquisition_verified"] = True
            else:
                refused = any(item["http_status"] in {401, 403, 429} for item in acquisition["attempts"])
                acquisition["full_text_access"] = "LAWFUL_OA_PDF_NOT_RETRIEVED" if refused else "FULL_TEXT_NOT_LAWFULLY_AVAILABLE"
                acquisition["blocker"] = "A public OA or CC-licensed PDF URL was recorded, but this client did not receive a PDF. No access-control bypass was attempted." if refused else "No PDF bytes were returned by the recorded official URLs."
        public_redistribution = any(token in license_text for token in REDISTRIBUTABLE) and "nc" not in license_text and "nd" not in license_text
        internal_use = "PERMITTED_OA_INTERNAL_RESEARCH" if open_access and license_text and not public_redistribution else (
            "PERMITTED_OA_INTERNAL_AND_REDISTRIBUTION_LICENSE" if public_redistribution else (
                "NOT_LAWFULLY_AVAILABLE" if acquisition["full_text_access"] == "FULL_TEXT_NOT_LAWFULLY_AVAILABLE" else "OA_LICENSE_NOT_STATED"
            )
        )
        identity_qualified = bool(new_revision and new_revision["identity_verdict"] == "CONFIRMED" and new_revision["title_anchor_replay_ok"] and (new_revision["doi_anchor_replay_ok"] or not doi))
        extraction_ready = bool(
            identity_qualified
            and acquisition.get("new_acquisition_verified")
            and cutoff == "ON_OR_BEFORE_CUTOFF"
            and internal_use.startswith("PERMITTED_OA")
            and acquisition["full_text_access"] == "NEW_OA_PDF_RETRIEVED"
        )
        package = {
            "source_id": sid,
            "vault_asset_revision": {"asset_revision_id": f"{sid}-VAULT", "sha256": old_sha, "path": str(old_pdf), "historical_acquisition": "HISTORICAL_ACQUISITION_UNPROVEN"},
            "new_asset_revision": new_revision,
            "external_crosscheck": _crosscheck(record, epmc_result, crossref_msg),
            "metadata_errors": metadata_errors,
            "europepmc_is_open_access": epmc_result.get("isOpenAccess"),
            "europepmc_pmcid": epmc_result.get("pmcid"),
            "license_evidence": license_text or "NO_LICENSE_FIELD",
            "version_of_record_date": issued,
            "manifest_publication_date": record.get("publication_date"),
            "evidence_cutoff": CUTOFF,
            "cutoff_status": cutoff,
            "qualifications": {
                "IDENTITY_QUALIFIED": identity_qualified,
                "ACQUISITION_RECONSTRUCTED": False,
                "NEW_ACQUISITION_VERIFIED": bool(acquisition.get("new_acquisition_verified")),
                "RIGHTS_INTERNAL_USE_ASSESSED": True,
                "internal_use_determination": internal_use,
                "RIGHTS_PUBLIC_REDISTRIBUTION_ALLOWED": public_redistribution,
                "EXTRACTION_READY": extraction_ready,
            },
            "release_disposition": "RELEASE_FOR_EXTRACTION" if extraction_ready else "HOLD",
            "release_meaning": "EXTRACTION_READY allows internal stratified extraction only. It is not Expert Gold and does not by itself allow public full-text redistribution.",
            "acquisition": acquisition,
            "sidecar_archived_at_not_used_as_signature": sidecar.get("archived_at"),
        }
        (source_dir / "qualification.json").write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")
        packages.append(package)
        print(sid, package["release_disposition"], acquisition["full_text_access"], package["qualifications"]["IDENTITY_QUALIFIED"])
    summary = {
        "candidate_count": len(packages),
        "release_for_extraction": sum(1 for item in packages if item["release_disposition"] == "RELEASE_FOR_EXTRACTION"),
        "hold": sum(1 for item in packages if item["release_disposition"] == "HOLD"),
        "by_access": dict(__import__("collections").Counter(item["acquisition"]["full_text_access"] for item in packages)),
        "sources": [{
            "source_id": item["source_id"],
            "disposition": item["release_disposition"],
            "access": item["acquisition"]["full_text_access"],
            "identity_qualified": item["qualifications"]["IDENTITY_QUALIFIED"],
            "new_acquisition_verified": item["qualifications"]["NEW_ACQUISITION_VERIFIED"],
            "internal_use": item["qualifications"]["internal_use_determination"],
            "public_redistribution": item["qualifications"]["RIGHTS_PUBLIC_REDISTRIBUTION_ALLOWED"],
            "cutoff_status": item["cutoff_status"],
            "binary_relation": (item.get("new_asset_revision") or {}).get("binary_relation_to_vault_asset"),
            "blocker": item["acquisition"].get("blocker"),
        } for item in packages],
    }
    (out_dir / "recovery_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary


if __name__ == "__main__":
    import sys
    recover(Path(sys.argv[1]))
